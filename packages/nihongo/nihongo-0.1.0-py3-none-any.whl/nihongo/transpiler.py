import io, sys, os, tokenize, importlib.abc, importlib.util

_JP2PY = {
    "関数": "def",
    "もし": "if",
    "他": "else",
    "戻る": "return",
    "取り込む": "import",
    "から": "from",
    "として": "as",
    "真": "True",
    "偽": "False",
    "無": "None",
}

def transpile_jp_to_py(src: str) -> str:
    out = io.StringIO()
    for tok_type, tok_str, *_ in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok_type == tokenize.NAME and tok_str in _JP2PY:
            tok_str = _JP2PY[tok_str]
        out.write(tok_str if tok_type != tokenize.NEWLINE else "\n")
    return out.getvalue()

def 実行ソース日本語(src: str, グローバル=None):
    py = transpile_jp_to_py(src)
    グローバル = グローバル or {}
    exec(compile(py, "<nihongo>", "exec"), グローバル)

class NihongoLoader(importlib.abc.SourceLoader):
    def __init__(self, path): self.path = path
    def get_filename(self, fullname): return self.path
    def get_data(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return transpile_jp_to_py(f.read()).encode("utf-8")

class NihongoFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        mod = fullname.split(".")[-1]
        for base in sys.path:
            p = os.path.join(base, mod + ".jp.py")
            if os.path.isfile(p):
                return importlib.util.spec_from_loader(fullname, NihongoLoader(p))
        return None

def install_importer():
    if not any(isinstance(f, NihongoFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, NihongoFinder())
