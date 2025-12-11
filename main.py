from waitress import serve

from web.app import app


def main():
    serve(app, host='192.168.111.108', port=5555, threads=5)


if __name__ == "__main__":
    main()
