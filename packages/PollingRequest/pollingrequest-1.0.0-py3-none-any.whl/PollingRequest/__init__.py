from copy import deepcopy
import threading
import time
from typing import (Dict, Callable, Optional,
                    Any)
import requests

__version__ = "1.0.0"

class Polling:
    def __init__(self):
        # 基本配置
        self._url = None
        self._method = "GET"
        self._cookie = {}
        self._headers = {}
        self._use_old_cookie = False
        self._max_requests = -1
        self._json_path = None
        self._sleep_time = 1.0
        self._data = {}
        
        # 回调函数
        self._on_edit_func = None
        self._on_end_func = None
        self._on_err_func = None
        self._is_end_func = None
        
        # 状态控制
        self._current_count = 0
        self._is_running = False
        self._is_paused = False
        self._should_stop = False
        self._session = None
        self._last_json = None
        self._lock = threading.Lock()
        self._polling_thread = None

    def data(self, data: Dict = None) -> 'Polling':
        """设置请求数据"""
        if data is not None:
            self._data = data
        return self

    def url(self, url: str) -> 'Polling':
        self._url = url
        return self

    def method(self, method: str) -> 'Polling':
        self._method = method.upper()
        return self

    def cookie(self, cookie: Dict = None, use_old_cookie: bool = False) -> 'Polling':
        if cookie is not None:
            self._cookie = cookie
        self._use_old_cookie = use_old_cookie
        return self

    def headers(self, headers: Dict = None) -> 'Polling':
        if headers is not None:
            self._headers = headers
        return self

    def setmax(self, num: int = -1) -> 'Polling':
        self._max_requests = num
        return self

    def isdifferent(self, path: str = "/") -> 'Polling':
        self._json_path = path
        return self

    def isend(self, f: Callable[[Any], bool]) -> 'Polling':
        self._is_end_func = f
        return self

    def sleeptime(self, t: float) -> 'Polling':
        self._sleep_time = t
        return self

    def onedit(self, f: Callable[[Any], None]) -> 'Polling':
        self._on_edit_func = f
        return self

    def onend(self, f: Callable[[Any], None]) -> 'Polling':
        self._on_end_func = f
        return self

    def onerr(self, f: Callable[[Exception], None]) -> 'Polling':
        self._on_err_func = f
        return self

    def copy(self) -> 'Polling':
        """复制当前的类，保护各变量状态"""
        new_instance = Polling()
        
        # 复制基本配置
        new_instance._url = self._url
        new_instance._method = self._method
        new_instance._cookie = deepcopy(self._cookie)
        new_instance._use_old_cookie = self._use_old_cookie
        new_instance._max_requests = self._max_requests
        new_instance._json_path = self._json_path
        new_instance._sleep_time = self._sleep_time
        new_instance._data = deepcopy(self._data)
        
        # 复制回调函数引用
        new_instance._on_edit_func = self._on_edit_func
        new_instance._on_end_func = self._on_end_func
        new_instance._on_err_func = self._on_err_func
        new_instance._is_end_func = self._is_end_func
        
        # 不复制运行时状态
        return new_instance

    def _check_required_fields(self):
        """检查所有必填项是否设置"""
        required_fields = ['_url']
        missing_fields = []
        
        for field in required_fields:
            if getattr(self, field) is None:
                missing_fields.append(field[1:])  # 去掉下划线前缀
        
        if missing_fields:
            raise ValueError(f"缺少必填项: {', '.join(missing_fields)}")

    def _get_json_by_path(self, data: Any, path: str) -> Any:
        """根据路径获取JSON中的值"""
        if path == "/" or not path:
            return data
        
        path_parts = path.strip('/').split('/')
        current = data
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current

    def _has_json_changed(self, new_json: Any) -> bool:
        """检查JSON是否有变化"""
        if self._last_json is None:
            self._last_json = new_json
            return True  # 第一次请求应该触发onedit
        
        if self._json_path:
            old_value = self._get_json_by_path(self._last_json, self._json_path)
            new_value = self._get_json_by_path(new_json, self._json_path)
            changed = old_value != new_value
        else:
            changed = self._last_json != new_json
        
        if changed:
            self._last_json = new_json
        return changed

    def _make_request(self) -> Optional[Any]:
        """执行HTTP请求"""
        try:
            if self._use_old_cookie and self._session is None:
                self._session = requests.Session()
            
            cookies = self._cookie
            headers = self._headers
            
            # 根据请求方法和是否有数据来决定如何发送请求
            if self._method in ['POST', 'PUT', 'PATCH'] and self._data:
                # 对于有请求体的方法，发送data
                if self._use_old_cookie and self._session:
                    response = self._session.request(
                        method=self._method,
                        url=self._url,
                        cookies=cookies,
                        headers=headers,
                        json=self._data
                    )
                else:
                    response = requests.request(
                        method=self._method,
                        url=self._url,
                        cookies=cookies,
                        headers=headers,
                        json=self._data
                    )
            else:
                # 对于GET等方法，或者没有data的情况
                if self._use_old_cookie and self._session:
                    response = self._session.request(
                        method=self._method,
                        url=self._url,
                        cookies=cookies,
                        headers=headers
                    )
                else:
                    response = requests.request(
                        method=self._method,
                        url=self._url,
                        cookies=cookies,
                        headers=headers
                    )
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            if self._on_err_func:
                self._on_err_func(e)
            return None

    def _polling_loop(self):
        """轮询主循环"""
        self._current_count = 0
        
        while not self._should_stop:
            # 检查暂停状态
            with self._lock:
                if self._is_paused:
                    time.sleep(0.1)
                    continue
            
            # 检查最大请求次数
            if self._max_requests > 0 and self._current_count >= self._max_requests:
                if self._on_end_func:
                    self._on_end_func(self._last_json)
                break
            
            # 执行请求
            current_json = self._make_request()
            self._current_count += 1
            
            if current_json is None:
                # 如果请求失败但没有错误处理函数，继续循环
                # 如果设置了错误处理函数，由错误处理函数决定是否继续
                # 注意：在错误处理函数中不应调用end()方法，否则可能导致线程问题
                if self._on_err_func:
                    self._on_err_func(Exception("Request failed and returned None"))
                if not self._on_err_func or not self._should_stop:
                    time.sleep(self._sleep_time)
                continue
            
            # 检查结束条件
            if self._is_end_func and self._is_end_func(current_json):
                if self._on_end_func:
                    self._on_end_func(current_json)
                break
            
            # 检查变化
            if self._on_edit_func and self._has_json_changed(current_json):
                self._on_edit_func(current_json)
            
            # 休眠
            time.sleep(self._sleep_time)
        
        # 确保在退出循环时重置状态
        self._is_running = False
        self._is_paused = False
        self._should_stop = False

    def start(self):
        """开始轮询"""
        self._check_required_fields()
        
        if self._is_running:
            return self
        
        self._should_stop = False
        self._is_running = True
        self._is_paused = False
        
        self._polling_thread = threading.Thread(target=self._polling_loop)
        self._polling_thread.daemon = True
        self._polling_thread.start()
        
        return self

    def stop(self):
        """暂停/继续轮询"""
        if not self._is_running:
            return self
        
        with self._lock:
            self._is_paused = not self._is_paused
        
        return self

    def end(self):
        """结束轮询"""
        if not self._is_running:
            return self
        
        self._should_stop = True
        self._is_running = False
        
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=5)
        
        return self

    @property
    def getconfig(self) -> Dict[str, Any]:
        """获取全部设置"""
        return {
            'url': self._url,
            'method': self._method,
            'cookie': self._cookie,
            'use_old_cookie': self._use_old_cookie,
            'max_requests': self._max_requests,
            'json_path': self._json_path,
            'sleep_time': self._sleep_time,
            'data': self._data,
            'has_on_edit': self._on_edit_func is not None,
            'has_on_end': self._on_end_func is not None,
            'has_on_err': self._on_err_func is not None,
            'has_is_end': self._is_end_func is not None
        }

    @property
    def getnow(self) -> int:
        """获取目前是第几次轮询"""
        return self._current_count

    @property
    def isstop(self) -> bool:
        """获取是否暂停"""
        return self._is_paused if self._is_running else False
