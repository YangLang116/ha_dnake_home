# 狄耐克网关 API 说明

本文档整理当前集成使用到的狄耐克本地网关接口。示例中的 IP、设备编号、通道号和网关路由标识需要以实际环境返回值为准。

## 一、网关访问

| 类型 | 地址 | 默认账密 |
|:---|:---|:---|
| HTTP | `http://192.168.1.2` | `admin` / `123456` |
| Telnet | `telnet 192.168.1.2 9900` | `root` / `1234321` |

## 二、认证

所有 HTTP 请求都需要携带 Basic Auth。

| Header | 值 |
|:---|:---|
| `Accept` | `application/json` |
| `Content-Type` | `application/json` |
| `Authorization` | `Basic <base64(username:password)>` |

`Authorization` 的生成方式可参考代码中的 `utils.encode_auth`。

## 三、查询接口

查询接口使用 `GET` 请求。

| 用途 | 地址 | 说明 |
|:---|:---|:---|
| 获取网关路由信息 | `/smart/iot.info` | 返回 `iotDeviceName` 和 `gwIotName`，用于后续控制请求的 `fromDev` / `toDev` |
| 获取设备列表 | `/smart/speDev.info` | 返回设备数组 `dl`，其中 `nm` 为设备编号，`ch` 为设备通道，`ty` 为设备类型 |
| 获取场景列表 | `/smart/speScene.info` | 返回网关场景列表 |
| 获取场景详情 | `/smart/scene/{nm}.json` | `nm` 来自场景列表 |

## 四、控制请求格式

设备状态读取和控制统一通过 `POST /route.cgi?api=request` 发送。

外层字段：

| 字段 | 说明 |
|:---|:---|
| `fromDev` | 来自 `/smart/iot.info` 的 `iotDeviceName` |
| `toDev` | 来自 `/smart/iot.info` 的 `gwIotName` |
| `data` | 具体动作参数 |

`data` 通用字段：

| 字段 | 说明 |
|:---|:---|
| `uuid` | 随机请求 ID |
| `action` | 动作类型，常用值为 `readAllDevState`、`readDev`、`ctrlDev` |
| `devNo` | 设备编号，对应设备列表中的 `nm` |
| `devCh` | 设备通道，对应设备列表中的 `ch` |

通用示例：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195531",
    "action": "readDev",
    "devNo": 16388,
    "devCh": 0
  }
}
```

## 五、设备类型

当前基础集成识别以下设备类型：

| 设备 | `ty` / `devType` | Home Assistant 平台 |
|:---|:---|:---|
| 灯具 | `256` | `light` |
| 窗帘 | `514` | `cover` |
| 空调 | `16640` | `climate` |
| 地暖 | `17169` | `climate` |
| 新风 | `16924` | `fan` |
| 空气盒子 | `18692` | `sensor` |

## 六、读取状态

读取所有设备状态：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195531",
    "action": "readAllDevState"
  }
}
```

读取指定设备状态：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195532",
    "action": "readDev",
    "devNo": 16388,
    "devCh": 0
  }
}
```

常见状态字段：

| 字段 | 说明 |
|:---|:---|
| `devType` | 设备类型 |
| `devNo` | 设备编号 |
| `devCh` | 设备通道 |
| `state` | 灯具开关状态，`1` 为开，`0` 为关 |
| `level` | 窗帘开合程度，范围 `0 ~ 254` |
| `powerOn` | 空调、地暖、新风电源状态，`1` 为开，`0` 为关 |
| `mode` | 空调或地暖模式 |
| `speed` | 空调或新风风速 |
| `swing` | 空调摆风状态 |
| `tempIndoor` | 室内温度 |
| `tempDesire` | 目标温度 |
| `temp` | 空气盒子温度原始值，集成按 `/100` 转换为摄氏度 |
| `humi` | 空气盒子湿度原始值，集成按 `/100` 转换为百分比 |
| `pm2.5` | PM2.5 浓度 |

## 七、控制命令

所有控制命令的 `action` 均为 `ctrlDev`。

### 灯具

| 操作 | `cmd` |
|:---|:---|
| 开灯 | `on` |
| 关灯 | `off` |

示例：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195533",
    "action": "ctrlDev",
    "cmd": "on",
    "devNo": 32,
    "devCh": 1
  }
}
```

### 窗帘

| 操作 | 字段 |
|:---|:---|
| 停止 | `cmd: stop` |
| 设置开合程度 | `cmd: level`，`level: 0 ~ 254` |

示例：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195534",
    "action": "ctrlDev",
    "cmd": "level",
    "level": 128,
    "devNo": 32,
    "devCh": 1
  }
}
```

### 空调

`cmd` 固定为 `airCondition`。

| 操作 | `oper` | `param` |
|:---|:---|:---|
| 开机 | `powerOn` | - |
| 关机 | `powerOff` | - |
| 设置模式 | `setMode` | `1` 制热，`2` 制冷，`3` 送风，`4` 除湿 |
| 设置风速 | `setFlow` | `0` 低速，`1` 中速，`2` 高速 |
| 设置风向 | `setSwing` | `0` 关闭摆动，`1` 开启摆动，`2` 横向摆风，`3` 纵向摆风 |
| 设置温度 | `setTemp` | `16 ~ 32` |

示例：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195535",
    "action": "ctrlDev",
    "cmd": "airCondition",
    "oper": "setTemp",
    "param": 26,
    "devNo": 16388,
    "devCh": 0
  }
}
```

### 地暖

`cmd` 固定为 `airHeater`。

| 操作 | `oper` | `param` |
|:---|:---|:---|
| 开机 | `powerOn` | - |
| 关机 | `powerOff` | - |
| 设置模式 | `setMode` | `0` 水暖，`1` 电暖 |
| 设置温度 | `setTemp` | `16 ~ 35` |

示例：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195536",
    "action": "ctrlDev",
    "cmd": "airHeater",
    "oper": "setMode",
    "param": 0,
    "devNo": 16395,
    "devCh": 0
  }
}
```

### 新风

`cmd` 固定为 `airFresh`。

| 操作 | `oper` | `param` |
|:---|:---|:---|
| 开机 | `powerOn` | - |
| 关机 | `powerOff` | - |
| 设置风速 | `setFlow` | `0` 低速，`1` 中速，`2` 高速，`3` 强劲 |

示例：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "d676538762ae4a00afdd41fdb0195537",
    "action": "ctrlDev",
    "cmd": "airFresh",
    "oper": "setFlow",
    "param": 2,
    "devNo": 16385,
    "devCh": 0
  }
}
```
