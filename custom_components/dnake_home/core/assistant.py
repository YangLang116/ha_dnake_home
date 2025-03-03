import logging
import requests

from .constant import Action, Cmd, Power
from .utils import encode_auth, get_uuid

_LOGGER = logging.getLogger(__name__)


class __AssistantCore:
    def __init__(self):
        self.gw_ip = None
        self.auth = None
        self.from_device = None
        self.to_device = None
        self.entries = {}

    def bind_auth_info(self, gw_ip, auth_name, auth_psw):
        self.gw_ip = gw_ip
        self.auth = encode_auth(auth_name, auth_psw)
        _LOGGER.info(f"bind auth info: ip={self.gw_ip},auth={self.auth}")

    def bind_iot_info(self, iot_device_name, gw_iot_name):
        self.from_device = iot_device_name
        self.to_device = gw_iot_name
        _LOGGER.info(f"bind iot info: from={self.from_device},to={self.to_device}")

    def __get_url(self, path):
        return f"http://{self.gw_ip}{path}"

    def __get_header(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth}",
        }

    def get(self, path):
        try:
            url = self.__get_url(path)
            resp = requests.get(url, headers=self.__get_header())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error("get error: path=%s,err=%s", path, e)
            return None

    def post(self, data: dict):
        try:
            url = self.__get_url("/route.cgi?api=request")
            data["uuid"] = get_uuid()
            resp = requests.post(
                url,
                headers=self.__get_header(),
                json={
                    "fromDev": self.from_device,
                    "toDev": self.to_device,
                    "data": data,
                },
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error("post error: data=%s,err=%s", data, e)
            return None

    def do_action(self, data: dict):
        resp = self.post(data)
        return resp and resp.get("result") == "ok"


class Assistant(__AssistantCore):

    def query_iot_info(self):
        iot_info = self.get("/smart/iot.info")
        if iot_info:
            return {
                "iot_device_name": iot_info.get("iotDeviceName"),
                "gw_iot_name": iot_info.get("gwIotName"),
            }
        else:
            _LOGGER.error("query iot info fail")
            return None

    def query_device_list(self):
        device_info = self.get("/smart/speDev.info")
        if device_info:
            device_array = device_info.get("dl", [])
            return device_array
        else:
            _LOGGER.error("query device info fail")
            return None

    def read_dev_state(self, dev_no, dev_ch):
        state_info = self.post(
            {
                "action": Action.ReadDev.value,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )
        if state_info:
            return state_info
        else:
            _LOGGER.error(f"query device status fail: devNo={dev_no},devCh={dev_ch}")
            return None

    def read_all_dev_state(self):
        state_info = self.post({"action": Action.ReadAllDevState.value})
        if state_info:
            return state_info.get("devList")
        else:
            _LOGGER.error("query all device status fail")
            return None

    def turnTo(self, dev_no, dev_ch, is_open: bool):
        cmd = Cmd.On if is_open else Cmd.Off
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": cmd.value,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )

    def stop(self, dev_no, dev_ch):
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": Cmd.Stop.value,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )

    def set_level(self, dev_no, dev_ch, level: int):
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": Cmd.Level.value,
                "level": level,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )

    def set_air_condition_power(self, dev_no, dev_ch, is_open: bool):
        power = Power.On if is_open else Power.Off
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": Cmd.AirCondition.value,
                "oper": power.value,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )

    def set_air_condition_temperature(self, dev_no, dev_ch, temp: int):
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": Cmd.AirCondition.value,
                "oper": "setTemp",
                "param": temp,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )

    def set_air_condition_mode(self, dev_no, dev_ch, mode: int):
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": Cmd.AirCondition.value,
                "oper": "setMode",
                "param": mode,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )

    def set_air_condition_fan(self, dev_no, dev_ch, mode: int):
        return self.do_action(
            {
                "action": Action.CtrlDev.value,
                "cmd": Cmd.AirCondition.value,
                "oper": "setFlow",
                "param": mode,
                "devNo": dev_no,
                "devCh": dev_ch,
            }
        )


assistant = Assistant()
