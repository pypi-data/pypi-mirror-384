"""TFA.me library for Home Assistant: data.py."""

from datetime import datetime
from typing import Any
from .exceptions import TFAmeJSONError


class TFAmeDataForHA:
    """Convert and hold TFA.me data."""

    def __init__(
        self,
        multiple_entities: bool,
    ):
        """Initialize the TFA.me data stucture."""
        self._multiple_entities = multiple_entities
        self._reset_rain_sensors = False
        self._gateway_id = ""

    def get_gateway_id(self) -> str:
        """Get the (parsed) gateway ID."""
        return self._gateway_id

    def json_to_entities(self, json_data: dict) -> Any:
        """Convert a TFA.me JSON dict into a TFA.me data dict."""
        parsed_data = {}  # dict

        try:
            # Parse JSON data
            gateway_id: str = json_data.get("gateway_id", "tfame")
            gateway_id = gateway_id.lower()
            self._gateway_id = gateway_id
            # Fallback time if "timestamp" is missing
            formatted_time_str = datetime.now().replace(microsecond=0).isoformat() + "Z"

            for sensor in json_data.get("sensors", []):
                sensor_id = sensor["sensor_id"]

                for measurement, values in sensor.get("measurements", {}).items():
                    if self._multiple_entities:
                        entity_id = f"sensor.{gateway_id}_{sensor_id}_{measurement}"  # Entity ID
                    else:
                        entity_id = f"sensor.{sensor_id}_{measurement}"  # Entity ID

                    parsed_data[entity_id] = {
                        "sensor_id": sensor_id,
                        "gateway_id": gateway_id,
                        "sensor_name": sensor["name"],
                        "measurement": measurement,
                        "value": values["value"],
                        "unit": values["unit"],
                        "timestamp": sensor.get("timestamp", formatted_time_str),
                        "ts": sensor["ts"],
                        "info": "",
                    }

                    if measurement == "lowbatt":
                        parsed_data[entity_id]["unit"] = ""  # remove "unit"
                        entity_id_lowbatt2 = f"{entity_id}_txt"
                        # lowbatt as text
                        parsed_data[entity_id_lowbatt2] = {
                            "sensor_id": sensor_id,
                            "gateway_id": gateway_id,
                            "sensor_name": f"{sensor['name']}",
                            "measurement": "lowbatt_text",
                            "value": values["value"],
                            "text": values["unit"],
                            "uint": "",
                            "timestamp": sensor.get("timestamp", formatted_time_str),
                            "ts": sensor["ts"],
                        }

                    if measurement == "wind_direction":
                        entity_id_wind2 = f"{entity_id}_deg"  # Entity ID for degrees
                        entity_id_wind3 = f"{entity_id}_txt"  # Entity ID for text
                        uint_str = "-"
                        val = int(values["value"])
                        if 0 <= val <= 15:
                            direction = [
                                "N",
                                "NNE",
                                "NE",
                                "ENE",
                                "E",
                                "ESE",
                                "SE",
                                "SSE",
                                "S",
                                "SSW",
                                "SW",
                                "WSW",
                                "W",
                                "WNW",
                                "NW",
                                "NNW",
                                "N",
                            ]
                            uint_str = direction[val]

                        # wind direction in degrees
                        parsed_data[entity_id_wind2] = {
                            "sensor_id": sensor_id,
                            "gateway_id": gateway_id,
                            "sensor_name": f"{sensor['name']}",
                            "measurement": f"{measurement}_deg",
                            "value": values["value"],
                            "unit": "°",
                            "timestamp": sensor.get("timestamp", formatted_time_str),
                            "ts": sensor["ts"],
                        }
                        # wind direction as text
                        parsed_data[entity_id_wind3] = {
                            "sensor_id": sensor_id,
                            "gateway_id": gateway_id,
                            "sensor_name": f"{sensor['name']}",
                            "measurement": "wind_direction_text",
                            "value": values["value"],
                            "text": "?",
                            "uint": "",
                            "timestamp": sensor.get("timestamp", formatted_time_str),
                            "ts": sensor["ts"],
                        }
                        parsed_data[entity_id_wind3]["text"] = uint_str

                    if measurement == "rain":
                        entity_id_2 = f"{entity_id}_rel"  # Entity ID
                        parsed_data[entity_id_2] = {
                            "sensor_id": sensor_id,
                            "gateway_id": gateway_id,
                            "sensor_name": f"{sensor['name']}",
                            "measurement": f"{measurement}_relative",
                            "value": values["value"],
                            "unit": values["unit"],
                            "timestamp": sensor.get(
                                "timestamp", "unknown"
                            ),  # datetime.utcnow()
                            "ts": sensor["ts"],
                            "reset_rain": self._reset_rain_sensors,
                        }
                        # rain last hour
                        entity_id_3 = f"{entity_id}_hour"  # Entity ID
                        parsed_data[entity_id_3] = {
                            "sensor_id": sensor_id,
                            "gateway_id": gateway_id,
                            "sensor_name": f"{sensor['name']}",
                            "measurement": f"{measurement}_1_hour",
                            "value": values["value"],
                            "unit": values["unit"],
                            "timestamp": sensor.get("timestamp", formatted_time_str),
                            "ts": sensor["ts"],
                            "reset_rain": self._reset_rain_sensors,
                        }
                        # rain last 24 hours
                        entity_id_4 = f"{entity_id}_24hours"  # Entity ID
                        parsed_data[entity_id_4] = {
                            "sensor_id": sensor_id,
                            "gateway_id": gateway_id,
                            "sensor_name": f"{sensor['name']}",
                            "measurement": f"{measurement}_24_hours",
                            "value": values["value"],
                            "unit": values["unit"],
                            "timestamp": sensor.get("timestamp", formatted_time_str),
                            "ts": sensor["ts"],
                            "reset_rain": self._reset_rain_sensors,
                        }

            return parsed_data

        except Exception as err:
            raise TFAmeJSONError(f"Invalid JSON response: {err}") from err
