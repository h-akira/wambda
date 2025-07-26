import importlib
import os
from hads.handler import Master

class NotMatched(Exception):
    """URLパターンが一致しなかった場合に発生する例外"""
    pass

class KwargsRemain(Exception):
    """URL生成時に使用されなかったキーワード引数がある場合に発生する例外"""
    pass

class Path:
    """URLパスパターンを表すクラス"""
    def __init__(self, path_pattern: str, view, name=None):
        """
        Args:
            path_pattern: URLパスパターン（例: 'users/{user_id}'）
            view: パスに対応するビュー関数
            name: パスの名前（リバースルックアップに使用）
        """
        if path_pattern.startswith("/"):
            raise ValueError("パスパターンは / で始まってはいけません")
        
        self.path_pattern = path_pattern
        self.view = view
        self.name = name
        self.segments = self._parse_segments(path_pattern)
    
    def _parse_segments(self, path_pattern):
        """パスパターンをセグメントに分割"""
        if path_pattern == "":
            return []
        return path_pattern.split('/')
    
    def matches(self, url_segments):
        """このパスがURL セグメントにマッチするかチェック"""
        if len(url_segments) != len(self.segments):
            return False, {}
        
        params = {}
        for pattern_seg, url_seg in zip(self.segments, url_segments):
            if self._is_parameter(pattern_seg):
                param_name = self._extract_parameter_name(pattern_seg)
                params[param_name] = url_seg
            elif pattern_seg != url_seg:
                return False, {}
        
        return True, params
    
    def _is_parameter(self, segment):
        """セグメントがパラメータかどうか判定"""
        return segment.startswith("{") and segment.endswith("}")
    
    def _extract_parameter_name(self, segment):
        """パラメータセグメントから名前を抽出"""
        return segment[1:-1]
    
    def generate_url(self, params):
        """パラメータからURLパスを生成"""
        result_segments = []
        used_params = set()
        
        for segment in self.segments:
            if self._is_parameter(segment):
                param_name = self._extract_parameter_name(segment)
                if param_name not in params:
                    raise ValueError(f"パラメータ '{param_name}' が不足しています")
                result_segments.append(str(params[param_name]))
                used_params.add(param_name)
            else:
                result_segments.append(segment)
        
        unused_params = {k: v for k, v in params.items() if k not in used_params}
        path = "/".join(result_segments) if result_segments else ""
        
        return path, unused_params

class Router:
    """URLルーティングを処理するクラス"""
    def __init__(self, root="", urls_str="project.urls", name=None):
        """
        Args:
            root: ルートパス
            urls_str: URLパターンを含むモジュールのインポートパス
            name: ルーターの名前
        """
        if root.startswith("/"):
            raise ValueError("ルートパスは / で始まってはいけません")
        
        urls_module = importlib.import_module(urls_str)
        self.urlpatterns = urls_module.urlpatterns
        self.root = root
        self.name = name
        self.root_segments = self._parse_segments(root)
        self.app_name = getattr(urls_module, 'app_name', None)
    
    def _parse_segments(self, path):
        """パスをセグメントに分割"""
        if path == "":
            return []
        return path.split('/')
    
    def _parse_url_path(self, abs_path):
        """絶対パスをセグメントに変換"""
        if not abs_path:
            raise ValueError("abs_pathは空であってはいけません")
        
        if abs_path == "/":
            return []
        
        if not abs_path.startswith("/"):
            raise ValueError("abs_pathは / で始まる必要があります")
        
        # 末尾のスラッシュを削除
        if len(abs_path) > 1 and abs_path.endswith("/"):
            abs_path = abs_path[:-1]
        
        return abs_path[1:].split('/')
    
    def path2view(self, abs_path=None, segments=None, kwargs=None):
        """
        パスからビュー関数を取得します。
        
        Args:
            abs_path: 絶対パス（例: '/users/123'）
            segments: パスセグメントのリスト
            kwargs: パスパラメータの値
            
        Returns:
            (view, kwargs)のタプル
            
        Raises:
            NotMatched: パスに一致するビューが見つからない場合
        """
        if abs_path is not None and segments is not None:
            raise ValueError("abs_pathとsegmentsは同時に指定できません")
        if abs_path is None and segments is None:
            raise ValueError("abs_pathまたはsegmentsを指定する必要があります")
        
        if abs_path is not None:
            segments = self._parse_url_path(abs_path)
        
        if kwargs is None:
            kwargs = {}
        
        # Path パターンでのマッチングを試行
        for pattern in self.urlpatterns:
            if isinstance(pattern, Path):
                matches, params = pattern.matches(segments)
                if matches:
                    merged_kwargs = {**kwargs, **params}
                    return pattern.view, merged_kwargs
        
        # Router パターンでのマッチングを試行
        for pattern in self.urlpatterns:
            if isinstance(pattern, Router):
                remaining_segments = self._try_router_match(segments, pattern)
                if remaining_segments is not None:
                    return pattern.path2view(segments=remaining_segments, kwargs=kwargs)
        
        raise NotMatched(f"パス '{'/'.join(segments) if segments else '/'}' に一致するビューが見つかりません")
    
    def _try_router_match(self, url_segments, router):
        """ルーターのルートパターンがURLセグメントにマッチするかチェック"""
        router_segments = router.root_segments
        
        # ルーターのセグメント数がURLセグメント数より多い場合は不一致
        if len(router_segments) > len(url_segments):
            return None
        
        # ルーターのセグメント数が0の場合（空のroot）は、全セグメントを渡す
        if len(router_segments) == 0:
            return url_segments
        
        # ルーターのセグメント数とURLセグメント数が同じ場合は不一致（残りがない）
        if len(router_segments) == len(url_segments):
            return None
        
        # 各セグメントをチェック
        for i, (router_seg, url_seg) in enumerate(zip(router_segments, url_segments)):
            if router_seg.startswith("{") and router_seg.endswith("}"):
                # パラメータセグメントは任意の値にマッチ
                continue
            elif router_seg != url_seg:
                return None
        
        # マッチした場合、残りのセグメントを返す
        return url_segments[len(router_segments):]
    
    def name2path(self, name: str, kwargs=None, root=""):
        """
        名前からURLパスを生成します。
        
        Args:
            name: 名前（例: 'app:user_detail'）
            kwargs: パスパラメータの値
            root: ルートパス
            
        Returns:
            生成されたURLパス
            
        Raises:
            NotMatched: 名前に一致するパスが見つからない場合
            KwargsRemain: 使用されなかったキーワード引数がある場合
        """
        if kwargs is None:
            kwargs = {}
        
        name_parts = name.split(":")
        
        # 単一名前の場合、このルーターのPath パターンから検索
        if len(name_parts) == 1:
            target_name = name_parts[0]
            for pattern in self.urlpatterns:
                if isinstance(pattern, Path) and pattern.name == target_name:
                    path, unused_params = pattern.generate_url(kwargs)
                    if unused_params:
                        raise KwargsRemain("未使用のキーワード引数があります: " + ", ".join(unused_params.keys()))
                    return os.path.join(root, path)
        
        # 名前空間付きの場合、該当するRouter から検索
        else:
            if len(name_parts) < 2:
                raise ValueError("ネストされたルーターには複数の名前要素が必要です")
            
            router_name = name_parts[0]
            remaining_name = ":".join(name_parts[1:])
            
            for pattern in self.urlpatterns:
                if isinstance(pattern, Router) and pattern.name == router_name:
                    router_path, unused_params = self._generate_router_path(pattern, kwargs)
                    full_root = os.path.join(root, router_path)
                    return pattern.name2path(remaining_name, unused_params, full_root)
        
        raise NotMatched(f"名前 '{name}' に一致するパスが見つかりません")
    
    def _generate_router_path(self, router, params):
        """ルーターのルートパスを生成"""
        if not router.root_segments:
            return "", params
        
        result_segments = []
        used_params = set()
        
        for segment in router.root_segments:
            if segment.startswith("{") and segment.endswith("}"):
                param_name = segment[1:-1]
                if param_name not in params:
                    raise ValueError(f"パラメータ '{param_name}' が不足しています")
                result_segments.append(str(params[param_name]))
                used_params.add(param_name)
            else:
                result_segments.append(segment)
        
        unused_params = {k: v for k, v in params.items() if k not in used_params}
        path = "/".join(result_segments)
        
        return path, unused_params

