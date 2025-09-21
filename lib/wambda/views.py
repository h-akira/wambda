"""
WAMBDA Framework default views
"""

def url_not_matched_view(master):
  """
  デフォルトの404エラーページビュー
  URLパターンにマッチしない場合に呼び出される
  """
  from wambda.shortcuts import gen_response

  html_content = """
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ページが見つかりません - 404 Error</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #f5f5f5;
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
      }
      .container {
        text-align: center;
        background: white;
        padding: 3rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        max-width: 500px;
      }
      .error-code {
        font-size: 4rem;
        font-weight: bold;
        color: #e74c3c;
        margin-bottom: 1rem;
      }
      .error-message {
        font-size: 1.2rem;
        color: #2c3e50;
        margin-bottom: 2rem;
      }
      .back-link {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        background-color: #3498db;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        transition: background-color 0.3s;
      }
      .back-link:hover {
        background-color: #2980b9;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="error-code">404</div>
      <div class="error-message">
        お探しのページが見つかりませんでした。<br>
        URLが正しいかご確認ください。
      </div>
    </div>
  </body>
</html>
  """

  return gen_response(master, html_content, "text/html; charset=UTF-8", 404)