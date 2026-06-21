import random
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)

from imblearn.over_sampling import ADASYN

import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import Sequential

import shap
from lime.lime_tabular import LimeTabularExplainer

warnings.filterwarnings('ignore')

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

data = pd.read_csv("data.csv")

print(f"Shape: {data.shape}")
data.head()

data.info()

data.describe()

label_columns = ["bearings", "wpump", "radiator", "exvalve"]
feature_columns = [c for c in data.columns if c not in label_columns + ["id"]]

TARGETS = {
    "bearings": {
        "label_map": {"Ok": 0, "Noisy": 1},
        "class_names": ["Ok", "Noisy"],
    },
    "wpump": {
        "label_map": {"Ok": 0, "Noisy": 1},
        "class_names": ["Ok", "Noisy"],
    },
    "radiator": {
        "label_map": {"Clean": 0, "Dirty": 1},
        "class_names": ["Clean", "Dirty"],
    },
    "exvalve": {
        "label_map": {"Clean": 0, "Dirty": 1},
        "class_names": ["Clean", "Dirty"],
    },
}

print("Feature columns:", feature_columns)
print(f"Total features: {len(feature_columns)}")
print("\nClass distribution per target:")
for target in label_columns:
    print(f"  {target}: {data[target].value_counts().to_dict()}")

models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

all_metrics = {}

for target_column, config in TARGETS.items():
    print(f"\n{'='*60}")
    print(f"  MODEL: {target_column.upper()}")
    print(f"{'='*60}\n")

    label_map = config["label_map"]
    class_names = config["class_names"]

    X = data[feature_columns].copy()
    y = data[target_column].map(label_map)

    # --- Split ---
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    X_train_raw, X_val_raw, y_train, y_val = train_test_split(
        X_train_raw, y_train, test_size=0.2, stratify=y_train, random_state=RANDOM_STATE
    )

    print(f"Train : {y_train.value_counts().to_dict()}")
    print(f"Val   : {y_val.value_counts().to_dict()}")
    print(f"Test  : {y_test.value_counts().to_dict()}")

    # --- Scale ---
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_val   = scaler.transform(X_val_raw)
    X_test  = scaler.transform(X_test_raw)

    # --- ADASYN ---
    adasyn = ADASYN(random_state=RANDOM_STATE)
    X_train_res, y_train_res = adasyn.fit_resample(X_train, y_train)
    print(f"After ADASYN: {pd.Series(y_train_res).value_counts().to_dict()}")

    # --- DNN ---
    tf.random.set_seed(RANDOM_STATE)
    model = Sequential([
        Input(shape=(X_train_res.shape[1],)),
        Dense(32, activation="relu"),
        Dropout(0.3),
        Dense(16, activation="relu", name="latent_features"),
        Dropout(0.3),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    early_stop = EarlyStopping(
        monitor="val_loss", patience=20, restore_best_weights=True
    )
    history = model.fit(
        X_train_res, y_train_res,
        epochs=150,
        batch_size=64,
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
        shuffle=True,
        verbose=1,
    )

    # Training history
    plt.figure(figsize=(8, 4))
    plt.plot(history.history["accuracy"], label="train")
    plt.plot(history.history["val_accuracy"], label="validation")
    plt.title(f"Training Accuracy — {target_column}")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    # --- Feature extractor ---
    feature_extractor = tf.keras.Model(
        inputs=model.inputs,
        outputs=model.get_layer("latent_features").output,
    )
    train_features_res = feature_extractor.predict(X_train_res, verbose=0)
    val_features       = feature_extractor.predict(X_val, verbose=0)
    test_features      = feature_extractor.predict(X_test, verbose=0)

    # --- SVM ---
    svm = SVC(
        kernel="rbf", C=10, gamma="scale",
        class_weight="balanced", probability=True,
        random_state=RANDOM_STATE,
    )
    svm.fit(train_features_res, y_train_res)

    # --- Evaluation ---
    pred   = svm.predict(test_features)
    y_prob = svm.predict_proba(test_features)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, pred),
        "f1_fault": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }
    all_metrics[target_column] = metrics

    print("\n--- Metrics ---")
    for name, value in metrics.items():
        print(f"  {name}: {value:.4f}")
    print(classification_report(y_test, pred, target_names=class_names))

    # Confusion matrix
    cm = confusion_matrix(y_test, pred)
    plt.figure(figsize=(5, 4))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=[f"Pred {c}" for c in class_names],
        yticklabels=[f"Actual {c}" for c in class_names],
    )
    plt.title(f"Confusion Matrix — {target_column}")
    plt.tight_layout()
    plt.show()

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.figure(figsize=(5, 4))
    plt.plot(fpr, tpr, label=f"AUC = {metrics['roc_auc']:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.title(f"ROC Curve — {target_column}")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    # --- SHAP ---
    latent_names = [f"latent_{i}" for i in range(train_features_res.shape[1])]
    shap_explainer = shap.KernelExplainer(
        svm.predict,
        shap.sample(train_features_res, 100, random_state=RANDOM_STATE),
    )
    shap_values = shap_explainer.shap_values(test_features[:100])
    shap.summary_plot(shap_values, test_features[:100], feature_names=latent_names, show=False)
    plt.title(f"SHAP Summary — {target_column}")
    plt.tight_layout()
    plt.show()

    # --- LIME ---
    lime_explainer = LimeTabularExplainer(
        train_features_res,
        feature_names=latent_names,
        class_names=class_names,
        mode="classification",
        discretize_continuous=True,
        random_state=RANDOM_STATE,
    )
    lime_exp = lime_explainer.explain_instance(
        test_features[0], svm.predict_proba, num_features=8
    )
    fig = lime_exp.as_pyplot_figure()
    fig.suptitle(f"LIME Explanation — {target_column}")
    plt.tight_layout()
    plt.show()

    # --- Save ---
    model.save(models_dir / f"dnn_{target_column}.keras")
    feature_extractor.save(models_dir / f"dnn_extractor_{target_column}.keras")
    joblib.dump(
        {
            "scaler": scaler,
            "svm": svm,
            "feature_columns": feature_columns,
            "target_column": target_column,
            "label_mapping": label_map,
            "class_names": class_names,
            "metrics": metrics,
        },
        models_dir / f"hybrid_model_{target_column}.pkl",
    )
    print(f"Saved: models/hybrid_model_{target_column}.pkl")

print("\n" + "="*60)
print("  RINGKASAN METRICS SEMUA KOMPONEN")
print("="*60)

summary_df = pd.DataFrame(all_metrics).T
summary_df.columns = ["Accuracy", "Balanced Acc", "F1 Fault", "ROC-AUC"]
print(summary_df.round(4).to_string())

fig, ax = plt.subplots(figsize=(9, 4))
summary_df.round(4).plot(kind="bar", ax=ax, ylim=(0, 1.05), rot=0)
ax.set_title("Perbandingan Metrics antar Komponen")
ax.set_xlabel("Komponen")
ax.set_ylabel("Score")
ax.legend(loc="lower right")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()

# Kesimpulan Pipeline
#
# Dataset  : data.csv — 1000 baris, 10 sensor, 4 label komponen
# Sensor   : rpm, motor_power, noise_db, outlet_pressure_bar, air_flow,
#            outlet_temp, wpump_outlet_press, water_flow, gaccz, haccz
# Target   : bearings, wpump, radiator, exvalve  (acmotor dihapus: semua Stable)
# Metode   : DNN (feature extractor 16-dim) + SVM RBF (classifier)
#
# Pipeline per komponen:
# 1. Sensor dipilih berbasis domain knowledge (10 dari 20 sensor asli).
# 2. Split stratified: 64% train / 16% validation / 20% test.
# 3. MinMaxScaler hanya fit pada data train (mencegah data leakage).
# 4. ADASYN hanya pada train set untuk menangani class imbalance.
# 5. DNN mengekstrak 16 fitur laten dari 10 sensor.
# 6. SVM RBF mengklasifikasikan fitur laten.
# 7. Evaluasi: accuracy, balanced accuracy, F1 fault, ROC-AUC.
# 8. SHAP (global) + LIME (lokal) untuk explainability.
# 9. Setiap komponen disimpan sebagai file model terpisah di folder models/.
