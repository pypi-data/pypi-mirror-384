import random
import time
from datetime import datetime
from typing import Callable, Self

from openmodule.models.base import Direction, Gateway, datetime_to_timestamp
from openmodule.models.presence import PresenceBaseMessage, PresenceEnterMessage, PresenceLeaveMessage, \
    PresenceForwardMessage, PresenceBackwardMessage, PresenceMedia, PresenceChangeMessage
from openmodule.models.vehicle import LPRMedium, LPRCountry, Medium, Vehicle, MakeModel, PresenceAllIds, \
    EnterDirection, QRMedium, MediumType
from openmodule.utils.misc_functions import utcnow


class VehicleBuilder:
    vehicle_id: int
    medium: PresenceMedia

    def __init__(self):
        self.vehicle_id = int(time.time() * 1e9) + random.randint(0, 1000000)
        self.medium = PresenceMedia()
        self.make_model = MakeModel(make="UNKNOWN", make_confidence=0.7, model="UNKNOWN", model_confidence=-1.0)
        self.enter_direction = EnterDirection.unknown
        self.enter_time = utcnow()
        self.leave_time = None

    def vehicle(self) -> Vehicle:
        return Vehicle(
            id=self.vehicle_id,
            lpr=self.medium.lpr,
            qr=self.medium.qr,
            nfc=self.medium.nfc,
            pin=self.medium.pin,
            make_model=self.make_model,
            enter_direction=self.enter_direction,
            enter_time=self.enter_time,
            leave_time=self.leave_time
        )

    def id(self, id: int) -> Self:
        self.vehicle_id = id
        return self

    def lpr(self, country: str | None, plate: str | None = None, state="") -> Self:
        if country is None:
            self.medium.lpr = None
        else:
            self.medium.lpr = LPRMedium(
                id=plate,
                country=LPRCountry(code=country, state=state)
            )
        return self

    def nfc(self, id: str | None) -> Self:
        if id is None:
            self.medium.nfc = id
        else:
            self.medium.nfc = Medium(id=id, type=MediumType.nfc)
        return self

    def qr(self, id: str | None, binary: str | None = None) -> Self:
        if id is None:
            self.medium.qr = id
        else:
            self.medium.qr = QRMedium(id=id, binary=binary)
        return self

    def pin(self, id: str | None) -> Self:
        if id is None:
            self.medium.pin = id
        else:
            self.medium.pin = Medium(id=id, type=MediumType.pin)
        return self

    def set_make_model(self, make_model) -> Self:
        self.make_model = make_model
        return self

    def set_enter_direction(self, enter_direction: EnterDirection) -> Self:
        self.enter_direction = enter_direction
        return self

    def set_enter_time(self, enter_time: datetime) -> Self:
        self.enter_time = enter_time
        return self

    def set_leave_time(self, leave_time: datetime) -> Self:
        self.leave_time = leave_time
        return self


class PresenceSimulator:
    current_present: VehicleBuilder | None = None

    def __init__(self, gate: str, direction: Direction, emit: Callable[[PresenceBaseMessage], None],
                 present_area_name: str | None = None):
        self.gateway = Gateway(gate=gate, direction=direction)
        self.emit = emit
        self.present_area_name = present_area_name or f"{self.gateway.gate}-present"

    def vehicle(self):
        return VehicleBuilder()

    def _common_kwargs(self, vehicle):
        timestamp = datetime_to_timestamp(utcnow())
        all_ids = PresenceAllIds(lpr=None if vehicle.medium.lpr is None else [vehicle.medium.lpr],
                                 qr=None if vehicle.medium.qr is None else [vehicle.medium.qr],
                                 nfc=None if vehicle.medium.nfc is None else [vehicle.medium.nfc],
                                 pin=None if vehicle.medium.pin is None else [vehicle.medium.pin])
        return {
            "vehicle_id": vehicle.vehicle_id,
            "present-area-name": self.present_area_name,
            "last_update": timestamp,
            "name": "presence-sim",
            "source": self.gateway.gate,
            "gateway": self.gateway,
            "medium": vehicle.medium,
            "make_model": vehicle.make_model,
            "all_ids": all_ids,
            "enter_direction": vehicle.enter_direction,
            "enter_time": vehicle.enter_time,
            "leave_time": vehicle.leave_time
        }

    def enter(self, vehicle: VehicleBuilder, enter_time: datetime | None = None):
        vehicle.enter_time = enter_time or vehicle.enter_time
        if self.current_present:
            self.leave()
        self.current_present = vehicle
        self.emit(PresenceEnterMessage(**self._common_kwargs(vehicle)))

    def enter_without_dropping_present_vehicle(self, vehicle: VehicleBuilder, enter_time: datetime | None = None):
        vehicle.enter_time = enter_time or vehicle.enter_time
        self.current_present = vehicle
        self.emit(PresenceEnterMessage(**self._common_kwargs(vehicle)))

    def leave(self, leave_time: datetime | None = None) -> VehicleBuilder:
        self.current_present.leave_time = leave_time or self.current_present.leave_time or utcnow()
        self.emit(PresenceLeaveMessage(**self._common_kwargs(self.current_present)))
        temp = self.current_present
        self.current_present = None
        return temp

    def leave_without_present(self, vehicle: VehicleBuilder, leave_time: datetime | None = None):
        vehicle.leave_time = leave_time or vehicle.leave_time or utcnow()
        self.emit(PresenceLeaveMessage(**self._common_kwargs(vehicle)))

    def forward(self, vehicle: VehicleBuilder | None = None):
        assert vehicle or self.current_present, "a vehicle must be present, or you have to pass a vehicle"
        if not vehicle:
            vehicle = self.leave()
        if vehicle.leave_time is None:  # if leave was not called for this vehicle
            vehicle.leave_time = utcnow()
        self.emit(PresenceForwardMessage(
            **self._common_kwargs(vehicle)
        ))

    def backward(self, vehicle: VehicleBuilder | None = None):
        assert vehicle or self.current_present, "a vehicle must be present, or you have to pass a vehicle"
        if not vehicle:
            vehicle = self.leave()
        if vehicle.leave_time is None:  # if leave was not called for this vehicle
            vehicle.leave_time = utcnow()
        self.emit(PresenceBackwardMessage(
            **self._common_kwargs(vehicle)
        ))

    def change(self, vehicle: VehicleBuilder):
        assert self.current_present, "a vehicle must be present"
        assert self.current_present.id == vehicle.id, "vehicle id must stay the same"
        self.current_present = vehicle
        self.emit(PresenceChangeMessage(
            **self._common_kwargs(vehicle),
        ))

    def change_before_enter(self, vehicle: VehicleBuilder):
        if self.current_present:
            self.leave()
        self.current_present = vehicle
        self.emit(PresenceChangeMessage(**self._common_kwargs(vehicle)))

    def change_vehicle_and_id(self, vehicle: VehicleBuilder):
        assert self.current_present, "a vehicle must be present"
        assert self.current_present.id != vehicle.id, "vehicle id must change"
        self.current_present = vehicle
        self.emit(PresenceChangeMessage(
            **self._common_kwargs(vehicle),
            change_vehicle_id=True
        ))
