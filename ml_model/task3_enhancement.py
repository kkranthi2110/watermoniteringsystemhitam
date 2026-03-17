import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Conv1D, MaxPooling1D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical
from sklearn.metrics import accuracy_score, f1_score

# Configuration
BASE_DIR = Path("c:/Users/Lenovo/OneDrive/Desktop/iiit(sw)/College-Research-Affiliate-Program-26/ml_model")
DATA_PATH = BASE_DIR / "water_dissegration_data.csv"
SAVE_DIR = BASE_DIR / "saved_models"
SAVE_DIR.mkdir(exist_ok=True)
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
    # Ensure Timestamp is datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    for source_name, grp in df.groupby("source_file"):
        g = grp.sort_values("Timestamp").copy().set_index("Timestamp")
        # Resample to 10s intervals
        r = g.resample("10s").agg({"distance": "mean", "label": mode_or_nan})
        r["distance"] = r["distance"].interpolate().bfill().ffill()
        r["label"] = r["label"].ffill().bfill()
        
        # Signal cleaning
        r["distance_clean"] = simple_outlier_correction(r["distance"])
        # Low-pass filter (rolling mean)
        r["distance_lp"] = r["distance_clean"].rolling(window=3, center=True, min_periods=1).mean()
        # Slope
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

print("Loading data...")
df = pd.read_csv(DATA_PATH)
if "source_file" not in df.columns:
    df["source_file"] = "water_dissegration_data.csv"

# Label cleaning
label_map = {"no activity": "no_activity", "no-activity": "no_activity", "washing machine": "washing_machine", "washing-machine": "washing_machine"}
df["label"] = df["label"].astype(str).str.strip().str.lower().replace(label_map)

print("Preprocessing...")
proc_df = preprocess_data(df)
X, y = build_windows(proc_df, WINDOW_SIZE, STEP_SIZE)

le = LabelEncoder()
y_enc = le.fit_transform(y)
y_cat = to_categorical(y_enc)
num_classes = len(le.classes_)

X_train, X_test, y_train, y_test = train_test_split(X, y_cat, test_size=0.2, random_state=RANDOM_STATE, stratify=y_enc)

experiments = []

def log_experiment(name, model_type, layers, units, dropout, lr, epochs, acc, f1, notes):
    experiments.append({
        "Experiment": len(experiments) + 1,
        "Model": model_type,
        "Layers": layers,
        "Units": units,
        "Dropout": dropout,
        "Learning Rate": lr,
        "Epochs": epochs,
        "Accuracy": f"{acc*100:.2f}%",
        "F1": f"{f1:.3f}",
        "Notes": notes
    })

# --- Experiment 1: Baseline LSTM ---
print("\nRunning Experiment 1: Baseline LSTM")
model1 = Sequential([
    LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE, 2)),
    LSTM(32),
    Dense(num_classes, activation='softmax')
])
model1.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model1.fit(X_train, y_train, epochs=8, batch_size=64, verbose=1, validation_split=0.1, callbacks=[EarlyStopping(patience=3)])
loss, acc = model1.evaluate(X_test, y_test, verbose=0)
y_pred = np.argmax(model1.predict(X_test), axis=1)
f1 = f1_score(np.argmax(y_test, axis=1), y_pred, average='macro')
log_experiment(1, "LSTM", 2, "64,32", 0.0, 0.001, 20, acc, f1, "Baseline")

# --- Experiment 2: Enhanced LSTM ---
print("Running Experiment 2: Enhanced LSTM")
model2 = Sequential([
    LSTM(128, return_sequences=True, input_shape=(WINDOW_SIZE, 2)),
    Dropout(0.3),
    LSTM(64, return_sequences=True),
    Dropout(0.2),
    LSTM(32),
    Dense(64, activation='relu'),
    Dense(num_classes, activation='softmax')
])
model2.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model2.fit(X_train, y_train, epochs=10, batch_size=64, verbose=1, validation_split=0.1, callbacks=[EarlyStopping(patience=5)])
loss2, acc2 = model2.evaluate(X_test, y_test, verbose=0)
y_pred2 = np.argmax(model2.predict(X_test), axis=1)
f1_2 = f1_score(np.argmax(y_test, axis=1), y_pred2, average='macro')
log_experiment(2, "LSTM", 3, "128,64,32", 0.3, 0.001, 30, acc2, f1_2, "Deeper with Dropout")

# --- Experiment 3: CNN ---
print("Running Experiment 3: CNN")
model3 = Sequential([
    Conv1D(64, kernel_size=3, activation='relu', input_shape=(WINDOW_SIZE, 2)),
    MaxPooling1D(pool_size=2),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(num_classes, activation='softmax')
])
model3.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model3.fit(X_train, y_train, epochs=5, batch_size=64, verbose=1, validation_split=0.1, callbacks=[EarlyStopping(patience=3)])
loss3, acc3 = model3.evaluate(X_test, y_test, verbose=0)
y_pred3 = np.argmax(model3.predict(X_test), axis=1)
f1_3 = f1_score(np.argmax(y_test, axis=1), y_pred3, average='macro')
log_experiment(3, "CNN", 1, "64", 0.0, 0.001, 20, acc3, f1_3, "Basic Convolutional")

# --- Experiment 4: GRU ---
print("Running Experiment 4: GRU")
model4 = Sequential([
    GRU(64, return_sequences=True, input_shape=(WINDOW_SIZE, 2)),
    GRU(32),
    Dense(num_classes, activation='softmax')
])
model4.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
model4.fit(X_train, y_train, epochs=5, batch_size=64, verbose=1, validation_split=0.1, callbacks=[EarlyStopping(patience=3)])
loss4, acc4 = model4.evaluate(X_test, y_test, verbose=0)
y_pred4 = np.argmax(model4.predict(X_test), axis=1)
f1_4 = f1_score(np.argmax(y_test, axis=1), y_pred4, average='macro')
log_experiment(4, "GRU", 2, "64,32", 0.0, 0.001, 20, acc4, f1_4, "Basic GRU")

# Find best model
best_idx = np.argmax([e['Accuracy'] for e in experiments])
best_model_info = experiments[best_idx]
print(f"\nBest Experiment: {best_model_info['Experiment']} ({best_model_info['Model']}) Accuracy: {best_model_info['Accuracy']}")

if best_idx == 0: best_model = model1
elif best_idx == 1: best_model = model2
elif best_idx == 2: best_model = model3
else: best_model = model4

# Save best model
best_model.save(SAVE_DIR / "best_model.h5")
print(f"Saved best model to {SAVE_DIR / 'best_model.h5'}")

# Also save classes and label encoder details for backend
with open(BASE_DIR / "model_info.txt", "w") as f:
    f.write(f"Classes: {list(le.classes_)}\n")
    f.write(f"Accuracy: {best_model_info['Accuracy']}\n")
    f.write(f"F1: {best_model_info['F1']}\n")

# Generate Markdown Log
log_path = BASE_DIR / "training_log.md"
with open(log_path, "w") as f:
    f.write("# 📊 ML Model Training Log\n\n")
    f.write("| Experiment | Model | Layers | Units | Dropout | Learning Rate | Epochs | Accuracy | F1 Score | Notes |\n")
    f.write("|------------|-------|--------|-------|---------|---------------|--------|----------|----------|-------|\n")
    for e in experiments:
        f.write(f"| {e['Experiment']} | {e['Model']} | {e['Layers']} | {e['Units']} | {e['Dropout']} | {e['Learning Rate']} | {e['Epochs']} | {e['Accuracy']} | {e['F1']} | {e['Notes']} |\n")

print(f"Training log generated at {log_path}")
