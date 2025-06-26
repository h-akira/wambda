# テンプレートシステム

HADSはJinja2テンプレートエンジンを使用して、動的なHTMLページを生成します。このページでは、HADSでのテンプレートシステムの使い方を詳しく説明します。

## 🎨 基本概念

### Jinja2テンプレートエンジン

HADSはJinja2を使用しており、以下の機能を提供します：
- **変数展開**: `{{ variable }}`
- **制御構造**: `{% if %}`, `{% for %}`, `{% block %}`
- **テンプレート継承**: `{% extends %}`
- **フィルター**: `{{ value|filter }}`
- **カスタム関数**: HADS独自の関数

### テンプレートディレクトリ

テンプレートファイルは `Lambda/templates/` ディレクトリに配置します：

```
Lambda/templates/
├── base.html           # ベーステンプレート
├── index.html          # トップページ
├── blog/              # ブログ関連テンプレート
│   ├── index.html
│   ├── detail.html
│   └── form.html
└── components/        # 再利用可能コンポーネント
    ├── navbar.html
    ├── footer.html
    └── pagination.html
```

## 🏗️ テンプレート継承

### ベーステンプレート

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ title | default('HADSアプリ') }}{% endblock %}</title>
    
    <!-- CSS -->
    <link href="{{ static(master, 'css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ static(master, 'css/app.css') }}" rel="stylesheet">
    {% block extra_css %}{% endblock %}
    
    <!-- メタタグ -->
    {% block meta %}
    <meta name="description" content="HADSで構築されたWebアプリケーション">
    <meta name="author" content="Your Name">
    {% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
    <!-- ナビゲーション -->
    {% block navbar %}
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ reverse(master, 'index') }}">
                📱 HADSアプリ
            </a>
            
            <div class="navbar-nav ms-auto">
                {% if master.request.auth %}
                    <span class="navbar-text me-3">
                        ようこそ、{{ master.request.username }}さん
                    </span>
                    <a class="nav-link" href="{{ reverse(master, 'logout') }}">
                        ログアウト
                    </a>
                {% else %}
                    <a class="nav-link" href="{{ get_login_url(master) }}">
                        ログイン
                    </a>
                {% endif %}
            </div>
        </div>
    </nav>
    {% endblock %}
    
    <!-- メインコンテンツ -->
    <main class="container my-4">
        {% block messages %}
            {% if messages %}
                {% for message in messages %}
                <div class="alert alert-{{ message.type }} alert-dismissible fade show">
                    {{ message.text }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
                {% endfor %}
            {% endif %}
        {% endblock %}
        
        {% block content %}{% endblock %}
    </main>
    
    <!-- フッター -->
    {% block footer %}
    <footer class="bg-light py-4 mt-5">
        <div class="container text-center">
            <p class="mb-0">&copy; 2024 HADSアプリケーション. All rights reserved.</p>
            <p class="mb-0">
                <small>Powered by <a href="https://github.com/h-akira/hads">HADS</a></small>
            </p>
        </div>
    </footer>
    {% endblock %}
    
    <!-- JavaScript -->
    <script src="{{ static(master, 'js/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ static(master, 'js/app.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 子テンプレート

```html
<!-- templates/blog/index.html -->
{% extends "base.html" %}

{% block title %}ブログ - {{ super() }}{% endblock %}

{% block meta %}
{{ super() }}
<meta name="description" content="最新のブログ記事一覧">
<meta property="og:title" content="ブログ">
<meta property="og:description" content="最新のブログ記事一覧">
{% endblock %}

{% block extra_css %}
<link href="{{ static(master, 'css/blog.css') }}" rel="stylesheet">
{% endblock %}

{% block body_class %}blog-page{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <h1>📝 ブログ</h1>
        
        {% if posts %}
            {% for post in posts %}
            <article class="blog-post mb-4">
                <h2>
                    <a href="{{ reverse(master, 'blog:detail', slug=post.slug) }}">
                        {{ post.title }}
                    </a>
                </h2>
                <p class="text-muted">
                    <small>
                        {{ post.created_at|datetime }} by {{ post.author }}
                    </small>
                </p>
                <p>{{ post.excerpt }}</p>
                <a href="{{ reverse(master, 'blog:detail', slug=post.slug) }}" 
                   class="btn btn-primary">続きを読む</a>
            </article>
            {% endfor %}
            
            <!-- ページネーション -->
            {% if pagination %}
                {% include "components/pagination.html" %}
            {% endif %}
        {% else %}
            <div class="text-center py-5">
                <h3>📄 記事がありません</h3>
                <p>まだブログ記事が投稿されていません。</p>
            </div>
        {% endif %}
    </div>
    
    <div class="col-md-4">
        <!-- サイドバー -->
        {% include "blog/sidebar.html" %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
console.log("ブログページが読み込まれました");
</script>
{% endblock %}
```

## 🔧 HADS組み込み関数

HADSは以下の関数をテンプレート内で使用できます：

### static() - 静的ファイルURL生成

```html
<!-- CSS -->
<link href="{{ static(master, 'css/style.css') }}" rel="stylesheet">

<!-- JavaScript -->
<script src="{{ static(master, 'js/app.js') }}"></script>

<!-- 画像 -->
<img src="{{ static(master, 'images/logo.png') }}" alt="ロゴ">

<!-- ファビコン -->
<link rel="icon" href="{{ static(master, 'favicon.ico') }}">
```

### reverse() - URL逆引き

```html
<!-- 基本的な使用 -->
<a href="{{ reverse(master, 'index') }}">ホーム</a>

<!-- パラメータ付き -->
<a href="{{ reverse(master, 'user_profile', user_id=user.id) }}">
    プロフィール
</a>

<!-- 名前空間付き -->
<a href="{{ reverse(master, 'blog:detail', slug=post.slug) }}">
    {{ post.title }}
</a>

<!-- フォームのaction -->
<form method="POST" action="{{ reverse(master, 'contact_form') }}">
    <!-- フォーム要素 -->
</form>
```

### get_login_url() / get_signup_url() - 認証URL

```html
<!-- ログインリンク -->
<a href="{{ get_login_url(master) }}" class="btn btn-primary">
    ログイン
</a>

<!-- サインアップリンク -->
<a href="{{ get_signup_url(master) }}" class="btn btn-outline-primary">
    新規登録
</a>

<!-- 条件付き表示 -->
{% if not master.request.auth %}
<div class="auth-buttons">
    <a href="{{ get_login_url(master) }}">ログイン</a>
    <a href="{{ get_signup_url(master) }}">サインアップ</a>
</div>
{% endif %}
```

## 🎛️ 制御構造とフィルター

### 条件分岐

```html
<!-- 基本的な条件分岐 -->
{% if user.is_admin %}
    <div class="admin-panel">
        <h3>管理者パネル</h3>
        <a href="{{ reverse(master, 'admin:dashboard') }}">ダッシュボード</a>
    </div>
{% elif user.is_moderator %}
    <div class="moderator-panel">
        <h3>モデレーターパネル</h3>
        <a href="{{ reverse(master, 'mod:dashboard') }}">モデレーターページ</a>
    </div>
{% else %}
    <div class="user-panel">
        <h3>ユーザーパネル</h3>
        <a href="{{ reverse(master, 'user:profile') }}">プロフィール</a>
    </div>
{% endif %}

<!-- 認証状態の確認 -->
{% if master.request.auth %}
    <p>ログイン中: {{ master.request.username }}</p>
{% else %}
    <p><a href="{{ get_login_url(master) }}">ログインしてください</a></p>
{% endif %}

<!-- 値の存在確認 -->
{% if posts %}
    <ul>
    {% for post in posts %}
        <li>{{ post.title }}</li>
    {% endfor %}
    </ul>
{% else %}
    <p>投稿がありません</p>
{% endif %}
```

### ループ処理

```html
<!-- 基本的なループ -->
<ul class="post-list">
{% for post in posts %}
    <li class="post-item">
        <h3>{{ post.title }}</h3>
        <p>{{ post.excerpt }}</p>
        <small>{{ loop.index }}件目 / 全{{ loop.length }}件</small>
    </li>
{% endfor %}
</ul>

<!-- ループ内での条件分岐 -->
<div class="row">
{% for item in items %}
    <div class="col-md-4 mb-3">
        <div class="card {% if loop.first %}border-primary{% endif %}">
            <div class="card-body">
                <h5 class="card-title">{{ item.title }}</h5>
                <p class="card-text">{{ item.description }}</p>
                {% if loop.last %}
                    <small class="text-muted">最後のアイテム</small>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- 3つごとに改行 -->
    {% if loop.index % 3 == 0 and not loop.last %}
        </div><div class="row">
    {% endif %}
{% endfor %}
</div>

<!-- 辞書のループ -->
<dl>
{% for key, value in user_info.items() %}
    <dt>{{ key }}</dt>
    <dd>{{ value }}</dd>
{% endfor %}
</dl>
```

### フィルター

```html
<!-- 文字列フィルター -->
<h1>{{ post.title|title }}</h1>  <!-- タイトルケース -->
<p>{{ post.content|truncate(100) }}...</p>  <!-- 文字数制限 -->
<p>{{ post.content|striptags }}</p>  <!-- HTMLタグ除去 -->

<!-- 日付フィルター -->
<p>投稿日: {{ post.created_at|strftime('%Y年%m月%d日') }}</p>
<p>更新: {{ post.updated_at|strftime('%Y-%m-%d %H:%M') }}</p>

<!-- 数値フィルター -->
<p>価格: ¥{{ product.price|int|comma }}</p>
<p>評価: {{ product.rating|round(1) }}/5.0</p>

<!-- リストフィルター -->
<p>タグ: {{ post.tags|join(', ') }}</p>
<p>最初の3つ: {{ items|slice(':3')|list }}</p>

<!-- デフォルト値 -->
<p>{{ user.bio|default('自己紹介がありません') }}</p>
<img src="{{ user.avatar|default(static(master, 'images/default-avatar.png')) }}" 
     alt="アバター">

<!-- 安全な出力（HTMLエスケープなし） -->
<div class="content">
    {{ post.html_content|safe }}
</div>

<!-- カスタムフィルター例 -->
<p>{{ post.content|markdown|safe }}</p>
```

## 🧩 コンポーネントとインクルード

### 再利用可能コンポーネント

```html
<!-- templates/components/pagination.html -->
{% if pagination.total_pages > 1 %}
<nav aria-label="ページネーション">
    <ul class="pagination justify-content-center">
        <!-- 前へ -->
        {% if pagination.has_previous %}
            <li class="page-item">
                <a class="page-link" 
                   href="{{ reverse(master, request.resolver_match.url_name, page=pagination.previous_page) }}">
                    前へ
                </a>
            </li>
        {% else %}
            <li class="page-item disabled">
                <span class="page-link">前へ</span>
            </li>
        {% endif %}
        
        <!-- ページ番号 -->
        {% for page_num in pagination.page_range %}
            {% if page_num == pagination.current_page %}
                <li class="page-item active">
                    <span class="page-link">{{ page_num }}</span>
                </li>
            {% else %}
                <li class="page-item">
                    <a class="page-link" 
                       href="{{ reverse(master, request.resolver_match.url_name, page=page_num) }}">
                        {{ page_num }}
                    </a>
                </li>
            {% endif %}
        {% endfor %}
        
        <!-- 次へ -->
        {% if pagination.has_next %}
            <li class="page-item">
                <a class="page-link" 
                   href="{{ reverse(master, request.resolver_match.url_name, page=pagination.next_page) }}">
                    次へ
                </a>
            </li>
        {% else %}
            <li class="page-item disabled">
                <span class="page-link">次へ</span>
            </li>
        {% endif %}
    </ul>
</nav>
{% endif %}
```

### フォームコンポーネント

```html
<!-- templates/components/form_field.html -->
<div class="mb-3">
    {% if field.label %}
        <label for="{{ field.id }}" class="form-label">
            {{ field.label }}
            {% if field.required %}<span class="text-danger">*</span>{% endif %}
        </label>
    {% endif %}
    
    {% if field.type == 'textarea' %}
        <textarea class="form-control {% if field.error %}is-invalid{% endif %}" 
                  id="{{ field.id }}" 
                  name="{{ field.name }}" 
                  {% if field.required %}required{% endif %}
                  {% if field.placeholder %}placeholder="{{ field.placeholder }}"{% endif %}>{{ field.value | default('') }}</textarea>
    {% elif field.type == 'select' %}
        <select class="form-select {% if field.error %}is-invalid{% endif %}" 
                id="{{ field.id }}" 
                name="{{ field.name }}" 
                {% if field.required %}required{% endif %}>
            {% if field.empty_option %}
                <option value="">{{ field.empty_option }}</option>
            {% endif %}
            {% for option in field.options %}
                <option value="{{ option.value }}" 
                        {% if option.value == field.value %}selected{% endif %}>
                    {{ option.label }}
                </option>
            {% endfor %}
        </select>
    {% else %}
        <input type="{{ field.type | default('text') }}" 
               class="form-control {% if field.error %}is-invalid{% endif %}" 
               id="{{ field.id }}" 
               name="{{ field.name }}" 
               value="{{ field.value | default('') }}"
               {% if field.required %}required{% endif %}
               {% if field.placeholder %}placeholder="{{ field.placeholder }}"{% endif %}>
    {% endif %}
    
    {% if field.help_text %}
        <div class="form-text">{{ field.help_text }}</div>
    {% endif %}
    
    {% if field.error %}
        <div class="invalid-feedback">{{ field.error }}</div>
    {% endif %}
</div>
```

### コンポーネントの使用

```html
<!-- ページネーションの使用 -->
{% include "components/pagination.html" %}

<!-- フォームフィールドの使用 -->
<form method="POST">
    {% set name_field = {
        'id': 'name',
        'name': 'name',
        'label': 'お名前',
        'type': 'text',
        'required': true,
        'placeholder': 'お名前を入力してください',
        'value': form_data.name if form_data else '',
        'error': errors.name if errors else null
    } %}
    {% include "components/form_field.html" with {"field": name_field} %}
    
    <button type="submit" class="btn btn-primary">送信</button>
</form>
```

## 🎨 レスポンシブデザイン

### Bootstrapとの連携

```html
<!-- templates/base.html のBootstrap部分 -->
<head>
    <!-- Bootstrap CSS -->
    <link href="{{ static(master, 'css/bootstrap.min.css') }}" rel="stylesheet">
    <!-- カスタムCSS -->
    <link href="{{ static(master, 'css/app.css') }}" rel="stylesheet">
</head>

<!-- レスポンシブナビゲーション -->
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
        <a class="navbar-brand" href="{{ reverse(master, 'index') }}">HADSアプリ</a>
        
        <!-- ハンバーガーメニュー -->
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
                data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item">
                    <a class="nav-link" href="{{ reverse(master, 'index') }}">ホーム</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{{ reverse(master, 'blog:index') }}">ブログ</a>
                </li>
                {% if master.request.auth %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ reverse(master, 'profile') }}">プロフィール</a>
                    </li>
                {% else %}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ get_login_url(master) }}">ログイン</a>
                    </li>
                {% endif %}
            </ul>
        </div>
    </div>
</nav>
```

### レスポンシブグリッド

```html
<!-- カードレイアウト -->
<div class="row">
    {% for item in items %}
    <div class="col-12 col-sm-6 col-md-4 col-lg-3 mb-4">
        <div class="card h-100">
            <img src="{{ static(master, 'images/' + item.image) }}" 
                 class="card-img-top" alt="{{ item.title }}">
            <div class="card-body d-flex flex-column">
                <h5 class="card-title">{{ item.title }}</h5>
                <p class="card-text flex-grow-1">{{ item.description }}</p>
                <a href="{{ reverse(master, 'item_detail', id=item.id) }}" 
                   class="btn btn-primary mt-auto">詳細を見る</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

## 🔧 高度なテンプレート機能

### マクロ定義

```html
<!-- templates/macros.html -->
{% macro render_card(title, content, url=None, button_text="詳細") %}
<div class="card mb-3">
    <div class="card-body">
        <h5 class="card-title">{{ title }}</h5>
        <p class="card-text">{{ content }}</p>
        {% if url %}
            <a href="{{ url }}" class="btn btn-primary">{{ button_text }}</a>
        {% endif %}
    </div>
</div>
{% endmacro %}

{% macro render_alert(type, message, dismissible=true) %}
<div class="alert alert-{{ type }} {% if dismissible %}alert-dismissible fade show{% endif %}">
    {{ message }}
    {% if dismissible %}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    {% endif %}
</div>
{% endmacro %}
```

### マクロの使用

```html
<!-- templates/index.html -->
{% from "macros.html" import render_card, render_alert %}

{% if success_message %}
    {{ render_alert('success', success_message) }}
{% endif %}

<div class="row">
    {% for post in posts %}
    <div class="col-md-6">
        {{ render_card(
            post.title, 
            post.excerpt, 
            reverse(master, 'blog:detail', slug=post.slug),
            "続きを読む"
        ) }}
    </div>
    {% endfor %}
</div>
```

### カスタムフィルター（Python側で定義）

```python
# Lambda/project/template_filters.py
def markdown_filter(text):
    """MarkdownをHTMLに変換"""
    import markdown
    return markdown.markdown(text)

def comma_number(value):
    """数値にカンマを追加"""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

# settings.py で登録
# TEMPLATE_FILTERS = {
#     'markdown': markdown_filter,
#     'comma': comma_number
# }
```

## 📋 ベストプラクティス

### 1. テンプレート構造の整理

```
templates/
├── base.html                  # 基本レイアウト
├── components/               # 再利用可能コンポーネント
│   ├── navbar.html
│   ├── footer.html
│   ├── pagination.html
│   └── form_field.html
├── macros.html               # マクロ定義
├── errors/                   # エラーページ
│   ├── 404.html
│   ├── 500.html
│   └── 403.html
└── pages/                    # 各ページテンプレート
    ├── index.html
    ├── about.html
    └── contact.html
```

### 2. SEO対応

```html
<!-- templates/base.html -->
<head>
    <title>{% block title %}{{ title | default('HADSアプリ') }}{% endblock %}</title>
    
    {% block meta %}
    <meta name="description" content="{% block description %}HADSで構築されたWebアプリケーション{% endblock %}">
    <meta name="keywords" content="{% block keywords %}HADS,サーバレス,Webアプリ{% endblock %}">
    <meta name="author" content="{% block author %}Your Name{% endblock %}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{% block og_title %}{{ self.title() }}{% endblock %}">
    <meta property="og:description" content="{% block og_description %}{{ self.description() }}{% endblock %}">
    <meta property="og:type" content="{% block og_type %}website{% endblock %}">
    <meta property="og:url" content="{% block og_url %}{{ request.url }}{% endblock %}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{{ self.og_title() }}">
    <meta name="twitter:description" content="{{ self.og_description() }}">
    {% endblock %}
</head>
```

### 3. パフォーマンス最適化

```html
<!-- CSS/JSの最適化 -->
<head>
    <!-- 重要なCSSは最初に読み込み -->
    <link href="{{ static(master, 'css/critical.css') }}" rel="stylesheet">
    
    <!-- 非重要なCSSは遅延読み込み -->
    <link rel="preload" href="{{ static(master, 'css/non-critical.css') }}" 
          as="style" onload="this.onload=null;this.rel='stylesheet'">
</head>

<!-- 画像の最適化 -->
<img src="{{ static(master, 'images/hero.jpg') }}" 
     alt="ヒーロー画像"
     loading="lazy"
     width="800" 
     height="400">

<!-- JSの最適化 -->
<script src="{{ static(master, 'js/app.js') }}" defer></script>
```

### 4. アクセシビリティ対応

```html
<!-- セマンティックなHTML -->
<main role="main">
    <article>
        <header>
            <h1>{{ post.title }}</h1>
            <time datetime="{{ post.created_at|isoformat }}">
                {{ post.created_at|strftime('%Y年%m月%d日') }}
            </time>
        </header>
        
        <section class="content">
            {{ post.content|safe }}
        </section>
    </article>
</main>

<!-- フォームのアクセシビリティ -->
<form>
    <div class="form-group">
        <label for="email">メールアドレス</label>
        <input type="email" id="email" name="email" 
               aria-describedby="email-help" required>
        <small id="email-help" class="form-text">
            有効なメールアドレスを入力してください
        </small>
    </div>
</form>
```

## 次のステップ

テンプレートシステムの基本を理解したら、以下のページで静的ファイルの管理について学習してください：

- [静的ファイル管理](./static-files.md) - CSS、JavaScript、画像ファイルの管理
- [認証とCognito連携](./authentication.md) - 認証機能とテンプレート連携

---

[← 前: ビューとハンドラー](./views-handlers.md) | [ドキュメント目次に戻る](./README.md) | [次: 静的ファイル管理 →](./static-files.md)
