from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import UnitOfVolume, UnitOfLength
from .lynk_co_sensor import LynkCoSensor
from .lynk_co_statistics_sensor import LynkCoStatisticsSensor


def create_sensors(coordinator, vin):
    sensors = [
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel Level",
            "vehicle_record.fuel.level",
            UnitOfVolume.LITERS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel Updated",
            "vehicle_record.fuel.vehicleUpdatedAt",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel Level status",
            "vehicle_record.fuel.levelStatus",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel Type",
            "vehicle_record.fuel.fuelType",
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel distance",
            "vehicle_record.fuel.distanceToEmpty",
            UnitOfLength.KILOMETERS,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel avg consumption",
            "vehicle_record.fuel.averageConsumption",
            "L/100km",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co Fuel avg consumption latest cycle",
            "vehicle_record.fuel.averageConsumptionLatestDrivingCycle",
            "L/100km",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co Tank Flap Status",
            "vehicle_shadow.vls.tankFlapStatus",
        ),
    ]
    return sensors
