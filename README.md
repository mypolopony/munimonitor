Ingesting GTFS with AWS

# Lambda

THe lambda does. . .

#### Reminder: Add the layers
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

# Makefile

A Makefile is included to facilitate deployment, including packaging the lambda and applying the Terraform configuration
