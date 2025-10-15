from pathlib import Path
import configparser


class IniUtil:
    # 获取项目根目录（假设当前文件位于项目结构中）

    def __init__(self, path: str):
        self._ROOT_DIR = Path(path)

    def _read_ini(self) -> configparser.ConfigParser:
        """读取 ini 文件，返回 ConfigParser 对象"""
        full_path = self._ROOT_DIR
        if not full_path.exists():
            raise FileNotFoundError(f"INI 文件不存在: {full_path}")

        config = configparser.ConfigParser()
        config.read(full_path, encoding="utf-8")
        return config

    def _write_ini(self, config: configparser.ConfigParser):
        """写入 ConfigParser 对象到指定的 ini 文件"""
        full_path = self._ROOT_DIR
        with open(full_path, "w", encoding="utf-8") as f:
            config.write(f)

    def get_value(self, section: str, option: str) -> str:
        """获取某个选项的值"""
        config = self._read_ini()
        if not config.has_option(section, option):
            raise KeyError(f"找不到配置项 [{section}]{option}")
        return config.get(section, option)

    def get_int(self, section: str, option: str) -> int:
        """获取某个选项的整数值"""
        return int(self.get_value(section, option))

    def get_float(self, section: str, option: str) -> float:
        """获取某个选项的浮点数值"""
        return float(self.get_value(section, option))

    def set_value(self, section: str, option: str, value: str):
        """设置某个选项的值，并保存"""
        config = self._read_ini()
        if not config.has_section(section):
            config.add_section(section)

        config.set(section, option, value)
        self._write_ini(config)
