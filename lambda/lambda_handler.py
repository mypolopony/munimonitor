import json
import logging
from vehicle_locations import fetch_and_push_to_kinesis  # Import your logic
from kinesis_handler import process_kinesis_event  # Existing handler logic

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Determine the source of the event
    event_source = event.get("source", "")
    
    if event_source == "aws.events":  # EventBridge-triggered task
        logger.info(f"Triggered by EventBridge. Event: {event}.")
        fetch_and_push_to_kinesis()
        return {"statusCode": 200, "body": json.dumps("Vehicle locations processed.")}
    elif "Records" in event:  # Kinesis-triggered task
        logger.info(f"Triggered by Kinesis to process event. Event: {event}.")
        process_kinesis_event(event, context)
        return {"statusCode": 200, "body": json.dumps("Kinesis events processed.")}
    else:
        logger.error(f"Unknown event source. Event: {event}.")
        return {"statusCode": 400, "body": json.dumps("Unknown event source.")}