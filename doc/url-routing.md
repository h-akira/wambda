# URLルーティング

WAMBDAのURLルーティングシステムは、DjangoのURLパターンに似た直感的なAPIを提供します。このページでは、URLルーティングの詳細な使い方を説明します。

## 🛣️ 基本概念

WAMBDAのURLルーティングは以下の2つの主要コンポーネントで構成されています：

- **Path**: 単一のURLパターンとビュー関数を関連付ける
- **Router**: 複数のURLパターンをグループ化し、ネストした構造を作る

## 📍 Path クラス

### 基本的な使い方

```python
from wambda.urls import Path
from .views import index, about, contact

urlpatterns = [
    Path("", index, name="index"),           # /
    Path("about", about, name="about"),      # /about
    Path("contact", contact, name="contact") # /contact
]
```

### パラメータ付きパス

URLパスにパラメータを含めることができます：

```python
from wambda.urls import Path
from .views import user_detail, post_detail, category_posts

urlpatterns = [
    # 単一パラメータ
    Path("user/{user_id}", user_detail, name="user_detail"),
    
    # 複数パラメータ
    Path("post/{year}/{month}/{slug}", post_detail, name="post_detail"),
    
    # パラメータと固定パス
    Path("category/{category_id}/posts", category_posts, name="category_posts"),
]
```

### パラメータの制約

パラメータには型の制約を設けることもできます（将来的な機能）：

```python
# 現在の実装では文字列として取得されるため、ビュー側で型変換が必要
Path("article/{article_id}", article_detail, name="article_detail")

# ビュー関数内で型変換
def article_detail(master, article_id):
    try:
        article_id = int(article_id)
    except ValueError:
        # エラーハンドリング
        pass
```

## 🗂️ Router クラス

### 基本的なネスト

```python
# project/urls.py
from wambda.urls import Path, Router
from .views import index

urlpatterns = [
    Path("", index, name="index"),
    Router("blog", "blog.urls", name="blog"),
    Router("api", "api.urls", name="api"),
]
```

```python
# blog/urls.py
from wambda.urls import Path
from .views import blog_index, blog_detail

app_name = "blog"  # アプリケーション名（オプション）

urlpatterns = [
    Path("", blog_index, name="index"),        # /blog/
    Path("{slug}", blog_detail, name="detail") # /blog/my-post/
]
```

### 深いネスト構造

```python
# project/urls.py
urlpatterns = [
    Router("api", "api.urls", name="api"),
]

# api/urls.py
from wambda.urls import Router

urlpatterns = [
    Router("v1", "api.v1.urls", name="v1"),
    Router("v2", "api.v2.urls", name="v2"),
]

# api/v1/urls.py
from wambda.urls import Path
from .views import users_list, user_detail

urlpatterns = [
    Path("users", users_list, name="users"),
    Path("users/{user_id}", user_detail, name="user_detail"),
]
```

この構造により以下のURLが生成されます：
- `/api/v1/users`
- `/api/v1/users/123`
- `/api/v2/users`
- `/api/v2/users/123`

## 🔗 URL の逆引き（リバースルックアップ）

### reverse 関数

ビュー関数内でURLを生成する場合：

```python
from wambda.shortcuts import reverse

def my_view(master):
    # 基本的な逆引き
    home_url = reverse(master, "index")
    
    # パラメータ付き
    user_url = reverse(master, "user_detail", user_id="123")
    
    # ネストされたルーター
    blog_url = reverse(master, "blog:detail", slug="my-post")
    
    context = {
        "home_url": home_url,
        "user_url": user_url,
        "blog_url": blog_url
    }
    return render(master, "template.html", context)
```

## 🔍 クエリパラメータの処理

### クエリパラメータの取得

ビュー関数内でクエリパラメータにアクセスする方法：

```python
def search_view(master):
    # クエリパラメータを取得
    query_params = master.event.get('queryStringParameters') or {}
    
    # 個別のパラメータを取得
    search_query = query_params.get('q', '')
    page = query_params.get('page', '1')
    category = query_params.get('category', 'all')
    
    # 型変換とデフォルト値の処理
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    context = {
        'search_query': search_query,
        'page': page,
        'category': category
    }
    return render(master, 'search.html', context)
```

### redirect関数でクエリパラメータを設定

改良された`redirect`関数を使用してクエリパラメータ付きのリダイレクトを行う：

```python
from wambda.shortcuts import redirect

def signup_view(master):
    if master.request.method == 'POST':
        # サインアップ処理...
        if signup_success:
            # クエリパラメータ付きでリダイレクト
            return redirect(master, 'accounts:verify', query_params={
                'username': username,
                'message': 'signup_success'
            })
    
    return render(master, 'accounts/signup.html', {'form': form})

def verify_view(master):
    # クエリパラメータからメッセージとユーザー名を取得
    query_params = master.event.get('queryStringParameters') or {}
    username = query_params.get('username', '')
    message_type = query_params.get('message', '')
    
    if message_type == 'signup_success':
        message = 'サインアップが完了しました。確認コードをメールで送信しました。'
    else:
        message = None
    
    return render(master, 'accounts/verify.html', {
        'username': username,
        'message': message
    })
```

### redirect関数の使用例

```python
# 基本的なリダイレクト
redirect(master, 'home')

# URLパラメータ付きリダイレクト
redirect(master, 'user:detail', user_id=123)

# クエリパラメータ付きリダイレクト
redirect(master, 'search', query_params={'q': 'python', 'page': '2'})

# URLパラメータとクエリパラメータの両方
redirect(master, 'user:posts', 
         user_id=123, 
         query_params={'filter': 'published', 'sort': 'date'})
# 結果: /user/123/posts?filter=published&sort=date
```

### 実践的な例

```python
def blog_list(master):
    """ブログ一覧ページ（ページネーションとフィルタリング付き）"""
    query_params = master.event.get('queryStringParameters') or {}
    
    # クエリパラメータの取得と検証
    page = max(1, int(query_params.get('page', '1')))
    category = query_params.get('category', 'all')
    sort_by = query_params.get('sort', 'date')
    
    # データ取得ロジック...
    posts = get_posts(page=page, category=category, sort_by=sort_by)
    
    # 次のページURLを生成
    if has_next_page:
        next_url = reverse(master, 'blog:list') + f'?page={page + 1}'
        if category != 'all':
            next_url += f'&category={category}'
        if sort_by != 'date':
            next_url += f'&sort={sort_by}'
    else:
        next_url = None
    
    context = {
        'posts': posts,
        'page': page,
        'category': category,
        'sort_by': sort_by,
        'next_url': next_url
    }
    return render(master, 'blog/list.html', context)
```

### テンプレート内での使用

```html
<!-- 基本的な使用 -->
<a href="{{ reverse(master, 'index') }}">ホーム</a>

<!-- パラメータ付き -->
<a href="{{ reverse(master, 'user_detail', user_id=user.id) }}">
    {{ user.name }}のプロフィール
</a>

<!-- ネストされたルーター -->
<a href="{{ reverse(master, 'blog:detail', slug=post.slug) }}">
    {{ post.title }}
</a>
```

## 🎯 実践的な例

### ブログアプリケーションの完全な例

```python
# project/urls.py
from wambda.urls import Path, Router
from .views import index

urlpatterns = [
    Path("", index, name="index"),
    Router("blog", "blog.urls", name="blog"),
    Router("admin", "admin.urls", name="admin"),
]
```

```python
# blog/urls.py
from wambda.urls import Path, Router
from .views import (
    blog_index, post_detail, category_list, 
    category_posts, author_posts, tag_posts
)

app_name = "blog"

urlpatterns = [
    # 基本ページ
    Path("", blog_index, name="index"),
    
    # 投稿詳細
    Path("post/{slug}", post_detail, name="post_detail"),
    
    # カテゴリ
    Path("category", category_list, name="category_list"),
    Path("category/{category_slug}", category_posts, name="category_posts"),
    
    # 著者別投稿
    Path("author/{author_slug}", author_posts, name="author_posts"),
    
    # タグ別投稿
    Path("tag/{tag_slug}", tag_posts, name="tag_posts"),
    
    # 管理系
    Router("manage", "blog.admin.urls", name="manage"),
]
```

```python
# blog/admin/urls.py
from wambda.urls import Path
from .views import admin_index, post_create, post_edit, post_delete

urlpatterns = [
    Path("", admin_index, name="index"),
    Path("post/create", post_create, name="post_create"),
    Path("post/{post_id}/edit", post_edit, name="post_edit"),
    Path("post/{post_id}/delete", post_delete, name="post_delete"),
]
```

### 対応するビュー関数

```python
# blog/views.py
from wambda.shortcuts import render, redirect

def blog_index(master):
    """ブログトップページ"""
    return render(master, "blog/index.html")

def post_detail(master, slug):
    """投稿詳細ページ"""
    context = {"slug": slug}
    return render(master, "blog/post_detail.html", context)

def category_posts(master, category_slug):
    """カテゴリ別投稿一覧"""
    context = {"category_slug": category_slug}
    return render(master, "blog/category_posts.html", context)

def author_posts(master, author_slug):
    """著者別投稿一覧"""
    context = {"author_slug": author_slug}
    return render(master, "blog/author_posts.html", context)
```

## 🔧 高度な機能

### 条件付きルーティング

```python
# settings.pyの設定に基づく条件付きルーティング
from wambda.urls import Path
from .views import debug_view, production_view

def get_urlpatterns():
    from project.settings import DEBUG
    
    patterns = [
        Path("", index, name="index"),
    ]
    
    if DEBUG:
        patterns.append(Path("debug", debug_view, name="debug"))
    else:
        patterns.append(Path("status", production_view, name="status"))
    
    return patterns

urlpatterns = get_urlpatterns()
```

### 動的ルーティング

```python
# データベースの内容に基づく動的ルーティング
def dynamic_urlpatterns():
    patterns = [
        Path("", index, name="index"),
    ]
    
    # 例: 動的ページの生成
    # pages = get_pages_from_database()
    # for page in pages:
    #     patterns.append(
    #         Path(page.slug, page_view, name=f"page_{page.id}")
    #     )
    
    return patterns
```

### HTTPメソッドによる分岐

WAMBDAではビュー関数内でHTTPメソッドを処理します：

```python
def api_endpoint(master):
    """RESTful APIエンドポイント"""
    if master.request.method == "GET":
        # データ取得
        return json_response(master, {"data": []})
    
    elif master.request.method == "POST":
        # データ作成
        return json_response(master, {"created": True})
    
    elif master.request.method == "PUT":
        # データ更新
        return json_response(master, {"updated": True})
    
    elif master.request.method == "DELETE":
        # データ削除
        return json_response(master, {"deleted": True})
    
    else:
        # 未対応メソッド
        return json_response(master, {"error": "Method not allowed"}, code=405)
```

## 🐛 トラブルシューティング

### よくあるエラーと解決方法

#### 1. NotMatched エラー

```
NotMatched: パス '/blog/my-post' に一致するビューが見つかりません
```

**原因と解決方法：**
- URLパターンのタイプミス
- Router の名前空間設定の間違い
- パスパラメータの命名不一致

```python
# 間違い
Path("post/{id}", post_detail, name="detail")

# 正しい
Path("post/{post_id}", post_detail, name="detail")
```

#### 2. KwargsRemain エラー

```
KwargsRemain: 未使用のキーワード引数があります: extra_param
```

**原因と解決方法：**
```python
# 間違い - 不要なパラメータを渡している
reverse(master, "post_detail", post_id="123", extra_param="value")

# 正しい
reverse(master, "post_detail", post_id="123")
```

#### 3. パラメータの型エラー

```python
# ビュー関数で適切な型変換を行う
def post_detail(master, post_id):
    try:
        post_id = int(post_id)
    except ValueError:
        # 無効なIDの場合の処理
        return render(master, "404.html", code=404)
```

## 📋 ベストプラクティス

### 1. 命名規則

```python
# URL名前は動詞_名詞の形式を推奨
Path("post/create", post_create, name="post_create")
Path("post/{id}/edit", post_edit, name="post_edit")
Path("post/{id}/delete", post_delete, name="post_delete")
```

### 2. アプリケーション名前空間

```python
# 各アプリケーションでapp_nameを設定
app_name = "blog"

# 使用時は名前空間を含める
reverse(master, "blog:post_detail", post_id="123")
```

### 3. パラメータの検証

```python
def user_detail(master, user_id):
    # パラメータの検証
    if not user_id.isdigit():
        return render(master, "400.html", code=400)
    
    user_id = int(user_id)
    if user_id <= 0:
        return render(master, "400.html", code=400)
```

### 4. SEO フレンドリーなURL

```python
# 良い例
Path("blog/{year}/{month}/{slug}", post_detail, name="post_detail")
# /blog/2024/03/introducing-wambda

# 避けるべき例
Path("post/{id}", post_detail, name="post_detail")
# /post/123
```

## 次のステップ

URLルーティングを理解したら、以下のページでビュー関数の詳細を学習してください：

- [ビューとハンドラー](./views-handlers.md) - ビュー関数の詳細な実装
- [テンプレートシステム](./templates.md) - レスポンスの生成方法

---

[← 前: プロジェクト構造](./project-structure.md) | [ドキュメント目次に戻る](./README.md) | [次: ビューとハンドラー →](./views-handlers.md)
