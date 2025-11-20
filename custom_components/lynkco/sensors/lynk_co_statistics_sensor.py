import logging
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from .lynk_co_sensor import LynkCoSensor

_LOGGER = logging.getLogger(__name__)


class LynkCoStatisticsSensor(LynkCoSensor):
    """Lynk & Co sensor with long-term statistics support."""

    def __init__(
        self,
        coordinator,
        vin,
        name,
        data_path,
        unit_of_measurement=None,
        state_mapping=None,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ):
        super().__init__(
            coordinator, vin, name, data_path, unit_of_measurement, state_mapping
        )
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def device_class(self):
        return self._attr_device_class

    @property
    def state_class(self):
        return self._attr_state_class
