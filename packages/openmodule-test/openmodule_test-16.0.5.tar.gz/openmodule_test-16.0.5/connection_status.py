import threading

from openmodule.connection_status import ConnectionStatus, BridgeStatus, ConnectionRPCResponse


class ConnectionStatusMocker:
    def __init__(self, initial_status: ConnectionRPCResponse):
        self._status = initial_status
        self._previous_status = ConnectionRPCResponse(connected=ConnectionStatus.shutdown)
        self._changed = threading.Condition(threading.Lock())

    def wait_for_change(self, timeout: float = None) -> bool:
        """Returns true when the connection status changes, otherwise waits for the timeout (or infinitely if none)
        and returns false."""
        with self._changed:
            res = self._changed.wait(timeout)
            return res

    @property
    def previous(self) -> ConnectionStatus:
        return self._previous_status.connected

    @property
    def previous_bridge(self) -> BridgeStatus:
        return self._previous_status.bridge_status

    def get(self) -> ConnectionStatus:
        return self._status.connected

    def get_bridge(self) -> BridgeStatus:
        return self._status.bridge_status

    def check_timeout(self) -> None:
        return None

    def change_status(self, status: ConnectionRPCResponse):
        self._previous_status = self._status
        self._status = status
        with self._changed:
            self._changed.notify_all()
