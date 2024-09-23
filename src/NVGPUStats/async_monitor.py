import threading
import time
from typing import Any

from .monitor import monitor

_INIT = 0
_STARTED = 1
_STOPPED = 2

class AsyncMonitor:
    period: float
    devices: list[int]
    information: list[str]
    _thread: threading.Thread
    _stop_event: threading.Event
    _results: list[tuple[float, dict[int, dict[str, Any]]]]
    __state: int

    def __init__(self, period: float, devices: list[int], information: list[str]):
        """
        Initializes the asynchronous monitor.
        """
        self.period = period
        self.devices = devices
        self.information = information
        self._thread: threading.Thread = None
        self._stop_event = threading.Event()
        self._results: list[tuple[float, dict[int, dict[str, Any]]]] = []
        self.__state = _INIT

    def start(self) -> None:
        """
        Starts the monitoring thread.
        """
        if self.__state != _INIT:
            raise RuntimeError("The monitor is already running. Start can only be called once.")
        self.__state = _STARTED
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run)
            self._thread.start()

    def stop(self) -> None:
        """
        Stops the monitoring thread.
        """
        if self.__state != _STARTED:
            raise RuntimeError("The monitor is not running. Stop can only be called right after start.")
        self.__state = _STOPPED
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()

    def get_results(self) -> list[tuple[float, dict[int, dict[str, Any]]]]:
        """
        Returns the collected monitoring results.
        """
        return self._results

    def _run(self) -> None:
        """
        The target function for the monitoring thread.
        """
        gen = monitor(self.devices, self.information)
        next(gen)  # Initialize the generator
        prev_time = None
        while not self._stop_event.is_set():
            cur_time = time.time()
            if prev_time is not None:
                sleep_time = self.period - (cur_time - prev_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            prev_time = time.time()
            timestamp, data = gen.send(True)
            self._results.append((timestamp, data))
        # Stop the generator
        try:
            gen.send(False)
        except StopIteration:
            pass

def convert_to_dict_list(results: list[tuple[float, dict[int, dict[str, Any]]]]) -> dict[str, Any]:
    """
    Converts the results to a list of dictionaries.
    """
    dict_results = {
        "timestamps": [],
        "data": {}
    }
    for timestamp, data in results:
        dict_results["timestamps"].append(timestamp)
        for device, device_data in data.items():
            if device not in dict_results["data"]:
                dict_results["data"][device] = {}
            for key in device_data:
                if key not in dict_results["data"][device]:
                    dict_results["data"][device][key] = []
                dict_results["data"][device][key].append(device_data[key])
    return dict_results