import requests
from typing import Any, Optional


def 发送_POST请求(
    url: str,
    严格模式: bool = True,
    **kwargs: Any
) -> Optional[str]:
    """
    安全发送 HTTP POST 请求并返回响应文本。

    功能说明：
        封装 requests.post()，在功能上完全兼容原生接口。
        请求成功时返回响应文本（str），出现异常时不会抛出错误，而是返回 None。
        适用于需要稳健执行的自动化脚本或无人值守任务。

    参数：
        url (str):
            请求目标的完整 URL，例如 "https://www.example.com/api"。
        严格模式 (bool):
            是否将非 2xx 状态码视为异常。
              - True：状态码非 2xx 会触发异常并返回 None。
              - False：始终返回响应文本，即使状态码异常。
            默认值为 True。
        **kwargs (Any):
            透传给 requests.post() 的所有参数，
            包括 data、json、headers、timeout、proxies、cookies 等。

    返回：
        str | None:
            - 请求成功时返回响应文本（HTML、JSON 等）。
            - 发生异常或请求失败时返回 None。

    使用示例：
        示例一：发送表单数据
            内容 = 发送_POST请求(
                "https://www.example.com/api/login",
                data={"username": "admin", "password": "123456"}
            )
            if 内容 is None:
                print("请求失败")
            else:
                print("响应内容：", 内容[:200])

        示例二：发送 JSON 数据并自定义请求头
            内容 = 发送_POST请求(
                "https://www.example.com/api/submit",
                json={"task": "run", "priority": "high"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            if 内容:
                print("请求成功，响应长度：", len(内容))
            else:
                print("请求失败")

    说明：
        1. 函数永不抛出异常，失败时返回 None。
        2. 若需获取完整 Response 对象，可使用 requests.post() 或单独封装。
        3. 若需测试 API 请求，可使用 IANA 保留域名 example.com。
    """
    try:
        resp = requests.post(url, **kwargs)
        if 严格模式:
            resp.raise_for_status()
        return resp.text
    except Exception:
        return None
