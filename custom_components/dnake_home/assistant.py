import requests
import logging

from .constant import Action, Cmd
from .utils import encode_auth, get_uuid

_LOGGER = logging.getLogger(__name__)


class __AssistantCore:
    def __init__(self):
        self.gw_ip = None
        self.auth = None
        self.from_device = None
        self.to_device = None

    def bind_auth_info(self, gw_ip, auth_name, auth_psw):
        self.gw_ip = gw_ip
        self.auth = encode_auth(auth_name, auth_psw)
        _LOGGER.info(f'bind auth info: ip={self.gw_ip},auth={self.auth}')

    def bind_iot_info(self, iot_device_name, gw_iot_name):
        self.from_device = iot_device_name
        self.to_device = gw_iot_name
        _LOGGER.info(f'bind iot info: fromDevice={self.from_device},toDevice={self.to_device}')

    def __get_url(self, path):
        return f'http://{self.gw_ip}{path}'

    def __get_header(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self.auth}'
        }

    def query_info(self, path):
        try:
            url = self.__get_url(path)
            resp = requests.get(url, headers=self.__get_header())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error('query info error: path=%s,err=%s', path, e)
            return None

    def do_action(self, data: dict):
        try:
            url = self.__get_url('/route.cgi?api=request')
            data['uuid'] = get_uuid()
            resp = requests.post(url, headers=self.__get_header(),
                                 json={'fromDev': self.from_device, 'toDev': self.to_device, 'data': data})
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error('do_action error: data=%s,err=%s', data, e)
            return None


class Assistant(__AssistantCore):

    def query_iot_info(self):
        iot_info = self.query_info('/smart/iot.info')
        if iot_info:
            return {'iot_device_name': iot_info.get('iotDeviceName'), 'gw_iot_name': iot_info.get('gwIotName')}
        else:
            _LOGGER.error('query iot info fail')
            return None

    def query_device_list(self):
        device_info = self.query_info('/smart/speDev.info')
        if device_info:
            device_array = device_info.get('dl', [])
            # self._update_device_list_state(device_array)
            return device_array
        else:
            _LOGGER.error('query device info fail')
            return None

    # def _update_device_list_state(self, device_array: list):
    #     if not device_array:
    #         return
    #     device_state_array = self.read_all_dev_state()
    #     if not device_state_array:
    #         return
    #     for device in device_array:
    #         dev_no = device.get('nm')
    #         dev_ch = device.get('ch')
    #         device_state = next((state for state in device_state_array if
    #                              state.get("devNo") == dev_no and state.get("devCh") == dev_ch), None)
    #         if device_state:
    #             state = device_state.get("state", 0)
    #             level = device_state.get("level", 0)
    #             device.update({"state": state, "level": level})

    def read_dev_state(self, dev_no, dev_ch):
        state_info = self.do_action({'action': Action.ReadDev.value, 'devNo': dev_no, 'devCh': dev_ch})
        if state_info:
            return state_info
        else:
            _LOGGER.error(f'query device status fail: devNo={dev_no},devCh={dev_ch}')
            return None

    def read_all_dev_state(self):
        state_info = self.do_action({'action': Action.ReadAllDevState.value})
        if state_info:
            return state_info.get('devList')
        else:
            _LOGGER.error('query all device status fail')
            return None

    # 控制灯、窗帘
    def switch(self, dev_no, dev_ch, is_open: bool):
        cmd = Cmd.On.value if is_open else Cmd.Off.value
        resp = self.do_action({'action': Action.CtrlDev.value, 'cmd': cmd, 'devNo': dev_no, 'devCh': dev_ch})
        return resp and resp.get('result') == 'ok'

    # 停止窗帘
    def stop(self, dev_no, dev_ch):
        resp = self.do_action({'action': Action.CtrlDev.value, 'cmd': Cmd.Stop.value, 'devNo': dev_no, 'devCh': dev_ch})
        return resp and resp.get('result') == 'ok'

    # 控制窗帘开合程度: 0 - 254
    def set_level(self, dev_no, dev_ch, level: int):
        resp = self.do_action(
            {'action': Action.CtrlDev.value, 'cmd': Cmd.Level.value, 'level': level, 'devNo': dev_no, 'devCh': dev_ch})
        return resp and resp.get('result') == 'ok'


assistant = Assistant()
