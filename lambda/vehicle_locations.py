import os
import boto3
import requests
from google.transit import gtfs_realtime_pb2

# AWS Kinesis Configuration
STREAM_NAME = os.getenv("KINESIS_STREAM_NAME")
kinesis_client = boto3.client("kinesis", region_name=os.getenv("REGION_NAME"))

# GTFS-Realtime Endpoint
gtfs_url = "http://api.511.org/transit/vehiclepositions?api_key=060b6606-efa3-43dc-ba04-7ee51dbaa246&agency=SF"

def fetch_and_push_to_kinesis():
    # Fetch GTFS-Realtime data
    response = requests.get(gtfs_url)
    if response.status_code == 200:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        # Iterate over entity messages and send to Kinesis
        for entity in feed.entity:
            record_data = entity.SerializeToString()  # Serialize the Protobuf message
            kinesis_client.put_record(
                StreamName=STREAM_NAME,
                Data=record_data,
                PartitionKey=entity.id  # Use a unique key to distribute load
            )
            print(f"Sent entity ID {entity.id} to Kinesis")
    else:
        print(f"Failed to fetch GTFS data. Status code: {response.status_code}")

# Run the fetch and send function
if __name__ == "__main__":
    fetch_and_push_to_kinesis()