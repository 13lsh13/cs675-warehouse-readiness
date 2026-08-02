terraform {
  required_version = ">= 1.6.0"
  required_providers { aws = { source = "hashicorp/aws"; version = "~> 5.0" } }
}

provider "aws" { region = var.aws_region }

resource "aws_s3_bucket" "data" { bucket = var.bucket_name }
resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}

resource "aws_glue_catalog_database" "curated" { name = "cs675_curated" }

resource "aws_athena_workgroup" "analytics" {
  name = "${var.project_name}-athena"
  configuration {
    enforce_workgroup_configuration = true
    result_configuration { output_location = "s3://${aws_s3_bucket.data.bucket}/athena-results/" }
  }
}

data "aws_iam_policy_document" "emr_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals { type = "Service"; identifiers = ["emr-serverless.amazonaws.com"] }
  }
}
resource "aws_iam_role" "emr_job" {
  name = "${var.project_name}-emr-job-role"
  assume_role_policy = data.aws_iam_policy_document.emr_assume.json
}
resource "aws_iam_role_policy" "emr_data" {
  role = aws_iam_role.emr_job.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "glue:GetDatabase", "glue:GetTable", "glue:CreateTable", "glue:UpdateTable"],
    Resource = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*", aws_glue_catalog_database.curated.arn, "arn:aws:glue:${var.aws_region}:*:catalog", "arn:aws:glue:${var.aws_region}:*:table/cs675_curated/*"]
  }] })
}

resource "aws_emrserverless_application" "spark" {
  name = "${var.project_name}-spark"
  release_label = "emr-7.1.0"
  type = "spark"
  auto_stop_configuration { enabled = true; idle_timeout_minutes = 15 }
}

output "bucket" { value = aws_s3_bucket.data.bucket }
output "emr_application_id" { value = aws_emrserverless_application.spark.id }
output "emr_job_role_arn" { value = aws_iam_role.emr_job.arn }
