import logging

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import assistant

_LOGGER = logging.getLogger(__name__)


def find_covers(device_list):
    result = []
    for device in device_list:
        if device.get('ty') == 514:
            result.append(DnakeCover(device))
    return result


def update_covers_state(cover_list, state_list):
    for cover in cover_list:
        for device_state in state_list:
            if cover._dev_no == device_state.get("devNo") and cover._dev_ch == device_state.get("devCh"):
                cover.set_state(device_state)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Dnake covers from a config entry."""
    cover_list = entry.data['cover_list']
    if cover_list:
        async_add_entities(cover_list)


class DnakeCover(CoverEntity):
    """Representation of a Dnake Cover with position control."""

    def __init__(self, device):
        """Initialize the cover."""
        self._device = device
        self._name = device.get("na")
        self._current_level = device.get("level", 0)
        self._is_closed = self._current_level == 0
        self._is_opening = False
        self._is_closing = False
        self._dev_no = device.get("nm")
        self._dev_ch = device.get("ch")

    @property
    def name(self):
        """Return the display name of this cover."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this cover."""
        return f"dnake_{self._dev_ch}_{self._dev_no}"

    @property
    def is_closed(self):
        """Return true if the cover is closed."""
        return self._is_closed

    @property
    def is_opening(self):
        """Return true if the cover is opening."""
        return self._is_opening

    @property
    def is_closing(self):
        """Return true if the cover is closing."""
        return self._is_closing

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return None if self._current_level is None else int((self._current_level / 254) * 100)

    @property
    def supported_features(self):
        """Flag supported features."""
        return (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION
        )

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        current_level = self.get_current_level()
        position = kwargs.get("position", 0)  # Position is 0-100
        level = int((position / 100) * 254)  # Convert to 0-254
        level = max(0, min(254, level))  # Ensure level is within range
        is_success = assistant.set_level(self._dev_no, self._dev_ch, level)
        if is_success:
            self._current_level = level
            self._is_opening = level > current_level
            self._is_closing = level < current_level
            self._is_closed = level == current_level
            self.async_write_ha_state()

    def open_cover(self, **kwargs):
        """Open the cover."""
        self.set_cover_position(position=100)

    def close_cover(self, **kwargs):
        """Close the cover."""
        self.set_cover_position(position=0)

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        is_success = assistant.stop(self._dev_no, self._dev_ch)
        if is_success:
            current_level = self.get_current_level()
            self._current_level = current_level
            self._is_closed = current_level == 0
            self._is_opening = False
            self._is_closing = False
            self.async_write_ha_state()

    async def async_update(self):
        current_level = self.get_current_level()
        self._current_level = current_level
        self._is_closed = current_level == 0
        self._is_opening = False
        self._is_closing = False

    def get_current_level(self):
        state = assistant.read_dev_state(self._dev_no, self._dev_ch)
        if state and state.get('result') == 'ok':
            return state.get('level', 0)
        else:
            return 0

    def set_state(self, device_state):
        current_level = device_state.get("level", 0)
        self._current_level = current_level
        self._is_closed = current_level == 0
        self.async_write_ha_state()
