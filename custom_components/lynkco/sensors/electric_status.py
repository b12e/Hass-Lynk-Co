from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTime

from .lynk_co_sensor import LynkCoSensor
from .lynk_co_statistics_sensor import LynkCoStatisticsSensor


def create_sensors(coordinator, vin):
    sensors = [
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Battery Updated",
            "vehicle_record.electricStatus.vehicleUpdatedAt",
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Time until charged",
            "vehicle_record.electricStatus.timeToFullyCharged",
            UnitOfTime.MINUTES,
            device_class=SensorDeviceClass.DURATION,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Battery",
            "vehicle_record.electricStatus.chargeLevel",
            PERCENTAGE,
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Battery distance",
            "vehicle_record.electricStatus.distanceToEmptyOnBatteryOnly",
            UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    ]
    return sensors
