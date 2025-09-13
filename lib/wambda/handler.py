import urllib.parse
import importlib
import os
import json
import logging

class Master:
  """
  リクエスト処理の中心となるクラス。
  
  AWS Lambda関数のハンドラーから呼び出され、リクエストの処理を行います。
  """
  def __init__(self, event, context):
    """
    Args:
        event: AWS Lambdaイベントオブジェクト
        context: AWS Lambdaコンテキストオブジェクト
    """
    from wambda.urls import Router
    self.event = event
    self.context = context
    self.settings = importlib.import_module('project.settings') 
    self.router = Router()
    self.request = Request(event, context)
    self._set_logger()
    self._set_local()
    
  def _set_local(self):
    """ローカル開発環境かどうかを判定します。"""
    AWS_SAM_LOCAL = os.getenv("AWS_SAM_LOCAL")
    if AWS_SAM_LOCAL is None:
      # 環境変数がない場合はadmin.jsonの存在で判断
      if os.path.isfile(os.path.join(self.settings.BASE_DIR, '../admin.json')):
        self.local = True
      else:
        self.local = False
    else:
      if AWS_SAM_LOCAL == "true":
        self.local = True
      elif AWS_SAM_LOCAL == "false":
        self.local = False
      else:
        raise ValueError("AWS_SAM_LOCALは'true'または'false'である必要があります")
        
  def _set_logger(self):
    """ロガーを設定します。"""
    self.logger = logging.getLogger()
    
    # settings.pyからログレベルを取得（未定義の場合はINFOをデフォルト）
    log_level_str = getattr(self.settings, 'LOG_LEVEL', 'INFO').upper()
    
    # ログレベル文字列を対応する定数に変換
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    log_level = log_level_map.get(log_level_str, logging.INFO)
    self.logger.setLevel(log_level)

  def _set_use_mock(self):
    """モックを使用するかどうかを判定します。"""
    USE_MOCK = os.getenv("USE_MOCK")
    if USE_MOCK is None:
      self.use_mock = False
    elif USE_MOCK.lower() == "true":
      self.use_mock = True
    elif USE_MOCK.lower() == "false":
      self.use_mock = False
    else:
      raise ValueError("USE_MOCKは'true'または'false'である必要があります")

  def get_view(self, path):
    """
    パスからビュー関数を取得し、NotMatchedエラーをハンドル
    
    Args:
        path: リクエストパス
        
    Returns:
        (view, kwargs)のタプル
    """
    from wambda.urls import NotMatched
    try:
      return self.router.path2view(path)
    except NotMatched:
      # settings.pyでカスタム404ビューが定義されているかチェック
      if hasattr(self.settings, 'URL_NOT_MATCHED_VIEW'):
        return self.settings.URL_NOT_MATCHED_VIEW, {}
      else:
        # デフォルトビューを使用
        from wambda.views import url_not_matched_view
        return url_not_matched_view, {}

class MultiDict:
    """WTFormsと互換性のあるシンプルなMultiDictクラス"""
    def __init__(self, data=None):
        self._data = {}
        if data:
            for key, value_list in data.items():
                self._data[key] = value_list
    
    def getlist(self, key):
        """指定されたキーの値をリストで取得"""
        return self._data.get(key, [])
    
    def get(self, key, default=None):
        """指定されたキーの最初の値を取得"""
        values = self.getlist(key)
        return values[0] if values else default
    
    def __getitem__(self, key):
        """指定されたキーの最初の値を取得"""
        values = self.getlist(key)
        if not values:
            raise KeyError(key)
        return values[0]
    
    def __contains__(self, key):
        """キーが存在するかチェック"""
        return key in self._data
    
    def keys(self):
        """すべてのキーを取得"""
        return self._data.keys()
    
    def items(self):
        """すべてのアイテムを取得（最初の値のみ）"""
        return [(key, self.get(key)) for key in self._data.keys()]

class Request:
  """
  HTTPリクエストを表すクラス。
  
  リクエストメソッド、パス、ボディ、認証情報などを保持します。
  """
  def __init__(self, event, context):
    """
    Args:
        event: AWS Lambdaイベントオブジェクト
        context: AWS Lambdaコンテキストオブジェクト
    """
    self.method = event['requestContext']["httpMethod"]
    self.path = event['path']
    
    # 認証関連の属性
    self.auth = False
    self.username = None
    self.set_cookie = False
    self.clean_cookie = False
    self.access_token = None
    self.id_token = None
    self.refresh_token = None
    self.decode_token = None
    self.body = event.get('body', None)
    
  def set_token(self, access_token, id_token, refresh_token):
    """認証トークンを設定します。"""
    self.access_token = access_token
    self.id_token = id_token
    self.refresh_token = refresh_token
    
  def get_form_data(self):
    """リクエストボディを解析してフォームデータを取得します。"""
    if self.method == 'POST':
      parsed_body = urllib.parse.parse_qs(self.body)
      if parsed_body:
        # WTFormsと互換性のあるMultiDictを作成
        return MultiDict(parsed_body)
      else:
        return MultiDict()
    else:
      raise ValueError("リクエストメソッドがPOSTではありません")



