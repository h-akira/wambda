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
            from hads.authenticate import get_login_url
            return {
                'statusCode': 302,
                'headers': {
                    'Location': get_login_url(master)
                }
            }
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

def redirect(master, url_name, query_params=None, **kwargs):
    """
    指定されたURL名前にリダイレクトするレスポンスを生成
    
    Args:
        master: Masterインスタンス
        url_name: リダイレクト先のURL名前
        query_params: クエリパラメータの辞書 (例: {'key': 'value'})
        **kwargs: URLパラメータ
        
    Returns:
        302リダイレクトレスポンス
    """
    import urllib.parse
    
    # ベースURLを生成
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
    
    # JWT検証失敗時の自動クッキークリア
    if getattr(master.request, 'clear_auth_cookies', False):
        if "Set-Cookie" not in response["headers"]:
            response["headers"]["Set-Cookie"] = []
        elif isinstance(response["headers"]["Set-Cookie"], str):
            response["headers"]["Set-Cookie"] = [response["headers"]["Set-Cookie"]]
        
        # 認証関連のクッキーをクリア
        auth_cookies = [
            "access_token=; Max-Age=0; Path=/; HttpOnly; Secure",
            "id_token=; Max-Age=0; Path=/; HttpOnly; Secure", 
            "refresh_token=; Max-Age=0; Path=/; HttpOnly; Secure"
        ]
        response["headers"]["Set-Cookie"].extend(auth_cookies)
    
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
    from hads.authenticate import get_login_url, get_signup_url, get_verify_url, get_logout_url
    jinja_env.globals['get_login_url'] = get_login_url
    jinja_env.globals['get_signup_url'] = get_signup_url
    jinja_env.globals['get_verify_url'] = get_verify_url
    jinja_env.globals['get_logout_url'] = get_logout_url

def _generate_debug_error_html(error_message, event, context):
    """デバッグモード用の詳細エラーHTML"""
    return f"""
    <h1>Error</h1>
    <h3>Error Message</h3>
    <pre>{error_message}</pre>
    <h3>Event</h3>
    <pre>{event}</pre>
    <h3>Context</h3>
    <pre>{context}</pre>
    """

def _generate_production_error_html():
    """本番モード用の簡潔なエラーHTML"""
    return """
    <h1>Error</h1>
    <p>Sorry, an error occurred.</p>
    <p>Please try again later, or contact the administrator.</p>
    """
