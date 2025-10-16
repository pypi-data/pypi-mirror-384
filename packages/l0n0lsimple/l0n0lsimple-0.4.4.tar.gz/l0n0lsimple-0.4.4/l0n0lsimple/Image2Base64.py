#!/usr/bin/env python3
import base64
import argparse
import mimetypes

def encode_image(image_path, output_file=None, prefix=False):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    if prefix:
        # 自动根据文件扩展名推断 MIME 类型
        mime, _ = mimetypes.guess_type(image_path)
        if mime is None:
            mime = "image/png"  # 默认兜底
        encoded = f"data:{mime};base64,{encoded}"

    if output_file:
        with open(output_file, "w") as f:
            f.write(encoded)
        print(f"[+] 已保存 Base64 到 {output_file}")
    else:
        print(encoded)

def decode_image(base64_file, output_file):
    with open(base64_file, "r") as f:
        data = f.read().strip()
    # 如果有 data:image/...;base64, 前缀，去掉它
    if data.startswith("data:"):
        data = data.split(",", 1)[1]
    decoded = base64.b64decode(data)
    with open(output_file, "wb") as f:
        f.write(decoded)
    print(f"[+] 已保存图片到 {output_file}")

def main():
    parser = argparse.ArgumentParser(description="图片 Base64 编码/解码工具")
    subparsers = parser.add_subparsers(dest="command")

    # 编码
    encode_parser = subparsers.add_parser("encode", help="图片转 Base64")
    encode_parser.add_argument("image", help="输入图片路径")
    encode_parser.add_argument("-o", "--output", help="输出 Base64 文件")
    encode_parser.add_argument("-p", "--prefix", action="store_true",
                               help="输出可直接用于 <img src=\"\"/> 的字符串")

    # 解码
    decode_parser = subparsers.add_parser("decode", help="Base64 转图片")
    decode_parser.add_argument("base64file", help="输入 Base64 文本文件")
    decode_parser.add_argument("-o", "--output", required=True, help="输出图片路径")

    args = parser.parse_args()

    if args.command == "encode":
        encode_image(args.image, args.output, args.prefix)
    elif args.command == "decode":
        decode_image(args.base64file, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
