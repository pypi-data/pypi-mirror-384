# qinglong-openapi

青龙api的python SDK (修复版本)

这是 [qinglongapi](https://github.com/yuxian158/qinglong-api) 的修复版本，主要修复了port参数被错误写成post的bug。

## 修复内容

- ✅ 修复了所有模块中port参数被错误写成post的问题
- ✅ 版本：0.0.1
- ✅ 保持与原项目完全兼容

## 安装

```bash
pip install qinglong-openapi
```

## 原始项目

原始项目地址：https://github.com/yuxian158/qinglong-api

## 文档

具体文档

https://yuxian158.github.io/qinglong-api/

所有模块使用方法大同小异，以环境变量模块为例:

```
from qlapi import qlenv

ql_env = qlenv(
    url="12.22.43.23",   #青龙面板IP地址(不包含http://)
    port=5700,			#青龙面板端口
    client_id="admin",  # 青龙面板openapi登录用户名
    client_secret="abcdefg_", # 青龙面板openapi登录密码
)
ql_env.list()
```

青龙api文档

https://qinglong.ukenn.top/#/

很多还没有完善，欢迎pr
