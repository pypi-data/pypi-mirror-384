from . import 実行ソース日本語, install_importer

def main():
    install_importer()
    サンプル = '''
取り込む nihongo として に

関数 起動():
    app = に.アプリ()

    @app.ルート('/')
    関数 ホーム(req):
        戻る 'こんにちは、世界! (nihongo)'

    app.実行('127.0.0.1', 8000)

もし __name__ == '__main__':
    起動()
'''
    print("🌸 nihongo: デモ実行中")
    実行ソース日本語(サンプル)

if __name__ == "__main__":
    main()
