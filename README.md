# Building a Serverless Child Allowance Tracker with Python and AWS

!!! info "Project Overview"
    A complete serverless application that tracks children's allowances and expenditures using Google Sheets as a data source, built with Flask, AWS Lambda, and GitHub Actions for CI/CD.

## :material-lightbulb: The Problem

Managing children's allowances can be challenging - tracking what they've earned, what they've spent, and maintaining accurate balances. This project solves that by creating a web application that:

- Reads allowance data from Google Sheets
- Tracks expenditures in DynamoDB
- Provides a web interface for viewing balances and adding expenses
- Restricts access to authorized users only

## :material-tools: Tech Stack

=== "Backend"
    - **Python 3.12** with Flask
    - **AWS Lambda** for serverless hosting
    - **DynamoDB** for expenditure storage
    - **Google Sheets API** for allowance data

=== "Infrastructure"
    - **AWS CloudFormation** for infrastructure as code
    - **API Gateway** for HTTP endpoints
    - **GitHub Actions** for CI/CD

=== "Development"
    - **uv** for fast Python package management
    - **pytest** for testing
    - **Material for MkDocs** for documentation

## :material-folder-outline: Project Structure

```
child-allowance-tracker/
├── .github/workflows/
│   └── deploy.yml              # CI/CD pipeline
├── src/
│   ├── app.py                  # Flask application
│   ├── handlers/
│   │   ├── auth.py             # Authentication logic
│   │   ├── calculations.py     # Balance calculations
│   │   └── expenditures.py     # Expense management
│   ├── services/
│   │   ├── google_sheets.py    # Google Sheets integration
│   │   └── database.py         # DynamoDB service
│   └── templates/
│       ├── index.html
│       ├── dashboard.html
│       └── expenditure_form.html
├── infrastructure/
│   └── cloudformation.yaml    # AWS resources
├── scripts/
│   ├── deploy-infrastructure.sh
│   ├── deploy.sh
│   └── dev-setup.sh
├── pyproject.toml             # Project configuration
└── lambda_function.py         # AWS Lambda entry point
```

## :material-rocket: Quick Start

### Prerequisites

- Python 3.12+
- AWS CLI configured
- Google Cloud Platform account
- GitHub account

### 1. Environment Setup

!!! tip "Using uv for Speed"
    This project uses [uv](https://docs.astral.sh/uv/) for blazingly fast Python package management.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <your-repo-url>
cd child-allowance-tracker
chmod +x scripts/*.sh
./scripts/dev-setup.sh
```

### 2. Configure Google Sheets

Create a service account and download the JSON credentials:

```python
# Example Google Sheets structure
# Sheet 1: "Allowance Earned"
Week_Date    | Before Today | child1 | child2 | child3
6/23/2024    | TRUE         | 7      | 8      | 10
6/30/2024    | TRUE         | 7      | 8      | 10

# Sheet 2: "Sheet1" (expenditures)
Who     | Cost | Date       | Description
child1  | 5.00 | 2024-06-25 | Candy
child2  | 3.50 | 2024-06-26 | Toy car
```

### 3. GitHub Secrets Configuration

Set up these secrets in your GitHub repository:

!!! warning "Security First"
    Never commit credentials to your repository. Use GitHub Secrets for all sensitive data.

| Secret Name | Description |
|-------------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Full JSON content of service account |
| `GOOGLE_SHEETS_ID` | Your Google Sheets ID |

## :material-code-braces: Key Components

### Flask Application

The main application handles routing and authentication:

```python title="src/app.py"
from flask import Flask, request, jsonify, render_template
from handlers.auth import is_authorized
from handlers.calculations import calculate_totals
from handlers.expenditures import post_expenditure, get_expenditures

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    totals = calculate_totals()
    return render_template('dashboard.html', totals=totals)

@app.route('/expenditures', methods=['POST'])
def expenditures():
    if not is_authorized(request):
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    amount = data.get('amount')
    description = data.get('description')
    date = data.get('date')
    
    if post_expenditure(amount, description, date):
        return jsonify({"message": "Expenditure posted successfully"}), 201
    else:
        return jsonify({"error": "Failed to post expenditure"}), 400

if __name__ == '__main__':
    app.run(debug=True)
```

### DynamoDB Service

Handles all database operations with proper error handling:

```python title="src/services/database.py"
import boto3
import os
from datetime import datetime
from decimal import Decimal

class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('DYNAMODB_TABLE')
        self.table = self.dynamodb.Table(self.table_name)
    
    def save_expenditure(self, child_name, amount, date, description):
        """Save expenditure to DynamoDB"""
        item = {
            'pk': f'CHILD#{child_name}',
            'sk': f'EXPENDITURE#{datetime.now().isoformat()}',
            'amount': Decimal(str(amount)),
            'date': date,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        self.table.put_item(Item=item)
        return True
    
    def get_total_spent(self, child_name):
        """Calculate total spent by a child"""
        expenditures = self.get_expenditures(child_name)
        return sum(exp['amount'] for exp in expenditures)
```

### Google Sheets Integration

Securely connects to Google Sheets using service account credentials:

```python title="src/services/google_sheets.py"
import gspread
from google.oauth2.service_account import Credentials
import os
import json

class GoogleSheetsService:
    def __init__(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Get credentials from environment variable
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        service_account_info = json.loads(service_account_json)
        
        creds = Credentials.from_service_account_info(
            service_account_info, 
            scopes=scope
        )
        
        self.client = gspread.authorize(creds)
        self.sheet_id = os.environ.get('GOOGLE_SHEETS_ID')
    
    def get_allowance_data(self):
        sheet = self.client.open_by_key(self.sheet_id).worksheet("Allowance Earned")
        return sheet.get_all_records()
    
    def add_expenditure(self, who, cost, date, description):
        sheet = self.client.open_by_key(self.sheet_id).worksheet("Sheet1")
        sheet.append_row([who, cost, date, description])
```

## :material-cloud: Infrastructure as Code

### CloudFormation Template

Define all AWS resources declaratively:

```yaml title="infrastructure/cloudformation.yaml"
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [production, staging]

Resources:
  AllowanceTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'allowance-data-${Environment}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S
        - AttributeName: sk
          AttributeType: S
      KeySchema:
        - AttributeName: pk
          KeyType: HASH
        - AttributeName: sk
          KeyType: RANGE

  ChildAllowanceFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub 'child-allowance-tracker-${Environment}'
      Handler: lambda_function.lambda_handler
      Runtime: python3.12
      Timeout: 30
      MemorySize: 256
      Environment:
        Variables:
          DYNAMODB_TABLE: !Ref AllowanceTable
      Events:
        Api:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

### GitHub Actions CI/CD

Automated testing and deployment:

```yaml title=".github/workflows/deploy.yml"
name: Deploy to AWS Lambda

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v2
      - name: Set up Python
        run: uv python install 3.12
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name child-allowance-tracker \
            --zip-file fileb://deployment.zip
```

## :material-play: Deployment

### Initial Infrastructure Setup

```bash
# Deploy AWS infrastructure
./scripts/deploy-infrastructure.sh
```

### Automated Deployment

Simply push to the main branch:

```bash
git add .
git commit -m "Deploy allowance tracker"
git push origin main
```

!!! success "Deployment Complete"
    GitHub Actions will automatically test and deploy your application to AWS Lambda.

## :material-currency-usd: Cost Optimization

This serverless architecture is designed for minimal costs:

- **AWS Lambda**: Pay only for execution time
- **DynamoDB**: Pay-per-request pricing
- **API Gateway**: Pay per request
- **Total estimated cost**: < $5/month for typical family usage

## :material-chart-line: Features

=== "Authentication"
    - Restricts access to authorized email addresses
    - Secure credential management via environment variables

=== "Data Management"
    - Real-time sync with Google Sheets
    - Persistent expenditure tracking in DynamoDB
    - Automatic balance calculations

=== "User Interface"
    - Clean, responsive web interface
    - Real-time balance updates
    - Simple expenditure entry form

## :material-help: Troubleshooting

??? question "Common Issues"
    
    **Lambda function not updating?**
    ```bash
    # Check function exists
    aws lambda get-function --function-name child-allowance-tracker
    
    # Manual deployment
    ./scripts/deploy.sh
    ```
    
    **Google Sheets access denied?**
    - Verify service account has sheet access
    - Check environment variable format
    
    **DynamoDB permission errors?**
    - Ensure Lambda role has DynamoDB permissions
    - Check table name in environment variables

## :material-rocket-launch: Next Steps

- [ ] Add email notifications for new expenditures
- [ ] Implement spending categories and budgets
- [ ] Create mobile-responsive design
- [ ] Add data export functionality
- [ ] Implement spending analytics dashboard

## :material-account-group: Contributing

Contributions welcome! Please check our [contributing guidelines](CONTRIBUTING.md) and submit a pull request.

## :material-license: License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

!!! tip "Questions?"
    Open an issue on GitHub or reach out to the maintainers for help with setup or customization.