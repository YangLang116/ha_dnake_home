# DNake Assistant 狄耐克集成

狄耐克集成是一个非官方提供支持的 Home Assistant 的集成组件，它可以让您在 Home Assistant 中使用狄耐克 IoT 智能设备。

## 安装

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

## 支持设备类型

- 灯光 (Light)
- 窗帘 (Cover)
- 空调 (Climate)

