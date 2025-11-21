from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature

from .lynk_co_sensor import LynkCoSensor
from .lynk_co_statistics_sensor import LynkCoStatisticsSensor


def create_sensors(coordinator, vin):
    sensors = [
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Interior Temperature",
            "vehicle_record.climate.interiorTemp.temp",
            UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Interior Temperature Quality",
            "vehicle_record.climate.interiorTemp.Quality",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Interior Temperature Unit",
            "vehicle_record.climate.interiorTemp.Unit",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Climate Updated",
            "vehicle_record.climate.vehicleUpdatedAt",
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Exterior temperature",
            "vehicle_record.climate.exteriorTemp.temp",
            UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Exterior Temperature Quality",
            "vehicle_record.climate.exteriorTemp.Quality",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Exterior Temperature Unit",
            "vehicle_record.climate.exteriorTemp.Unit",
        ),
    ]
    return sensors
