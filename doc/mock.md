# Mock機能とテスト環境

WAMBDAフレームワークは、ローカル開発とテスト環境でAWSサービスをモック（模擬）する機能を提供しています。これにより、実際のAWSリソースを使用せずに開発・テストが可能です。

## 🎭 Mock機能の概要

WAMBDAのMock機能は以下の技術を使用しています：

- **moto**: AWSサービスのPythonモックライブラリ
- **@mock_aws デコレータ**: motoのAWSサービスモック化
- **USE_MOCK設定**: settings.pyでのモック有効化
- **mockディレクトリ**: プロジェクト固有のモックデータ設定

## 🏗️ Mock機能の仕組み

### Lambda関数内での動作

```python
# Lambda/lambda_function.py
from moto import mock_aws

def lambda_handler(event, context):
    master = Master(event, context)
    try:
        if master.settings.USE_MOCK:
            return use_mock(master)  # モック環境で実行
        else:
            return main(master)      # 実際のAWS環境で実行
    except Exception as e:
        # エラーハンドリング

@mock_aws
def use_mock(master):
    # モックデータを設定
    from mock.dynamodb import set_data as set_dynamodb_data
    from mock.ssm import set_data as set_ssm_data
    
    # モックサービスにデータを投入
    set_dynamodb_data()
    set_ssm_data()
    
    # 通常のビジネスロジックを実行
    from wambda.authenticate import set_auth_by_cookie, add_set_cookie_to_header
    set_auth_by_cookie(master)
    view, kwargs = master.router.path2view(master.request.path)
    response = view(master, **kwargs)
    add_set_cookie_to_header(master, response)
    return response
```

### settings.pyでの設定

```python
# Lambda/project/settings.py

# テスト・開発用の設定
DEBUG = True          # エラーの詳細表示
USE_MOCK = True       # motoを使用してAWSサービスをモック化
NO_AUTH = True        # 認証をバイパス（開発時のみ）
```

## 📁 Mock ディレクトリ構造

プロジェクト内でのベストプラクティス構造：

```
MyProject/
├── Lambda/
│   ├── lambda_function.py
│   ├── project/
│   │   └── settings.py
│   └── mock/                    # モック設定ディレクトリ
│       ├── ssm.py              # SSM Parameter Store モック
│       ├── dynamodb.py         # DynamoDB モック
│       ├── s3.py               # S3 モック（必要に応じて）
│       └── cognito.py          # Cognito モック（必要に応じて）
```

## 🛠️ Mock ファイルの実装

### SSM Parameter Store モック

```python
# Lambda/mock/ssm.py
import boto3

def set_data():
    """SSM Parameter Storeのモックデータを設定"""
    ssm = boto3.client('ssm')
    
    # アプリケーション固有のパラメータを設定
    parameters = [
        {
            'Name': '/MyProject/Database/Host',
            'Value': 'localhost',
            'Type': 'String'
        },
        {
            'Name': '/MyProject/Cognito/user_pool_id',
            'Value': 'ap-northeast-1_mocktestpool',
            'Type': 'String'
        },
        {
            'Name': '/MyProject/Cognito/client_id',
            'Value': 'mocktestclientid',
            'Type': 'String'
        },
        {
            'Name': '/MyProject/Cognito/client_secret',
            'Value': 'mocktestclientsecret',
            'Type': 'SecureString'
        }
    ]
    
    for param in parameters:
        try:
            ssm.put_parameter(
                Name=param['Name'],
                Value=param['Value'],
                Type=param['Type'],
                Overwrite=True
            )
            print(f"Set SSM parameter: {param['Name']}")
        except Exception as e:
            print(f"SSM parameter setting error: {e}")
```

### DynamoDB モック

```python
# Lambda/mock/dynamodb.py
import boto3

def set_data():
    """DynamoDBのモックデータを設定"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
    
    # テーブル設定
    tables_config = [
        {
            'name': 'Users',
            'key_schema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            'attribute_definitions': [{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            'sample_data': [
                {'user_id': '1', 'name': 'テストユーザー1', 'email': 'user1@example.com'},
                {'user_id': '2', 'name': 'テストユーザー2', 'email': 'user2@example.com'},
            ]
        },
        {
            'name': 'Products',
            'key_schema': [{'AttributeName': 'product_id', 'KeyType': 'HASH'}],
            'attribute_definitions': [{'AttributeName': 'product_id', 'AttributeType': 'S'}],
            'sample_data': [
                {'product_id': '1', 'name': 'サンプル商品1', 'price': 1000},
                {'product_id': '2', 'name': 'サンプル商品2', 'price': 2000},
            ]
        }
    ]
    
    for table_config in tables_config:
        create_table_with_data(dynamodb, table_config)

def create_table_with_data(dynamodb, config):
    """テーブル作成とサンプルデータ投入"""
    table_name = config['name']
    
    try:
        # テーブル作成
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=config['key_schema'],
            AttributeDefinitions=config['attribute_definitions'],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        print(f"Created DynamoDB table: {table_name}")
        
    except Exception as e:
        print(f"Table creation error (may already exist): {e}")
        table = dynamodb.Table(table_name)
    
    # サンプルデータ投入
    for item in config['sample_data']:
        table.put_item(Item=item)
    
    print(f"Inserted {len(config['sample_data'])} items into {table_name}")
```

### S3 モック（オプション）

```python
# Lambda/mock/s3.py
import boto3
import json

def set_data():
    """S3のモックデータを設定"""
    s3 = boto3.client('s3', region_name='ap-northeast-1')
    
    # バケット作成
    buckets = [
        'my-project-static-files',
        'my-project-user-uploads'
    ]
    
    for bucket_name in buckets:
        try:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-1'}
            )
            print(f"Created S3 bucket: {bucket_name}")
        except Exception as e:
            print(f"S3 bucket creation error: {e}")
    
    # サンプルファイルをアップロード
    sample_files = [
        {
            'bucket': 'my-project-static-files',
            'key': 'config.json',
            'body': json.dumps({'version': '1.0', 'environment': 'mock'})
        }
    ]
    
    for file_config in sample_files:
        try:
            s3.put_object(
                Bucket=file_config['bucket'],
                Key=file_config['key'],
                Body=file_config['body']
            )
            print(f"Uploaded {file_config['key']} to {file_config['bucket']}")
        except Exception as e:
            print(f"S3 upload error: {e}")
```

## 🚀 Mock機能の使用方法

### 1. 開発環境での有効化

```python
# Lambda/project/settings.py
DEBUG = True
USE_MOCK = True  # モック機能を有効化
NO_AUTH = True   # 認証をバイパス（開発時）
```

### 2. テストコマンド実行

```bash
# モック環境でのテスト（lambda_function.pyを直接実行）
cd Lambda
python lambda_function.py
```

**注意**: `wambda-admin.py get`コマンドは廃止されました。代わりに`python lambda_function.py`を使用してください。

### 3. ローカル開発サーバー

```bash
# プロキシサーバー起動（モック環境）
wambda-admin.py proxy
```

ブラウザで `http://localhost:8000` にアクセスすると、モック環境でアプリケーションが動作します。

## 🧪 テストシナリオの例

### lambda_function.py直接実行でのテスト

```bash
# モック環境でのテスト実行
cd Lambda
python lambda_function.py
```

`main_debug_handler`により、対話的にHTTPリクエストをテストできます。以下のような流れでテストが可能です：

1. パスの入力（例: `/`, `/api/users`）
2. HTTPメソッドの選択（GET, POST, PUT, DELETE）
3. リクエストボディの入力（POST/PUT時）
4. モック環境での実行結果確認

## ⚙️ 設定のカスタマイズ

### 環境による切り替え

```python
# Lambda/project/settings.py
import os

# 環境変数による制御
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'development':
    DEBUG = True
    USE_MOCK = True
    NO_AUTH = True
elif ENVIRONMENT == 'testing':
    DEBUG = True
    USE_MOCK = True
    NO_AUTH = False  # テスト環境では認証も検証
elif ENVIRONMENT == 'production':
    DEBUG = False
    USE_MOCK = False
    NO_AUTH = False
```

### 部分的なモック利用

```python
# 特定のサービスのみモック化
USE_MOCK_DYNAMODB = True
USE_MOCK_SSM = True
USE_MOCK_S3 = False  # S3は実際のサービスを使用
```

## 🔍 デバッグとトラブルシューティング

### モック動作の確認

```python
# Lambda/mock/ssm.py
def set_data():
    ssm = boto3.client('ssm')
    
    # デバッグ出力を追加
    print("Setting up SSM mock data...")
    
    # パラメータ設定後の確認
    try:
        response = ssm.get_parameter(Name='/MyProject/Database/Host')
        print(f"Verified parameter: {response['Parameter']['Name']} = {response['Parameter']['Value']}")
    except Exception as e:
        print(f"Verification failed: {e}")
```

### よくある問題と解決方法

#### 1. モックデータが反映されない

**原因**: USE_MOCKがFalseになっている
**解決**: `settings.py`でUSE_MOCK = Trueを確認

#### 2. テーブル作成エラー

**原因**: 同じ名前のテーブルが既に存在
**解決**: try-except文でエラーハンドリング

```python
try:
    table = dynamodb.create_table(...)
except dynamodb.exceptions.ResourceInUseException:
    table = dynamodb.Table(table_name)
```

#### 3. パラメータが見つからない

**原因**: SSMパラメータの名前が一致していない
**解決**: パラメータ名を正確に確認

```python
# デバッグ用：設定済みパラメータ一覧表示
def debug_parameters():
    ssm = boto3.client('ssm')
    response = ssm.describe_parameters()
    for param in response['Parameters']:
        print(f"Parameter: {param['Name']}")
```

## 🎯 ベストプラクティス

### 1. プロジェクト構造

- `Lambda/mock/`ディレクトリに各AWSサービス用のファイルを作成
- サービス毎にファイルを分離（ssm.py, dynamodb.py, s3.pyなど）
- `set_data()`関数でデータセットアップを統一

### 2. データ設計

- 実際のプロダクションデータに近いモックデータを作成
- テストケースに必要な最小限のデータに留める
- エッジケース用のデータも含める

### 3. 設定管理

- 環境変数での設定切り替えを活用
- development/testing/productionで適切な設定を使い分け
- モック機能のオン/オフを柔軟に制御

### 4. テスト戦略

- 単体テスト、統合テスト、E2Eテストでモック機能を使い分け
- CIパイプラインでのモックテスト自動化
- 本番環境への影響を避けるためモック環境での十分な検証

## 📚 関連ドキュメント

- [CLI Tools](./cli-tools.md) - lambda_function.py直接実行でのモック機能テスト
- [Local Development](./local-development.md) - ローカル開発環境でのモック利用
- [Best Practices](./best-practices.md) - 開発・テストのベストプラクティス

---

[← 前: 認証とCognito連携](./authentication.md) | [ドキュメント目次に戻る](./README.md) | [次: デプロイメント →](./deployment.md)