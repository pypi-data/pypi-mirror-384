from typing import Callable

from openmodule.models.signals import SignalMessage, TriggerSignalsRequest, TriggerSignalsResponse, \
    GetSignalValueRequest, GetSignalValueResponse, SignalType
from openmodule.rpc import RPCClient


class SignalSimulator:
    def __init__(self, emit: Callable[[SignalMessage], None]):
        self.emit = emit
        self._signals = {}

    def add_signal(self, value: bool, additional_data: dict | None, signal_type: SignalType,
                   gate: str | None = None, parking_area_id: str | None = None,
                   signal_name: str | None = None):
        if signal_type == SignalType.custom:
            assert signal_name is not None
            signal_msg = SignalMessage(signal=signal_name, type=signal_type, gate=gate, parking_area_id=parking_area_id,
                                       value=value, additional_data=additional_data)
        elif signal_type == SignalType.parkinglot_full:
            signal_name: str = signal_type.value  # type: ignore (just pycharm)
            signal_msg = SignalMessage(signal=signal_name, type=signal_type,
                                       value=value, additional_data=additional_data)
        elif signal_type == SignalType.area_full:
            assert parking_area_id is not None
            signal_name = f"{parking_area_id}-area_full"
            signal_msg = SignalMessage(signal=signal_name, type=signal_type,  parking_area_id=parking_area_id,
                                       value=value, additional_data=additional_data)
        else:
            assert gate is not None
            signal_name = f"{gate}-{signal_type}"
            signal_msg = SignalMessage(signal=signal_name, type=signal_type,  gate=gate,
                                       value=value, additional_data=additional_data)
        self._signals[signal_msg.signal] = signal_msg

    def remove_signal(self, signal: str):
        self._signals.pop(signal, None)

    def set_signal(self, signal: str, value: bool, additional_data: dict | None = None):
        self._signals[signal].value = value
        self._signals[signal].additional_data = additional_data
        self.emit(self._signals[signal])

    def trigger_signal_callback(self, request: TriggerSignalsRequest, _):
        res = TriggerSignalsResponse(success=True)
        for signal in request.signals:
            if signal in self._signals:
                self.emit(self._signals[signal])
            else:
                res.success = False
        return res

    def get_value_callback(self, request: GetSignalValueRequest, _):
        if request.signal in self._signals:
            return GetSignalValueResponse(value=self._signals[request.signal].value,
                                          additional_data=self._signals[request.signal].additional_data)
        else:
            raise RPCClient.TimeoutError()
