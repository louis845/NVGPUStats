import time
from typing import Any, Generator

from .nvda_query import query_devices, list_devices
from .information import information_list, information_details

def monitor(devices: list[int], information: list[str]) -> Generator[tuple[float, dict[int, dict[str, Any]]], bool, None]:
    """
    Generator function that periodically queries the GPU devices for the specified information.
    """
    # Validate devices and information
    available_devices = list_devices()
    if not set(devices).issubset(set(available_devices)):
        invalid_devices = set(devices) - set(available_devices)
        raise ValueError(f"Invalid device IDs specified: {invalid_devices}")

    if not set(information).issubset(set(information_list)):
        invalid_info = set(information) - set(information_list)
        raise ValueError(f"Invalid information requested: {invalid_info}")

    # Check that all information is not static
    for info in information:
        if information_details[info]["is_static"]:
            raise ValueError(f"Information '{info}' is static and cannot be monitored.")

    while True:
        current_time = time.time()
        data = query_devices(devices, information)
        # Yield the current data point
        control = yield (current_time, data)
        # Control the continuation based on the value sent
        if (control is None) or (not isinstance(control, bool)) or (not control):
            break

def active_monitor(
    period: float,
    total_time: float,
    devices: list[int],
    information: list[str]
) -> list[tuple[float, dict[int, dict[str, Any]]]]:
    """
    Collects GPU information at regular intervals over a total duration.
    Returns a list of tuples with timestamps and GPU data.
    """
    gen = monitor(devices, information)
    next(gen)  # Initialize the generator

    collected_data: list[tuple[float, dict[int, dict[str, Any]]]] = []
    start_time = time.time()
    prev_time = None
    while True:
        cur_time = time.time()
        if (cur_time - start_time) > total_time:
            break
        if prev_time is not None:
            sleep_time = period - (cur_time - prev_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
        prev_time = time.time()
        timestamp, data = gen.send(True)
        collected_data.append((timestamp, data))
    # Stop the generator
    try:
        gen.send(False)
    except StopIteration:
        pass
    return collected_data