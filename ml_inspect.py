import joblib
from pathlib import Path
path = Path('machine-learning/models/hybrid_model.pkl')

bundle = joblib.load(path)
print('bundle keys:', list(bundle.keys()))
print('target:', bundle.get('target_column'))
print('feature_columns:')
for c in bundle.get('feature_columns', []):
    print('-', c)
