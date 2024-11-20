provider "aws" {
  region = var.aws_region
}

# Create Kinesis Stream
resource "aws_kinesis_stream" "gtfs-muni" {
  name             = "gtfs-muni"
  shard_count      = 1  # Adjust the number of shards based on your expected data volume
  retention_period = 24 # Retention period in hours (default is 24)

  # Enhanced monitoring
  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "ReadProvisionedThroughputExceeded",
    "WriteProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds"
  ]

  tags = {
    Environment = "Development"
    Project     = var.project_name
  }
}

# Create Timestream Database
resource "aws_timestreamwrite_database" "gtfs_database" {
  database_name = var.database_name
  tags = {
    Environment = "Development"
    Project     = var.project_name
  }
}

# Create Timestream Table
resource "aws_timestreamwrite_table" "vehicle_positions_table" {
  database_name = aws_timestreamwrite_database.gtfs_database.database_name
  table_name    = var.table_name

  retention_properties {
    memory_store_retention_period_in_hours  = 24   # Data stays in memory for 1 day
    magnetic_store_retention_period_in_days = 365  # Data stays in storage for 1 year
  }

  tags = {
    Environment = "Development"
    Project     = var.project_name
  }
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda-kinesis-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach Policies to the Lambda Execution Role
resource "aws_iam_policy" "lambda_kinesis_policy" {
  name = "lambda-kinesis-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:ListStreams",
          "kinesis:PutRecord"
        ],
        Effect   = "Allow",
        Resource = aws_kinesis_stream.gtfs-muni.arn
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "cloudwatch:PutMetricData"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "timestream:DescribeEndpoints",
          "timestream:WriteRecords"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_kinesis_policy.arn
}

# Create the Lambda Function
resource "aws_lambda_function" "gtfs-lambda" {
  function_name = "gtfs-combined-handler"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.9"

  # Path to the Lambda deployment package  (ZIP file)
  filename = "../lambda/lambda.zip"

  # Ensure we check the contents to detect changes
  source_code_hash = filebase64sha256("../lambda/lambda.zip")

  # Environment Variables
  environment {
    variables = {
      TIMESTREAM_DATABASE = aws_timestreamwrite_database.gtfs_database.database_name
      KINESIS_STREAM_NAME = aws_kinesis_stream.gtfs-muni.name
      REGION_NAME = var.aws_region
    }
  }

  # Add extra layers
  layers = [
    "arn:aws:lambda:us-west-2:897729117324:layer:gtfs-realtime-layer:1",
    "arn:aws:lambda:us-west-2:897729117324:layer:requests-layer:1"
  ]

  # Lambda Timeout and Memory
  timeout      = 30
  memory_size  = 128
}

# Cloudwatch Log Group
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.gtfs-lambda.function_name}"
  retention_in_days = 7 # Retain logs for 7 days (adjust as needed)
  tags = {
    Environment = "Development"
  }
}

# Cloudwatch IAM Policy
resource "aws_iam_policy" "lambda_cloudwatch_policy" {
  name = "lambda-cloudwatch-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:*:*:*" # Allows access to all CloudWatch Logs (can be scoped down)
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_cloudwatch_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_cloudwatch_policy.arn
}

# Create the Event Source Mapping (Link Kinesis to Lambda)
resource "aws_lambda_event_source_mapping" "kinesis_to_lambda" {
  event_source_arn = aws_kinesis_stream.gtfs-muni.arn
  function_name    = aws_lambda_function.gtfs-lambda.arn
  starting_position = "LATEST" # Options: TRIM_HORIZON, LATEST
}

# Eventbridge
resource "aws_cloudwatch_event_rule" "schedule_rule" {
  name                = "vehicle-locations-schedule"
  schedule_expression = "rate(2 minutes)"  # Adjust the schedule as needed
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.schedule_rule.name
  arn       = aws_lambda_function.gtfs-lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gtfs-lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule_rule.arn
}

output "timestream_table_arn" {
  value = aws_timestreamwrite_table.vehicle_positions_table.arn
}

output "kinesis_stream_arn" {
  value = aws_kinesis_stream.gtfs-muni.arn
}