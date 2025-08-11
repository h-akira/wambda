# HADS フレームワーク 開発環境設計書

## 1. 開発環境概要

### 1.1 開発環境構成
HADSフレームワークは、SAM Local、統合プロキシサーバー、専用CLIツールによる、モダンなサーバーレス開発環境を提供します。

### 1.2 開発環境の特徴
- **コマンドライン中心**: 設定ファイル不要のCLIベース管理
- **統合プロキシサーバー**: SAM LocalとStatic Serverを統合したワンストップ開発環境
- **テスト機能内蔵**: SAM Local Invokeによる単体テスト機能
- **環境自動判定**: 環境変数ベースの自動環境切り替え

## 2. 開発環境アーキテクチャ

### 2.1 ローカル開発構成図

```mermaid
graph TD
    A[Developer] --> B[hads-admin.py CLI]
    B --> C[Command Router]
    
    C -->|init| D[Project Template]
    C -->|proxy| E[Proxy Server<br/>Port 8000]
    C -->|static| F[Static Server<br/>Port 8080] 
    C -->|get| G[SAM Local Invoke<br/>Test Runner]
    
    E --> H{Request Type}
    H -->|Static Files<br/>/static/*| F
    H -->|Application<br/>Other paths| I[SAM Local<br/>Port 3000]
    
    I --> J[Lambda Function]
    J --> K[HADS Framework]
    F --> L[Static Files]
    
    M[Environment Variables] --> N[Runtime Config]
    N --> I
```

### 2.2 CLIコマンド構成

| コマンド | 機能 | 説明 |
|---------|------|------|
| `hads-admin.py init` | プロジェクト初期化 | テンプレートベースの新規プロジェクト作成 |
| `hads-admin.py proxy` | 統合プロキシサーバー | SAM Local + Static Serverの統合エンドポイント |
| `hads-admin.py static` | 静的ファイルサーバー | CSS, JS, 画像などの専用配信サーバー |
| `hads-admin.py get` | テスト実行 | SAM Local Invokeによる単体テスト |

### 2.3 サーバー構成

| サーバー | ポート | 起動方法 | 説明 |
|---------|--------|---------|------|
| プロキシサーバー | 8000 | `hads-admin.py proxy` | 統合開発エンドポイント |
| SAM Local | 3000 | `sam local start-api` | Lambda関数とAPI Gateway模擬 |
| 静的ファイルサーバー | 8080 | `hads-admin.py static` | 静的ファイル専用配信 |

## 3. ローカルサーバー詳細

### 3.1 静的ファイルサーバー

```python
def run_static_server(static_url, static_dir, port=8080):
    """
    静的ファイルを提供するサーバーを実行
    
    Args:
        static_url: 静的ファイルのURLパス（例: '/static'）
        static_dir: 静的ファイルのディレクトリパス
        port: サーバーのポート番号
    """
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if path.startswith(static_url):
                return os.path.join(os.getcwd(), path[1:])
            else:
                return None
                
        def do_GET(self):
            path = self.translate_path(self.path)
            if path and os.path.exists(path) and os.path.isfile(path):
                super().do_GET()
            else:
                self.send_error(404, "File Not Found")
```

#### 特徴
- **パスマッピング**: `/static/*` リクエストを実際のファイルシステムパスにマッピング
- **セキュリティ**: 指定されたディレクトリ外へのアクセスを制限
- **エラーハンドリング**: 存在しないファイルへの適切な404レスポンス

### 3.2 プロキシサーバー

```python
def run_proxy_server(static_url, port=8000, sam_port=3000, static_port=8080):
    """
    リバースプロキシサーバーを実行
    
    Args:
        static_url: 静的ファイルのURLパス
        port: プロキシサーバーのポート
        sam_port: SAM Localサーバーのポート
        static_port: 静的ファイルサーバーのポート
    """
    class ReverseProxyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_url = urlparse(self.path)
            if parsed_url.path.startswith(static_url):
                target_url = f'http://localhost:{static_port}{self.path}'
            else:
                target_url = f'http://localhost:{sam_port}{self.path}'
            
            try:
                with urllib.request.urlopen(target_url) as response:
                    self.send_response(response.status)
                    self.send_header('Content-type', 
                                   response.headers.get('Content-type', 'text/html'))
                    self.end_headers()
                    self.wfile.write(response.read())
            except urllib.error.URLError as e:
                self.send_error(500, str(e.reason))
```

#### ルーティング規則
- **静的ファイル**: `/static/*` → 静的ファイルサーバー (8080)
- **アプリケーション**: その他すべて → SAM Local (3000)

## 4. 環境判定システム

### 4.1 環境判定ロジック

```python
def _set_local(self):
    """ローカル開発環境かどうかを判定"""
    AWS_SAM_LOCAL = os.getenv("AWS_SAM_LOCAL")
    
    if AWS_SAM_LOCAL is not None:
        # 環境変数による判定（優先）
        if AWS_SAM_LOCAL == "true":
            self.local = True
        elif AWS_SAM_LOCAL == "false":
            self.local = False
        else:
            raise ValueError("AWS_SAM_LOCALは'true'または'false'である必要があります")
    else:
        # 環境変数がない場合はデフォルトで本番環境
        self.local = False
```

### 4.2 判定基準

| 判定方法 | 条件 | 結果 |
|---------|------|------|
| 環境変数 | `AWS_SAM_LOCAL=true` | ローカル環境 |
| 環境変数 | `AWS_SAM_LOCAL=false` | 本番環境 |
| デフォルト | 環境変数が設定されていない | 本番環境 |

### 4.3 環境変数の設定方法

```bash
# ローカル開発時（SAM Local使用時は自動設定）
export AWS_SAM_LOCAL=true

# 本番環境（明示的に設定）
export AWS_SAM_LOCAL=false
```

## 5. 設定管理

### 5.1 コマンドライン引数による設定

HADSは設定ファイルに依存せず、すべてコマンドライン引数で設定を管理します：

```bash
# プロキシサーバーのポート設定
hads-admin.py proxy -p 9000 -s 3001 --static-port 8081

# 静的ファイルディレクトリの指定
hads-admin.py static -d assets --static-url /files

# テンプレート指定でプロジェクト作成
hads-admin.py init -n my-app -t SSR001
```

### 5.2 環境変数による設定

実行時設定は環境変数で管理：

```bash
# AWSプロファイル指定
export AWS_PROFILE=development

# AWSリージョン指定
export AWS_DEFAULT_REGION=ap-northeast-1

# ローカル環境指定
export AWS_SAM_LOCAL=true
```

### 5.3 SAM設定ファイル（samconfig.toml）

デプロイ設定は`samconfig.toml`で管理：

```toml
version = 0.1

[default.deploy.parameters]
stack_name = "hads-dev"
region = "ap-northeast-1"
capabilities = "CAPABILITY_IAM"

[production.deploy.parameters]
stack_name = "hads-prod"
region = "ap-northeast-1"
profile = "production"
```

### 5.3 URL/パス設定の環境対応

```python
# settings.py
MAPPING_PATH = "stage-01"  # 本番: API Gatewayのステージ名
MAPPING_PATH_LOCAL = ""    # ローカル: 空文字列（ステージなし）

# 使用時の自動切り替え
def reverse(master, app_name, **kwargs):
    path = master.router.name2path(app_name, kwargs)
    
    if master.local:
        MAPPING_PATH = master.settings.MAPPING_PATH_LOCAL
    else:
        MAPPING_PATH = master.settings.MAPPING_PATH
        
    if MAPPING_PATH.startswith("/"):
        MAPPING_PATH = MAPPING_PATH[1:]
        
    return os.path.join("/", MAPPING_PATH, path)
```

## 6. 開発ワークフロー

### 6.1 新規プロジェクト作成

```bash
# 1. HADSプロジェクトの初期化
hads-admin.py init -n my-blog-app -t SSR001

# 2. プロジェクトディレクトリに移動
cd my-blog-app

# 3. 初期テスト実行
hads-admin.py get

# 4. 統合開発サーバー起動
hads-admin.py proxy
```

### 6.2 日常的な開発サイクル

```bash
# 1. 統合プロキシサーバー起動
hads-admin.py proxy

# 2. 別ターミナルでSAM Local起動
sam local start-api --port 3000

# 3. 開発とテスト
# コード編集...
hads-admin.py get -p /new-feature

# 4. 本番デプロイ
sam build && sam deploy
```

### 6.3 個別サーバー起動（デバッグ用）

```bash
# 静的ファイルサーバーのみ
hads-admin.py static

# カスタム設定で起動
hads-admin.py proxy -p 9000 --static-port 8081
```

### 6.3 開発時のURL構成

```
ローカル開発環境:
http://localhost:8000/                 → アプリケーションホーム
http://localhost:8000/api/users        → API エンドポイント
http://localhost:8000/static/css/style.css → 静的ファイル

本番環境:
https://api.example.com/stage-01/      → アプリケーションホーム
https://api.example.com/stage-01/api/users → API エンドポイント
https://api.example.com/stage-01/static/css/style.css → 静的ファイル
```

## 7. デバッグとログ

### 7.1 ローカル開発でのログ出力

```python
# lambda_function.py
def lambda_handler(event, context):
    master = Master(event, context)
    master.logger.info(f"Request: {master.request.method} {master.request.path}")
    
    if master.local:
        master.logger.info("ローカル開発環境で実行中")
    
    try:
        # アプリケーション処理
        pass
    except Exception as e:
        master.logger.exception("エラーが発生しました")
```

### 7.2 エラー表示の環境対応

```python
def error_render(master, error_message=None):
    if master.settings.DEBUG:
        # 開発環境: 詳細なエラー情報を表示
        error_html = f"""
        <h1>Error</h1>
        <h3>Error Message</h3>
        <pre>{error_message}</pre>
        <h3>Event</h3>
        <pre>{master.event}</pre>
        """
        return gen_response(master, error_html, "text/html; charset=UTF-8", 200)
    else:
        # 本番環境: 簡潔なエラーメッセージ
        return gen_response(master, "<h1>Internal Server Error</h1>", 
                          "text/html; charset=UTF-8", 500)
```

## 8. 本番デプロイ

### 8.1 SAM デプロイ設定

```yaml
# samconfig.toml
version = 0.1
[default]
[default.deploy]
[default.deploy.parameters]
stack_name = "my-hads-app"
s3_bucket = "my-deployment-bucket"
s3_prefix = "my-hads-app"
region = "ap-northeast-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "ParameterKey=Environment,ParameterValue=production"
```

### 8.2 環境変数の設定

```yaml
# template.yaml
Environment:
  Variables:
    AWS_SAM_LOCAL: "false"  # 本番環境であることを明示
```

### 8.3 静的ファイルの配信

本番環境では、静的ファイルは以下の方法で配信：

1. **API Gateway統合**: Lambdaで静的ファイルも処理
2. **S3 + CloudFront**: 別途CDNを構築
3. **カスタムドメイン**: API Gatewayのカスタムドメイン機能

## 9. パフォーマンス最適化

### 9.1 ローカル開発の最適化

```python
# 開発時の高速化設定
if master.local:
    # テンプレートキャッシュを無効化（開発時の変更を即座に反映）
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(master.settings.TEMPLATE_DIR),
        cache_size=0
    )
```

### 9.2 静的ファイルキャッシュ

```python
# 開発環境での適切なキャッシュヘッダー設定
def do_GET(self):
    # ... ファイル処理 ...
    
    # 開発環境ではキャッシュを無効化
    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    self.send_header('Pragma', 'no-cache')
    self.send_header('Expires', '0')
```

## 10. トラブルシューティング

### 10.1 よくある問題

1. **ポート競合**
   - 他のプロセスがポート使用中
   - 解決: `lsof -i :8000` でプロセス確認、または別ポート使用

2. **静的ファイル404エラー**
   - パスマッピングの設定ミス
   - 解決: `--static-url` オプションの確認

3. **AWS認証エラー**
   - AWS認証情報の設定不備
   - 解決: `aws configure` または環境変数の設定確認

4. **SAM Local起動エラー**
   - SAM CLIのインストール不備
   - 解決: `sam --version` で確認、必要に応じて再インストール

### 10.2 デバッグとログ確認

```bash
# SAM Local のログ出力
sam local start-api --port 3000 --log-file sam.log

# テスト実行でのデバッグ
hads-admin.py get -p /debug-endpoint

# プロキシサーバーのログ
# hads-admin.py proxy の出力をそのまま確認

# 環境変数でのデバッグ設定
export DEBUG=true
hads-admin.py proxy
```

### 10.3 パフォーマンス最適化

```bash
# 開発時のキャッシュ無効化
hads-admin.py proxy --no-cache

# 静的ファイルの高速配信
hads-admin.py static --static-dir public
``` 