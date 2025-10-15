from typing import Any, List, Optional
from pathlib import Path


def get_user_project_root() -> str:
    """
    获取使用本库的项目的最外层目录路径（字符串格式）

    1. 首先尝试获取主脚本所在目录
    2. 然后向上查找常见的项目标识文件
    3. 返回字符串形式的绝对路径
    """
    # 获取主模块的目录作为起点
    try:
        main_module = __import__("__main__")
        if hasattr(main_module, "__file__") and main_module.__file__:
            start = Path(main_module.__file__).parent
        else:
            start = Path.cwd()
    except Exception:
        start = Path.cwd()

    # 常见的项目根目录标识
    marker_files = ("pyproject.toml", "setup.py", "requirements.txt")
    marker_dirs = (".git", ".hg", ".svn")

    # 从起点向上遍历目录树
    for parent in [start, *start.parents]:
        # 检查是否存在项目标识文件或目录
        if any((parent / marker).exists() for marker in marker_files) or any(
            (parent / marker).is_dir() for marker in marker_dirs
        ):
            return str(parent.resolve())

    # 如果没有找到标识，返回主脚本所在目录或当前工作目录
    return str(start.resolve())


# 使用示例
if __name__ == "__main__":
    root_path = get_user_project_root()
    print(f"项目根目录: {root_path}")  # 输出字符串路径


def pre_condition(condition: bool, msg: str):
    """
        判断条件是否发生了异常

    :param bool condition: 条件
    :param str msg: 信息
    :raises ModelExcption: 异常
    """
    if not condition:
        raise Exception(msg)


def pre_condition_data_err(condition: bool, msg: str):
    pre_condition(condition, f"数据异常:{msg}")


def is_str_empty_in_list(v: List[str]) -> bool:
    """
    判断列表中是否有空字符串

    :param v:
    :return:
    """
    return any(map(is_empty, v))


def is_empty(string: Optional[str]) -> bool:
    if string is None:
        return True
    if string.rstrip() == "":
        return True

    return False


def is_not_empty(string: Optional[str]) -> bool:
    return not is_empty(string)


def to_response(code: int, msg: str, data: Any):
    """
    按照标准的数据结构进行返回信息

    :param int code: 成功与否的标识
    :param str msg: 提示的内容信息
    :param Any data: 模型实际返回的消息
    """
    return {"code": code, "msg": msg, "data": data}


def is_segments_crossing_1d(segment1, segment2, safe_d=0):
    """
    判断两个一维线段是否交叉
    :param segment1: 第一个线段 [start1, end1]
    :param segment2: 第二个线段 [start2, end2]
    :return: 如果交叉返回 True，否则返回 False
    """
    # 确保线段的起点和终点是有序的 (起点 <= 终点)
    start1, end1 = sorted(segment1)
    start2, end2 = sorted(segment2)

    # 判断两个区间是否有重叠
    return max(start1, start2) - safe_d <= min(end1, end2)
