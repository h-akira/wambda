# よくある質問（FAQ）

このページでは、HADSフレームワークを使用する際によく寄せられる質問とその回答をまとめています。

## 目次
- [一般的な質問](#一般的な質問)
- [開発環境について](#開発環境について)
- [デプロイメントについて](#デプロイメントについて)
- [パフォーマンスについて](#パフォーマンスについて)
- [セキュリティについて](#セキュリティについて)
- [トラブルシューティング](#トラブルシューティング)

---

## 一般的な質問

### Q: HADSとDjangoの主な違いは何ですか？

**A:** HADSはAWS Lambdaで動作するサーバレスアプリケーション専用に設計されています：

- **実行環境**: Lambdaのイベント駆動型実行モデル
- **スケーリング**: 自動的な無限スケーリング
- **状態管理**: ステートレスな設計
- **認証**: AWS Cognitoとの緊密な統合
- **コスト**: 使用量ベースの課金

### Q: 既存のDjangoアプリケーションをHADSに移植できますか？

**A:** 部分的に可能ですが、以下の点を考慮する必要があります：

- **URLパターン**: HADSの`urls.py`形式に変更
- **ビュー関数**: Lambda形式のハンドラーに変更
- **データベース**: サーバレス対応のデータベース（DynamoDB、RDS Serverless等）への移行
- **セッション管理**: ステートレス設計への変更

### Q: HADSはどのようなユースケースに適していますか？

**A:** 以下のようなアプリケーションに最適です：

- **API開発**: RESTful API、GraphQL API
- **マイクロサービス**: 小規模で独立したサービス
- **Webアプリケーション**: 軽量なWebアプリ
- **管理ツール**: 社内ツール、ダッシュボード
- **イベント処理**: Webhook、バッチ処理

---

## 開発環境について

### Q: ローカル開発環境のセットアップで問題が発生します

**A:** 以下の手順を確認してください：

1. **Python環境**: Python 3.8以上がインストールされているか
2. **仮想環境**: `venv`または`conda`で隔離された環境を使用
3. **依存関係**: `pip install -r requirements.txt`が正常に実行されるか
4. **AWS設定**: AWS CLIが正しく設定されているか

```bash
# 環境確認コマンド
python --version
pip --version
aws --version
aws sts get-caller-identity
```

### Q: ローカルサーバーが起動しません

**A:** 以下をチェックしてください：

1. **ポート競合**: デフォルトポート8000が使用されていないか
2. **設定ファイル**: `settings.py`が正しく配置されているか
3. **環境変数**: 必要な環境変数が設定されているか

```bash
# ポート確認
lsof -i :8000

# 別のポートで起動
python -m hads.local_server --port 8080
```

### Q: テンプレートが見つからないエラーが発生します

**A:** テンプレートパスの設定を確認してください：

```python
# settings.py
TEMPLATE_DIRS = [
    'templates',
    'static/templates'
]
```

---

## デプロイメントについて

### Q: Lambda関数のメモリ設定はどうすべきですか？

**A:** アプリケーションの複雑さに応じて設定してください：

- **軽量API**: 128-256MB
- **一般的なWebアプリ**: 512-1024MB
- **重い処理**: 1024-3008MB

### Q: コールドスタートの問題を軽減するには？

**A:** 以下の方法が効果的です：

1. **Provisioned Concurrency**: 事前にウォームアップ
2. **依存関係の最適化**: 不要なライブラリの除去
3. **レイヤーの活用**: 共通ライブラリの分離
4. **初期化の最適化**: グローバルスコープでの初期化

### Q: 環境変数の管理方法は？

**A:** AWS Systems Manager Parameter Storeまたは環境変数を使用：

```python
import os
import boto3

# 環境変数から取得
DATABASE_URL = os.environ.get('DATABASE_URL')

# Parameter Storeから取得
ssm = boto3.client('ssm')
response = ssm.get_parameter(
    Name='/myapp/database/url',
    WithDecryption=True
)
DATABASE_URL = response['Parameter']['Value']
```

---

## パフォーマンスについて

### Q: レスポンス時間を改善するには？

**A:** 以下の最適化を検討してください：

1. **データベース最適化**:
   - クエリの最適化
   - インデックスの適切な設定
   - 接続プールの活用

2. **キャッシング**:
   - ElastiCacheの活用
   - CDNの利用（CloudFront）

3. **コード最適化**:
   - 不要な処理の削除
   - 非同期処理の活用

### Q: メモリ使用量を最適化するには？

**A:** 以下の方法が効果的です：

```python
# 大きなオブジェクトの適切な管理
import gc

def handler(event, context):
    # 処理
    result = heavy_processing()
    
    # 明示的なガベージコレクション
    gc.collect()
    
    return result
```

---

## セキュリティについて

### Q: API認証のベストプラクティスは？

**A:** 以下の方法を推奨します：

1. **JWT Token**: 短期間有効なトークン
2. **API Key**: 外部サービス連携用
3. **AWS Cognito**: ユーザー認証
4. **IAM Role**: AWS リソースアクセス

### Q: CORS設定で問題が発生します

**A:** 適切なCORS設定を行ってください：

```python
# handler.py
def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }

def handler(event, context):
    # OPTIONSリクエストの処理
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': ''
        }
    
    # 通常の処理
    response = process_request(event)
    response['headers'].update(cors_headers())
    
    return response
```

---

## トラブルシューティング

### Q: Lambda関数がタイムアウトします

**A:** 以下を確認してください：

1. **タイムアウト設定**: Lambda関数のタイムアウト時間
2. **外部API**: 外部サービスの応答時間
3. **データベース**: クエリの実行時間
4. **ネットワーク**: VPC設定やセキュリティグループ

### Q: 「Module not found」エラーが発生します

**A:** 依存関係の問題です：

```bash
# ローカル環境で確認
pip list

# requirements.txtの更新
pip freeze > requirements.txt

# Lambda レイヤーの確認
aws lambda list-layers
```

### Q: CloudWatchログが出力されません

**A:** IAMロールの権限を確認してください：

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

---

## 関連ドキュメント

- [トラブルシューティングガイド](troubleshooting.md)
- [ベストプラクティス](best-practices.md)
- [API リファレンス](api-reference.md)
- [サンプルアプリケーション](examples.md)

---

[← 戻る](README.md)
