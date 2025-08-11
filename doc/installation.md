# インストールと初期設定

このページでは、HADSフレームワークをインストールして、開発環境を構築する手順を説明します。

## 前提条件

HADSを使用するために、以下のツールがインストールされている必要があります：

### 必須ツール

- **Python 3.9以上** - HADSフレームワーク本体
- **AWS CLI** - AWSリソースの管理
- **Git** - ソースコード管理

### 用途別ツール

- **AWS SAM CLI** - ローカル開発サーバー（proxy）とAWSデプロイ用
  - `hads-admin.py proxy` 使用時に必要
  - AWS環境へのデプロイ時に必要
  - **注意**: `hads-admin.py get` によるテストでは不要

### 推奨ツール

- **Docker** - SAM Localでのローカル実行（proxy使用時）
- **VS Code** - Python開発に適したエディタ

## インストール手順

### 1. AWS CLI のインストール

```bash
# macOSの場合
brew install awscli

# Windowsの場合
# AWS公式サイトからインストーラーをダウンロード

# Linuxの場合
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. AWS SAM CLI のインストール

```bash
# macOSの場合
brew install aws-sam-cli

# Windowsの場合
# AWS公式サイトからMSIインストーラーをダウンロード

# Linuxの場合
pip install aws-sam-cli
```

### 3. HADSフレームワークのインストール

#### PyPI登録について

HADSは名前の重複により、PyPIへの登録が困難な状況です。以下の選択肢を検討中：

- **現状維持**: GitHubリポジトリからの直接インストール
- **名前変更**: 新しい名前でPyPIに登録（将来的な選択肢）

#### 現在のインストール方法

GitHubリポジトリから直接インストール：

```bash
# リポジトリのクローン
git clone https://github.com/h-akira/hads.git
cd hads

# 開発モードでインストール
pip install -e .

# または通常のインストール
pip install .
```

#### パッケージが利用可能になるコマンド

インストール後、以下のコマンドが利用可能になります：

```bash
# HADSプロジェクト管理ツール
hads-admin.py --help

# または相対パスから直接実行
python bin/hads-admin.py --help
```

## AWS認証設定

### AWS認証情報の設定

```bash
aws configure
```

プロンプトに従って以下を入力：
- **AWS Access Key ID**: AWSアクセスキー
- **AWS Secret Access Key**: AWSシークレットキー
- **Default region name**: `ap-northeast-1` (東京リージョン推奨)
- **Default output format**: `json`

### プロファイルの設定（複数環境の場合）

```bash
# 開発環境用プロファイル
aws configure --profile dev

# 本番環境用プロファイル
aws configure --profile prod
```

## 最初のプロジェクト作成

### 1. プロジェクトの初期化

```bash
hads-admin.py --init
```

対話的にプロジェクト設定を入力：

```
Enter project name (directory name): my-first-app
Enter suffix (to make resources unique, default is same as project name): my-first-app
Enter python version (default is 3.12): 3.12
Enter region (default is ap-northeast-1): ap-northeast-1
```

### 2. 生成されたファイル構造

```
my-first-app/
├── samconfig.toml      # SAM設定ファイル
├── template.yaml       # CloudFormationテンプレート
├── static/            # 静的ファイルディレクトリ
└── Lambda/
    ├── lambda_function.py     # メインハンドラー
    ├── project/
    │   ├── settings.py        # Django風設定ファイル
    │   └── urls.py           # URLルーティング
    ├── templates/            # Jinja2テンプレート
    └── requirements.txt      # Python依存関係
```

### 3. 環境設定

環境変数でAWS認証を設定：

```bash
# AWSプロファイルの設定
export AWS_PROFILE=default
export AWS_DEFAULT_REGION=ap-northeast-1

# ローカル開発時（SAM Local使用時は自動設定）
export AWS_SAM_LOCAL=true
```

## 開発環境の確認

### 1. ローカルでの動作確認

```bash
cd my-first-app

# SAM Local でAPIサーバーを起動
sam build && sam deploy sam
```

### 2. ブラウザでアクセス

ブラウザで `http://localhost:3000` にアクセスして、正常に動作することを確認します。

### 3. テスト用エンドポイントの確認

```bash
# Lambda関数の直接テスト（SAM CLI不要）
hads-admin.py get

# 特定パスのテスト
hads-admin.py get -p /api/test
```

## 静的ファイルの設定

### 1. 静的ファイルディレクトリの作成

```bash
mkdir static
mkdir static/css
mkdir static/js
mkdir static/images
```

### 2. S3バケットの作成（本番環境用）

```bash
aws s3 mb s3://your-unique-bucket-name --region ap-northeast-1
```

### 3. 静的ファイルの同期

```bash
# S3に静的ファイルをアップロード
sam build && sam deploy2s3
```

## エディタの設定

### VS Code の推奨拡張機能

- **Python** - Python開発サポート
- **AWS Toolkit** - AWS統合
- **YAML** - template.yamlの編集

### .vscode/settings.json

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "yaml.schemas": {
        "https://raw.githubusercontent.com/aws/serverless-application-model/main/samtranslator/schema/schema.json": "*template.yaml"
    }
}
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. AWS認証エラー

```bash
# 認証情報を確認
aws sts get-caller-identity

# プロファイルを指定して確認
aws sts get-caller-identity --profile your-profile
```

#### 2. SAM CLIが見つからない

```bash
# SAM CLIのインストール確認
sam --version

# パスの確認
which sam
```

#### 3. Pythonバージョンの不整合

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# HADSのインストール
pip install -e .
```

## 次のステップ

インストールが完了したら、以下のページに進んでください：

- [クイックスタート](./quickstart.md) - 簡単なアプリケーションの作成
- [プロジェクト構造](./project-structure.md) - プロジェクトの詳細な構造

---

[← ドキュメント目次に戻る](./README.md) | [次: クイックスタート →](./quickstart.md)
