from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.simulation_source_data_schedule_on_type_0 import (
    SimulationSourceDataScheduleOnType0,
)
from ..models.simulation_source_data_schedule_on_type_1 import (
    SimulationSourceDataScheduleOnType1,
)
from ..models.simulation_source_data_schedule_once_every import (
    SimulationSourceDataScheduleOnceEvery,
)
from typing import Union


T = TypeVar("T", bound="SimulationSourceDataSchedule")


@_attrs_define
class SimulationSourceDataSchedule:
    """
    Attributes:
        once_every (SimulationSourceDataScheduleOnceEvery):
        around (str):
        time_zone (str):
        send_email_when_complete (bool):
        on (Union[SimulationSourceDataScheduleOnType0, SimulationSourceDataScheduleOnType1, Unset]):
        email_address (Union[Unset, str]):
    """

    once_every: SimulationSourceDataScheduleOnceEvery
    around: str
    time_zone: str
    send_email_when_complete: bool
    on: Union[
        SimulationSourceDataScheduleOnType0, SimulationSourceDataScheduleOnType1, Unset
    ] = UNSET
    email_address: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        once_every = self.once_every.value

        around = self.around

        time_zone = self.time_zone

        send_email_when_complete = self.send_email_when_complete

        on: Union[Unset, str]
        if isinstance(self.on, Unset):
            on = UNSET
        elif isinstance(self.on, SimulationSourceDataScheduleOnType0):
            on = self.on.value
        else:
            on = self.on.value

        email_address = self.email_address

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "onceEvery": once_every,
                "around": around,
                "timeZone": time_zone,
                "sendEmailWhenComplete": send_email_when_complete,
            }
        )
        if on is not UNSET:
            field_dict["on"] = on
        if email_address is not UNSET:
            field_dict["emailAddress"] = email_address

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        once_every = SimulationSourceDataScheduleOnceEvery(d.pop("onceEvery"))

        around = d.pop("around")

        time_zone = d.pop("timeZone")

        send_email_when_complete = d.pop("sendEmailWhenComplete")

        def _parse_on(
            data: object,
        ) -> Union[
            SimulationSourceDataScheduleOnType0,
            SimulationSourceDataScheduleOnType1,
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                on_type_0 = SimulationSourceDataScheduleOnType0(data)

                return on_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, str):
                raise TypeError()
            on_type_1 = SimulationSourceDataScheduleOnType1(data)

            return on_type_1

        on = _parse_on(d.pop("on", UNSET))

        email_address = d.pop("emailAddress", UNSET)

        simulation_source_data_schedule = cls(
            once_every=once_every,
            around=around,
            time_zone=time_zone,
            send_email_when_complete=send_email_when_complete,
            on=on,
            email_address=email_address,
        )

        return simulation_source_data_schedule
