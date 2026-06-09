# DNake Assistant 狄耐克集成

狄耐克集成是一个非官方的 Home Assistant 自定义集成，用于将狄耐克 IoT 智能家居设备接入 Home Assistant。

## 一、特性

- 灯具
    - 开灯
    - 关灯

- 窗帘
    - 打开窗帘
    - 关闭窗帘
    - 控制窗帘开合程度
    - 停止窗帘

- 空调面板
    - 开关空调
    - 查看室内温度
    - 设置温度：16 ~ 32 ℃
    - 设置模式：制冷、制热、送风、除湿
    - 设置风速：低速、中速、高速
    - 设置风向：横向摆风、纵向摆风

- 地暖设备
    - 开关地暖
    - 查看室内温度
    - 设置温度：16 ~ 35 ℃
    - 设置模式：水暖、电暖

- 新风系统
    - 开关新风系统
    - 设置风速：低速、中速、高速、强劲

- 空气盒子
    - 查看温度
    - 查看湿度
    - 查看 PM2.5

## 二、安装

> Home Assistant 版本要求：
>
> - Core >= 2024.4.4
> - Operating System >= 13.0

1. 打开 [HACS](https://hacs.xyz/) > 右上角三个点 > Custom repositories。
2. 填写仓库地址 `https://github.com/YangLang116/ha_dnake_home.git`，类型选择 `Integration`，然后点击 `ADD`。
3. 在 HACS 的 `New` 或 `Available for download` 中打开 `Dnake Home`，进入集成详情页并点击 `DOWNLOAD`。
4. 重启 Home Assistant。

## 三、配置

- 网关：智能家居网关 IP 地址。
- 登录账密：网关登录用户名和密码，默认通常为 `admin` / `123456`。
- 状态刷新间隔：全量刷新设备状态的时间间隔。

## 四、项目说明与支持

- 本项目提供的是经过验证、稳定运行的 Dnake 设备接入 Home Assistant 基础代码。
- 设备协议和实际项目环境可能存在差异，不同网关版本或设备类型可能需要额外适配。
- 接口协议整理见 [docs/api.md](docs/api.md)。
