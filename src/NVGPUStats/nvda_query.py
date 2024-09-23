import subprocess
from typing import Any
from threading import Lock

from .information import information_list, information_details
from . import information as info_code

# Globals for caching
_cached_devices: list[int] = []
_devices_lock = Lock()

def list_devices() -> list[int]:
    """
    Returns a list of available NVIDIA GPU device numbers.
    Caches the result to avoid redundant calls to nvidia-smi.
    """
    global _cached_devices

    with _devices_lock:
        if not _cached_devices:
            try:
                output = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    shell=False
                )
                devices = [int(line.strip()) for line in output.strip().split('\n') if line.strip().isdigit()]
                _cached_devices = sorted(devices)
            except subprocess.CalledProcessError as e:
                raise RuntimeError("Failed to list NVIDIA GPUs.") from e

    return _cached_devices

# Globals for cached static information
_cached_static_info: dict[int, dict[str, Any]] = {}
_static_info_lock = Lock()

def get_static_info(device: int) -> dict[str, Any]:
    """
    Returns static information about the specified device.
    Caches the result to avoid redundant calls to nvidia-smi.
    """
    global _cached_static_info
    static_information_list = [info for info in information_list if information_details[info]["is_static"]]
    static_information_list_mapped = [_QUERY_MAPPING[info] for info in static_information_list]

    with _static_info_lock:
        if device not in _cached_static_info:
            try:
                cmd = ["nvidia-smi", f"--query-gpu={','.join(static_information_list_mapped)}", f"--id={device}", "--format=csv,noheader,nounits"]
                output = subprocess.check_output(
                    cmd,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    shell=False
                )
                values = [value.strip() for value in output.strip().split(',')]
                static_info = {}
                for idx, info in enumerate(static_information_list):
                    info_type = information_details[info]["type"]
                    if info_type == "int":
                        static_info[info] = int(float(values[idx]))
                    elif info_type == "float":
                        static_info[info] = float(values[idx])
                    else:  # "str"
                        static_info[info] = values[idx]
                _cached_static_info[device] = static_info
            except subprocess.CalledProcessError as e:
                raise RuntimeError("Failed to get static information for NVIDIA GPU.") from e

    return _cached_static_info[device]

def _compute_memory_used_percentage(memory_used: float, total_memory: float) -> float:
    return (memory_used / total_memory) * 100

_QUERY_MAPPING = {
    "GPU_NAME": "name",
    "TOTAL_MEMORY": "memory.total",
    "MEMORY_USED": "memory.used",
    "AVAILABLE_MEMORY": "memory.free",
    "UTILIZATION": "utilization.gpu",
    "WATTAGE": "power.draw",
    "TEMPERATURE": "temperature.gpu",
    "FAN_SPEED": "fan.speed",
    "POWER_LIMIT": "power.max_limit",
}
_DERIVED_PROPERTIES = {
    "MEMORY_USED_PERCENTAGE": (("MEMORY_USED", "TOTAL_MEMORY"), _compute_memory_used_percentage),
}
assert set(information_list).issubset(set(_QUERY_MAPPING.keys()).union(_DERIVED_PROPERTIES.keys())), "Invalid!"
assert set(_QUERY_MAPPING.keys()).isdisjoint(set(_DERIVED_PROPERTIES.keys())), "Invalid!"

def _get_property(device: int, property_name: str, gpu_data: dict[str, Any]) -> Any:
    """
    Returns the value of the specified property for the specified device.
    """
    if property_name in gpu_data:
        return gpu_data[property_name]
    elif info_code.is_static(property_name):
        static_info = get_static_info(device)
        return static_info[property_name]
    else:
        raise ValueError("Invalid property name: {}".format(property_name))

def query_devices(devices: list[int], information: list[str]) -> dict[int, dict[str, Any]]:
    """
    Queries the specified devices for the requested information.
    """
    available_devices = list_devices()
    if not set(devices).issubset(set(available_devices)):
        invalid_devices = set(devices) - set(available_devices)
        raise ValueError(f"Invalid device IDs specified: {invalid_devices}")

    if not set(information).issubset(set(information_list)):
        invalid_info = set(information) - set(information_list)
        raise ValueError(f"Invalid information requested: {invalid_info}")
    
    # Check the required properties of derived properties are included
    for info in information:
        if info in _DERIVED_PROPERTIES:
            for info_depends in _DERIVED_PROPERTIES[info][0]:
                if not info_code.is_static(info_depends) and info_depends not in information:
                    raise ValueError(f"Derived property {info} requires {info_depends} to be included in the query.")

    # Map the information keys to nvidia-smi query parameters. Derived properties will be calculated separately
    query_params = []
    for info in information:
        if info in _QUERY_MAPPING:
            query_params.append(_QUERY_MAPPING[info])
    query_params.append("index") # Always include the GPU index to map results

    # Run nvidia-smi to get the information
    try:
        cmd = ["nvidia-smi", f"--query-gpu={','.join(query_params)}", "--format=csv,noheader,nounits"]
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=False
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Failed to query NVIDIA GPUs.") from e

    data: dict[int, dict[str, Any]] = {}
    lines = output.strip().split('\n')
    for line in lines:
        values = [value.strip() for value in line.split(',')]
        # The last value is the GPU index
        gpu_index = int(values[-1])
        if gpu_index in devices:
            gpu_data: dict[str, Any] = {}
            # Get the queried properties
            q_idx = 0
            for info in information:
                if info in _QUERY_MAPPING:
                    info_type = information_details[info]["type"]
                    if info_type == "int":
                        gpu_data[info] = int(float(values[q_idx]))
                    elif info_type == "float":
                        gpu_data[info] = float(values[q_idx])
                    else:  # "str"
                        gpu_data[info] = values[q_idx]
                    q_idx += 1
            
            # Calculate derived properties
            for info in information:
                if info in _DERIVED_PROPERTIES:
                    info_type = information_details[info]["type"]
                    # call the function
                    value = _DERIVED_PROPERTIES[info][1](*[_get_property(gpu_index, info_key, gpu_data)
                                                           for info_key in _DERIVED_PROPERTIES[info][0]])
                    if info_type == "int":
                        gpu_data[info] = int(float(value))
                    elif info_type == "float":
                        gpu_data[info] = float(value)
                    else:  # "str"
                        gpu_data[info] = value
            
            data[gpu_index] = gpu_data

    return data