# コマンドラインツール

HADSは強力なコマンドラインツール `hads-admin.py` を提供し、プロジェクトの作成から本番デプロイまでを統合的に管理できます。このページでは、コマンドラインツールの詳細な使用方法を説明します。

## 🛠️ hads-admin.py の概要

`hads-admin.py` はHADSプロジェクトの中心的な管理ツールです。

### 基本構文

```bash
hads-admin.py [admin-file] [options]
```

- `admin-file`: プロジェクト設定ファイル（admin.json）
- `options`: 実行する操作

## 📋 利用可能なオプション

### プロジェクト管理

#### --init: プロジェクト初期化

```bash
# 新しいプロジェクトを作成
hads-admin.py --init
```

対話的にプロジェクト設定を入力：
```
Enter project name (directory name): my-app
Enter suffix (to make resources unique, default is same as project name): my-app-prod
Enter python version (default is 3.12): 3.12
Enter region (default is ap-northeast-1): ap-northeast-1
```

生成されるファイル：
- `admin.json` - プロジェクト設定
- `template.yaml` - CloudFormationテンプレート
- `samconfig.toml` - SAM設定
- `Lambda/` - アプリケーションコード
- `static/` - 静的ファイル（空）

### ローカル開発

#### --local-server-run: 開発サーバー起動

```bash
# SAM Localサーバー
hads-admin.py admin.json --local-server-run sam

# 静的ファイルサーバー
hads-admin.py admin.json --local-server-run static

# プロキシサーバー（推奨）
hads-admin.py admin.json --local-server-run proxy
```

各サーバーの詳細：

| サーバー | ポート | 説明 |
|----------|--------|------|
| sam | 3000 | Lambda関数をローカル実行 |
| static | 8080 | 静的ファイル配信 |
| proxy | 8000 | 統合エンドポイント |

### テスト機能

#### --test-get: GETリクエストテスト

```bash
# トップページのテスト
hads-admin.py admin.json --test-get /

# 特定のパスをテスト
hads-admin.py admin.json --test-get /api/users
hads-admin.py admin.json --test-get /blog/my-post

# パラメータ付きパス
hads-admin.py admin.json --test-get /user/123/profile
```

#### --test-get-event: イベントファイルでテスト

```bash
# カスタムイベントでテスト
hads-admin.py admin.json --test-get-event event.json
```

イベントファイルの例：
```json
{
  "path": "/api/users",
  "requestContext": {
    "httpMethod": "POST"
  },
  "body": "name=John&email=john@example.com",
  "headers": {
    "Content-Type": "application/x-www-form-urlencoded"
  }
}
```

### ビルドとデプロイ

#### --build: SAMビルド

```bash
# プロジェクトをビルド
hads-admin.py admin.json --build

# 特定のプロファイルでビルド
hads-admin.py admin.json --build --profile production
```

#### --deploy: デプロイ実行

```bash
# 通常デプロイ（確認あり）
hads-admin.py admin.json --deploy

# 自動デプロイ（確認スキップ）
hads-admin.py admin.json --deploy --no-confirm-changeset

# ビルドとデプロイを同時実行
hads-admin.py admin.json --build --deploy
```

#### --delete: スタック削除

```bash
# CloudFormationスタックを削除
hads-admin.py admin.json --delete
```

⚠️ **注意**: この操作は取り消せません。本番環境では特に注意してください。

### 静的ファイル管理

#### --static-sync2s3: S3同期

```bash
# 静的ファイルをS3にアップロード
hads-admin.py admin.json --static-sync2s3
```

内部で実行されるコマンド：
```bash
aws s3 sync static/ s3://your-bucket/static/ --delete
```

### AWS CLI統合

#### --aws: AWS CLIコマンド実行

```bash
# S3バケット一覧
hads-admin.py admin.json --aws s3 ls

# Lambda関数一覧
hads-admin.py admin.json --aws lambda list-functions

# CloudFormationスタック状態確認
hads-admin.py admin.json --aws cloudformation describe-stacks --stack-name my-stack
```

#### --sam: SAM CLIコマンド実行

```bash
# SAM validate
hads-admin.py admin.json --sam validate

# SAM logs
hads-admin.py admin.json --sam logs --name MyFunction --tail

# SAM sync（開発中のホットデプロイ）
hads-admin.py admin.json --sam sync --watch
```

## 🔧 認証とプロファイル

### AWS認証設定

#### --profile: AWSプロファイル指定

```bash
# 開発環境プロファイル
hads-admin.py admin.json --profile dev --deploy

# 本番環境プロファイル
hads-admin.py admin.json --profile prod --deploy
```

#### --region: リージョン指定

```bash
# 特定のリージョンでデプロイ
hads-admin.py admin.json --region us-east-1 --deploy

# 東京リージョン
hads-admin.py admin.json --region ap-northeast-1 --deploy
```

プロファイルとリージョンの優先順位：
1. コマンドライン引数（`--profile`, `--region`）
2. admin.jsonの設定
3. AWS CLIのデフォルト設定

## 📄 admin.json 詳細仕様

### 基本構造

```json
{
  "region": "ap-northeast-1",
  "profile": "default",
  "static": {
    "local": "static",
    "s3": "s3://your-bucket-name/static/"
  },
  "local_server": {
    "port": {
      "static": 8080,
      "proxy": 8000,
      "sam": 3000
    }
  }
}
```

### 高度な設定

```json
{
  "region": "ap-northeast-1",
  "profile": "production",
  "static": {
    "local": "static",
    "s3": "s3://prod-bucket/static/",
    "cloudfront": "https://d123456789.cloudfront.net"
  },
  "local_server": {
    "port": {
      "static": 8080,
      "proxy": 8000,
      "sam": 3000
    },
    "host": "0.0.0.0",
    "cors": true
  },
  "deployment": {
    "stack_name": "my-production-stack",
    "capabilities": ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
    "parameter_overrides": {
      "Environment": "production",
      "DomainName": "api.example.com"
    }
  },
  "environment": {
    "AWS_SAM_LOCAL": "false",
    "LOG_LEVEL": "INFO"
  }
}
```

### 設定項目の説明

| 項目 | 説明 | 必須 |
|------|------|------|
| `region` | AWSリージョン | ✅ |
| `profile` | AWS認証プロファイル | ❌ |
| `static.local` | ローカル静的ファイルパス | ✅ |
| `static.s3` | S3静的ファイルパス | ❌ |
| `static.cloudfront` | CloudFront URL | ❌ |
| `local_server.port.*` | 各サーバーのポート | ✅ |
| `deployment.stack_name` | CloudFormationスタック名 | ❌ |
| `environment.*` | 環境変数 | ❌ |

## 🚀 実践的な使用例

### 1. 新規プロジェクト作成から初回デプロイ

```bash
# 1. プロジェクト初期化
hads-admin.py --init

# 2. プロジェクトディレクトリに移動
cd my-new-project

# 3. admin.jsonを編集（S3バケット名など）

# 4. ローカルテスト
hads-admin.py admin.json --test-get /

# 5. ローカルサーバー起動
hads-admin.py admin.json --local-server-run proxy

# 6. 開発とテスト
# ...

# 7. 初回デプロイ
hads-admin.py admin.json --build --deploy

# 8. 静的ファイルアップロード
hads-admin.py admin.json --static-sync2s3
```

### 2. 継続的開発とデプロイ

```bash
# 日常的な開発サイクル

# ローカル開発
hads-admin.py admin.json --local-server-run proxy

# 変更後のテスト
hads-admin.py admin.json --test-get /new-feature

# 本番デプロイ
hads-admin.py admin.json --build --deploy --no-confirm-changeset

# 静的ファイル更新
hads-admin.py admin.json --static-sync2s3
```

### 3. 複数環境での開発

```bash
# 開発環境
cp admin.json admin-dev.json
hads-admin.py admin-dev.json --profile dev --deploy

# ステージング環境
cp admin.json admin-staging.json
hads-admin.py admin-staging.json --profile staging --deploy

# 本番環境
hads-admin.py admin.json --profile prod --deploy
```

### 4. デバッグとトラブルシューティング

```bash
# ログの確認
hads-admin.py admin.json --sam logs --name MyFunction --tail

# スタック状態の確認
hads-admin.py admin.json --aws cloudformation describe-stacks

# Lambda関数の詳細確認
hads-admin.py admin.json --aws lambda get-function --function-name MyFunction

# S3バケットの内容確認
hads-admin.py admin.json --aws s3 ls s3://my-bucket/static/ --recursive
```

## 🔧 カスタマイズと拡張

### 環境変数の設定

```bash
# 一時的な環境変数設定
AWS_PROFILE=production hads-admin.py admin.json --deploy

# 永続的な設定
export AWS_PROFILE=production
export AWS_DEFAULT_REGION=ap-northeast-1
hads-admin.py admin.json --deploy
```

### シェルスクリプトでの自動化

```bash
#!/bin/bash
# deploy.sh

set -e

ENVIRONMENT=${1:-development}
ADMIN_FILE="admin-${ENVIRONMENT}.json"

echo "🚀 Deploying to ${ENVIRONMENT} environment..."

# プロファイルの確認
if [ "$ENVIRONMENT" = "production" ]; then
    PROFILE="prod"
elif [ "$ENVIRONMENT" = "staging" ]; then
    PROFILE="staging"
else
    PROFILE="dev"
fi

# ビルドとデプロイ
echo "📦 Building..."
hads-admin.py "$ADMIN_FILE" --profile "$PROFILE" --build

echo "🚀 Deploying..."
hads-admin.py "$ADMIN_FILE" --profile "$PROFILE" --deploy --no-confirm-changeset

echo "📁 Syncing static files..."
hads-admin.py "$ADMIN_FILE" --profile "$PROFILE" --static-sync2s3

echo "✅ Deployment completed successfully!"
```

### Makefileとの連携

```makefile
# Makefile

ADMIN_FILE ?= admin.json
PROFILE ?= default

.PHONY: dev test build deploy sync clean

dev:
	hads-admin.py $(ADMIN_FILE) --local-server-run proxy

test:
	hads-admin.py $(ADMIN_FILE) --test-get /

build:
	hads-admin.py $(ADMIN_FILE) --profile $(PROFILE) --build

deploy: build
	hads-admin.py $(ADMIN_FILE) --profile $(PROFILE) --deploy

sync:
	hads-admin.py $(ADMIN_FILE) --profile $(PROFILE) --static-sync2s3

clean:
	hads-admin.py $(ADMIN_FILE) --profile $(PROFILE) --delete

full-deploy: deploy sync

# 環境別デプロイ
deploy-dev:
	$(MAKE) deploy ADMIN_FILE=admin-dev.json PROFILE=dev

deploy-prod:
	$(MAKE) deploy ADMIN_FILE=admin-prod.json PROFILE=prod
```

## 🐛 トラブルシューティング

### よくあるエラーと解決方法

#### 1. admin.jsonが見つからない

```bash
Error: file 'admin.json' does not exist
```

**解決方法:**
- ファイル名を確認
- 正しいディレクトリにいるか確認
- `hads-admin.py --init` でプロジェクトを初期化

#### 2. AWS認証エラー

```bash
Unable to locate credentials
```

**解決方法:**
```bash
# AWS CLIの設定確認
aws configure list

# プロファイルの確認
aws configure list-profiles

# 認証情報の再設定
aws configure --profile your-profile
```

#### 3. SAMビルドエラー

```bash
Build failed
```

**解決方法:**
```bash
# template.yamlの構文確認
hads-admin.py admin.json --sam validate

# 詳細なエラー確認
hads-admin.py admin.json --sam build --debug
```

#### 4. 静的ファイル同期エラー

```bash
S3 sync failed
```

**解決方法:**
```bash
# S3バケットの存在確認
hads-admin.py admin.json --aws s3 ls s3://your-bucket

# 権限の確認
hads-admin.py admin.json --aws s3api get-bucket-location --bucket your-bucket
```

## 📋 ベストプラクティス

### 1. バージョン管理

```bash
# admin.json は環境ごとに分ける
admin-dev.json
admin-staging.json  
admin-prod.json

# 機密情報は環境変数で管理
export S3_BUCKET_NAME="my-prod-bucket"
```

### 2. CI/CD 連携

```yaml
# .github/workflows/deploy.yml
name: Deploy HADS App

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
          
      - name: Install HADS
        run: pip install hads
        
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
          
      - name: Deploy
        run: |
          hads-admin.py admin-prod.json --build --deploy --no-confirm-changeset
          hads-admin.py admin-prod.json --static-sync2s3
```

### 3. ログ管理

```bash
# ログファイルに出力
hads-admin.py admin.json --deploy 2>&1 | tee deploy.log

# 日付付きログ
hads-admin.py admin.json --deploy 2>&1 | tee "deploy-$(date +%Y%m%d-%H%M%S).log"
```

## 次のステップ

コマンドラインツールの使い方を理解したら、以下のページで実践的な開発手法を学習してください：

- [ベストプラクティス](./best-practices.md) - 効率的な開発手法
- [デプロイメント](./deployment.md) - 本番環境へのデプロイ

---

[← 前: ローカル開発環境](./local-development.md) | [ドキュメント目次に戻る](./README.md) | [次: ベストプラクティス →](./best-practices.md)
