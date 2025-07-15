import joblib
import logging
import pandas as pd
import numpy as np 


#Setting up the logger configuration 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



logging.info("data has been loaded successfully")
df=joblib.load("df.pkl")

def feature_engineer(df):
    # Step 1: Calculate mode (most frequent asset symbol)
    most_common_asset = df.loc[df['assetSymbol'] != '', 'assetSymbol'].mode().iloc[0]
    # Step 2: Replace '' with mode
    df['assetSymbol'] = df['assetSymbol'].replace('', most_common_asset)

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['assetPriceUSD'] = pd.to_numeric(df['assetPriceUSD'], errors='coerce')

    # Calculate USD value
    df['usd_value'] = df['amount'] * df['assetPriceUSD']
    df.drop(['amount', 'assetPriceUSD'], axis=1, inplace=True)

    # made a final list of columns which we have to drop 
    columns_to_drop = [
        '_id',  # internally MongoDB generated ID
        'network',  # always having the same value
        'protocol',  # always having the same value
        'txHash',  # not useful
        'logId',  # not useful for analysis
        'blockNumber',  # same as timestamp
        'action_type',  # same as action
        'amount_raw',  # already processed as amount
        'poolId',  # pool contract address
        'userId',  # already made userWallet
        '__v',  # MongoDB version ID
        'createdAt',  # internal metadata
        'updatedAt' # internal metadata
    ]
    logging.info("dataset is the the name of the dataset which is made by removing all the listed columns ")
    dataset=df.drop(columns_to_drop,axis=1)


    # Now extracting some common features

    most_used_asset = dataset.groupby("userWallet")["assetSymbol"].agg(lambda x: x.mode())
    logging.info(f"The most used asset used by the each customer are as follows  {most_used_asset}")

    asset_usage = dataset.groupby("assetSymbol")["usd_value"].sum().sort_values(ascending=False)
    num_unique_assets = dataset.groupby("userWallet")["assetSymbol"].nunique()


    top_deposits = dataset[dataset['action'] == 'deposit'].groupby('assetSymbol')['usd_value'].sum().sort_values(ascending=False)
    top_borrows = dataset[dataset['action'] == 'borrow'].groupby('assetSymbol')['usd_value'].sum().sort_values(ascending=False)
    logging.info(f"the top_deposits and the top_borrows by each assest are  {top_deposits} and {top_borrows}")


    dataset=pd.merge(dataset,most_used_asset.reset_index(),how='left',on='userWallet')
    dataset.drop("assetSymbol_y",axis=1,inplace=True)
    dataset = pd.merge(
        dataset,
        num_unique_assets.reset_index(),
        on="userWallet",
        how='left',
        suffixes=('', '_drop')  # avoids duplicate column error
    )
    dataset.rename(columns={
        'assetSymbol': 'Most_Assest_Used ',
        'assetSymbol_drop': 'Unique_Assest_Used'
    }, inplace=True)

    dataset.drop("assetSymbol_x",axis=1,inplace=True)
    logging.info("The features regarding the assests are generated successfully")





    # Step 2: Group by userWallet and create features
    group = dataset.groupby("userWallet")

    wallet_features = group.agg(
        total_transactions=('action', 'count'),
        num_deposits=('action', lambda x: (x == 'deposit').sum()),
        num_borrows=('action', lambda x: (x == 'borrow').sum()),
        num_repays=('action', lambda x: (x == 'repay').sum()),
        num_liquidations=('action', lambda x: (x == 'liquidationcall').sum()),
        num_redeems=('action', lambda x: (x == 'redeemunderlying').sum()),
        
        total_deposit_usd=('usd_value', lambda x: x[dataset.loc[x.index, 'action'] == 'deposit'].sum()),
        total_borrow_usd=('usd_value', lambda x: x[dataset.loc[x.index, 'action'] == 'borrow'].sum()),
        total_repay_usd=('usd_value', lambda x: x[dataset.loc[x.index, 'action'] == 'repay'].sum()),
        total_redeem_usd=('usd_value', lambda x: x[dataset.loc[x.index, 'action'] == 'redeemunderlying'].sum()),
        
        avg_tx_usd=('usd_value', 'mean'),
        std_tx_usd=('usd_value', 'std'),
        
        
        first_tx_timestamp=('timestamp', 'min'),
        last_tx_timestamp=('timestamp', 'max'),
        active_days=('timestamp', lambda x: pd.to_datetime(x, unit='s').dt.date.nunique())
    )

    # Step 3: Derived ratio & risk features
    wallet_features["borrow_to_repay_ratio"] = wallet_features["total_borrow_usd"] / wallet_features["total_repay_usd"].replace(0, np.nan)
    wallet_features["repaid_percentage"] = wallet_features["total_repay_usd"] / wallet_features["total_borrow_usd"].replace(0, np.nan)
    wallet_features["liquidation_ratio"] = wallet_features["num_liquidations"] / wallet_features["num_borrows"].replace(0, np.nan)
    wallet_features["deposit_to_borrow_ratio"] = wallet_features["total_deposit_usd"] / wallet_features["total_borrow_usd"].replace(0, np.nan)
    wallet_features["redeem_to_deposit_ratio"] = wallet_features["total_redeem_usd"] / wallet_features["total_deposit_usd"].replace(0, np.nan)
    wallet_features["net_borrowed"] = wallet_features["total_borrow_usd"] - wallet_features["total_repay_usd"]

    # Step 4: Time since last transaction
    wallet_features["days_since_last_tx"] = (pd.Timestamp.now().timestamp() - wallet_features["last_tx_timestamp"]) / (3600 * 24)

    # Step 5: Final clean-up
    wallet_features.fillna(0, inplace=True)
    wallet_features.reset_index(inplace=True)

    wallet_features = pd.merge(wallet_features, num_unique_assets.reset_index(), on="userWallet", how="left")
    wallet_features = pd.merge(wallet_features, most_used_asset.reset_index(), on="userWallet", how="left")


    # credit score Formula 
    wallet_features['credit_score'] = (
        (wallet_features['repaid_percentage'].clip(0, 1.2) * 400) +
        ((1 - wallet_features['liquidation_ratio'].clip(0, 1)) * 200) +
        (wallet_features['redeem_to_deposit_ratio'].clip(0, 1.5) * 150) +
        (wallet_features['active_days'] / wallet_features['active_days'].max() * 100) +
        ((1 / (1 + wallet_features['days_since_last_tx'])) * 150)
    ).clip(0, 1000)
    joblib.dump(wallet_features,"wallet_features.pkl")
logging.info("The final datset with all the features which are important formed successfully")