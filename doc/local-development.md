# ローカル開発環境

HADSは効率的なローカル開発環境を提供し、AWS環境をシミュレートしながら快適に開発できます。このページでは、ローカル開発環境の詳細な設定と使用方法を説明します。

## 🏗️ ローカル開発の仕組み

### 3つのサーバー構成

HADSのローカル開発環境は3つのサーバーで構成されています：

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
hads-admin.py proxy
```

### 個別起動

```bash
# ターミナル1: SAM Local
sam local start-api

# ターミナル2: 静的ファイルサーバー
hads-admin.py static

# ターミナル3: プロキシサーバー
hads-admin.py proxy
```

## ⚙️ CLIオプションによる詳細設定

### ポート設定

```bash
# プロキシサーバーのカスタムポート設定
hads-admin.py proxy -p 9000 -s 3001 --static-port 8081

# 静的ファイルサーバーのカスタム設定
hads-admin.py static -p 8090 -d assets --static-url /files
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
stack_name = "hads-dev"
region = "ap-northeast-1"

[production.deploy.parameters]
stack_name = "hads-prod"
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
hads-admin.py proxy

# 異なる環境での実行
export AWS_PROFILE=staging
hads-admin.py proxy -p 9000

# samconfig.tomlで環境別デプロイ
sam deploy --config-env development
sam deploy --config-env production
```

## 🧪 テスト機能

### コマンドラインテスト

```bash
# GETリクエストのテスト
hads-admin.py get -p /
hads-admin.py get -p /api/users
hads-admin.py get -p /blog/my-post

# POSTリクエストのテスト
hads-admin.py get -p-event event.json
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
    assert "HADSアプリ" in response["body"]

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
from hads.shortcuts import render, json_response

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

## 🔧 開発ツール連携

### VS Code設定

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "files.associations": {
        "*.yaml": "yaml",
        "admin*.json": "jsonc"
    },
    "yaml.schemas": {
        "https://raw.githubusercontent.com/aws/serverless-application-model/main/samtranslator/schema/schema.json": "*template.yaml"
    }
}
```

### launch.json（デバッグ設定）

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Lambda Function",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/Lambda/lambda_function.py",
            "console": "integratedTerminal",
            "env": {
                "AWS_SAM_LOCAL": "true"
            },
            "args": []
        }
    ]
}
```

### tasks.json（タスク設定）

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Local Server",
            "type": "shell",
            "command": "hads-admin.py",
            "args": ["CLI オプション", "--local-server-run", "proxy"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "python",
            "args": ["-m", "pytest", "tests/"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            }
        }
    ]
}
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
hads-admin.py proxy
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
	hads-admin.py proxy

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

## 次のステップ

ローカル開発環境を理解したら、以下のページで本番環境へのデプロイについて学習してください：

- [デプロイメント](./deployment.md) - 本番環境への安全なデプロイ
- [ベストプラクティス](./best-practices.md) - 効率的な開発手法

---

[← 前: 認証とCognito連携](./authentication.md) | [ドキュメント目次に戻る](./README.md) | [次: デプロイメント →](./deployment.md)
