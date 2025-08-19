# Train simple regression and classification models on synthetic data.
import numpy as np, pickle, os
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

os.makedirs('models', exist_ok=True)

# Synthetic dataset: daily amount -> annual expense (rough) and distress label
np.random.seed(0)
daily = np.random.gamma(2.0, 200.0, 1000)  # simulate daily spends
annual = daily * 365 + np.random.normal(0, 2000, size=daily.shape)
# distress label: 1 if annual > 80000
labels = (annual > 80000).astype(int)

X = daily.reshape(-1,1)
y_reg = annual
y_clf = labels

reg = LinearRegression().fit(X, y_reg)
clf = RandomForestClassifier(n_estimators=50, random_state=0).fit(np.hstack([X, y_reg.reshape(-1,1)]), y_clf)

with open('models/regression_model.pkl','wb') as f:
    pickle.dump(reg, f)
with open('models/classification_model.pkl','wb') as f:
    pickle.dump(clf, f)

print('Models trained and saved to models/')