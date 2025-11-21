from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfLength

from .lynk_co_sensor import LynkCoSensor
from .lynk_co_statistics_sensor import LynkCoStatisticsSensor


def create_sensors(coordinator, vin):
    sensors = [
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Odometer",
            "vehicle_record.odometer.odometerKm",
            UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Odometer miles",
            "vehicle_record.odometer.odometerMile",
            UnitOfLength.MILES,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Odometer Updated",
            "vehicle_record.odometer.vehicleUpdatedAt",
        ),
    ]
    return sensors
