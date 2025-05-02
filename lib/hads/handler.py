import urllib.parse
import importlib
import os
import json

class Master:
  def __init__(self, event, context):
    from hads.urls import Router
    self.event = event
    self.context = context
    self.settings = importlib.import_module('project.settings') 
    self.router = Router()
    self.request = Request(event, context)
    self._set_logger()
    self._set_local()
  def _set_local(self):
    AWS_SAM_LOCAL = os.getenv("AWS_SAM_LOCAL")
    if AWS_SAM_LOCAL is None:
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
        raise ValueError("AWS_SAM_LOCAL must be 'true' or 'false'.")
  def _set_logger(self):
    import logging
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.INFO)

class Request:
  def __init__(self, event, context):
    self.method = event['requestContext']["httpMethod"]
    self.path = event['path']
    self._set_parsed_body(event)
    self.auth = False
    self.username = None
    self.set_cookie = False
    self.clean_cookie = False
    self.access_token = None
    self.id_token = None
    self.refresh_token = None
  def set_token(self, access_token, id_token, refresh_token):
    self.access_token = access_token
    self.id_token = id_token
    self.refresh_token = refresh_token
  def _set_parsed_body(self, event):
    if event["requestContext"]["httpMethod"] == "POST":
      self.body = urllib.parse.parse_qs(event['body'])
      for key, value in self.body.items():
        if len(value) == 1:
          self.body[key] = value[0]
    else:
      self.body = None

