# サンプルアプリケーション

このページでは、WAMBDAフレームワークを使用したサンプルアプリケーションを紹介します。実際のコードを通じて、WAMBDAの機能と使い方を学ぶことができます。

## 目次
- [1. Hello World API](#1-hello-world-api)
- [2. Todo アプリケーション](#2-todo-アプリケーション)
- [3. ユーザー管理API](#3-ユーザー管理api)
- [4. ブログシステム](#4-ブログシステム)
- [5. ファイルアップロードAPI](#5-ファイルアップロードapi)
- [6. 認証付きダッシュボード](#6-認証付きダッシュボード)

---

## 1. Hello World API

最も基本的なAPIの例です。

### プロジェクト構造
```
hello-world/
├── handler.py
├── urls.py
├── settings.py
└── requirements.txt
```

### コード実装

**requirements.txt**
```
wambda
```

**settings.py**
```python
# settings.py
DEBUG = True
TEMPLATE_DIRS = ['templates']
CORS_ORIGINS = ['*']
```

**urls.py**
```python
# urls.py
from wambda.urls import path
from handler import hello_handler, info_handler

urlpatterns = [
    path('hello', hello_handler),
    path('hello/{name}', hello_handler),
    path('info', info_handler),
]
```

**handler.py**
```python
# handler.py
import json
from datetime import datetime

def hello_handler(event, context):
    """Hello World ハンドラー"""
    # パスパラメータの取得
    path_params = event.get('pathParameters') or {}
    name = path_params.get('name', 'World')
    
    # クエリパラメータの取得
    query_params = event.get('queryStringParameters') or {}
    lang = query_params.get('lang', 'en')
    
    # 言語に応じたメッセージ
    messages = {
        'en': f'Hello, {name}!',
        'ja': f'こんにちは、{name}さん！',
        'es': f'¡Hola, {name}!',
        'fr': f'Bonjour, {name}!'
    }
    
    message = messages.get(lang, messages['en'])
    
    response = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'language': lang
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response)
    }

def info_handler(event, context):
    """システム情報ハンドラー"""
    info = {
        'service': 'Hello World API',
        'version': '1.0.0',
        'endpoints': [
            'GET /hello - Basic greeting',
            'GET /hello/{name} - Personalized greeting',
            'GET /info - System information'
        ],
        'supported_languages': ['en', 'ja', 'es', 'fr']
    }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(info)
    }
```

### 使用例
```bash
# 基本的な挨拶
curl https://api.example.com/hello

# 名前を指定
curl https://api.example.com/hello/Alice

# 言語を指定
curl https://api.example.com/hello/太郎?lang=ja

# システム情報
curl https://api.example.com/info
```

---

## 2. Todo アプリケーション

DynamoDBを使用したTodoアプリケーションの例です。

### プロジェクト構造
```
todo-app/
├── handler.py
├── urls.py
├── settings.py
├── models.py
├── utils.py
└── requirements.txt
```

### コード実装

**requirements.txt**
```
wambda
boto3
```

**settings.py**
```python
# settings.py
import os

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'todos')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
```

**models.py**
```python
# models.py
import boto3
import uuid
from datetime import datetime
from settings import DYNAMODB_TABLE, AWS_REGION

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

class Todo:
    @staticmethod
    def create(title, description=''):
        """新しいTodoを作成"""
        todo_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        item = {
            'id': todo_id,
            'title': title,
            'description': description,
            'completed': False,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        table.put_item(Item=item)
        return item
    
    @staticmethod
    def get_all():
        """すべてのTodoを取得"""
        response = table.scan()
        return response.get('Items', [])
    
    @staticmethod
    def get_by_id(todo_id):
        """IDでTodoを取得"""
        response = table.get_item(Key={'id': todo_id})
        return response.get('Item')
    
    @staticmethod
    def update(todo_id, **kwargs):
        """Todoを更新"""
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': datetime.now().isoformat()}
        
        for key, value in kwargs.items():
            if key != 'id':
                update_expression += f", {key} = :{key}"
                expression_values[f':{key}'] = value
        
        table.update_item(
            Key={'id': todo_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        return Todo.get_by_id(todo_id)
    
    @staticmethod
    def delete(todo_id):
        """Todoを削除"""
        table.delete_item(Key={'id': todo_id})
        return True
```

**utils.py**
```python
# utils.py
import json

def json_response(status_code, data):
    """JSON レスポンスを生成"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(data, default=str)
    }

def error_response(status_code, message):
    """エラーレスポンスを生成"""
    return json_response(status_code, {'error': message})

def parse_json_body(event):
    """リクエストボディからJSONを解析"""
    try:
        body = event.get('body', '{}')
        return json.loads(body) if body else {}
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in request body")
```

**handler.py**
```python
# handler.py
from models import Todo
from utils import json_response, error_response, parse_json_body

def todo_list_handler(event, context):
    """Todo一覧・作成ハンドラー"""
    method = event['httpMethod']
    
    if method == 'GET':
        # Todo一覧取得
        todos = Todo.get_all()
        return json_response(200, {'todos': todos})
    
    elif method == 'POST':
        # 新しいTodo作成
        try:
            data = parse_json_body(event)
            title = data.get('title')
            
            if not title:
                return error_response(400, 'Title is required')
            
            todo = Todo.create(
                title=title,
                description=data.get('description', '')
            )
            
            return json_response(201, {'todo': todo})
            
        except ValueError as e:
            return error_response(400, str(e))
        except Exception as e:
            return error_response(500, 'Internal server error')
    
    elif method == 'OPTIONS':
        # CORS プリフライト
        return json_response(200, {})
    
    else:
        return error_response(405, 'Method not allowed')

def todo_detail_handler(event, context):
    """Todo詳細・更新・削除ハンドラー"""
    method = event['httpMethod']
    todo_id = event['pathParameters']['id']
    
    # Todoの存在確認
    todo = Todo.get_by_id(todo_id)
    if not todo:
        return error_response(404, 'Todo not found')
    
    if method == 'GET':
        # Todo詳細取得
        return json_response(200, {'todo': todo})
    
    elif method == 'PUT':
        # Todo更新
        try:
            data = parse_json_body(event)
            
            # 更新可能なフィールド
            allowed_fields = ['title', 'description', 'completed']
            update_data = {
                key: value for key, value in data.items()
                if key in allowed_fields
            }
            
            if not update_data:
                return error_response(400, 'No valid fields to update')
            
            updated_todo = Todo.update(todo_id, **update_data)
            return json_response(200, {'todo': updated_todo})
            
        except ValueError as e:
            return error_response(400, str(e))
        except Exception as e:
            return error_response(500, 'Internal server error')
    
    elif method == 'DELETE':
        # Todo削除
        try:
            Todo.delete(todo_id)
            return json_response(204, {})
        except Exception as e:
            return error_response(500, 'Internal server error')
    
    elif method == 'OPTIONS':
        # CORS プリフライト
        return json_response(200, {})
    
    else:
        return error_response(405, 'Method not allowed')

def health_handler(event, context):
    """ヘルスチェック"""
    return json_response(200, {
        'status': 'healthy',
        'service': 'Todo API',
        'version': '1.0.0'
    })
```

**urls.py**
```python
# urls.py
from wambda.urls import path
from handler import todo_list_handler, todo_detail_handler, health_handler

urlpatterns = [
    path('api/todos', todo_list_handler),
    path('api/todos/{id}', todo_detail_handler),
    path('health', health_handler),
]
```

### DynamoDBテーブル作成
```bash
aws dynamodb create-table \
    --table-name todos \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

### 使用例
```bash
# Todo一覧取得
curl https://api.example.com/api/todos

# 新しいTodo作成
curl -X POST https://api.example.com/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, bread, eggs"}'

# Todo更新
curl -X PUT https://api.example.com/api/todos/123 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Todo削除
curl -X DELETE https://api.example.com/api/todos/123
```

---

## 3. ユーザー管理API

Cognitoを使用したユーザー認証システムの例です。

### プロジェクト構造
```
user-management/
├── handler.py
├── urls.py
├── settings.py
├── auth.py
├── models.py
└── requirements.txt
```

### コード実装

**auth.py**
```python
# auth.py
import jwt
import requests
import json
from jwt.algorithms import RSAAlgorithm
from functools import wraps
from settings import COGNITO_USER_POOL_ID, COGNITO_REGION, COGNITO_CLIENT_ID

def get_cognito_public_keys():
    """Cognito公開鍵を取得"""
    jwks_url = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
    response = requests.get(jwks_url)
    return response.json()['keys']

def verify_jwt_token(token):
    """JWTトークンを検証"""
    try:
        # ヘッダーからkidを取得
        header = jwt.get_unverified_header(token)
        kid = header['kid']
        
        # 公開鍵を取得
        public_keys = get_cognito_public_keys()
        key = None
        for jwk in public_keys:
            if jwk['kid'] == kid:
                key = RSAAlgorithm.from_jwk(json.dumps(jwk))
                break
        
        if not key:
            raise ValueError("Public key not found")
        
        # トークンを検証
        payload = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=COGNITO_CLIENT_ID
        )
        
        return payload
        
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")

def require_auth(func):
    """認証が必要なエンドポイント用デコレータ"""
    @wraps(func)
    def wrapper(event, context):
        try:
            # Authorizationヘッダーから取得
            auth_header = event.get('headers', {}).get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {
                    'statusCode': 401,
                    'body': json.dumps({'error': 'Missing or invalid token'})
                }
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            
            # ユーザー情報をイベントに追加
            event['user'] = payload
            
            return func(event, context)
            
        except ValueError as e:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': str(e)})
            }
    
    return wrapper
```

### 詳細なハンドラー実装は [GitHub リポジトリ](https://github.com/example/wambda-examples) をご参照ください。

---

## 4. ブログシステム

記事の投稿・編集・表示機能を持つブログシステムです。

### 機能
- 記事の作成・編集・削除
- カテゴリー分類
- タグ機能
- コメント機能
- 検索機能

### 主要なファイル構成
```
blog-system/
├── handlers/
│   ├── article_handler.py
│   ├── category_handler.py
│   ├── comment_handler.py
│   └── search_handler.py
├── models/
│   ├── article.py
│   ├── category.py
│   └── comment.py
├── templates/
│   ├── article_list.html
│   ├── article_detail.html
│   └── base.html
├── static/
│   ├── css/
│   └── js/
├── urls.py
└── settings.py
```

---

## 5. ファイルアップロードAPI

S3を使用したファイルアップロード機能の例です。

### 機能
- ファイルアップロード
- プレサインドURL生成
- ファイル一覧・削除
- 画像リサイズ（Pillowを使用）

### キーポイント
```python
# S3プレサインドURL生成
def generate_presigned_url(bucket_name, object_key, expiration=3600):
    s3_client = boto3.client('s3')
    response = s3_client.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=expiration
    )
    return response
```

---

## 6. 認証付きダッシュボード

Cognitoを使用した管理ダッシュボードの例です。

### 機能
- ユーザーログイン・ログアウト
- ダッシュボード表示
- ユーザー管理
- アクセス権限制御

### テンプレート例
```html
<!-- templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        /* ダッシュボードのスタイル */
    </style>
</head>
<body>
    <nav>
        <h1>Admin Dashboard</h1>
        <div>
            Welcome, {{ user.name }}
            <a href="/logout">Logout</a>
        </div>
    </nav>
    
    <main>
        <div class="stats">
            <div class="stat-card">
                <h3>Total Users</h3>
                <p>{{ stats.total_users }}</p>
            </div>
            <!-- その他の統計情報 -->
        </div>
        
        <div class="content">
            <!-- ダッシュボードコンテンツ -->
        </div>
    </main>
</body>
</html>
```

---

## サンプルのダウンロードとセットアップ

### リポジトリのクローン
```bash
git clone https://github.com/example/wambda-examples.git
cd wambda-examples
```

### 個別サンプルのセットアップ
```bash
# Hello World API
cd hello-world
pip install -r requirements.txt
python -m wambda.local_server

# Todo アプリケーション
cd todo-app
pip install -r requirements.txt
# DynamoDBテーブル作成
aws dynamodb create-table --cli-input-json file://table-config.json
python -m wambda.local_server
```

### デプロイ
```bash
# Serverless Framework を使用
npm install -g serverless
serverless deploy --stage dev
```

---

## カスタマイズのヒント

### 1. 環境設定の分離
```python
# config.py
import os

class Config:
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = 'sqlite:///dev.db'

class ProductionConfig(Config):
    DATABASE_URL = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### 2. エラーハンドリングの強化
```python
class APIException(Exception):
    status_code = 500
    message = "Internal server error"

class ValidationError(APIException):
    status_code = 400
    message = "Validation error"

def handle_exceptions(func):
    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except APIException as e:
            return json_response(e.status_code, {'error': e.message})
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return json_response(500, {'error': 'Internal server error'})
    return wrapper
```

### 3. テストコードの追加
```python
# tests/test_handlers.py
import pytest
from unittest.mock import Mock, patch
from handler import todo_list_handler

class TestTodoHandler:
    def test_create_todo_success(self):
        event = {
            'httpMethod': 'POST',
            'body': '{"title": "Test Todo"}'
        }
        context = Mock()
        
        with patch('models.Todo.create') as mock_create:
            mock_create.return_value = {'id': '123', 'title': 'Test Todo'}
            
            response = todo_list_handler(event, context)
            
            assert response['statusCode'] == 201
            assert 'todo' in json.loads(response['body'])
```

---

## 関連ドキュメント

- [クイックスタート](quickstart.md)
- [APIリファレンス](api-reference.md)
- [ベストプラクティス](best-practices.md)
- [デプロイメントガイド](deployment.md)

---

[← 戻る](README.md)
