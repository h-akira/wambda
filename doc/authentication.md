# 認証とCognito連携

HADSはAmazon Cognitoとの深い連携を通じて、強力で安全な認証システムを提供します。このページでは、認証機能の実装方法を詳しく説明します。

## 🔐 認証システムの概要

### 構成要素

HADSの認証システムは以下で構成されています：

- **Amazon Cognito User Pool**: ユーザー管理とトークン発行
- **Cognito クラス**: HADS側の認証ハンドラー
- **ManagedAuthPage クラス**: 認証ページの管理
- **認証デコレータ**: ビューへのアクセス制御

### 認証フロー

```
1. ユーザーがログインページにアクセス
2. Cognitoの認証画面にリダイレクト
3. ユーザーが認証情報を入力
4. Cognitoが認証コードを発行
5. HADSがコードをトークンに交換
6. トークンをクッキーに保存
7. 以降のリクエストでトークンを検証
```

## ⚙️ Cognito設定

### User Poolの作成

```bash
# AWS CLIでUser Poolを作成
aws cognito-idp create-user-pool \
  --pool-name "hads-user-pool" \
  --policies PasswordPolicy='{
    "MinimumLength": 8,
    "RequireUppercase": true,
    "RequireLowercase": true,
    "RequireNumbers": true,
    "RequireSymbols": false
  }' \
  --auto-verified-attributes email \
  --username-attributes email \
  --region ap-northeast-1
```

### App Clientの作成

```bash
# User Pool IDを取得
USER_POOL_ID="ap-northeast-1_XXXXXXXXX"

# App Clientを作成
aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name "hads-app-client" \
  --generate-secret \
  --explicit-auth-flows ADMIN_NO_SRP_AUTH ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --supported-identity-providers COGNITO \
  --callback-urls "https://your-domain.com/auth/callback" "http://localhost:3000/auth/callback" \
  --logout-urls "https://your-domain.com/" "http://localhost:3000/" \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes email openid phone profile \
  --region ap-northeast-1
```

### ドメイン設定

```bash
# Cognitoドメインを設定
aws cognito-idp create-user-pool-domain \
  --user-pool-id $USER_POOL_ID \
  --domain "your-app-auth" \
  --region ap-northeast-1
```

## 🔧 HADS側の設定

### Systems Manager Parameter Store

認証情報はSSM Parameter Storeに保存することを推奨します：

```bash
# Cognitoドメイン
aws ssm put-parameter \
  --name "/your-app/cognito/domain" \
  --value "https://your-app-auth.auth.ap-northeast-1.amazoncognito.com" \
  --type "String"

# User Pool ID
aws ssm put-parameter \
  --name "/your-app/cognito/user_pool_id" \
  --value "ap-northeast-1_XXXXXXXXX" \
  --type "String"

# Client ID
aws ssm put-parameter \
  --name "/your-app/cognito/client_id" \
  --value "your-client-id" \
  --type "String"

# Client Secret
aws ssm put-parameter \
  --name "/your-app/cognito/client_secret" \
  --value "your-client-secret" \
  --type "SecureString"

# Redirect URI
aws ssm put-parameter \
  --name "/your-app/auth/redirect_uri" \
  --value "https://your-domain.com/auth/callback" \
  --type "String"
```

### settings.py の設定

```python
# Lambda/project/settings.py
import os
import boto3
from hads.authenticate import Cognito, ManagedAuthPage

# ... 他の設定 ...

# AWS Systems Manager Parameter Store設定
# 環境変数やAWS認証情報を使用
ssm = boto3.client('ssm')

# Cognitoクライアントの設定
COGNITO = Cognito(
    domain=ssm.get_parameter(Name="/your-app/cognito/domain")["Parameter"]["Value"],
    user_pool_id=ssm.get_parameter(Name="/your-app/cognito/user_pool_id")["Parameter"]["Value"],
    client_id=ssm.get_parameter(Name="/your-app/cognito/client_id")["Parameter"]["Value"],
    client_secret=ssm.get_parameter(Name="/your-app/cognito/client_secret")["Parameter"]["Value"],
    region="ap-northeast-1",
)

# 認証ページの設定
AUTH_PAGE = ManagedAuthPage(
    scope="aws.cognito.signin.user.admin email openid phone profile",
    login_redirect_uri=ssm.get_parameter(Name="/your-app/auth/redirect_uri")["Parameter"]["Value"],
    local_login_redirect_uri="http://localhost:3000/auth/callback"
)
```

## 🚪 認証フローの実装

### lambda_function.py での認証処理

```python
# Lambda/lambda_function.py
import sys
import os
from hads.handler import Master

def lambda_handler(event, context):
    sys.path.append(os.path.dirname(__file__))
    master = Master(event, context)
    master.logger.info(f"path: {master.request.path}")
    
    # 認証コードからトークンを取得
    master.settings.COGNITO.set_auth_by_code(master)
    
    # クッキーからトークンを検証
    master.settings.COGNITO.set_auth_by_cookie(master)
    
    try:
        view, kwargs = master.router.path2view(master.request.path)
        response = view(master, **kwargs)
        
        # 認証クッキーをレスポンスに追加
        master.settings.COGNITO.add_set_cookie_to_header(master, response)
        
        master.logger.info(f"response: {response}")
        return response
        
    except Exception as e:
        if master.request.path == "/favicon.ico":
            master.logger.warning("favicon.ico not found")
        else:
            master.logger.exception(e)
        from hads.shortcuts import error_render
        import traceback
        return error_render(master, traceback.format_exc())
```

### URLルーティングの設定

```python
# Lambda/project/urls.py
from hads.urls import Path
from .views import index, profile, auth_callback, logout

urlpatterns = [
    Path("", index, name="index"),
    Path("profile", profile, name="profile"),
    Path("auth/callback", auth_callback, name="auth_callback"),
    Path("logout", logout, name="logout"),
]
```

### 認証関連ビューの実装

```python
# Lambda/project/views.py
from hads.shortcuts import render, redirect, login_required

def index(master):
    """トップページ"""
    context = {
        "title": "ホーム",
        "is_authenticated": master.request.auth,
        "username": master.request.username if master.request.auth else None
    }
    return render(master, "index.html", context)

@login_required
def profile(master):
    """プロフィールページ（認証必須）"""
    # IDトークンから追加情報を取得
    user_info = {}
    if master.request.decode_token:
        user_info = {
            "username": master.request.decode_token.get("cognito:username", ""),
            "email": master.request.decode_token.get("email", ""),
            "given_name": master.request.decode_token.get("given_name", ""),
            "family_name": master.request.decode_token.get("family_name", ""),
            "phone_number": master.request.decode_token.get("phone_number", ""),
            "email_verified": master.request.decode_token.get("email_verified", False)
        }
    
    context = {
        "title": "プロフィール",
        "user_info": user_info
    }
    return render(master, "auth/profile.html", context)

def auth_callback(master):
    """認証コールバック"""
    # 認証処理はlambda_function.pyで実行済み
    if master.request.auth:
        master.logger.info(f"ユーザーログイン成功: {master.request.username}")
        return redirect(master, "profile")
    else:
        master.logger.warning("認証コールバックでログインに失敗")
        return redirect(master, "index")

def logout(master):
    """ログアウト"""
    master.request.clean_cookie = True
    master.logger.info(f"ユーザーログアウト: {master.request.username}")
    
    # Cognitoのログアウトページにリダイレクト
    logout_url = master.settings.AUTH_PAGE.get_logout_url(master)
    return {
        "statusCode": 302,
        "headers": {
            "Location": logout_url
        }
    }
```

## 🎨 認証テンプレート

### ベーステンプレートでの認証状態表示

```html
<!-- templates/base.html -->
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
        <a class="navbar-brand" href="{{ reverse(master, 'index') }}">HADSアプリ</a>
        
        <div class="navbar-nav ms-auto">
            {% if master.request.auth %}
                <!-- ログイン中 -->
                <div class="dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" 
                       data-bs-toggle="dropdown">
                        👤 {{ master.request.username }}
                    </a>
                    <ul class="dropdown-menu">
                        <li>
                            <a class="dropdown-item" href="{{ reverse(master, 'profile') }}">
                                👤 プロフィール
                            </a>
                        </li>
                        <li><hr class="dropdown-divider"></li>
                        <li>
                            <a class="dropdown-item" href="{{ reverse(master, 'logout') }}">
                                🚪 ログアウト
                            </a>
                        </li>
                    </ul>
                </div>
            {% else %}
                <!-- 未ログイン -->
                <a class="nav-link" href="{{ get_login_url(master) }}">
                    🔑 ログイン
                </a>
                <a class="nav-link" href="{{ get_signup_url(master) }}">
                    📝 サインアップ
                </a>
            {% endif %}
        </div>
    </div>
</nav>
```

### プロフィールページ

```html
<!-- templates/auth/profile.html -->
{% extends "base.html" %}

{% block title %}プロフィール - {{ super() }}{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h4>👤 ユーザープロフィール</h4>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-sm-4">
                        <strong>ユーザー名:</strong>
                    </div>
                    <div class="col-sm-8">
                        {{ user_info.username | default('未設定') }}
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-sm-4">
                        <strong>メールアドレス:</strong>
                    </div>
                    <div class="col-sm-8">
                        {{ user_info.email | default('未設定') }}
                        {% if user_info.email_verified %}
                            <span class="badge bg-success ms-2">✅ 認証済み</span>
                        {% else %}
                            <span class="badge bg-warning ms-2">⚠️ 未認証</span>
                        {% endif %}
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-sm-4">
                        <strong>名前:</strong>
                    </div>
                    <div class="col-sm-8">
                        {% if user_info.given_name or user_info.family_name %}
                            {{ user_info.family_name }} {{ user_info.given_name }}
                        {% else %}
                            未設定
                        {% endif %}
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-sm-4">
                        <strong>電話番号:</strong>
                    </div>
                    <div class="col-sm-8">
                        {{ user_info.phone_number | default('未設定') }}
                    </div>
                </div>
            </div>
            <div class="card-footer">
                <a href="{{ get_signup_url(master) }}" class="btn btn-primary">
                    ✏️ プロフィール編集
                </a>
                <a href="{{ reverse(master, 'logout') }}" class="btn btn-outline-secondary">
                    🚪 ログアウト
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 🔒 アクセス制御

### デコレータによる認証制御

```python
from hads.shortcuts import login_required

@login_required
def protected_view(master):
    """ログインが必要なページ"""
    context = {
        "title": "保護されたページ",
        "username": master.request.username
    }
    return render(master, "protected.html", context)
```

### カスタム認証デコレータ

```python
def admin_required(func):
    """管理者権限が必要なビューのデコレータ"""
    def wrapper(master, **kwargs):
        # ログインチェック
        if not master.request.auth:
            return {
                'statusCode': 302,
                'headers': {
                    'Location': get_login_url(master)
                }
            }
        
        # 管理者権限チェック
        if not master.request.decode_token:
            return render(master, "403.html", code=403)
            
        user_groups = master.request.decode_token.get("cognito:groups", [])
        if "admin" not in user_groups:
            return render(master, "403.html", {
                "error": "管理者権限が必要です"
            }, code=403)
        
        return func(master, **kwargs)
    return wrapper

@admin_required
def admin_dashboard(master):
    """管理者ダッシュボード"""
    context = {
        "title": "管理者ダッシュボード",
        "admin_user": master.request.username
    }
    return render(master, "admin/dashboard.html", context)
```

### グループベースの認証

```python
def group_required(*required_groups):
    """特定のグループに所属するユーザーのみアクセス可能"""
    def decorator(func):
        def wrapper(master, **kwargs):
            if not master.request.auth:
                return redirect_to_login(master)
            
            if not master.request.decode_token:
                return render(master, "403.html", code=403)
            
            user_groups = master.request.decode_token.get("cognito:groups", [])
            
            # 必要なグループのいずれかに所属しているかチェック
            if not any(group in user_groups for group in required_groups):
                return render(master, "403.html", {
                    "error": f"このページにアクセスするには以下のいずれかのグループに所属している必要があります: {', '.join(required_groups)}"
                }, code=403)
            
            return func(master, **kwargs)
        return wrapper
    return decorator

@group_required("moderators", "admin")
def moderator_panel(master):
    """モデレーターパネル"""
    return render(master, "moderator/panel.html")
```

## 🛠️ 高度な認証機能

### ユーザー情報の更新

```python
def update_profile(master):
    """プロフィール更新"""
    if master.request.method == "POST":
        # 更新データの取得
        given_name = master.request.body.get("given_name", "").strip()
        family_name = master.request.body.get("family_name", "").strip()
        phone_number = master.request.body.get("phone_number", "").strip()
        
        # Cognitoのユーザー属性を更新
        import boto3
        cognito_client = boto3.client('cognito-idp')
        
        try:
            attributes = []
            if given_name:
                attributes.append({"Name": "given_name", "Value": given_name})
            if family_name:
                attributes.append({"Name": "family_name", "Value": family_name})
            if phone_number:
                attributes.append({"Name": "phone_number", "Value": phone_number})
            
            cognito_client.admin_update_user_attributes(
                UserPoolId=master.settings.COGNITO.user_pool_id,
                Username=master.request.username,
                UserAttributes=attributes
            )
            
            master.logger.info(f"ユーザー情報更新: {master.request.username}")
            return redirect(master, "profile")
            
        except Exception as e:
            master.logger.error(f"ユーザー情報更新エラー: {e}")
            context = {
                "error": "プロフィールの更新に失敗しました",
                "form_data": {
                    "given_name": given_name,
                    "family_name": family_name,
                    "phone_number": phone_number
                }
            }
            return render(master, "auth/update_profile.html", context)
    
    # 現在のユーザー情報を取得
    current_info = {}
    if master.request.decode_token:
        current_info = {
            "given_name": master.request.decode_token.get("given_name", ""),
            "family_name": master.request.decode_token.get("family_name", ""),
            "phone_number": master.request.decode_token.get("phone_number", "")
        }
    
    context = {"user_info": current_info}
    return render(master, "auth/update_profile.html", context)
```

### パスワード変更

```python
def change_password(master):
    """パスワード変更"""
    if master.request.method == "POST":
        current_password = master.request.body.get("current_password", "")
        new_password = master.request.body.get("new_password", "")
        confirm_password = master.request.body.get("confirm_password", "")
        
        errors = {}
        
        # バリデーション
        if not current_password:
            errors["current_password"] = "現在のパスワードを入力してください"
        if not new_password:
            errors["new_password"] = "新しいパスワードを入力してください"
        elif len(new_password) < 8:
            errors["new_password"] = "パスワードは8文字以上で入力してください"
        if new_password != confirm_password:
            errors["confirm_password"] = "パスワードが一致しません"
        
        if not errors:
            import boto3
            cognito_client = boto3.client('cognito-idp')
            
            try:
                # アクセストークンを使ってパスワードを変更
                cognito_client.change_password(
                    PreviousPassword=current_password,
                    ProposedPassword=new_password,
                    AccessToken=master.request.access_token
                )
                
                master.logger.info(f"パスワード変更成功: {master.request.username}")
                context = {"success": "パスワードが正常に変更されました"}
                return render(master, "auth/change_password.html", context)
                
            except cognito_client.exceptions.NotAuthorizedException:
                errors["current_password"] = "現在のパスワードが正しくありません"
            except Exception as e:
                master.logger.error(f"パスワード変更エラー: {e}")
                errors["general"] = "パスワードの変更に失敗しました"
        
        context = {"errors": errors}
        return render(master, "auth/change_password.html", context)
    
    return render(master, "auth/change_password.html")
```

## 🧪 テストとデバッグ

### ローカルでの認証テスト

```python
# Lambda/project/test_auth.py
def test_auth_flow(master):
    """認証フローのテスト用ビュー"""
    if not master.settings.DEBUG:
        return render(master, "404.html", code=404)
    
    auth_info = {
        "auth_status": master.request.auth,
        "username": master.request.username,
        "access_token": master.request.access_token[:20] + "..." if master.request.access_token else None,
        "id_token": master.request.id_token[:20] + "..." if master.request.id_token else None,
        "decode_token": master.request.decode_token
    }
    
    context = {
        "title": "認証テスト",
        "auth_info": auth_info
    }
    
    return render(master, "test/auth_debug.html", context)
```

### デバッグ用テンプレート

```html
<!-- templates/test/auth_debug.html -->
{% extends "base.html" %}

{% block title %}認証デバッグ - {{ super() }}{% endblock %}

{% block content %}
<div class="container">
    <h2>🔍 認証状態デバッグ</h2>
    
    <div class="card mb-4">
        <div class="card-header">
            <h5>認証状態</h5>
        </div>
        <div class="card-body">
            <dl class="row">
                <dt class="col-sm-3">認証状態:</dt>
                <dd class="col-sm-9">
                    {% if auth_info.auth_status %}
                        <span class="badge bg-success">✅ 認証済み</span>
                    {% else %}
                        <span class="badge bg-danger">❌ 未認証</span>
                    {% endif %}
                </dd>
                
                <dt class="col-sm-3">ユーザー名:</dt>
                <dd class="col-sm-9">{{ auth_info.username | default('未設定') }}</dd>
                
                <dt class="col-sm-3">アクセストークン:</dt>
                <dd class="col-sm-9">
                    <code>{{ auth_info.access_token | default('なし') }}</code>
                </dd>
                
                <dt class="col-sm-3">IDトークン:</dt>
                <dd class="col-sm-9">
                    <code>{{ auth_info.id_token | default('なし') }}</code>
                </dd>
            </dl>
        </div>
    </div>
    
    {% if auth_info.decode_token %}
    <div class="card">
        <div class="card-header">
            <h5>デコードされたトークン情報</h5>
        </div>
        <div class="card-body">
            <pre><code>{{ auth_info.decode_token | tojson(indent=2) }}</code></pre>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

## 📋 ベストプラクティス

### 1. セキュリティ設定

```python
# settings.py
# セキュアなクッキー設定
SECURE_COOKIES = not DEBUG
COOKIE_SAMESITE = "Lax"
COOKIE_HTTPONLY = True

# セッションタイムアウト
SESSION_TIMEOUT = 3600  # 1時間
```

### 2. エラーハンドリング

```python
def robust_auth_view(master):
    """堅牢な認証チェック"""
    try:
        # 認証チェック
        if not master.request.auth:
            return redirect_to_login(master)
        
        # トークンの有効性チェック
        if not master.request.decode_token:
            master.logger.warning("無効なトークン")
            master.request.clean_cookie = True
            return redirect_to_login(master)
        
        # トークンの期限チェック
        import time
        current_time = int(time.time())
        token_exp = master.request.decode_token.get("exp", 0)
        
        if current_time >= token_exp:
            master.logger.info("トークンの有効期限切れ")
            master.request.clean_cookie = True
            return redirect_to_login(master)
        
        # 正常な処理
        return render(master, "protected.html")
        
    except Exception as e:
        master.logger.error(f"認証エラー: {e}")
        return render(master, "auth/error.html", {
            "error": "認証処理中にエラーが発生しました"
        })
```

### 3. ログ出力

```python
def log_auth_events(master):
    """認証イベントのログ出力"""
    if master.request.auth:
        master.logger.info(f"認証ユーザーアクセス: {master.request.username} -> {master.request.path}")
    else:
        master.logger.info(f"未認証アクセス: {master.request.path}")
```

## 次のステップ

認証システムを理解したら、以下のページでローカル開発環境の詳細を学習してください：

- [ローカル開発環境](./local-development.md) - 効率的な開発環境構築
- [デプロイメント](./deployment.md) - 本番環境へのデプロイ

---

[← 前: 静的ファイル管理](./static-files.md) | [ドキュメント目次に戻る](./README.md) | [次: ローカル開発環境 →](./local-development.md)
