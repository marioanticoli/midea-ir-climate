from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.restore_state import RestoreEntity

from .midea import build_code, build_state

HVAC_TO_MODE = {
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "heat",
}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MideaIrClimate(entry)])


class MideaIrClimate(ClimateEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_assumed_state = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 17
    _attr_max_temp = 30
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [HVACMode.OFF, *HVAC_TO_MODE]
    _attr_fan_modes = ["auto", "low", "medium", "high"]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, entry):
        self._ieee = entry.data["ieee"]
        self._attr_unique_id = entry.entry_id
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = 24
        self._attr_fan_mode = "auto"
        self._last_mode = HVACMode.COOL

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None:
            return
        if last.state in [m.value for m in self._attr_hvac_modes]:
            self._attr_hvac_mode = HVACMode(last.state)
            if self._attr_hvac_mode != HVACMode.OFF:
                self._last_mode = self._attr_hvac_mode
        temp = last.attributes.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._attr_target_temperature = int(temp)
        fan = last.attributes.get("fan_mode")
        if fan in self._attr_fan_modes:
            self._attr_fan_mode = fan

    async def _send(self):
        powered = self._attr_hvac_mode != HVACMode.OFF
        mode = self._attr_hvac_mode if powered else self._last_mode
        state = build_state(
            powered,
            HVAC_TO_MODE[mode],
            int(self._attr_target_temperature),
            self._attr_fan_mode,
        )
        await self.hass.services.async_call(
            "zha",
            "issue_zigbee_cluster_command",
            {
                "ieee": self._ieee,
                "endpoint_id": 1,
                "cluster_id": 57348,
                "cluster_type": "in",
                "command": 2,
                "command_type": "server",
                "params": {"code": build_code(state)},
            },
            blocking=True,
            context=self._context,
        )
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        self._attr_hvac_mode = hvac_mode
        if hvac_mode != HVACMode.OFF:
            self._last_mode = hvac_mode
        await self._send()

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._send()
        else:
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        self._attr_fan_mode = fan_mode
        if self._attr_hvac_mode != HVACMode.OFF:
            await self._send()
        else:
            self.async_write_ha_state()
