import warnings
warnings.filterwarnings("ignore")
import os
os.chdir(r"d:\TugasAkhir\cmms-manufacture-main - Copy\machine-learning filtered data")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
from lime.lime_tabular import LimeTabularExplainer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from imblearn.over_sampling import ADASYN
import tensorflow as tf
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Sequential

print("Loading data...")
data = pd.read_csv("data.csv")
print(f"Shape: {data.shape}")

X = data[["rpm","motor_power","noise_db","gaccz","haccz"]].values[:200]
y = (data["bearings"] == "Noisy").astype(int).values[:200]

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
scaler = MinMaxScaler()
X_tr = scaler.fit_transform(X_tr)
X_te = scaler.transform(X_te)

try:
    ada = ADASYN(random_state=42)
    X_tr, y_tr = ada.fit_resample(X_tr, y_tr)
    print(f"ADASYN ok: {X_tr.shape}")
except Exception as e:
    print(f"ADASYN error: {e}")

model = Sequential([
    Input(shape=(X_tr.shape[1],)),
    Dense(8, activation="relu", name="latent_features"),
    Dense(1, activation="sigmoid")
])
model.compile(optimizer="adam", loss="binary_crossentropy")
model.fit(X_tr, y_tr, epochs=3, verbose=0)

extractor = tf.keras.Model(inputs=model.inputs, outputs=model.get_layer("latent_features").output)
tr_feat = extractor.predict(X_tr, verbose=0)
te_feat = extractor.predict(X_te, verbose=0)

svm = SVC(kernel="rbf", probability=True, random_state=42)
svm.fit(tr_feat, y_tr)
print("SVM ok")

print("Testing SHAP...")
exp = shap.KernelExplainer(svm.predict, shap.sample(tr_feat, 20, random_state=42))
sv = exp.shap_values(te_feat[:10])
shap.summary_plot(sv, te_feat[:10], show=False)
plt.tight_layout()
plt.savefig("test_shap.png")
plt.close()
print("SHAP ok")

print("Testing LIME...")
lime_exp_obj = LimeTabularExplainer(tr_feat, class_names=["Ok","Noisy"], mode="classification", random_state=42)
le = lime_exp_obj.explain_instance(te_feat[0], svm.predict_proba, num_features=4)
fig = le.as_pyplot_figure()
plt.tight_layout()
plt.savefig("test_lime.png")
plt.close(fig)
print("LIME ok")
print("ALL TESTS PASSED")
