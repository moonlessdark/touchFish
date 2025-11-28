import sys
import os
import configparser


def get_resource_path():
    """获取资源文件路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        return sys._MEIPASS
    else:
        # 开发时的路径
        return os.path.dirname(os.path.abspath(__file__))


def load_config(file: str):
    """加载配置文件"""
    base_path = get_resource_path()
    # config_file = os.path.join(base_path, 'config.ini')
    config_file = os.path.join(base_path, file)
    # print("__------___" + config_file)

    if not os.path.exists(config_file):
        # print(f"配置文件不存在: {config_file}")
        return None
    return config_file


# 主程序中使用
if __name__ == "__main__":
    config = load_config()
    if config:
        # 使用配置
        print("配置加载成功")
