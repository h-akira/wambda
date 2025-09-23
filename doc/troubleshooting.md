# トラブルシューティング

このガイドでは、WAMBDAフレームワークを使用する際によく発生する問題とその解決方法をまとめています。

## 目次
- [セットアップの問題](#セットアップの問題)
- [開発環境の問題](#開発環境の問題)
- [認証の問題](#認証の問題)
- [モック環境の問題](#モック環境の問題)
- [パフォーマンスの問題](#パフォーマンスの問題)
- [デプロイメントの問題](#デプロイメントの問題)
- [ログとデバッグ](#ログとデバッグ)

---

## セットアップの問題

### ImportError: No module named 'wambda'

**症状**: WAMBDAモジュールがインポートできない

**解決方法**:

1. **正しいディレクトリの確認**:
```bash
# lambda_function.pyと同じディレクトリにwambdaライブラリが必要
Lambda/
├── lambda_function.py
├── wambda/           # wambdaライブラリ
│   ├── handler.py
│   ├── authenticate.py
│   └── shortcuts.py
└── project/
    └── settings.py
```

2. **パスの確認**:
```python
# Lambda/lambda_function.py
import sys
import os
sys.path.append(os.path.dirname(__file__))  # 現在のディレクトリをパスに追加

from wambda.handler import Master
```

3. **WambdaInitProject_SSR001から正しくコピー**:
```bash
# 正しいテンプレートを使用
python wambda-admin.py init -n my-project -t SSR001
```

### lambda_function.pyが見つからない

**症状**: エントリーポイントが認識されない

**解決方法**:

WAMBDAでは`lambda_function.py`が唯一のエントリーポイントです:

```python
# Lambda/lambda_function.py - 必須ファイル
import sys
import os
sys.path.append(os.path.dirname(__file__))

from wambda.handler import Master
from wambda.authenticate import set_auth_by_cookie, add_set_cookie_to_header

def lambda_handler(event, context):
    """WAMBDAのメインハンドラー"""
    master = Master(event, context)
    master.logger.info(f"Request: {master.request.method} {master.request.path}")

    set_auth_by_cookie(master)

    try:
        view, kwargs = master.get_view(master.request.path)
        response = view(master, **kwargs)
        response = add_set_cookie_to_header(master, response)
        return response
    except Exception as e:
        master.logger.exception(e)
        from wambda.shortcuts import error_render
        import traceback
        return error_render(master, traceback.format_exc())
```

---

## 開発環境の問題

### wambda-admin.py が動作しない

**症状**: `python wambda-admin.py proxy` でエラーが発生

**解決手順**:

1. **実行ディレクトリの確認**:
```bash
# wambda-admin.pyがあるディレクトリで実行
ls -la
# wambda-admin.py が存在することを確認

# または絶対パスで実行
python /path/to/wambda/bin/wambda-admin.py proxy
```

2. **ポート競合の確認**:
```bash
# デフォルトポートが使用中かチェック
lsof -i :8000  # プロキシサーバー
lsof -i :3000  # SAM Local
lsof -i :8080  # 静的ファイルサーバー

# 別のポートで起動
python wambda-admin.py proxy -p 8001
```

3. **SAM CLIの確認**:
```bash
# SAM CLIがインストールされているかチェック
sam --version

# template.yamlの存在確認
ls template.yaml
```

### テンプレートが見つからないエラー

**症状**: `TemplateNotFoundError` が発生

**解決方法**:

1. **settings.pyの設定確認**:
```python
# Lambda/project/settings.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "..", "templates")  # 単一ディレクトリ

# ❌ 間違い: WAMBDAはリストをサポートしていません
# TEMPLATE_DIRS = ['templates', 'other_templates']
```

2. **ディレクトリ構造の確認**:
```bash
Lambda/
├── templates/          # テンプレートディレクトリ
│   ├── base.html
│   └── accounts/
│       └── login.html
└── project/
    └── settings.py
```

### Static files が表示されない

**症状**: CSS・JavaScript・画像が読み込まれない

**解決方法**:

1. **ローカル開発での静的ファイル設定**:
```bash
# プロキシサーバーを使用（推奨）
python wambda-admin.py proxy

# 静的ファイルサーバーのみ
python wambda-admin.py static -d static
```

2. **テンプレートでの正しい参照**:
```html
<!-- templates/base.html -->
<link rel="stylesheet" href="{{ static(master, 'css/main.css') }}">
<script src="{{ static(master, 'js/menu.js') }}"></script>
```

---

## 認証の問題

### ログインができない

**症状**: 正しい認証情報でもログインに失敗

**解決手順**:

1. **SSMパラメータの確認**:
```bash
# Cognitoパラメータが設定されているかチェック
aws ssm get-parameter --name "/Cognito/user_pool_id"
aws ssm get-parameter --name "/Cognito/client_id"
aws ssm get-parameter --name "/Cognito/client_secret" --with-decryption
```

2. **IAM権限の確認**:
```bash
# Lambda実行ロールに必要な権限があるかチェック
aws iam get-role-policy --role-name lambda-execution-role --policy-name CognitoAccess
```

必要なCognito権限:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminGetUser",
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminConfirmSignUp",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:ChangePassword",
                "cognito-idp:ForgotPassword",
                "cognito-idp:ConfirmForgotPassword"
            ],
            "Resource": "*"
        }
    ]
}
```

3. **NO_AUTHモードでのテスト**:
```python
# Lambda/project/settings.py
# 開発時は認証をスキップ
NO_AUTH = True
```

### 認証Cookieが正しく設定されない

**症状**: ログイン後もセッションが維持されない

**解決方法**:

1. **HTTPSの確認**:
```python
# Lambda/project/settings.py
# ローカル開発時はHTTPでもCookieを送信
import os
SECURE_COOKIE = os.environ.get('WAMBDA_SECURE_COOKIE', 'True').lower() == 'true'
```

2. **lambda_function.pyでのCookie処理確認**:
```python
def lambda_handler(event, context):
    master = Master(event, context)
    set_auth_by_cookie(master)  # Cookie読み取り

    # ビュー処理
    view, kwargs = master.get_view(master.request.path)
    response = view(master, **kwargs)

    # Cookie設定
    response = add_set_cookie_to_header(master, response)  # 重要！
    return response
```

---

## モック環境の問題

### モックが動作しない

**症状**: `USE_MOCK=True`でもAWSサービスにアクセスしようとする

**解決方法**:

1. **use_mock()の呼び出し確認**:
```python
# Lambda/lambda_function.py
from wambda.handler import use_mock

# lambda_handlerの前でuse_mockを呼び出す
use_mock()

def lambda_handler(event, context):
    # 処理
    pass
```

2. **モックファイルの存在確認**:
```bash
Lambda/mock/
├── __init__.py     # 空ファイル
├── ssm.py         # SSMモック
└── dynamodb.py    # DynamoDBモック
```

3. **motoライブラリの確認**:
```bash
pip list | grep moto
# motoがインストールされていない場合
pip install moto
```

### モックデータが初期化されない

**症状**: Mock SSMパラメータやDynamoDBテーブルが見つからない

**解決方法**:

```python
# Lambda/mock/ssm.py
def set_data():
    """必要なSSMパラメータを設定"""
    import boto3
    ssm = boto3.client('ssm')

    # Cognito設定
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

# Lambda/mock/dynamodb.py
def set_data():
    """テスト用DynamoDBテーブル作成"""
    import boto3

    dynamodb = boto3.resource('dynamodb')

    try:
        table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()

        # サンプルデータ投入
        with table.batch_writer() as batch:
            batch.put_item(Item={
                'user_id': 'test-user-1',
                'email': 'test1@example.com',
                'name': 'テストユーザー1'
            })
    except Exception:
        # テーブルが既に存在する場合は無視
        pass
```

---

## パフォーマンスの問題

### Lambda関数のタイムアウト

**症状**: 29秒または設定時間でタイムアウトが発生

**解決方法**:

1. **template.yamlでタイムアウト設定**:
```yaml
# template.yaml
Globals:
  Function:
    Timeout: 30          # 最大900秒まで設定可能
    MemorySize: 512      # メモリ増加でCPU性能向上
```

2. **コールドスタートの最適化**:
```python
# Lambda/lambda_function.py
import boto3

# グローバルで初期化（コールドスタート時のみ）
dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    # 初期化済みリソースを再利用
    master = Master(event, context)
    # 処理続行...
```

3. **ログでの処理時間測定**:
```python
def lambda_handler(event, context):
    import time
    start_time = time.time()

    master = Master(event, context)
    master.logger.info(f"Request started: {master.request.path}")

    try:
        set_auth_by_cookie(master)
        view, kwargs = master.get_view(master.request.path)
        response = view(master, **kwargs)

        processing_time = time.time() - start_time
        master.logger.info(f"Request completed in {processing_time:.2f}s")

        return add_set_cookie_to_header(master, response)
    except Exception as e:
        processing_time = time.time() - start_time
        master.logger.error(f"Request failed after {processing_time:.2f}s: {e}")
        raise
```

### メモリ不足エラー

**症状**: Lambda関数でメモリ不足が発生

**解決方法**:

1. **メモリサイズ増加**:
```yaml
# template.yaml
Resources:
  MainFunction:
    Type: AWS::Serverless::Function
    Properties:
      MemorySize: 1024    # 128MB から増加
```

2. **大量データ処理の最適化**:
```python
def process_large_data_view(master):
    """大量データ処理での最適化"""
    # ページング処理
    page_size = 100
    page = int(master.request.query_params.get('page', 1))

    # 必要なデータのみ取得
    data = get_paginated_data(page, page_size)

    return render(master, 'data_list.html', {
        'data': data,
        'page': page
    })
```

---

## デプロイメントの問題

### SAM buildが失敗する

**症状**: `sam build`でエラーが発生

**解決方法**:

1. **template.yamlの構文確認**:
```bash
sam validate
```

2. **requirements.txtの確認**:
```bash
# Lambda/requirements.txt に必要な依存関係があるか確認
pip install -r Lambda/requirements.txt
```

3. **Pythonバージョンの確認**:
```yaml
# template.yaml
Globals:
  Function:
    Runtime: python3.12  # 対応バージョンを使用
```

### デプロイ後にエラーが発生

**症状**: デプロイは成功するが実行時にエラー

**解決方法**:

1. **CloudWatchログの確認**:
```bash
# SAM CLI でログ確認
sam logs --stack-name wambda-app --tail

# AWS CLI でログ確認
aws logs tail /aws/lambda/wambda-app-MainFunction --follow
```

2. **環境変数の確認**:
```bash
# Lambda関数の設定確認
aws lambda get-function-configuration --function-name wambda-app-MainFunction
```

3. **IAM権限の確認**:
```bash
#実行ロールの権限確認
aws iam list-attached-role-policies --role-name wambda-app-MainFunctionRole
```

---

## ログとデバッグ

### ログが出力されない

**症状**: CloudWatchにログが表示されない

**解決方法**:

1. **IAM権限の確認**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

2. **ログ出力の確認**:
```python
def lambda_handler(event, context):
    master = Master(event, context)

    # ログレベルの設定
    master.logger.info("Request started")
    master.logger.debug(f"Event: {event}")

    try:
        # 処理
        return process_request(master)
    except Exception as e:
        master.logger.error(f"Error: {e}", exc_info=True)
        raise
```

### デバッグ情報の取得

**症状**: エラーの詳細情報が不足

**解決方法**:

1. **DEBUGモードの有効化**:
```python
# Lambda/project/settings.py
DEBUG = True  # 開発時のみ
```

2. **詳細ログの出力**:
```python
def lambda_handler(event, context):
    master = Master(event, context)

    if master.settings.DEBUG:
        master.logger.debug(f"Full event: {event}")
        master.logger.debug(f"Context: {context}")
        master.logger.debug(f"Request headers: {master.request.headers}")

    # 処理続行...
```

3. **ローカルテストでのデバッグ**:
```bash
# 直接ハンドラーをテスト
python wambda-admin.py get -p /

# POSTリクエストテスト
python wambda-admin.py get -p /accounts/login -m POST -b "username=test&password=secret"

# カスタムイベントでテスト
python wambda-admin.py get -e custom-event.json
```

### エラートレースの取得

**症状**: エラーの発生箇所が特定できない

**解決方法**:

```python
def lambda_handler(event, context):
    master = Master(event, context)

    try:
        set_auth_by_cookie(master)
        view, kwargs = master.get_view(master.request.path)
        response = view(master, **kwargs)
        return add_set_cookie_to_header(master, response)

    except Exception as e:
        # 詳細なエラー情報をログ出力
        import traceback
        error_traceback = traceback.format_exc()

        master.logger.error(f"Lambda handler error: {e}")
        master.logger.error(f"Traceback: {error_traceback}")

        # 開発環境ではエラー詳細を表示
        if master.settings.DEBUG:
            from wambda.shortcuts import error_render
            return error_render(master, error_traceback)
        else:
            # 本番環境では一般的なエラーページ
            from wambda.shortcuts import render
            return render(master, "errors/500.html", {"error": "サーバーエラーが発生しました"}, code=500)
```

---

## よくある設定ミス

### 1. URLパターンの設定ミス

```python
# ❌ 間違い
from django.urls import path  # djangoではない

# ✅ 正しい
from wambda.urls import path

urlpatterns = [
    path('accounts/login', login_view, name='accounts:login'),
]
```

### 2. ビュー関数の引数ミス

```python
# ❌ 間違い
def login_view(request):  # Djangoスタイル
    pass

# ✅ 正しい
def login_view(master):   # WAMBDAスタイル
    return render(master, 'login.html')
```

### 3. テンプレート関数の引数ミス

```html
<!-- ❌ 間違い -->
<a href="{{ url('home') }}">ホーム</a>

<!-- ✅ 正しい -->
<a href="{{ reverse(master, 'home') }}">ホーム</a>
<link rel="stylesheet" href="{{ static(master, 'css/main.css') }}">
```

---

## 関連ドキュメント

- [ベストプラクティス](./best-practices.md) - 推奨実装パターン
- [認証とCognito統合](./authentication.md) - 認証システムの詳細
- [ローカル開発環境](./local-development.md) - 開発環境のセットアップ
- [デプロイメントガイド](./deployment.md) - 本番環境への配布

---

[← ドキュメント目次に戻る](./README.md)