# Dnake Home 网关协议速查

本引用整理了狄耐克本地网关常用 HTTP API、设备类型、状态字段和控制命令。

## 访问方式

- HTTP 基础地址：`http://<gateway_ip>`
- 网关 IP 必须由用户提供或从技能保存的配置读取。
- HTTP 账号和密码必须由用户提供或从用户本地配置读取，不要猜测默认凭据。
- 所有 HTTP 请求使用 Basic Auth 和 JSON 头：
  - `Accept: application/json`
  - `Content-Type: application/json`
  - `Authorization: Basic <base64(username:password)>`

## 查询接口

| 用途 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| 查询网关路由名 | GET | `/smart/iot.info` | 返回 `iotDeviceName` 和 `gwIotName`。 |
| 查询设备列表 | GET | `/smart/speDev.info` | 返回 `dl`，设备含 `na`、`nm`、`ch`、`ty`。 |

## 路由 POST 包

状态读取和设备控制都发送到：

```text
POST /route.cgi?api=request
```

外层包格式：

```json
{
  "fromDev": "iotDeviceName",
  "toDev": "gwIotName",
  "data": {
    "uuid": "random-request-id",
    "action": "readDev",
    "devNo": 16388,
    "devCh": 0
  }
}
```

当前集成会在 POST 前自动生成 `uuid`。

## 设备类型

| 设备 | `ty` / `devType` |
| --- | ---: |
| 灯 | `256` |
| 窗帘 | `514` |
| 空调 | `16640` |
| 地暖 | `17169` |
| 新风 | `16924` |
| 空气盒子 | `18692` |

设备列表字段：

- `na`：显示名称。
- `nm`：设备编号，控制时作为 `devNo`。
- `ch`：设备通道，控制时作为 `devCh`。
- `ty`：设备类型。

状态字段：

- `devType`、`devNo`、`devCh`：用于把状态匹配到设备。
- `state`：灯开关状态，`1` 为开，`0` 为关。
- `level`：窗帘开合程度，范围 `0..254`；对用户展示时通常换算为 `0..100%`。
- `powerOn`：空调、地暖、新风电源状态，`1` 为开，`0` 为关。
- `mode`：空调或地暖模式。
- `speed`：空调或新风风速。
- `swing`：空调摆风状态。
- `tempIndoor`：室内温度。
- `tempDesire`：目标温度。
- `temp`：空气盒子温度原始值，除以 `100`。
- `humi`：湿度原始值，除以 `100`。
- `pm2.5`：PM2.5 浓度。

## 读取状态

读取全部设备状态：

```json
{
  "action": "readAllDevState"
}
```

读取单个设备状态：

```json
{
  "action": "readDev",
  "devNo": 16388,
  "devCh": 0
}
```

## 控制命令

所有控制都包含：

```json
{
  "action": "ctrlDev",
  "devNo": 32,
  "devCh": 1
}
```

### 灯

| 操作 | 字段 |
| --- | --- |
| 开灯 | `"cmd": "on"` |
| 关灯 | `"cmd": "off"` |

### 窗帘

| 操作 | 字段 |
| --- | --- |
| 停止 | `"cmd": "stop"` |
| 设置位置 | `"cmd": "level"`，`"level": 0..254` |

位置换算：

- 百分比转 Dnake level：`int((percent / 100) * 254)`。
- Dnake level 转百分比：`int((level / 254) * 100)`。

### 空调

使用 `"cmd": "airCondition"`。

| 操作 | `oper` | `param` |
| --- | --- | --- |
| 开机 | `powerOn` | 省略 |
| 关机 | `powerOff` | 省略 |
| 设置模式 | `setMode` | `1` 制热，`2` 制冷，`3` 送风，`4` 除湿 |
| 设置风速 | `setFlow` | `0` 低速，`1` 中速，`2` 高速 |
| 设置摆风 | `setSwing` | `0` 关闭，`1` 摆动，`2` 横向，`3` 纵向 |
| 设置温度 | `setTemp` | `16..32` |

### 地暖

使用 `"cmd": "airHeater"`。

| 操作 | `oper` | `param` |
| --- | --- | --- |
| 开机 | `powerOn` | 省略 |
| 关机 | `powerOff` | 省略 |
| 设置模式 | `setMode` | `0` 水暖，`1` 电暖 |
| 设置温度 | `setTemp` | `16..35` |

### 新风

使用 `"cmd": "airFresh"`。

| 操作 | `oper` | `param` |
| --- | --- | --- |
| 开机 | `powerOn` | 省略 |
| 关机 | `powerOff` | 省略 |
| 设置风速 | `setFlow` | `0` 低速，`1` 中速，`2` 高速，`3` 强劲 |

新风百分比映射建议：

- `<=25%` -> `0`
- `<=50%` -> `1`
- `<=75%` -> `2`
- `>75%` -> `3`
