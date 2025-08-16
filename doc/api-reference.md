# API リファレンス

HADSフレームワークのAPIリファレンスです。主要なクラス、関数、メソッドの詳細な使用方法を説明します。

## 📚 モジュール構成

```python
hads/
├── handler.py          # Master, Request クラス
├── urls.py            # Path, Router クラス
├── shortcuts.py       # ヘルパー関数群
├── authenticate.py    # Cognito, ManagedAuthPage クラス
├── local_server.py    # ローカルサーバー関数
└── init_option.py     # プロジェクト初期化
```

## 🏗️ Core Classes

### Master クラス

Lambda関数のメインハンドラークラス。

```python
class Master:
    def __init__(self, event, context)
```

#### 属性

| 属性 | 型 | 説明 |
|------|----|----- |
| `event` | dict | AWS Lambdaイベントオブジェクト |
| `context` | object | AWS Lambdaコンテキストオブジェクト |
| `settings` | module | プロジェクト設定モジュール |
| `router` | Router | URLルーターインスタンス |
| `request` | Request | リクエストオブジェクト |
| `logger` | Logger | ログ出力用ロガー |
| `local` | bool | ローカル環境かどうか |

#### 使用例

```python
from hads.handler import Master

def lambda_handler(event, context):
    master = Master(event, context)
    master.logger.info(f"リクエスト: {master.request.path}")
    
    # ビュー関数の実行
    view, kwargs = master.router.path2view(master.request.path)
    return view(master, **kwargs)
```

### Request クラス

HTTPリクエスト情報を管理するクラス。

```python
class Request:
    def __init__(self, event, context)
```

#### 属性

| 属性 | 型 | 説明 |
|------|----|----- |
| `method` | str | HTTPメソッド (GET, POST, etc.) |
| `path` | str | リクエストパス |
| `body` | dict | POSTデータ（解析済み） |
| `auth` | bool | 認証状態 |
| `username` | str | 認証済みユーザー名 |
| `access_token` | str | Cognitoアクセストークン |
| `id_token` | str | CognitoIDトークン |
| `refresh_token` | str | Cognitoリフレッシュトークン |
| `decode_token` | dict | デコード済みIDトークン |
| `set_cookie` | bool | クッキー設定フラグ |
| `clean_cookie` | bool | クッキー削除フラグ |

#### メソッド

##### set_token(access_token, id_token, refresh_token)

認証トークンを設定します。

```python
request.set_token(
    access_token="eyJ...",
    id_token="eyJ...", 
    refresh_token="eyJ..."
)
```

## 🛣️ Routing Classes

### Path クラス

単一のURLパターンを定義するクラス。

```python
class Path:
    def __init__(self, path_pattern: str, view, name=None)
```

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `path_pattern` | str | URLパターン（例: "user/{user_id}"） |
| `view` | function | ビュー関数 |
| `name` | str | パスの名前（リバースルックアップ用） |

#### 使用例

```python
from hads.urls import Path
from .views import user_detail

# 基本的なパス
Path("about", about_view, name="about")

# パラメータ付きパス
Path("user/{user_id}", user_detail, name="user_detail")

# 複数パラメータ
Path("blog/{year}/{month}/{slug}", post_detail, name="post_detail")
```

### Router クラス

URLパターンをグループ化し、ネストした構造を作るクラス。

```python
class Router:
    def __init__(self, root="", urls_str="project.urls", name=None)
```

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `root` | str | ルートパス |
| `urls_str` | str | URLモジュールのインポートパス |
| `name` | str | ルーターの名前 |

#### メソッド

##### name2path(name, kwargs={}, root="")

名前からURLパスを生成します。

```python
# 基本的な使用
url = router.name2path("index")

# パラメータ付き
url = router.name2path("user_detail", {"user_id": "123"})

# 名前空間付き
url = router.name2path("blog:post_detail", {"slug": "my-post"})
```

**戻り値**: `str` - 生成されたURLパス

**例外**: 
- `NotMatched` - 名前に一致するパスが見つからない
- `KwargsRemain` - 未使用のキーワード引数がある

##### path2view(abs_path=None, segments=None, kwargs={})

パスからビュー関数を取得します。

```python
# 絶対パスから
view, kwargs = router.path2view("/user/123")

# セグメントから
view, kwargs = router.path2view(segments=["user", "123"])
```

**戻り値**: `tuple[function, dict]` - (ビュー関数, パラメータ辞書)

**例外**: `NotMatched` - パスに一致するビューが見つからない

#### 使用例

```python
from hads.urls import Router

# ネストされたルーター
Router("api", "api.urls", name="api")
Router("admin", "admin.urls", name="admin")
```

## 🔧 Shortcut Functions

### render(master, template_file, context={}, content_type="text/html; charset=UTF-8", code=200)

HTMLテンプレートをレンダリングしてHTTPレスポンスを生成します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `master` | Master | Masterオブジェクト |
| `template_file` | str | テンプレートファイル名 |
| `context` | dict | テンプレート変数 |
| `content_type` | str | Content-Typeヘッダー |
| `code` | int | HTTPステータスコード |

#### 戻り値

HTTPレスポンス辞書

```python
{
    "statusCode": 200,
    "headers": {"Content-Type": "text/html; charset=UTF-8"},
    "body": "レンダリングされたHTML"
}
```

#### 使用例

```python
from hads.shortcuts import render

def my_view(master):
    context = {
        "title": "ページタイトル",
        "items": ["項目1", "項目2", "項目3"]
    }
    return render(master, "template.html", context)
```

### json_response(master, body, code=200)

JSON形式のHTTPレスポンスを生成します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `master` | Master | Masterオブジェクト |
| `body` | dict/list | JSONシリアライズ可能なオブジェクト |
| `code` | int | HTTPステータスコード |

#### 使用例

```python
from hads.shortcuts import json_response

def api_view(master):
    data = {
        "status": "success",
        "data": [{"id": 1, "name": "項目1"}],
        "count": 1
    }
    return json_response(master, data)
```

### redirect(master, url_name, query_params=None, **kwargs)

指定したURLにリダイレクトします。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `master` | Master | Masterオブジェクト |
| `url_name` | str | リダイレクト先のURL名 |
| `query_params` | dict | クエリパラメータの辞書（オプション） |
| `**kwargs` | dict | URLパラメータ |

#### 戻り値

HTTPリダイレクトレスポンス（statusCode: 302）

#### 使用例

```python
from hads.shortcuts import redirect

def login_view(master):
    # 基本的なリダイレクト
    return redirect(master, "profile")

def user_redirect(master):
    # URLパラメータ付きリダイレクト
    return redirect(master, "user_detail", user_id="123")

def signup_success(master):
    # クエリパラメータ付きリダイレクト
    return redirect(master, "accounts:verify", query_params={
        'username': 'john_doe',
        'message': 'signup_success'
    })

def complex_redirect(master):
    # URLパラメータとクエリパラメータの両方
    return redirect(master, "user:posts", 
                   user_id="123",
                   query_params={'filter': 'published', 'sort': 'date'})
    # 生成されるURL: /user/123/posts?filter=published&sort=date
```

### reverse(master, app_name, **kwargs)

URL名からURLパスを生成します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `master` | Master | Masterオブジェクト |
| `app_name` | str | URL名 |
| `**kwargs` | dict | URLパラメータ |

#### 戻り値

`str` - 生成されたURLパス

#### 使用例

```python
from hads.shortcuts import reverse

def my_view(master):
    # ユーザー詳細ページのURL生成
    user_url = reverse(master, "user_detail", user_id="123")
    
    context = {"user_url": user_url}
    return render(master, "template.html", context)
```

### static(master, file_path)

静的ファイルのURLを生成します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `master` | Master | Masterオブジェクト |
| `file_path` | str | 静的ファイルのパス |

#### 戻り値

`str` - 静的ファイルのURL

#### 使用例

```python
from hads.shortcuts import static

def my_view(master):
    # CSS ファイルのURL
    css_url = static(master, "css/app.css")
    
    # 画像ファイルのURL
    image_url = static(master, "images/logo.png")
```

### login_required(func)

ログインが必要なビューのデコレータ。

#### 使用例

```python
from hads.shortcuts import login_required

@login_required
def protected_view(master):
    return render(master, "protected.html")
```

### gen_response(master, body, content_type="text/html; charset=UTF-8", code=200, isBase64Encoded=None)

カスタムHTTPレスポンスを生成します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `master` | Master | Masterオブジェクト |
| `body` | str | レスポンスボディ |
| `content_type` | str | Content-Typeヘッダー |
| `code` | int | HTTPステータスコード |
| `isBase64Encoded` | bool | Base64エンコードフラグ |

#### 使用例

```python
from hads.shortcuts import gen_response

def csv_download(master):
    csv_data = "name,email\nJohn,john@example.com"
    return gen_response(
        master,
        csv_data,
        content_type="text/csv",
        code=200
    )
```

## 🔐 Authentication Classes

### Cognito クラス

Amazon Cognitoとの認証連携を行うクラス。

```python
class Cognito:
    def __init__(self, domain, user_pool_id, client_id, client_secret, region)
```

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `domain` | str | Cognitoドメイン |
| `user_pool_id` | str | User Pool ID |
| `client_id` | str | App Client ID |
| `client_secret` | str | App Client Secret |
| `region` | str | AWSリージョン |

#### メソッド

##### set_auth_by_code(master)

認証コードからトークンを取得し、認証状態を設定します。

```python
cognito.set_auth_by_code(master)
```

##### set_auth_by_cookie(master)

クッキーからトークンを検証し、認証状態を設定します。

```python
cognito.set_auth_by_cookie(master)
```

##### add_set_cookie_to_header(master, response)

レスポンスヘッダーに認証クッキーを追加します。

```python
response = view(master)
cognito.add_set_cookie_to_header(master, response)
```

#### 使用例

```python
from hads.authenticate import Cognito

# 設定
cognito = Cognito(
    domain="https://your-domain.auth.region.amazoncognito.com",
    user_pool_id="region_XXXXXXXXX",
    client_id="your-client-id",
    client_secret="your-client-secret",
    region="ap-northeast-1"
)

# lambda_function.py での使用
def lambda_handler(event, context):
    master = Master(event, context)
    
    # 認証処理
    master.settings.COGNITO.set_auth_by_code(master)
    master.settings.COGNITO.set_auth_by_cookie(master)
    
    # ビュー実行
    view, kwargs = master.router.path2view(master.request.path)
    response = view(master, **kwargs)
    
    # クッキー設定
    master.settings.COGNITO.add_set_cookie_to_header(master, response)
    
    return response
```

### ManagedAuthPage クラス

認証ページのURL管理を行うクラス。

```python
class ManagedAuthPage:
    def __init__(self, scope, login_redirect_uri, local_login_redirect_uri)
```

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `scope` | str | OAuth2スコープ |
| `login_redirect_uri` | str | 本番環境のリダイレクトURI |
| `local_login_redirect_uri` | str | ローカル環境のリダイレクトURI |

#### メソッド

##### get_login_url(master)

ログインページのURLを取得します。

```python
login_url = auth_page.get_login_url(master)
```

##### get_signup_url(master)

サインアップページのURLを取得します。

```python
signup_url = auth_page.get_signup_url(master)
```

##### get_logout_url(master)

ログアウトページのURLを取得します。

```python
logout_url = auth_page.get_logout_url(master)
```

## 🖥️ Local Server Functions

### run_static_server(static_url, static_dir, port=8080)

静的ファイル配信サーバーを起動します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `static_url` | str | 静的ファイルのURLパス |
| `static_dir` | str | 静的ファイルのディレクトリ |
| `port` | int | サーバーポート番号 |

### run_proxy_server(static_url, port=8000, sam_port=3000, static_port=8080)

プロキシサーバーを起動します。

#### パラメータ

| パラメータ | 型 | 説明 |
|-----------|----|----- |
| `static_url` | str | 静的ファイルのURLパス |
| `port` | int | プロキシサーバーのポート |
| `sam_port` | int | SAM Localのポート |
| `static_port` | int | 静的ファイルサーバーのポート |

## 🔧 Template Functions

テンプレート内で使用可能な関数群。

### reverse(master, name, **kwargs)

テンプレート内でURL逆引きを行います。

```html
<a href="{{ reverse(master, 'user_detail', user_id=user.id) }}">
    ユーザー詳細
</a>
```

### static(master, file_path)

テンプレート内で静的ファイルURLを生成します。

```html
<link href="{{ static(master, 'css/app.css') }}" rel="stylesheet">
<img src="{{ static(master, 'images/logo.png') }}" alt="ロゴ">
```

### get_login_url(master)

テンプレート内でログインURLを取得します。

```html
<a href="{{ get_login_url(master) }}">ログイン</a>
```

### get_signup_url(master)

テンプレート内でサインアップURLを取得します。

```html
<a href="{{ get_signup_url(master) }}">サインアップ</a>
```

## ⚠️ Exceptions

### NotMatched

URLパターンが一致しなかった場合に発生する例外。

```python
from hads.urls import NotMatched

try:
    view, kwargs = router.path2view("/nonexistent")
except NotMatched:
    # 404ページを表示
    return render(master, "404.html", code=404)
```

### KwargsRemain

URL生成時に未使用のキーワード引数がある場合に発生する例外。

```python
from hads.urls import KwargsRemain

try:
    url = router.name2path("user_detail", {
        "user_id": "123",
        "extra_param": "value"  # 使用されないパラメータ
    })
except KwargsRemain as e:
    print(f"未使用パラメータ: {e}")
```

## 📋 型ヒント

HADSでの型ヒント使用例：

```python
from typing import Dict, Any, Optional, Tuple, Callable
from hads.handler import Master

# ビュー関数の型定義
ViewFunction = Callable[[Master], Dict[str, Any]]

def my_view(master: Master) -> Dict[str, Any]:
    context: Dict[str, Any] = {"title": "ページ"}
    return render(master, "template.html", context)

# URLパターンの型定義
def create_urlpatterns() -> List[Union[Path, Router]]:
    return [
        Path("", my_view, name="index"),
        Router("api", "api.urls", name="api")
    ]
```

## 🧪 テスト用ユーティリティ

### テスト用のMasterオブジェクト作成

```python
def create_test_master(path="/", method="GET", body=None):
    """テスト用のMasterオブジェクトを作成"""
    event = {
        "path": path,
        "requestContext": {"httpMethod": method},
        "body": body
    }
    return Master(event, None)

# 使用例
def test_view():
    master = create_test_master("/user/123")
    response = user_detail(master, user_id="123")
    assert response["statusCode"] == 200
```

### モック認証

```python
def set_mock_auth(master, username="testuser"):
    """テスト用の認証状態を設定"""
    master.request.auth = True
    master.request.username = username
    master.request.decode_token = {
        "cognito:username": username,
        "email": f"{username}@example.com"
    }
```

## 🔍 デバッグユーティリティ

### ログ出力の設定

```python
import logging

# ログレベルの設定
logging.basicConfig(level=logging.DEBUG)

def debug_view(master):
    master.logger.debug(f"リクエスト詳細: {master.event}")
    master.logger.info(f"認証状態: {master.request.auth}")
    return render(master, "debug.html")
```

### リクエスト情報の表示

```python
def debug_request(master):
    """リクエスト情報をJSON形式で返すデバッグビュー"""
    debug_info = {
        "path": master.request.path,
        "method": master.request.method,
        "body": master.request.body,
        "auth": master.request.auth,
        "local": master.local
    }
    return json_response(master, debug_info)
```

---

[← ドキュメント目次に戻る](./README.md)
