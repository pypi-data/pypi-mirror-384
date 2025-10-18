from enum import Enum


class SimulationSourceDataScheduleOnType1(str, Enum):
    VALUE_0 = "1"
    VALUE_1 = "2"
    VALUE_10 = "11"
    VALUE_11 = "12"
    VALUE_12 = "13"
    VALUE_13 = "14"
    VALUE_14 = "15"
    VALUE_15 = "16"
    VALUE_16 = "17"
    VALUE_17 = "18"
    VALUE_18 = "19"
    VALUE_19 = "20"
    VALUE_2 = "3"
    VALUE_20 = "21"
    VALUE_21 = "22"
    VALUE_22 = "23"
    VALUE_23 = "24"
    VALUE_24 = "25"
    VALUE_25 = "26"
    VALUE_26 = "27"
    VALUE_27 = "28"
    VALUE_28 = "29"
    VALUE_29 = "30"
    VALUE_3 = "4"
    VALUE_30 = "31"
    VALUE_4 = "5"
    VALUE_5 = "6"
    VALUE_6 = "7"
    VALUE_7 = "8"
    VALUE_8 = "9"
    VALUE_9 = "10"

    def __str__(self) -> str:
        return str(self.value)
