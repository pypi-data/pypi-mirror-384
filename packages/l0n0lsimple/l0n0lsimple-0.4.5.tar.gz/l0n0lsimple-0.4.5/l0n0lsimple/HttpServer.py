from aiohttp import web
import argparse
import ssl
import os


def main():
    parser = argparse.ArgumentParser(description="启动一个 aiohttp 静态文件服务器。")
    parser.add_argument(
        'directory',
        type=str,
        help='要提供静态文件的目录路径。'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='服务器绑定的主机地址（默认：127.0.0.1）。'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='服务器绑定的端口号（默认：8080）。'
    )
    parser.add_argument("-s", "--show-index",
                        action="store_true", help="显示索引目录")

    # 新增 SSL 参数
    parser.add_argument(
        '--certfile',
        type=str,
        help='SSL 证书文件路径 (PEM 格式)'
    )
    parser.add_argument(
        '--keyfile',
        type=str,
        help='SSL 私钥文件路径 (PEM 格式)'
    )

    args = parser.parse_args()

    app = web.Application()
    app.router.add_static('/', args.directory, show_index=args.show_index)

    ssl_context = None
    if args.certfile and args.keyfile:
        if not os.path.exists(args.certfile):
            raise FileNotFoundError(f"证书文件不存在: {args.certfile}")
        if not os.path.exists(args.keyfile):
            raise FileNotFoundError(f"私钥文件不存在: {args.keyfile}")

        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=args.certfile, keyfile=args.keyfile)

    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context)


if __name__ == '__main__':
    main()
