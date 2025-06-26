# デプロイメントガイド

このガイドでは、HADSアプリケーションをAWS Lambdaにデプロイする方法を詳しく説明します。

## 目次
- [デプロイメント概要](#デプロイメント概要)
- [手動デプロイ](#手動デプロイ)
- [Serverless Framework](#serverless-framework)
- [AWS SAM](#aws-sam)
- [CI/CD パイプライン](#cicd-パイプライン)
- [環境管理](#環境管理)
- [モニタリング設定](#モニタリング設定)
- [トラブルシューティング](#トラブルシューティング)

---

## デプロイメント概要

### デプロイメント方式の比較

| 方式 | 難易度 | 機能 | 推奨用途 |
|------|--------|------|----------|
| 手動デプロイ | 低 | 基本的 | 学習・プロトタイプ |
| Serverless Framework | 中 | 高機能 | 本格的な開発 |
| AWS SAM | 中 | AWS特化 | AWS環境のみ |
| CI/CD | 高 | 自動化 | 本番運用 |

### 必要な準備

1. **AWS アカウント**: アクティブなAWSアカウント
2. **IAM権限**: Lambda、API Gateway、CloudFormationの権限
3. **AWS CLI**: 設定済みのAWS CLI
4. **Python環境**: Python 3.8以上

---

## 手動デプロイ

### 基本的なデプロイ手順

#### 1. デプロイパッケージの作成

```bash
# プロジェクトディレクトリに移動
cd your-hads-project

# 依存関係をインストール
mkdir deployment-package
pip install -r requirements.txt -t deployment-package/

# プロジェクトファイルをコピー
cp -r lib/ deployment-package/
cp handler.py deployment-package/
cp urls.py deployment-package/
cp settings.py deployment-package/

# ZIPファイルを作成
cd deployment-package
zip -r ../deployment-package.zip .
cd ..
```

#### 2. Lambda関数の作成

```bash
# Lambda関数を作成
aws lambda create-function \
    --function-name hads-app \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler handler.main \
    --zip-file fileb://deployment-package.zip \
    --timeout 30 \
    --memory-size 512
```

#### 3. API Gatewayの設定

```bash
# REST APIを作成
aws apigateway create-rest-api --name hads-api

# リソースとメソッドを設定
API_ID="your-api-id"
RESOURCE_ID="your-resource-id"

# プロキシリソースを作成
aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $RESOURCE_ID \
    --path-part "{proxy+}"

# メソッドを作成
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE
```

#### 4. 関数の更新

```bash
# コードを更新
aws lambda update-function-code \
    --function-name hads-app \
    --zip-file fileb://deployment-package.zip
```

---

## Serverless Framework

### セットアップ

```bash
# Serverless Frameworkをインストール
npm install -g serverless

# プロジェクトディレクトリでserverless.ymlを作成
```

### serverless.yml設定

```yaml
# serverless.yml
service: hads-app

frameworkVersion: '3'

provider:
  name: aws
  runtime: python3.9
  stage: ${opt:stage, 'dev'}
  region: ${opt:region, 'us-east-1'}
  memorySize: 512
  timeout: 30
  
  environment:
    STAGE: ${self:provider.stage}
    DATABASE_URL: ${env:DATABASE_URL_${self:provider.stage}}
    
  iamRoleStatements:
    - Effect: Allow
      Action:
        - dynamodb:Query
        - dynamodb:Scan
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:UpdateItem
        - dynamodb:DeleteItem
      Resource: "arn:aws:dynamodb:${self:provider.region}:*:table/*"

functions:
  api:
    handler: handler.main
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true

package:
  exclude:
    - node_modules/**
    - venv/**
    - .git/**
    - .pytest_cache/**
    - tests/**
    - "*.pyc"
    - __pycache__/**
```

### プラグインのインストール

```bash
# 必要なプラグインをインストール
npm init -y
npm install --save-dev serverless-python-requirements
```

### デプロイコマンド

```bash
# 開発環境にデプロイ
serverless deploy --stage dev

# 本番環境にデプロイ
serverless deploy --stage prod

# 特定の関数のみ更新
serverless deploy function --function api --stage dev

# 環境変数を設定してデプロイ
DATABASE_URL_dev="your-database-url" serverless deploy --stage dev
```

### 環境別設定

```yaml
# serverless.yml
provider:
  environment:
    DATABASE_URL: ${self:custom.config.${self:provider.stage}.DATABASE_URL}
    CORS_ORIGINS: ${self:custom.config.${self:provider.stage}.CORS_ORIGINS}

custom:
  config:
    dev:
      DATABASE_URL: ${env:DATABASE_URL_DEV}
      CORS_ORIGINS: "*"
    prod:
      DATABASE_URL: ${env:DATABASE_URL_PROD}
      CORS_ORIGINS: "https://yourapp.com"
```

---

## AWS SAM

### template.yaml設定

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: HADS Application

Globals:
  Function:
    Timeout: 30
    Runtime: python3.9
    Environment:
      Variables:
        STAGE: !Ref Stage

Parameters:
  Stage:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - prod

Resources:
  HadsApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Stage
      Cors:
        AllowMethods: "'*'"
        AllowHeaders: "'*'"
        AllowOrigin: "'*'"

  HadsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: handler.main
      MemorySize: 512
      Events:
        ProxyApiRoot:
          Type: Api
          Properties:
            RestApiId: !Ref HadsApi
            Path: /
            Method: ANY
        ProxyApiGreedy:
          Type: Api
          Properties:
            RestApiId: !Ref HadsApi
            Path: /{proxy+}
            Method: ANY
      Environment:
        Variables:
          DATABASE_URL: !Sub "{{resolve:ssm:/hads/${Stage}/database-url}}"

  TodoTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "todos-${Stage}"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH

Outputs:
  HadsApi:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${HadsApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}/"
    
  HadsFunctionArn:
    Description: "HADS Lambda Function ARN"
    Value: !GetAtt HadsFunction.Arn
```

### samconfig.toml設定

```toml
# samconfig.toml
version = 0.1

[default]
[default.deploy]
[default.deploy.parameters]
stack_name = "hads-app"
s3_bucket = "your-sam-deployment-bucket"
s3_prefix = "hads-app"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "Stage=dev"

[prod]
[prod.deploy]
[prod.deploy.parameters]
stack_name = "hads-app-prod"
parameter_overrides = "Stage=prod"
```

### デプロイコマンド

```bash
# ビルド
sam build

# ローカルテスト
sam local start-api

# デプロイ
sam deploy --config-env default

# 本番環境デプロイ
sam deploy --config-env prod
```

---

## CI/CD パイプライン

### GitHub Actions設定

```yaml
# .github/workflows/deploy.yml
name: Deploy HADS Application

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=./ --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  deploy-dev:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Serverless Framework
      run: npm install -g serverless serverless-python-requirements
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Deploy to development
      run: serverless deploy --stage dev
      env:
        DATABASE_URL_dev: ${{ secrets.DATABASE_URL_DEV }}

  deploy-prod:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Serverless Framework
      run: npm install -g serverless serverless-python-requirements
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Deploy to production
      run: serverless deploy --stage prod
      env:
        DATABASE_URL_prod: ${{ secrets.DATABASE_URL_PROD }}
```

### AWS CodePipeline設定

```yaml
# buildspec.yml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.9
      nodejs: 18
    commands:
      - echo Installing dependencies
      - pip install -r requirements.txt
      - npm install -g serverless serverless-python-requirements

  pre_build:
    commands:
      - echo Running tests
      - python -m pytest tests/

  build:
    commands:
      - echo Build started on `date`
      - serverless package --stage $STAGE

  post_build:
    commands:
      - echo Deploying to $STAGE
      - serverless deploy --stage $STAGE

artifacts:
  files:
    - '**/*'
```

---

## 環境管理

### 環境変数の管理

```bash
# AWS Systems Manager Parameter Store を使用
aws ssm put-parameter \
    --name "/hads/dev/database-url" \
    --value "your-database-url" \
    --type "SecureString"

aws ssm put-parameter \
    --name "/hads/prod/database-url" \
    --value "your-production-database-url" \
    --type "SecureString"
```

### 設定ファイルでの参照

```python
# settings.py
import boto3
import os

def get_parameter(name, with_decryption=True):
    """SSM Parameter Store から値を取得"""
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(
            Name=name,
            WithDecryption=with_decryption
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting parameter {name}: {e}")
        return None

STAGE = os.getenv('STAGE', 'dev')
DATABASE_URL = (
    os.getenv('DATABASE_URL') or 
    get_parameter(f'/hads/{STAGE}/database-url')
)
```

### 複数環境の管理

```yaml
# environments/dev.yml
DATABASE_URL: "postgresql://localhost:5432/hads_dev"
DEBUG: true
CORS_ORIGINS: "*"

# environments/prod.yml
DATABASE_URL: "${ssm:/hads/prod/database-url}"
DEBUG: false
CORS_ORIGINS: "https://yourapp.com"
```

---

## モニタリング設定

### CloudWatch Alarms

```yaml
# serverless.yml
resources:
  Resources:
    ErrorAlarm:
      Type: AWS::CloudWatch::Alarm
      Properties:
        AlarmName: ${self:service}-${self:provider.stage}-errors
        AlarmDescription: Function errors
        MetricName: Errors
        Namespace: AWS/Lambda
        Statistic: Sum
        Period: 60
        EvaluationPeriods: 2
        Threshold: 5
        ComparisonOperator: GreaterThanThreshold
        Dimensions:
          - Name: FunctionName
            Value: ${self:service}-${self:provider.stage}-api

    DurationAlarm:
      Type: AWS::CloudWatch::Alarm
      Properties:
        AlarmName: ${self:service}-${self:provider.stage}-duration
        AlarmDescription: Function duration
        MetricName: Duration
        Namespace: AWS/Lambda
        Statistic: Average
        Period: 60
        EvaluationPeriods: 2
        Threshold: 10000
        ComparisonOperator: GreaterThanThreshold
```

### X-Ray トレーシング

```yaml
# serverless.yml
provider:
  tracing:
    lambda: true
    apiGateway: true

functions:
  api:
    handler: handler.main
    tracing: Active
```

### カスタムメトリクス

```python
# monitoring.py
import boto3
import time
from functools import wraps

cloudwatch = boto3.client('cloudwatch')

def monitor_performance(metric_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # 成功メトリクス
                put_metric(f"{metric_name}_success", 1)
                return result
            except Exception as e:
                # エラーメトリクス
                put_metric(f"{metric_name}_error", 1)
                raise
            finally:
                # 実行時間メトリクス
                duration = (time.time() - start_time) * 1000
                put_metric(f"{metric_name}_duration", duration, "Milliseconds")
        return wrapper
    return decorator

def put_metric(metric_name, value, unit="Count"):
    cloudwatch.put_metric_data(
        Namespace='HADS/Application',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }]
    )
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. デプロイパッケージが大きすぎる

```bash
# 不要なファイルを除外
echo "*.pyc" >> .serverlessignore
echo "__pycache__/" >> .serverlessignore
echo "tests/" >> .serverlessignore
echo ".git/" >> .serverlessignore

# Lambda Layers を使用
serverless plugin install -n serverless-python-requirements
```

#### 2. 権限エラー

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:*",
                "apigateway:*",
                "cloudformation:*",
                "iam:*",
                "s3:*"
            ],
            "Resource": "*"
        }
    ]
}
```

#### 3. 環境変数が設定されない

```bash
# デプロイ前に環境変数を確認
serverless print --stage dev

# 環境変数を明示的に設定
export DATABASE_URL_dev="your-url"
serverless deploy --stage dev
```

### ログの確認

```bash
# Serverless Framework でログ確認
serverless logs --function api --stage dev --tail

# AWS CLI でログ確認
aws logs tail /aws/lambda/hads-app-dev-api --follow
```

---

## 関連ドキュメント

- [ベストプラクティス](best-practices.md)
- [トラブルシューティング](troubleshooting.md)
- [モニタリングとロギング](monitoring.md)
- [セキュリティガイド](security.md)

---

[← 戻る](README.md)
