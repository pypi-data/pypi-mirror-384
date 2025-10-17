# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Starsme2(KaitaiStruct):
    """:field s: s
    :field beacon_no: beacon_no
    :field rssi: rssi
    :field micro_switch_status_deployment: micro_switch_status_deployment
    :field micro_switch_status_mission: micro_switch_status_mission
    :field micro_switch_status_paddle: micro_switch_status_paddle
    :field bus_voltage: bus_voltage
    :field bus_current: bus_current
    :field main_cpu_voltage: main_cpu_voltage
    :field battery_voltage: battery_voltage
    :field beacon: beacon
    
    .. seealso::
       Source - http://stars.eng.shizuoka.ac.jp/english/CW_Telemetry_format.pdf
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.identifier = (self._io.read_bytes(6)).decode(u"ASCII")
        if not  ((self.identifier == u"jj2yxo")) :
            raise kaitaistruct.ValidationNotAnyOfError(self.identifier, self._io, u"/seq/0")
        self.s = (self._io.read_bytes(1)).decode(u"ASCII")
        if not  ((self.s == u"s")) :
            raise kaitaistruct.ValidationNotAnyOfError(self.s, self._io, u"/seq/1")
        self.beacon_no = (self._io.read_bytes(1)).decode(u"ASCII")
        if not  ((self.beacon_no == u"1") or (self.beacon_no == u"2")) :
            raise kaitaistruct.ValidationNotAnyOfError(self.beacon_no, self._io, u"/seq/2")
        self.value1 = self._io.read_u1()
        self.value2 = self._io.read_u1()
        self.value3 = self._io.read_u1()
        self.value4 = self._io.read_u1()
        self.lengthcheck = (self._io.read_bytes_full()).decode(u"utf-8")

    @property
    def value3_hex_right_digit(self):
        if hasattr(self, '_m_value3_hex_right_digit'):
            return self._m_value3_hex_right_digit

        self._m_value3_hex_right_digit = (u"a" if str(self.value3_hex_right) == u"10" else (u"b" if str(self.value3_hex_right) == u"11" else (u"c" if str(self.value3_hex_right) == u"12" else (u"d" if str(self.value3_hex_right) == u"13" else (u"e" if str(self.value3_hex_right) == u"14" else (u"f" if str(self.value3_hex_right) == u"15" else str(self.value3_hex_right)))))))
        return getattr(self, '_m_value3_hex_right_digit', None)

    @property
    def micro_switch_status_deployment(self):
        if hasattr(self, '_m_micro_switch_status_deployment'):
            return self._m_micro_switch_status_deployment

        if self.beacon_no == u"1":
            self._m_micro_switch_status_deployment = self.value2

        return getattr(self, '_m_micro_switch_status_deployment', None)

    @property
    def necessary_for_lengthcheck(self):
        if hasattr(self, '_m_necessary_for_lengthcheck'):
            return self._m_necessary_for_lengthcheck

        if len(self.lengthcheck) != 0:
            self._m_necessary_for_lengthcheck = int(self.lengthcheck) // 0

        return getattr(self, '_m_necessary_for_lengthcheck', None)

    @property
    def value1_hex_left(self):
        if hasattr(self, '_m_value1_hex_left'):
            return self._m_value1_hex_left

        self._m_value1_hex_left = self.value1 // 16
        return getattr(self, '_m_value1_hex_left', None)

    @property
    def micro_switch_status_mission(self):
        if hasattr(self, '_m_micro_switch_status_mission'):
            return self._m_micro_switch_status_mission

        if self.beacon_no == u"1":
            self._m_micro_switch_status_mission = self.value3

        return getattr(self, '_m_micro_switch_status_mission', None)

    @property
    def value2_hex_right(self):
        if hasattr(self, '_m_value2_hex_right'):
            return self._m_value2_hex_right

        self._m_value2_hex_right = (self.value2 % 16)
        return getattr(self, '_m_value2_hex_right', None)

    @property
    def value3_hex(self):
        if hasattr(self, '_m_value3_hex'):
            return self._m_value3_hex

        self._m_value3_hex = self.value3_hex_left_digit + self.value3_hex_right_digit
        return getattr(self, '_m_value3_hex', None)

    @property
    def rssi(self):
        if hasattr(self, '_m_rssi'):
            return self._m_rssi

        if self.beacon_no == u"1":
            self._m_rssi = self.value1

        return getattr(self, '_m_rssi', None)

    @property
    def value3_hex_right(self):
        if hasattr(self, '_m_value3_hex_right'):
            return self._m_value3_hex_right

        self._m_value3_hex_right = (self.value3 % 16)
        return getattr(self, '_m_value3_hex_right', None)

    @property
    def battery_voltage(self):
        if hasattr(self, '_m_battery_voltage'):
            return self._m_battery_voltage

        if self.beacon_no == u"2":
            self._m_battery_voltage = (self.value4 * 0.0195)

        return getattr(self, '_m_battery_voltage', None)

    @property
    def value1_hex_right_digit(self):
        if hasattr(self, '_m_value1_hex_right_digit'):
            return self._m_value1_hex_right_digit

        self._m_value1_hex_right_digit = (u"a" if str(self.value1_hex_right) == u"10" else (u"b" if str(self.value1_hex_right) == u"11" else (u"c" if str(self.value1_hex_right) == u"12" else (u"d" if str(self.value1_hex_right) == u"13" else (u"e" if str(self.value1_hex_right) == u"14" else (u"f" if str(self.value1_hex_right) == u"15" else str(self.value1_hex_right)))))))
        return getattr(self, '_m_value1_hex_right_digit', None)

    @property
    def beacon(self):
        if hasattr(self, '_m_beacon'):
            return self._m_beacon

        self._m_beacon = self.s + self.beacon_no + u" " + self.value1_hex + u" " + self.value2_hex + u" " + self.value3_hex + u" " + self.value4_hex
        return getattr(self, '_m_beacon', None)

    @property
    def value3_hex_left(self):
        if hasattr(self, '_m_value3_hex_left'):
            return self._m_value3_hex_left

        self._m_value3_hex_left = self.value3 // 16
        return getattr(self, '_m_value3_hex_left', None)

    @property
    def value4_hex_left_digit(self):
        if hasattr(self, '_m_value4_hex_left_digit'):
            return self._m_value4_hex_left_digit

        self._m_value4_hex_left_digit = (u"a" if str(self.value4_hex_left) == u"10" else (u"b" if str(self.value4_hex_left) == u"11" else (u"c" if str(self.value4_hex_left) == u"12" else (u"d" if str(self.value4_hex_left) == u"13" else (u"e" if str(self.value4_hex_left) == u"14" else (u"f" if str(self.value4_hex_left) == u"15" else str(self.value4_hex_left)))))))
        return getattr(self, '_m_value4_hex_left_digit', None)

    @property
    def value1_hex_right(self):
        if hasattr(self, '_m_value1_hex_right'):
            return self._m_value1_hex_right

        self._m_value1_hex_right = (self.value1 % 16)
        return getattr(self, '_m_value1_hex_right', None)

    @property
    def value4_hex_right(self):
        if hasattr(self, '_m_value4_hex_right'):
            return self._m_value4_hex_right

        self._m_value4_hex_right = (self.value4 % 16)
        return getattr(self, '_m_value4_hex_right', None)

    @property
    def value4_hex_right_digit(self):
        if hasattr(self, '_m_value4_hex_right_digit'):
            return self._m_value4_hex_right_digit

        self._m_value4_hex_right_digit = (u"a" if str(self.value4_hex_right) == u"10" else (u"b" if str(self.value4_hex_right) == u"11" else (u"c" if str(self.value4_hex_right) == u"12" else (u"d" if str(self.value4_hex_right) == u"13" else (u"e" if str(self.value4_hex_right) == u"14" else (u"f" if str(self.value4_hex_right) == u"15" else str(self.value4_hex_right)))))))
        return getattr(self, '_m_value4_hex_right_digit', None)

    @property
    def value1_hex(self):
        if hasattr(self, '_m_value1_hex'):
            return self._m_value1_hex

        self._m_value1_hex = self.value1_hex_left_digit + self.value1_hex_right_digit
        return getattr(self, '_m_value1_hex', None)

    @property
    def value2_hex_right_digit(self):
        if hasattr(self, '_m_value2_hex_right_digit'):
            return self._m_value2_hex_right_digit

        self._m_value2_hex_right_digit = (u"a" if str(self.value2_hex_right) == u"10" else (u"b" if str(self.value2_hex_right) == u"11" else (u"c" if str(self.value2_hex_right) == u"12" else (u"d" if str(self.value2_hex_right) == u"13" else (u"e" if str(self.value2_hex_right) == u"14" else (u"f" if str(self.value2_hex_right) == u"15" else str(self.value2_hex_right)))))))
        return getattr(self, '_m_value2_hex_right_digit', None)

    @property
    def value4_hex_left(self):
        if hasattr(self, '_m_value4_hex_left'):
            return self._m_value4_hex_left

        self._m_value4_hex_left = self.value4 // 16
        return getattr(self, '_m_value4_hex_left', None)

    @property
    def value2_hex_left_digit(self):
        if hasattr(self, '_m_value2_hex_left_digit'):
            return self._m_value2_hex_left_digit

        self._m_value2_hex_left_digit = (u"a" if str(self.value2_hex_left) == u"10" else (u"b" if str(self.value2_hex_left) == u"11" else (u"c" if str(self.value2_hex_left) == u"12" else (u"d" if str(self.value2_hex_left) == u"13" else (u"e" if str(self.value2_hex_left) == u"14" else (u"f" if str(self.value2_hex_left) == u"15" else str(self.value2_hex_left)))))))
        return getattr(self, '_m_value2_hex_left_digit', None)

    @property
    def main_cpu_voltage(self):
        if hasattr(self, '_m_main_cpu_voltage'):
            return self._m_main_cpu_voltage

        if self.beacon_no == u"2":
            self._m_main_cpu_voltage = (self.value3 * 0.039)

        return getattr(self, '_m_main_cpu_voltage', None)

    @property
    def value2_hex(self):
        if hasattr(self, '_m_value2_hex'):
            return self._m_value2_hex

        self._m_value2_hex = self.value2_hex_left_digit + self.value2_hex_right_digit
        return getattr(self, '_m_value2_hex', None)

    @property
    def value4_hex(self):
        if hasattr(self, '_m_value4_hex'):
            return self._m_value4_hex

        self._m_value4_hex = self.value4_hex_left_digit + self.value4_hex_right_digit
        return getattr(self, '_m_value4_hex', None)

    @property
    def bus_current(self):
        if hasattr(self, '_m_bus_current'):
            return self._m_bus_current

        if self.beacon_no == u"2":
            self._m_bus_current = (self.value2 * 0.0296)

        return getattr(self, '_m_bus_current', None)

    @property
    def value3_hex_left_digit(self):
        if hasattr(self, '_m_value3_hex_left_digit'):
            return self._m_value3_hex_left_digit

        self._m_value3_hex_left_digit = (u"a" if str(self.value3_hex_left) == u"10" else (u"b" if str(self.value3_hex_left) == u"11" else (u"c" if str(self.value3_hex_left) == u"12" else (u"d" if str(self.value3_hex_left) == u"13" else (u"e" if str(self.value3_hex_left) == u"14" else (u"f" if str(self.value3_hex_left) == u"15" else str(self.value3_hex_left)))))))
        return getattr(self, '_m_value3_hex_left_digit', None)

    @property
    def bus_voltage(self):
        if hasattr(self, '_m_bus_voltage'):
            return self._m_bus_voltage

        if self.beacon_no == u"2":
            self._m_bus_voltage = (self.value1 * 0.039)

        return getattr(self, '_m_bus_voltage', None)

    @property
    def micro_switch_status_paddle(self):
        if hasattr(self, '_m_micro_switch_status_paddle'):
            return self._m_micro_switch_status_paddle

        if self.beacon_no == u"1":
            self._m_micro_switch_status_paddle = self.value4

        return getattr(self, '_m_micro_switch_status_paddle', None)

    @property
    def value2_hex_left(self):
        if hasattr(self, '_m_value2_hex_left'):
            return self._m_value2_hex_left

        self._m_value2_hex_left = self.value2 // 16
        return getattr(self, '_m_value2_hex_left', None)

    @property
    def value1_hex_left_digit(self):
        if hasattr(self, '_m_value1_hex_left_digit'):
            return self._m_value1_hex_left_digit

        self._m_value1_hex_left_digit = (u"a" if str(self.value1_hex_left) == u"10" else (u"b" if str(self.value1_hex_left) == u"11" else (u"c" if str(self.value1_hex_left) == u"12" else (u"d" if str(self.value1_hex_left) == u"13" else (u"e" if str(self.value1_hex_left) == u"14" else (u"f" if str(self.value1_hex_left) == u"15" else str(self.value1_hex_left)))))))
        return getattr(self, '_m_value1_hex_left_digit', None)


