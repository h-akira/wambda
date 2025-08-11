# ベストプラクティス

このガイドでは、HADSフレームワークを使用する際の推奨パターンとベストプラクティスをまとめています。

## 目次
- [プロジェクト設計](#プロジェクト設計)
- [コード品質](#コード品質)
- [パフォーマンス最適化](#パフォーマンス最適化)
- [セキュリティ](#セキュリティ)
- [デプロイメント](#デプロイメント)
- [監視とロギング](#監視とロギング)
- [テスト戦略](#テスト戦略)

---

## プロジェクト設計

### アーキテクチャ設計

#### マイクロサービス指向
```
project/
├── user-service/          # ユーザー管理
├── product-service/       # 商品管理
├── order-service/         # 注文処理
└── notification-service/  # 通知サービス
```

#### 責任の分離
```python
# ❌ 悪い例：すべてを一つの関数で処理
def handler(event, context):
    # ユーザー認証
    user = authenticate_user(event)
    # 商品取得
    products = get_products()
    # 注文処理
    order = create_order(user, products)
    # メール送信
    send_email(user, order)
    # レスポンス生成
    return generate_response(order)

# ✅ 良い例：責任を分離
def user_handler(event, context):
    """ユーザー管理専用"""
    return handle_user_request(event)

def product_handler(event, context):
    """商品管理専用"""
    return handle_product_request(event)

def order_handler(event, context):
    """注文処理専用"""
    return handle_order_request(event)
```

### URLルーティング設計

#### RESTful API設計
```python
# urls.py
urlpatterns = [
    # リソース指向のURL設計
    path('api/v1/users', user_list_handler),
    path('api/v1/users/{id}', user_detail_handler),
    path('api/v1/users/{id}/orders', user_orders_handler),
    
    # バージョニング
    path('api/v1/products', product_list_v1),
    path('api/v2/products', product_list_v2),
    
    # ヘルスチェック
    path('health', health_check_handler),
]
```

#### エラーハンドリング
```python
def safe_handler(handler_func):
    """エラーハンドリングデコレータ"""
    def wrapper(event, context):
        try:
            return handler_func(event, context)
        except ValidationError as e:
            return error_response(400, str(e))
        except PermissionError as e:
            return error_response(403, str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return error_response(500, "Internal server error")
    return wrapper

@safe_handler
def product_handler(event, context):
    # メイン処理
    pass
```

---

## コード品質

### 型ヒント使用
```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class Product:
    id: str
    name: str
    price: float
    category: Optional[str] = None

def get_products(category: Optional[str] = None) -> List[Product]:
    """商品一覧を取得"""
    products = fetch_products_from_db(category)
    return [Product(**product) for product in products]

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda ハンドラー"""
    return {
        'statusCode': 200,
        'body': json.dumps({'products': get_products()})
    }
```

### 設定管理
```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    """アプリケーション設定"""
    debug: bool = False
    database_url: str = ""
    cognito_user_pool_id: str = ""
    cors_origins: List[str] = None
    
    def __post_init__(self):
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.database_url = os.getenv('DATABASE_URL', '')
        self.cognito_user_pool_id = os.getenv('COGNITO_USER_POOL_ID', '')
        self.cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')

# グローバルインスタンス
settings = Settings()
```

### 依存関係注入
```python
# services.py
from abc import ABC, abstractmethod

class DatabaseService(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[Dict]:
        pass

class DynamoDBService(DatabaseService):
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        response = self.table.get_item(Key={'id': user_id})
        return response.get('Item')

# handler.py
def create_handler(db_service: DatabaseService):
    def handler(event, context):
        user_id = event['pathParameters']['id']
        user = db_service.get_user(user_id)
        return {'statusCode': 200, 'body': json.dumps(user)}
    return handler

# 実際の使用
db_service = DynamoDBService('users')
user_handler = create_handler(db_service)
```

---

## パフォーマンス最適化

### 初期化最適化
```python
# ❌ 悪い例：関数内で初期化
def handler(event, context):
    # 毎回初期化される
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('products')
    # 処理...

# ✅ 良い例：グローバルで初期化
import boto3

# コールドスタート時のみ初期化
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('products')

def handler(event, context):
    # 初期化済みのリソースを使用
    response = table.get_item(Key={'id': product_id})
    # 処理...
```

### 接続プーリング
```python
# database.py
import psycopg2.pool
from contextlib import contextmanager

# グローバル接続プール
connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=5,
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

@contextmanager
def get_db_connection():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def get_products():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        return cursor.fetchall()
```

### キャッシング戦略
```python
import redis
import json
from functools import wraps

# Redis接続（グローバル）
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=6379,
    decode_responses=True
)

def cache_result(ttl=300):
    """結果をキャッシュするデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュキー生成
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # キャッシュから取得
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 関数実行
            result = func(*args, **kwargs)
            
            # キャッシュに保存
            redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

@cache_result(ttl=600)
def get_popular_products():
    """人気商品を取得（10分キャッシュ）"""
    # 重い処理
    return fetch_popular_products_from_db()
```

---

## セキュリティ

### 入力検証
```python
from marshmallow import Schema, fields, ValidationError

class ProductSchema(Schema):
    """商品データのスキーマ"""
    name = fields.Str(required=True, validate=Length(min=1, max=100))
    price = fields.Float(required=True, validate=Range(min=0))
    category = fields.Str(validate=Length(max=50))

def validate_product_data(data):
    """商品データを検証"""
    schema = ProductSchema()
    try:
        return schema.load(data)
    except ValidationError as err:
        raise ValueError(f"Invalid input: {err.messages}")

def create_product_handler(event, context):
    try:
        data = json.loads(event['body'])
        validated_data = validate_product_data(data)
        # 処理続行
    except (json.JSONDecodeError, ValueError) as e:
        return error_response(400, str(e))
```

### SQL インジェクション対策
```python
# ❌ 悪い例：SQLインジェクション脆弱性
def get_user_by_email(email):
    query = f"SELECT * FROM users WHERE email = '{email}'"
    cursor.execute(query)  # 危険！

# ✅ 良い例：パラメータ化クエリ
def get_user_by_email(email):
    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))
```

### 認証・認可
```python
import jwt
from functools import wraps

def require_auth(func):
    """JWT認証が必要なエンドポイント"""
    @wraps(func)
    def wrapper(event, context):
        try:
            # Authorizationヘッダーから取得
            auth_header = event.get('headers', {}).get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return error_response(401, 'Missing or invalid token')
            
            token = auth_header.split(' ')[1]
            
            # JWT検証
            payload = jwt.decode(
                token, 
                settings.jwt_secret, 
                algorithms=['HS256']
            )
            
            # ユーザー情報をイベントに追加
            event['user'] = payload
            
            return func(event, context)
            
        except jwt.ExpiredSignatureError:
            return error_response(401, 'Token expired')
        except jwt.InvalidTokenError:
            return error_response(401, 'Invalid token')
    
    return wrapper

@require_auth
def protected_handler(event, context):
    user = event['user']
    return {'statusCode': 200, 'body': f"Hello, {user['username']}"}
```

---

## デプロイメント

### 環境分離
```yaml
# serverless.yml
service: hads-app

provider:
  name: aws
  runtime: python3.9
  stage: ${opt:stage, 'dev'}
  environment:
    STAGE: ${self:provider.stage}
    DATABASE_URL: ${env:DATABASE_URL_${self:provider.stage}}
    
functions:
  api:
    handler: handler.main
    events:
      - http:
          path: /{proxy+}
          method: ANY
    environment:
      COGNITO_USER_POOL_ID: ${env:COGNITO_USER_POOL_ID_${self:provider.stage}}

# 環境変数ファイル
# .env.dev
DATABASE_URL_dev=postgresql://localhost:5432/hads_dev
COGNITO_USER_POOL_ID_dev=us-east-1_xxxxxxx

# .env.prod
DATABASE_URL_prod=postgresql://prod-host:5432/hads_prod
COGNITO_USER_POOL_ID_prod=us-east-1_yyyyyyy
```

### デプロイ自動化
```bash
#!/bin/bash
# deploy.sh

set -e

STAGE=${1:-dev}

echo "Deploying to $STAGE environment..."

# テスト実行
python -m pytest tests/

# 依存関係チェック
pip check

# デプロイ
serverless deploy --stage $STAGE

# ヘルスチェック
curl -f "https://api-$STAGE.example.com/health" || exit 1

echo "Deployment completed successfully!"
```

---

## 監視とロギング

### 構造化ログ
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
    
    def log(self, level, message, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))
    
    def info(self, message, **kwargs):
        self.log('INFO', message, **kwargs)
    
    def error(self, message, **kwargs):
        self.log('ERROR', message, **kwargs)

# 使用例
logger = StructuredLogger(__name__)

def handler(event, context):
    logger.info(
        'Request received',
        request_id=context.aws_request_id,
        method=event['httpMethod'],
        path=event['path']
    )
    
    try:
        # 処理
        result = process_request(event)
        
        logger.info(
            'Request completed',
            request_id=context.aws_request_id,
            duration_ms=context.get_remaining_time_in_millis()
        )
        
        return result
        
    except Exception as e:
        logger.error(
            'Request failed',
            request_id=context.aws_request_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

### メトリクス収集
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name, value, unit='Count', **dimensions):
    """CloudWatchにカスタムメトリクスを送信"""
    cloudwatch.put_metric_data(
        Namespace='HADS/Application',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Dimensions': [
                    {'Name': key, 'Value': str(value)}
                    for key, value in dimensions.items()
                ]
            }
        ]
    )

def handler(event, context):
    start_time = time.time()
    
    try:
        result = process_request(event)
        
        # 成功メトリクス
        put_custom_metric(
            'RequestSuccess',
            1,
            endpoint=event['path'],
            method=event['httpMethod']
        )
        
        return result
        
    except Exception as e:
        # エラーメトリクス
        put_custom_metric(
            'RequestError',
            1,
            endpoint=event['path'],
            error_type=type(e).__name__
        )
        raise
        
    finally:
        # レスポンス時間メトリクス
        duration = (time.time() - start_time) * 1000
        put_custom_metric(
            'ResponseTime',
            duration,
            'Milliseconds',
            endpoint=event['path']
        )
```

---

## Mock機能のベストプラクティス

### Mockディレクトリ構造

プロジェクト内でのMock機能の標準的な構造：

```
Lambda/
├── mock/
│   ├── __init__.py          # 空ファイル（Pythonパッケージとして認識）
│   ├── ssm.py              # SSM Parameter Store モック
│   ├── dynamodb.py         # DynamoDB モック
│   ├── s3.py               # S3 モック（必要に応じて）
│   ├── cognito.py          # Cognito モック（必要に応じて）
│   └── utils.py            # 共通ユーティリティ
├── project/
│   └── settings.py         # USE_MOCK設定
└── lambda_function.py      # use_mock()関数
```

### Mock設定の管理

#### settings.pyでの環境別設定

```python
# Lambda/project/settings.py
import os

# 環境の判定
ENV = os.getenv('ENVIRONMENT', 'development')

# 基本設定
if ENV == 'development':
    DEBUG = True
    USE_MOCK = True
    NO_AUTH = True           # 開発時は認証バイパス
    LOG_LEVEL = 'DEBUG'
    
elif ENV == 'testing':
    DEBUG = True
    USE_MOCK = True
    NO_AUTH = False          # テスト時は認証も検証
    LOG_LEVEL = 'INFO'
    
elif ENV == 'staging':
    DEBUG = False
    USE_MOCK = False         # ステージング環境では実AWS使用
    NO_AUTH = False
    LOG_LEVEL = 'WARNING'
    
else:  # production
    DEBUG = False
    USE_MOCK = False
    NO_AUTH = False
    LOG_LEVEL = 'ERROR'

# Mock機能の部分的制御（上級者向け）
USE_MOCK_DYNAMODB = USE_MOCK
USE_MOCK_SSM = USE_MOCK
USE_MOCK_S3 = USE_MOCK
USE_MOCK_COGNITO = USE_MOCK and NO_AUTH
```

### データ設計のベストプラクティス

#### 1. 実データに近いMockデータ

```python
# Lambda/mock/dynamodb.py - 良い例
def set_data():
    """実際のデータ構造に近いモックデータ"""
    users = [
        {
            'user_id': 'u-12345678',  # 実際のID形式に合わせる
            'email': 'user1@example.com',
            'name': 'テストユーザー1',
            'created_at': '2023-12-01T00:00:00Z',
            'updated_at': '2023-12-01T00:00:00Z',
            'status': 'active'
        },
        {
            'user_id': 'u-87654321',
            'email': 'user2@example.com', 
            'name': 'テストユーザー2',
            'created_at': '2023-12-02T00:00:00Z',
            'updated_at': '2023-12-02T00:00:00Z',
            'status': 'inactive'  # エッジケース用データ
        }
    ]
```

#### 2. テストケース網羅のためのデータ

```python
# Lambda/mock/utils.py
def generate_test_cases():
    """様々なテストケースに対応するデータセット"""
    return {
        'normal_users': [
            {'user_id': 'normal-1', 'name': '通常ユーザー1'},
            {'user_id': 'normal-2', 'name': '通常ユーザー2'}
        ],
        'edge_cases': [
            {'user_id': 'empty-name', 'name': ''},  # 空文字
            {'user_id': 'long-name', 'name': 'a' * 255},  # 長い文字列
            {'user_id': 'special-chars', 'name': '特殊文字@#$%'}  # 特殊文字
        ],
        'error_cases': [
            {'user_id': 'invalid-data', 'status': 'corrupted'}
        ]
    }
```

### Mock関数の実装パターン

#### 1. エラーハンドリング付きMock設定

```python
# Lambda/mock/ssm.py
import boto3
import logging

logger = logging.getLogger(__name__)

def set_data():
    """エラー処理を含むSSMモック設定"""
    ssm = boto3.client('ssm')
    
    # パラメータ定義
    parameters = get_required_parameters()
    
    success_count = 0
    error_count = 0
    
    for param in parameters:
        try:
            ssm.put_parameter(
                Name=param['Name'],
                Value=param['Value'],
                Type=param['Type'],
                Overwrite=True
            )
            logger.info(f"✓ Set parameter: {param['Name']}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"✗ Failed to set {param['Name']}: {e}")
            error_count += 1
    
    logger.info(f"SSM Mock setup: {success_count} success, {error_count} errors")
    
    # 設定確認
    verify_parameters(ssm, [p['Name'] for p in parameters])

def get_required_parameters():
    """必要なパラメータの定義"""
    return [
        {
            'Name': '/MyProject/Database/Host',
            'Value': 'localhost',
            'Type': 'String',
            'Description': 'Database host for mock environment'
        },
        {
            'Name': '/MyProject/API/Key', 
            'Value': 'mock-api-key-12345',
            'Type': 'SecureString',
            'Description': 'API key for external services'
        }
    ]

def verify_parameters(ssm, parameter_names):
    """パラメータ設定の確認"""
    for name in parameter_names:
        try:
            response = ssm.get_parameter(Name=name)
            logger.debug(f"Verified: {name} = {response['Parameter']['Value']}")
        except Exception as e:
            logger.warning(f"Verification failed for {name}: {e}")
```

#### 2. DynamoDB Mock のベストプラクティス

```python
# Lambda/mock/dynamodb.py
import boto3
from botocore.exceptions import ResourceInUseException
import logging

logger = logging.getLogger(__name__)

def set_data():
    """DynamoDB Mock の最適化された設定"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
    
    # テーブル設定を外部化
    table_configs = get_table_configurations()
    
    for config in table_configs:
        setup_table(dynamodb, config)

def get_table_configurations():
    """テーブル設定の定義"""
    return [
        {
            'name': 'Users',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            'attribute_definitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            'global_secondary_indexes': [
                {
                    'IndexName': 'email-index',
                    'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                    'AttributeDefinitions': [{'AttributeName': 'email', 'AttributeType': 'S'}],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            'sample_data': get_users_sample_data()
        }
    ]

def setup_table(dynamodb, config):
    """個別テーブルのセットアップ"""
    table_name = config['name']
    
    try:
        # テーブル作成
        create_params = {
            'TableName': table_name,
            'KeySchema': config['key_schema'],
            'AttributeDefinitions': config['attribute_definitions'],
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        # GSI設定があれば追加
        if 'global_secondary_indexes' in config:
            create_params['GlobalSecondaryIndexes'] = config['global_secondary_indexes']
            # GSI用のAttributeDefinitionsも追加
            for gsi in config['global_secondary_indexes']:
                for attr_def in gsi.get('AttributeDefinitions', []):
                    if attr_def not in create_params['AttributeDefinitions']:
                        create_params['AttributeDefinitions'].append(attr_def)
        
        table = dynamodb.create_table(**create_params)
        table.wait_until_exists()
        logger.info(f"✓ Created table: {table_name}")
        
    except ResourceInUseException:
        logger.info(f"→ Table already exists: {table_name}")
        table = dynamodb.Table(table_name)
        
    except Exception as e:
        logger.error(f"✗ Table creation failed: {table_name} - {e}")
        return
    
    # データ投入
    insert_sample_data(table, config['sample_data'])

def insert_sample_data(table, sample_data):
    """サンプルデータの一括投入"""
    with table.batch_writer() as batch:
        for item in sample_data:
            batch.put_item(Item=item)
    
    logger.info(f"✓ Inserted {len(sample_data)} items into {table.name}")

def get_users_sample_data():
    """ユーザーテーブル用サンプルデータ"""
    return [
        {
            'user_id': 'u-001',
            'email': 'admin@example.com',
            'name': '管理者',
            'role': 'admin',
            'created_at': '2023-01-01T00:00:00Z'
        },
        {
            'user_id': 'u-002', 
            'email': 'user1@example.com',
            'name': '一般ユーザー1',
            'role': 'user',
            'created_at': '2023-01-02T00:00:00Z'
        }
    ]
```

### Mock機能のテスト戦略

#### 1. 段階的テストアプローチ

```python
# Lambda/mock/testing_strategy.py
class MockTestStrategy:
    """Mock環境でのテスト戦略"""
    
    @staticmethod
    def unit_test_setup():
        """ユニットテスト用の最小限Mock"""
        return {
            'USE_MOCK': True,
            'MOCK_MINIMAL': True,  # 必要最小限のみ
            'MOCK_SERVICES': ['ssm']  # SSMのみモック
        }
    
    @staticmethod
    def integration_test_setup():
        """統合テスト用の完全Mock"""
        return {
            'USE_MOCK': True,
            'MOCK_MINIMAL': False,
            'MOCK_SERVICES': ['ssm', 'dynamodb', 's3']
        }
    
    @staticmethod
    def e2e_test_setup():
        """E2Eテスト用の部分Mock"""
        return {
            'USE_MOCK': True,
            'MOCK_SERVICES': ['ssm'],  # 機密データのみモック
            'REAL_SERVICES': ['dynamodb', 's3']  # 実サービスも使用
        }
```

#### 2. CIパイプラインでのMock活用

```yaml
# .github/workflows/test.yml
name: HADS Test Pipeline

on: [push, pull_request]

jobs:
  mock-tests:
    runs-on: ubuntu-latest
    env:
      ENVIRONMENT: testing
      USE_MOCK: true
      
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run Mock Tests
      run: |
        # Mock環境でのテスト実行
        hads-admin.py get -p /
        hads-admin.py get -p /api/users
        hads-admin.py get -p /api/health
        
    - name: Validate Mock Data
      run: |
        # Mockデータの整合性確認
        python -c "
        import sys
        sys.path.append('Lambda')
        from mock.ssm import set_data as setup_ssm
        from mock.dynamodb import set_data as setup_dynamodb
        setup_ssm()
        setup_dynamodb()
        print('Mock validation passed')
        "
```

### トラブルシューティング

#### 1. よくある問題と解決策

```python
# Lambda/mock/troubleshooting.py
import boto3
import logging

logger = logging.getLogger(__name__)

class MockTroubleshooter:
    """Mock機能のトラブルシューティング"""
    
    @staticmethod
    def diagnose_mock_environment():
        """Mock環境の診断"""
        issues = []
        
        # 1. moto のインポート確認
        try:
            from moto import mock_aws
            logger.info("✓ moto library available")
        except ImportError:
            issues.append("✗ moto library not installed")
        
        # 2. Mock設定確認
        try:
            from project.settings import USE_MOCK
            if USE_MOCK:
                logger.info("✓ USE_MOCK is enabled")
            else:
                issues.append("→ USE_MOCK is disabled")
        except ImportError:
            issues.append("✗ Cannot import USE_MOCK from settings")
        
        # 3. Mock ディレクトリ確認
        import os
        mock_dir = os.path.join(os.path.dirname(__file__))
        required_files = ['ssm.py', 'dynamodb.py']
        
        for file in required_files:
            if os.path.exists(os.path.join(mock_dir, file)):
                logger.info(f"✓ {file} exists")
            else:
                issues.append(f"✗ {file} not found in mock directory")
        
        return issues
    
    @staticmethod
    def validate_mock_data():
        """Mockデータの検証"""
        results = {}
        
        # SSM検証
        try:
            ssm = boto3.client('ssm')
            response = ssm.get_parameter(Name='/MyProject/Database/Host')
            results['ssm'] = "✓ SSM parameters accessible"
        except Exception as e:
            results['ssm'] = f"✗ SSM error: {e}"
        
        # DynamoDB検証
        try:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('Users')
            response = table.scan(Limit=1)
            results['dynamodb'] = f"✓ DynamoDB accessible ({response['Count']} items)"
        except Exception as e:
            results['dynamodb'] = f"✗ DynamoDB error: {e}"
        
        return results
```

#### 2. デバッグ用ヘルパー

```python
# Lambda/mock/debug.py
def debug_mock_status():
    """Mock機能のステータス表示"""
    from project.settings import USE_MOCK, DEBUG
    import os
    
    print("=== HADS Mock Status ===")
    print(f"USE_MOCK: {USE_MOCK}")
    print(f"DEBUG: {DEBUG}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"AWS Region: {os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-1')}")
    
    if USE_MOCK:
        print("\n=== Mock Services ===")
        # 各サービスの状態確認
        diagnose_services()

def diagnose_services():
    """各AWSサービスMockの診断"""
    services = {
        'SSM': diagnose_ssm,
        'DynamoDB': diagnose_dynamodb,
        'S3': diagnose_s3
    }
    
    for service_name, diagnose_func in services.items():
        try:
            status = diagnose_func()
            print(f"{service_name}: {status}")
        except Exception as e:
            print(f"{service_name}: Error - {e}")
```

## テスト戦略

### ユニットテスト
```python
# tests/test_handlers.py
import pytest
from unittest.mock import Mock, patch
from handler import product_handler

class TestProductHandler:
    def test_get_product_success(self):
        # テストイベント
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'id': '123'},
            'headers': {}
        }
        context = Mock()
        
        # モック設定
        with patch('handler.get_product_from_db') as mock_get:
            mock_get.return_value = {
                'id': '123',
                'name': 'Test Product',
                'price': 100.0
            }
            
            # テスト実行
            response = product_handler(event, context)
            
            # アサーション
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['id'] == '123'
            assert body['name'] == 'Test Product'
    
    def test_get_product_not_found(self):
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'id': '999'},
            'headers': {}
        }
        context = Mock()
        
        with patch('handler.get_product_from_db') as mock_get:
            mock_get.return_value = None
            
            response = product_handler(event, context)
            
            assert response['statusCode'] == 404
```

### 統合テスト
```python
# tests/test_integration.py
import requests
import pytest

class TestAPIIntegration:
    @pytest.fixture
    def api_url(self):
        return "https://api-dev.example.com"
    
    def test_create_and_get_product(self, api_url):
        # 商品作成
        product_data = {
            'name': 'Integration Test Product',
            'price': 50.0,
            'category': 'test'
        }
        
        create_response = requests.post(
            f"{api_url}/api/v1/products",
            json=product_data
        )
        assert create_response.status_code == 201
        
        product_id = create_response.json()['id']
        
        # 商品取得
        get_response = requests.get(
            f"{api_url}/api/v1/products/{product_id}"
        )
        assert get_response.status_code == 200
        
        product = get_response.json()
        assert product['name'] == product_data['name']
        assert product['price'] == product_data['price']
```

---

## 関連ドキュメント

- [FAQ](faq.md)
- [トラブルシューティング](troubleshooting.md)
- [API リファレンス](api-reference.md)
- [サンプルアプリケーション](examples.md)

---

[← 戻る](README.md)
