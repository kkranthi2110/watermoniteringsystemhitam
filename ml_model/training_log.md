# ML Model Training Log

| Experiment | Model | Layers | Units | Dropout | Learning Rate | Epochs | Accuracy | F1 Score | Notes |
|------------|-------|--------|-------|---------|---------------|--------|----------|----------|-------|
| 1 | LSTM | 2 | 64,32 | 0.0 | 0.001 | 20 | 84.13% | 0.629 | Baseline |
| 2 | LSTM | 3 | 128,64,32 | 0.3 | 0.001 | 30 | 83.69% | 0.614 | Deeper with Dropout |
| 3 | CNN | 1 | 64 | 0.0 | 0.001 | 20 | 80.44% | 0.521 | Basic Convolutional |
| 4 | GRU | 2 | 64,32 | 0.0 | 0.001 | 20 | 83.28% | 0.587 | Basic GRU |
