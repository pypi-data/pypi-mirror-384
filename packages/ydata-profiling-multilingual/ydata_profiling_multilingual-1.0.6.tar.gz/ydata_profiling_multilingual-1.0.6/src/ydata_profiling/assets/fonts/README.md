# 字体文件说明
 
本目录包含ydata-profiling的字体资源文件。
 
## 字体文件
 
- `simhei.ttf`: 黑体字体，用于中文字符显示
 
## 使用说明
 
字体文件会自动被字体管理器加载和使用。用户可以通过配置启用中文字体支持：
 
```python
profile = ProfileReport(df, plot={"font": {"chinese_support": True}})
```
## 许可证

请确保字体文件的使用符合相应的许可证要求。
