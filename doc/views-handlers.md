# ビューとハンドラー

WAMBDAのビューシステムは、Djangoライクなアプローチを採用しており、リクエストを受け取ってレスポンスを返すシンプルな関数として実装されています。このページでは、ビュー関数の詳細な実装方法を説明します。

## 🎯 ビュー関数の基本

### 基本構造

```python
def my_view(master, **kwargs):
    """
    ビュー関数の基本構造
    
    Args:
        master: WAMBDAのMasterオブジェクト（リクエスト情報やログ機能を含む）
        **kwargs: URLパラメータから渡される引数
        
    Returns:
        HTTPレスポンス辞書
    """
    # ビジネスロジック
    context = {"message": "Hello, WAMBDA!"}
    
    # レスポンスを返す
    return render(master, "template.html", context)
```

### Masterオブジェクト

`master`オブジェクトには以下の属性があります：

```python
def my_view(master):
    # リクエスト情報
    master.request.method    # HTTPメソッド（GET, POST, etc.）
    master.request.path      # リクエストパス
    master.request.body      # POSTデータ（辞書形式）
    master.request.auth      # 認証状態（True/False）
    master.request.username  # 認証済みユーザー名
    
    # 設定情報
    master.settings          # settings.pyの内容
    master.local            # ローカル環境かどうか（True/False）
    
    # ユーティリティ
    master.logger           # ロガーオブジェクト
    master.router          # ルーターオブジェクト
```

## 📝 基本的なビューパターン

### シンプルなページ表示

```python
from wambda.shortcuts import render

def index(master):
    """トップページ"""
    context = {
        "title": "ホーム",
        "message": "WAMBDAアプリケーションへようこそ",
        "items": ["項目1", "項目2", "項目3"]
    }
    return render(master, "index.html", context)
```

### パラメータを受け取るビュー

```python
def user_profile(master, user_id):
    """ユーザープロフィールページ"""
    # パラメータの検証
    try:
        user_id = int(user_id)
    except ValueError:
        master.logger.error(f"無効なuser_id: {user_id}")
        return render(master, "400.html", code=400)
    
    # データ取得（ここでは簡単な例）
    user_data = {
        "id": user_id,
        "name": f"ユーザー{user_id}",
        "email": f"user{user_id}@example.com"
    }
    
    context = {
        "user": user_data,
        "title": f"{user_data['name']}のプロフィール"
    }
    
    return render(master, "user/profile.html", context)
```

### フォーム処理

```python
from wambda.shortcuts import render, redirect

def contact_form(master):
    """お問い合わせフォーム"""
    if master.request.method == "POST":
        # POSTデータの取得
        name = master.request.body.get("name", "").strip()
        email = master.request.body.get("email", "").strip()
        message = master.request.body.get("message", "").strip()
        
        # バリデーション
        errors = {}
        if not name:
            errors["name"] = "お名前は必須です"
        if not email:
            errors["email"] = "メールアドレスは必須です"
        elif "@" not in email:
            errors["email"] = "有効なメールアドレスを入力してください"
        if not message:
            errors["message"] = "メッセージは必須です"
        
        if not errors:
            # 処理成功時
            master.logger.info(f"お問い合わせを受信: {name} <{email}>")
            
            # ここで実際の処理（メール送信など）を行う
            # send_email(name, email, message)
            
            # 成功ページにリダイレクト
            return redirect(master, "contact_success")
        else:
            # エラーがある場合はフォームを再表示
            context = {
                "errors": errors,
                "form_data": {
                    "name": name,
                    "email": email,
                    "message": message
                }
            }
            return render(master, "contact/form.html", context)
    
    # GETリクエストの場合は空のフォームを表示
    return render(master, "contact/form.html")

def contact_success(master):
    """お問い合わせ送信完了ページ"""
    return render(master, "contact/success.html")
```

## 🔄 HTTPレスポンスの種類

### HTML レスポンス

```python
from wambda.shortcuts import render

def html_response(master):
    context = {"data": "value"}
    return render(master, "template.html", context, code=200)
```

### JSON レスポンス

```python
from wambda.shortcuts import json_response

def api_data(master):
    data = {
        "status": "success",
        "data": [
            {"id": 1, "name": "項目1"},
            {"id": 2, "name": "項目2"}
        ],
        "count": 2
    }
    return json_response(master, data)

def api_error(master):
    error_data = {
        "status": "error",
        "message": "リクエストが無効です",
        "code": "INVALID_REQUEST"
    }
    return json_response(master, error_data, code=400)
```

### リダイレクト

```python
from wambda.shortcuts import redirect

def redirect_view(master):
    # 名前付きURLへのリダイレクト
    return redirect(master, "index")

def redirect_with_params(master):
    # パラメータ付きリダイレクト
    return redirect(master, "user_profile", user_id="123")
```

### カスタムレスポンス

```python
from wambda.shortcuts import gen_response

def csv_download(master):
    csv_data = "name,email\nJohn,john@example.com\nJane,jane@example.com"
    return gen_response(
        master,
        csv_data,
        content_type="text/csv",
        code=200
    )

def file_download(master):
    # バイナリファイルの場合
    import base64
    
    # ファイルデータをBase64エンコード
    with open("path/to/file.pdf", "rb") as f:
        file_data = base64.b64encode(f.read()).decode()
    
    return gen_response(
        master,
        file_data,
        content_type="application/pdf",
        code=200,
        isBase64Encoded=True
    )
```

## 🔐 認証とアクセス制御

### ログイン必須デコレータ

```python
from wambda.shortcuts import login_required

@login_required
def protected_view(master):
    """ログインが必要なページ"""
    context = {
        "username": master.request.username,
        "title": "保護されたページ"
    }
    return render(master, "protected.html", context)
```

### カスタム認証チェック

```python
def admin_required(func):
    """管理者権限が必要なビューのデコレータ"""
    def wrapper(master, **kwargs):
        # ログインチェック
        if not master.request.auth:
            return redirect(master, "login")
        
        # 管理者権限チェック（実装例）
        if not master.request.username.endswith("@admin.com"):
            return render(master, "403.html", code=403)
        
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

## 🎨 APIビューの実装

### RESTful API

```python
from wambda.shortcuts import json_response

def users_api(master):
    """ユーザー一覧API"""
    if master.request.method == "GET":
        # ユーザー一覧取得
        users = [
            {"id": 1, "name": "田中太郎", "email": "tanaka@example.com"},
            {"id": 2, "name": "佐藤花子", "email": "sato@example.com"}
        ]
        return json_response(master, {"users": users})
    
    elif master.request.method == "POST":
        # 新規ユーザー作成
        name = master.request.body.get("name")
        email = master.request.body.get("email")
        
        if not name or not email:
            return json_response(
                master, 
                {"error": "名前とメールアドレスは必須です"}, 
                code=400
            )
        
        # ユーザー作成処理（簡単な例）
        new_user = {
            "id": 3,
            "name": name,
            "email": email
        }
        
        master.logger.info(f"新規ユーザー作成: {new_user}")
        return json_response(master, {"user": new_user}, code=201)
    
    else:
        return json_response(
            master, 
            {"error": "サポートされていないメソッドです"}, 
            code=405
        )

def user_detail_api(master, user_id):
    """ユーザー詳細API"""
    try:
        user_id = int(user_id)
    except ValueError:
        return json_response(
            master, 
            {"error": "無効なユーザーIDです"}, 
            code=400
        )
    
    if master.request.method == "GET":
        # ユーザー詳細取得
        user = {
            "id": user_id,
            "name": f"ユーザー{user_id}",
            "email": f"user{user_id}@example.com"
        }
        return json_response(master, {"user": user})
    
    elif master.request.method == "PUT":
        # ユーザー情報更新
        name = master.request.body.get("name")
        email = master.request.body.get("email")
        
        updated_user = {
            "id": user_id,
            "name": name or f"ユーザー{user_id}",
            "email": email or f"user{user_id}@example.com"
        }
        
        return json_response(master, {"user": updated_user})
    
    elif master.request.method == "DELETE":
        # ユーザー削除
        master.logger.info(f"ユーザー削除: {user_id}")
        return json_response(master, {"message": "ユーザーが削除されました"})
```

## 🔧 高度なビューパターン

### ページネーション

```python
def paginated_list(master):
    """ページネーション付きリスト"""
    page = int(master.request.body.get("page", "1"))
    per_page = 10
    
    # 全データ数（実際はDBから取得）
    total_count = 100
    
    # ページネーション計算
    total_pages = (total_count + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    # データ取得（実際はDBから取得）
    items = [f"アイテム{i}" for i in range(start + 1, min(end + 1, total_count + 1))]
    
    context = {
        "items": items,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "has_previous": page > 1,
            "has_next": page < total_pages,
            "previous_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None
        }
    }
    
    return render(master, "list.html", context)
```

### ファイルアップロード処理

```python
import base64
import os

def file_upload(master):
    """ファイルアップロード処理"""
    if master.request.method == "POST":
        # ファイルデータの取得（実際の実装では適切なパース処理が必要）
        file_data = master.request.body.get("file")
        filename = master.request.body.get("filename", "uploaded_file")
        
        if not file_data:
            return json_response(
                master, 
                {"error": "ファイルが選択されていません"}, 
                code=400
            )
        
        try:
            # Base64デコード（実際の実装では multipart/form-data のパースが必要）
            decoded_data = base64.b64decode(file_data)
            
            # ファイル保存（実際はS3などに保存）
            upload_path = f"/tmp/{filename}"
            with open(upload_path, "wb") as f:
                f.write(decoded_data)
            
            master.logger.info(f"ファイルアップロード完了: {filename}")
            
            return json_response(master, {
                "message": "ファイルのアップロードが完了しました",
                "filename": filename,
                "size": len(decoded_data)
            })
            
        except Exception as e:
            master.logger.error(f"ファイルアップロードエラー: {e}")
            return json_response(
                master, 
                {"error": "ファイルのアップロードに失敗しました"}, 
                code=500
            )
    
    return render(master, "upload.html")
```

### エラーハンドリング

```python
def robust_view(master):
    """エラーハンドリングの例"""
    try:
        # 危険な処理
        result = some_risky_operation()
        
        context = {"result": result}
        return render(master, "success.html", context)
        
    except ValueError as e:
        master.logger.warning(f"バリデーションエラー: {e}")
        return render(master, "error.html", {
            "error": "入力データが無効です"
        }, code=400)
        
    except Exception as e:
        master.logger.error(f"予期しないエラー: {e}")
        
        if master.settings.DEBUG:
            # デバッグモードでは詳細なエラー情報を表示
            import traceback
            context = {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            return render(master, "debug_error.html", context, code=500)
        else:
            # 本番環境では一般的なエラーメッセージ
            return render(master, "500.html", code=500)
```

## 📋 ベストプラクティス

### 1. ビュー関数の責務分離

```python
# 良い例：ビジネスロジックとプレゼンテーション層を分離
def user_list(master):
    # データ取得は別の関数で
    users = get_users_from_database()
    
    # ビューはレスポンス生成に集中
    context = {"users": users}
    return render(master, "users/list.html", context)

def get_users_from_database():
    """データ取得ロジック"""
    # 実際のデータベース操作
    pass
```

### 2. 入力検証の徹底

```python
def create_post(master):
    if master.request.method == "POST":
        # 必須フィールドの検証
        title = master.request.body.get("title", "").strip()
        content = master.request.body.get("content", "").strip()
        
        errors = validate_post_data(title, content)
        
        if not errors:
            post = create_post_in_database(title, content)
            return redirect(master, "post_detail", post_id=post["id"])
        else:
            context = {"errors": errors, "title": title, "content": content}
            return render(master, "posts/create.html", context)

def validate_post_data(title, content):
    """投稿データの検証"""
    errors = {}
    if not title:
        errors["title"] = "タイトルは必須です"
    elif len(title) > 100:
        errors["title"] = "タイトルは100文字以内で入力してください"
    
    if not content:
        errors["content"] = "内容は必須です"
    elif len(content) > 10000:
        errors["content"] = "内容は10000文字以内で入力してください"
    
    return errors
```

### 3. ログ出力の活用

```python
def important_operation(master):
    master.logger.info(f"重要な処理を開始: ユーザー={master.request.username}")
    
    try:
        result = perform_critical_task()
        master.logger.info(f"処理完了: 結果={result}")
        return json_response(master, {"result": result})
        
    except Exception as e:
        master.logger.error(f"処理失敗: {e}", exc_info=True)
        return json_response(master, {"error": "処理に失敗しました"}, code=500)
```

## 次のステップ

ビューとハンドラーの実装方法を理解したら、以下のページでテンプレートシステムの詳細を学習してください：

- [テンプレートシステム](./templates.md) - Jinja2テンプレートの詳細
- [認証とCognito連携](./authentication.md) - 認証機能の実装

---

[← 前: URLルーティング](./url-routing.md) | [ドキュメント目次に戻る](./README.md) | [次: テンプレートシステム →](./templates.md)

## 🛠️ ショートカット関数

WAMBDAでは、よく使用される機能を簡単に呼び出せるショートカット関数を提供しています。

> **注意**: ライブラリのバージョンによっては、`wambda.shortcuts`ではなく`wambda.shourtcuts`（typo）でインポートする必要がある場合があります。エラーが発生する場合は両方試してみてください。

```python
# 正しいインポート（推奨）
from wambda.shortcuts import render, redirect, json_response, login_required

# typoがある場合（一部のバージョン）
# from wambda.shourtcuts import render, redirect, json_response, login_required
```
