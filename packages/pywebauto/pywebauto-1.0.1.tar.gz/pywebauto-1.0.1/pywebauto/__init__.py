"""
封装好基础行为和浏览器常用选项
"""
__author__ = "yandifei"
__package__ = "pywebauto"
__version__ = "1.0.1"
__author_email__ = "3058439878@qq.com"
__url__ = "https://github.com/yandifei/pywebauto"         # 项目主页
__license__ = "MIT"

# 导入核心类，使得用户可以直接通过包名访问
from .base_actions import BaseActions
from .base_options import BaseOptions
from .cookie_manager import CookieManager

#  定义 __all__，控制 from pywebauto import * 的行为
__all__ = ["BaseActions","BaseOptions","CookieManager",]
