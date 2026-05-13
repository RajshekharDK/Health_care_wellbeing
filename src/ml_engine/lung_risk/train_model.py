import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix


# =====================================================
# CONFIG
# =====================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

DATA_PATH = os.path.join(BASE_DIR, "data", "survey lung cancer.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "src", "ml_engine", "lung_risk")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)

# Normalize column names
df.columns = df.columns.str.strip().str.upper()


# =====================================================
# TARGET VARIABLE
# =====================================================

df["LUNG_CANCER"] = df["LUNG_CANCER"].map({"YES": 1, "NO": 0})

y = df["LUNG_CANCER"]
X = df.drop("LUNG_CANCER", axis=1)


# =====================================================
# FEATURE TYPES
# =====================================================

categorical_features = ["GENDER"]
numeric_features = [col for col in X.columns if col not in categorical_features]


# =====================================================
# PREPROCESSING PIPELINE
# =====================================================

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(
            drop="first",
            handle_unknown="ignore"   # 🔥 FIX
        ), categorical_features)
    ]
)


# =====================================================
# MODEL PIPELINE
# =====================================================

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(max_iter=1000, random_state=42))
])


# =====================================================
# TRAIN TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)

print("Train size:", len(X_train))
print("Test size:", len(X_test))


# =====================================================
# TRAIN MODEL
# =====================================================

pipeline.fit(X_train, y_train)


# =====================================================
# EVALUATION
# =====================================================

y_pred = pipeline.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))


# =====================================================
# CROSS VALIDATION
# =====================================================

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

scores = cross_val_score(
    pipeline,
    X,
    y,
    cv=skf,
    scoring="accuracy"
)

print("\nCross Validation Scores:", scores)
print("Mean CV Accuracy:", scores.mean())

# =====================================================
# SAVE MODEL (ENHANCED)
# =====================================================

model_path = os.path.join(OUTPUT_DIR, "pipeline.pkl")
schema_path = os.path.join(OUTPUT_DIR, "schema.json")
feature_meta_path = os.path.join(OUTPUT_DIR, "feature_meta.json")

joblib.dump(pipeline, model_path)


# -----------------------------------------------------
# SCHEMA (UPDATED)
# -----------------------------------------------------

schema = {
    "model_type": "Lung Cancer Risk Estimator",
    "target": "LUNG_CANCER",
    "features": list(X.columns),
    "risk_logic": {
        "low": "< 0.35",
        "moderate": "0.35 - 0.65",
        "high": "> 0.65"
    }
}

with open(schema_path, "w") as f:
    json.dump(schema, f, indent=4)


# -----------------------------------------------------
# FEATURE METADATA (NEW)
# -----------------------------------------------------

feature_meta = {
    "categorical_features": categorical_features,
    "numeric_features": numeric_features,
    "input_shape": len(X.columns),
    "training_samples": int(len(df)),
    "class_distribution": df["LUNG_CANCER"].value_counts().to_dict()
}

with open(feature_meta_path, "w") as f:
    json.dump(feature_meta, f, indent=4)


print("\n✅ Lung model saved with full metadata")
print("Model:", model_path)
print("Schema:", schema_path)
print("Feature Meta:", feature_meta_path)