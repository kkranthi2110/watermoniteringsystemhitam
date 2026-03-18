import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM, GRU, Conv1D, MaxPooling1D, GlobalAveragePooling1D,
    Flatten, Dense, Dropout, BatchNormalization, Bidirectional
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.utils import to_categorical
from sklearn.metrics import accuracy_score, f1_score
import shutil

# Configuration
BASE_DIR = Path("c:/Users/Lenovo/OneDrive/Desktop/iiit(sw)/College-Research-Affiliate-Program-26/ml_model")
DATA_PATH = BASE_DIR / "water_dissegration_data.csv"
SAVE_DIR = BASE_DIR / "saved_models"
BACKEND_SAVE_DIR = Path("c:/Users/Lenovo/OneDrive/Desktop/iiit(sw)/College-Research-Affiliate-Program-26/backend/saved_models")
SAVE_DIR.mkdir(exist_ok=True)
BACKEND_SAVE_DIR.mkdir(exist_ok=True)
RANDOM_STATE = 42
WINDOW_SIZE = 30
STEP_SIZE = 10

def mode_or_nan(series):
    m = series.mode(dropna=True)
    return m.iloc[0] if len(m) > 0 else np.nan

def simple_outlier_correction(signal, z_thresh=3.0, window=50):
    signal = signal.astype(float).interpolate().bfill().ffill()
    rolling_median = signal.rolling(window=window, center=True, min_periods=1).median()
    rolling_mad = (signal - rolling_median).abs().rolling(window=window, center=True, min_periods=1).median()
    rolling_mad = rolling_mad.replace(0, rolling_mad.mean())
    modified_z = 0.6745 * (signal - rolling_median) / rolling_mad
    outliers = np.abs(modified_z) > z_thresh
    corrected = signal.copy()
    corrected[outliers] = rolling_median[outliers]
    return corrected

def preprocess_data(df):
    processed = []
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    for source_name, grp in df.groupby("source_file"):
        g = grp.sort_values("Timestamp").copy().set_index("Timestamp")
        r = g.resample("10s").agg({"distance": "mean", "label": mode_or_nan})
        r["distance"] = r["distance"].interpolate().bfill().ffill()
        r["label"] = r["label"].ffill().bfill()
        
        r["distance_clean"] = simple_outlier_correction(r["distance"])
        r["distance_lp"] = r["distance_clean"].rolling(window=3, center=True, min_periods=1).mean()
        r["slope"] = r["distance_lp"].diff().fillna(0.0)
        
        r["source_file"] = source_name
        processed.append(r.reset_index())
    
    final = pd.concat(processed, ignore_index=True)
    return final.dropna(subset=["distance_lp", "slope", "label"])

def build_windows(df, window_size=30, step=10):
    X, y = [], []
    for _, grp in df.groupby("source_file"):
        levels = grp["distance_lp"].to_numpy()
        slopes = grp["slope"].to_numpy()
        labels = grp["label"].to_numpy()
        
        for start in range(0, len(grp) - window_size + 1, step):
            X.append(np.stack([levels[start:start+window_size], slopes[start:start+window_size]], axis=-1))
            y.append(pd.Series(labels[start:start+window_size]).mode().iloc[0])
    return np.array(X), np.array(y)

print("=" * 60)
print("  ML Model Enhancement - Hyperparameter Tuning")
print("=" * 60)

print("\nLoading data...")
df = pd.read_csv(DATA_PATH)
if "source_file" not in df.columns:
    df["source_file"] = "water_dissegration_data.csv"

# Label cleaning
label_map = {
    "no activity": "no_activity", "no-activity": "no_activity",
    "washing machine": "washing_machine", "washing-machine": "washing_machine"
}
df["label"] = df["label"].astype(str).str.strip().str.lower().replace(label_map)

print("Preprocessing...")
proc_df = preprocess_data(df)
X, y = build_windows(proc_df, WINDOW_SIZE, STEP_SIZE)

le = LabelEncoder()
y_enc = le.fit_transform(y)
y_cat = to_categorical(y_enc)
num_classes = len(le.classes_)

print(f"Dataset: {X.shape[0]} samples, {num_classes} classes: {list(le.classes_)}")
print(f"Input shape: {X.shape[1:]}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y_cat, test_size=0.2, random_state=RANDOM_STATE, stratify=y_enc
)

experiments = []

def evaluate_and_log(model, name, model_type, layers, units, dropout, lr, epochs, notes):
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
    f1 = f1_score(np.argmax(y_test, axis=1), y_pred, average='macro')
    
    exp = {
        "Experiment": len(experiments) + 1,
        "Model": model_type,
        "Layers": layers,
        "Units": units,
        "Dropout": dropout,
        "Learning Rate": lr,
        "Epochs": epochs,
        "Accuracy": acc,
        "Accuracy_str": f"{acc*100:.2f}%",
        "F1": f1,
        "F1_str": f"{f1:.3f}",
        "Notes": notes
    }
    experiments.append(exp)
    print(f"  -> Accuracy: {acc*100:.2f}%, F1: {f1:.3f}")
    return acc

# Common callbacks
def get_callbacks(patience_es=8, patience_lr=4):
    return [
        EarlyStopping(monitor='val_loss', patience=patience_es, restore_best_weights=True, verbose=0),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=patience_lr, min_lr=1e-6, verbose=0)
    ]

# ============================================================
# Experiment 1: Baseline LSTM (same as before but more epochs)
# ============================================================
print("\n[1/5] Experiment 1: Baseline LSTM")
model1 = Sequential([
    LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE, 2)),
    LSTM(32),
    Dense(num_classes, activation='softmax')
])
model1.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model1.fit(X_train, y_train, epochs=50, batch_size=64, verbose=0,
           validation_split=0.15, callbacks=get_callbacks(patience_es=10, patience_lr=5))
evaluate_and_log(model1, "Baseline LSTM", "LSTM", 2, "64,32", 0.0, 0.001, 50, "Baseline")

# ============================================================
# Experiment 2: Enhanced Bidirectional LSTM with BatchNorm
# ============================================================
print("\n[2/5] Experiment 2: Bidirectional LSTM + BatchNorm")
model2 = Sequential([
    Bidirectional(LSTM(96, return_sequences=True), input_shape=(WINDOW_SIZE, 2)),
    BatchNormalization(),
    Dropout(0.25),
    Bidirectional(LSTM(64, return_sequences=True)),
    BatchNormalization(),
    Dropout(0.2),
    LSTM(32),
    Dense(64, activation='relu'),
    BatchNormalization(),
    Dropout(0.15),
    Dense(num_classes, activation='softmax')
])
model2.compile(optimizer=Adam(learning_rate=0.0008), loss='categorical_crossentropy', metrics=['accuracy'])
model2.fit(X_train, y_train, epochs=80, batch_size=32, verbose=0,
           validation_split=0.15, callbacks=get_callbacks(patience_es=12, patience_lr=5))
evaluate_and_log(model2, "Bi-LSTM", "LSTM", 3, "192,128,32", 0.25, 0.0008, 80, "Bidirectional + BatchNorm")

# ============================================================
# Experiment 3: CNN with BatchNorm and deeper architecture
# ============================================================
print("\n[3/5] Experiment 3: Deep CNN + BatchNorm")
model3 = Sequential([
    Conv1D(64, kernel_size=3, activation='relu', padding='same', input_shape=(WINDOW_SIZE, 2)),
    BatchNormalization(),
    Conv1D(128, kernel_size=3, activation='relu', padding='same'),
    BatchNormalization(),
    MaxPooling1D(pool_size=2),
    Dropout(0.25),
    Conv1D(64, kernel_size=3, activation='relu', padding='same'),
    BatchNormalization(),
    GlobalAveragePooling1D(),
    Dense(64, activation='relu'),
    Dropout(0.2),
    Dense(num_classes, activation='softmax')
])
model3.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model3.fit(X_train, y_train, epochs=80, batch_size=32, verbose=0,
           validation_split=0.15, callbacks=get_callbacks(patience_es=12, patience_lr=5))
evaluate_and_log(model3, "Deep CNN", "CNN", 3, "64,128,64", 0.25, 0.001, 80, "Deep CNN + BatchNorm + GAP")

# ============================================================
# Experiment 4: GRU with Dropout and more units
# ============================================================
print("\n[4/5] Experiment 4: Enhanced GRU")
model4 = Sequential([
    GRU(96, return_sequences=True, input_shape=(WINDOW_SIZE, 2)),
    BatchNormalization(),
    Dropout(0.2),
    GRU(64, return_sequences=True),
    Dropout(0.15),
    GRU(32),
    Dense(48, activation='relu'),
    Dropout(0.1),
    Dense(num_classes, activation='softmax')
])
model4.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model4.fit(X_train, y_train, epochs=80, batch_size=32, verbose=0,
           validation_split=0.15, callbacks=get_callbacks(patience_es=12, patience_lr=5))
evaluate_and_log(model4, "Enhanced GRU", "GRU", 3, "96,64,32", 0.2, 0.001, 80, "Enhanced GRU + BatchNorm")

# ============================================================
# Experiment 5: CNN-LSTM Hybrid
# ============================================================
print("\n[5/5] Experiment 5: CNN-LSTM Hybrid")
model5 = Sequential([
    Conv1D(64, kernel_size=3, activation='relu', padding='same', input_shape=(WINDOW_SIZE, 2)),
    BatchNormalization(),
    Conv1D(64, kernel_size=3, activation='relu', padding='same'),
    BatchNormalization(),
    MaxPooling1D(pool_size=2),
    Dropout(0.2),
    LSTM(64, return_sequences=False),
    Dense(48, activation='relu'),
    Dropout(0.15),
    Dense(num_classes, activation='softmax')
])
model5.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model5.fit(X_train, y_train, epochs=80, batch_size=32, verbose=0,
           validation_split=0.15, callbacks=get_callbacks(patience_es=12, patience_lr=5))
evaluate_and_log(model5, "CNN-LSTM Hybrid", "CNN-LSTM", 4, "64,64,64,48", 0.2, 0.001, 80, "CNN-LSTM Hybrid")

# ============================================================
# Find and save best model
# ============================================================
print("\n" + "=" * 60)
print("  RESULTS SUMMARY")
print("=" * 60)

for e in experiments:
    marker = " ★" if e["Accuracy"] == max(exp["Accuracy"] for exp in experiments) else ""
    print(f"  Exp {e['Experiment']}: {e['Model']:12s} → Accuracy: {e['Accuracy_str']:8s}  F1: {e['F1_str']}{marker}")

best_idx = np.argmax([e["Accuracy"] for e in experiments])
best_exp = experiments[best_idx]
print(f"\n✅ Best: Experiment {best_exp['Experiment']} ({best_exp['Model']}) with {best_exp['Accuracy_str']} accuracy")

models = [model1, model2, model3, model4, model5]
best_model = models[best_idx]

# Save best model to both locations
best_model.save(SAVE_DIR / "best_model.h5")
print(f"Saved to {SAVE_DIR / 'best_model.h5'}")

shutil.copy(SAVE_DIR / "best_model.h5", BACKEND_SAVE_DIR / "best_model.h5")
print(f"Copied to {BACKEND_SAVE_DIR / 'best_model.h5'}")

# Save model info
with open(BASE_DIR / "model_info.txt", "w", encoding="utf-8") as f:
    f.write(f"Classes: {list(le.classes_)}\n")
    f.write(f"Best Model: Experiment {best_exp['Experiment']} ({best_exp['Model']})\n")
    f.write(f"Accuracy: {best_exp['Accuracy_str']}\n")
    f.write(f"F1: {best_exp['F1_str']}\n")
    f.write(f"Notes: {best_exp['Notes']}\n")

# Generate Markdown Log
log_path = BASE_DIR / "training_log.md"
with open(log_path, "w", encoding="utf-8") as f:
    f.write("# ML Model Training Log\n\n")
    f.write("| Experiment | Model | Layers | Units | Dropout | Learning Rate | Epochs | Accuracy | F1 Score | Notes |\n")
    f.write("|------------|-------|--------|-------|---------|---------------|--------|----------|----------|-------|\n")
    for e in experiments:
        best_marker = " ⭐" if e["Experiment"] == best_exp["Experiment"] else ""
        f.write(f"| {e['Experiment']} | {e['Model']} | {e['Layers']} | {e['Units']} | {e['Dropout']} | {e['Learning Rate']} | {e['Epochs']} | {e['Accuracy_str']} | {e['F1_str']} | {e['Notes']}{best_marker} |\n")

print(f"\nTraining log saved to {log_path}")
print("\nDone! 🎉")
