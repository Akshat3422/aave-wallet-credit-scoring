import os 
import json
import zipfile
import logging
import joblib
import pandas as pd

#Setting up the logger configuration 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Unzip the file
try:
    with zipfile.ZipFile("user-wallet-transactions.json.zip", 'r') as file:
        os.makedirs("data", exist_ok=True)
        file.extractall("data/")
        logging.info("Unzipped file successfully into 'data/' folder.")
except FileNotFoundError:
    logging.error("Zip file not found.")
    raise

# Load the JSON data
file_path = r"C:\Users\user\Desktop\Zeru\data\user-wallet-transactions.json"

try:
    with open(file_path, 'r') as f:
        data = json.load(f)
        logging.info("JSON data loaded successfully.")
except FileNotFoundError:
    logging.error(f"JSON file not found at path: {file_path}")
    raise


# creating dataframe from the json object 
flattened_data = []
for tx in data:
    try:
        tx_flat = {
            "_id": tx.get('_id', {}).get('$oid'),
            "userWallet": tx.get('userWallet'),
            "network": tx.get('network'),
            "protocol": tx.get('protocol'),
            "txHash": tx.get('txHash'),
            "logId": tx.get('logId'),
            "timestamp": tx.get('timestamp'),
            "blockNumber": tx.get('blockNumber'),
            "action": tx.get('action'),
            "action_type": tx.get('actionData', {}).get('type'),
            "amount_raw": tx.get('actionData', {}).get('amount'),
            "assetSymbol": tx.get('actionData', {}).get('assetSymbol'),
            "assetPriceUSD": tx.get('actionData', {}).get('assetPriceUSD'),
            "poolId": tx.get('actionData', {}).get('poolId'),
            "userId": tx.get('actionData', {}).get('userId'),
            "__v": tx.get('__v'),
            "createdAt": tx.get('createdAt', {}).get('$date'),
            "updatedAt": tx.get('updatedAt', {}).get('$date')
        }

        # Convert amount and price
        try:
            amount = float(tx_flat["amount_raw"])
        except:
            amount = None
        try:
            price = float(tx_flat["assetPriceUSD"])
        except:
            price = None

        tx_flat["amount"] = amount
        tx_flat["usd_value"] = amount * price if amount and price else None

        flattened_data.append(tx_flat)

    except Exception as e:
        print(f"Error parsing record: {e}")

# Convert to DataFrame
df = pd.DataFrame(flattened_data)
joblib.dump(df,"df.pkl")
logging.info("pickle file of dataframe has been created successfully ")





