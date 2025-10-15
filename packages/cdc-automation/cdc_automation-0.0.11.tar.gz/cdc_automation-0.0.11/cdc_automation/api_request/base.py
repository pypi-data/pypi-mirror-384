from pathlib import Path
from contextlib import contextmanager
from requests.models import Response
from requests.sessions import Session
import json as JSON
import time
import re
import logging
import inspect
import warnings
from .package_info import PackageEnvInfo


class Request(PackageEnvInfo, Session):

    def __init__(self, test_env: str = None):
        """
        Build a Request object
        :param test_env: if you want to use specific test env in this instance
        """
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        # self.session = requests.sessions.Session()
        super().__init__()
        self.url = None
        self._env = test_env if test_env else super().TestEnv
        self.logger = logging.getLogger(__name__)

    def re_param(self, url, **kwargs):
        """
        please add own data in env_info.py and update to cdc_automation.package_info.PackageEnvInfo
        """
        if "http" not in url:
            self.url = super().build_url(url, self._env)
        else:
            self.url = url

        if "headers" not in kwargs:
            # self.session.headers = super().build_header(url, self._env)
            self.headers = super().build_header(url, self._env)

    def _custom_logger(self, response):
        def repl(matchobj):
            if matchobj.group(0) == "\\":
                return ""
            else:
                return matchobj.group(0)[:-1] + "."
        caller_frame = inspect.currentframe().f_back.f_back
        frame_info = inspect.getframeinfo(caller_frame)
        file_path = re.search(rf"{re.escape(str(super().project_root_dir))}(.+)", frame_info.filename).group(1)
        function_name = frame_info.function
        line_number = frame_info.lineno

        matched_regex = ".*?\\\\"
        response_log = self.format_res_log(response)
        self.logger.debug(
            f'{re.sub(matched_regex, repl, file_path)}:{function_name}[{line_number}] {JSON.dumps(response_log)}',
            extra=response_log
        )

    def get(self, url, logged=True, **kwargs):
        self.re_param(url, **kwargs)
        # res = self.session.get(self.url, **kwargs, verify=False if 'https://' in self.url else None)
        res = super().get(self.url, **kwargs, verify=False if 'https://' in self.url else None)
        if logged is True:
            self._custom_logger(res)
        return res

    def post(self, url, data=None, json=None, logged=True, **kwargs):
        self.re_param(url, **kwargs)
        # res = self.session.post(self.url, data, json, **kwargs, verify=False if 'https://' in self.url else None)
        res = super().post(self.url, data, json, **kwargs, verify=False if 'https://' in self.url else None)
        if logged is True:
            self._custom_logger(res)
        return res

    def put(self, url, data=None, **kwargs):
        self.re_param(url, **kwargs)
        # res = self.session.put(self.url, data, **kwargs, verify=False if 'https://' in self.url else None)
        res = super().put(self.url, data, **kwargs, verify=False if 'https://' in self.url else None)
        self._custom_logger(res)
        return res

    def delete(self, url, **kwargs):
        self.re_param(url, **kwargs)
        # res = self.session.delete(self.url, **kwargs, verify=False if 'https://' in self.url else None)
        res = super().delete(self.url, **kwargs, verify=False if 'https://' in self.url else None)
        self._custom_logger(res)
        return res

    @staticmethod
    def format_res_log(res: Response) -> dict:
        """
        Change Response Obj to log format

        :param res: Response Obj
        :return: log format as dict
        """
        if res.request.method == "GET":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers)
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }
        elif res.request.method == "POST":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers),
                    "body": JSON.loads(res.request.body) if res.request.headers.get("content-type") == "application/json" else None
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }
        elif res.request.method == "PUT":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers),
                    "body": JSON.loads(res.request.body)
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }
        elif res.request.method == "DELETE":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers)
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }


def _find_project_root(possible_markers=None):
    if possible_markers is None:
        possible_markers = ["pyproject.toml", "setup.py", "requirements.txt", ".git"]

    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        for marker in possible_markers:
            if (parent / marker).exists():
                return parent
    # 如果都找不到，就回傳最上層資料夾
    return current_path.parents[-1]


_PROJECT_ROOT = _find_project_root()


class RequestContext(Session):

    def __init__(self, base_url: str = "", default_headers: dict[str, str] = None, verify: bool = None, token_refresher: object = None, logged: bool = True):
        """

        :param base_url:
        :param default_headers:
        :param verify:
        :param token_refresher: will pass dict key {"token", "expire_at", "refresh_token"} param to object and object must return tuple (new_token, expires_in, refresh_token)
        :param logged:
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.base_url = base_url
        self.headers.update(default_headers or {})
        self.verify = verify
        self.logged = logged
        self.token_refresher = token_refresher
        self.token_info = {
            "token": self.headers.get("Authorization"),  # 初始 token
            "expire_at": None,  # 過期時間（timestamp）
            "refresh_token": None  # 交換用token
        }

    def request(self, method, url, *args, **kwargs):
        # combine URL if no http in url by this time request
        url = url if re.search(r"^http", url) else self.base_url + url

        # add default verify value in kwargs if no "verify" value by this time request
        try:
            kwargs["verify"]
        except KeyError as e:
            kwargs["verify"] = self.verify

        # 在送出前自動刷新 token
        self._refresh_token_if_needed()

        # send request
        response = super().request(method, url, *args, **kwargs)

        # record log from response
        if self.logged is True:
            self._custom_logger(response)
        return response

    def _custom_logger(self, response):
        def repl(matchobj):
            if matchobj.group(0) == "\\":
                return ""
            else:
                return matchobj.group(0)[:-1] + "."
        caller_frame = inspect.currentframe().f_back.f_back.f_back
        frame_info = inspect.getframeinfo(caller_frame)
        file_path = re.search(rf"{re.escape(str(_PROJECT_ROOT))}(.+)", frame_info.filename).group(1)
        function_name = frame_info.function
        line_number = frame_info.lineno

        matched_regex = ".*?\\\\"
        response_log = self.format_res_log(response)
        self.logger.debug(
            f'{re.sub(matched_regex, repl, file_path)}:{function_name}[{line_number}] {JSON.dumps(response_log)}',
            extra=response_log
        )

    @contextmanager
    def temp_logged_status(self, temp_logged_status: bool = False):
        """
        set temporary logged status by with statement

        with request_context.temp_logged_status(False):
            print(request_context.logged)
        """
        original = self.logged
        self.logged = temp_logged_status
        try:
            yield
        finally:
            self.logged = original

    @staticmethod
    def format_res_log(res: Response) -> dict:
        """
        Change Response Obj to log format

        :param res: Response Obj
        :return: log format as dict
        """
        if res.request.method == "GET":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers)
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }
        elif res.request.method == "POST":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers),
                    "body": JSON.loads(res.request.body) if res.request.headers.get("content-type") == "application/json" else None
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }
        elif res.request.method == "PUT":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers),
                    "body": JSON.loads(res.request.body)
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }
        elif res.request.method == "DELETE":
            return {
                "request": {
                    "url": str(res.request.url),
                    "headers": dict(res.request.headers)
                },
                "response": {
                    "headers": dict(res.headers),
                    "body": res.json() if res.headers.get("content-type") and "json" in res.headers.get("content-type") else None
                }
            }

    def set_token(self, token: str, expires_in: int = None, refresh_token: str = None):
        """設定 token 與過期時間"""
        self.token_info["token"] = token
        self.token_info["expire_at"] = time.time() + expires_in if expires_in else None
        self.token_info["refresh_token"] = refresh_token
        self.headers["Authorization"] = f"Bearer {token}"

    def _is_token_expired(self) -> bool:
        """檢查 token 是否過期"""
        expire_at = self.token_info.get("expire_at")
        if not expire_at:
            return False  # 沒設定過期時間 → 視為不會過期
        return time.time() + 10 >= expire_at

    def _refresh_token_if_needed(self):
        """如有設定 token_refresher，則在過期時自動刷新"""
        if self._is_token_expired() and callable(self.token_refresher):
            new_token, expires_in, refresh_token = self.token_refresher(**self.token_info)
            self.set_token(new_token, expires_in, refresh_token)
