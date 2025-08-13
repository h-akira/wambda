# トラブルシューティング

このガイドでは、HADSフレームワークを使用する際によく発生する問題とその解決方法をまとめています。

## 目次
- [一般的な問題](#一般的な問題)
- [開発環境の問題](#開発環境の問題)
- [デプロイメントの問題](#デプロイメントの問題)
- [実行時の問題](#実行時の問題)
- [パフォーマンスの問題](#パフォーマンスの問題)
- [認証・認可の問題](#認証認可の問題)
- [ログとデバッグ](#ログとデバッグ)

---

## 一般的な問題

### ImportError: No module named 'hads'

**症状**: HADSモジュールがインポートできない

**原因と解決方法**:

1. **インストールの確認**:
```bash
pip show hads
pip list | grep hads
```

2. **パスの確認**:
```python
import sys
print(sys.path)
```

3. **仮想環境の確認**:
```bash
which python
echo $VIRTUAL_ENV
```

4. **解決方法**:
```bash
# 仮想環境の作成
python -m venv env
source env/bin/activate  # macOS/Linux
# または
env\Scripts\activate  # Windows

# HADSのインストール
pip install -e .
```

### AttributeError: module 'hads' has no attribute 'X'

**症状**: HADSの属性や関数が見つからない

**解決方法**:

1. **バージョン確認**:
```bash
pip show hads
```

2. **ドキュメント確認**:
```python
import hads
help(hads)
dir(hads)
```

3. **正しいインポート**:
```python
# ❌ 間違い
from hads import nonexistent_function

# ✅ 正しい
from hads.handler import handler
from hads.urls import path
```

---

## 開発環境の問題

### ローカルサーバーが起動しない

**症状**: `python -m hads.local_server`でエラーが発生

**解決手順**:

1. **ポート競合の確認**:
```bash
# ポート8000が使用されているかチェック
lsof -i :8000
netstat -an | grep 8000
```

2. **別のポートで起動**:
```bash
python -m hads.local_server --port 8080
```

3. **設定ファイルの確認**:
```python
# settings.py が存在し、正しく設定されているか確認
import os
print(os.path.exists('settings.py'))

# 設定内容の確認
from settings import *
print(DEBUG)
print(TEMPLATE_DIRS)
```

4. **依存関係の確認**:
```bash
pip install -r requirements.txt
pip check
```

### テンプレートが見つからない

**症状**: `TemplateNotFound` エラー

**解決手順**:

1. **テンプレートディレクトリの確認**:
```python
# settings.py
TEMPLATE_DIRS = [
    'templates',
    'static/templates',
    os.path.join(os.path.dirname(__file__), 'templates')
]
```

2. **ファイル存在確認**:
```bash
find . -name "*.html" -type f
ls -la templates/
```

3. **パス設定のデバッグ**:
```python
import os
from hads import get_template_dirs

print("Current directory:", os.getcwd())
print("Template directories:", get_template_dirs())

for template_dir in get_template_dirs():
    print(f"Directory exists: {os.path.exists(template_dir)}")
    if os.path.exists(template_dir):
        print(f"Contents: {os.listdir(template_dir)}")
```

### AWS認証情報の問題

**症状**: `NoCredentialsError` または認証エラー

**解決手順**:

1. **AWS CLI設定の確認**:
```bash
aws configure list
aws sts get-caller-identity
```

2. **環境変数の確認**:
```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $AWS_DEFAULT_REGION
```

3. **IAMロールの確認**:
```bash
# EC2インスタンスの場合
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

4. **プロファイル設定**:
```bash
aws configure --profile hads-dev
export AWS_PROFILE=hads-dev
```

---

## デプロイメントの問題

### Lambda関数のデプロイエラー

**症状**: デプロイ時にエラーが発生

**解決手順**:

1. **パッケージサイズの確認**:
```bash
# デプロイパッケージのサイズ確認
du -sh deployment-package.zip

# Lambdaの制限: 50MB (zip), 250MB (unzipped)
```

2. **不要ファイルの除外**:
```bash
# .lambdaignore または serverless.yml で除外設定
echo "tests/" >> .lambdaignore
echo "*.pyc" >> .lambdaignore
echo "__pycache__/" >> .lambdaignore
```

3. **Lambdaレイヤーの活用**:
```yaml
# serverless.yml
layers:
  - arn:aws:lambda:us-east-1:123456789012:layer:python-libs:1
```

### デプロイ後に404エラー

**症状**: APIエンドポイントで404が発生

**解決手順**:

1. **API Gateway設定の確認**:
```bash
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id YOUR_API_ID
```

2. **URLパターンの確認**:
```python
# urls.py の確認
from hads.urls import urlpatterns
for pattern in urlpatterns:
    print(f"Path: {pattern.path}, Handler: {pattern.handler}")
```

3. **プロキシ統合の確認**:
```yaml
# serverless.yml
functions:
  api:
    events:
      - http:
          path: /{proxy+}
          method: ANY
```

### 環境変数が設定されない

**症状**: Lambda内で環境変数が取得できない

**解決手順**:

1. **Lambda設定の確認**:
```bash
aws lambda get-function --function-name your-function-name
```

2. **Serverless設定の確認**:
```yaml
# serverless.yml
provider:
  environment:
    DATABASE_URL: ${env:DATABASE_URL}
    
functions:
  api:
    environment:
      CUSTOM_VAR: ${env:CUSTOM_VAR}
```

3. **デプロイ時の環境変数**:
```bash
export DATABASE_URL="your-database-url"
serverless deploy
```

---

## 実行時の問題

### Lambda関数のタイムアウト

**症状**: Lambda関数が時間制限で終了する

**解決手順**:

1. **タイムアウト設定の確認**:
```yaml
# serverless.yml
functions:
  api:
    timeout: 30  # 秒
```

2. **処理時間の測定**:
```python
import time

def handler(event, context):
    start_time = time.time()
    
    try:
        # メイン処理
        result = process_request(event)
        
        processing_time = time.time() - start_time
        print(f"Processing time: {processing_time:.2f} seconds")
        
        return result
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"Error after {processing_time:.2f} seconds: {str(e)}")
        raise
```

3. **非同期処理の活用**:
```python
import asyncio
import aiohttp

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

def handler(event, context):
    # 非同期処理でタイムアウト回避
    urls = ['http://api1.com', 'http://api2.com']
    
    async def fetch_all():
        tasks = [fetch_data(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    results = asyncio.run(fetch_all())
    return {'statusCode': 200, 'body': json.dumps(results)}
```

### メモリ使用量エラー

**症状**: Lambda関数でメモリ不足エラー

**解決手順**:

1. **メモリ設定の調整**:
```yaml
# serverless.yml
functions:
  api:
    memorySize: 1024  # MB
```

2. **メモリ使用量の監視**:
```python
import psutil
import gc

def handler(event, context):
    process = psutil.Process()
    
    print(f"Memory before: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
    # メイン処理
    result = process_request(event)
    
    print(f"Memory after: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
    # ガベージコレクション
    gc.collect()
    
    print(f"Memory after GC: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
    return result
```

3. **メモリリークの対策**:
```python
# 大きなオブジェクトの適切な管理
def handler(event, context):
    large_data = None
    try:
        large_data = fetch_large_dataset()
        result = process_data(large_data)
        return result
    finally:
        # 明示的にメモリ解放
        if large_data:
            del large_data
        gc.collect()
```

### データベース接続エラー

**症状**: RDSやDynamoDBへの接続に失敗

**解決手順**:

1. **VPC設定の確認**:
```yaml
# serverless.yml
functions:
  api:
    vpc:
      securityGroupIds:
        - sg-12345678
      subnetIds:
        - subnet-12345678
        - subnet-87654321
```

2. **セキュリティグループの確認**:
```bash
aws ec2 describe-security-groups --group-ids sg-12345678
```

3. **接続テスト**:
```python
import boto3
import psycopg2
from botocore.exceptions import ClientError

def test_dynamodb_connection():
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('test-table')
        response = table.describe_table()
        print("DynamoDB connection successful")
        return True
    except ClientError as e:
        print(f"DynamoDB connection failed: {e}")
        return False

def test_rds_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f"RDS connection successful: {result}")
        return True
    except Exception as e:
        print(f"RDS connection failed: {e}")
        return False
```

---

## パフォーマンスの問題

### コールドスタートの遅延

**症状**: 初回リクエストが遅い

**解決手順**:

1. **Provisioned Concurrencyの設定**:
```yaml
# serverless.yml
functions:
  api:
    provisionedConcurrency: 2
```

2. **初期化の最適化**:
```python
# グローバルスコープで初期化
import boto3

# Lambda関数外で初期化（再利用される）
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

def handler(event, context):
    # 初期化済みのクライアントを使用
    pass
```

3. **不要な依存関係の削除**:
```bash
# 使用していないパッケージの確認
pip show package-name
pip uninstall package-name
```

### データベースクエリの遅延

**症状**: データベース操作が遅い

**解決手順**:

1. **クエリの最適化**:
```python
# ❌ 悪い例：N+1クエリ
def get_users_with_orders():
    users = get_all_users()
    for user in users:
        user.orders = get_orders_by_user_id(user.id)  # N回実行
    return users

# ✅ 良い例：JOINクエリ
def get_users_with_orders():
    query = """
    SELECT u.*, o.* 
    FROM users u 
    LEFT JOIN orders o ON u.id = o.user_id
    """
    return execute_query(query)
```

2. **インデックスの追加**:
```sql
-- よく検索される列にインデックス追加
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

3. **接続プールの設定**:
```python
import psycopg2.pool

# 接続プールの作成（グローバル）
connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=5,
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
```

---

## 認証・認可の問題

### JWT トークンエラー

**症状**: トークンの検証に失敗

**解決手順**:

1. **トークン形式の確認**:
```python
import jwt
import base64
import json

def debug_jwt_token(token):
    try:
        # ヘッダーの確認
        header = jwt.get_unverified_header(token)
        print(f"Header: {header}")
        
        # ペイロードの確認（検証なし）
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"Payload: {payload}")
        
    except Exception as e:
        print(f"Token debug error: {e}")
```

2. **シークレットキーの確認**:
```python
import os

# 環境変数の確認
jwt_secret = os.getenv('JWT_SECRET')
if not jwt_secret:
    print("JWT_SECRET not set")
else:
    print(f"JWT_SECRET length: {len(jwt_secret)}")
```

3. **時刻同期の確認**:
```python
import time
from datetime import datetime

def verify_token_timing(token):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        
        now = int(time.time())
        exp = payload.get('exp', 0)
        iat = payload.get('iat', 0)
        
        print(f"Current time: {now} ({datetime.fromtimestamp(now)})")
        print(f"Token issued: {iat} ({datetime.fromtimestamp(iat)})")
        print(f"Token expires: {exp} ({datetime.fromtimestamp(exp)})")
        print(f"Token expired: {now > exp}")
        
    except Exception as e:
        print(f"Token timing error: {e}")
```

### Cognito認証エラー

**症状**: AWS Cognitoでの認証に失敗

**解決手順**:

1. **Cognitoの設定確認**:
```python
import boto3

def verify_cognito_config():
    cognito = boto3.client('cognito-idp')
    
    try:
        user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        client_id = os.getenv('COGNITO_CLIENT_ID')
        
        # ユーザープールの確認
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        print(f"User Pool: {response['UserPool']['Name']}")
        
        # クライアントの確認
        response = cognito.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id
        )
        print(f"Client: {response['UserPoolClient']['ClientName']}")
        
    except Exception as e:
        print(f"Cognito config error: {e}")
```

2. **トークン検証**:
```python
import requests
import jwt
from jwt.algorithms import RSAAlgorithm

def verify_cognito_token(token):
    try:
        # JWKSの取得
        region = 'us-east-1'  # あなたのリージョン
        user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        
        jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
        jwks = requests.get(jwks_url).json()
        
        # ヘッダーからkidを取得
        header = jwt.get_unverified_header(token)
        kid = header['kid']
        
        # 対応する公開鍵を取得
        key = None
        for jwk in jwks['keys']:
            if jwk['kid'] == kid:
                key = RSAAlgorithm.from_jwk(json.dumps(jwk))
                break
        
        if not key:
            raise ValueError("Public key not found")
        
        # トークン検証
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=os.getenv('COGNITO_CLIENT_ID')
        )
        
        print(f"Token valid: {payload}")
        return payload
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return None
```

### プロキシサーバー経由でログインできない

**症状**: プロキシサーバー（`hads-admin.py proxy`）を使用すると認証が失敗するが、SAM Local直接接続（ポート3000）では正常にログインできる

**原因**: プロキシサーバーのリダイレクト処理とCookieヘッダー処理の問題

**診断手順**:

1. **ログでリダイレクト処理を確認**:
```bash
# プロキシサーバー起動（詳細ログ付き）
hads-admin.py proxy

# ログイン試行後、以下を確認：
# - POSTリクエストのResponse status（302である必要がある）
# - Set-Cookieヘッダーの有無
```

2. **期待される正常ログ**:
```
[PROXY] POST /accounts/login -> http://localhost:3000/accounts/login
[PROXY] Response status: 302
[PROXY] Found 1 Set-Cookie headers:
[PROXY]   Cookie 1: no_auth_user=username; Path=/; Expires=...
```

3. **問題のあるログ例**:
```
[PROXY] POST /accounts/login -> http://localhost:3000/accounts/login
[PROXY] Response status: 200
[PROXY] No Set-Cookie headers found
```

**解決策**:

この問題は以下の要因で発生し、HADSフレームワークで修正済みです：

1. **リダイレクト自動追跡の無効化**:
   - `urllib.request.urlopen()`はデフォルトで302リダイレクトを自動追跡
   - カスタム`NoRedirectErrorHandler`により302レスポンスをそのまま転送

2. **複数Set-Cookieヘッダーの適切な処理**:
   - 認証時に複数のCookieが設定される（id_token、access_token、refresh_token）
   - 各Cookieヘッダーを個別に処理

**回避策**（古いバージョンの場合）:
- SAM Local直接接続を使用: `http://localhost:3000`
- または最新のHADSバージョンにアップデート

---

## ログとデバッグ

### CloudWatchログが出力されない

**症状**: Lambda関数のログがCloudWatchに表示されない

**解決手順**:

1. **IAMロールの権限確認**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

2. **ログ出力のテスト**:
```python
import logging

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info("Lambda function started")
    print("This is a print statement")
    
    try:
        # メイン処理
        result = process_request(event)
        logger.info(f"Request processed successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise
```

3. **ログの確認**:
```bash
# AWS CLI でログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/"
aws logs get-log-events --log-group-name "/aws/lambda/your-function-name" --log-stream-name "latest"
```

### デバッグ情報の追加

**デバッグ用のログ関数**:
```python
import json
import sys
import traceback

def debug_request(event, context):
    """リクエスト情報をデバッグ出力"""
    debug_info = {
        'event': event,
        'context': {
            'function_name': context.function_name,
            'function_version': context.function_version,
            'invoked_function_arn': context.invoked_function_arn,
            'memory_limit_in_mb': context.memory_limit_in_mb,
            'remaining_time_in_millis': context.get_remaining_time_in_millis(),
            'log_group_name': context.log_group_name,
            'log_stream_name': context.log_stream_name,
            'aws_request_id': context.aws_request_id
        },
        'environment': dict(os.environ),
        'python_version': sys.version,
        'python_path': sys.path
    }
    
    print("=== DEBUG INFO ===")
    print(json.dumps(debug_info, indent=2, default=str))
    print("==================")

def error_handler(func):
    """エラー詳細をログ出力するデコレータ"""
    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            error_info = {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'event': event,
                'context_aws_request_id': context.aws_request_id
            }
            
            print("=== ERROR INFO ===")
            print(json.dumps(error_info, indent=2, default=str))
            print("==================")
            
            raise
    
    return wrapper

@error_handler
def handler(event, context):
    if os.getenv('DEBUG', '').lower() == 'true':
        debug_request(event, context)
    
    # メイン処理
    return process_request(event)
```

---

## 関連ドキュメント

- [FAQ](faq.md)
- [ベストプラクティス](best-practices.md)
- [API リファレンス](api-reference.md)
- [ローカル開発環境](local-development.md)

---

[← 戻る](README.md)
