# pywebauto
基于selenium的自动化测试框架和Page Object (PO) 模型，内置工具快速进行Python Web UI 自动化测试和web自动化脚本开发
- 包含内置工具快速构建项目结构
- 对封装selenium进行二次封装
- cookie注入的封装和处理
- requests的简单封装

# 使用方式
```bash
pip install pywebauto
```
- 依赖的第三方库
```
pytest>=8.3.5
selenium>=4.36.0
```

# 包的架构
`base_actions.py`对应`BaseActions`类，基础行为封装
`base_options.py`对应`BaseOptions`类，基础选项封装
`cookie_manager.py`对应`CookieManager`类，cookies管理封装

# 无法实现的封装
在selenium中没有鼠标中键的操作，更准确的说是绝大多数现代浏览器都没有这个操作，对于类似于`<a>`标签实行鼠标中建实际上是进行了一次右击罢了。deepseek给的`actions.click(element, button='middle').perform()`这个方法是错的，旧版早就移除了。