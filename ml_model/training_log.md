# ML Model Training Log

| Experiment | Model | Layers | Units | Dropout | Learning Rate | Epochs | Accuracy | F1 Score | Notes |
|------------|-------|--------|-------|---------|---------------|--------|----------|----------|-------|
| 1 | LSTM | 2 | 64,32 | 0.0 | 0.001 | 50 | 86.15% | 0.675 | Baseline |
| 2 | LSTM | 3 | 192,128,32 | 0.25 | 0.0008 | 80 | 88.29% | 0.801 | Bidirectional + BatchNorm |
| 3 | CNN | 3 | 64,128,64 | 0.25 | 0.001 | 80 | 84.86% | 0.619 | Deep CNN + BatchNorm + GAP |
| 4 | GRU | 3 | 96,64,32 | 0.2 | 0.001 | 80 | 92.66% | 0.884 | Enhanced GRU + BatchNorm ⭐ |
| 5 | CNN-LSTM | 4 | 64,64,64,48 | 0.2 | 0.001 | 80 | 85.92% | 0.711 | CNN-LSTM Hybrid |
