
```bash
cd docs
# 输出 html
sphinx-build -b html -D language='zh' source build/locale/zh/
sphinx-build -b html -D language='en' source build/locale/en/

# 生成 zh 语言文件
sphinx-build -b gettext source build/locale/gettext
```