from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults
from urllib.parse import parse_qs
import json

class リクエスト:
    def __init__(self, environ):
        setup_testing_defaults(environ)
        self.方法 = environ.get("REQUEST_METHOD", "GET")
        self.パス = environ.get("PATH_INFO", "/")
        self.クエリ文字列 = environ.get("QUERY_STRING", "")
        self.クエリ = parse_qs(self.クエリ文字列)
        try:
            長さ = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            長さ = 0
        self.本文 = environ["wsgi.input"].read(長さ) if 長さ > 0 else b""

    def テキスト(self):
        return self.本文.decode("utf-8", errors="replace")

    def JSON(self):
        if not self.本文:
            return None
        try:
            return json.loads(self.本文.decode("utf-8"))
        except json.JSONDecodeError:
            return None


def 応答(本文, 状態=200, ヘッダ=None, 種類=None):
    if isinstance(本文, str):
        本文 = 本文.encode("utf-8")
        種類 = 種類 or "text/plain; charset=utf-8"
    ヘッダ = ヘッダ or {}
    ヘッダ.setdefault("Content-Type", 種類)
    ヘッダ.setdefault("Content-Length", str(len(本文)))
    return 状態, ヘッダ, 本文


def JSON応答(データ, 状態=200, ヘッダ=None):
    本文 = json.dumps(データ, ensure_ascii=False)
    return 応答(本文, 状態, ヘッダ, "application/json; charset=utf-8")


class アプリ:
    def __init__(self):
        self._routes = {}

    def ルート(self, パス, メソッド="GET"):
        メソッド = メソッド.upper()
        def _decorator(func):
            self._routes[(メソッド, パス)] = func
            return func
        return _decorator

    def __call__(self, environ, start_response):
        req = リクエスト(environ)
        func = self._routes.get((req.方法, req.パス))
        if func:
            結果 = func(req)
            状態, ヘッダ, 本文 = 応答(結果)
        else:
            状態, ヘッダ, 本文 = 応答("404 Not Found", 404)
        start_response(f"{状態} OK", [(k, v) for k, v in ヘッダ.items()])
        return [本文]

    def 実行(self, ホスト="127.0.0.1", ポート=8000):
        with make_server(ホスト, ポート, self) as httpd:
            print(f"🌸 サーバー起動: http://{ホスト}:{ポート}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("💤 終了しました")
