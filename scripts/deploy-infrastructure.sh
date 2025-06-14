#!/bin/bash

set -e

STACK_NAME="child-allowance-tracker"
REGION="us-east-1"
ENVIRONMENT="production"

echo "Deploying infrastructure..."

aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides Environment=$ENVIRONMENT \
  --capabilities CAPABILITY_IAM \
  --region $REGION

echo "Getting API Gateway URL..."
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
