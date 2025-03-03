import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.helpers.entity_platform import AddEntitiesCallback, async_call_later
from homeassistant.helpers.event import async_track_time_interval

from .core.assistant import assistant

_LOGGER = logging.getLogger(__name__)


def load_covers(device_list):
    covers = [DnakeCover(device) for device in device_list if device.get("ty") == 514]
    _LOGGER.info(f"find cover num: {len(covers)}")
    assistant.entries["cover"] = covers


def update_covers_state(states):
    covers = assistant.entries["cover"]
    for cover in covers:
        if cover.is_opening or cover.is_closing:
            return
        state = next((state for state in states if cover.is_hint_state(state)), None)
        if state:
            cover.update_state(state)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    cover_list = assistant.entries["cover"]
    if cover_list:
        async_add_entities(cover_list)


class DnakeCover(CoverEntity):

    def __init__(self, device):
        self._name = device.get("na")
        self._dev_no = device.get("nm")
        self._dev_ch = device.get("ch")
        self._target_level = 0
        self._current_level = 0
        self._level_refresher_cancel = None

    def is_hint_state(self, state):
        return state.get("devNo") == self._dev_no and state.get("devCh") == self._dev_ch

    @property
    def unique_id(self):
        return f"dnake_{self._dev_ch}_{self._dev_no}"

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def is_closed(self):
        return self._current_level == 0

    @property
    def is_opening(self):
        return self._target_level > self._current_level

    @property
    def is_closing(self):
        return self._target_level < self._current_level

    @property
    def current_cover_position(self):
        # 0 - 254 for dnake cover
        return int((self._current_level / 254) * 100)

    @property
    def supported_features(self):
        return (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    async def async_close_cover(self, **kwargs):
        await self.async_set_cover_position(position=0)

    async def async_open_cover(self, **kwargs):
        await self.async_set_cover_position(position=100)

    async def async_set_cover_position(self, **kwargs):
        target_level = int((kwargs.get("position", 0) / 100) * 254)
        is_success = await self.hass.async_add_executor_job(
            assistant.set_level,
            self._dev_no,
            self._dev_ch,
            target_level,
        )
        if is_success:
            self._target_level = target_level
            self._start_schedule_update()
        else:
            _LOGGER.error("set cover position fail")

    async def async_stop_cover(self, **kwargs):
        is_success = await self.hass.async_add_executor_job(
            assistant.stop,
            self._dev_no,
            self._dev_ch,
        )
        if is_success:
            self._stop_schedule_update()

            # 停止后，延迟获取level状态才准确
            async def _reload_cover(_):
                await self._async_refresh_level()

            async_call_later(self.hass, timedelta(seconds=2), _reload_cover)

    def _start_schedule_update(self):
        self._stop_schedule_update()
        self._level_refresher_cancel = async_track_time_interval(
            self.hass,
            self._do_schedule_update,
            timedelta(milliseconds=500),
        )

    async def _do_schedule_update(self, now=None):
        await self._async_refresh_level(update_target_level=False)
        if self._current_level == self._target_level:
            self._stop_schedule_update()

    def _stop_schedule_update(self):
        if self._level_refresher_cancel:
            self._level_refresher_cancel()

    async def _async_refresh_level(self, update_target_level=True):
        state = await self.hass.async_add_executor_job(
            assistant.read_dev_state,
            self._dev_no,
            self._dev_ch,
        )
        if state and state.get("result") == "ok":
            self.update_state(state, update_target_level=update_target_level)

    def update_state(self, state, update_target_level=True):
        current_level = state.get("level", 0)
        self._current_level = current_level
        if update_target_level:
            self._target_level = current_level
        self.async_write_ha_state()
