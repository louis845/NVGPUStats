from typing import Any

information_list: list[str] = [
    "GPU_NAME",
    "TOTAL_MEMORY",
    "MEMORY_USED",
    "AVAILABLE_MEMORY",
    "UTILIZATION",
    "WATTAGE",
    "TEMPERATURE",
    "FAN_SPEED",
    "MEMORY_USED_PERCENTAGE",
    "POWER_LIMIT"
]

information_details: dict[str, dict[str, Any]] = {
    "GPU_NAME": {
        "description": "Name of GPU",
        "is_static": True,
        "type": "str",
    },
    "TOTAL_MEMORY": {
        "description": "Total memory of GPU in MiB",
        "is_static": True,
        "type": "int",
    },
    "MEMORY_USED": {
        "description": "Memory used in GPU in MiB",
        "is_static": False,
        "type": "int",
    },
    "AVAILABLE_MEMORY": {
        "description": "Available memory in GPU in MiB",
        "is_static": False,
        "type": "int",
    },
    "UTILIZATION": {
        "description": "GPU utilization percentage",
        "is_static": False,
        "type": "int",
    },
    "WATTAGE": {
        "description": "Current power consumption in watts",
        "is_static": False,
        "type": "float",
    },
    "TEMPERATURE": {
        "description": "Current temperature in Celsius",
        "is_static": False,
        "type": "int",
    },
    "FAN_SPEED": {
        "description": "Fan speed percentage",
        "is_static": False,
        "type": "int",
    },
    "MEMORY_USED_PERCENTAGE": {
        "description": "Percentage of memory used",
        "is_static": False,
        "type": "float",
    },
    "POWER_LIMIT": {
        "description": "Power limit in watts",
        "is_static": True,
        "type": "float",
    }
}

assert set(information_list) == set(information_details.keys()), "Invalid!"

def is_static(information: str) -> bool:
    """
    Returns whether the specified information is static.
    """
    return information_details[information]["is_static"]