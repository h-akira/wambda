import os

def login_required(func):
    """
    ログインが必要なビューのデコレータ
    
    Args:
        func: デコレートするビュー関数
        
    Returns:
        未認証の場合はログインページにリダイレクト、認証済みの場合は元の関数を実行
    """
    def wrapper(master, **kwargs):
        if not master.request.auth:
            from wambda.authenticate import get_login_url
            response = {
                'statusCode': 302,
                'headers': {
                    'Location': get_login_url(master)
                }
            }
            
            
            return response
        return func(master, **kwargs)
    return wrapper

def reverse(master, url_name, **kwargs):
    """
    URL名前から実際のURLパスを生成する
    
    Args:
        master: Masterインスタンス
        url_name: URL名前（例: 'home', 'app:view'）
        **kwargs: URLパラメータ
        
    Returns:
        完全なURLパス（マッピングパス含む）
    """
    # ルーターからパスを生成
    path = master.router.name2path(url_name, kwargs)
    
    # マッピングパスを正規化
    mapping_path = _normalize_path(master.settings.MAPPING_PATH)
    
    # 完全なURLパスを構築
    return _build_full_path(mapping_path, path)

def static(master, file_path):
    """
    静的ファイルのURLを生成する
    
    Args:
        master: Masterインスタンス
        file_path: 静的ファイルのパス
        
    Returns:
        静的ファイルの完全なURLパス
    """
    # 静的ファイルのベースURLを取得
    static_url = _normalize_path(master.settings.STATIC_URL)
    
    # マッピングパスを正規化
    mapping_path = _normalize_path(master.settings.MAPPING_PATH)
    
    # 完全なURLパスを構築
    return _build_full_path(mapping_path, static_url, file_path)

def redirect(master, url_name, query_params=None, no_reverse=False, **kwargs):
    """
    指定されたURL名前にリダイレクトするレスポンスを生成

    Args:
        master: Masterインスタンス
        url_name: リダイレクト先のURL名前またはURL
        query_params: クエリパラメータの辞書 (例: {'key': 'value'})
        no_reverse: Trueの場合、url_nameをそのままURLとして使用（reverseしない）
        **kwargs: URLパラメータ

    Returns:
        302リダイレクトレスポンス
    """
    import urllib.parse

    # ベースURLを生成
    if no_reverse:
        base_url = url_name
    else:
        base_url = reverse(master, url_name, **kwargs)

    # クエリパラメータがある場合は追加
    if query_params:
        query_string = urllib.parse.urlencode(query_params)
        full_url = f"{base_url}?{query_string}"
    else:
        full_url = base_url

    return {
        "statusCode": 302,
        "headers": {
            "Location": full_url
        }
    }

def gen_response(master, body, content_type="text/html; charset=UTF-8", code=200, isBase64Encoded=None):
    """
    AWS Lambda用のHTTPレスポンスを生成
    
    Args:
        master: Masterインスタンス
        body: レスポンスボディ
        content_type: Content-Typeヘッダー
        code: HTTPステータスコード
        isBase64Encoded: Base64エンコードフラグ
        
    Returns:
        AWS Lambda用レスポンス辞書
    """
    response = {
        "statusCode": code,
        "headers": {
            "Content-Type": content_type
        },
        "body": body
    }
    
    if isBase64Encoded is not None:
        response["isBase64Encoded"] = isBase64Encoded
    
    
    return response

def render(master, template_file, context={}, content_type="text/html; charset=UTF-8", code=200):
    """
    Jinja2テンプレートをレンダリングしてHTMLレスポンスを生成
    
    Args:
        master: Masterインスタンス
        template_file: テンプレートファイル名
        context: テンプレート変数の辞書
        content_type: Content-Typeヘッダー
        code: HTTPステータスコード
        
    Returns:
        レンダリングされたHTMLレスポンス
    """
    import jinja2
    
    # Jinja2環境の設定
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(master.settings.TEMPLATE_DIR),
    )
    
    # テンプレート内で使用可能なグローバル関数を登録
    _register_template_globals(env)
    
    # テンプレートの取得とレンダリング
    template = env.get_template(template_file)
    
    # masterオブジェクトをコンテキストに追加（既に存在しない場合）
    if "master" not in context:
        context["master"] = master
    
    # HTMLをレンダリングしてレスポンスを生成
    html_content = template.render(**context)
    return gen_response(master, html_content, content_type, code)

def json_response(master, data, code=200):
    """
    JSONレスポンスを生成
    
    Args:
        master: Masterインスタンス
        data: JSONシリアライズ可能なデータ
        code: HTTPステータスコード
        
    Returns:
        JSONレスポンス
    """
    import json
    json_string = json.dumps(data, ensure_ascii=False)
    return gen_response(master, json_string, "application/json; charset=UTF-8", code)

def error_render(master, error_message=None):
    """
    エラーページを生成
    
    Args:
        master: Masterインスタンス
        error_message: エラーメッセージ（デバッグモード時のみ表示）
        
    Returns:
        エラーページのHTMLレスポンス
    """
    if master.settings.DEBUG:
        # デバッグモード: 詳細なエラー情報を表示
        html_content = _generate_debug_error_html(error_message, master.event, master.context)
        return gen_response(master, html_content, "text/html; charset=UTF-8", 200)
    else:
        # 本番モード: 簡潔なエラーメッセージ
        html_content = _generate_production_error_html()
        return gen_response(master, html_content, "text/html; charset=UTF-8", 500)

# プライベート関数（内部使用）


def _normalize_path(path):
    """パスの先頭スラッシュを除去して正規化"""
    if path.startswith("/"):
        return path[1:]
    return path

def _build_full_path(*path_parts):
    """複数のパス要素から完全なURLパスを構築"""
    # 空の要素を除去してパスを結合
    clean_parts = [part for part in path_parts if part]
    if not clean_parts:
        return "/"
    
    return "/" + os.path.join(*clean_parts)

def _register_template_globals(jinja_env):
    """Jinja2テンプレート環境にグローバル関数を登録"""
    jinja_env.globals['static'] = static
    jinja_env.globals['reverse'] = reverse
    
    # 認証関連の関数はauthenticate.pyから直接インポート
    from wambda.authenticate import get_login_url, get_signup_url, get_verify_url, get_logout_url
    jinja_env.globals['get_login_url'] = get_login_url
    jinja_env.globals['get_signup_url'] = get_signup_url
    jinja_env.globals['get_verify_url'] = get_verify_url
    jinja_env.globals['get_logout_url'] = get_logout_url

def _generate_debug_error_html(error_message, event, context):
    """デバッグモード用の詳細エラーHTML"""
    import html
    import json

    # HTMLエスケープ処理
    safe_error_message = html.escape(str(error_message)) if error_message else "No error message"
    safe_event = html.escape(json.dumps(event, indent=2, ensure_ascii=False)) if event else "No event data"
    safe_context = html.escape(str(context)) if context else "No context data"

    return f"""\
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WAMBDA Debug Error</title>
    <style>
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }}

      body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
        color: #333;
      }}

      .container {{
        max-width: 1200px;
        margin: 0 auto;
        background: white;
        border-radius: 12px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        overflow: hidden;
      }}

      .header {{
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        padding: 30px;
        text-align: center;
      }}

      .wambda-brand {{
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 10px;
        letter-spacing: 2px;
      }}

      .error-title {{
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 8px;
      }}

      .debug-badge {{
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
      }}

      .content {{
        padding: 40px;
      }}

      .section {{
        margin-bottom: 40px;
      }}

      .section:last-child {{
        margin-bottom: 0;
      }}

      .section-title {{
        font-size: 18px;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
      }}

      .code-block {{
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 13px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
        color: #2d3748;
        max-height: 300px;
        overflow-y: auto;
      }}

      .error-message {{
        background: #fed7d7;
        border: 1px solid #feb2b2;
        color: #822727;
      }}

      .footer {{
        background: #f7fafc;
        padding: 20px 40px;
        text-align: center;
        color: #718096;
        font-size: 12px;
        border-top: 1px solid #e2e8f0;
      }}

      .refresh-hint {{
        margin-top: 20px;
        padding: 15px;
        background: #ebf8ff;
        border: 1px solid #90cdf4;
        border-radius: 8px;
        color: #2c5282;
        font-size: 14px;
      }}

      @media (max-width: 768px) {{
        .container {{
          margin: 10px;
          border-radius: 8px;
        }}

        .header {{
          padding: 20px;
        }}

        .content {{
          padding: 20px;
        }}

        .footer {{
          padding: 15px 20px;
        }}

        .error-title {{
          font-size: 24px;
        }}

        .wambda-brand {{
          font-size: 20px;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <div class="wambda-brand">WAMBDA FRAMEWORK</div>
        <h1 class="error-title">Debug Error</h1>
        <span class="debug-badge">Development Mode</span>
      </div>

      <div class="content">
        <div class="section">
          <h2 class="section-title">Error Message</h2>
          <pre class="code-block error-message">{safe_error_message}</pre>
        </div>

        <div class="section">
          <h2 class="section-title">Event Data</h2>
          <pre class="code-block">{safe_event}</pre>
        </div>

        <div class="section">
          <h2 class="section-title">Context Information</h2>
          <pre class="code-block">{safe_context}</pre>
        </div>

        <div class="refresh-hint">
          <strong>💡 Debug Tip:</strong> Fix the error in your code and refresh the page to see the changes.
        </div>
      </div>

      <div class="footer">
        Powered by WAMBDA Framework • Debug mode is enabled
      </div>
    </div>
  </body>
</html>
    """

def _generate_production_error_html():
    """本番モード用の簡潔なエラーHTML"""
    return """\
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error</title>
    <style>
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        background: #f8fafc;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        color: #2d3748;
      }

      .container {
        max-width: 500px;
        width: 100%;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        padding: 40px 30px;
      }

      .error-icon {
        font-size: 48px;
        margin-bottom: 20px;
        color: #e53e3e;
      }

      h1 {
        font-size: 24px;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 12px;
      }

      p {
        font-size: 16px;
        line-height: 1.6;
        color: #4a5568;
        margin-bottom: 8px;
      }

      .refresh-button {
        margin-top: 24px;
        padding: 12px 24px;
        background: #4299e1;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
      }

      .refresh-button:hover {
        background: #3182ce;
      }

      @media (max-width: 480px) {
        .container {
          padding: 30px 20px;
        }

        h1 {
          font-size: 20px;
        }

        p {
          font-size: 14px;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="error-icon">⚠️</div>
      <h1>エラーが発生しました</h1>
      <p>申し訳ございませんが、処理中にエラーが発生しました。</p>
      <p>しばらく時間をおいてから再度お試しください。</p>
      <p>問題が解決しない場合は、管理者にお問い合わせください。</p>
      <button class="refresh-button" onclick="window.location.reload()">ページを再読み込み</button>
    </div>
  </body>
</html>
    """
