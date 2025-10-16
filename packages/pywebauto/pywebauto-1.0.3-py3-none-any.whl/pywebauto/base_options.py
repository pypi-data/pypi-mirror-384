"""base_options.py
对web自动化的基础配置进行封装
1. webdriver路径和chrom浏览器的封装
2. 对浏览器选项进行封装
"""
# 第三方库
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

class BaseOptions:
    def __init__(self, chromedriver_path: str = r"chromedriver.exe", chrome_path: str = r"C:\Program Files\Google\Chrome\Application"):
        """
        web自动化的基础配置进行封装
        :param chromedriver_path: 谷歌驱动路径，默认当前目录下
        :param chrome_path: 谷歌浏览器位置，默认系统的C:\Program Files\Google\Chrome\Application
        """
        # 创建Chrome浏览器选项实例
        self.options = webdriver.ChromeOptions()
        # 添加无沙盒模式参数（常用于Linux环境或容器环境）
        self.options.add_argument("--no-sandbox")
        # 禁用或隐藏一些 Chrome 浏览器自带的弹出功能，以防止它们干扰测试流程。
        # 偏好设置
        self.prefs = {
            'profile.default_content_setting_values': {  # 控制网站的通知权限
                'notifications': 2  # 隐藏chromedriver的通知
            },
            'credentials_enable_service': False,  # 禁用 Chrome 自动保存密码或提示保存密码的功能（凭证管理服务）
            'profile.password_manager_enabled': False  # 控制 Chrome 是否启用内置的密码管理器（进一步确保 禁用与密码相关的弹出窗口或功能）
        }
        self.options.add_experimental_option('prefs', self.prefs)   # 启用偏好设置
        # 禁用自动化检测提示
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 禁用 GPU 硬件加速，规避一些与图形处理相关的已知 Bug 或兼容性问题，尤其是在无头模式（无界面）
        self.options.add_argument('--disable-gpu')
        # 禁用了 CPU 上的备用渲染方案
        self.options.add_argument('--disable-software-rasterizer')
        # 这通常用于阻止 "打印预览" 或 "另存为" 窗口，但对链接点击效果不佳
        self.options.add_argument("--disable-popup-blocking")
        # 禁用扩展（扩展会增加测试用的资源）
        self.options.add_argument("--disable-extensions")
        # 创建服务对象（传入谷歌webdriver驱动路径）
        self.service = Service(executable_path=fr"{chromedriver_path}")
        # 谷歌浏览器位置
        self.options.binary_location  = fr"{chrome_path}"

    def silent(self) -> bool:
        """
        开启静音参数
        :return: True
        """
        # 静音处理
        self.options.add_argument("--mute-audio")
        return True


    def running_in_the_background(self) -> bool:
        """在后台运行（无头模式）
        :return: True
        """
        # 添加无头模式，不渲染图形界面
        self.options.add_argument("--headless=new")
        # # 添加大小（无头可能很小）
        # self.options.add_argument("--window-size=1920,1080")
        return True

    def remove_image(self) -> bool:
        """
        移除图片资源加载
        :return:True
        """
        self.prefs["profile.managed_default_content_settings.images"] = 2
        return True

    def remove_css(self) -> bool:
        """
        移除css样式加载(移除后可能导致网页结构错乱)
        :return: True
        """
        self.options.add_argument("--autoplay-policy=user-gesture-required")
        return True