import joblib
from sklearn.preprocessing import LabelEncoder
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score,mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.metrics import make_scorer, mean_squared_error



wallet_features=joblib.load("wallet_features.pkl")


wallet_features['assetSymbol_x']=pd.to_numeric(wallet_features['assetSymbol_x'])

# Step 1: Ensure values are strings, even if they're arrays
wallet_features['assetSymbol_y'] = wallet_features['assetSymbol_y'].apply(lambda x: str(x) if isinstance(x, (list, np.ndarray)) else x)

# Step 2: Fill missing values if any
wallet_features['assetSymbol_y'] = wallet_features['assetSymbol_y'].fillna('unknown')

# Step 3: Encode
le = LabelEncoder()
wallet_features['assetSymbol_y'] = le.fit_transform(wallet_features['assetSymbol_y'])


X=wallet_features.drop(["userWallet","credit_score"],axis=1)
y=wallet_features['credit_score']

X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.3,random_state=42)

from xgboost import XGBRegressor
model=XGBRegressor(early_stopping=10)
model.fit(X_train,y_train)

accuracy=model.score(X_test,y_test)
y_pred=model.predict(X_test)

r2=r2_score(y_test,y_pred)
error=mean_squared_error(y_test,y_pred)

print(f"The model has an acccuracy of {accuracy} and also have a r2_score of {r2} with an error of {error}")



import matplotlib.pyplot as plt
plt.scatter(y_test, y_pred, alpha=0.5)
plt.xlabel("True Score")
plt.ylabel("Predicted Score")
plt.title("True vs Predicted Credit Scores")
plt.plot([0, 1000], [0, 1000], 'r--')  # Ideal line
plt.show()



from sklearn.model_selection import cross_val_score
from sklearn.metrics import make_scorer, mean_squared_error

mse_scorer = make_scorer(mean_squared_error)
scores = cross_val_score(model, X, y, cv=5, scoring=mse_scorer)
print("Cross-validated MSE:", scores)

wallet_features['predicted_score'] = model.predict(X)
wallet_features[['userWallet', 'predicted_score']].to_csv("wallet_score_output.csv", index=False)
print("✅ Final credit scores saved to 'wallet_score_output.csv'")
