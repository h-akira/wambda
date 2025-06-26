# クイックスタート

このページでは、HADSを使って簡単なWebアプリケーションを作成し、ローカル環境での動作確認からAWSへのデプロイまでを実践します。

## 🎯 作成するアプリケーション

シンプルなTodoアプリケーションを作成します：
- トップページでTodoリストを表示
- 新しいTodoの追加
- Todoの完了/未完了の切り替え

## 📁 プロジェクトの作成

### 1. プロジェクト初期化

```bash
hads-admin.py --init
```

以下のように入力：
```
Enter project name (directory name): todo-app
Enter suffix (to make resources unique, default is same as project name): todo-app
Enter python version (default is 3.12): 3.12
Enter region (default is ap-northeast-1): ap-northeast-1
```

### 2. プロジェクトディレクトリに移動

```bash
cd todo-app
```

## 🌐 URLルーティングの設定

### Lambda/project/urls.py の編集

```python
from hads.urls import Path
from .views import index, add_todo, toggle_todo

urlpatterns = [
    Path("", index, name="index"),
    Path("add", add_todo, name="add_todo"),
    Path("toggle/{todo_id}", toggle_todo, name="toggle_todo"),
]
```

## 📝 ビューの実装

### Lambda/project/views.py の作成

```python
from hads.shortcuts import render, redirect, json_response

# 簡単なインメモリストレージ（本番では外部DBを使用）
todos = [
    {"id": 1, "text": "HADSを学習する", "completed": False},
    {"id": 2, "text": "Todoアプリを作る", "completed": True},
]
next_id = 3

def index(master):
    """トップページ - Todoリストを表示"""
    context = {
        "todos": todos,
        "total_count": len(todos),
        "completed_count": len([t for t in todos if t["completed"]])
    }
    return render(master, "index.html", context)

def add_todo(master):
    """新しいTodoを追加"""
    global next_id
    
    if master.request.method == "POST":
        todo_text = master.request.body.get("todo_text", "").strip()
        if todo_text:
            todos.append({
                "id": next_id,
                "text": todo_text,
                "completed": False
            })
            next_id += 1
        return redirect(master, "index")
    
    # GETリクエストの場合は追加フォームを表示
    return render(master, "add_todo.html")

def toggle_todo(master, todo_id):
    """Todoの完了/未完了を切り替え"""
    todo_id = int(todo_id)
    
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = not todo["completed"]
            break
    
    # AJAXリクエストの場合はJSONレスポンス
    if master.request.method == "POST":
        todo = next((t for t in todos if t["id"] == todo_id), None)
        return json_response(master, {"success": True, "completed": todo["completed"] if todo else False})
    
    # 通常のリクエストの場合はリダイレクト
    return redirect(master, "index")
```

## 🎨 テンプレートの作成

### Lambda/templates/base.html

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Todo App{% endblock %}</title>
    <link href="{{ static(master, 'css/style.css') }}" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1><a href="{{ reverse(master, 'index') }}">📝 Todo App</a></h1>
        </header>
        
        <main>
            {% block content %}{% endblock %}
        </main>
        
        <footer>
            <p>Powered by HADS</p>
        </footer>
    </div>
    <script src="{{ static(master, 'js/app.js') }}"></script>
</body>
</html>
```

### Lambda/templates/index.html

```html
{% extends "base.html" %}

{% block title %}Todo List - Todo App{% endblock %}

{% block content %}
<div class="stats">
    <p>総数: {{ total_count }} | 完了: {{ completed_count }} | 残り: {{ total_count - completed_count }}</p>
</div>

<div class="add-todo">
    <a href="{{ reverse(master, 'add_todo') }}" class="btn btn-primary">➕ 新しいTodoを追加</a>
</div>

<div class="todo-list">
    {% if todos %}
        {% for todo in todos %}
        <div class="todo-item {% if todo.completed %}completed{% endif %}" data-id="{{ todo.id }}">
            <div class="todo-content">
                <span class="todo-text">{{ todo.text }}</span>
                <div class="todo-actions">
                    <button class="btn btn-toggle" onclick="toggleTodo({{ todo.id }})">
                        {% if todo.completed %}
                            ↩️ 未完了に戻す
                        {% else %}
                            ✅ 完了
                        {% endif %}
                    </button>
                </div>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty-state">
            <p>📋 まだTodoがありません</p>
            <a href="{{ reverse(master, 'add_todo') }}" class="btn btn-primary">最初のTodoを追加する</a>
        </div>
    {% endif %}
</div>
{% endblock %}
```

### Lambda/templates/add_todo.html

```html
{% extends "base.html" %}

{% block title %}Todo追加 - Todo App{% endblock %}

{% block content %}
<div class="form-container">
    <h2>📝 新しいTodoを追加</h2>
    
    <form method="POST" action="{{ reverse(master, 'add_todo') }}">
        <div class="form-group">
            <label for="todo_text">Todo内容:</label>
            <input type="text" id="todo_text" name="todo_text" required
                   placeholder="やることを入力してください..." autofocus>
        </div>
        
        <div class="form-actions">
            <button type="submit" class="btn btn-primary">✅ 追加</button>
            <a href="{{ reverse(master, 'index') }}" class="btn btn-secondary">❌ キャンセル</a>
        </div>
    </form>
</div>
{% endblock %}
```

## 🎨 静的ファイルの作成

### 1. 静的ファイルディレクトリを作成

```bash
mkdir -p static/css static/js static/images
```

### static/css/style.css

```css
/* リセットCSS */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: white;
    min-height: 100vh;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

/* ヘッダー */
header h1 a {
    text-decoration: none;
    color: #2c3e50;
    font-size: 2.5em;
    font-weight: bold;
}

header h1 a:hover {
    color: #3498db;
}

/* 統計情報 */
.stats {
    background-color: #ecf0f1;
    padding: 15px;
    border-radius: 5px;
    margin: 20px 0;
    text-align: center;
    font-weight: bold;
}

/* ボタン */
.btn {
    display: inline-block;
    padding: 10px 20px;
    margin: 5px;
    border: none;
    border-radius: 5px;
    text-decoration: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
    transition: background-color 0.3s ease;
}

.btn-primary {
    background-color: #3498db;
    color: white;
}

.btn-primary:hover {
    background-color: #2980b9;
}

.btn-secondary {
    background-color: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background-color: #7f8c8d;
}

.btn-toggle {
    background-color: #27ae60;
    color: white;
    font-size: 12px;
    padding: 5px 10px;
}

.btn-toggle:hover {
    background-color: #229954;
}

/* Todo関連 */
.add-todo {
    text-align: center;
    margin: 20px 0;
}

.todo-list {
    margin: 20px 0;
}

.todo-item {
    background-color: #ffffff;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin: 10px 0;
    padding: 15px;
    transition: all 0.3s ease;
}

.todo-item:hover {
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.todo-item.completed {
    background-color: #d5f4e6;
    opacity: 0.7;
}

.todo-item.completed .todo-text {
    text-decoration: line-through;
    color: #666;
}

.todo-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.todo-text {
    flex: 1;
    font-size: 16px;
}

.todo-actions {
    margin-left: 10px;
}

.empty-state {
    text-align: center;
    padding: 40px;
    color: #666;
}

.empty-state p {
    font-size: 18px;
    margin-bottom: 20px;
}

/* フォーム */
.form-container {
    max-width: 500px;
    margin: 40px auto;
    padding: 30px;
    background-color: #f9f9f9;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.form-container h2 {
    text-align: center;
    margin-bottom: 30px;
    color: #2c3e50;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
    color: #34495e;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
}

.form-group input:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 5px rgba(52, 152, 219, 0.3);
}

.form-actions {
    text-align: center;
    margin-top: 30px;
}

/* フッター */
footer {
    text-align: center;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    color: #666;
}

/* レスポンシブ */
@media (max-width: 600px) {
    .container {
        padding: 10px;
    }
    
    header h1 a {
        font-size: 2em;
    }
    
    .todo-content {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .todo-actions {
        margin-left: 0;
        margin-top: 10px;
    }
}
```

### static/js/app.js

```javascript
// Todo切り替え機能
function toggleTodo(todoId) {
    fetch(`/toggle/${todoId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // ページをリロードして最新状態を表示
            location.reload();
        } else {
            alert('エラーが発生しました');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('通信エラーが発生しました');
    });
}

// フォームの送信時にボタンを無効化
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '処理中...';
            }
        });
    });
});
```

## 🚀 ローカル実行

### 1. SAM Local でテスト

```bash
# SAMサーバーを起動（別ターミナル）
hads-admin.py admin.json --local-server-run sam

# 静的ファイルサーバーを起動（別ターミナル）
hads-admin.py admin.json --local-server-run static

# プロキシサーバーを起動（メインターミナル）
hads-admin.py admin.json --local-server-run proxy
```

### 2. ブラウザでアクセス

`http://localhost:8000` にアクセスして動作確認

### 3. コマンドラインでテスト

```bash
# トップページのテスト
hads-admin.py admin.json --test-get /

# 特定パスのテスト
hads-admin.py admin.json --test-get /add
```

## ☁️ AWSへのデプロイ

### 1. ビルド

```bash
hads-admin.py admin.json --build
```

### 2. 初回デプロイ

```bash
hads-admin.py admin.json --deploy
```

デプロイ確認画面で `y` を入力してデプロイを実行

### 3. 静的ファイルのアップロード

```bash
# S3バケットを作成（admin.jsonで設定済みの場合）
aws s3 mb s3://your-todo-app-static --region ap-northeast-1

# admin.jsonのS3パスを更新後
hads-admin.py admin.json --static-sync2s3
```

### 4. デプロイ後の確認

デプロイ完了後に表示されるAPI Gateway URLにアクセスして動作確認

## 🔄 更新とデプロイ

### コードの更新

```bash
# 変更後にビルド・デプロイ
hads-admin.py admin.json --build --deploy --no-confirm-changeset
```

### 静的ファイルの更新

```bash
# S3に静的ファイルを同期
hads-admin.py admin.json --static-sync2s3
```

## 🎉 完成！

これでHADSを使った最初のWebアプリケーションが完成しました！

### 学習した内容

- ✅ HADSプロジェクトの初期化
- ✅ URLルーティングの設定
- ✅ ビュー関数の実装
- ✅ Jinja2テンプレートの作成
- ✅ 静的ファイルの管理
- ✅ ローカル開発環境の使用
- ✅ AWSへのデプロイ

## 次のステップ

より高度な機能を学びたい場合は、以下のページを参照してください：

- [認証とCognito連携](./authentication.md) - ユーザー認証機能の追加
- [データベース連携](./database.md) - DynamoDBとの連携
- [ベストプラクティス](./best-practices.md) - 効率的な開発手法

---

[← 前: インストールと初期設定](./installation.md) | [ドキュメント目次に戻る](./README.md) | [次: プロジェクト構造 →](./project-structure.md)
