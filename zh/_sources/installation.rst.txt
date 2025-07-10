
安装
======

1. 克隆仓库并安装依赖
.. code-block:: bash
  :linenos:
  git clone https://github.com/HBcao233/mtgbot
  python -m pip install -r requirement.txt
  
  # 安装 ffmpeg (推荐)
  pkg install ffmpeg
  yum install ffmpeg
 
2. 覆盖 telethon 部分文件, 以实现如 解析<blockquote expandable></blockquote> 等功能
 
.. code-block:: bash
  :linenos:
  # 查看包安装目录 (显示信息中的 Location 项)
  pip show telethon
  cp -r libs/telethon <site-package-location>
