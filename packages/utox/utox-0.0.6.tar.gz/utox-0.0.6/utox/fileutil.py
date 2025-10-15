def read_file(path: str, cls):
    """
    读取文件

    :return _type_: 返回读取成功的数据对象
    """
    with open(path, encoding="UTF-8", mode="r") as f:
        con: str = f.read()
        dataObj = cls.model_validate_json(con)
    return dataObj


def write_file(path: str, data: str):
    """
    写入文件

    :return _type_:
    """
    with open(path, encoding="UTF-8", mode="w") as f:
        f.write(data)
    return True
