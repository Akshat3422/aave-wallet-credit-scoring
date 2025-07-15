# Aave Wallet Credit Scoring

This project builds a machine learning pipeline to score DeFi user wallets based on transaction history from the Aave protocol. It includes data preprocessing, feature engineering, model training, and score prediction.

---

##  Project Workflow

### 1. Data Extraction
- The zipped file `user-wallet-transactions.json.zip` is unzipped.
- JSON transaction data is loaded and flattened into a structured pandas DataFrame.
- Data is stored as `df.pkl`.

### 2. Feature Engineering
Wallet-level features are computed, including:
- **Transaction Counts**: deposits, borrows, repays, redeems, liquidations
- **USD Values**: total deposit, borrow, repay, redeem amounts
- **Ratios**: borrow-to-repay, repay percentage, liquidation ratio, deposit-to-borrow, etc.
- **Time Features**: first and last transaction, days active, days since last transaction
- **Activity**: average and standard deviation of transaction values
- **Most Used Asset** and **Unique Asset Count**

The final wallet-level DataFrame is saved as `wallet_features.pkl`.

### 3. Credit Score Calculation
A synthetic credit score is generated for each wallet using a weighted formula:
credit_score =
(repaid_percentage.clip(0, 1.2) * 400) +
((1 - liquidation_ratio.clip(0, 1)) * 200) +
(redeem_to_deposit_ratio.clip(0, 1.5) * 150) +
(active_days / max(active_days) * 100) +
(1 / (1 + days_since_last_tx) * 150)

### Credit Score Calculation Logic
The credit scoring methodology used in this project is a heuristic model. Instead of being learned from labels or supervised data, the score is derived from predefined behavioral rules and weighted features that reflect responsible or risky user activity on the Aave V2 protocol.
Each wallet is assigned a credit score ranging from 0 to 1000, where higher scores represent more trustworthy and consistent behavior. The score is calculated based on the following key indicators:
`` credit_score = (
    (repaid_percentage.clip(0, 1.2) * 400) +
    ((1 - liquidation_ratio.clip(0, 1)) * 200) +
    (redeem_to_deposit_ratio.clip(0, 1.5) * 150) +
    (active_days / max_active_days * 100) +
    ((1 / (1 + days_since_last_tx)) * 150)
).clip(0, 1000) ``
| Feature                     | Max Weight | Description                                                                                                     |
| --------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| **Repaid Percentage**       | 400        | Measures how much of the borrowed amount was repaid. A higher percentage indicates strong repayment discipline. |
| **Liquidation Ratio**       | 200        | Reflects how often the user was liquidated after borrowing. Lower values imply better risk management.          |
| **Redeem-to-Deposit Ratio** | 150        | Indicates how much of the deposited value the user has responsibly redeemed.                                    |
| **Activity Days**           | 100        | Number of unique days the wallet was active. Normalized to reward consistent engagement.                        |
| **Recency of Transactions** | 150        | Recent wallet activity is favored. More recent = higher score due to ongoing engagement.                        |

## Why Heuristic Scoring?
This approach is transparent, interpretable, and applicable across datasets. It avoids overfitting and provides explainable reasoning for how a score was assigned, which is critical in financial systems. It also reflects typical lending heuristics found in both traditional and decentralized finance.
The score is capped at 1000 to maintain consistency and ease of interpretation.
The score is clipped to fall between 0 and 1000.

### 4. Model Training (XGBoost)
- An XGBoost regression model is trained on the wallet features to predict the credit score.
- Model metrics:
  - R² score
  - Mean Squared Error (MSE)
  - 5-fold cross-validated MSE

The model is used to predict scores for all wallets.

### 5. Output
- Final output file: `wallet_score_output.csv`  
  (contains: `userWallet`, `predicted_score`)
- Visuals:
  - True vs. Predicted Score Scatter Plot
  - Score Distribution Bar Plot (0–1000 buckets)

---

## 🔍 Score Analysis

### Score Buckets:
Wallets are grouped into buckets based on predicted scores:

| Score Range | Wallet Behavior Summary |
|-------------|--------------------------|
| 0–200       | Poor repayment, frequent liquidations, low activity |
| 200–500     | Moderate borrowing with occasional liquidations |
| 500–800     | Balanced activity and healthy repayment behavior |
| 800–1000    | High repayment %, low risk, frequent redemptions |


