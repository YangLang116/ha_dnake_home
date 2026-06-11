---
name: dnake-home-skill
description: 通过狄耐克本地网关查询和控制智能家居设备。适用于列出设备、读取状态，或操作灯、窗帘、空调、地暖、新风、空气盒子传感器设备的任务。
---

# 狄耐克智能家居控制

使用本技能通过本地网关查询设备、读取状态和发送控制命令。

## 快速流程

1. 确认连接配置：网关 IP、用户名、密码必须来自已保存配置或用户明确提供，不要猜测。
2. 需要直接访问网关时，使用 `scripts/dnake_gateway.js`。
3. 操作设备前，先运行 `devices` 或 `states` 获取设备名、设备编号 `nm`、通道 `ch` 和类型 `ty`。
4. 按用户给出的设备名、房间、设备类型或明确编号匹配目标设备；无法唯一匹配时先询问。
5. 能读取状态时，控制前后都读取状态。只有响应包含 `result: "ok"` 且复查合理时，才报告操作成功。
6. 多设备或多步骤操作逐项记录结果，分别说明成功、失败。

## 连接配置

- 用户提供网关 IP 后，运行 `node scripts/dnake_gateway.js config set-host <gateway_ip>` 保存。
- 用户提供账号密码后，运行 `node scripts/dnake_gateway.js config set-credentials <username> <password>` 保存。
- 需要查看保存状态时，运行 `node scripts/dnake_gateway.js config show`；不要在回复中明文复述密码。
- 后续命令可以省略 `--host`、`--username`、`--password`，脚本会读取本地配置。
- 如果没有已保存 IP、用户名或密码，先询问用户。
- 如果接口返回 404、连接失败、超时、无法解析 JSON，或之前可用的接口突然不可用，提醒用户网关 IP 可能已经变化。
- 如果用户确认新 IP，重新执行 `config set-host <gateway_ip>` 保存。

## 常用命令

```bash
node scripts/dnake_gateway.js config show
node scripts/dnake_gateway.js devices
node scripts/dnake_gateway.js states
node scripts/dnake_gateway.js read --dev-no <n> --dev-ch <n>
```

控制命令：

```bash
node scripts/dnake_gateway.js light --dev-no <n> --dev-ch <n> --power on|off
node scripts/dnake_gateway.js cover --dev-no <n> --dev-ch <n> --position <0..100>
node scripts/dnake_gateway.js cover --dev-no <n> --dev-ch <n> --stop
node scripts/dnake_gateway.js aircon --dev-no <n> --dev-ch <n> --power on|off
node scripts/dnake_gateway.js aircon --dev-no <n> --dev-ch <n> --temperature <16..32>
node scripts/dnake_gateway.js aircon --dev-no <n> --dev-ch <n> --mode <1..4>
node scripts/dnake_gateway.js aircon --dev-no <n> --dev-ch <n> --fan <0..2>
node scripts/dnake_gateway.js aircon --dev-no <n> --dev-ch <n> --swing <0..3>
node scripts/dnake_gateway.js floor-heat --dev-no <n> --dev-ch <n> --power on|off
node scripts/dnake_gateway.js floor-heat --dev-no <n> --dev-ch <n> --temperature <16..35>
node scripts/dnake_gateway.js floor-heat --dev-no <n> --dev-ch <n> --mode <0..1>
node scripts/dnake_gateway.js fresh-air --dev-no <n> --dev-ch <n> --power on|off
node scripts/dnake_gateway.js fresh-air --dev-no <n> --dev-ch <n> --speed <0..3>
```

使用 `--dry-run` 只预览路由报文，不发送控制命令；不要把 dry-run 说成操作成功。

## 设备匹配

- 设备列表来自 `/smart/speDev.info`，常用字段为 `na`、`nm`、`ch`、`ty`。
- 状态读取和控制使用 `devNo = nm`、`devCh = ch`。
- 控制前需要网关路由名：`/smart/iot.info` 返回 `iotDeviceName` 和 `gwIotName`，脚本会自动处理。
- 需要设备类型、状态字段、命令映射、取值范围或 JSON 示例时，读取 `references/protocol.md`。

## 安全规则

- 不要臆造 `devNo` 或 `devCh`，必须来自设备列表、状态结果或用户明确提供。
- 遵守取值范围：窗帘位置 `0..100%` 或原始 `level 0..254`，空调温度 `16..32`，地暖温度 `16..35`，新风风速 `0..3`。
- 传感器只读，不发送控制命令。
- 除非用户明确要求自动化循环，否则不要对窗帘和暖通设备连续快速发送命令。
- 失败时说明 HTTP 错误、连接错误、参数越界、响应缺少 `result: "ok"`，或状态复查不一致。

## 汇报格式

- 对每个设备分别汇报：设备、操作、成功/失败、证据。
- 成功证据优先使用响应中的 `result: "ok"` 和控制后的状态。
- 批量操作中即使部分成功，也列出失败项；不要用笼统的“已完成”代替明细。
