# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Dragonfly(KaitaiStruct):
    """:field cw_name_callsign: id1.id2.cw_name_callsign
    :field bat_v: id1.id2.bat_v
    :field bat_i: id1.id2.bat_i
    :field bat_t: id1.id2.bat_t
    :field kill_main: id1.id2.kill_main
    :field kill_fab: id1.id2.kill_fab
    :field solar_cell_plus_x: id1.id2.solar_cell_plus_x
    :field solar_cell_plus_y: id1.id2.solar_cell_plus_y
    :field solar_cell_plus_z: id1.id2.solar_cell_plus_z
    :field solar_cell_minus_x: id1.id2.solar_cell_minus_x
    :field solar_cell_minus_y: id1.id2.solar_cell_minus_y
    :field solar_cell_minus_z: id1.id2.solar_cell_minus_z
    :field ant_1_deploy: id1.id2.ant_1_deploy
    :field ant_1_set_count: id1.id2.ant_1_set_count
    :field ant_2_deploy: id1.id2.ant_2_deploy
    :field ant_2_set_count: id1.id2.ant_2_set_count
    :field aprs_reference_1: id1.id2.aprs_reference_1
    :field aprs_reference_2: id1.id2.aprs_reference_2
    :field aprs_payload_1: id1.id2.aprs_payload_1
    :field aprs_payload_2: id1.id2.aprs_payload_2
    :field aprs_payload_3: id1.id2.aprs_payload_3
    :field aprs_payload_4: id1.id2.aprs_payload_4
    :field aprs_payload_5: id1.id2.aprs_payload_5
    :field main_pic_power_line_status: id1.id2.main_pic_power_line_status
    :field com_pic_power_line_status: id1.id2.com_pic_power_line_status
    :field v3_3_1_status: id1.id2.v3_3_1_status
    :field v3_3_2_status: id1.id2.v3_3_2_status
    :field v5_status: id1.id2.v5_status
    :field unreg1_status: id1.id2.unreg1_status
    :field unreg2_status: id1.id2.unreg2_status
    :field time_after_last_reset: id1.id2.time_after_last_reset
    :field necessary_for_lengthcheck: id1.id2.necessary_for_lengthcheck
    :field beacon_type: id1.id2.beacon_type
    :field cw_beacon: id1.id2.cw_beacon
    
    :field packet_number: id1.id2.id3.packet_number
    :field bat_v: id1.id2.id3.bat_v
    :field bat_i: id1.id2.id3.bat_i
    :field bat_t: id1.id2.id3.bat_t
    :field kill_main: id1.id2.id3.kill_main
    :field kill_fab: id1.id2.id3.kill_fab
    :field solar_cell_plus_x: id1.id2.id3.solar_cell_plus_x
    :field solar_cell_plus_y: id1.id2.id3.solar_cell_plus_y
    :field solar_cell_plus_z: id1.id2.id3.solar_cell_plus_z
    :field solar_cell_minus_x: id1.id2.id3.solar_cell_minus_x
    :field solar_cell_minus_y: id1.id2.id3.solar_cell_minus_y
    :field solar_cell_minus_z: id1.id2.id3.solar_cell_minus_z
    :field ant_1_deploy: id1.id2.id3.ant_1_deploy
    :field ant_1_set_count: id1.id2.id3.ant_1_set_count
    :field ant_2_deploy: id1.id2.id3.ant_2_deploy
    :field ant_2_set_count: id1.id2.id3.ant_2_set_count
    :field aprs_reference_1: id1.id2.id3.aprs_reference_1
    :field aprs_reference_2: id1.id2.id3.aprs_reference_2
    :field aprs_payload_1: id1.id2.id3.aprs_payload_1
    :field aprs_payload_2: id1.id2.id3.aprs_payload_2
    :field aprs_payload_3: id1.id2.id3.aprs_payload_3
    :field aprs_payload_4: id1.id2.id3.aprs_payload_4
    :field aprs_payload_5: id1.id2.id3.aprs_payload_5
    :field main_pic_power_line_status: id1.id2.id3.main_pic_power_line_status
    :field com_pic_power_line_status: id1.id2.id3.com_pic_power_line_status
    :field v3_3_1_status: id1.id2.id3.v3_3_1_status
    :field v3_3_2_status: id1.id2.id3.v3_3_2_status
    :field v5_status: id1.id2.id3.v5_status
    :field unreg1_status: id1.id2.id3.unreg1_status
    :field unreg2_status: id1.id2.id3.unreg2_status
    :field time_after_last_reset: id1.id2.id3.time_after_last_reset
    :field necessary_for_lengthcheck: id1.id2.id3.necessary_for_lengthcheck
    :field beacon_type: id1.id2.id3.beacon_type
    
    :field digi_dest_callsign: id1.id2.id3.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field digi_src_callsign: id1.id2.id3.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field digi_src_ssid: id1.id2.id3.ax25_frame.ax25_header.src_ssid_raw.ssid
    :field digi_dest_ssid: id1.id2.id3.ax25_frame.ax25_header.dest_ssid_raw.ssid
    :field rpt_instance___callsign: id1.id2.id3.ax25_frame.ax25_header.repeater.rpt_instance.___.rpt_callsign_raw.callsign_ror.callsign
    :field rpt_instance___ssid: id1.id2.id3.ax25_frame.ax25_header.repeater.rpt_instance.___.rpt_ssid_raw.ssid
    :field rpt_instance___hbit: id1.id2.id3.ax25_frame.ax25_header.repeater.rpt_instance.___.rpt_ssid_raw.hbit
    :field digi_ctl: id1.id2.id3.ax25_frame.ax25_header.ctl
    :field digi_pid: id1.id2.id3.ax25_frame.ax25_header.pid
    :field digi_message: id1.id2.id3.ax25_frame.ax25_info.digi_message
    
    .. seealso::
       Source - https://birds-x.birds-project.com/satellite-information/
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.id1 = Dragonfly.Type1(self._io, self, self._root)

    class Type1(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.message_type1
            if _on == 7237954648016840300:
                self.id2 = Dragonfly.Cw(self._io, self, self._root)
            else:
                self.id2 = Dragonfly.GmskOrDigi(self._io, self, self._root)

        @property
        def message_type1(self):
            if hasattr(self, '_m_message_type1'):
                return self._m_message_type1

            _pos = self._io.pos()
            self._io.seek(0)
            self._m_message_type1 = self._io.read_u8be()
            self._io.seek(_pos)
            return getattr(self, '_m_message_type1', None)


    class Gmsk(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.header_and_reserved_1 = self._io.read_u8be()
            self.header_and_reserved_2 = self._io.read_u8be()
            self.header_and_reserved_3 = self._io.read_bits_int_be(24)
            self.packet_number = self._io.read_bits_int_be(24)
            self._io.align_to_byte()
            self.bat_v_raw_1 = self._io.read_u1()
            self.bat_v_raw_2 = self._io.read_u1()
            self.bat_i_raw_1 = self._io.read_u1()
            self.bat_i_raw_2 = self._io.read_u1()
            self.bat_t_raw_1 = self._io.read_u1()
            self.bat_t_raw_2 = self._io.read_u1()
            self.free_1 = self._io.read_bits_int_be(4)
            self.kill_main_boolean = self._io.read_bits_int_be(1) != 0
            self.kill_fab_boolean = self._io.read_bits_int_be(1) != 0
            self.solar_cell_plus_x_boolean = self._io.read_bits_int_be(1) != 0
            self.solar_cell_plus_y_boolean = self._io.read_bits_int_be(1) != 0
            self.free_2 = self._io.read_bits_int_be(4)
            self.solar_cell_plus_z_boolean = self._io.read_bits_int_be(1) != 0
            self.solar_cell_minus_x_boolean = self._io.read_bits_int_be(1) != 0
            self.solar_cell_minus_y_boolean = self._io.read_bits_int_be(1) != 0
            self.solar_cell_minus_z_boolean = self._io.read_bits_int_be(1) != 0
            self.free_3 = self._io.read_bits_int_be(4)
            self.ant_1_deploy_boolean = self._io.read_bits_int_be(1) != 0
            self.ant_1_set_count = self._io.read_bits_int_be(3)
            self.free_4 = self._io.read_bits_int_be(4)
            self.ant_2_deploy_boolean = self._io.read_bits_int_be(1) != 0
            self.ant_2_set_count = self._io.read_bits_int_be(3)
            self.free_5 = self._io.read_bits_int_be(4)
            self.aprs_reference_1_boolean = self._io.read_bits_int_be(1) != 0
            self.aprs_reference_2_boolean = self._io.read_bits_int_be(1) != 0
            self.aprs_payload_1_boolean = self._io.read_bits_int_be(1) != 0
            self.aprs_payload_2_boolean = self._io.read_bits_int_be(1) != 0
            self.free_6 = self._io.read_bits_int_be(4)
            self.aprs_payload_3_boolean = self._io.read_bits_int_be(1) != 0
            self.aprs_payload_4_boolean = self._io.read_bits_int_be(1) != 0
            self.aprs_payload_5_boolean = self._io.read_bits_int_be(1) != 0
            self.free_7 = self._io.read_bits_int_be(5)
            self.main_pic_power_line_status_boolean = self._io.read_bits_int_be(1) != 0
            self.com_pic_power_line_status_boolean = self._io.read_bits_int_be(1) != 0
            self.v3_3_1_status_boolean = self._io.read_bits_int_be(1) != 0
            self.v3_3_2_status_boolean = self._io.read_bits_int_be(1) != 0
            self.free_8 = self._io.read_bits_int_be(4)
            self.v5_status_boolean = self._io.read_bits_int_be(1) != 0
            self.unreg1_status_boolean = self._io.read_bits_int_be(1) != 0
            self.unreg2_status_boolean = self._io.read_bits_int_be(1) != 0
            self._io.align_to_byte()
            self.time_after_last_reset_1 = self._io.read_u1()
            self.time_after_last_reset_2 = self._io.read_u1()
            self.ff = []
            for i in range(65):
                self.ff.append(self._io.read_u1())

            self.lengthcheck = (self._io.read_bytes_full()).decode(u"utf-8")

        @property
        def bat_i_raw(self):
            if hasattr(self, '_m_bat_i_raw'):
                return self._m_bat_i_raw

            self._m_bat_i_raw = ((self.bat_i_raw_1 << 4) + self.bat_i_raw_2)
            return getattr(self, '_m_bat_i_raw', None)

        @property
        def bat_v(self):
            if hasattr(self, '_m_bat_v'):
                return self._m_bat_v

            self._m_bat_v = ((6.512 * self.bat_v_raw) / 256)
            return getattr(self, '_m_bat_v', None)

        @property
        def main_pic_power_line_status(self):
            if hasattr(self, '_m_main_pic_power_line_status'):
                return self._m_main_pic_power_line_status

            self._m_main_pic_power_line_status = int(self.main_pic_power_line_status_boolean)
            return getattr(self, '_m_main_pic_power_line_status', None)

        @property
        def necessary_for_lengthcheck(self):
            if hasattr(self, '_m_necessary_for_lengthcheck'):
                return self._m_necessary_for_lengthcheck

            if len(self.lengthcheck) != 0:
                self._m_necessary_for_lengthcheck = int(self.lengthcheck) // 0

            return getattr(self, '_m_necessary_for_lengthcheck', None)

        @property
        def aprs_payload_3(self):
            if hasattr(self, '_m_aprs_payload_3'):
                return self._m_aprs_payload_3

            self._m_aprs_payload_3 = int(self.aprs_payload_3_boolean)
            return getattr(self, '_m_aprs_payload_3', None)

        @property
        def unreg1_status(self):
            if hasattr(self, '_m_unreg1_status'):
                return self._m_unreg1_status

            self._m_unreg1_status = int(self.unreg1_status_boolean)
            return getattr(self, '_m_unreg1_status', None)

        @property
        def kill_main(self):
            if hasattr(self, '_m_kill_main'):
                return self._m_kill_main

            self._m_kill_main = int(self.kill_main_boolean)
            return getattr(self, '_m_kill_main', None)

        @property
        def unreg2_status(self):
            if hasattr(self, '_m_unreg2_status'):
                return self._m_unreg2_status

            self._m_unreg2_status = int(self.unreg2_status_boolean)
            return getattr(self, '_m_unreg2_status', None)

        @property
        def bat_v_raw(self):
            if hasattr(self, '_m_bat_v_raw'):
                return self._m_bat_v_raw

            self._m_bat_v_raw = ((self.bat_v_raw_1 << 4) + self.bat_v_raw_2)
            return getattr(self, '_m_bat_v_raw', None)

        @property
        def solar_cell_plus_y(self):
            if hasattr(self, '_m_solar_cell_plus_y'):
                return self._m_solar_cell_plus_y

            self._m_solar_cell_plus_y = int(self.solar_cell_plus_y_boolean)
            return getattr(self, '_m_solar_cell_plus_y', None)

        @property
        def aprs_reference_1(self):
            if hasattr(self, '_m_aprs_reference_1'):
                return self._m_aprs_reference_1

            self._m_aprs_reference_1 = int(self.aprs_reference_1_boolean)
            return getattr(self, '_m_aprs_reference_1', None)

        @property
        def aprs_payload_5(self):
            if hasattr(self, '_m_aprs_payload_5'):
                return self._m_aprs_payload_5

            self._m_aprs_payload_5 = int(self.aprs_payload_5_boolean)
            return getattr(self, '_m_aprs_payload_5', None)

        @property
        def ant_2_deploy(self):
            if hasattr(self, '_m_ant_2_deploy'):
                return self._m_ant_2_deploy

            self._m_ant_2_deploy = int(self.ant_2_deploy_boolean)
            return getattr(self, '_m_ant_2_deploy', None)

        @property
        def aprs_payload_2(self):
            if hasattr(self, '_m_aprs_payload_2'):
                return self._m_aprs_payload_2

            self._m_aprs_payload_2 = int(self.aprs_payload_2_boolean)
            return getattr(self, '_m_aprs_payload_2', None)

        @property
        def v5_status(self):
            if hasattr(self, '_m_v5_status'):
                return self._m_v5_status

            self._m_v5_status = int(self.v5_status_boolean)
            return getattr(self, '_m_v5_status', None)

        @property
        def com_pic_power_line_status(self):
            if hasattr(self, '_m_com_pic_power_line_status'):
                return self._m_com_pic_power_line_status

            self._m_com_pic_power_line_status = int(self.com_pic_power_line_status_boolean)
            return getattr(self, '_m_com_pic_power_line_status', None)

        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = u"GMSK"
            return getattr(self, '_m_beacon_type', None)

        @property
        def solar_cell_plus_z(self):
            if hasattr(self, '_m_solar_cell_plus_z'):
                return self._m_solar_cell_plus_z

            self._m_solar_cell_plus_z = int(self.solar_cell_plus_z_boolean)
            return getattr(self, '_m_solar_cell_plus_z', None)

        @property
        def solar_cell_minus_x(self):
            if hasattr(self, '_m_solar_cell_minus_x'):
                return self._m_solar_cell_minus_x

            self._m_solar_cell_minus_x = int(self.solar_cell_minus_x_boolean)
            return getattr(self, '_m_solar_cell_minus_x', None)

        @property
        def bat_i(self):
            if hasattr(self, '_m_bat_i'):
                return self._m_bat_i

            self._m_bat_i = ((-2.99589 * self.bat_i_raw) + 6129.78533)
            return getattr(self, '_m_bat_i', None)

        @property
        def aprs_reference_2(self):
            if hasattr(self, '_m_aprs_reference_2'):
                return self._m_aprs_reference_2

            self._m_aprs_reference_2 = int(self.aprs_reference_2_boolean)
            return getattr(self, '_m_aprs_reference_2', None)

        @property
        def ant_1_deploy(self):
            if hasattr(self, '_m_ant_1_deploy'):
                return self._m_ant_1_deploy

            self._m_ant_1_deploy = int(self.ant_1_deploy_boolean)
            return getattr(self, '_m_ant_1_deploy', None)

        @property
        def v3_3_1_status(self):
            if hasattr(self, '_m_v3_3_1_status'):
                return self._m_v3_3_1_status

            self._m_v3_3_1_status = int(self.v3_3_1_status_boolean)
            return getattr(self, '_m_v3_3_1_status', None)

        @property
        def bat_t_raw(self):
            if hasattr(self, '_m_bat_t_raw'):
                return self._m_bat_t_raw

            self._m_bat_t_raw = ((self.bat_t_raw_1 << 4) + self.bat_t_raw_2)
            return getattr(self, '_m_bat_t_raw', None)

        @property
        def time_after_last_reset(self):
            if hasattr(self, '_m_time_after_last_reset'):
                return self._m_time_after_last_reset

            self._m_time_after_last_reset = ((self.time_after_last_reset_1 << 4) + self.time_after_last_reset_2)
            return getattr(self, '_m_time_after_last_reset', None)

        @property
        def solar_cell_plus_x(self):
            if hasattr(self, '_m_solar_cell_plus_x'):
                return self._m_solar_cell_plus_x

            self._m_solar_cell_plus_x = int(self.solar_cell_plus_x_boolean)
            return getattr(self, '_m_solar_cell_plus_x', None)

        @property
        def kill_fab(self):
            if hasattr(self, '_m_kill_fab'):
                return self._m_kill_fab

            self._m_kill_fab = int(self.kill_fab_boolean)
            return getattr(self, '_m_kill_fab', None)

        @property
        def bat_t(self):
            if hasattr(self, '_m_bat_t'):
                return self._m_bat_t

            self._m_bat_t = (75 - ((self.bat_t_raw * 97.68) / 256))
            return getattr(self, '_m_bat_t', None)

        @property
        def solar_cell_minus_y(self):
            if hasattr(self, '_m_solar_cell_minus_y'):
                return self._m_solar_cell_minus_y

            self._m_solar_cell_minus_y = int(self.solar_cell_minus_y_boolean)
            return getattr(self, '_m_solar_cell_minus_y', None)

        @property
        def aprs_payload_4(self):
            if hasattr(self, '_m_aprs_payload_4'):
                return self._m_aprs_payload_4

            self._m_aprs_payload_4 = int(self.aprs_payload_4_boolean)
            return getattr(self, '_m_aprs_payload_4', None)

        @property
        def solar_cell_minus_z(self):
            if hasattr(self, '_m_solar_cell_minus_z'):
                return self._m_solar_cell_minus_z

            self._m_solar_cell_minus_z = int(self.solar_cell_minus_z_boolean)
            return getattr(self, '_m_solar_cell_minus_z', None)

        @property
        def v3_3_2_status(self):
            if hasattr(self, '_m_v3_3_2_status'):
                return self._m_v3_3_2_status

            self._m_v3_3_2_status = int(self.v3_3_2_status_boolean)
            return getattr(self, '_m_v3_3_2_status', None)

        @property
        def aprs_payload_1(self):
            if hasattr(self, '_m_aprs_payload_1'):
                return self._m_aprs_payload_1

            self._m_aprs_payload_1 = int(self.aprs_payload_1_boolean)
            return getattr(self, '_m_aprs_payload_1', None)


    class GmskOrDigi(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.message_type2
            if _on == 4043305215:
                self.id3 = Dragonfly.Gmsk(self._io, self, self._root)
            else:
                self.id3 = Dragonfly.Digi(self._io, self, self._root)

        @property
        def message_type2(self):
            if hasattr(self, '_m_message_type2'):
                return self._m_message_type2

            _pos = self._io.pos()
            self._io.seek(15)
            self._m_message_type2 = self._io.read_u4be()
            self._io.seek(_pos)
            return getattr(self, '_m_message_type2', None)


    class Cw(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.cw_name_callsign = (self._io.read_bytes(15)).decode(u"ASCII")
            if not self.cw_name_callsign == u"dragonflyjg6yow":
                raise kaitaistruct.ValidationNotEqualError(u"dragonflyjg6yow", self.cw_name_callsign, self._io, u"/types/cw/seq/0")
            self.bat_v_raw = self._io.read_u1()
            self.bat_i_raw = self._io.read_u1()
            self.bat_t_raw = self._io.read_u1()
            self.value1 = self._io.read_u1()
            self.value2 = self._io.read_u1()
            self.value3 = self._io.read_u1()
            self.value4 = self._io.read_u1()
            self.time_after_last_reset = self._io.read_u1()
            self.lengthcheck = (self._io.read_bytes_full()).decode(u"utf-8")

        @property
        def ant_1_set_count(self):
            if hasattr(self, '_m_ant_1_set_count'):
                return self._m_ant_1_set_count

            self._m_ant_1_set_count = ((self.value2 & 112) >> 4)
            return getattr(self, '_m_ant_1_set_count', None)

        @property
        def bat_v(self):
            if hasattr(self, '_m_bat_v'):
                return self._m_bat_v

            self._m_bat_v = ((6.512 * self.bat_v_raw) / 256)
            return getattr(self, '_m_bat_v', None)

        @property
        def main_pic_power_line_status(self):
            if hasattr(self, '_m_main_pic_power_line_status'):
                return self._m_main_pic_power_line_status

            self._m_main_pic_power_line_status = ((self.value4 & 128) >> 7)
            return getattr(self, '_m_main_pic_power_line_status', None)

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
        def aprs_payload_3(self):
            if hasattr(self, '_m_aprs_payload_3'):
                return self._m_aprs_payload_3

            self._m_aprs_payload_3 = ((self.value3 & 8) >> 3)
            return getattr(self, '_m_aprs_payload_3', None)

        @property
        def value1_hex_left(self):
            if hasattr(self, '_m_value1_hex_left'):
                return self._m_value1_hex_left

            self._m_value1_hex_left = self.value1 // 16
            return getattr(self, '_m_value1_hex_left', None)

        @property
        def unreg1_status(self):
            if hasattr(self, '_m_unreg1_status'):
                return self._m_unreg1_status

            self._m_unreg1_status = ((self.value4 & 4) >> 2)
            return getattr(self, '_m_unreg1_status', None)

        @property
        def kill_main(self):
            if hasattr(self, '_m_kill_main'):
                return self._m_kill_main

            self._m_kill_main = ((self.value1 & 128) >> 7)
            return getattr(self, '_m_kill_main', None)

        @property
        def bat_t_raw_hex_right(self):
            if hasattr(self, '_m_bat_t_raw_hex_right'):
                return self._m_bat_t_raw_hex_right

            self._m_bat_t_raw_hex_right = (self.bat_t_raw % 16)
            return getattr(self, '_m_bat_t_raw_hex_right', None)

        @property
        def unreg2_status(self):
            if hasattr(self, '_m_unreg2_status'):
                return self._m_unreg2_status

            self._m_unreg2_status = ((self.value4 & 2) >> 1)
            return getattr(self, '_m_unreg2_status', None)

        @property
        def time_after_last_reset_hex_right_digit(self):
            if hasattr(self, '_m_time_after_last_reset_hex_right_digit'):
                return self._m_time_after_last_reset_hex_right_digit

            self._m_time_after_last_reset_hex_right_digit = (u"a" if str(self.time_after_last_reset_hex_right) == u"10" else (u"b" if str(self.time_after_last_reset_hex_right) == u"11" else (u"c" if str(self.time_after_last_reset_hex_right) == u"12" else (u"d" if str(self.time_after_last_reset_hex_right) == u"13" else (u"e" if str(self.time_after_last_reset_hex_right) == u"14" else (u"f" if str(self.time_after_last_reset_hex_right) == u"15" else str(self.time_after_last_reset_hex_right)))))))
            return getattr(self, '_m_time_after_last_reset_hex_right_digit', None)

        @property
        def bat_i_raw_hex_right(self):
            if hasattr(self, '_m_bat_i_raw_hex_right'):
                return self._m_bat_i_raw_hex_right

            self._m_bat_i_raw_hex_right = (self.bat_i_raw % 16)
            return getattr(self, '_m_bat_i_raw_hex_right', None)

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
        def bat_v_raw_hex(self):
            if hasattr(self, '_m_bat_v_raw_hex'):
                return self._m_bat_v_raw_hex

            self._m_bat_v_raw_hex = (u".." if self.bat_v_raw_hex_left_digit + self.bat_v_raw_hex_right_digit == u"ff" else self.bat_v_raw_hex_left_digit + self.bat_v_raw_hex_right_digit)
            return getattr(self, '_m_bat_v_raw_hex', None)

        @property
        def value3_hex_right(self):
            if hasattr(self, '_m_value3_hex_right'):
                return self._m_value3_hex_right

            self._m_value3_hex_right = (self.value3 % 16)
            return getattr(self, '_m_value3_hex_right', None)

        @property
        def solar_cell_plus_y(self):
            if hasattr(self, '_m_solar_cell_plus_y'):
                return self._m_solar_cell_plus_y

            self._m_solar_cell_plus_y = ((self.value1 & 16) >> 4)
            return getattr(self, '_m_solar_cell_plus_y', None)

        @property
        def ant_2_set_count(self):
            if hasattr(self, '_m_ant_2_set_count'):
                return self._m_ant_2_set_count

            self._m_ant_2_set_count = (self.value2 & 7)
            return getattr(self, '_m_ant_2_set_count', None)

        @property
        def aprs_reference_1(self):
            if hasattr(self, '_m_aprs_reference_1'):
                return self._m_aprs_reference_1

            self._m_aprs_reference_1 = ((self.value3 & 128) >> 7)
            return getattr(self, '_m_aprs_reference_1', None)

        @property
        def value1_hex_right_digit(self):
            if hasattr(self, '_m_value1_hex_right_digit'):
                return self._m_value1_hex_right_digit

            self._m_value1_hex_right_digit = (u"a" if str(self.value1_hex_right) == u"10" else (u"b" if str(self.value1_hex_right) == u"11" else (u"c" if str(self.value1_hex_right) == u"12" else (u"d" if str(self.value1_hex_right) == u"13" else (u"e" if str(self.value1_hex_right) == u"14" else (u"f" if str(self.value1_hex_right) == u"15" else str(self.value1_hex_right)))))))
            return getattr(self, '_m_value1_hex_right_digit', None)

        @property
        def aprs_payload_5(self):
            if hasattr(self, '_m_aprs_payload_5'):
                return self._m_aprs_payload_5

            self._m_aprs_payload_5 = ((self.value3 & 2) >> 1)
            return getattr(self, '_m_aprs_payload_5', None)

        @property
        def time_after_last_reset_hex_left_digit(self):
            if hasattr(self, '_m_time_after_last_reset_hex_left_digit'):
                return self._m_time_after_last_reset_hex_left_digit

            self._m_time_after_last_reset_hex_left_digit = (u"a" if str(self.time_after_last_reset_hex_left) == u"10" else (u"b" if str(self.time_after_last_reset_hex_left) == u"11" else (u"c" if str(self.time_after_last_reset_hex_left) == u"12" else (u"d" if str(self.time_after_last_reset_hex_left) == u"13" else (u"e" if str(self.time_after_last_reset_hex_left) == u"14" else (u"f" if str(self.time_after_last_reset_hex_left) == u"15" else str(self.time_after_last_reset_hex_left)))))))
            return getattr(self, '_m_time_after_last_reset_hex_left_digit', None)

        @property
        def bat_i_raw_hex_right_digit(self):
            if hasattr(self, '_m_bat_i_raw_hex_right_digit'):
                return self._m_bat_i_raw_hex_right_digit

            self._m_bat_i_raw_hex_right_digit = (u"a" if str(self.bat_i_raw_hex_right) == u"10" else (u"b" if str(self.bat_i_raw_hex_right) == u"11" else (u"c" if str(self.bat_i_raw_hex_right) == u"12" else (u"d" if str(self.bat_i_raw_hex_right) == u"13" else (u"e" if str(self.bat_i_raw_hex_right) == u"14" else (u"f" if str(self.bat_i_raw_hex_right) == u"15" else str(self.bat_i_raw_hex_right)))))))
            return getattr(self, '_m_bat_i_raw_hex_right_digit', None)

        @property
        def ant_2_deploy(self):
            if hasattr(self, '_m_ant_2_deploy'):
                return self._m_ant_2_deploy

            self._m_ant_2_deploy = ((self.value2 & 8) >> 3)
            return getattr(self, '_m_ant_2_deploy', None)

        @property
        def aprs_payload_2(self):
            if hasattr(self, '_m_aprs_payload_2'):
                return self._m_aprs_payload_2

            self._m_aprs_payload_2 = ((self.value3 & 16) >> 4)
            return getattr(self, '_m_aprs_payload_2', None)

        @property
        def time_after_last_reset_hex(self):
            if hasattr(self, '_m_time_after_last_reset_hex'):
                return self._m_time_after_last_reset_hex

            self._m_time_after_last_reset_hex = (u".." if self.time_after_last_reset_hex_left_digit + self.time_after_last_reset_hex_right_digit == u"ff" else self.time_after_last_reset_hex_left_digit + self.time_after_last_reset_hex_right_digit)
            return getattr(self, '_m_time_after_last_reset_hex', None)

        @property
        def v5_status(self):
            if hasattr(self, '_m_v5_status'):
                return self._m_v5_status

            self._m_v5_status = ((self.value4 & 8) >> 3)
            return getattr(self, '_m_v5_status', None)

        @property
        def com_pic_power_line_status(self):
            if hasattr(self, '_m_com_pic_power_line_status'):
                return self._m_com_pic_power_line_status

            self._m_com_pic_power_line_status = ((self.value4 & 64) >> 6)
            return getattr(self, '_m_com_pic_power_line_status', None)

        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = u"CW"
            return getattr(self, '_m_beacon_type', None)

        @property
        def value3_hex_left(self):
            if hasattr(self, '_m_value3_hex_left'):
                return self._m_value3_hex_left

            self._m_value3_hex_left = self.value3 // 16
            return getattr(self, '_m_value3_hex_left', None)

        @property
        def solar_cell_plus_z(self):
            if hasattr(self, '_m_solar_cell_plus_z'):
                return self._m_solar_cell_plus_z

            self._m_solar_cell_plus_z = ((self.value1 & 8) >> 3)
            return getattr(self, '_m_solar_cell_plus_z', None)

        @property
        def solar_cell_minus_x(self):
            if hasattr(self, '_m_solar_cell_minus_x'):
                return self._m_solar_cell_minus_x

            self._m_solar_cell_minus_x = ((self.value1 & 4) >> 2)
            return getattr(self, '_m_solar_cell_minus_x', None)

        @property
        def bat_i_raw_hex_left_digit(self):
            if hasattr(self, '_m_bat_i_raw_hex_left_digit'):
                return self._m_bat_i_raw_hex_left_digit

            self._m_bat_i_raw_hex_left_digit = (u"a" if str(self.bat_i_raw_hex_left) == u"10" else (u"b" if str(self.bat_i_raw_hex_left) == u"11" else (u"c" if str(self.bat_i_raw_hex_left) == u"12" else (u"d" if str(self.bat_i_raw_hex_left) == u"13" else (u"e" if str(self.bat_i_raw_hex_left) == u"14" else (u"f" if str(self.bat_i_raw_hex_left) == u"15" else str(self.bat_i_raw_hex_left)))))))
            return getattr(self, '_m_bat_i_raw_hex_left_digit', None)

        @property
        def bat_i(self):
            if hasattr(self, '_m_bat_i'):
                return self._m_bat_i

            self._m_bat_i = ((-2.99589 * self.bat_i_raw) + 6129.78533)
            return getattr(self, '_m_bat_i', None)

        @property
        def bat_v_raw_hex_right(self):
            if hasattr(self, '_m_bat_v_raw_hex_right'):
                return self._m_bat_v_raw_hex_right

            self._m_bat_v_raw_hex_right = (self.bat_v_raw % 16)
            return getattr(self, '_m_bat_v_raw_hex_right', None)

        @property
        def aprs_reference_2(self):
            if hasattr(self, '_m_aprs_reference_2'):
                return self._m_aprs_reference_2

            self._m_aprs_reference_2 = ((self.value3 & 64) >> 6)
            return getattr(self, '_m_aprs_reference_2', None)

        @property
        def bat_t_raw_hex_left(self):
            if hasattr(self, '_m_bat_t_raw_hex_left'):
                return self._m_bat_t_raw_hex_left

            self._m_bat_t_raw_hex_left = self.bat_t_raw // 16
            return getattr(self, '_m_bat_t_raw_hex_left', None)

        @property
        def ant_1_deploy(self):
            if hasattr(self, '_m_ant_1_deploy'):
                return self._m_ant_1_deploy

            self._m_ant_1_deploy = ((self.value2 & 128) >> 7)
            return getattr(self, '_m_ant_1_deploy', None)

        @property
        def bat_t_raw_hex_left_digit(self):
            if hasattr(self, '_m_bat_t_raw_hex_left_digit'):
                return self._m_bat_t_raw_hex_left_digit

            self._m_bat_t_raw_hex_left_digit = (u"a" if str(self.bat_t_raw_hex_left) == u"10" else (u"b" if str(self.bat_t_raw_hex_left) == u"11" else (u"c" if str(self.bat_t_raw_hex_left) == u"12" else (u"d" if str(self.bat_t_raw_hex_left) == u"13" else (u"e" if str(self.bat_t_raw_hex_left) == u"14" else (u"f" if str(self.bat_t_raw_hex_left) == u"15" else str(self.bat_t_raw_hex_left)))))))
            return getattr(self, '_m_bat_t_raw_hex_left_digit', None)

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
        def time_after_last_reset_hex_right(self):
            if hasattr(self, '_m_time_after_last_reset_hex_right'):
                return self._m_time_after_last_reset_hex_right

            self._m_time_after_last_reset_hex_right = (self.time_after_last_reset % 16)
            return getattr(self, '_m_time_after_last_reset_hex_right', None)

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
        def bat_v_raw_hex_right_digit(self):
            if hasattr(self, '_m_bat_v_raw_hex_right_digit'):
                return self._m_bat_v_raw_hex_right_digit

            self._m_bat_v_raw_hex_right_digit = (u"a" if str(self.bat_v_raw_hex_right) == u"10" else (u"b" if str(self.bat_v_raw_hex_right) == u"11" else (u"c" if str(self.bat_v_raw_hex_right) == u"12" else (u"d" if str(self.bat_v_raw_hex_right) == u"13" else (u"e" if str(self.bat_v_raw_hex_right) == u"14" else (u"f" if str(self.bat_v_raw_hex_right) == u"15" else str(self.bat_v_raw_hex_right)))))))
            return getattr(self, '_m_bat_v_raw_hex_right_digit', None)

        @property
        def bat_v_raw_hex_left(self):
            if hasattr(self, '_m_bat_v_raw_hex_left'):
                return self._m_bat_v_raw_hex_left

            self._m_bat_v_raw_hex_left = self.bat_v_raw // 16
            return getattr(self, '_m_bat_v_raw_hex_left', None)

        @property
        def cw_beacon(self):
            if hasattr(self, '_m_cw_beacon'):
                return self._m_cw_beacon

            self._m_cw_beacon = self.bat_v_raw_hex + self.bat_i_raw_hex + self.bat_t_raw_hex + self.value1_hex + self.value2_hex + self.value3_hex + self.value4_hex + self.time_after_last_reset_hex
            return getattr(self, '_m_cw_beacon', None)

        @property
        def v3_3_1_status(self):
            if hasattr(self, '_m_v3_3_1_status'):
                return self._m_v3_3_1_status

            self._m_v3_3_1_status = ((self.value4 & 32) >> 5)
            return getattr(self, '_m_v3_3_1_status', None)

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
        def bat_t_raw_hex(self):
            if hasattr(self, '_m_bat_t_raw_hex'):
                return self._m_bat_t_raw_hex

            self._m_bat_t_raw_hex = (u".." if self.bat_t_raw_hex_left_digit + self.bat_t_raw_hex_right_digit == u"ff" else self.bat_t_raw_hex_left_digit + self.bat_t_raw_hex_right_digit)
            return getattr(self, '_m_bat_t_raw_hex', None)

        @property
        def solar_cell_plus_x(self):
            if hasattr(self, '_m_solar_cell_plus_x'):
                return self._m_solar_cell_plus_x

            self._m_solar_cell_plus_x = ((self.value1 & 32) >> 5)
            return getattr(self, '_m_solar_cell_plus_x', None)

        @property
        def value2_hex(self):
            if hasattr(self, '_m_value2_hex'):
                return self._m_value2_hex

            self._m_value2_hex = (u".." if self.value2_hex_left_digit + self.value2_hex_right_digit == u"ff" else self.value2_hex_left_digit + self.value2_hex_right_digit)
            return getattr(self, '_m_value2_hex', None)

        @property
        def kill_fab(self):
            if hasattr(self, '_m_kill_fab'):
                return self._m_kill_fab

            self._m_kill_fab = ((self.value1 & 64) >> 6)
            return getattr(self, '_m_kill_fab', None)

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

            self._m_bat_t = (75 - ((self.bat_t_raw * 97.68) / 256))
            return getattr(self, '_m_bat_t', None)

        @property
        def bat_v_raw_hex_left_digit(self):
            if hasattr(self, '_m_bat_v_raw_hex_left_digit'):
                return self._m_bat_v_raw_hex_left_digit

            self._m_bat_v_raw_hex_left_digit = (u"a" if str(self.bat_v_raw_hex_left) == u"10" else (u"b" if str(self.bat_v_raw_hex_left) == u"11" else (u"c" if str(self.bat_v_raw_hex_left) == u"12" else (u"d" if str(self.bat_v_raw_hex_left) == u"13" else (u"e" if str(self.bat_v_raw_hex_left) == u"14" else (u"f" if str(self.bat_v_raw_hex_left) == u"15" else str(self.bat_v_raw_hex_left)))))))
            return getattr(self, '_m_bat_v_raw_hex_left_digit', None)

        @property
        def solar_cell_minus_y(self):
            if hasattr(self, '_m_solar_cell_minus_y'):
                return self._m_solar_cell_minus_y

            self._m_solar_cell_minus_y = ((self.value1 & 2) >> 1)
            return getattr(self, '_m_solar_cell_minus_y', None)

        @property
        def value3_hex_left_digit(self):
            if hasattr(self, '_m_value3_hex_left_digit'):
                return self._m_value3_hex_left_digit

            self._m_value3_hex_left_digit = (u"a" if str(self.value3_hex_left) == u"10" else (u"b" if str(self.value3_hex_left) == u"11" else (u"c" if str(self.value3_hex_left) == u"12" else (u"d" if str(self.value3_hex_left) == u"13" else (u"e" if str(self.value3_hex_left) == u"14" else (u"f" if str(self.value3_hex_left) == u"15" else str(self.value3_hex_left)))))))
            return getattr(self, '_m_value3_hex_left_digit', None)

        @property
        def bat_i_raw_hex_left(self):
            if hasattr(self, '_m_bat_i_raw_hex_left'):
                return self._m_bat_i_raw_hex_left

            self._m_bat_i_raw_hex_left = self.bat_i_raw // 16
            return getattr(self, '_m_bat_i_raw_hex_left', None)

        @property
        def aprs_payload_4(self):
            if hasattr(self, '_m_aprs_payload_4'):
                return self._m_aprs_payload_4

            self._m_aprs_payload_4 = ((self.value3 & 4) >> 2)
            return getattr(self, '_m_aprs_payload_4', None)

        @property
        def solar_cell_minus_z(self):
            if hasattr(self, '_m_solar_cell_minus_z'):
                return self._m_solar_cell_minus_z

            self._m_solar_cell_minus_z = (self.value1 & 1)
            return getattr(self, '_m_solar_cell_minus_z', None)

        @property
        def value2_hex_left(self):
            if hasattr(self, '_m_value2_hex_left'):
                return self._m_value2_hex_left

            self._m_value2_hex_left = self.value2 // 16
            return getattr(self, '_m_value2_hex_left', None)

        @property
        def v3_3_2_status(self):
            if hasattr(self, '_m_v3_3_2_status'):
                return self._m_v3_3_2_status

            self._m_v3_3_2_status = ((self.value4 & 16) >> 4)
            return getattr(self, '_m_v3_3_2_status', None)

        @property
        def bat_t_raw_hex_right_digit(self):
            if hasattr(self, '_m_bat_t_raw_hex_right_digit'):
                return self._m_bat_t_raw_hex_right_digit

            self._m_bat_t_raw_hex_right_digit = (u"a" if str(self.bat_t_raw_hex_right) == u"10" else (u"b" if str(self.bat_t_raw_hex_right) == u"11" else (u"c" if str(self.bat_t_raw_hex_right) == u"12" else (u"d" if str(self.bat_t_raw_hex_right) == u"13" else (u"e" if str(self.bat_t_raw_hex_right) == u"14" else (u"f" if str(self.bat_t_raw_hex_right) == u"15" else str(self.bat_t_raw_hex_right)))))))
            return getattr(self, '_m_bat_t_raw_hex_right_digit', None)

        @property
        def aprs_payload_1(self):
            if hasattr(self, '_m_aprs_payload_1'):
                return self._m_aprs_payload_1

            self._m_aprs_payload_1 = ((self.value3 & 32) >> 5)
            return getattr(self, '_m_aprs_payload_1', None)

        @property
        def value1_hex_left_digit(self):
            if hasattr(self, '_m_value1_hex_left_digit'):
                return self._m_value1_hex_left_digit

            self._m_value1_hex_left_digit = (u"a" if str(self.value1_hex_left) == u"10" else (u"b" if str(self.value1_hex_left) == u"11" else (u"c" if str(self.value1_hex_left) == u"12" else (u"d" if str(self.value1_hex_left) == u"13" else (u"e" if str(self.value1_hex_left) == u"14" else (u"f" if str(self.value1_hex_left) == u"15" else str(self.value1_hex_left)))))))
            return getattr(self, '_m_value1_hex_left_digit', None)

        @property
        def bat_i_raw_hex(self):
            if hasattr(self, '_m_bat_i_raw_hex'):
                return self._m_bat_i_raw_hex

            self._m_bat_i_raw_hex = (u".." if self.bat_i_raw_hex_left_digit + self.bat_i_raw_hex_right_digit == u"ff" else self.bat_i_raw_hex_left_digit + self.bat_i_raw_hex_right_digit)
            return getattr(self, '_m_bat_i_raw_hex', None)

        @property
        def time_after_last_reset_hex_left(self):
            if hasattr(self, '_m_time_after_last_reset_hex_left'):
                return self._m_time_after_last_reset_hex_left

            self._m_time_after_last_reset_hex_left = self.time_after_last_reset // 16
            return getattr(self, '_m_time_after_last_reset_hex_left', None)


    class Digi(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Dragonfly.Digi.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Dragonfly.Digi.Ax25Header(self._io, self, self._root)
                self._raw_ax25_info = self._io.read_bytes_full()
                _io__raw_ax25_info = KaitaiStream(BytesIO(self._raw_ax25_info))
                self.ax25_info = Dragonfly.Digi.Ax25InfoData(_io__raw_ax25_info, self, self._root)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Dragonfly.Digi.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Dragonfly.Digi.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Dragonfly.Digi.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Dragonfly.Digi.SsidMask(self._io, self, self._root)
                if (self.src_ssid_raw.ssid_mask & 1) == 0:
                    self.repeater = Dragonfly.Digi.Repeater(self._io, self, self._root)

                self.ctl = self._io.read_u1()
                self.pid = self._io.read_u1()


        class Callsign(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.callsign = (self._io.read_bytes(6)).decode(u"ASCII")


        class SsidMask(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ssid_mask = self._io.read_u1()

            @property
            def ssid(self):
                if hasattr(self, '_m_ssid'):
                    return self._m_ssid

                self._m_ssid = ((self.ssid_mask & 31) >> 1)
                return getattr(self, '_m_ssid', None)

            @property
            def hbit(self):
                if hasattr(self, '_m_hbit'):
                    return self._m_hbit

                self._m_hbit = ((self.ssid_mask & 128) >> 7)
                return getattr(self, '_m_hbit', None)


        class Repeaters(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.rpt_callsign_raw = Dragonfly.Digi.CallsignRaw(self._io, self, self._root)
                self.rpt_ssid_raw = Dragonfly.Digi.SsidMask(self._io, self, self._root)


        class Repeater(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.rpt_instance = []
                i = 0
                while True:
                    _ = Dragonfly.Digi.Repeaters(self._io, self, self._root)
                    self.rpt_instance.append(_)
                    if (_.rpt_ssid_raw.ssid_mask & 1) == 1:
                        break
                    i += 1


        class CallsignRaw(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self._raw__raw_callsign_ror = self._io.read_bytes(6)
                self._raw_callsign_ror = KaitaiStream.process_rotate_left(self._raw__raw_callsign_ror, 8 - (1), 1)
                _io__raw_callsign_ror = KaitaiStream(BytesIO(self._raw_callsign_ror))
                self.callsign_ror = Dragonfly.Digi.Callsign(_io__raw_callsign_ror, self, self._root)


        class Ax25InfoData(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.digi_message = (self._io.read_bytes_full()).decode(u"utf-8")




