import argparse
import json
import asyncio
import secrets
from pathlib import Path
from typing import Any, Dict
from aiohttp import web

# 全局变量
令牌空间: Dict[str, Dict[str, Any]] = {}
允许令牌 = []
令牌文件 = Path("tokens.json")
最后修改时间 = None

# ---- 封装 JSON 响应 ----


def json响应(data, status=200):
    return web.json_response(
        data,
        status=status,
        dumps=lambda obj: json.dumps(obj, ensure_ascii=False)
    )

# ---- 类型辅助 ----


def 类型名(值: Any) -> str:
    if 值 is None:
        return "null"
    if isinstance(值, bool):
        return "bool"
    if isinstance(值, int):
        return "int"
    if isinstance(值, float):
        return "float"
    if isinstance(值, str):
        return "str"
    if isinstance(值, list):
        return "list"
    if isinstance(值, dict):
        return "dict"
    return type(值).__name__


def 响应编码(值: Any) -> Dict[str, Any]:
    return {"类型": 类型名(值), "值": 值}

# ---- 令牌加载 ----


def 确保令牌文件():
    if not 令牌文件.exists():
        随机令牌 = secrets.token_hex(32)  # 256 hex 字符
        with 令牌文件.open("w", encoding="utf-8") as f:
            json.dump([随机令牌], f, indent=2, ensure_ascii=False)
        print(f"[INFO] 已创建 tokens.json，令牌: {随机令牌}")


def 加载令牌():
    global 允许令牌, 令牌空间, 最后修改时间
    确保令牌文件()

    修改时间 = 令牌文件.stat().st_mtime
    if 最后修改时间 is not None and 修改时间 == 最后修改时间:
        return

    with 令牌文件.open("r", encoding="utf-8") as f:
        令牌列表 = json.load(f)
        if not isinstance(令牌列表, list) or not all(isinstance(t, str) for t in 令牌列表):
            raise ValueError("tokens.json 必须是字符串数组")

    旧集合 = set(允许令牌)
    新集合 = set(令牌列表)

    for t in 旧集合 - 新集合:
        令牌空间.pop(t, None)
    for t in 新集合 - 旧集合:
        令牌空间[t] = {}

    允许令牌[:] = 令牌列表
    最后修改时间 = 修改时间
    print(f"[INFO] 已加载 tokens.json: {允许令牌}")


async def 监视令牌():
    while True:
        try:
            加载令牌()
        except Exception as e:
            print(f"[WARN] 重新加载 tokens.json 失败: {e}")
        await asyncio.sleep(5)

# ---- 中间件 ----


@web.middleware
async def 身份验证中间件(request, handler):
    认证头 = request.headers.get("Authorization", "")
    if not 认证头.startswith("Bearer "):
        return json响应({"错误": "未授权"}, status=401)
    令牌 = 认证头.split(" ", 1)[1]
    if 令牌 not in 允许令牌:
        return json响应({"错误": "未授权"}, status=401)
    request["令牌"] = 令牌
    request["空间"] = 令牌空间[令牌]
    return await handler(request)

# ---- 处理函数 ----


async def 设置处理(request):
    try:
        数据 = await request.json()
    except Exception:
        return json响应({"错误": "无效 JSON"}, status=400)

    键 = 数据.get("键")
    if not isinstance(键, str) or not 键:
        return json响应({"错误": "缺少或无效的 键"}, status=400)

    if "值" not in 数据:
        return json响应({"错误": "缺少 值"}, status=400)

    request["空间"][键] = 数据["值"]
    return json响应({"状态": "ok"})


async def 获取处理(request):
    try:
        数据 = await request.json()
    except Exception:
        return json响应({"错误": "无效 JSON"}, status=400)

    键 = 数据.get("键")
    if not 键:
        return json响应({"错误": "缺少 键"}, status=400)

    空间 = request["空间"]
    if 键 not in 空间:
        return json响应({"错误": "未找到"}, status=404)

    值 = 空间[键]
    响应数据 = {"键": 键, **响应编码(值)}
    return json响应(响应数据)


def 创建应用():
    应用 = web.Application(middlewares=[身份验证中间件])
    应用.router.add_post("/set", 设置处理)
    应用.router.add_post("/get", 获取处理)
    return 应用


def main():
    解析器 = argparse.ArgumentParser(description="中文接口 aiohttp Key-Value 服务器")
    解析器.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    解析器.add_argument("--port", type=int, default=8080, help="监听端口")
    参数 = 解析器.parse_args()

    加载令牌()

    应用 = 创建应用()
    循环 = asyncio.get_event_loop()
    循环.create_task(监视令牌())
    web.run_app(应用, host=参数.host, port=参数.port)


if __name__ == "__main__":
    main()
