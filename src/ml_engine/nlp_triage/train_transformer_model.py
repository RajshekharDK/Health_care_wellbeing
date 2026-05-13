import os
import re
import joblib
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


# ==========================================================
# PATHS
# ==========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../../"))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")

SYMPTOM2_PATH = os.path.join(DATA_DIR, "Symptom2Disease.csv")
DISEASES_PATH = os.path.join(DATA_DIR, "Diseases_Symptoms.csv")

PIPELINE_PATH = os.path.join(CURRENT_DIR, "pipeline.pkl")
ENCODER_PATH = os.path.join(CURRENT_DIR, "label_encoder.pkl")


# ==========================================================
# TEXT CLEANING
# ==========================================================

def clean_text(text):

    text = text.lower()

    text = re.sub(r"[^\w\s]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ==========================================================
# LOAD DATASETS
# ==========================================================

print("Loading datasets...")

df1 = pd.read_csv(SYMPTOM2_PATH)
df1 = df1[["text", "label"]]
df1.columns = ["symptoms", "disease"]

df2 = pd.read_csv(DISEASES_PATH)
df2 = df2[["Name", "Symptoms"]]
df2.columns = ["disease", "symptoms"]

df2["symptoms"] = df2["symptoms"].str.replace(",", " ")

dataset = pd.concat([df1, df2], ignore_index=True)
dataset = dataset.dropna()

print("Original dataset size:", len(dataset))


# ==========================================================
# CLEAN TEXT
# ==========================================================

dataset["symptoms"] = dataset["symptoms"].apply(clean_text)


# ==========================================================
# REMOVE RARE DISEASES
# ==========================================================

MIN_SAMPLES = 3

disease_counts = dataset["disease"].value_counts()

valid_diseases = disease_counts[disease_counts >= MIN_SAMPLES].index

dataset = dataset[dataset["disease"].isin(valid_diseases)]

print("Filtered dataset size:", len(dataset))
print("Unique diseases:", dataset["disease"].nunique())


# ==========================================================
# LIMIT DISEASE CLASSES (IMPORTANT FOR ACCURACY)
# ==========================================================

TOP_DISEASES = 40

top_diseases = dataset["disease"].value_counts().head(TOP_DISEASES).index

dataset = dataset[dataset["disease"].isin(top_diseases)]

print("Top diseases used:", len(top_diseases))


# ==========================================================
# SHUFFLE DATA
# ==========================================================

dataset = dataset.sample(frac=1, random_state=42)


# ==========================================================
# LABEL ENCODING
# ==========================================================

encoder = LabelEncoder()

dataset["label"] = encoder.fit_transform(dataset["disease"])


# ==========================================================
# LOAD EMBEDDING MODEL
# ==========================================================

print("Loading SentenceTransformer...")

embedder = SentenceTransformer("all-MiniLM-L6-v2")


# ==========================================================
# GENERATE EMBEDDINGS
# ==========================================================

print("Generating embeddings...")

X_embeddings = embedder.encode(
    dataset["symptoms"].tolist(),
    show_progress_bar=True
)

y = dataset["label"].values


# ==========================================================
# TRAIN TEST SPLIT
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X_embeddings,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# ==========================================================
# TRAIN XGBOOST CLASSIFIER
# ==========================================================

print("Training XGBoost model...")

clf = XGBClassifier(
    objective="multi:softprob",
    eval_metric="mlogloss",
    max_depth=7,
    n_estimators=400,
    learning_rate=0.03,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_lambda=1,
    n_jobs=-1
)

clf.fit(
    X_train,
    y_train,
    eval_set=[(X_test, y_test)],
    verbose=False
)


# ==========================================================
# EVALUATE MODEL
# ==========================================================

accuracy = clf.score(X_test, y_test)

print("\nModel accuracy:", round(accuracy, 4))


# ==========================================================
# SAVE PIPELINE
# ==========================================================

pipeline = {
    "embedder": embedder,
    "classifier": clf
}

joblib.dump(pipeline, PIPELINE_PATH)

joblib.dump(encoder, ENCODER_PATH)

print("\nModel saved successfully:")
print("Pipeline:", PIPELINE_PATH)
print("Encoder:", ENCODER_PATH)