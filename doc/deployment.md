# デプロイメントガイド

このガイドでは、WAMBDAアプリケーションをAWS SAM（Serverless Application Model）を使用してAWS Lambdaにデプロイする方法を説明します。

## 目次
- [デプロイメント概要](#デプロイメント概要)
- [AWS SAM](#aws-sam)
- [環境管理](#環境管理)
- [モニタリング設定](#モニタリング設定)
- [トラブルシューティング](#トラブルシューティング)

---

## デプロイメント概要

### 必要な準備

1. **AWS アカウント**: アクティブなAWSアカウント
2. **IAM権限**: Lambda、API Gateway、CloudFormationの権限
3. **AWS CLI**: 設定済みのAWS CLI
4. **AWS SAM CLI**: インストール済みのSAM CLI
5. **Python環境**: Python 3.8以上

### AWS SAM CLI のインストール

```bash
# macOS (Homebrew)
brew tap aws/tap
brew install aws-sam-cli

# Windows (Chocolatey)
choco install aws-sam-cli

# Linux
curl -L "https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip" -o "aws-sam-cli.zip"
unzip aws-sam-cli.zip -d sam-installation
sudo ./sam-installation/install
```

---

## AWS SAM

### template.yaml設定

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: WAMBDA Application

Globals:
  Function:
    Timeout: 30
    Runtime: python3.12
    Environment:
      Variables:
        WAMBDA_LOG_LEVEL: !Ref LogLevel

Parameters:
  Stage:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - prod
    Description: Deployment stage

  LogLevel:
    Type: String
    Default: INFO
    AllowedValues:
      - DEBUG
      - INFO
      - WARNING
      - ERROR
    Description: Log level for the application

Resources:
  # Lambda Function
  MainFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: Lambda/
      Handler: lambda_function.lambda_handler
      MemorySize: 512
      Events:
        ProxyApiRoot:
          Type: Api
          Properties:
            RestApiId: !Ref MainApi
            Path: /
            Method: ANY
        ProxyApiGreedy:
          Type: Api
          Properties:
            RestApiId: !Ref MainApi
            Path: /{proxy+}
            Method: ANY
      Environment:
        Variables:
          WAMBDA_MAPPING_PATH: !Sub "/${Stage}"
          WAMBDA_DEBUG: !If [IsDevStage, "true", "false"]
          WAMBDA_USE_MOCK: !If [IsDevStage, "true", "false"]

  # API Gateway
  MainApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Stage
      Cors:
        AllowMethods: "'*'"
        AllowHeaders: "'*'"
        AllowOrigin: "'*'"
        AllowCredentials: true

  # Static Files S3 Bucket
  StaticFilesBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-static-files-${Stage}"
      PublicAccessBlockConfiguration:
        BlockPublicAcls: false
        BlockPublicPolicy: false
        IgnorePublicAcls: false
        RestrictPublicBuckets: false
      WebsiteConfiguration:
        IndexDocument: index.html
        ErrorDocument: error.html

  # S3 Bucket Policy for Static Files
  StaticFilesBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref StaticFilesBucket
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal: "*"
            Action: s3:GetObject
            Resource: !Sub "${StaticFilesBucket}/*"

  # CloudFront Distribution for Static Files
  StaticFilesDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
          - DomainName: !GetAtt StaticFilesBucket.RegionalDomainName
            Id: S3Origin
            S3OriginConfig:
              OriginAccessIdentity: ""
        Enabled: true
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # CachingOptimized
        PriceClass: PriceClass_100
        ViewerCertificate:
          CloudFrontDefaultCertificate: true

  # Lambda Execution Role
  MainFunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: SSMParameterAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - ssm:GetParameter
                  - ssm:GetParameters
                  - ssm:GetParametersByPath
                Resource: !Sub "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/Cognito/*"
        - PolicyName: CognitoAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - cognito-idp:AdminInitiateAuth
                  - cognito-idp:AdminGetUser
                  - cognito-idp:AdminCreateUser
                  - cognito-idp:AdminConfirmSignUp
                  - cognito-idp:AdminDeleteUser
                  - cognito-idp:ChangePassword
                  - cognito-idp:ForgotPassword
                  - cognito-idp:ConfirmForgotPassword
                Resource: "*"

Conditions:
  IsDevStage: !Equals [!Ref Stage, "dev"]

Outputs:
  ApiEndpoint:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${MainApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}/"
    Export:
      Name: !Sub "${AWS::StackName}-ApiEndpoint"

  LambdaFunctionArn:
    Description: "Lambda Function ARN"
    Value: !GetAtt MainFunction.Arn
    Export:
      Name: !Sub "${AWS::StackName}-LambdaFunctionArn"

  StaticFilesBucketName:
    Description: "S3 bucket name for static files"
    Value: !Ref StaticFilesBucket
    Export:
      Name: !Sub "${AWS::StackName}-StaticFilesBucket"

  StaticFilesUrl:
    Description: "CloudFront URL for static files"
    Value: !Sub "https://${StaticFilesDistribution.DomainName}"
    Export:
      Name: !Sub "${AWS::StackName}-StaticFilesUrl"
```

### samconfig.toml設定

```toml
# samconfig.toml
version = 0.1

[default]
[default.deploy]
[default.deploy.parameters]
stack_name = "wambda-app"
s3_bucket = ""  # SAM が自動的に作成
s3_prefix = "wambda-app"
region = "ap-northeast-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "Stage=dev LogLevel=INFO"
confirm_changeset = true
fail_on_empty_changeset = false

[staging]
[staging.deploy]
[staging.deploy.parameters]
stack_name = "wambda-app-staging"
parameter_overrides = "Stage=staging LogLevel=INFO"
confirm_changeset = true

[prod]
[prod.deploy]
[prod.deploy.parameters]
stack_name = "wambda-app-prod"
parameter_overrides = "Stage=prod LogLevel=WARNING"
confirm_changeset = true
fail_on_empty_changeset = false
```

### デプロイコマンド

```bash
# プロジェクトディレクトリに移動
cd your-wambda-project

# 依存関係のビルド
sam build

# ローカルテスト（オプション）
sam local start-api --port 3000

# 開発環境にデプロイ
sam deploy --config-env default

# ステージング環境にデプロイ
sam deploy --config-env staging

# 本番環境にデプロイ
sam deploy --config-env prod

# 初回デプロイ時（ガイド付き）
sam deploy --guided
```

### 静的ファイルのデプロイ

```bash
# S3バケット名を取得
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name wambda-app \
  --query 'Stacks[0].Outputs[?OutputKey==`StaticFilesBucketName`].OutputValue' \
  --output text)

# 静的ファイルをS3にアップロード
aws s3 sync static/ s3://$BUCKET_NAME/static/ --delete

# CloudFrontのキャッシュをクリア（必要に応じて）
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name wambda-app \
  --query 'Stacks[0].Outputs[?OutputKey==`StaticFilesDistributionId`].OutputValue' \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

---

## 環境管理

### SSM Parameter Store を使用した設定管理

```bash
# Cognito設定をSSMに保存
aws ssm put-parameter \
    --name "/Cognito/user_pool_id" \
    --value "ap-northeast-1_XXXXXXXXX" \
    --type "String"

aws ssm put-parameter \
    --name "/Cognito/client_id" \
    --value "your-client-id" \
    --type "String"

aws ssm put-parameter \
    --name "/Cognito/client_secret" \
    --value "your-client-secret" \
    --type "SecureString"
```

### 設定ファイルでの参照

```python
# Lambda/project/settings.py
import os

# 基本設定
MAPPING_PATH = os.environ.get('WAMBDA_MAPPING_PATH', "")
DEBUG = os.environ.get('WAMBDA_DEBUG', 'False').lower() == 'true'
USE_MOCK = os.environ.get('WAMBDA_USE_MOCK', 'False').lower() == 'true'
LOG_LEVEL = os.environ.get('WAMBDA_LOG_LEVEL', 'INFO')

# 認証設定（SSMパラメータ名）
COGNITO_SSM_PARAMS = {
    'USER_POOL_ID': '/Cognito/user_pool_id',
    'CLIENT_ID': '/Cognito/client_id',
    'CLIENT_SECRET': '/Cognito/client_secret'
}
```

### 環境別パラメータ管理

```bash
# 開発環境
aws ssm put-parameter --name "/Cognito/dev/user_pool_id" --value "dev-pool-id" --type "String"

# ステージング環境
aws ssm put-parameter --name "/Cognito/staging/user_pool_id" --value "staging-pool-id" --type "String"

# 本番環境
aws ssm put-parameter --name "/Cognito/prod/user_pool_id" --value "prod-pool-id" --type "String"
```

---

## モニタリング設定

### CloudWatch Alarms

```yaml
# template.yaml に追加
Resources:
  # エラー率アラーム
  ErrorRateAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "${AWS::StackName}-error-rate"
      AlarmDescription: Lambda function error rate
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 2
      Threshold: 5
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: FunctionName
          Value: !Ref MainFunction

  # レスポンス時間アラーム
  DurationAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "${AWS::StackName}-duration"
      AlarmDescription: Lambda function duration
      MetricName: Duration
      Namespace: AWS/Lambda
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 10000
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: FunctionName
          Value: !Ref MainFunction
```

### X-Ray トレーシング

```yaml
# template.yaml のGlobalsセクションに追加
Globals:
  Function:
    Tracing: Active
  Api:
    TracingConfig:
      PassthroughBehavior: Active
```

### カスタムメトリクス

```python
# Lambda/monitoring.py
import boto3
import time
from functools import wraps

cloudwatch = boto3.client('cloudwatch')

def monitor_performance(metric_name):
    """パフォーマンス監視デコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                put_metric(f"{metric_name}_success", 1)
                return result
            except Exception as e:
                put_metric(f"{metric_name}_error", 1)
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                put_metric(f"{metric_name}_duration", duration, "Milliseconds")
        return wrapper
    return decorator

def put_metric(metric_name, value, unit="Count"):
    """CloudWatch メトリクス送信"""
    try:
        cloudwatch.put_metric_data(
            Namespace='WAMBDA/Application',
            MetricData=[{
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }]
        )
    except Exception as e:
        print(f"Failed to put metric {metric_name}: {e}")
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. SAM ビルドエラー

```bash
# 依存関係の問題
pip install -r Lambda/requirements.txt

# Pythonバージョンの確認
python --version

# SAM CLIのバージョン確認
sam --version
```

#### 2. デプロイ権限エラー

必要なIAM権限を確認してください：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*",
                "lambda:*",
                "apigateway:*",
                "iam:*",
                "s3:*",
                "cloudfront:*"
            ],
            "Resource": "*"
        }
    ]
}
```

#### 3. 環境変数が反映されない

```bash
# スタックの出力確認
aws cloudformation describe-stacks --stack-name wambda-app

# Lambda関数の環境変数確認
aws lambda get-function-configuration --function-name wambda-app-MainFunction
```

#### 4. 静的ファイルが表示されない

```bash
# S3バケットの存在確認
aws s3 ls s3://your-bucket-name/

# バケットポリシーの確認
aws s3api get-bucket-policy --bucket your-bucket-name

# CloudFrontの配信確認
aws cloudfront get-distribution --id your-distribution-id
```

### ログの確認

```bash
# SAM CLI でログ確認
sam logs --stack-name wambda-app --tail

# AWS CLI でログ確認
aws logs tail /aws/lambda/wambda-app-MainFunction --follow

# 特定期間のログ取得
aws logs filter-log-events \
  --log-group-name /aws/lambda/wambda-app-MainFunction \
  --start-time $(date -d '1 hour ago' +%s)000
```

### デバッグのヒント

1. **ローカルテスト**: `sam local start-api` でローカル環境を構築
2. **段階的デプロイ**: 開発環境→ステージング→本番の順でデプロイ
3. **ログレベル調整**: 開発時は`DEBUG`、本番では`WARNING`以上
4. **リソース監視**: CloudWatch でメトリクスとアラームを設定

---

## 関連ドキュメント

- [プロジェクト構造](./project-structure.md) - ディレクトリ構成の詳細
- [認証とCognito統合](./authentication.md) - 認証システムの設定
- [ローカル開発環境](./local-development.md) - 開発環境のセットアップ

---

[← ドキュメント目次に戻る](./README.md)