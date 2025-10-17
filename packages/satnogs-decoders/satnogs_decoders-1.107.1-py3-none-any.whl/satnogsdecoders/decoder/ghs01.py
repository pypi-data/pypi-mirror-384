# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Ghs01(KaitaiStruct):
    """:field callsign: callsign
    :field s: s
    :field rssi: rssi
    :field bat_1v: bat_1v
    :field bat_2v: bat_2v
    :field bat_t: bat_t
    :field solar_minus_x: solar_minus_x
    :field solar_plus_x: solar_plus_x
    :field solar_plus_y: solar_plus_y
    :field solar_minus_y: solar_minus_y
    :field necessary_for_lengthcheck: necessary_for_lengthcheck
    :field beacon: beacon
    
    .. seealso::
       Source - https://gifuhs2022.wordpress.com/通信フォーマット仕様/
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.callsign = (self._io.read_bytes(12)).decode(u"ASCII")
        if not self.callsign == u"jj2yza ghs01":
            raise kaitaistruct.ValidationNotEqualError(u"jj2yza ghs01", self.callsign, self._io, u"/seq/0")
        self.s = (self._io.read_bytes(2)).decode(u"ASCII")
        if not  ((self.s == u"s1") or (self.s == u"s2") or (self.s == u"S1") or (self.s == u"S2")) :
            raise kaitaistruct.ValidationNotAnyOfError(self.s, self._io, u"/seq/1")
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
    def value2_hex_right(self):
        if hasattr(self, '_m_value2_hex_right'):
            return self._m_value2_hex_right

        self._m_value2_hex_right = (self.value2 % 16)
        return getattr(self, '_m_value2_hex_right', None)

    @property
    def value3_hex(self):
        if hasattr(self, '_m_value3_hex'):
            return self._m_value3_hex

        self._m_value3_hex = (u".." if self.value3_hex_left_digit + self.value3_hex_right_digit == u"ff" else self.value3_hex_left_digit + self.value3_hex_right_digit)
        return getattr(self, '_m_value3_hex', None)

    @property
    def rssi(self):
        if hasattr(self, '_m_rssi'):
            return self._m_rssi

        if self.s == u"s1":
            self._m_rssi = self.value1

        return getattr(self, '_m_rssi', None)

    @property
    def value3_hex_right(self):
        if hasattr(self, '_m_value3_hex_right'):
            return self._m_value3_hex_right

        self._m_value3_hex_right = (self.value3 % 16)
        return getattr(self, '_m_value3_hex_right', None)

    @property
    def bat_2v(self):
        if hasattr(self, '_m_bat_2v'):
            return self._m_bat_2v

        if self.s == u"s1":
            self._m_bat_2v = ((self.value3 * 5.0) / 256)

        return getattr(self, '_m_bat_2v', None)

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

        self._m_beacon = self.s + u" " + self.value1_hex + u" " + self.value2_hex + u" " + self.value3_hex + u" " + self.value4_hex
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
    def solar_minus_y(self):
        if hasattr(self, '_m_solar_minus_y'):
            return self._m_solar_minus_y

        if self.s == u"s2":
            self._m_solar_minus_y = ((self.value4 * 5.0) / 256)

        return getattr(self, '_m_solar_minus_y', None)

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

        self._m_value1_hex = (u".." if self.value1_hex_left_digit + self.value1_hex_right_digit == u"ff" else self.value1_hex_left_digit + self.value1_hex_right_digit)
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
    def solar_minus_x(self):
        if hasattr(self, '_m_solar_minus_x'):
            return self._m_solar_minus_x

        if self.s == u"s2":
            self._m_solar_minus_x = ((self.value1 * 5.0) / 256)

        return getattr(self, '_m_solar_minus_x', None)

    @property
    def value2_hex(self):
        if hasattr(self, '_m_value2_hex'):
            return self._m_value2_hex

        self._m_value2_hex = (u".." if self.value2_hex_left_digit + self.value2_hex_right_digit == u"ff" else self.value2_hex_left_digit + self.value2_hex_right_digit)
        return getattr(self, '_m_value2_hex', None)

    @property
    def value4_hex(self):
        if hasattr(self, '_m_value4_hex'):
            return self._m_value4_hex

        self._m_value4_hex = (u".." if self.value4_hex_left_digit + self.value4_hex_right_digit == u"ff" else self.value4_hex_left_digit + self.value4_hex_right_digit)
        return getattr(self, '_m_value4_hex', None)

    @property
    def bat_t(self):
        if hasattr(self, '_m_bat_t'):
            return self._m_bat_t

        if self.s == u"s1":
            self._m_bat_t = ((self.value4 * 5.0) / 256)

        return getattr(self, '_m_bat_t', None)

    @property
    def solar_plus_y(self):
        if hasattr(self, '_m_solar_plus_y'):
            return self._m_solar_plus_y

        if self.s == u"s2":
            self._m_solar_plus_y = ((self.value3 * 5.0) / 256)

        return getattr(self, '_m_solar_plus_y', None)

    @property
    def value3_hex_left_digit(self):
        if hasattr(self, '_m_value3_hex_left_digit'):
            return self._m_value3_hex_left_digit

        self._m_value3_hex_left_digit = (u"a" if str(self.value3_hex_left) == u"10" else (u"b" if str(self.value3_hex_left) == u"11" else (u"c" if str(self.value3_hex_left) == u"12" else (u"d" if str(self.value3_hex_left) == u"13" else (u"e" if str(self.value3_hex_left) == u"14" else (u"f" if str(self.value3_hex_left) == u"15" else str(self.value3_hex_left)))))))
        return getattr(self, '_m_value3_hex_left_digit', None)

    @property
    def solar_plus_x(self):
        if hasattr(self, '_m_solar_plus_x'):
            return self._m_solar_plus_x

        if self.s == u"s2":
            self._m_solar_plus_x = ((self.value2 * 5.0) / 256)

        return getattr(self, '_m_solar_plus_x', None)

    @property
    def value2_hex_left(self):
        if hasattr(self, '_m_value2_hex_left'):
            return self._m_value2_hex_left

        self._m_value2_hex_left = self.value2 // 16
        return getattr(self, '_m_value2_hex_left', None)

    @property
    def bat_1v(self):
        if hasattr(self, '_m_bat_1v'):
            return self._m_bat_1v

        if self.s == u"s1":
            self._m_bat_1v = ((self.value2 * 5.0) / 256)

        return getattr(self, '_m_bat_1v', None)

    @property
    def value1_hex_left_digit(self):
        if hasattr(self, '_m_value1_hex_left_digit'):
            return self._m_value1_hex_left_digit

        self._m_value1_hex_left_digit = (u"a" if str(self.value1_hex_left) == u"10" else (u"b" if str(self.value1_hex_left) == u"11" else (u"c" if str(self.value1_hex_left) == u"12" else (u"d" if str(self.value1_hex_left) == u"13" else (u"e" if str(self.value1_hex_left) == u"14" else (u"f" if str(self.value1_hex_left) == u"15" else str(self.value1_hex_left)))))))
        return getattr(self, '_m_value1_hex_left_digit', None)


