import os
import logging
import hmac
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
import boto3

class MaintenanceOptionError(Exception):
    """メンテナンス時に発生するエラー"""
    pass

# Lambdaコンテナレベルのキャッシュ
_cognito_settings_cache = None

def get_cognito_settings(master):
    """
    Cognito設定をSSMから取得（キャッシュ付き）
    
    Args:
        master: Masterインスタンス
        
    Returns:
        dict: Cognito設定値の辞書
    """
    global _cognito_settings_cache
    
    if _cognito_settings_cache is not None:
        return _cognito_settings_cache
    
    # SSMから取得（モック環境ではmock/ssm.pyが設定したデータを取得）
    ssm = boto3.client('ssm', region_name=master.settings.REGION)
    ssm_params = master.settings.COGNITO_SSM_PARAMS
    
    _cognito_settings_cache = {}
    for key, param_name in ssm_params.items():
        try:
            value = ssm.get_parameter(Name=param_name, WithDecryption=True)["Parameter"]["Value"]
            _cognito_settings_cache[key] = value
        except Exception as e:
            logging.error(f"Failed to get SSM parameter {param_name}: {e}")
            raise
    
    return _cognito_settings_cache


def login(master, username, password):
    """
    ログイン
    
    Args:
        master: Masterインスタンス
        username: ユーザー名  
        password: パスワード
        
    Returns:
        bool: ログイン成功の場合True
        
    Raises:
        MaintenanceOptionError: DENY_LOGINが有効な場合
    """
    # メンテナンス時のログイン拒否チェック
    if getattr(master.settings, 'DENY_LOGIN', False):
        raise MaintenanceOptionError()
    
    # NO_AUTHモードの場合、簡易ログイン
    if getattr(master.settings, 'NO_AUTH', False):
        return no_auth_login(master, username)
    
    import boto3
    from botocore.exceptions import ClientError
    
    client = boto3.client('cognito-idp', region_name=master.settings.REGION)
    
    try:
        # SECRET_HASHが必要な場合は計算
        auth_params = {
            'USERNAME': username,
            'PASSWORD': password
        }
        
        # Cognito設定を取得
        cognito_settings = get_cognito_settings(master)
        
        # CLIENT_SECRETが設定されている場合はSECRET_HASHを追加
        if cognito_settings.get('CLIENT_SECRET'):
            auth_params['SECRET_HASH'] = _calculate_secret_hash(master, username)
        
        response = client.admin_initiate_auth(
            UserPoolId=cognito_settings['USER_POOL_ID'],
            ClientId=cognito_settings['CLIENT_ID'],
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters=auth_params
        )
        
        # トークンを設定
        master.request.set_token(
            access_token=response['AuthenticationResult']['AccessToken'],
            id_token=response['AuthenticationResult']['IdToken'],
            refresh_token=response['AuthenticationResult']['RefreshToken']
        )
        
        # IDトークンをデコードしてユーザー情報を取得
        master.request.decode_token = _decode_id_token(master, response['AuthenticationResult']['IdToken'])
        master.request.username = master.request.decode_token.get('cognito:username')
        master.request.auth = True
        master.request.set_cookie = True
        
        return True
        
    except ClientError as e:
        master.logger.exception(f"ログインエラー: {e}")
        return False

def signup(master, username, email, password):
    """
    サインアップ
    
    Args:
        master: Masterインスタンス
        username: ユーザー名
        email: メールアドレス
        password: パスワード
        
    Returns:
        bool: サインアップ成功の場合True
        
    Raises:
        MaintenanceOptionError: DENY_SIGNUPが有効な場合
    """
    # メンテナンス時のサインアップ拒否チェック
    if getattr(master.settings, 'DENY_SIGNUP', False):
        raise MaintenanceOptionError()
    
    # NO_AUTHモードの場合、簡易サインアップ（実際にはログインと同じ）
    if getattr(master.settings, 'NO_AUTH', False):
        return no_auth_login(master, username)
    
    import boto3
    from botocore.exceptions import ClientError
    
    client = boto3.client('cognito-idp', region_name=master.settings.REGION)
    
    try:
        # ユーザー属性
        user_attributes = [
            {
                'Name': 'email',
                'Value': email
            }
        ]
        
        # SECRET_HASHが必要な場合は計算
        signup_params = {
            'Username': username,
            'Password': password,
            'UserAttributes': user_attributes
        }
        
        # Cognito設定を取得
        cognito_settings = get_cognito_settings(master)
        
        # CLIENT_SECRETが設定されている場合はSECRET_HASHを追加
        if cognito_settings.get('CLIENT_SECRET'):
            signup_params['SecretHash'] = _calculate_secret_hash(master, username)
        
        response = client.sign_up(
            ClientId=cognito_settings['CLIENT_ID'],
            **signup_params
        )
        
        master.logger.info(f"サインアップ成功: UserSub={response.get('UserSub')}")
        return True
        
    except ClientError as e:
        master.logger.exception(f"サインアップエラー: {e}")
        return False

def verify(master, username, code):
    """
    メールアドレス確認
    
    Args:
        master: Masterインスタンス
        username: ユーザー名
        code: 確認コード
        
    Returns:
        bool: 確認成功の場合True
    """
    # NO_AUTHモードの場合、常に成功
    if getattr(master.settings, 'NO_AUTH', False):
        master.logger.info(f"NO_AUTHモード: ユーザー {username} の確認をスキップ")
        return True
    
    import boto3
    from botocore.exceptions import ClientError
    
    client = boto3.client('cognito-idp', region_name=master.settings.REGION)
    
    try:
        # 確認パラメータ
        confirm_params = {
            'Username': username,
            'ConfirmationCode': code
        }
        
        # Cognito設定を取得
        cognito_settings = get_cognito_settings(master)
        
        # CLIENT_SECRETが設定されている場合はSECRET_HASHを追加
        if cognito_settings.get('CLIENT_SECRET'):
            confirm_params['SecretHash'] = _calculate_secret_hash(master, username)
        
        response = client.confirm_sign_up(
            ClientId=cognito_settings['CLIENT_ID'],
            **confirm_params
        )
        
        master.logger.info(f"メールアドレス確認成功: ユーザー {username}")
        return True
        
    except ClientError as e:
        master.logger.exception(f"メールアドレス確認エラー: {e}")
        return False









def set_auth_by_cookie(master):
    """
    Cookieからトークンを取得して認証情報を設定・更新
    
    Args:
        master: Masterインスタンス
        
    Returns:
        bool: 認証成功の場合True
    """
    if master.request.auth:
        return True
    
    # NO_AUTHモードの場合、簡易認証を実行
    if getattr(master.settings, 'NO_AUTH', False):
        return _set_no_auth_mode(master)
    
    # Cookieからトークンを抽出
    tokens = _extract_tokens_from_cookie(master)
    if not tokens:
        return False
    
    id_token, refresh_token, access_token = tokens
    
    try:
        from jwt import ExpiredSignatureError, InvalidTokenError
        
        # IDトークンを検証・デコード
        master.request.decode_token = _decode_id_token(master, id_token)
        
        # JWT検証に失敗した場合（Noneが返される）
        if master.request.decode_token is None:
            # クッキーをクリアして再認証を促す
            master.request.clean_cookie = True
            return False
            
        master.request.username = master.request.decode_token.get('cognito:username')
        
        if master.request.username is None:
            # ユーザー名が取得できない場合もクッキーをクリア
            master.request.clean_cookie = True
            return False
        
        # トークンを設定
        master.request.set_token(
            access_token=access_token,
            id_token=id_token,
            refresh_token=refresh_token
        )
        master.request.auth = True
        return True
        
    except ExpiredSignatureError:
        # トークンが期限切れの場合、リフレッシュトークンで更新
        master.logger.info("JWTトークンの期限切れを検出、リフレッシュトークンで更新を試行")
        return _refresh_tokens(master, refresh_token, id_token)
        
    except InvalidTokenError as e:
        master.logger.exception(e)
        # 無効なトークンの場合もクッキーをクリア
        master.request.clean_cookie = True
        return False

def add_set_cookie_to_header(master, response):
    """
    レスポンスヘッダーにCookieを追加
    
    Args:
        master: Masterインスタンス
        response: レスポンス辞書
        
    Returns:
        dict: 更新されたレスポンス辞書
    """
    cookies = None
    
    if master.request.set_cookie:
        # NO_AUTHモードの場合、簡易Cookieを生成
        if getattr(master.settings, 'NO_AUTH', False):
            cookies = _generate_no_auth_cookies(master)
        else:
            cookies = _generate_auth_cookies(master)
    elif master.request.clean_cookie:
        # NO_AUTHモードの場合、簡易Cookie削除
        if getattr(master.settings, 'NO_AUTH', False):
            cookies = _generate_no_auth_clear_cookies()
        else:
            cookies = _generate_clear_cookies()
    
    if cookies is None:
        return response
    
    # レスポンスヘッダーにCookieを追加
    if "multiValueHeaders" in response:
        response["multiValueHeaders"]["Set-Cookie"] = cookies
    else:
        response["multiValueHeaders"] = {"Set-Cookie": cookies}
    
    return response

def sign_out(master):
    """
    ユーザーをサインアウト
    
    Args:
        master: Masterインスタンス
        
    Raises:
        Exception: 未認証の場合
    """
    if not master.request.auth:
        raise Exception("認証されていません")
    
    # NO_AUTHモードの場合、boto3を使わずにローカルでサインアウト
    if getattr(master.settings, 'NO_AUTH', False):
        _no_auth_sign_out(master)
    else:
        import boto3
        client = boto3.client('cognito-idp', region_name=master.settings.REGION)
        
        try:
            client.global_sign_out(AccessToken=master.request.access_token)
        except client.exceptions.NotAuthorizedException as e:
            master.logger.error("既にサインアウト済み")
            master.logger.exception(e)
    
    # Cookie削除フラグを設定
    if master.request.set_cookie:
        master.request.set_cookie = False
    master.request.clean_cookie = True

def get_login_url(master):
    """
    ログインURLを生成
    
    Args:
        master: Masterインスタンス
        
    Returns:
        str: ログインURL
    """
    return _generate_url_from_setting(master, 'LOGIN_URL')

def get_signup_url(master):
    """
    サインアップURLを生成
    
    Args:
        master: Masterインスタンス
        
    Returns:
        str: サインアップURL
    """
    return _generate_url_from_setting(master, 'SIGNUP_URL')

def get_verify_url(master, username=None):
    """
    確認（検証）URLを生成
    
    Args:
        master: Masterインスタンス
        username: ユーザー名（オプション）
        
    Returns:
        str: 確認URL
    """
    url = _generate_url_from_setting(master, 'VERIFY_URL')
    if username:
        # クエリパラメータとしてusernameを追加
        separator = "&" if "?" in url else "?"
        url += f"{separator}username={username}"
    return url

def get_logout_url(master):
    """
    ログアウトURLを生成
    
    Args:
        master: Masterインスタンス
        
    Returns:
        str: ログアウトURL
    """
    return _generate_url_from_setting(master, 'LOGOUT_URL')

# プライベート関数（内部使用）

def _set_no_auth_mode(master):
    """
    NO_AUTHモードでの簡易認証処理
    
    Args:
        master: Masterインスタンス
        
    Returns:
        bool: 常にTrue（認証成功）
    """
    # Cookieから簡易認証情報を取得
    username = _extract_no_auth_username_from_cookie(master)
    
    # Cookieにユーザー名がない場合、認証しない
    if not username:
        return False
    
    # 簡易認証情報を設定（トークンはすべてユーザー名と同じ）
    master.request.set_token(
        access_token=username,
        id_token=username,
        refresh_token=username
    )
    
    # ユーザー情報を設定
    master.request.username = username
    master.request.auth = True
    master.request.decode_token = {
        'cognito:username': username,
        'email': f'{username}@example.com',
        'sub': f'test-{username}-uuid'
    }
    
    return True

def _extract_no_auth_username_from_cookie(master):
    """
    NO_AUTHモード用：Cookieからユーザー名を抽出
    
    Args:
        master: Masterインスタンス
        
    Returns:
        str: ユーザー名、なければNone
    """
    try:
        cookies = master.event['headers'].get('Cookie', '')
        if not cookies:
            return None
        
        # シンプルなCookie解析（NO_AUTHモード用）
        cookie_dict = {}
        for item in cookies.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookie_dict[key] = value
        
        # no_auth_userクッキーからユーザー名を取得
        return cookie_dict.get('no_auth_user')
        
    except (KeyError, TypeError, AttributeError):
        return None

def _generate_no_auth_cookies(master):
    """
    NO_AUTHモード用の簡易Cookieを生成
    
    Args:
        master: Masterインスタンス
        
    Returns:
        list: Cookieの文字列リスト
    """
    username = master.request.username
    
    # 有効期限を設定（7日後）
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # NO_AUTHモード用のシンプルなCookie
    cookie = f"no_auth_user={username}; Path=/; Expires={expires_str}; HttpOnly; SameSite=Lax"
    
    # ローカル環境でない場合はSecureフラグを追加
    if not master.local:
        cookie += "; Secure"
    
    return [cookie]

def no_auth_login(master, username):
    """
    NO_AUTHモード用の簡易ログイン
    
    Args:
        master: Masterインスタンス
        username: ログインするユーザー名
        
    Returns:
        bool: 常にTrue（ログイン成功）
    """
    if not getattr(master.settings, 'NO_AUTH', False):
        raise Exception("NO_AUTHモードが有効でありません")
    
    # 簡易認証情報を設定
    master.request.set_token(
        access_token=username,
        id_token=username,
        refresh_token=username
    )
    
    # ユーザー情報を設定
    master.request.username = username
    master.request.auth = True
    master.request.set_cookie = True
    master.request.decode_token = {
        'cognito:username': username,
        'email': f'{username}@example.com',
        'sub': f'test-{username}-uuid'
    }
    
    return True



def _decode_id_token(master, id_token, verify=True):
    """IDトークンをデコード"""
    if verify:
        from jwt import decode, PyJWKClient
        from jwt.exceptions import PyJWKClientError, InvalidTokenError, ExpiredSignatureError
        import logging
        import json
        import base64
        
        # 事前チェック: トークンのissuerを確認（完全な検証前の早期チェック）
        try:
            # JWTヘッダーとペイロードを取得（署名検証なし）
            header, payload, signature = id_token.split('.')
            decoded_payload = json.loads(base64.urlsafe_b64decode(payload + '=='))
            
            # 期待されるissuerを生成
            cognito_settings = get_cognito_settings(master)
            expected_issuer = f'https://cognito-idp.{master.settings.REGION}.amazonaws.com/{cognito_settings["USER_POOL_ID"]}'
            
            # issuerが一致しない場合は早期リターン
            if decoded_payload.get('iss') != expected_issuer:
                logging.warning(f"Token issuer mismatch. Expected: {expected_issuer}, Got: {decoded_payload.get('iss')}")
                master.request.clean_cookie = True
                return None
                
        except Exception as e:
            logging.warning(f"Failed to pre-validate token: {e}")
            return None
        
        cognito_settings = get_cognito_settings(master)
        jwk_client = PyJWKClient(
            f'https://cognito-idp.{master.settings.REGION}.amazonaws.com/{cognito_settings["USER_POOL_ID"]}/.well-known/jwks.json'
        )
        
        try:
            signing_key = jwk_client.get_signing_key_from_jwt(id_token)
            return decode(
                id_token,
                signing_key.key,
                algorithms=['RS256'],
                audience=cognito_settings['CLIENT_ID'],
                issuer=f'https://cognito-idp.{master.settings.REGION}.amazonaws.com/{cognito_settings["USER_POOL_ID"]}'
            )
        except PyJWKClientError as e:
            logging.warning(f"JWT signing key not found (likely from different User Pool): {e}")
            # Mark for cookie clearing to force re-authentication
            master.request.clean_cookie = True
            return None
        except ExpiredSignatureError as e:
            logging.warning(f"Invalid or expired JWT token: {e}")
            # ExpiredSignatureErrorは呼び出し元でリフレッシュ処理を行うため再発生
            raise e
        except InvalidTokenError as e:
            logging.warning(f"Invalid JWT token: {e}")
            master.request.clean_cookie = True
            return None
        except Exception as e:
            logging.error(f"Unexpected error during JWT verification: {e}")
            return None
    else:
        from jwt import decode
        return decode(id_token, options={"verify_signature": False})

def _calculate_secret_hash(master, username):
    """シークレットハッシュを計算"""
    if username is None:
        raise ValueError("ユーザー名がNoneです")
    
    cognito_settings = get_cognito_settings(master)
    message = username + cognito_settings['CLIENT_ID']
    dig = hmac.new(
        cognito_settings['CLIENT_SECRET'].encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    
    return base64.b64encode(dig).decode()

def _extract_tokens_from_cookie(master):
    """Cookieからトークンを抽出"""
    cookies = master.event['headers'].get('Cookie', '')
    if not cookies:
        return None
    
    id_token = None
    refresh_token = None
    access_token = None
    
    for cookie in cookies.split(';'):
        try:
            name, value = cookie.strip().split('=', 1)
            if name == 'id_token':
                id_token = value
            elif name == 'refresh_token':
                refresh_token = value
            elif name == 'access_token':
                access_token = value
        except ValueError:
            continue
    
    if all([id_token, refresh_token, access_token]):
        return id_token, refresh_token, access_token
    
    return None

def _refresh_tokens(master, refresh_token, old_id_token):
    """リフレッシュトークンで新しいトークンを取得"""
    master.logger.info("トークンリフレッシュを開始")
    import boto3
    
    client = boto3.client('cognito-idp', region_name=master.settings.REGION)
    
    try:
        # 古いIDトークンからユーザー名を取得（署名検証なし）
        old_token_data = _decode_id_token(master, old_id_token, verify=False)
        username = old_token_data.get('cognito:username')
        
        if not username:
            master.logger.error("リフレッシュ時にユーザー名を取得できませんでした")
            master.request.clean_cookie = True
            return False
        
        # シークレットハッシュを計算
        secret_hash = _calculate_secret_hash(master, username)
        
        # Cognito設定を取得
        cognito_settings = get_cognito_settings(master)
        
        # トークンをリフレッシュ
        response = client.initiate_auth(
            ClientId=cognito_settings['CLIENT_ID'],
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': secret_hash
            }
        )
        
        # 新しいトークンを設定
        new_id_token = response['AuthenticationResult']['IdToken']
        new_access_token = response['AuthenticationResult']['AccessToken']
        
        master.request.set_cookie = True
        master.request.set_token(
            access_token=new_access_token,
            id_token=new_id_token,
            refresh_token=refresh_token
        )
        
        # 新しいIDトークンをデコード
        master.request.decode_token = _decode_id_token(master, new_id_token)
        master.request.username = master.request.decode_token.get('cognito:username')
        
        if master.request.username is None:
            master.request.auth = False
            master.logger.error("リフレッシュ後にユーザー名がNullです")
            master.request.clean_cookie = True
            return False
        
        master.request.auth = True
        master.logger.info(f"トークンリフレッシュ成功: ユーザー {master.request.username}")
        return True
        
    except Exception as e:
        master.logger.error(f"トークンリフレッシュ失敗: {str(e)}")
        master.logger.exception(e)
        master.request.auth = False
        # Refresh tokenが期限切れなどでリフレッシュに失敗した場合もクッキーをクリア
        master.request.clean_cookie = True
        return False

def _validate_token_response(response):
    """トークンレスポンスの妥当性を検証"""
    required_keys = ['id_token', 'access_token', 'refresh_token']
    return all(key in response for key in required_keys)

def _generate_auth_cookies(master):
    """認証Cookieを生成"""
    cookie = SimpleCookie()
    cookies = []
    
    if master.request.id_token is not None:
        cookie['id_token'] = master.request.id_token
        cookie['id_token']['httponly'] = True
        cookie['id_token']['secure'] = not master.local
        cookie['id_token']['path'] = '/'
        cookies.append(cookie['id_token'].OutputString())
    
    if master.request.access_token is not None:
        cookie['access_token'] = master.request.access_token
        cookie['access_token']['httponly'] = True
        cookie['access_token']['secure'] = not master.local
        cookie['access_token']['path'] = '/'
        cookies.append(cookie['access_token'].OutputString())
    
    if master.request.refresh_token is not None:
        cookie['refresh_token'] = master.request.refresh_token
        cookie['refresh_token']['httponly'] = True
        cookie['refresh_token']['secure'] = not master.local
        cookie['refresh_token']['path'] = '/'
        cookies.append(cookie['refresh_token'].OutputString())
    
    return cookies

def _generate_clear_cookies():
    """Cookie削除用の期限切れCookieを生成"""
    cookie = SimpleCookie()
    expired_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")
    
    for token_name in ['id_token', 'access_token', 'refresh_token']:
        cookie[token_name] = ''
        cookie[token_name]['expires'] = expired_date
        cookie[token_name]['path'] = '/'
    
    return [
        cookie['id_token'].OutputString(),
        cookie['access_token'].OutputString(),
        cookie['refresh_token'].OutputString()
    ]

def _generate_no_auth_clear_cookies():
    """NO_AUTHモード用のCookie削除用の期限切れCookieを生成"""
    expired_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    return [f"no_auth_user=; Path=/; Expires={expired_date}; HttpOnly; SameSite=Lax"]

def _generate_url_from_setting(master, setting_name):
    """
    settings.pyの設定値からURLを生成
    
    Args:
        master: Masterインスタンス
        setting_name: 設定名 (LOGIN_URL, SIGNUP_URL, VERIFY_URL等)
        
    Returns:
        str: 生成されたURL
    """
    from hads.shortcuts import reverse
    
    # 設定値を取得
    url_setting = getattr(master.settings, setting_name, None)
    if not url_setting:
        raise ValueError(f"設定 '{setting_name}' が見つかりません")
    
    # URL生成
    if url_setting.startswith('/') or url_setting.startswith('http'):
        # 絶対パスまたは完全URLの場合はそのまま使用
        return url_setting
    else:
        # URL名前の場合は逆引きでパスを生成
        return reverse(master, url_setting)

def _no_auth_sign_out(master):
    """
    NO_AUTHモード用のサインアウト処理
    
    Args:
        master: Masterインスタンス
    """
    # 認証情報をクリア
    master.request.auth = False
    master.request.username = None
    master.request.decode_token = None
    master.request.access_token = None
    master.request.id_token = None
    master.request.refresh_token = None
    
    # # Cookie削除フラグを設定
    # master.request.clean_cookie = True



