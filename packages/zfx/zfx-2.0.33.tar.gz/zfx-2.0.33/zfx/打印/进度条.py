import sys


def 进度条(当前值, 总值, 长度=40):
    """
    打印进度条。

    参数:
        - 当前值 (int): 当前进度值。
        - 总值 (int): 总进度值。
        - 长度 (int, optional): 进度条的长度。默认是 40。

    返回:
        - bool: 如果打印过程中没有出现异常，返回 True；否则返回 False。

    使用示例：
        总值 = 100
        for 当前值 in range(总值 + 1):
            打印_打印进度条(当前值, 总值)
            time.sleep(0.1)  # 模拟进度
    """
    try:
        百分比 = 当前值 / 总值
        完成长度 = int(长度 * 百分比)
        进度 = "█" * 完成长度 + "-" * (长度 - 完成长度)
        sys.stdout.write(f"\r|{进度}| {当前值}/{总值} ({百分比:.2%})")
        sys.stdout.flush()
        if 当前值 >= 总值:
            print()  # 完成后换行
        return True
    except Exception as e:
        print(f"打印时出现异常: {e}")
        return False
