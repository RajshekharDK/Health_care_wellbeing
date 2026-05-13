"""
HWELBEING — Phase 2 Final Clinical Triage Model
Purpose: symptom → possible condition ranking
Treatment is ALWAYS retrieved from SAP HANA database.

SAFETY:
This model does NOT diagnose and does NOT prescribe.
"""

import numpy as np
import pandas as pd
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import random

# =========================================================
# 1. Symptom Schema (Patient-reportable only)
# =========================================================
SYMPTOMS = [
    "fever","high_fever","chills","fatigue","weight_loss","loss_of_appetite",
    "persistent_cough","shortness_of_breath","chest_pain",
    "abdominal_pain","nausea","vomiting","diarrhea","bloating","heartburn",
    "increased_thirst","frequent_urination","blurred_vision",
    "skin_rash","itching","pimples",
    "memory_loss","headache"
]

# =========================================================
# 2. Disease List (MUST match database EXACTLY)
# =========================================================
PROFILES = {

"Typhoid": ["fever","high_fever","abdominal_pain","headache","fatigue","loss_of_appetite"],
"Tuberculosis": ["persistent_cough","weight_loss","night_sweats","chest_pain","shortness_of_breath","fatigue"],
"Gastric": ["abdominal_pain","bloating","heartburn","nausea","vomiting"],
"Diabetes": ["increased_thirst","frequent_urination","blurred_vision","fatigue","weight_loss"],
"Hypertension": ["headache","chest_pain","fatigue"],
"Bronchial Asthma": ["persistent_cough","shortness_of_breath","chest_pain"],
"Cholera": ["diarrhea","vomiting","chills","fatigue"],
"Lung Cancer": ["persistent_cough","weight_loss","chest_pain","shortness_of_breath"],
"Fatty Liver": ["fatigue","abdominal_pain","loss_of_appetite"],
"Acne": ["pimples"],
"Eczema": ["skin_rash","itching"],
"Impetigo": ["skin_rash"],
"Ring Worm": ["skin_rash","itching"],
"Alzheimer'S Disease": ["memory_loss"]
}

# =========================================================
# 3. Synthetic Patient Generator
# =========================================================
def generate_patient(disease):
    patient = dict.fromkeys(SYMPTOMS, 0)

    # add real symptoms
    for s in PROFILES[disease]:
        if random.random() > 0.12:  # sometimes symptom missing
            patient[s] = 1

    # add noise symptoms
    noise = random.sample(SYMPTOMS, k=random.randint(0,3))
    for n in noise:
        patient[n] = 1

    return patient

# =========================================================
# 4. Build Dataset
# =========================================================
records = []
for disease in PROFILES:
    for _ in range(260):
        p = generate_patient(disease)
        p["disease"] = disease
        records.append(p)

df = pd.DataFrame(records)
print("Dataset size:", df.shape)

# =========================================================
# 5. Preprocessing
# =========================================================
X = df[SYMPTOMS]
y = df["disease"]

encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded,
    test_size=0.20,
    random_state=42,
    stratify=y_encoded
)

# =========================================================
# 6. Train Model
# =========================================================
model = RandomForestClassifier(
    n_estimators=350,
    max_depth=18,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)

# =========================================================
# 7. Evaluation
# =========================================================
y_pred = model.predict(X_test)
print("\nAccuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, target_names=encoder.classes_))

# =========================================================
# 8. Save Artifacts (VERY IMPORTANT)
# =========================================================
joblib.dump(model, "hwelbeing_triage_model.pkl")
joblib.dump(scaler, "hwelbeing_scaler.pkl")
joblib.dump(encoder, "hwelbeing_label_encoder.pkl")

with open("hwelbeing_symptoms_schema.json","w") as f:
    json.dump({"symptoms":SYMPTOMS,"diseases":list(encoder.classes_)},f,indent=2)

print("\n✔ Phase-2 model training complete.")