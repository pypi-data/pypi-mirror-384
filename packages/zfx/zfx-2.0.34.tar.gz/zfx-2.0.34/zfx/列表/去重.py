def 去重(列表对象, debug=True):
    """
    去除列表中重复的元素，返回一个新的列表，保持元素出现的顺序。

    参数:
        - 列表对象 (list): 要处理的列表，例如 [1, 2, 2, 3, 4, 4]。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值:
        - list:
            - 成功时返回去重后的新列表；
            - 如果输入为空列表或发生异常，返回空列表 []。

    注意事项:
        1. 输入必须是列表类型，否则会触发异常。
        2. 保持原列表中元素第一次出现的顺序。

    使用示例:
        新列表 = 去重([1, 2, 2, 3, 4, 4])
        新列表 = 去重(["a", "b", "a", "c"])
    """
    try:
        if not isinstance(列表对象, list):
            raise TypeError("参数必须为列表类型")
        seen = set()
        去重后的列表 = []
        for 元素 in 列表对象:
            if 元素 not in seen:
                去重后的列表.append(元素)
                seen.add(元素)
        return 去重后的列表
    except Exception as e:
        if debug:
            print(f"[去重] 功能异常：{e}（输入={列表对象}）")
        return []
