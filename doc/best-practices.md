# ベストプラクティス

このガイドでは、WAMBDAフレームワークを使用する際の推奨パターンとベストプラクティスをまとめています。

## 目次
- [WAMBDAアーキテクチャの理解](#wambdaアーキテクチャの理解)
- [プロジェクト設計](#プロジェクト設計)
- [ビューとルーティング](#ビューとルーティング)
- [認証の実装](#認証の実装)
- [フォーム処理](#フォーム処理)
- [モック環境の活用](#モック環境の活用)
- [パフォーマンス最適化](#パフォーマンス最適化)
- [エラーハンドリング](#エラーハンドリング)
- [ログ出力](#ログ出力)

---

## WAMBDAアーキテクチャの理解

### 基本原則

WAMBDAでは**単一のLambda関数**ですべてのHTTPリクエストを処理します：

```python
# Lambda/lambda_function.py - 唯一のエントリーポイント
def lambda_handler(event, context):
    master = Master(event, context)

    # 認証処理
    set_auth_by_cookie(master)

    # パスに基づいてビューを取得・実行
    view, kwargs = master.get_view(master.request.path)
    response = view(master, **kwargs)

    # レスポンス処理
    response = add_set_cookie_to_header(master, response)
    return response
```

### ❌ 間違った認識
```python
# これはWAMBDAのアーキテクチャではありません
def user_handler(event, context):
    # ユーザー管理専用ハンドラー
    pass

def product_handler(event, context):
    # 商品管理専用ハンドラー
    pass
```

### ✅ 正しいWAMBDAアーキテクチャ
```python
# Lambda/accounts/views.py - ビューレイヤー
def login_view(master):
    """ログインビュー"""
    if master.request.method == 'POST':
        # ログイン処理
        pass
    return render(master, 'accounts/login.html', context)

# Lambda/project/urls.py - URL設定
from accounts.views import login_view
urlpatterns = [
    path('accounts/login', login_view, name='accounts:login'),
]
```

---

## プロジェクト設計

### ディレクトリ構造のベストプラクティス

```
Lambda/
├── lambda_function.py          # 唯一のエントリーポイント
├── project/
│   ├── settings.py            # 設定ファイル
│   ├── urls.py               # メインURL設定
│   └── views.py              # 共通ビュー（404等）
├── accounts/                   # 認証アプリ
│   ├── views.py              # 認証関連ビュー
│   ├── forms.py              # 認証フォーム
│   └── urls.py               # 認証URL
├── myapp/                     # カスタムアプリ
│   ├── views.py              # アプリケーションビュー
│   ├── forms.py              # アプリケーションフォーム
│   └── urls.py               # アプリケーションURL
├── mock/                      # モック環境
│   ├── ssm.py               # SSMパラメータモック
│   └── dynamodb.py          # DynamoDBモック
└── templates/                # テンプレートファイル
```

### アプリケーション分割の指針

```python
# ✅ 良い例：機能別アプリケーション分割
accounts/     # 認証機能
├── views.py    # login_view, signup_view, logout_view
├── forms.py    # LoginForm, SignupForm
└── urls.py     # accounts関連のURL

blog/         # ブログ機能
├── views.py    # post_list_view, post_detail_view
├── forms.py    # PostForm, CommentForm
└── urls.py     # blog関連のURL

api/          # API機能
├── views.py    # api_user_view, api_post_view
└── urls.py     # API関連のURL
```

---

## ビューとルーティング

### ビュー関数の基本パターン

```python
# Lambda/myapp/views.py
from wambda.shortcuts import render, redirect, login_required
from .forms import MyForm

def basic_view(master):
    """基本的なビューパターン"""
    context = {
        'title': 'ページタイトル',
        'message': 'Hello, WAMBDA!'
    }
    return render(master, 'myapp/basic.html', context)

@login_required
def protected_view(master):
    """認証が必要なビュー"""
    context = {
        'username': master.request.username,
        'user_data': master.request.decode_token
    }
    return render(master, 'myapp/protected.html', context)

def form_view(master):
    """フォーム処理パターン"""
    if master.request.method == 'POST':
        form = MyForm(master.request.get_form_data())
        if form.validate():
            # 処理成功
            return redirect(master, 'success_url')
        else:
            # バリデーションエラー
            context = {'form': form, 'errors': form.errors}
            return render(master, 'myapp/form.html', context)
    else:
        form = MyForm()
        context = {'form': form}
        return render(master, 'myapp/form.html', context)
```

### URL設計のベストプラクティス

```python
# Lambda/project/urls.py - メインURL設定
from wambda.urls import path, include

urlpatterns = [
    # ホーム
    path('', home_view, name='home'),

    # アプリケーション別URL
    path('accounts/', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path('api/v1/', include('api.urls')),

    # 静的ページ
    path('about', about_view, name='about'),
    path('contact', contact_view, name='contact'),
]

# Lambda/blog/urls.py - アプリケーション別URL
from wambda.urls import path
from .views import post_list_view, post_detail_view, post_create_view

urlpatterns = [
    path('', post_list_view, name='blog:list'),
    path('post/{id}', post_detail_view, name='blog:detail'),
    path('create', post_create_view, name='blog:create'),
]
```

### クエリパラメータの活用

```python
def search_view(master):
    """検索機能でのクエリパラメータ活用"""
    # クエリパラメータ取得
    query = master.request.query_params.get('q', '')
    page = int(master.request.query_params.get('page', '1'))

    if query:
        # 検索実行
        results = search_posts(query, page)
    else:
        results = []

    context = {
        'query': query,
        'results': results,
        'page': page
    }
    return render(master, 'search.html', context)

def success_with_message(master):
    """リダイレクト時のメッセージ表示"""
    message_type = master.request.query_params.get('message', '')

    context = {}
    if message_type == 'created':
        context['success_message'] = '作成が完了しました'
    elif message_type == 'updated':
        context['success_message'] = '更新が完了しました'

    return render(master, 'success.html', context)
```

---

## 認証の実装

### 認証ビューのパターン

```python
# Lambda/accounts/views.py
from wambda.shortcuts import render, redirect
from wambda.authenticate import login, signup, verify, sign_out
from .forms import LoginForm, SignupForm, VerifyForm

def login_view(master):
    """ログインビューの標準実装"""
    if master.request.method == 'POST':
        form = LoginForm(master.request.get_form_data())
        if form.validate():
            username = form.username.data
            password = form.password.data

            if login(master, username, password):
                # ログイン成功
                return redirect(master, 'home')
            else:
                # ログイン失敗
                context = {'form': form, 'error': 'ログインに失敗しました'}
                return render(master, 'accounts/login.html', context)
    else:
        form = LoginForm()

        # メッセージ表示
        message_type = master.request.query_params.get('message', '')
        context = {'form': form}

        if message_type == 'verify_success':
            context['message'] = 'メールアドレスの確認が完了しました'
        elif message_type == 'logout_success':
            context['message'] = 'ログアウトしました'

    return render(master, 'accounts/login.html', context)

def signup_view(master):
    """サインアップビューの標準実装"""
    if master.request.method == 'POST':
        form = SignupForm(master.request.get_form_data())
        if form.validate():
            username = form.username.data
            email = form.email.data
            password = form.password.data

            if signup(master, username, email, password):
                # サインアップ成功
                return redirect(master, 'accounts:verify', query_params={
                    'username': username,
                    'message': 'signup_success'
                })
            else:
                context = {'form': form, 'error': 'サインアップに失敗しました'}
                return render(master, 'accounts/signup.html', context)
    else:
        form = SignupForm()

    return render(master, 'accounts/signup.html', {'form': form})
```

### 認証デコレータの使用

```python
from wambda.shortcuts import login_required

@login_required
def user_profile_view(master):
    """ユーザープロフィール表示"""
    # 認証済みユーザーの情報取得
    username = master.request.username
    user_token = master.request.decode_token

    context = {
        'username': username,
        'email': user_token.get('email', ''),
        'user_attributes': user_token
    }
    return render(master, 'accounts/profile.html', context)
```

---

## フォーム処理

### WTFormsの活用

```python
# Lambda/myapp/forms.py
from wtforms import Form, StringField, TextAreaField, validators

class ContactForm(Form):
    """お問い合わせフォーム"""
    name = StringField('お名前', [
        validators.DataRequired(message='お名前は必須です'),
        validators.Length(min=2, max=50, message='2文字以上50文字以下で入力してください')
    ])

    email = StringField('メールアドレス', [
        validators.DataRequired(message='メールアドレスは必須です'),
        validators.Email(message='正しいメールアドレスを入力してください')
    ])

    message = TextAreaField('メッセージ', [
        validators.DataRequired(message='メッセージは必須です'),
        validators.Length(min=10, max=1000, message='10文字以上1000文字以下で入力してください')
    ])

# Lambda/myapp/views.py
def contact_view(master):
    """お問い合わせフォームの処理"""
    if master.request.method == 'POST':
        form = ContactForm(master.request.get_form_data())
        if form.validate():
            # フォームデータの保存・送信処理
            save_contact_message(form.data)

            return redirect(master, 'contact_success')
        else:
            # バリデーションエラー
            context = {'form': form}
            return render(master, 'contact.html', context)
    else:
        form = ContactForm()
        context = {'form': form}
        return render(master, 'contact.html', context)
```

### ファイルアップロード

```python
def upload_view(master):
    """ファイルアップロードの処理"""
    if master.request.method == 'POST':
        # multipart/form-dataの処理
        form_data = master.request.get_form_data()

        if 'file' in form_data:
            file_data = form_data['file']

            # ファイル検証
            if validate_file(file_data):
                # S3にアップロード
                s3_key = upload_to_s3(file_data)

                return redirect(master, 'upload_success', query_params={
                    'file_key': s3_key
                })
            else:
                context = {'error': '無効なファイルです'}
                return render(master, 'upload.html', context)

    return render(master, 'upload.html')
```

---

## モック環境の活用

### 開発時のモック設定

```python
# Lambda/project/settings.py
import os

# 環境に応じたモック設定
DEBUG = os.environ.get('WAMBDA_DEBUG', 'False').lower() == 'true'
USE_MOCK = os.environ.get('WAMBDA_USE_MOCK', 'False').lower() == 'true'

# 開発時は認証をバイパス
NO_AUTH = DEBUG and USE_MOCK

# モック環境でのみ使用
if USE_MOCK:
    # モックデータの自動セットアップ
    from wambda.handler import use_mock
    use_mock()
```

### モックデータの設計

```python
# Lambda/mock/ssm.py - SSMパラメータモック
def set_data():
    """開発に必要なSSMパラメータを設定"""
    import boto3
    ssm = boto3.client('ssm')

    # Cognito設定（モック用）
    parameters = [
        {
            'Name': '/Cognito/user_pool_id',
            'Value': 'ap-northeast-1_MockPool123',
            'Type': 'String'
        },
        {
            'Name': '/Cognito/client_id',
            'Value': 'mock-client-id-12345',
            'Type': 'String'
        },
        {
            'Name': '/Cognito/client_secret',
            'Value': 'mock-client-secret-67890',
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

# Lambda/mock/dynamodb.py - DynamoDBモック
def set_data():
    """テスト用DynamoDBテーブルとデータを作成"""
    import boto3

    dynamodb = boto3.resource('dynamodb')

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
        sample_users = [
            {
                'user_id': 'test-user-1',
                'email': 'test1@example.com',
                'name': 'テストユーザー1'
            },
            {
                'user_id': 'test-user-2',
                'email': 'test2@example.com',
                'name': 'テストユーザー2'
            }
        ]

        with table.batch_writer() as batch:
            for user in sample_users:
                batch.put_item(Item=user)

    except Exception as e:
        # テーブルが既に存在する場合は無視
        pass
```

---

## パフォーマンス最適化

### 初期化の最適化

```python
# Lambda/lambda_function.py
import boto3
from wambda.handler import Master

# ❌ 悪い例：関数内で初期化
def lambda_handler(event, context):
    # 毎回初期化される（コールドスタートのたびに実行）
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

# ✅ 良い例：グローバルで初期化
import boto3
dynamodb = boto3.resource('dynamodb')  # コールドスタート時のみ
users_table = dynamodb.Table('Users')

def lambda_handler(event, context):
    master = Master(event, context)
    # 初期化済みのリソースを使用
    set_auth_by_cookie(master)
    # 以下処理継続...
```

### AWSリソースの再利用

```python
# Lambda/utils/aws_clients.py
import boto3

# AWSクライアントのシングルトン管理
class AWSClients:
    _dynamodb = None
    _s3 = None
    _ssm = None

    @classmethod
    def get_dynamodb(cls):
        if cls._dynamodb is None:
            cls._dynamodb = boto3.resource('dynamodb')
        return cls._dynamodb

    @classmethod
    def get_s3(cls):
        if cls._s3 is None:
            cls._s3 = boto3.client('s3')
        return cls._s3

    @classmethod
    def get_ssm(cls):
        if cls._ssm is None:
            cls._ssm = boto3.client('ssm')
        return cls._ssm

# Lambda/myapp/views.py
from utils.aws_clients import AWSClients

def data_view(master):
    """最適化されたAWSリソース使用"""
    dynamodb = AWSClients.get_dynamodb()
    table = dynamodb.Table('Users')

    # データ取得
    response = table.scan()
    users = response.get('Items', [])

    return render(master, 'data.html', {'users': users})
```

---

## エラーハンドリング

### 統一されたエラーレスポンス

```python
# Lambda/utils/errors.py
from wambda.shortcuts import render

def handle_404(master):
    """404エラーの統一処理"""
    context = {
        'error_code': '404',
        'error_message': 'ページが見つかりません',
        'requested_path': master.request.path
    }
    return render(master, 'errors/404.html', context, code=404)

def handle_500(master, error=None):
    """500エラーの統一処理"""
    context = {
        'error_code': '500',
        'error_message': 'サーバー内部エラーが発生しました'
    }

    # デバッグ情報（開発環境のみ）
    if master.settings.DEBUG and error:
        context['debug_info'] = str(error)

    return render(master, 'errors/500.html', context, code=500)

# Lambda/myapp/views.py
def safe_view(master):
    """エラーハンドリング付きビュー"""
    try:
        # メイン処理
        data = get_user_data(master.request.username)
        return render(master, 'user_data.html', {'data': data})

    except UserNotFoundError:
        return handle_404(master)

    except DatabaseError as e:
        master.logger.error(f"Database error: {e}")
        return handle_500(master, e)

    except Exception as e:
        master.logger.error(f"Unexpected error: {e}")
        return handle_500(master, e)
```

---

## ログ出力

### 構造化ログの実装

```python
# Lambda/lambda_function.py
def lambda_handler(event, context):
    master = Master(event, context)

    # リクエスト開始ログ
    master.logger.info(
        f"Request started: {master.request.method} {master.request.path}",
        extra={
            'request_id': context.aws_request_id,
            'method': master.request.method,
            'path': master.request.path,
            'user_agent': master.request.headers.get('User-Agent', ''),
            'ip_address': master.request.remote_addr
        }
    )

    try:
        set_auth_by_cookie(master)

        # 認証状態ログ
        if master.request.auth:
            master.logger.info(
                f"Authenticated user: {master.request.username}",
                extra={'username': master.request.username}
            )

        view, kwargs = master.get_view(master.request.path)
        response = view(master, **kwargs)

        # レスポンス成功ログ
        master.logger.info(
            f"Request completed: {response.get('statusCode', 200)}",
            extra={
                'status_code': response.get('statusCode', 200),
                'response_size': len(response.get('body', ''))
            }
        )

        return add_set_cookie_to_header(master, response)

    except Exception as e:
        # エラーログ
        master.logger.error(
            f"Request failed: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc()
            },
            exc_info=True
        )

        from utils.errors import handle_500
        return handle_500(master, e)
```

### ビュー内でのログ出力

```python
def business_logic_view(master):
    """ビジネスロジックでのログ活用"""
    master.logger.info("Starting business process", extra={
        'user': master.request.username,
        'process': 'data_import'
    })

    try:
        # 処理実行
        result = execute_business_process()

        master.logger.info("Business process completed", extra={
            'user': master.request.username,
            'process': 'data_import',
            'result_count': len(result)
        })

        return render(master, 'success.html', {'result': result})

    except ProcessingError as e:
        master.logger.warning("Business process warning", extra={
            'user': master.request.username,
            'process': 'data_import',
            'warning': str(e)
        })

        return render(master, 'warning.html', {'message': str(e)})
```

---

## 関連ドキュメント

- [プロジェクト構造](./project-structure.md) - ディレクトリ構成の詳細
- [認証とCognito統合](./authentication.md) - 認証システムの詳細
- [ローカル開発環境](./local-development.md) - 開発環境のセットアップ
- [デプロイメントガイド](./deployment.md) - 本番環境への配布

---

[← ドキュメント目次に戻る](./README.md)