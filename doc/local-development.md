# ローカル開発環境

WAMBDAは効率的なローカル開発環境を提供し、AWS環境をシミュレートしながら快適に開発できます。このページでは、ローカル開発環境の詳細な設定と使用方法を説明します。

## 🏗️ ローカル開発の仕組み

### 3つのサーバー構成

WAMBDAのローカル開発環境は3つのサーバーで構成されています：

```
┌─────────────────────────────────┐
│    プロキシサーバー (8000)      │
│    統合エンドポイント           │
└─────────────┬───────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────────┐  ┌─────────────┐
│ SAM Local   │  │ 静的ファイル │
│ (3000)      │  │ サーバー     │
│ Lambda実行  │  │ (8080)      │
└─────────────┘  └─────────────┘
```

1. **SAM Local** (ポート3000): Lambda関数をローカルで実行
2. **静的ファイルサーバー** (ポート8080): CSS、JS、画像を配信
3. **プロキシサーバー** (ポート8000): 統合されたエンドポイントを提供

## 🚀 開発サーバーの起動

### 一括起動（推奨）

```bash
# プロキシサーバーを起動（他のサーバーも自動起動）
wambda-admin.py proxy
```

### 個別起動

```bash
# ターミナル1: SAM Local
sam local start-api

# ターミナル2: 静的ファイルサーバー
wambda-admin.py static

# ターミナル3: プロキシサーバー
wambda-admin.py proxy
```

## ⚙️ CLIオプションによる詳細設定

### ポート設定

```bash
# プロキシサーバーのカスタムポート設定
wambda-admin.py proxy -p 9000 -s 3001 --static-port 8081

# 静的ファイルサーバーのカスタム設定
wambda-admin.py static -p 8090 -d assets --static-url /files
```

### 環境変数による設定

```bash
# AWS認証設定
export AWS_PROFILE=development
export AWS_DEFAULT_REGION=ap-northeast-1

# デバッグ設定
export DEBUG=true
export LOG_LEVEL=INFO

# SAM Local設定（自動設定されるが明示的に指定可能）
export AWS_SAM_LOCAL=true
```

### samconfig.tomlによる環境設定

```toml
version = 0.1

[default.deploy.parameters]
stack_name = "wambda-dev"
region = "ap-northeast-1"

[production.deploy.parameters]
stack_name = "wambda-prod"
region = "ap-northeast-1"
profile = "production"
```

## 🔧 効率的な開発ワークフロー

### ホットリロード設定

```bash
# ファイル変更を監視してSAMを自動再起動
sam local start-api --watch

# 静的ファイルの変更を監視
npm run watch  # package.jsonで設定
```

### 複数環境での開発

```bash
# 環境変数で環境を切り替え
export AWS_PROFILE=development
wambda-admin.py proxy

# 異なる環境での実行
export AWS_PROFILE=staging
wambda-admin.py proxy -p 9000

# samconfig.tomlで環境別デプロイ
sam deploy --config-env development
sam deploy --config-env production
```

## 🧪 テスト機能

### コマンドラインテスト

```bash
# GETリクエストのテスト
wambda-admin.py get -p /
wambda-admin.py get -p /api/users
wambda-admin.py get -p /blog/my-post

# リクエストボディ付きPOSTテスト
wambda-admin.py get -p /api/users -m POST -b '{"name":"John"}'

# カスタムイベントファイルでテスト
wambda-admin.py get -e event.json
```

### テストイベントファイル

```json
# event.json
{
  "path": "/api/users",
  "requestContext": {
    "httpMethod": "POST"
  },
  "body": "name=John&email=john@example.com"
}
```

### ユニットテスト

```python
# tests/test_views.py
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '../Lambda'))

from lambda_function import lambda_handler

def test_index_view():
    """トップページのテスト"""
    event = {
        "path": "/",
        "requestContext": {
            "httpMethod": "GET"
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200
    assert "WAMBDAアプリ" in response["body"]

def test_api_endpoint():
    """APIエンドポイントのテスト"""
    event = {
        "path": "/api/data",
        "requestContext": {
            "httpMethod": "GET"
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200
    data = json.loads(response["body"])
    assert "status" in data

def test_protected_view():
    """認証が必要なページのテスト"""
    event = {
        "path": "/profile",
        "requestContext": {
            "httpMethod": "GET"
        }
    }
    
    response = lambda_handler(event, None)
    
    # 未認証の場合はリダイレクト
    assert response["statusCode"] == 302
    assert "Location" in response["headers"]
```

## 🔍 デバッグとログ

### ログレベルの設定

```python
# Lambda/project/settings.py
import logging

if DEBUG:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### デバッグビューの作成

```python
# Lambda/project/debug_views.py
from wambda.shortcuts import render, json_response

def debug_info(master):
    """デバッグ情報表示"""
    if not master.settings.DEBUG:
        return render(master, "404.html", code=404)
    
    debug_data = {
        "request": {
            "method": master.request.method,
            "path": master.request.path,
            "body": master.request.body,
            "auth": master.request.auth,
            "username": master.request.username
        },
        "environment": {
            "local": master.local,
            "debug": master.settings.DEBUG,
            "base_dir": master.settings.BASE_DIR
        },
        "system": {
            "python_version": sys.version,
            "aws_sam_local": os.getenv("AWS_SAM_LOCAL"),
            "aws_region": os.getenv("AWS_DEFAULT_REGION")
        }
    }
    
    return json_response(master, debug_data)

def debug_headers(master):
    """リクエストヘッダーの表示"""
    if not master.settings.DEBUG:
        return render(master, "404.html", code=404)
    
    headers = master.event.get("headers", {})
    return json_response(master, {"headers": headers})
```

### エラーページの改善

```python
# Lambda/project/views.py
def custom_error_render(master, error_message):
    """カスタムエラーページ"""
    if master.settings.DEBUG:
        # 開発環境では詳細なエラー情報を表示
        import traceback
        error_html = f"""
        <h1>🐛 デバッグ情報</h1>
        <h2>エラーメッセージ</h2>
        <pre>{error_message}</pre>
        <h2>リクエスト情報</h2>
        <pre>Path: {master.request.path}</pre>
        <pre>Method: {master.request.method}</pre>
        <pre>Body: {master.request.body}</pre>
        <h2>スタックトレース</h2>
        <pre>{traceback.format_exc()}</pre>
        """
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/html; charset=UTF-8"},
            "body": error_html
        }
    else:
        # 本番環境では一般的なエラーページ
        return render(master, "500.html", code=500)
```

## 🎭 Mock環境での開発

WAMBDAの組み込みMock機能を使用することで、実際のAWSサービスを使用せずに開発できます。

### Mock機能の有効化

```python
# Lambda/project/settings.py
DEBUG = True      # デバッグ情報を表示
USE_MOCK = True   # Mock機能を有効化
NO_AUTH = True    # 認証をバイパス（開発時）
```

### Mockデータの設定

プロジェクト内に`Lambda/mock/`ディレクトリを作成し、各AWSサービス用のモックデータを設定：

```python
# Lambda/mock/ssm.py
import boto3

def set_data():
    """SSM Parameter Storeのモックデータを設定"""
    ssm = boto3.client('ssm')
    parameters = [
        {
            'Name': '/MyProject/Database/Host',
            'Value': 'localhost',
            'Type': 'String'
        },
        {
            'Name': '/MyProject/API/Key',
            'Value': 'mock-api-key',
            'Type': 'SecureString'
        }
    ]
    
    for param in parameters:
        ssm.put_parameter(
            Name=param['Name'],
            Value=param['Value'],
            Type=param['Type'],
            Overwrite=True
        )
```

```python
# Lambda/mock/dynamodb.py
import boto3

def set_data():
    """DynamoDBのモックデータを設定"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
    
    # テーブル作成
    try:
        table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        
        # サンプルデータ投入
        items = [
            {'user_id': '1', 'name': 'テストユーザー1'},
            {'user_id': '2', 'name': 'テストユーザー2'}
        ]
        for item in items:
            table.put_item(Item=item)
            
    except Exception as e:
        print(f"Mock setup error: {e}")
```

### Mock環境での開発ワークフロー

```bash
# 1. Mock設定の確認
wambda-admin.py get -p /debug/config  # Mock設定状況確認

# 2. Mockデータを使った機能テスト
wambda-admin.py get -p /api/users      # DynamoDBモックデータ取得
wambda-admin.py get -p /config         # SSMモックパラメータ取得

# 3. プロキシサーバー起動（Mock環境）
wambda-admin.py proxy                  # ブラウザでhttp://localhost:8000

# 4. 開発とテストのサイクル
# コード変更 → getコマンドでテスト → ブラウザで確認
```

### Mock環境でのデバッグ

Mock機能では詳細なログが出力されます：

```bash
$ wambda-admin.py get -p /api/users
Importing lambda_handler from /path/to/Lambda/lambda_function.py
Executing lambda_handler...
Setting up SSM mock data...
Set SSM parameter: /MyProject/Database/Host
Created DynamoDB table: Users
Inserted 2 items into Users
Event: {
  "path": "/api/users",
  ...
}
Response: {
  "statusCode": 200,
  "body": "[{\"user_id\": \"1\", \"name\": \"テストユーザー1\"}]"
}
```

## 🗄️ データベース開発

### DynamoDB Local

```bash
# DynamoDB Localを起動
docker run -p 8000:8000 amazon/dynamodb-local

# テーブル作成
aws dynamodb create-table \
  --table-name users \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --endpoint-url http://localhost:8000
```

### データベース接続の設定

```python
# Lambda/project/database.py
import boto3
import os

def get_dynamodb_resource():
    """DynamoDBリソースを取得"""
    if os.getenv("AWS_SAM_LOCAL") == "true":
        # ローカル開発環境
        return boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='ap-northeast-1'
        )
    else:
        # AWS環境
        return boto3.resource('dynamodb')

def get_users_table():
    """ユーザーテーブルを取得"""
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table('users')
```


## 📊 パフォーマンス最適化

### 開発時のキャッシュ設定

```python
# Lambda/project/settings.py
if DEBUG:
    # 開発時はキャッシュを無効化
    CACHE_ENABLED = False
    TEMPLATE_CACHE = False
else:
    # 本番環境ではキャッシュを有効化
    CACHE_ENABLED = True
    TEMPLATE_CACHE = True
```

### 静的ファイルの最適化

```javascript
// package.json
{
  "scripts": {
    "dev": "npm run watch-css & npm run watch-js",
    "watch-css": "sass static/scss:static/css --watch --style expanded",
    "watch-js": "webpack --mode development --watch",
    "build": "npm run build-css && npm run build-js",
    "build-css": "sass static/scss:static/css --style compressed",
    "build-js": "webpack --mode production"
  }
}
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. ポートが既に使用されている

```bash
# ポートの使用状況を確認
lsof -i :3000
lsof -i :8000
lsof -i :8080

# プロセスを終了
kill -9 <PID>

# または別のポートを使用
# CLI オプションでポート番号を変更
```

#### 2. 静的ファイルが見つからない

```bash
# 静的ファイルディレクトリの確認
ls -la static/

# 権限の確認
chmod -R 755 static/

# プロキシサーバーの再起動
wambda-admin.py proxy
```

#### 3. Lambda関数のインポートエラー

```python
# Lambda/lambda_function.py
import sys
import os

# パスの確認とデバッグ
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# プロジェクトディレクトリを追加
sys.path.append(os.path.dirname(__file__))
```

#### 4. 認証が動作しない

```bash
# 環境変数の確認
echo $AWS_SAM_LOCAL
echo $AWS_DEFAULT_REGION

# CLI オプションの確認
cat CLI オプション | jq '.'

# ログの確認
tail -f ~/.aws/sam/logs/sam-app.log
```

## 🔄 継続的開発

### Git フック

```bash
#!/bin/sh
# .git/hooks/pre-commit
# コミット前にテストを実行

echo "Running tests..."
python -m pytest tests/

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "Running linting..."
flake8 Lambda/

if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

echo "All checks passed. Committing..."
```

### Makefile

```makefile
# Makefile
.PHONY: dev test build deploy clean

dev:
	wambda-admin.py proxy

test:
	python -m pytest tests/ -v

build:
	sam build

deploy:
	sam deploy --no-confirm-changeset

clean:
	rm -rf .aws-sam/
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete

install:
	pip install -r requirements.txt
	npm install

lint:
	flake8 Lambda/
	black Lambda/ --check

format:
	black Lambda/
	isort Lambda/
```

## 📋 ベストプラクティス

### 1. 開発環境の標準化

```bash
# .env ファイルで環境変数を管理
# .env
AWS_SAM_LOCAL=true
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=http://localhost:8000
```

### 2. コード品質の維持

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
```

### 3. ドキュメント化

```python
# Lambda/project/README.md
# プロジェクト固有のREADME

## 開発環境セットアップ
1. `python -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `make dev`

## テスト実行
`make test`

## デプロイ
`make deploy`
```

## 🔧 プロキシサーバーの技術詳細

### リクエスト・レスポンス処理

プロキシサーバーは以下の方式でリクエストを処理します：

```python
# 基本的な処理フロー
1. ブラウザからのリクエストを受信 (localhost:8000)
2. パスに基づいて転送先を決定:
   - /static/* → 静的ファイルサーバー (localhost:8080)
   - その他 → SAM Local (localhost:3000)
3. ヘッダーを適切に転送
4. レスポンスを受信して適切に処理
5. ブラウザにレスポンスを返却
```

### 認証・Cookieの処理

WAMBDAの認証システムは複数のCookieを使用するため、プロキシサーバーでは特別な処理が必要です：

#### 問題と解決策

**問題**: デフォルトの`urllib.request.urlopen()`は：
- 302リダイレクトを自動追跡してしまう
- 複数の`Set-Cookie`ヘッダーを適切に処理しない

**解決策**: カスタムハンドラーによる処理
```python
# リダイレクト自動追跡を無効化
class NoRedirectErrorHandler(urllib.request.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response  # 3xxレスポンスでもエラーとして扱わない

# 複数Set-Cookieヘッダーの個別処理
for cookie_header in set_cookie_headers:
    self.send_header('Set-Cookie', cookie_header)
```

#### 修正された処理フロー

1. **ログイン成功時**:
   - SAM Local: `302リダイレクト + Set-Cookie` レスポンス
   - プロキシ: 302をそのまま転送（自動追跡しない）
   - ブラウザ: 302を受信してCookieを保存、`/`に自動リダイレクト

2. **次回リクエスト時**:
   - ブラウザ: Cookieヘッダー付きでリクエスト送信
   - プロキシ: Cookieヘッダーをそのまま転送
   - SAM Local: 認証済みとして処理

### デバッグとログ

#### プロキシサーバーのデバッグログ

開発時にプロキシサーバーの詳細ログを確認できます：

```bash
# プロキシサーバー起動（詳細ログ付き）
wambda-admin.py proxy

# ログ例
[PROXY] POST /accounts/login -> http://localhost:3000/accounts/login
[PROXY] Response status: 302
[PROXY] Found 1 Set-Cookie headers:
[PROXY]   Cookie 1: no_auth_user=username; Path=/; Expires=...
```

#### Lambda関数の直接デバッグ

Lambda関数を直接実行してテストできます（SAM Local不要）：

```bash
# 基本的な使用方法
cd Lambda
PYTHONPATH=../wambda/lib python3 lambda_function.py -p /

# POSTリクエストのテスト
PYTHONPATH=../wambda/lib python3 lambda_function.py \
  -p /accounts/login \
  -m POST \
  -b "username=test&password=test" \
  -H "Content-Type: application/x-www-form-urlencoded"

# JSONリクエストのテスト
PYTHONPATH=../wambda/lib python3 lambda_function.py \
  -p /api/data \
  -m POST \
  -b '{"key":"value"}' \
  --json

# クエリパラメータ付きリクエスト
PYTHONPATH=../wambda/lib python3 lambda_function.py \
  -p /api/search \
  -q "query=python&limit=10"
```

**デバッグ用オプション**:
- `-p, --path`: テストするパス（デフォルト: `/`）
- `-m, --method`: HTTPメソッド（デフォルト: `GET`）
- `-b, --body`: リクエストボディ
- `-H, --header`: ヘッダー追加（例: `'Content-Type: application/json'`）
- `-q, --query`: クエリパラメータ（例: `'key1=value1&key2=value2'`）
- `--json`: ボディをJSON形式として解析
- `--quiet`: 最小限の出力（ステータスコードのみ）

**便利なラッパースクリプト**:
```bash
# プロジェクトルートにdebug.shを配置
./debug.sh -p /accounts/login -m POST -b "username=test&password=test"
```

## 次のステップ

ローカル開発環境を理解したら、以下のページで本番環境へのデプロイについて学習してください：

- [デプロイメント](./deployment.md) - 本番環境への安全なデプロイ
- [ベストプラクティス](./best-practices.md) - 効率的な開発手法

---

[← 前: 認証とCognito連携](./authentication.md) | [ドキュメント目次に戻る](./README.md) | [次: デプロイメント →](./deployment.md)
