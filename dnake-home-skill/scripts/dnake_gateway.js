#!/usr/bin/env node
"use strict";

const http = require("http");

const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");

const CONFIG_PATH =
  process.env.DNAKE_HOME_SKILL_CONFIG ||
  path.join(os.homedir(), ".codex", "dnake-home-skill", "config.json");

function stable(value) {
  if (Array.isArray(value)) {
    return value.map(stable);
  }
  if (value && typeof value === "object" && value.constructor === Object) {
    return Object.keys(value)
      .sort()
      .reduce((result, key) => {
        result[key] = stable(value[key]);
        return result;
      }, {});
  }
  return value;
}

function printJson(value) {
  process.stdout.write(`${JSON.stringify(stable(value), null, 2)}\n`);
}

function fail(message, exitCode = 1) {
  const error = new Error(message);
  error.exitCode = exitCode;
  throw error;
}

function boundedInt(name, value, minimum, maximum) {
  if (value < minimum || value > maximum) {
    fail(`${name} 必须在 ${minimum}..${maximum} 范围内`);
  }
  return value;
}

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    return {};
  }
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  } catch (error) {
    if (error instanceof SyntaxError) {
      fail(`配置文件不是合法 JSON: ${CONFIG_PATH}: ${error.message}`);
    }
    throw error;
  }
}

function saveConfig(config) {
  fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
  fs.writeFileSync(CONFIG_PATH, `${JSON.stringify(stable(config), null, 2)}\n`, "utf8");
}

function maskedConfig(config) {
  return Object.assign({}, config, config.password ? { password: "******" } : {});
}

function resolveHost(host, dryRun = false) {
  if (host) {
    return host;
  }
  const savedHost = loadConfig().host;
  if (savedHost) {
    return savedHost;
  }
  if (dryRun) {
    return "dry-run";
  }
  fail(
    "缺少网关 IP。请先询问用户网关 IP，然后运行: " +
      "node scripts/dnake_gateway.js config set-host <gateway_ip>",
  );
}

function resolveCredentials(username, password, dryRun = false) {
  const config = loadConfig();
  const resolvedUsername = username || config.username;
  const resolvedPassword = password || config.password;
  if (resolvedUsername && resolvedPassword) {
    return [resolvedUsername, resolvedPassword];
  }
  if (dryRun) {
    return [resolvedUsername, resolvedPassword];
  }
  const missing = [];
  if (!resolvedUsername) {
    missing.push("用户名");
  }
  if (!resolvedPassword) {
    missing.push("密码");
  }
  fail(
    `缺少${missing.join("和")}。请先询问用户账号密码，然后运行: ` +
      "node scripts/dnake_gateway.js config set-credentials <username> <password>",
  );
}

function summarizeResult(operation, response) {
  if (response && typeof response === "object" && response.dryRun === true) {
    return {
      operation,
      success: null,
      message: "dry-run：只预览报文，未发送控制命令，不能判定设备操作成功或失败",
      request: response.request,
    };
  }
  const success = !!(response && typeof response === "object" && response.result === "ok");
  return {
    operation,
    success,
    message: success ? "成功" : "失败：响应中没有 result: ok",
    response,
  };
}

function isIpChangeHint(message) {
  return ["HTTP 404", "请求失败", "响应不是合法 JSON", "网关 IP 可能"].some((hint) =>
    message.includes(hint),
  );
}

async function executeControl(gateway, args, operation, fields) {
  let beforeState = null;
  let afterState = null;
  const verificationErrors = [];

  if (!args.noVerify && !gateway.dryRun) {
    try {
      beforeState = await gateway.read(args.devNo, args.devCh);
    } catch (error) {
      verificationErrors.push(`控制前状态读取失败: ${error.message}`);
    }
  }

  const response = await gateway.control(args.devNo, args.devCh, fields);
  const result = summarizeResult(operation, response);

  if (!args.noVerify && !gateway.dryRun) {
    try {
      afterState = await gateway.read(args.devNo, args.devCh);
    } catch (error) {
      verificationErrors.push(`控制后状态读取失败: ${error.message}`);
    }
  }

  if (beforeState !== null) {
    result.before_state = beforeState;
  }
  if (afterState !== null) {
    result.after_state = afterState;
  }
  if (verificationErrors.length > 0) {
    result.verification_errors = verificationErrors;
    if (result.success === true) {
      result.message = "命令响应成功，但状态复查不完整";
    }
  } else if (!args.noVerify && !gateway.dryRun) {
    result.verification = "已读取控制前后状态，请据此核对实际设备状态";
  }

  return result;
}

class Gateway {
  constructor({ host, username, password, fromDev = null, toDev = null, timeout = 10, dryRun = false }) {
    this.baseUrl = host.startsWith("http://") || host.startsWith("https://") ? host : `http://${host}`;
    this.username = username;
    this.password = password;
    this.fromDev = fromDev;
    this.toDev = toDev;
    this.timeout = timeout;
    this.dryRun = dryRun;
  }

  headers() {
    const headers = { Accept: "application/json", "Content-Type": "application/json" };
    if (this.username !== undefined && this.username !== null && this.password !== undefined && this.password !== null) {
      const token = Buffer.from(`${this.username}:${this.password}`, "utf8").toString("base64");
      headers.Authorization = `Basic ${token}`;
    }
    return headers;
  }

  async request(method, requestPath, body = null) {
    return new Promise((resolve, reject) => {
      const url = new URL(\`${this.baseUrl}${requestPath}\`);
      const headers = this.headers();
      const options = {
        hostname: url.hostname,
        port: url.port || (url.protocol === "https:" ? 443 : 80),
        path: url.pathname + url.search,
        method: method,
        headers: headers,
        timeout: this.timeout * 1000,
        agent: false
      };

      const req = http.request(options, (res) => {
        let data = "";
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => {
          if (res.statusCode !== 200) {
            let message = \`HTTP \${res.statusCode} \${method} \${requestPath}: \${res.statusMessage}\`;
            if (res.statusCode === 404) {
              message += "。如果该接口之前可用，网关 IP 可能已经变化，请重新向用户确认并保存。";
            }
            reject(new Error(message));
            return;
          }
          if (!data) {
            resolve(null);
            return;
          }
          try {
            resolve(JSON.parse(data));
          } catch (error) {
            reject(new Error(\`响应不是合法 JSON: \${method} \${requestPath}。如果该接口之前可用，网关 IP 可能已经变化，请重新向用户确认并保存。\`));
          }
        });
      });

      req.on("error", (error) => {
        reject(new Error(\`请求失败 \${method} \${requestPath}: \${error.message}。如果该接口之前可用，网关 IP 可能已经变化，请重新向用户确认并保存。\`));
      });

      req.on("timeout", () => {
        req.destroy();
        reject(new Error(\`请求超时 \${method} \${requestPath}\`));
      });

      if (body !== null) {
        req.write(JSON.stringify(body));
      }
      req.end();
    });
  }

  get(requestPath) {
    return this.request("GET", requestPath);
  }

  iotInfo() {
    return this.get("/smart/iot.info");
  }

  devices() {
    return this.get("/smart/speDev.info");
  }

  async ensureRouteNames() {
    if (this.fromDev && this.toDev) {
      return;
    }
    if (this.dryRun) {
      this.fromDev = this.fromDev || "iotDeviceName";
      this.toDev = this.toDev || "gwIotName";
      return;
    }
    const info = await this.iotInfo();
    this.fromDev = info.iotDeviceName;
    this.toDev = info.gwIotName;
    if (!this.fromDev || !this.toDev) {
      fail(`响应缺少 iotDeviceName/gwIotName: ${JSON.stringify(info)}`);
    }
  }

  async postData(data) {
    await this.ensureRouteNames();
    const requestData = Object.assign({}, data, { uuid: crypto.randomUUID().replace(/-/g, "") });
    const envelope = { fromDev: this.fromDev, toDev: this.toDev, data: requestData };
    if (this.dryRun) {
      return { dryRun: true, request: envelope };
    }
    return this.request("POST", "/route.cgi?api=request", envelope);
  }

  states() {
    return this.postData({ action: "readAllDevState" });
  }

  read(devNo, devCh) {
    return this.postData({ action: "readDev", devNo, devCh });
  }

  control(devNo, devCh, fields) {
    return this.postData(Object.assign({ action: "ctrlDev", devNo, devCh }, fields));
  }
}

function usage() {
  return [
    "用法: node scripts/dnake_gateway.js [options] <command> [args]",
    "",
    "全局选项:",
    "  --host <host>             网关 IP 或基础 URL；省略时读取已保存配置",
    "  --username <username>     网关用户名；省略时读取已保存配置",
    "  --password <password>     网关密码；省略时读取已保存配置",
    "  --from-dev <name>         指定 iotDeviceName，避免自动查询",
    "  --to-dev <name>           指定 gwIotName，避免自动查询",
    "  --timeout <seconds>       请求超时时间，默认 10",
    "  --dry-run                 只打印路由报文，不发送 POST",
    "  --no-verify              控制后不读取状态复查",
    "",
    "命令:",
    "  config set-host <gateway_ip>",
    "  config set-credentials <username> <password>",
    "  config show",
    "  config clear-host",
    "  config clear-credentials",
    "  iot-info",
    "  devices",
    "  states",
    "  read --dev-no <n> --dev-ch <n>",
    "  light --dev-no <n> --dev-ch <n> --power on|off",
    "  cover --dev-no <n> --dev-ch <n> (--position <0..100>|--level <0..254>|--stop)",
    "  aircon --dev-no <n> --dev-ch <n> (--power on|off|--temperature <16..32>|--mode <1..4>|--fan <0..2>|--swing <0..3>)",
    "  floor-heat --dev-no <n> --dev-ch <n> (--power on|off|--temperature <16..35>|--mode <0..1>)",
    "  fresh-air --dev-no <n> --dev-ch <n> (--power on|off|--speed <0..3>)",
  ].join("\n");
}

function popValue(tokens, index, name) {
  if (index + 1 >= tokens.length || tokens[index + 1].startsWith("--")) {
    fail(`${name} 缺少取值`);
  }
  return [tokens[index + 1], index + 2];
}

function parseIntValue(value, name) {
  if (!/^-?\d+$/.test(value)) {
    fail(`${name} 必须是整数`);
  }
  return Number.parseInt(value, 10);
}

function parseGlobal(argv) {
  const args = {
    host: null,
    username: null,
    password: null,
    fromDev: null,
    toDev: null,
    timeout: 10,
    dryRun: false,
    noVerify: false,
  };
  const rest = [];
  for (let index = 0; index < argv.length; ) {
    const token = argv[index];
    if (token === "--help" || token === "-h") {
      args.help = true;
      index += 1;
    } else if (token === "--host") {
      [args.host, index] = popValue(argv, index, "--host");
    } else if (token === "--username") {
      [args.username, index] = popValue(argv, index, "--username");
    } else if (token === "--password") {
      [args.password, index] = popValue(argv, index, "--password");
    } else if (token === "--from-dev") {
      [args.fromDev, index] = popValue(argv, index, "--from-dev");
    } else if (token === "--to-dev") {
      [args.toDev, index] = popValue(argv, index, "--to-dev");
    } else if (token === "--timeout") {
      let raw;
      [raw, index] = popValue(argv, index, "--timeout");
      args.timeout = Number(raw);
      if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
        fail("--timeout 必须是正数");
      }
    } else if (token === "--dry-run") {
      args.dryRun = true;
      index += 1;
    } else if (token === "--no-verify") {
      args.noVerify = true;
      index += 1;
    } else {
      rest.push(...argv.slice(index));
      break;
    }
  }
  return { args, rest };
}

function parseDeviceOptions(tokens) {
  const args = {};
  const remaining = [];
  for (let index = 0; index < tokens.length; ) {
    const token = tokens[index];
    if (token === "--dev-no") {
      let raw;
      [raw, index] = popValue(tokens, index, "--dev-no");
      args.devNo = parseIntValue(raw, "--dev-no");
    } else if (token === "--dev-ch") {
      let raw;
      [raw, index] = popValue(tokens, index, "--dev-ch");
      args.devCh = parseIntValue(raw, "--dev-ch");
    } else {
      remaining.push(token);
      index += 1;
    }
  }
  if (args.devNo === undefined) {
    fail("缺少 --dev-no");
  }
  if (args.devCh === undefined) {
    fail("缺少 --dev-ch");
  }
  return { args, remaining };
}

function parseActionOptions(tokens, definitions, required = true) {
  const args = {};
  const seenActions = [];
  for (let index = 0; index < tokens.length; ) {
    const token = tokens[index];
    const definition = definitions[token];
    if (!definition) {
      fail(`未知参数: ${token}`);
    }
    seenActions.push(token);
    if (definition.type === "flag") {
      args[definition.key] = true;
      index += 1;
      continue;
    }
    let raw;
    [raw, index] = popValue(tokens, index, token);
    if (definition.choices && !definition.choices.includes(raw)) {
      fail(`${token} 必须是 ${definition.choices.join("|")} 之一`);
    }
      args[definition.key] = definition.type === "int" ? parseIntValue(raw, token) : raw;
  }
  if (required && seenActions.length !== 1) {
    fail(`必须且只能指定一个操作参数: ${Object.keys(definitions).join("|")}`);
  }
  if (!required && seenActions.length !== 0) {
    fail(`不支持的操作参数: ${seenActions.join(" ")}`);
  }
  return args;
}

function parseDeviceCommand(tokens, definitions, actionRequired = true) {
  const { args, remaining } = parseDeviceOptions(tokens);
  return Object.assign(args, parseActionOptions(remaining, definitions, actionRequired));
}

function withGlobalControlOptions(commandArgs, args) {
  return Object.assign(commandArgs, { noVerify: args.noVerify });
}

function buildGateway(args) {
  const [username, password] = resolveCredentials(args.username, args.password, args.dryRun);
  return new Gateway({
    host: resolveHost(args.host, args.dryRun),
    username,
    password,
    fromDev: args.fromDev,
    toDev: args.toDev,
    timeout: args.timeout,
    dryRun: args.dryRun,
  });
}

async function main(argv) {
  const { args, rest } = parseGlobal(argv);
  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  if (rest.length === 0) {
    fail(usage());
  }

  const command = rest[0];
  if (command === "config") {
    const config = loadConfig();
    const subcommand = rest[1];
    if (subcommand === "set-host") {
      if (rest.length !== 3) {
        fail("用法: config set-host <gateway_ip>");
      }
      config.host = rest[2];
      saveConfig(config);
      printJson({ success: true, message: "已保存网关 IP", host: rest[2] });
    } else if (subcommand === "set-credentials") {
      if (rest.length !== 4) {
        fail("用法: config set-credentials <username> <password>");
      }
      config.username = rest[2];
      config.password = rest[3];
      saveConfig(config);
      printJson({ success: true, message: "已保存网关账号密码", username: rest[2], password: "******" });
    } else if (subcommand === "show") {
      printJson(maskedConfig(config));
    } else if (subcommand === "clear-host") {
      delete config.host;
      saveConfig(config);
      printJson({ success: true, message: "已清除已保存网关 IP" });
    } else if (subcommand === "clear-credentials") {
      delete config.username;
      delete config.password;
      saveConfig(config);
      printJson({ success: true, message: "已清除已保存账号密码" });
    } else {
      fail(`未处理的配置命令: ${subcommand || ""}`);
    }
    return 0;
  }

  const gateway = buildGateway(args);
  let result;

  if (command === "iot-info") {
    result = await gateway.iotInfo();
  } else if (command === "devices") {
    result = await gateway.devices();
  } else if (command === "states") {
    result = await gateway.states();
  } else if (command === "read") {
    const commandArgs = parseDeviceCommand(rest.slice(1), {}, false);
    result = await gateway.read(commandArgs.devNo, commandArgs.devCh);
  } else if (command === "light") {
    const commandArgs = withGlobalControlOptions(
      parseDeviceCommand(rest.slice(1), {
        "--power": { key: "power", type: "string", choices: ["on", "off"] },
      }),
      args,
    );
    result = await executeControl(
      gateway,
      commandArgs,
      `灯 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} power=${commandArgs.power}`,
      { cmd: commandArgs.power },
    );
  } else if (command === "cover") {
    const commandArgs = withGlobalControlOptions(
      parseDeviceCommand(rest.slice(1), {
        "--position": { key: "position", type: "int" },
        "--level": { key: "level", type: "int" },
        "--stop": { key: "stop", type: "flag" },
      }),
      args,
    );
    if (commandArgs.stop) {
      result = await executeControl(
        gateway,
        commandArgs,
        `窗帘 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} stop`,
        { cmd: "stop" },
      );
    } else {
      let level = commandArgs.level;
      if (level === undefined) {
        const position = boundedInt("position", commandArgs.position, 0, 100);
        level = Math.trunc((position / 100) * 254);
      }
      level = boundedInt("level", level, 0, 254);
      result = await executeControl(
        gateway,
        commandArgs,
        `窗帘 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} level=${level}`,
        { cmd: "level", level },
      );
    }
  } else if (command === "aircon") {
    const commandArgs = withGlobalControlOptions(
      parseDeviceCommand(rest.slice(1), {
        "--power": { key: "power", type: "string", choices: ["on", "off"] },
        "--temperature": { key: "temperature", type: "int" },
        "--mode": { key: "mode", type: "int", choices: ["1", "2", "3", "4"] },
        "--fan": { key: "fan", type: "int", choices: ["0", "1", "2"] },
        "--swing": { key: "swing", type: "int", choices: ["0", "1", "2", "3"] },
      }),
      args,
    );
    if (commandArgs.power) {
      const oper = commandArgs.power === "on" ? "powerOn" : "powerOff";
      result = await executeControl(
        gateway,
        commandArgs,
        `空调 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} ${oper}`,
        { cmd: "airCondition", oper },
      );
    } else if (commandArgs.temperature !== undefined) {
      const temp = boundedInt("temperature", commandArgs.temperature, 16, 32);
      result = await executeControl(
        gateway,
        commandArgs,
        `空调 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setTemp=${temp}`,
        { cmd: "airCondition", oper: "setTemp", param: temp },
      );
    } else if (commandArgs.mode !== undefined) {
      result = await executeControl(
        gateway,
        commandArgs,
        `空调 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setMode=${commandArgs.mode}`,
        { cmd: "airCondition", oper: "setMode", param: commandArgs.mode },
      );
    } else if (commandArgs.fan !== undefined) {
      result = await executeControl(
        gateway,
        commandArgs,
        `空调 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setFlow=${commandArgs.fan}`,
        { cmd: "airCondition", oper: "setFlow", param: commandArgs.fan },
      );
    } else {
      result = await executeControl(
        gateway,
        commandArgs,
        `空调 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setSwing=${commandArgs.swing}`,
        { cmd: "airCondition", oper: "setSwing", param: commandArgs.swing },
      );
    }
  } else if (command === "floor-heat") {
    const commandArgs = withGlobalControlOptions(
      parseDeviceCommand(rest.slice(1), {
        "--power": { key: "power", type: "string", choices: ["on", "off"] },
        "--temperature": { key: "temperature", type: "int" },
        "--mode": { key: "mode", type: "int", choices: ["0", "1"] },
      }),
      args,
    );
    if (commandArgs.power) {
      const oper = commandArgs.power === "on" ? "powerOn" : "powerOff";
      result = await executeControl(
        gateway,
        commandArgs,
        `地暖 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} ${oper}`,
        { cmd: "airHeater", oper },
      );
    } else if (commandArgs.temperature !== undefined) {
      const temp = boundedInt("temperature", commandArgs.temperature, 16, 35);
      result = await executeControl(
        gateway,
        commandArgs,
        `地暖 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setTemp=${temp}`,
        { cmd: "airHeater", oper: "setTemp", param: temp },
      );
    } else {
      result = await executeControl(
        gateway,
        commandArgs,
        `地暖 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setMode=${commandArgs.mode}`,
        { cmd: "airHeater", oper: "setMode", param: commandArgs.mode },
      );
    }
  } else if (command === "fresh-air") {
    const commandArgs = withGlobalControlOptions(
      parseDeviceCommand(rest.slice(1), {
        "--power": { key: "power", type: "string", choices: ["on", "off"] },
        "--speed": { key: "speed", type: "int", choices: ["0", "1", "2", "3"] },
      }),
      args,
    );
    if (commandArgs.power) {
      const oper = commandArgs.power === "on" ? "powerOn" : "powerOff";
      result = await executeControl(
        gateway,
        commandArgs,
        `新风 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} ${oper}`,
        { cmd: "airFresh", oper },
      );
    } else {
      result = await executeControl(
        gateway,
        commandArgs,
        `新风 devNo=${commandArgs.devNo} devCh=${commandArgs.devCh} setFlow=${commandArgs.speed}`,
        { cmd: "airFresh", oper: "setFlow", param: commandArgs.speed },
      );
    }
  } else {
    fail(`未处理的命令: ${command}`);
  }

  printJson(result);
  return 0;
}

main(process.argv.slice(2))
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    const message = error.message || String(error);
    printJson({
      success: false,
      message,
      ip_may_have_changed: isIpChangeHint(message),
    });
    process.exitCode = error.exitCode || 1;
  });
