# DNake Assistant 狄耐克集成

狄耐克集成是一个非官方提供支持的 Home Assistant 的集成组件，它可以让您在 Home Assistant 中使用狄耐克 IoT 智能设备。

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
  - 查看室内温度
  - 设置温度：16 ~ 32 ℃
  - 设置模式：制冷、制热、送风、除湿
  - 设置风速：低速、中速、高速

## 二、安装

> Home Assistant 版本要求：
>
> - Core $\geq$ 2024.4.4
> - Operating System $\geq$ 13.0

### 方法 1：使用 git clone 命令从 GitHub 下载

```bash
cd config
git clone https://github.com/YangLang116/ha_dnake_home.git
cd ha_dnake_home
./install.sh /config
```

### 方法 2: [HACS](https://hacs.xyz/)

HACS > 右上角三个点 > Custom repositories > Repository: https://github.com/YangLang116/ha_dnake_home.git & Category or
Type:
Integration > ADD > 点击 HACS 的 New 或 Available for download 分类下的 Dnake Home ，进入集成详情页  > DOWNLOAD

## 三、配置
- 网关：智能家居网关ip地址
- 登录账密：网关登录用户账密，默认: admin/123456
- 状态刷新间隔: 全量刷新设备状态的时间间隔

## 四、项目说明与支持

- 稳定基础版本： 本项目提供的是经过验证的、稳定运行的Dnake设备与Home Assistant集成**基础**代码。
- 有偿服务选项： 如果您需要专业的**部署协助**或针对特定场景的**定制化开发**服务，本人可提供有偿的技术支持，联系[1004145468@qq.com](mailto:1004145468@qq.com) 。
- 问题处理优先度说明： 为了能持续维护和优化这个基础项目，我将优先处理和支持通过上述有偿服务渠道提出的需求或深度适配问题。对于基础版本使用中遇到的、特别是涉及特定环境深度适配的问题，我可能无法提供详尽的免费支持，敬请理解。

