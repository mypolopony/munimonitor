variable "project_name" {
  type        = string
  description = "The name of the project"
  default     = "GTFS-Realtime"
}

variable "aws_region" {
  type        = string
  description = "The AWS region name"
  default     = "us-west-2"
}

variable "database_name" {
  type        = string
  description = "The Timeshare DB name"
  default     = "gtfs_data"
}

variable "table_name" {
  type        = string
  description = "The Timeshare table name"
  default     = "vehicle_positions"
}