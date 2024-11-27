import os
import boto3
import logging
import json
from google.transit import gtfs_realtime_pb2
from base64 import b64decode

# Timestream client
timestream_client = boto3.client("timestream-write", region_name=os.getenv("AWS_REGION"))

# Timestream settings
DATABASE_NAME = os.getenv("TIMESTREAM_DATABASE")
TABLE_NAME = "vehicle_positions"

# Configure the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.info(f"Sending to database: {DATABASE_NAME}")

def process_kinesis_event(event, context):
    logger.info("Received event: %s", json.dumps(event))

    for record in event["Records"]:
        # Decode Kinesis data
        data = b64decode(record["kinesis"]["data"])

        logger.info("Processing record: %s", data)

        # Parse GTFS data
        feed_entity = gtfs_realtime_pb2.FeedEntity()
        feed_entity.ParseFromString(data)

        # Extract data from the GTFS entity with defaults if blank
        vehicle_id = feed_entity.vehicle.vehicle.id or "unknown_vehicle"
        trip_id = feed_entity.vehicle.trip.trip_id or "unknown_trip_id"
        route_id = feed_entity.vehicle.trip.route_id or "unknown_route_id"
        latitude = feed_entity.vehicle.position.latitude or 0.0
        longitude = feed_entity.vehicle.position.longitude or 0.0
        timestamp = int(feed_entity.vehicle.timestamp)
        speed = feed_entity.vehicle.position.speed if feed_entity.vehicle.position.speed else 0.0

        # Write to Timestream
        timestream_client.write_records(
            DatabaseName=DATABASE_NAME,
            TableName=TABLE_NAME,
            Records=[
                {
                    "Dimensions": [
                        {"Name": "vehicle_id", "Value": vehicle_id},
                        {"Name": "route_id", "Value": route_id},
                        {"Name": "trip_id", "Value": trip_id}
                    ],
                    "MeasureName": "vehicle_data",
                    "MeasureValues": [
                        {"Name": "latitude", "Value": str(latitude), "Type": "DOUBLE"},
                        {"Name": "longitude", "Value": str(longitude), "Type": "DOUBLE"},
                        {"Name": "speed", "Value": str(speed), "Type": "DOUBLE"}
                    ],
                    "MeasureValueType": "MULTI",
                    "Time": str(timestamp * 1000)  # Timestream expects time in milliseconds
                }
            ]
        )