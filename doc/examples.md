# サンプルアプリケーション

WAMBDAフレームワークの公式テンプレートプロジェクトを紹介します。これらのテンプレートを使用することで、WAMBDA アプリケーションの開発をすぐに開始できます。

## 公式テンプレート

### WambdaInitProject_SSR001

**サーバーサイドレンダリング（SSR）テンプレート**

完全な認証機能付きのWebアプリケーションテンプレートです。

#### 特徴
- **AWS Cognito認証**: ユーザー登録、ログイン、パスワード管理
- **アカウント管理**: プロフィール表示、パスワード変更、アカウント削除
- **フォーム処理**: WTFormsによる統合フォーム検証
- **テンプレートシステム**: Jinja2による動的HTML生成
- **クエリパラメータ**: URLパラメータ対応
- **モック環境**: 開発時のAWSサービスモック

#### プロジェクト構造
```
WambdaInitProject_SSR001/
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
│   ├── todo/                      # サンプルアプリ
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── mock/                      # モック設定
│   │   ├── ssm.py               # SSMパラメータモック
│   │   └── dynamodb.py          # DynamoDBモック
│   └── templates/                # Jinja2テンプレート
├── static/                        # 静的ファイル
├── template.yaml                  # SAM設定
└── samconfig.toml                # SAM デプロイ設定
```

#### 取得方法
```bash
# wambda-admin.pyを使用（推奨）
python wambda-admin.py init -n my-project -t SSR001

# 直接クローン
git clone https://github.com/h-akira/WambdaInitProject_SSR001.git
cd WambdaInitProject_SSR001
rm -rf .git
```

#### セットアップ
```bash
cd my-project/Lambda

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# ローカル開発サーバー起動
cd ..
python wambda-admin.py proxy
```

#### デプロイ
```bash
# SAM CLI でデプロイ
sam build
sam deploy --guided

# 静的ファイルをS3に同期
aws s3 sync static/ s3://your-bucket/static/
```

### WambdaInitProject_CSR001（将来予定）

**クライアントサイドレンダリング（CSR）テンプレート**

Vue、React、Angular等のフロントエンドフレームワークと組み合わせて使用するAPIテンプレートです。

*※ 現在開発中です。リリース時期は未定です。*

## カスタマイズガイド

### 認証設定のカスタマイズ

```python
# Lambda/project/settings.py

# 認証URL設定
LOGIN_URL = "accounts:login"
SIGNUP_URL = "accounts:signup"
VERIFY_URL = "accounts:verify"
LOGOUT_URL = "accounts:logout"

# 開発・テスト設定
NO_AUTH = False  # 認証スキップ（開発用）
DENY_SIGNUP = False  # サインアップ無効化
DENY_LOGIN = False   # ログイン無効化
```

### モック環境の活用

開発時にAWSサービスをローカルでエミュレートできます：

```python
# Lambda/project/settings.py
USE_MOCK = True  # モック環境を有効化

# Lambda/mock/ssm.py - SSMパラメータのモック
# Lambda/mock/dynamodb.py - DynamoDBテーブルのモック
```

### アプリケーション拡張

TodoアプリをベースにしたカスタマイズExample：

```python
# Lambda/myapp/views.py
from wambda.shortcuts import render, redirect, login_required
from .forms import MyForm

@login_required
def my_view(master):
    if master.request.method == 'POST':
        form = MyForm(master.request.get_form_data())
        if form.validate():
            # 処理ロジック
            return redirect(master, 'success')
    else:
        form = MyForm()

    return render(master, 'myapp/form.html', {'form': form})
```

## テスト方法

### ローカルテスト

```bash
# lambda_function.pyを直接実行してテスト
cd Lambda
python lambda_function.py
```

### 認証テスト

```bash
# ログインフローテスト（対話的実行）
cd Lambda
python lambda_function.py
# 実行時に以下のパスをテスト:
# /accounts/signup
# /accounts/verify
# /accounts/login
```

## トラブルシューティング

### よくある問題

1. **モジュールが見つからない**
   ```bash
   pip install -r Lambda/requirements.txt
   ```

2. **認証エラー**
   ```python
   # settings.py
   NO_AUTH = True  # 開発時のみ
   ```

3. **ポート競合**
   ```bash
   python wambda-admin.py proxy -p 8001  # 別ポートを使用
   ```

## 関連ドキュメント

- [認証とCognito統合](./authentication.md) - 詳細な認証システムの解説
- [ローカル開発環境](./local-development.md) - 開発環境のセットアップ
- [デプロイメントガイド](./deployment.md) - 本番環境へのデプロイ
- [プロジェクト構造](./project-structure.md) - ディレクトリ構成の説明

---

[← ドキュメント目次に戻る](./README.md)