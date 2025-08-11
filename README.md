# HADS

## 概要

HADS（h-akira AWS Develop with Serverless）は、AWSでサーバーレスWebアプリケーションを開発するためのPythonフレームワークです。このフレームワークは[HAD](https://github.com/h-akira/had)の後継として開発されましたが、設計思想が大きく異なるため、用途によってはHADの継続使用を推奨する場合もあります。

## 設計思想

- **SAMの活用**: AWS Serverless Application Modelを使用したインフラストラクチャの管理
- **単一Lambda**: すべてのリクエストを1つのLambda関数で処理
- **S3静的ファイル配信**: 静的ファイルはS3から効率的に配信
- **ローカル開発**: 本番環境と同等の開発環境をローカルで構築
- **Django風の設計**: urls.py、views.py、テンプレートによるMVC構造

## アーキテクチャ

### システム構成

HADSで構築されるAWSシステムの構成図：

![structure](images/structure.png)

- **API Gateway**: HTTPリクエストの受付と Lambda への転送
- **Lambda関数**: 単一関数ですべてのルーティングとビジネスロジックを処理
- **S3**: 静的ファイル（CSS、JS、画像）の配信
- **その他のAWSサービス**: 必要に応じてSAMテンプレートで追加定義

### Lambda内部構造

Lambda関数内の処理フローとコンポーネント構成：

![lambda](images/lambda.png)

1. **リクエスト受信**: API Gatewayからイベント情報を受信
2. **初期化処理**: Masterクラスによる設定読み込みと認証処理
3. **ルーティング**: urls.pyの設定に基づいてビュー関数を決定
4. **ビュー実行**: views.pyの関数によりビジネスロジックを実行
5. **レスポンス生成**: テンプレートエンジンによるHTML生成とHTTPレスポンス返却  

## 📚 Documentation

**Note: All documentation is written in Japanese.**

Comprehensive documentation is available in the [doc](./doc/README.md) directory.

### 🚀 Getting Started
- [Installation and Setup](./doc/installation.md)
- [Quick Start Guide](./doc/quickstart.md)

### 📖 Basic Guides
- [Project Structure](./doc/project-structure.md)
- [URL Routing](./doc/url-routing.md)
- [Views and Handlers](./doc/views-handlers.md)
- [Template System](./doc/templates.md)

### 🔧 Advanced Features
- [Authentication & Cognito Integration](./doc/authentication.md)
- [Local Development Environment](./doc/local-development.md)
- [Deployment Guide](./doc/deployment.md)

## 🚀 クイックスタート

HADSによる基本的な開発ワークフロー：

### 1. プロジェクトの初期化
```bash
# 対話式でテンプレートを選択
hads-admin.py init -n my-project

# テンプレートを指定して作成
hads-admin.py init -n my-project -t SSR001
```

利用可能なテンプレート：
- **SSR001**: サーバーサイドレンダリングテンプレート（認証機能付き）
- **API001**: APIテンプレート（Vue、React、Angular等のフロントエンド用）

### 2. ローカル開発環境の起動
```bash
cd my-project

# プロキシサーバーを起動（推奨: SAM Local + 静的ファイルサーバーを統合）
hads-admin.py proxy

# 個別にサーバーを起動する場合
hads-admin.py static          # 静的ファイルサーバー（ポート8080）
sam local start-api           # SAM Local APIサーバー（ポート3000）
```

### 3. テスト実行
```bash
# GET リクエストのテスト
hads-admin.py get

# 特定のパスとメソッドのテスト
hads-admin.py get -p /api/users -m POST

# カスタムイベントファイルを使用したテスト
hads-admin.py get -e custom-event.json
```

### 4. AWSへのデプロイ
```bash
# SAM CLIを使用したデプロイ
sam build
sam deploy

# 静的ファイルのS3同期（AWS CLI）
aws s3 sync static/ s3://your-bucket/static/
```

詳細な使用方法については[ドキュメント](./doc/README.md)をご参照ください。

## 📁 サンプルプロジェクト

HADSを使用したサンプルプロジェクト：

### 最新版（推奨）
- **[HadsSampleProject2](../HadsSampleProject2/)** - 認証機能、フォーム処理、モック機能を含む最新のサンプル
  - AWS Cognito認証統合
  - WTFormsによるフォームバリデーション
  - motoによるAWSサービスモック
  - アカウント管理（サインアップ、ログイン、メール確認）

### その他のプロジェクト例
- **[HadsSampleProject](../HadsSampleProject/)** - 基本的なサンプル（旧版）
- **[ShogiProject](https://github.com/h-akira/ShogiProject)** - 将棋棋譜管理システム（実用例）

## 🛠️ CLI ツール詳細

### hads-admin.py コマンド

HADSの管理ツールは、シンプルで直感的なコマンドラインインターフェースを提供します。設定ファイルに依存せず、すべてコマンドラインオプションで制御できます。

#### init - プロジェクト初期化
```bash
hads-admin.py init -n <プロジェクト名> [-t <テンプレート>]

# オプション:
# -n, --name      : プロジェクト名（必須）
# -t, --template  : テンプレート（SSR001, API001）
```

#### proxy - プロキシサーバー起動
```bash
hads-admin.py proxy [オプション]

# オプション:
# -p, --proxy-port  : プロキシサーバーポート（デフォルト: 8000）
# -s, --sam-port    : SAM Localポート（デフォルト: 3000）
# --static-port     : 静的ファイルサーバーポート（デフォルト: 8080）
# --static-url      : 静的ファイルURL プレフィックス（デフォルト: /static）
# -d, --static-dir  : 静的ファイルディレクトリ（デフォルト: static）
```

#### static - 静的ファイルサーバー起動
```bash
hads-admin.py static [オプション]

# オプション:
# -p, --port        : サーバーポート（デフォルト: 8080）
# --static-url      : URL プレフィックス（デフォルト: /static）
# -d, --static-dir  : ファイルディレクトリ（デフォルト: static）
```

#### get - Lambda関数テスト
```bash
hads-admin.py get [オプション]

# オプション:
# -p, --path         : テストするパス（デフォルト: /）
# -m, --method       : HTTPメソッド（デフォルト: GET）
# -e, --event-file   : カスタムイベントJSONファイル
# -t, --template     : SAMテンプレートファイル（デフォルト: template.yaml）
# -f, --function-name: Lambda関数名（デフォルト: MainFunction）
```

## 🔧 開発スケジュール

今後追加予定の機能：
- **テンプレート生成機能**: SAMテンプレートやその他設定ファイルの自動生成
- **エラーハンドリング強化**: より詳細なエラー情報の提供
- **ドキュメント改善**: より詳細な使用例とベストプラクティス
- **認証プロバイダー追加**: Cognito以外の認証システムへの対応
- **デプロイ支援機能**: 自動ビルド・デプロイ機能の統合
