#!/bin/bash
cd ~/finsight
source venv/bin/activate
export AUTH_MODE=cognito
export COGNITO_REGION=us-east-1
export COGNITO_USER_POOL_ID=us-east-1_CwVO01fel
export COGNITO_CLIENT_ID=5vt84f5poh0hqkuqcblvkn45ai
export AWS_DEFAULT_REGION=us-east-1
export FILINGS_BUCKET=vaultsight-filings-370415175142
uvicorn backend.main:app
