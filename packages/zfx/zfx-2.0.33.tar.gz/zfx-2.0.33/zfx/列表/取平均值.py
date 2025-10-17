def 取平均值(列表对象, debug=True):
    r"""
    计算列表中所有元素的平均值。

    参数：
        - 列表对象 (list): 要处理的列表，例如 [1, 2, 3, 4]。
        - debug (bool): 是否输出调试日志（异常时打印错误信息），默认值为 True。

    返回值：
        - float:
            - 成功时返回平均值；
            - 如果列表为空或发生异常，返回 None。

    注意事项：
        1. 输入必须是列表类型，否则会触发异常。
        2. 列表必须全部为数字类型，否则会触发异常。
        3. 如果列表为空，将返回 None。

    使用示例：
        平均值 = 取平均值([5, 2, 9])
        平均值 = 取平均值([1.5, 2.5, 3.5])
        平均值 = 取平均值([], debug=False)
    """
    try:
        # 确保输入是列表类型
        if not isinstance(列表对象, list):
            raise TypeError("参数必须为列表类型")

        # 处理空列表情况
        if not 列表对象:
            return None

        # 检查列表内所有元素必须为数字
        if not all(isinstance(x, (int, float)) for x in 列表对象):
            raise ValueError("列表元素必须全部为数字类型")

        # 计算平均值
        return sum(列表对象) / len(列表对象)

    except Exception as e:
        if debug:
            print(f"[取平均值] 功能异常：{e}（输入={列表对象}）")
        return None
