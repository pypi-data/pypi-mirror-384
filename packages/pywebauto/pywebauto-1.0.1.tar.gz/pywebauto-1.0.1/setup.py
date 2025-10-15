from setuptools import setup, find_packages

# 临时读取pywebauto版本号等元数据，避免执行相对导入
import re
def get_metadata(name):
    # 假设 __init__.py 在 pywebauto/ 目录下
    with open(f'pywebauto/__init__.py', 'r', encoding='utf-8') as f:
        # 使用正则表达式安全地提取所需的值
        match = re.search(r"^__%s__\s*=\s*['\"]([^'\"]*)['\"]" % name, f.read(), re.M)
        if match:
            return match.group(1)
        raise RuntimeError(f"Unable to find __%s__ string." % name)
# 获得元数据
__package__ = get_metadata("package")
__version__ = get_metadata("version")
__author__ = get_metadata("author")
__author_email__ = get_metadata("author_email")
__url__ = get_metadata("url")
__license__ = get_metadata("license")

# 加载readme文件内容
with open("README.md","r",encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name=__package__,                                     # 包名(PyPI注册名)
    version=__version__,                                    # 版本号
    author=__author__,                                  # 作者
    author_email=__author_email__,                   # 邮箱
    description="web自动化开发及测试",                     # 简短描述
    long_description=long_description,                  # 详细说明
    long_description_content_type="text/markdown",      # 详细说明使用标记类型
    url=__url__,          # 项目主页
    license=__license__,                                      # SPDX许可证表达式（新增，用于解决警告）
    # 需要打包的部分，自动发现包目录(排除不需要打包的文件)
    packages=find_packages(exclude=[".idea", ".git", ".gitignore", "pytest学习"]),
    # package_dir={"": "web自动化测试"},  # 设web自动化测试目录为根目录
    # package_data={
    #         "包名": [
    #             "包中的文件夹/*",  # 分词必要的文件
    #             "包中的文件夹/*",    # 提示库文件
    #         ]
    # },
    classifiers=[               # 分类标签（可选）
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License", 已经过时了
        "Operating System :: Microsoft :: Windows :: Windows 11"
    ],
    python_requires=">=3.8",                      # 项目支持的Python版本
    install_requires=[
        "pytest>=8.4.2",
        "selenium>=4.36.0"
    ],               # 项目必须的依赖
    include_package_data=True                       # 是否包含非Python文件（如资源文件）
)