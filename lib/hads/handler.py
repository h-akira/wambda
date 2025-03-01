from datetime import datetime
import urllib.parse
import importlib
import os

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
    if os.path.isfile(os.path.join(self.settings.BASE_DIR, '../../admin.json')):
      self.local = True
    else:
      self.local = False
  def _set_logger(self):
    import logging
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.INFO)

class Request:
  def __init__(self, event, context):
    self.method = event['requestContext']["httpMethod"]
    self.path = event['path']
    self._set_parsed_body(self.method)
    # self._set_auth()  # self.authとself.username
  def _set_parsed_body(self, method):
    if method == "POST":
      self.body = urllib.parse.parse_qs(self.event['body'])
      for key, value in self.body.items():
        if len(value) == 1:
          self.body[key] = value[0]
    else:
      self.body = None

