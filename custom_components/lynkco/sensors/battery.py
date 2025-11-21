from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential

from .lynk_co_sensor import LynkCoSensor
from .lynk_co_statistics_sensor import LynkCoStatisticsSensor


def create_sensors(coordinator, vin):
    sensors = [
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co 12V Battery",
            "vehicle_record.battery.chargeLevel",
            PERCENTAGE,
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co 12V Battery Charge",
            "vehicle_record.battery.charge",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co 12V Battery Health",
            "vehicle_record.battery.health",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co 12V Battery Power level",
            "vehicle_record.battery.powerLevel",
        ),
        LynkCoSensor(
            coordinator,
            vin,
            "Lynk & Co 12V Battery Energy level",
            "vehicle_record.battery.energyLevel",
        ),
        LynkCoStatisticsSensor(
            coordinator,
            vin,
            "Lynk & Co 12V Battery Voltage",
            "vehicle_record.battery.voltage",
            UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    ]
    return sensors
