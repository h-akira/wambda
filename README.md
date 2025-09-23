# WAMBDA
WAMBDA（ワムダ）は、AWS Lambdaで動作するサーバーレスWebアプリケーション開発フレームワークです。Django風のアーキテクチャを採用し、単一のLambda関数ですべてのリクエストを処理する「Lambdalithアプローチ」を採用しています。

## 特徴

### 🎯 設計思想
- **SAM活用**: AWS Serverless Application Modelによるインフラ管理
- **単一Lambda**: 一つのLambda関数ですべてのリクエストを処理（Lambdalithアプローチ）
- **S3静的ファイル配信**: 効率的な静的ファイル配信
- **ローカル開発環境**: 本番環境と同等のローカル開発環境
- **Django風設計**: urls.py、views.py、テンプレートによるMVC構造

### 🚀 主要機能
- **AWS Cognito認証**: 完全なユーザー認証・アカウント管理システム
- **フォーム検証**: WTFormsによる統合フォーム処理
- **モック環境**: motoライブラリによるローカルAWSサービステスト
- **プロキシサーバー**: SAM Local + 静的ファイルサーバーの統合開発環境
- **クエリパラメータ**: URLクエリパラメータサポート
- **パスワード管理**: パスワード変更・リセット機能
- **アカウント削除**: 完全なアカウント削除機能

## アーキテクチャ

### システム構成
```
[CloudFront]
     ├── [API Gateway] → [Lambda Function] → [AWS Services]
     └── [S3 Static Files]
```

### Lambda内部構造
```
Event → Master → Router → View → Template → Response
         ↓
    Authentication
         ↓
    Request/Response
```

## クイックスタート

### 1. プロジェクト初期化
```bash
# 対話式テンプレート選択
python wambda-admin.py init

# または直接指定
python wambda-admin.py init -n my-project -t SSR001
```

**利用可能テンプレート:**
- **SSR001**: サーバーサイドレンダリングテンプレート（認証機能付き）
- **API001**: APIテンプレート（Vue、React、Angular等フロントエンド用） ※準備中

### 2. ローカル開発環境の起動
```bash
cd my-project

# プロキシサーバー起動（推奨: SAM Local + 静的ファイルサーバー統合）
python wambda-admin.py proxy

# 個別サーバー起動
python wambda-admin.py static    # 静的ファイルサーバー（ポート 8080）
sam local start-api              # SAM Local APIサーバー（ポート 3000）
```

### 3. テスト
```bash
# lambda_function.pyを直接実行してテスト
cd Lambda
python lambda_function.py
```

### 4. AWS デプロイ
```bash
# SAM CLIでデプロイ
sam build
sam deploy

# 静的ファイルをS3に同期
aws s3 sync static/ s3://your-bucket/static/
```

### 5. CloudWatch ログ確認
```bash
# 直近1時間のログ表示
python wambda-admin.py log -f your-function-name

# 特定期間のログ表示
python wambda-admin.py log -f your-function-name --hours 24 --limit 100
```

## CLI ツール詳細

### `wambda-admin.py` コマンド

#### `init` - プロジェクト初期化
```bash
python wambda-admin.py init [-n <name>] [-t <template>]

# オプション:
# -n, --name      : プロジェクト名（対話式入力可能）
# -t, --template  : テンプレート（SSR001、API001）
```

#### `proxy` - プロキシサーバー起動
```bash
python wambda-admin.py proxy [options]

# オプション:
# -p, --proxy-port  : プロキシサーバーポート（デフォルト: 8000）
# -s, --sam-port    : SAM Localポート（デフォルト: 3000）
# --static-port     : 静的ファイルサーバーポート（デフォルト: 8080）
# --static-url      : 静的ファイルURLプレフィックス（デフォルト: /static）
# -d, --static-dir  : 静的ファイルディレクトリ（デフォルト: static）
```

#### `static` - 静的ファイルサーバー起動
```bash
python wambda-admin.py static [options]

# オプション:
# -p, --port        : サーバーポート（デフォルト: 8080）
# --static-url      : URLプレフィックス（デフォルト: /static）
# -d, --static-dir  : ファイルディレクトリ（デフォルト: static）
```

#### `log` - CloudWatch ログ取得
```bash
python wambda-admin.py log -f <function-name> [options]

# オプション:
# -f, --function-name : Lambda関数名（必須）
# -l, --limit         : 最大ログイベント数（デフォルト: 50）
# --hours             : 遡る時間数（デフォルト: 1）
# -r, --region        : AWSリージョン（デフォルト: ap-northeast-1）
# -p, --profile       : AWSプロファイル名
# --start-time        : 開始時刻（ISO形式）
# --end-time          : 終了時刻（ISO形式）
```

## フレームワーク詳細

### 認証システム
WAMBDAはAWS Cognitoとの完全統合を提供します：

- **ユーザー登録**: メール認証付きサインアップ
- **ログイン/ログアウト**: JWTトークンベース認証
- **パスワード管理**: 変更・リセット機能
- **アカウント削除**: 完全なアカウント削除
- **セッション管理**: 自動トークンリフレッシュ

### コア機能

#### Master クラス (`wambda/lib/wambda/handler.py`)
- リクエスト処理の中心クラス
- 設定読み込み、ルーター初期化、認証処理
- ローカル/本番環境の自動判定

#### Request クラス (`wambda/lib/wambda/handler.py`)
- HTTPリクエスト表現
- クエリパラメータ、フォームデータ、認証情報を保持
- MultiDict によるWTForms互換フォームデータ処理

#### 認証機能 (`wambda/lib/wambda/authenticate.py`)
- Cognito統合ログイン/サインアップ
- JWTトークン検証・リフレッシュ
- NO_AUTHモード（開発用）
- メンテナンスモード対応

#### ショートカット関数 (`wambda/lib/wambda/shortcuts.py`)
- `render()`: Jinja2テンプレートレンダリング
- `redirect()`: クエリパラメータ付きリダイレクト
- `reverse()`: URL名からパス生成
- `login_required`: ログイン必須デコレータ

### プロジェクト構造
```
my-project/
├── Lambda/
│   ├── lambda_function.py          # エントリーポイント
│   ├── project/
│   │   ├── settings.py            # 設定ファイル
│   │   ├── urls.py               # URLルーティング
│   │   └── views.py              # カスタムビュー（404等）
│   ├── accounts/                   # 認証機能
│   │   ├── views.py              # 認証ビュー
│   │   ├── forms.py              # 認証フォーム
│   │   └── urls.py               # 認証URL
│   ├── mock/                      # モック設定
│   │   ├── ssm.py               # SSMパラメータモック
│   │   └── dynamodb.py          # DynamoDBモック
│   └── templates/                # Jinja2テンプレート
├── static/                        # 静的ファイル
├── template.yaml                  # SAM設定
└── samconfig.toml                # SAM デプロイ設定
```

### 設定システム (`project/settings.py`)
```python
# 基本設定
BASE_DIR = "/path/to/lambda"
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_URL = "/static"
MAPPING_PATH = ""  # API Gateway ステージ

# 認証設定
COGNITO_SSM_PARAMS = {
    'USER_POOL_ID': '/Cognito/user_pool_id',
    'CLIENT_ID': '/Cognito/client_id',
    'CLIENT_SECRET': '/Cognito/client_secret'
}

# URL設定
LOGIN_URL = "accounts:login"
SIGNUP_URL = "accounts:signup"
VERIFY_URL = "accounts:verify"
LOGOUT_URL = "accounts:logout"

# 開発・テスト設定
DEBUG = True
USE_MOCK = False
NO_AUTH = False
DENY_SIGNUP = False
DENY_LOGIN = False
```

### 最新機能

#### クエリパラメータサポート
```python
# リクエストからクエリパラメータ取得
username = master.request.query_params.get('username', '')
message = master.request.query_params.get('message', '')

# リダイレクト時にクエリパラメータ付与
return redirect(master, 'accounts:login', query_params={
    'message': 'verify_success'
})
```

#### フォーム処理（WTForms統合）
```python
from wtforms import Form, StringField, PasswordField, validators

class LoginForm(Form):
    username = StringField('ユーザー名', [validators.DataRequired()])
    password = PasswordField('パスワード', [validators.DataRequired()])

# ビューでの使用
def login_view(master):
    if master.request.method == 'POST':
        form = LoginForm(master.request.get_form_data())
        if form.validate():
            # ログイン処理
            pass
```

#### アカウント削除機能
```python
def delete_account_view(master):
    # パスワード認証確認
    # Cognitoからユーザー削除
    # セッション削除
    # ホームページへリダイレクト
```

## モック環境

開発時のAWSサービスモックをサポート：

```python
# settings.py
USE_MOCK = True

# mock/ssm.py - SSMパラメータモック
# mock/dynamodb.py - DynamoDBテーブルモック
```

## 依存関係

主要なPythonパッケージ：
- `boto3/botocore`: AWS SDK
- `Jinja2`: テンプレートエンジン
- `WTForms`: フォーム処理
- `PyJWT`: JWTトークン処理
- `moto`: AWSモック（開発用）

## ドキュメント

📚 **詳細なドキュメント**: [doc/README.md](./doc/README.md)

### 基本ガイド
- [インストールとセットアップ](./doc/installation.md)
- [プロジェクト構造](./doc/project-structure.md)
- [URLルーティング](./doc/url-routing.md)
- [ビューとハンドラー](./doc/views-handlers.md)

### 高度な機能
- [認証とCognito統合](./doc/authentication.md)
- [ローカル開発環境](./doc/local-development.md)
- [デプロイガイド](./doc/deployment.md)

## サンプルプロジェクト

- **[WambdaInitProject_SSR001](https://github.com/h-akira/WambdaInitProject_SSR001)**: 最新の完全な認証機能付きテンプレート

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告、機能リクエスト、プルリクエストを歓迎します。

---

**WAMBDA** - Modern Serverless Web Application Framework for AWS
