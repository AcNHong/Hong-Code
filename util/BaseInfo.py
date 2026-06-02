import platform

def get_platform_info():
    """获取用于注入提示词的系统平台信息"""
    info = f"os and arch info:\nos:{platform.system()}\narch:{platform.machine()}"
    return info


# print(get_platform_info())