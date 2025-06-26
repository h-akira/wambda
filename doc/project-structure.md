# プロジェクト構造

このページでは、HADSプロジェクトの詳細な構造と各ファイルの役割について説明します。

## 📁 基本的なプロジェクト構造

HADSプロジェクトは以下のような構造になっています：

```
my-hads-project/
├── admin.json              # HADS管理設定ファイル
├── samconfig.toml          # SAM CLI設定ファイル
├── template.yaml           # CloudFormationテンプレート
├── static/                 # 静的ファイル
│   ├── css/
│   ├── js/
│   └── images/
└── Lambda/                 # Lambda関数のソースコード
    ├── lambda_function.py  # メインハンドラー
    ├── project/            # アプリケーションコード
    │   ├── __init__.py
    │   ├── settings.py     # 設定ファイル
    │   ├── urls.py         # URLルーティング
    │   └── views.py        # ビュー関数
    └── templates/          # テンプレートファイル
        ├── base.html
        └── index.html
```

## 📄 設定ファイル

### admin.json

HADSプロジェクトの管理設定ファイルです。

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

| フィールド | 説明 |
|------------|------|
| `region` | AWSリージョン |
| `profile` | AWS認証プロファイル |
| `static.local` | ローカル静的ファイルディレクトリ |
| `static.s3` | S3静的ファイルパス |
| `local_server.port.*` | ローカル開発時のポート設定 |

### samconfig.toml

AWS SAM CLIの設定ファイルです。

```toml
version = 0.1

[default.global.parameters]
stack_name = "my-hads-stack"

[default.build.parameters]
cached = true
parallel = true

[default.deploy.parameters]
capabilities = "CAPABILITY_NAMED_IAM"
confirm_changeset = true
resolve_s3 = true
region = "ap-northeast-1"
```

### template.yaml

CloudFormationテンプレートです。HADSはAWS SAMを使用してインフラを定義します。

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: HADS Serverless Web Application

Globals:
  Function:
    Timeout: 30
    Tracing: Active
    MemorySize: 256

Resources:
  MainAPIGateway:
    Type: AWS::Serverless::Api
    Properties:
      Name: 'my-api-gateway'
      StageName: 'stage-01'
      
  MainFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: 'my-lambda-function'
      CodeUri: Lambda/
      Handler: lambda_function.lambda_handler
      Runtime: python3.12
      Role: !GetAtt LambdaExecutionRole.Arn
      Events:
        ApiRoot:
          Type: Api
          Properties:
            Path: '/'
            Method: ANY
            RestApiId: !Ref MainAPIGateway
        ApiProxy:
          Type: Api
          Properties:
            Path: '/{proxy+}'
            Method: ANY
            RestApiId: !Ref MainAPIGateway
```

## 🐍 Lambdaコード構造

### lambda_function.py

Lambda関数のメインエントリーポイントです。

```python
import sys
import os
from hads.handler import Master

def lambda_handler(event, context):
    """
    AWS Lambda ハンドラー関数
    
    Args:
        event: AWS Lambda イベントオブジェクト
        context: AWS Lambda コンテキストオブジェクト
        
    Returns:
        HTTPレスポンス辞書
    """
    # プロジェクトディレクトリをPythonパスに追加
    sys.path.append(os.path.dirname(__file__))
    
    # HADSマスターオブジェクトを初期化
    master = Master(event, context)
    master.logger.info(f"リクエストパス: {master.request.path}")
    
    # 認証処理（必要に応じてコメントアウト）
    # master.settings.COGNITO.set_auth_by_code(master)
    # master.settings.COGNITO.set_auth_by_cookie(master)
    
    try:
        # URLルーティングでビュー関数を取得
        view, kwargs = master.router.path2view(master.request.path)
        
        # ビュー関数を実行
        response = view(master, **kwargs)
        
        # 認証クッキーの設定（必要に応じて）
        # master.settings.COGNITO.add_set_cookie_to_header(master, response)
        
        master.logger.info(f"レスポンス: {response}")
        return response
        
    except Exception as e:
        # エラーハンドリング
        if master.request.path == "/favicon.ico":
            master.logger.warning("favicon.ico が見つかりません")
        else:
            master.logger.exception(e)
            
        # エラーページを表示
        from hads.shortcuts import error_render
        import traceback
        return error_render(master, traceback.format_exc())
```

### project/settings.py

HADSアプリケーションの設定ファイルです。

```python
import os
import boto3

# パスマッピング設定
MAPPING_PATH = ""  # API Gatewayをそのまま使う場合はステージ名、独自ドメインを使う場合は空文字列
MAPPING_PATH_LOCAL = ""  # ローカル開発時の設定
DEBUG = True

# ディレクトリパス
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_URL = "/static"  # 先頭の/はあってもなくても同じ扱い
TIMEZONE = "Asia/Tokyo"

# AWS Systems Manager Parameter Store設定
if os.path.exists(os.path.join(BASE_DIR, "../admin.json")):
    import json
    with open(os.path.join(BASE_DIR, "../admin.json")) as f:
        admin = json.load(f)
    kwargs = {}
    try:
        kwargs["region_name"] = admin["region"]
    except KeyError:
        pass
    try:
        kwargs["profile_name"] = admin["profile"]
    except KeyError:
        pass
    session = boto3.Session(**kwargs)
    ssm = session.client('ssm')
else:
    ssm = boto3.client('ssm')

# Cognito認証設定
from hads.authenticate import Cognito, ManagedAuthPage

COGNITO = Cognito(
    domain=ssm.get_parameter(Name="/YourProject/Cognito/domain")["Parameter"]["Value"],
    user_pool_id=ssm.get_parameter(Name="/YourProject/Cognito/user_pool_id")["Parameter"]["Value"],
    client_id=ssm.get_parameter(Name="/YourProject/Cognito/client_id")["Parameter"]["Value"],
    client_secret=ssm.get_parameter(Name="/YourProject/Cognito/client_secret")["Parameter"]["Value"],
    region="ap-northeast-1"
)

AUTH_PAGE = ManagedAuthPage(
    scope="aws.cognito.signin.user.admin email openid phone",
    login_redirect_uri=ssm.get_parameter(Name="/YourProject/URL/home")["Parameter"]["Value"],
    local_login_redirect_uri="http://localhost:3000"
)
```

### project/urls.py

URLルーティング設定ファイルです。

```python
from hads.urls import Path, Router
from .views import index, detail, api_data

# アプリケーション名（オプション）
app_name = "main"

# URLパターン定義
urlpatterns = [
    # 基本的なパス
    Path("", index, name="index"),
    Path("about", about, name="about"),
    
    # パラメータ付きパス
    Path("item/{item_id}", detail, name="detail"),
    Path("user/{user_id}/profile", user_profile, name="user_profile"),
    
    # ネストされたルーター
    Router("api", "api.urls", name="api"),
    Router("admin", "admin.urls", name="admin"),
]
```

### project/views.py

ビュー関数を定義するファイルです。

```python
from hads.shortcuts import render, redirect, json_response, login_required

def index(master):
    """トップページ"""
    context = {
        "title": "ホーム",
        "message": "HADSへようこそ!"
    }
    return render(master, "index.html", context)

def detail(master, item_id):
    """詳細ページ"""
    # パスパラメータを使用
    context = {
        "item_id": item_id,
        "title": f"アイテム {item_id} の詳細"
    }
    return render(master, "detail.html", context)

@login_required
def profile(master):
    """プロフィールページ（認証必須）"""
    context = {
        "username": master.request.username,
        "title": "プロフィール"
    }
    return render(master, "profile.html", context)

def api_endpoint(master):
    """API エンドポイント"""
    data = {
        "status": "success",
        "message": "HADSのAPIレスポンス",
        "method": master.request.method
    }
    return json_response(master, data)

def form_handler(master):
    """フォーム処理"""
    if master.request.method == "POST":
        # POSTデータの処理
        name = master.request.body.get("name", "")
        email = master.request.body.get("email", "")
        
        # 処理後にリダイレクト
        return redirect(master, "index")
    
    # GETの場合はフォーム表示
    return render(master, "form.html")
```

## 🎨 テンプレート構造

### templates/base.html

基本テンプレートです。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ title | default('HADS App') }}{% endblock %}</title>
    
    <!-- 静的ファイルの読み込み -->
    <link rel="stylesheet" href="{{ static(master, 'css/bootstrap.min.css') }}">
    <link rel="stylesheet" href="{{ static(master, 'css/app.css') }}">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- ナビゲーション -->
    <nav class="navbar">
        <div class="container">
            <a href="{{ reverse(master, 'index') }}" class="navbar-brand">HADS App</a>
            
            {% if master.request.auth %}
                <div class="navbar-nav">
                    <span>ようこそ、{{ master.request.username }}さん</span>
                    <a href="{{ reverse(master, 'logout') }}">ログアウト</a>
                </div>
            {% else %}
                <div class="navbar-nav">
                    <a href="{{ get_login_url(master) }}">ログイン</a>
                    <a href="{{ get_signup_url(master) }}">サインアップ</a>
                </div>
            {% endif %}
        </div>
    </nav>
    
    <!-- メインコンテンツ -->
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    
    <!-- フッター -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 HADS Application. All rights reserved.</p>
        </div>
    </footer>
    
    <!-- JavaScript -->
    <script src="{{ static(master, 'js/app.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### templates/index.html

具体的なページテンプレートです。

```html
{% extends "base.html" %}

{% block title %}{{ title }} - HADS App{% endblock %}

{% block content %}
<div class="hero">
    <h1>{{ title }}</h1>
    <p class="lead">{{ message }}</p>
</div>

<div class="features">
    <div class="row">
        <div class="col-md-4">
            <h3>🚀 高速</h3>
            <p>サーバレスアーキテクチャによる高速レスポンス</p>
        </div>
        <div class="col-md-4">
            <h3>💰 経済的</h3>
            <p>使用した分だけの従量課金</p>
        </div>
        <div class="col-md-4">
            <h3>🔧 簡単</h3>
            <p>Djangoライクな開発体験</p>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
console.log("HADSアプリケーションが読み込まれました");
</script>
{% endblock %}
```

## 📂 静的ファイル構造

```
static/
├── css/
│   ├── bootstrap.min.css
│   ├── app.css
│   └── admin.css
├── js/
│   ├── app.js
│   ├── form-validation.js
│   └── lib/
│       └── jquery.min.js
├── images/
│   ├── logo.png
│   ├── favicon.ico
│   └── icons/
└── fonts/
    └── custom-font.woff2
```

## 🔧 高度な構造

### アプリケーションの分割

大きなプロジェクトでは、機能ごとにアプリケーションを分割できます：

```
Lambda/
├── lambda_function.py
├── project/
│   ├── settings.py
│   └── urls.py
├── blog/                    # ブログアプリ
│   ├── __init__.py
│   ├── urls.py
│   └── views.py
├── shop/                    # ショップアプリ
│   ├── __init__.py
│   ├── urls.py
│   └── views.py
└── common/                  # 共通ユーティリティ
    ├── __init__.py
    ├── decorators.py
    └── helpers.py
```

### テンプレート階層化

```
templates/
├── base.html
├── components/              # 再利用可能コンポーネント
│   ├── navbar.html
│   ├── footer.html
│   └── pagination.html
├── blog/                    # ブログ関連テンプレート
│   ├── index.html
│   ├── detail.html
│   └── form.html
└── shop/                    # ショップ関連テンプレート
    ├── product_list.html
    └── cart.html
```

## 📋 ベストプラクティス

### 1. ファイル命名規則

- **Python**: スネークケース（`my_module.py`）
- **テンプレート**: ハイフン区切り（`product-detail.html`）
- **静的ファイル**: ハイフン区切り（`app-styles.css`）

### 2. ディレクトリ構成

- 機能ごとにアプリケーションを分割
- 共通機能は `common` や `utils` ディレクトリに配置
- テンプレートはアプリケーションごとにディレクトリを作成

### 3. 設定管理

- 環境ごとに異なる設定は環境変数を使用
- 秘密情報はAWS Systems Manager Parameter Storeを活用
- 開発用と本番用の設定を分離

## 次のステップ

プロジェクト構造を理解したら、以下のページで詳細な機能を学習してください：

- [URLルーティング](./url-routing.md) - 詳細なルーティング設定
- [ビューとハンドラー](./views-handlers.md) - ビュー関数の詳細
- [テンプレートシステム](./templates.md) - Jinja2テンプレートの活用

---

[← 前: クイックスタート](./quickstart.md) | [ドキュメント目次に戻る](./README.md) | [次: URLルーティング →](./url-routing.md)
