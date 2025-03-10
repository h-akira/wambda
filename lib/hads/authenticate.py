import os

class Cognito:
  def __init__(self, domain, user_pool_id: str, client_id: str, client_secret: str, region: str):
    self.domain = domain
    self.user_pool_id = user_pool_id
    self.client_id = client_id
    self.client_secret = client_secret
    self.region = region
  def _authCode2token(self, code, redirect_uri):
    import requests
    import boto3
    import base64
    url = f"{self.domain}/oauth2/token"
    auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
    headers = {
      "Content-Type": "application/x-www-form-urlencoded",
      "Authorization": f"Basic {auth_header}"
    }
    data = {
      'grant_type': 'authorization_code',
      'client_id': self.client_id,
      'code': code,
      'redirect_uri': redirect_uri,
      'client_secret': self.client_secret
    }
    response = requests.post(url, data=data)
    return response.json()
  def _get_decode_token(self, id_token):
    from jwt import decode, PyJWKClient
    jwk_client = PyJWKClient(
      f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json'
    )
    signing_key = jwk_client.get_signing_key_from_jwt(id_token)
    return decode(
      id_token, 
      signing_key.key, 
      algorithms=['RS256'], 
      audience=self.client_id,
      issuer=f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}'
    )
  def set_auth_by_code(self, master):
    if master.request.auth:
      return True
    try:
      code = master.event['queryStringParameters']['code']
    except:
      return False
    response = self._authCode2token(code, master.settings.AUTH_PAGE.get_redirect_uri(master))
    if "id_token" not in response.keys() or "access_token" not in response.keys() or "refresh_token" not in response.keys():
      master.logger.warning("code is not found")
      return False
    master.request.set_token(
      access_token=response['access_token'], 
      id_token=response['id_token'], 
      refresh_token=response['refresh_token']
    )
    master.request.auth = True
    master.request.set_cookie = True
    master.request.decode_token = self._get_decode_token(response['id_token'])
    master.request.username = master.request.decode_token.get('cognito:username', None)
    master.request.auth = True
    return True
  def set_auth_by_cookie(self, master):
    if master.request.auth:
      return True
    cookies = master.event['headers'].get('Cookie', '')
    if not cookies:
      return False
    id_token = None
    refresh_token = None
    access_token = None
    for cookie in cookies.split(';'):
      name, value = cookie.strip().split('=')
      if name == 'id_token':
        id_token = value
      elif name == 'refresh_token':
        refresh_token = value
      elif name == 'access_token':
        access_token = value
      if id_token is not None and refresh_token is not None and access_token is not None:
        break
    else:
      return False
    from jwt import ExpiredSignatureError, InvalidTokenError
    try:
      master.request.decode_token = self._get_decode_token(id_token)
      master.request.username = master.request.decode_token.get('cognito:username', None)
      master.request.set_token(
        access_token=access_token,
        id_token=id_token,
        refresh_token=refresh_token
      )
      master.request.auth = True
      master.request.username = master.request.decode_token.get('cognito:username', None)
      return True
    except ExpiredSignatureError:
      import boto3
      client = boto3.client('cognito-idp')
      try:
        response = client.initiate_auth(
          ClientId=self.client_id,
          AuthFlow='REFRESH_TOKEN_AUTH',
          AuthParameters={
            'REFRESH_TOKEN': refresh_token
          }
        )
        new_id_token = response['AuthenticationResult']['IdToken']
        new_access_token = response['AuthenticationResult']['AccessToken']
        master.request.set_cookie = True
        master.request.set_token(
          access_token=new_access_token,
          id_token=new_id_token,
          refresh_token=refresh_token
        )
        master.request.decode_token = self._get_decode_token(new_id_token)
        master.request.username = master.request.decode_token.get('cognito:username', None)
        master.request.auth = True
      except Exception as e:
        master.logger.exception(e)
        return False
    except InvalidTokenError as e:
      master.logger.exception(e)
      return False
  def add_set_cookie_to_header(self, master, response):
    from http.cookies import SimpleCookie
    cookie = SimpleCookie()
    if master.request.set_cookie:
      cookies = []
      if master.request.id_token is not None:
        cookie['id_token'] = master.request.id_token
        cookie['id_token']['httponly'] = True
        cookie['id_token']['secure'] = True
        cookie['id_token']['path'] = '/'
        cookies.append(cookie['id_token'].OutputString())
      if master.request.access_token is not None:
        cookie['access_token'] = master.request.access_token
        cookie['access_token']['httponly'] = True
        cookie['access_token']['secure'] = True
        cookie['access_token']['path'] = '/'
        cookies.append(cookie['access_token'].OutputString())
      if master.request.refresh_token is not None:
        cookie['refresh_token'] = master.request.refresh_token
        cookie['refresh_token']['httponly'] = True
        cookie['refresh_token']['secure'] = True
        cookie['refresh_token']['path'] = '/'
        cookies.append(cookie['refresh_token'].OutputString())
    elif master.request.clean_cookie:
      from datetime import datetime, timedelta, timezone
      cookie['id_token'] = ''
      cookie['id_token']['expires'] = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")
      cookie['id_token']['path'] = '/'
      cookie['access_token'] = ''
      cookie['access_token']['expires'] = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")
      cookie['access_token']['path'] = '/'
      cookie['refresh_token'] = ''
      cookie['refresh_token']['expires'] = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")
      cookie['refresh_token']['path'] = '/'
      cookies = [cookie['id_token'].OutputString(), cookie['access_token'].OutputString(), cookie['refresh_token'].OutputString()]
    else:
      return response
    if "multiValueHeaders" in response.keys():
      response["multiValueHeaders"]["Set-Cookie"] = cookies
    else:
      response["multiValueHeaders"] = {"Set-Cookie": cookies}
    return response
  def sign_out(self, master):
    if not master.request.auth:
      raise Exception("not auth")
    import boto3
    client = boto3.client('cognito-idp')
    response = client.global_sign_out(
      AccessToken = master.request.access_token
    )
    if master.request.set_cookie:
      master.request.set_cookie = False
    master.request.clean_cookie = True


class ManagedAuthPage:
  def __init__(self, scope, login_redirect_uri: str, local_login_redirect_uri: str=None):
    self.scope = scope
    self.login_redirect_uri = login_redirect_uri
    self.local_login_redirect_uri = local_login_redirect_uri
  def get_redirect_uri(self, master):
    if master.local:
      if self.local_login_redirect_uri is None:
        return self.login_redirect_uri
      else:
        return self.local_login_redirect_uri
    else:
      return self.login_redirect_uri
  def get_login_url(self, master):
    return self._get_url(master, '/login')
  def get_signup_url(self, master):
    return self._get_url(master, '/signup')
  def _get_url(self, master, path):
    params = {
      'client_id': master.settings.COGNITO.client_id,
      'response_type': 'code',
      'scope': self.scope,
    }
    if master.local:
      if self.local_login_redirect_uri is None:
        master.logger.warning("local_login_redirect_uri is not set")
        params['redirect_uri'] = self.login_redirect_uri
      else:
        params['redirect_uri'] = self.local_login_redirect_uri
    else:
      params['redirect_uri'] = self.login_redirect_uri
    from urllib.parse import urlencode
    query_string = urlencode(params)
    return f"{master.settings.COGNITO.domain}{path}?{query_string}"

