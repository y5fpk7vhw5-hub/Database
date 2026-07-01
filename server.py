import os
from http.server import ThreadingHTTPServer

from app import Handler
from seed import DB_PATH, initialize


def main():
    initialize(reset=not DB_PATH.exists())
    port = int(os.environ.get('PORT', '8080'))
    server = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print(f'Construction Site DB running on port {port}')
    server.serve_forever()


if __name__ == '__main__':
    main()
