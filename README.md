Ingesting GTFS with AWS

*In Heavy Development*

# Description

511.org provides GTFS and GTFS-Realtime (Trip Updates, Vehicle Positions, Service Alerts) feeds of transportation providers in the region. We can use those streams to demonstrate a number of functionalities, for example:
- storage and retrieval of historical data (via TimeStream database) for querying and model building
- streaming analysis (anomaly detection)

# Pineline Architecture

**EventBridge**: Drives the pipeline periodically
**Lambda** (*push_to_kinesis*): Responds to the EventBridge and makes an API request from 511. It receives data in protobuf format and pushes it to Kinesis
**Kinesis**: Receives the raw data and triggers Lambda
**Lambda** (*process_process_kinesis_event*): Decodes the data and sends to structured **TimeStream** database

# Querying



# Makefile

A Makefile is included to facilitate deployment, including packaging the lambda and applying the Terraform configuration

### Implementation Reminders

#### Lambda: Add the layers
Some libraries, like `requests` and `gtfs-realtime-bindings` need to be added to the lambda in order to import these functionalities. In general, the pattern to install locally, upload the layer, and then refer to them in Terraform is as follows:

```bash
cd lambda
mkdir python
pip install gtfs-realtime-bindings -t lambda_layer/python
zip -r layer.zip python
aws lambda publish-layer-version \
	--region [AWS_REGION]
    --layer-name gtfs-realtime-layer \
    --compatible-runtimes python3.9 \
    --zip-file fileb://layer.zip
```

And then add to `resource "aws_lambda_function" "kinesis_lambda"`:
```
layers = [
    "arn:aws:lambda:us-west-1:123456789012:layer:gtfs-realtime-layer:1" # Replace with your Layer ARN
  ]
```