import boto3
import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle

# Example usage in your code:
def process_query_response(response: QueryResponse) -> None:
    for row in response["Rows"]:
        print(row)

# Query historical data from Timestream
def fetch_historical_data():
    timestream_query = boto3.client('timestream-query')
    query = """
    SELECT time, route_id, vehicle_id, latitude, longitude, speed
    FROM "YourDatabase"."YourTable"
    WHERE time > ago(7d)
    """
    response = timestream_query.query(QueryString=query)
    rows = response['Rows']
    # Process rows into a Pandas DataFrame
    return pd.DataFrame([dict(zip(response['ColumnInfo'], r['Data'])) for r in rows])

# Train the model
def train_model(data):
    features = data[['latitude', 'longitude', 'speed']]
    model = IsolationForest(contamination=0.01)
    model.fit(features)
    return model

# Save model to S3
def save_model_to_s3(model, bucket_name, model_name):
    s3 = boto3.client('s3')
    with open('/tmp/model.pkl', 'wb') as f:
        pickle.dump(model, f)
    s3.upload_file('/tmp/model.pkl', bucket_name, model_name)

data = fetch_historical_data()
model = train_model(data)
save_model_to_s3(model, 'your-bucket-name', 'anomaly_detection_model.pkl')