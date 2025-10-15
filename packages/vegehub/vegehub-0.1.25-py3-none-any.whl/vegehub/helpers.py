"""Helper file containing data transformations."""
from typing import Any

def vh400_transform(value: int | str | float) -> float | None:
    """Perform a piecewise linear transformation on the input value.

    The transform is based on the following pairs of points:
    (0,0), (1.1000, 10.0000), (1.3000, 15.0000), (1.8200, 40.0000),
    (2.2000, 50.0000), (3.0000, 100.0000)
    """

    float_value = None

    if isinstance(value, float):
        float_value = value

    if isinstance(value, (int, str)):
        try:
            float_value = float(value)
        except ValueError:
            return None

    if not isinstance(float_value, float):
        return None

    ret = 100.0

    if float_value <= 0.0100:
        # Below 0.01V is just noise and should be reported as 0
        ret = 0
    elif float_value <= 1.1000:
        # Linear interpolation between (0.0000, 0.0000) and (1.1000, 10.0000)
        ret = (10.0000 - 0.0000) / (1.1000 - 0.0000) * (float_value - 0.0000) + 0.0000
    elif float_value <= 1.3000:
        # Linear interpolation between (1.1000, 10.0000) and (1.3000, 15.0000)
        ret = (15.0000 - 10.0000) / (1.3000 - 1.1000) * (float_value - 1.1000) + 10.0000
    elif float_value <= 1.8200:
        # Linear interpolation between (1.3000, 15.0000) and (1.8200, 40.0000)
        ret = (40.0000 - 15.0000) / (1.8200 - 1.3000) * (float_value - 1.3000) + 15.0000
    elif float_value <= 2.2000:
        # Linear interpolation between (1.8200, 40.0000) and (2.2000, 50.0000)
        ret = (50.0000 - 40.0000) / (2.2000 - 1.8200) * (float_value - 1.8200) + 40.0000
    elif float_value <= 3.0000:
        # Linear interpolation between (2.2000, 50.0000) and (3.0000, 100.0000)
        ret = (100.0000 - 50.0000) / (3.0000 - 2.2000) * (float_value - 2.2000) + 50.0000

    # For values greater than 3.0000, return 100.0000
    return ret

def therm200_transform(value: int | str | float) -> float | None:
    """Transform to change voltage into degrees celsius."""
    if not isinstance(value, (int, str, float)):
        return None
    try:
        float_value = float(value)
    except ValueError:
        return None

    return (41.6700 * float_value) - 40.0000

def update_data_to_latest_dict(data: dict[str,Any]) -> dict[str,Any]:
    """Accepts raw update data and returns a dict of the latest values of each sensor."""
    sensor_data = {}
    # Process sensor data
    if "sensors" in data and "mac" in data:
        for sensor in data["sensors"]:
            slot = sensor.get("slot")
            latest_sample = sensor["samples"][-1]
            value = latest_sample["v"]
            entity_id = f"{data['mac']}_{slot}".lower()
            sensor_data[entity_id] = value
    return sensor_data

def update_data_to_ha_dict(
    data: dict[str, Any],
    num_sensors: int,
    num_actuators: int,
    is_ac: bool
) -> dict[str, Any]:
    """Transform raw update data into a dictionary of sensor and actuator values.
    
    Returns:
        Dictionary mapping entity IDs to their values
    """
    if not ("sensors" in data and "mac" in data):
        return {}

    result = {}
    slots = sorted(data["sensors"], key=lambda x: x.get("slot", 0))

    for item in slots:
        slot = item["slot"]
        samples = item.get("samples", [])
        if not samples:
            continue  # skip empty slots
        value = samples[-1].get("v", 0)
        # Determine what this slot represents
        if 1 <= slot <= num_sensors:
            result[f"analog_{slot - 1}"] = value
        elif not is_ac and slot == num_sensors + 1:
            result["battery"] = value
        else:
            # Actuator slots come after sensors (+1 for battery if present)
            actuator_offset = num_sensors + (0 if is_ac else 1)
            if actuator_offset < slot <= actuator_offset + num_actuators:
                actuator_index = slot - actuator_offset - 1
                result[f"actuator_{actuator_index}"] = value

    return result
