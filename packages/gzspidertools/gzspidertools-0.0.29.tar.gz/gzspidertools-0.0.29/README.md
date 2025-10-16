概述
=======
   一句话介绍：用于扩展 Scrapy 功能来解放双手。


安装
=======

   可以直接输入以下命令：

.. code:: bash

   pip install gzspidertools

-------------------------------

   可选安装1，安装数据库相关的所有依赖：

.. code:: bash

   pip install gzspidertools[database]

-----------------------------------------

   可选安装2，通过以下命令安装所有依赖：

.. code:: bash

   pip install gzspidertools[all]

注：详细的安装介绍请查看 `安装指南`_。

用法
=======
   开发人员只需根据命令生成示例模板，再配置相关设置即可。

   # 查看库版本
   gzcmd version

   # 创建项目
   gzcmd startproject <project_name>

   # 进入项目根目录
   cd <project_name>

   # 替换(覆盖)为真实的配置 .conf 文件：
   # 这里是为了演示方便，正常情况是直接在 VIT 中的 .conf 文件填上你需要的配置即可
   cp /root/mytemp/.conf DemoSpider/VIT/.conf

   # 生成爬虫脚本
   gzcmd genspider <spider_name> <example.com>

   # 运行脚本
   scrapy crawl <spider_name>
   # 注：也可以使用 gzcmd crawl <spider_name>
=======

## uv

uv 安装更新
> pip install --upgrade uv

uv sync


## build

> uv build 

> uv publish 
