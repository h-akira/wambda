import importlib
import os
from hads.handler import Master

class NotMatched(Exception):
  pass
class KwargsRemain(Exception):
  pass

class Path:
  def __init__(self, path_pattern: str, view, name=None):
    if path_pattern == "":
      self.segments = []
    elif path_pattern[0] == "/":
      raise Exception
    else:
      self.segments = path_pattern.split('/')
    self.path_pattern = path_pattern
    self.view = view
    self.name = name

class Router:
  def __init__(self, root="", urls_str="project.urls", name=None):
    urls = importlib.import_module(urls_str)
    self.urlpatterns = urls.urlpatterns
    self.root = root
    self.name = name
    if self.root == "":
      self.segments = []
    elif self.root[0] == "/":
      raise Exception("root should not start with /")
    else:
      self.segments = self.root.split('/')
    try:
      self.app_name = urls.app_name
    except AttributeError:
      self.app_name = None
  def name2path(self, name: str, kwargs={}, root=""):
    name_list = name.split(":")
    for urlpattern in self.urlpatterns:
      if urlpattern.__class__ is Path:
        if len(name_list) != 1:
          continue
        if urlpattern.name == name_list[0]:
          formatted, kwargs = _step_format(urlpattern.path_pattern, kwargs)
          if kwargs:
            raise KwargsRemain
          else:
            return os.path.join(root, formatted)
      elif urlpattern.__class__ is self.__class__:
        if len(name_list) == 1:
          raise Exception("name_list must have more than 1 element")
        if urlpattern.name == name_list[0]:
          root, kwargs = _step_format(urlpattern.root, kwargs)
          return urlpattern.name2path(":".join(name_list[1:]), kwargs, root=os.path.join(root, urlpattern.root))
        if path:
          return self.root + path
    raise NotMatched
  def path2view(self, abs_path=None, segments=None):
    if abs_path is not None and segments is not None:
      raise Exception("abs_path and segments should not be given at the same time")
    if abs_path is None and segments is None:
      raise Exception("abs_path or segments should be given")
    if abs_path is not None:
      if len(abs_path)>1 and abs_path[-1] == "/":
        abs_path = abs_path[:-1]
      segments = self._abs_path2segments(abs_path)
    routers = []
    for urlpattern in self.urlpatterns:
      if urlpattern.__class__ is Path:
        flag, kwargs = self._matching_chercker(segments, urlpattern.segments, mode="path")
        if flag:
          return urlpattern.view, kwargs
      elif urlpattern.__class__ is self.__class__:
        routers.append(urlpattern)
      else:
        raise Exception("urlpatten should be Path or Router")
    for router in routers:
      remaining_segments, kwargs = self._matching_chercker(segments, router.segments, mode="router", kwargs=kwargs)
      print("-----------------")
      print(remaining_segments)
      print("-----------------")
      print(kwargs)
      print("-----------------")
      if remaining_segments:
        return router.path2view(segments=remaining_segments)
    raise NotMatched
  def _abs_path2segments(self, abs_path):
    if abs_path:
      if abs_path == "/":
        return []
      else:
        if abs_path[0] == "/":
          return abs_path[1:].split('/')
        else:
          raise Exception("abs_path should start with /")
    else:
      raise Exception("abs_path should not be empty")
  def _matching_chercker(self, segments, pattern_segments, mode, kwargs={}):
    _kwargs = kwargs.copy()
    if mode not in ["path", "router"]:
      raise ValueError
    if len(segments) < len(pattern_segments):
      return False, kwargs
    for i,p in enumerate(pattern_segments):
      if p[0] == "{" and p[-1] == "}":
        _kwargs[p[1:-1]] = segments[i]
        continue
      else:
        if segments[i] != p:
          return False, kwargs
    else:
      if mode == "path":
        if len(segments) == len(pattern_segments):
          return True, _kwargs
        else:
          return False, kwargs
      else:
        if len(segments) == len(pattern_segments):
          return False, kwargs
        else:
          return segments[i+1:], _kwargs

def _step_format(text: str, kwargs: dict):
  exec_kwargs = {}
  return_kwargs = {}
  for k, v in kwargs.items():
    if "{"+k+"}" in text:
      exec_kwargs[k] = v
    else:
      return_kwargs[k] = v
  return text.format(**exec_kwargs), return_kwargs

