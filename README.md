# Introduction

This project uses nonebot2 and python 3.9.6, please refer to https://nonebot.dev/docs/quick-start for setup.

## 操作步骤

1. 安装qq
2. 参考 https://github.com/LiteLoaderQQNT/LiteLoaderQQNT 给 qq 安装 qqnt。可以去 https://github.com/Mzdyl/LiteLoaderQQNT_Install/releases 里找最新的一键安装方式
3. 参考 https://github.com/LLOneBot/LLOneBot 安装 onebot 插件
4. 参考 https://github.com/nonebot/nonebot2 初始化环境。一般来说就是选 python 3.12 开一个虚拟环境，安装必要库最后用 `nb init` 初始化（初始化的时候随便初始化一个异名插件就可以，主要需要初始化过程中安装的各种东西）
5. 在 llonebot 里建立反向ws，地址用 `ws://127.0.0.1:8080/onebot/v11/ws`。正向的端口用 6700 即可。