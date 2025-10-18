from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast, Union
from typing import Literal


T = TypeVar("T", bound="SimulationCreateSchemaSourceDataType0Schedule")


@_attrs_define
class SimulationCreateSchemaSourceDataType0Schedule:
    """
    Attributes:
        once_every (Union[Literal['day'], Literal['month'], Literal['week']]):
        around (str):
        time_zone (str):
        send_email_when_complete (bool):
        on (Union[Literal['1'], Literal['10'], Literal['11'], Literal['12'], Literal['13'], Literal['14'],
            Literal['15'], Literal['16'], Literal['17'], Literal['18'], Literal['19'], Literal['2'], Literal['20'],
            Literal['21'], Literal['22'], Literal['23'], Literal['24'], Literal['25'], Literal['26'], Literal['27'],
            Literal['28'], Literal['29'], Literal['3'], Literal['30'], Literal['31'], Literal['4'], Literal['5'],
            Literal['6'], Literal['7'], Literal['8'], Literal['9'], Literal['Friday'], Literal['Monday'],
            Literal['Saturday'], Literal['Sunday'], Literal['Thursday'], Literal['Tuesday'], Literal['Wednesday'], Unset]):
        email_address (Union[Unset, str]):
    """

    once_every: Union[Literal["day"], Literal["month"], Literal["week"]]
    around: str
    time_zone: str
    send_email_when_complete: bool
    on: Union[
        Literal["1"],
        Literal["10"],
        Literal["11"],
        Literal["12"],
        Literal["13"],
        Literal["14"],
        Literal["15"],
        Literal["16"],
        Literal["17"],
        Literal["18"],
        Literal["19"],
        Literal["2"],
        Literal["20"],
        Literal["21"],
        Literal["22"],
        Literal["23"],
        Literal["24"],
        Literal["25"],
        Literal["26"],
        Literal["27"],
        Literal["28"],
        Literal["29"],
        Literal["3"],
        Literal["30"],
        Literal["31"],
        Literal["4"],
        Literal["5"],
        Literal["6"],
        Literal["7"],
        Literal["8"],
        Literal["9"],
        Literal["Friday"],
        Literal["Monday"],
        Literal["Saturday"],
        Literal["Sunday"],
        Literal["Thursday"],
        Literal["Tuesday"],
        Literal["Wednesday"],
        Unset,
    ] = UNSET
    email_address: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        once_every: Union[Literal["day"], Literal["month"], Literal["week"]]
        once_every = self.once_every

        around = self.around

        time_zone = self.time_zone

        send_email_when_complete = self.send_email_when_complete

        on: Union[
            Literal["1"],
            Literal["10"],
            Literal["11"],
            Literal["12"],
            Literal["13"],
            Literal["14"],
            Literal["15"],
            Literal["16"],
            Literal["17"],
            Literal["18"],
            Literal["19"],
            Literal["2"],
            Literal["20"],
            Literal["21"],
            Literal["22"],
            Literal["23"],
            Literal["24"],
            Literal["25"],
            Literal["26"],
            Literal["27"],
            Literal["28"],
            Literal["29"],
            Literal["3"],
            Literal["30"],
            Literal["31"],
            Literal["4"],
            Literal["5"],
            Literal["6"],
            Literal["7"],
            Literal["8"],
            Literal["9"],
            Literal["Friday"],
            Literal["Monday"],
            Literal["Saturday"],
            Literal["Sunday"],
            Literal["Thursday"],
            Literal["Tuesday"],
            Literal["Wednesday"],
            Unset,
        ]
        if isinstance(self.on, Unset):
            on = UNSET
        else:
            on = self.on

        email_address = self.email_address

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        def _parse_once_every(
            data: object,
        ) -> Union[Literal["day"], Literal["month"], Literal["week"]]:
            once_every_type_0 = cast(Literal["day"], data)
            if once_every_type_0 != "day":
                raise ValueError(
                    f"onceEvery_type_0 must match const 'day', got '{once_every_type_0}'"
                )
            return once_every_type_0
            once_every_type_1 = cast(Literal["week"], data)
            if once_every_type_1 != "week":
                raise ValueError(
                    f"onceEvery_type_1 must match const 'week', got '{once_every_type_1}'"
                )
            return once_every_type_1
            once_every_type_2 = cast(Literal["month"], data)
            if once_every_type_2 != "month":
                raise ValueError(
                    f"onceEvery_type_2 must match const 'month', got '{once_every_type_2}'"
                )
            return once_every_type_2

        once_every = _parse_once_every(d.pop("onceEvery"))

        around = d.pop("around")

        time_zone = d.pop("timeZone")

        send_email_when_complete = d.pop("sendEmailWhenComplete")

        def _parse_on(
            data: object,
        ) -> Union[
            Literal["1"],
            Literal["10"],
            Literal["11"],
            Literal["12"],
            Literal["13"],
            Literal["14"],
            Literal["15"],
            Literal["16"],
            Literal["17"],
            Literal["18"],
            Literal["19"],
            Literal["2"],
            Literal["20"],
            Literal["21"],
            Literal["22"],
            Literal["23"],
            Literal["24"],
            Literal["25"],
            Literal["26"],
            Literal["27"],
            Literal["28"],
            Literal["29"],
            Literal["3"],
            Literal["30"],
            Literal["31"],
            Literal["4"],
            Literal["5"],
            Literal["6"],
            Literal["7"],
            Literal["8"],
            Literal["9"],
            Literal["Friday"],
            Literal["Monday"],
            Literal["Saturday"],
            Literal["Sunday"],
            Literal["Thursday"],
            Literal["Tuesday"],
            Literal["Wednesday"],
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            on_type_0_type_0 = cast(Literal["Sunday"], data)
            if on_type_0_type_0 != "Sunday":
                raise ValueError(
                    f"on_type_0_type_0 must match const 'Sunday', got '{on_type_0_type_0}'"
                )
            return on_type_0_type_0
            on_type_0_type_1 = cast(Literal["Monday"], data)
            if on_type_0_type_1 != "Monday":
                raise ValueError(
                    f"on_type_0_type_1 must match const 'Monday', got '{on_type_0_type_1}'"
                )
            return on_type_0_type_1
            on_type_0_type_2 = cast(Literal["Tuesday"], data)
            if on_type_0_type_2 != "Tuesday":
                raise ValueError(
                    f"on_type_0_type_2 must match const 'Tuesday', got '{on_type_0_type_2}'"
                )
            return on_type_0_type_2
            on_type_0_type_3 = cast(Literal["Wednesday"], data)
            if on_type_0_type_3 != "Wednesday":
                raise ValueError(
                    f"on_type_0_type_3 must match const 'Wednesday', got '{on_type_0_type_3}'"
                )
            return on_type_0_type_3
            on_type_0_type_4 = cast(Literal["Thursday"], data)
            if on_type_0_type_4 != "Thursday":
                raise ValueError(
                    f"on_type_0_type_4 must match const 'Thursday', got '{on_type_0_type_4}'"
                )
            return on_type_0_type_4
            on_type_0_type_5 = cast(Literal["Friday"], data)
            if on_type_0_type_5 != "Friday":
                raise ValueError(
                    f"on_type_0_type_5 must match const 'Friday', got '{on_type_0_type_5}'"
                )
            return on_type_0_type_5
            on_type_0_type_6 = cast(Literal["Saturday"], data)
            if on_type_0_type_6 != "Saturday":
                raise ValueError(
                    f"on_type_0_type_6 must match const 'Saturday', got '{on_type_0_type_6}'"
                )
            return on_type_0_type_6
            on_type_1_type_0 = cast(Literal["1"], data)
            if on_type_1_type_0 != "1":
                raise ValueError(
                    f"on_type_1_type_0 must match const '1', got '{on_type_1_type_0}'"
                )
            return on_type_1_type_0
            on_type_1_type_1 = cast(Literal["2"], data)
            if on_type_1_type_1 != "2":
                raise ValueError(
                    f"on_type_1_type_1 must match const '2', got '{on_type_1_type_1}'"
                )
            return on_type_1_type_1
            on_type_1_type_2 = cast(Literal["3"], data)
            if on_type_1_type_2 != "3":
                raise ValueError(
                    f"on_type_1_type_2 must match const '3', got '{on_type_1_type_2}'"
                )
            return on_type_1_type_2
            on_type_1_type_3 = cast(Literal["4"], data)
            if on_type_1_type_3 != "4":
                raise ValueError(
                    f"on_type_1_type_3 must match const '4', got '{on_type_1_type_3}'"
                )
            return on_type_1_type_3
            on_type_1_type_4 = cast(Literal["5"], data)
            if on_type_1_type_4 != "5":
                raise ValueError(
                    f"on_type_1_type_4 must match const '5', got '{on_type_1_type_4}'"
                )
            return on_type_1_type_4
            on_type_1_type_5 = cast(Literal["6"], data)
            if on_type_1_type_5 != "6":
                raise ValueError(
                    f"on_type_1_type_5 must match const '6', got '{on_type_1_type_5}'"
                )
            return on_type_1_type_5
            on_type_1_type_6 = cast(Literal["7"], data)
            if on_type_1_type_6 != "7":
                raise ValueError(
                    f"on_type_1_type_6 must match const '7', got '{on_type_1_type_6}'"
                )
            return on_type_1_type_6
            on_type_1_type_7 = cast(Literal["8"], data)
            if on_type_1_type_7 != "8":
                raise ValueError(
                    f"on_type_1_type_7 must match const '8', got '{on_type_1_type_7}'"
                )
            return on_type_1_type_7
            on_type_1_type_8 = cast(Literal["9"], data)
            if on_type_1_type_8 != "9":
                raise ValueError(
                    f"on_type_1_type_8 must match const '9', got '{on_type_1_type_8}'"
                )
            return on_type_1_type_8
            on_type_1_type_9 = cast(Literal["10"], data)
            if on_type_1_type_9 != "10":
                raise ValueError(
                    f"on_type_1_type_9 must match const '10', got '{on_type_1_type_9}'"
                )
            return on_type_1_type_9
            on_type_1_type_10 = cast(Literal["11"], data)
            if on_type_1_type_10 != "11":
                raise ValueError(
                    f"on_type_1_type_10 must match const '11', got '{on_type_1_type_10}'"
                )
            return on_type_1_type_10
            on_type_1_type_11 = cast(Literal["12"], data)
            if on_type_1_type_11 != "12":
                raise ValueError(
                    f"on_type_1_type_11 must match const '12', got '{on_type_1_type_11}'"
                )
            return on_type_1_type_11
            on_type_1_type_12 = cast(Literal["13"], data)
            if on_type_1_type_12 != "13":
                raise ValueError(
                    f"on_type_1_type_12 must match const '13', got '{on_type_1_type_12}'"
                )
            return on_type_1_type_12
            on_type_1_type_13 = cast(Literal["14"], data)
            if on_type_1_type_13 != "14":
                raise ValueError(
                    f"on_type_1_type_13 must match const '14', got '{on_type_1_type_13}'"
                )
            return on_type_1_type_13
            on_type_1_type_14 = cast(Literal["15"], data)
            if on_type_1_type_14 != "15":
                raise ValueError(
                    f"on_type_1_type_14 must match const '15', got '{on_type_1_type_14}'"
                )
            return on_type_1_type_14
            on_type_1_type_15 = cast(Literal["16"], data)
            if on_type_1_type_15 != "16":
                raise ValueError(
                    f"on_type_1_type_15 must match const '16', got '{on_type_1_type_15}'"
                )
            return on_type_1_type_15
            on_type_1_type_16 = cast(Literal["17"], data)
            if on_type_1_type_16 != "17":
                raise ValueError(
                    f"on_type_1_type_16 must match const '17', got '{on_type_1_type_16}'"
                )
            return on_type_1_type_16
            on_type_1_type_17 = cast(Literal["18"], data)
            if on_type_1_type_17 != "18":
                raise ValueError(
                    f"on_type_1_type_17 must match const '18', got '{on_type_1_type_17}'"
                )
            return on_type_1_type_17
            on_type_1_type_18 = cast(Literal["19"], data)
            if on_type_1_type_18 != "19":
                raise ValueError(
                    f"on_type_1_type_18 must match const '19', got '{on_type_1_type_18}'"
                )
            return on_type_1_type_18
            on_type_1_type_19 = cast(Literal["20"], data)
            if on_type_1_type_19 != "20":
                raise ValueError(
                    f"on_type_1_type_19 must match const '20', got '{on_type_1_type_19}'"
                )
            return on_type_1_type_19
            on_type_1_type_20 = cast(Literal["21"], data)
            if on_type_1_type_20 != "21":
                raise ValueError(
                    f"on_type_1_type_20 must match const '21', got '{on_type_1_type_20}'"
                )
            return on_type_1_type_20
            on_type_1_type_21 = cast(Literal["22"], data)
            if on_type_1_type_21 != "22":
                raise ValueError(
                    f"on_type_1_type_21 must match const '22', got '{on_type_1_type_21}'"
                )
            return on_type_1_type_21
            on_type_1_type_22 = cast(Literal["23"], data)
            if on_type_1_type_22 != "23":
                raise ValueError(
                    f"on_type_1_type_22 must match const '23', got '{on_type_1_type_22}'"
                )
            return on_type_1_type_22
            on_type_1_type_23 = cast(Literal["24"], data)
            if on_type_1_type_23 != "24":
                raise ValueError(
                    f"on_type_1_type_23 must match const '24', got '{on_type_1_type_23}'"
                )
            return on_type_1_type_23
            on_type_1_type_24 = cast(Literal["25"], data)
            if on_type_1_type_24 != "25":
                raise ValueError(
                    f"on_type_1_type_24 must match const '25', got '{on_type_1_type_24}'"
                )
            return on_type_1_type_24
            on_type_1_type_25 = cast(Literal["26"], data)
            if on_type_1_type_25 != "26":
                raise ValueError(
                    f"on_type_1_type_25 must match const '26', got '{on_type_1_type_25}'"
                )
            return on_type_1_type_25
            on_type_1_type_26 = cast(Literal["27"], data)
            if on_type_1_type_26 != "27":
                raise ValueError(
                    f"on_type_1_type_26 must match const '27', got '{on_type_1_type_26}'"
                )
            return on_type_1_type_26
            on_type_1_type_27 = cast(Literal["28"], data)
            if on_type_1_type_27 != "28":
                raise ValueError(
                    f"on_type_1_type_27 must match const '28', got '{on_type_1_type_27}'"
                )
            return on_type_1_type_27
            on_type_1_type_28 = cast(Literal["29"], data)
            if on_type_1_type_28 != "29":
                raise ValueError(
                    f"on_type_1_type_28 must match const '29', got '{on_type_1_type_28}'"
                )
            return on_type_1_type_28
            on_type_1_type_29 = cast(Literal["30"], data)
            if on_type_1_type_29 != "30":
                raise ValueError(
                    f"on_type_1_type_29 must match const '30', got '{on_type_1_type_29}'"
                )
            return on_type_1_type_29
            on_type_1_type_30 = cast(Literal["31"], data)
            if on_type_1_type_30 != "31":
                raise ValueError(
                    f"on_type_1_type_30 must match const '31', got '{on_type_1_type_30}'"
                )
            return on_type_1_type_30

        on = _parse_on(d.pop("on", UNSET))

        email_address = d.pop("emailAddress", UNSET)

        simulation_create_schema_source_data_type_0_schedule = cls(
            once_every=once_every,
            around=around,
            time_zone=time_zone,
            send_email_when_complete=send_email_when_complete,
            on=on,
            email_address=email_address,
        )

        simulation_create_schema_source_data_type_0_schedule.additional_properties = d
        return simulation_create_schema_source_data_type_0_schedule

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
