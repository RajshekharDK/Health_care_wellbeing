import os
import json
import joblib
import numpy as np
import pandas as pd


from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC


# =====================================================
# 1. CONFIG
# =====================================================

# Get project root directory dynamically
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DATA_PATH = os.path.join(BASE_DIR, "data", "Symptom2Disease.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "src", "ml_engine", "nlp_triage")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("DATA_PATH:", DATA_PATH)
print("OUTPUT_DIR:", OUTPUT_DIR)

TARGET_DISEASES = [
    "typhoid",
    "hypertension",
    "bronchial asthma",
    "diabetes",
    "acne",
    "impetigo"
]

RANDOM_STATE = 42


# =====================================================
# 2. LOAD DATA
# =====================================================

df = pd.read_csv(DATA_PATH)

print("\nColumns:", df.columns)
print("Initial Shape:", df.shape)

# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# Keep only required columns
df = df[["label", "text"]]

# Clean labels
df["label"] = df["label"].str.strip().str.lower()

# Remove missing
df.dropna(subset=["text", "label"], inplace=True)

print("\nUnique labels before filtering:", df["label"].unique())

# Filter required diseases
df = df[df["label"].isin(TARGET_DISEASES)]

print("\nFiltered Shape:", df.shape)
print("Class Distribution:\n", df["label"].value_counts())


# =====================================================
# 3. LEAKAGE CLEANING
# =====================================================

for disease in TARGET_DISEASES:
    df["text"] = df["text"].str.replace(disease, "", case=False, regex=True)

print("\nLeakage removal complete.")


# =====================================================
# 4. ENCODE LABELS
# =====================================================

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(df["label"])
X = df["text"]

print("\nEncoded Classes:", label_encoder.classes_)


# =====================================================
# 5. TRAIN TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    stratify=y,
    random_state=RANDOM_STATE
)

print("\nTrain size:", len(X_train))
print("Test size:", len(X_test))

# =====================================================
# 6. PIPELINE (TF-IDF + Logistic Regression)
# =====================================================

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=3000,
        stop_words="english"
    )),
    ("clf", LogisticRegression(
        max_iter=1000,
        random_state=RANDOM_STATE
    ))
])

# Train
pipeline.fit(X_train, y_train)

# =====================================================
# 7. EVALUATION
# =====================================================

y_pred = pipeline.predict(X_test)
y_prob = pipeline.predict_proba(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nAUC:", roc_auc_score(y_test, y_prob, multi_class="ovr"))

# =====================================================
# 8. CROSS VALIDATION (SAFE NOW)
# =====================================================

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

cv_scores = cross_val_score(
    pipeline,
    X,
    y,
    cv=skf,
    scoring="accuracy"
)

print("\nCross Validation Scores:", cv_scores)
print("Mean CV Accuracy:", cv_scores.mean())

# =====================================================
# 9. SAVE ARTIFACTS (ONLY PIPELINE)
# =====================================================

joblib.dump(pipeline, os.path.join(OUTPUT_DIR, "pipeline.pkl"))
joblib.dump(label_encoder, os.path.join(OUTPUT_DIR, "label_encoder.pkl"))

schema = {
    "model_type": "NLP Symptom Triage",
    "diseases": label_encoder.classes_.tolist(),
    "pipeline": "TF-IDF (1-2 grams, max_features=3000) + LogisticRegression",
    "risk_logic": {
        "low": "< 0.40",
        "moderate": "0.40 - 0.70",
        "high": "> 0.70"
    }
}

with open(os.path.join(OUTPUT_DIR, "schema.json"), "w") as f:
    json.dump(schema, f, indent=4)

print("\nPipeline saved successfully.")