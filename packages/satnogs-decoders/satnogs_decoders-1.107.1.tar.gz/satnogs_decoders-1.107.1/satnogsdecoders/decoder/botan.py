# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
import satnogsdecoders.process


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Botan(KaitaiStruct):
    """:field cw_batt_v: satellite.type_check.cw_batt_v
    :field cw_batt_i: satellite.type_check.cw_batt_i
    :field cw_batt_t: satellite.type_check.cw_batt_t
    :field cw_bpb_t: satellite.type_check.cw_bpb_t
    :field cw_raw_i: satellite.type_check.cw_raw_i
    :field cw_power_5v0: satellite.type_check.cw_power_5v0
    :field cw_pwr_ant_dep: satellite.type_check.cw_pwr_ant_dep
    :field cw_power_com: satellite.type_check.cw_power_com
    :field cw_sap_minus_x: satellite.type_check.cw_sap_minus_x
    :field cw_sap_plus_y: satellite.type_check.cw_sap_plus_y
    :field cw_sap_minus_y: satellite.type_check.cw_sap_minus_y
    :field cw_sap_plus_z: satellite.type_check.cw_sap_plus_z
    :field cw_sap_minus_z: satellite.type_check.cw_sap_minus_z
    :field cw_reserve_cmd_counter: satellite.type_check.cw_reserve_cmd_counter
    :field cw_gmsk_cmd_counter: satellite.type_check.cw_gmsk_cmd_counter
    :field cw_kill_sw: satellite.type_check.cw_kill_sw
    :field cw_kill_counter: satellite.type_check.cw_kill_counter
    :field cw_mission_pic_on_off: satellite.type_check.cw_mission_pic_on_off
    :field cw_mis_error_flag: satellite.type_check.cw_mis_error_flag
    :field cw_mis_end_flag: satellite.type_check.cw_mis_end_flag
    :field cw_aprs_flag: satellite.type_check.cw_aprs_flag
    :field cw_current_mis: satellite.type_check.cw_current_mis
    :field cw_beacon: satellite.type_check.cw_beacon
    :field beacon_type: satellite.type_check.beacon_type
    
    :field hk_packet_sequence_number: satellite.type_check.type_check_1.hk_packet_sequence_number
    :field seconds: satellite.type_check.type_check_1.seconds
    :field minutes: satellite.type_check.type_check_1.minutes
    :field hours: satellite.type_check.type_check_1.hours
    :field days: satellite.type_check.type_check_1.days
    :field temp_plus_x: satellite.type_check.type_check_1.temp_plus_x
    :field temp_minus_x: satellite.type_check.type_check_1.temp_minus_x
    :field temp_plus_y: satellite.type_check.type_check_1.temp_plus_y
    :field temp_minus_y: satellite.type_check.type_check_1.temp_minus_y
    :field temp_plus_z: satellite.type_check.type_check_1.temp_plus_z
    :field temp_minus_z: satellite.type_check.type_check_1.temp_minus_z
    :field temp_cigs: satellite.type_check.type_check_1.temp_cigs
    :field bpb_t: satellite.type_check.type_check_1.bpb_t
    :field voltage_minus_x: satellite.type_check.type_check_1.voltage_minus_x
    :field voltage_plus_y: satellite.type_check.type_check_1.voltage_plus_y
    :field voltage_minus_y: satellite.type_check.type_check_1.voltage_minus_y
    :field voltage_plus_z: satellite.type_check.type_check_1.voltage_plus_z
    :field voltage_minus_z: satellite.type_check.type_check_1.voltage_minus_z
    :field current_minus_x: satellite.type_check.type_check_1.current_minus_x
    :field current_plus_y: satellite.type_check.type_check_1.current_plus_y
    :field current_minus_y: satellite.type_check.type_check_1.current_minus_y
    :field current_plus_z: satellite.type_check.type_check_1.current_plus_z
    :field current_minus_z: satellite.type_check.type_check_1.current_minus_z
    :field batt_t: satellite.type_check.type_check_1.batt_t
    :field batt_v: satellite.type_check.type_check_1.batt_v
    :field batt_i: satellite.type_check.type_check_1.batt_i
    :field raw_v: satellite.type_check.type_check_1.raw_v
    :field raw_i: satellite.type_check.type_check_1.raw_i
    :field src_v: satellite.type_check.type_check_1.src_v
    :field src_i: satellite.type_check.type_check_1.src_i
    :field kill_sw: satellite.type_check.type_check_1.kill_sw
    :field raw_v_1: satellite.type_check.type_check_1.raw_v_1
    :field q3v3_1_i: satellite.type_check.type_check_1.q3v3_1_i
    :field q3v3_2_i: satellite.type_check.type_check_1.q3v3_2_i
    :field com_i: satellite.type_check.type_check_1.com_i
    :field ant_dep_i: satellite.type_check.type_check_1.ant_dep_i
    :field q5v0_i: satellite.type_check.type_check_1.q5v0_i
    :field reset_raw_v_mon: satellite.type_check.type_check_1.reset_raw_v_mon
    :field power_com: satellite.type_check.type_check_1.power_com
    :field power_5v0: satellite.type_check.type_check_1.power_5v0
    :field dcdc_3v3_1: satellite.type_check.type_check_1.dcdc_3v3_1
    :field pwr_ant_dep: satellite.type_check.type_check_1.pwr_ant_dep
    :field pwr_3v3_2: satellite.type_check.type_check_1.pwr_3v3_2
    :field pwr_3v3_1: satellite.type_check.type_check_1.pwr_3v3_1
    :field dcdc_5v0: satellite.type_check.type_check_1.dcdc_5v0
    :field dcdc_3v3_2: satellite.type_check.type_check_1.dcdc_3v3_2
    :field pwr_compic: satellite.type_check.type_check_1.pwr_compic
    :field pwr_mainpic: satellite.type_check.type_check_1.pwr_mainpic
    :field empty: satellite.type_check.type_check_1.empty
    :field mp_reset_counter: satellite.type_check.type_check_1.mp_reset_counter
    :field rssi: satellite.type_check.type_check_1.rssi
    :field com_t: satellite.type_check.type_check_1.com_t
    :field com_seq_counter: satellite.type_check.type_check_1.com_seq_counter
    :field mis_ack: satellite.type_check.type_check_1.mis_ack
    :field n_a_2: satellite.type_check.type_check_1.n_a_2
    :field current_mis: satellite.type_check.type_check_1.current_mis
    :field mis_counter: satellite.type_check.type_check_1.mis_counter
    :field checksum: satellite.type_check.type_check_1.checksum
    :field beacon_type: satellite.type_check.type_check_1.beacon_type
    
    :field gyro_sat_id: satellite.type_check.type_check_1.type_check_2.gyro_sat_id
    :field gyro_packet_id: satellite.type_check.type_check_1.type_check_2.gyro_packet_id
    :field gyro_reserved_1: satellite.type_check.type_check_1.type_check_2.gyro_reserved_1
    :field gyro_header: satellite.type_check.type_check_1.type_check_2.gyro_header
    :field gyro_packet_number: satellite.type_check.type_check_1.type_check_2.gyro_packet_number
    :field gyro_time: satellite.type_check.type_check_1.type_check_2.gyro_time
    :field gyro_n_a_1: satellite.type_check.type_check_1.type_check_2.gyro_n_a_1
    :field gyro_n_a_2: satellite.type_check.type_check_1.type_check_2.gyro_n_a_2
    :field gyro_n_a_3: satellite.type_check.type_check_1.type_check_2.gyro_n_a_3
    :field gyro_vector_i: satellite.type_check.type_check_1.type_check_2.gyro_vector_i
    :field gyro_vector_j: satellite.type_check.type_check_1.type_check_2.gyro_vector_j
    :field gyro_vector_k: satellite.type_check.type_check_1.type_check_2.gyro_vector_k
    :field gyro_vector_w: satellite.type_check.type_check_1.type_check_2.gyro_vector_w
    :field gyro_reserved_2: satellite.type_check.type_check_1.type_check_2.gyro_reserved_2
    :field gyro_sap_current_minus_x: satellite.type_check.type_check_1.type_check_2.gyro_sap_current_minus_x
    :field gyro_sap_current_plus_y: satellite.type_check.type_check_1.type_check_2.gyro_sap_current_plus_y
    :field gyro_sap_current_minus_y: satellite.type_check.type_check_1.type_check_2.gyro_sap_current_minus_y
    :field gyro_sap_current_plus_z: satellite.type_check.type_check_1.type_check_2.gyro_sap_current_plus_z
    :field gyro_sap_current_minus_z: satellite.type_check.type_check_1.type_check_2.gyro_sap_current_minus_z
    :field gyro_reserved_3: satellite.type_check.type_check_1.type_check_2.gyro_reserved_3
    :field beacon_type: satellite.type_check.type_check_1.type_check_2.beacon_type
    
    :field cam_sat_id: satellite.type_check.type_check_1.type_check_2.cam_sat_id
    :field cam_packet_id: satellite.type_check.type_check_1.type_check_2.cam_packet_id
    :field cam_reserved: satellite.type_check.type_check_1.type_check_2.cam_reserved
    :field cam_packet_number: satellite.type_check.type_check_1.type_check_2.cam_packet_number
    :field cam_data_b64_encoded: satellite.type_check.type_check_1.type_check_2.cam_data.b64encstring.cam_data_b64_encoded
    :field beacon_type: satellite.type_check.type_check_1.type_check_2.beacon_type
    
    :field dest_callsign: satellite.type_check.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: satellite.type_check.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field src_ssid: satellite.type_check.ax25_frame.ax25_header.src_ssid_raw.ssid
    :field dest_ssid: satellite.type_check.ax25_frame.ax25_header.dest_ssid_raw.ssid
    :field rpt_instance___callsign: satellite.type_check.ax25_frame.ax25_header.repeater.rpt_instance.___.rpt_callsign_raw.callsign_ror.callsign
    :field rpt_instance___ssid: satellite.type_check.ax25_frame.ax25_header.repeater.rpt_instance.___.rpt_ssid_raw.ssid
    :field rpt_instance___hbit: satellite.type_check.ax25_frame.ax25_header.repeater.rpt_instance.___.rpt_ssid_raw.hbit
    :field ctl: satellite.type_check.ax25_frame.ax25_header.ctl
    :field pid: satellite.type_check.ax25_frame.ax25_header.pid
    :field digi_message: satellite.type_check.ax25_frame.ax25_info.digi_message
    :field beacon_type: satellite.type_check.beacon_type
    
    .. seealso::
       Source - https://sites.google.com/p.chibakoudai.jp/gardens-04/satellite/downlink-format
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.satellite = Botan.SatelliteT(self._io, self, self._root)

    class Cam(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.cam_callsign_header_1 = self._io.read_u8be()
            if not self.cam_callsign_header_1 == 10711357282986385556:
                raise kaitaistruct.ValidationNotEqualError(10711357282986385556, self.cam_callsign_header_1, self._io, u"/types/cam/seq/0")
            self.cam_callsign_header_2 = self._io.read_u8be()
            if not self.cam_callsign_header_2 == 11989341561103138544:
                raise kaitaistruct.ValidationNotEqualError(11989341561103138544, self.cam_callsign_header_2, self._io, u"/types/cam/seq/1")
            self.cam_sat_id = self._io.read_u1()
            if not self.cam_sat_id == 66:
                raise kaitaistruct.ValidationNotEqualError(66, self.cam_sat_id, self._io, u"/types/cam/seq/2")
            self.cam_packet_id = self._io.read_u1()
            if not self.cam_packet_id == 204:
                raise kaitaistruct.ValidationNotEqualError(204, self.cam_packet_id, self._io, u"/types/cam/seq/3")
            self.cam_reserved = self._io.read_u1()
            if not self.cam_reserved == 255:
                raise kaitaistruct.ValidationNotEqualError(255, self.cam_reserved, self._io, u"/types/cam/seq/4")
            self.cam_packet_number = self._io.read_bits_int_be(24)
            self._io.align_to_byte()
            self._raw_cam_data = self._io.read_bytes_full()
            _io__raw_cam_data = KaitaiStream(BytesIO(self._raw_cam_data))
            self.cam_data = Botan.Cam.Base64(_io__raw_cam_data, self, self._root)

        class Base64(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self._raw__raw_b64encstring = self._io.read_bytes_full()
                _process = satnogsdecoders.process.B64encode()
                self._raw_b64encstring = _process.decode(self._raw__raw_b64encstring)
                _io__raw_b64encstring = KaitaiStream(BytesIO(self._raw_b64encstring))
                self.b64encstring = Botan.Cam.Base64string(_io__raw_b64encstring, self, self._root)


        class Base64string(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.cam_data_b64_encoded = (self._io.read_bytes_full()).decode(u"UTF-8")


        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = (u"CAM" if 0 == 0 else u"CAM")
            return getattr(self, '_m_beacon_type', None)


    class Gyro(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.gyro_callsign_header_1 = self._io.read_u8be()
            if not self.gyro_callsign_header_1 == 10711357282986385556:
                raise kaitaistruct.ValidationNotEqualError(10711357282986385556, self.gyro_callsign_header_1, self._io, u"/types/gyro/seq/0")
            self.gyro_callsign_header_2 = self._io.read_u8be()
            if not self.gyro_callsign_header_2 == 11989341561103138544:
                raise kaitaistruct.ValidationNotEqualError(11989341561103138544, self.gyro_callsign_header_2, self._io, u"/types/gyro/seq/1")
            self.gyro_sat_id = self._io.read_u1()
            if not self.gyro_sat_id == 66:
                raise kaitaistruct.ValidationNotEqualError(66, self.gyro_sat_id, self._io, u"/types/gyro/seq/2")
            self.gyro_packet_id = self._io.read_u1()
            if not self.gyro_packet_id == 204:
                raise kaitaistruct.ValidationNotEqualError(204, self.gyro_packet_id, self._io, u"/types/gyro/seq/3")
            self.gyro_reserved_1 = self._io.read_u1()
            if not self.gyro_reserved_1 == 255:
                raise kaitaistruct.ValidationNotEqualError(255, self.gyro_reserved_1, self._io, u"/types/gyro/seq/4")
            self.gyro_header = self._io.read_u1()
            if not self.gyro_header == 208:
                raise kaitaistruct.ValidationNotEqualError(208, self.gyro_header, self._io, u"/types/gyro/seq/5")
            self.gyro_packet_number = self._io.read_u2be()
            self.gyro_time = self._io.read_u2be()
            self.gyro_n_a_1 = self._io.read_u4be()
            self.gyro_n_a_2 = self._io.read_u2be()
            self.gyro_n_a_3 = self._io.read_u1()
            self.gyro_vector_i = self._io.read_u2be()
            self.gyro_vector_j = self._io.read_u2be()
            self.gyro_vector_k = self._io.read_u2be()
            self.gyro_vector_w = self._io.read_u2be()
            self.gyro_reserved_2 = self._io.read_u1()
            self.gyro_sap_current_minus_x = self._io.read_u2be()
            self.gyro_sap_current_plus_y = self._io.read_u2be()
            self.gyro_sap_current_minus_y = self._io.read_u2be()
            self.gyro_sap_current_plus_z = self._io.read_u2be()
            self.gyro_sap_current_minus_z = self._io.read_u2be()
            self.gyro_reserved_3 = self._io.read_u1()

        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = (u"GYRO" if 0 == 0 else u"GYRO")
            return getattr(self, '_m_beacon_type', None)


    class Discard(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.first_byte = self._io.read_u1()
            if not self.first_byte == 0:
                raise kaitaistruct.ValidationNotEqualError(0, self.first_byte, self._io, u"/types/discard/seq/0")


    class Cw(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.cw_callsign_and_satellite_name = (self._io.read_bytes(12)).decode(u"ASCII")
            if not self.cw_callsign_and_satellite_name == u"botan js1ypt":
                raise kaitaistruct.ValidationNotEqualError(u"botan js1ypt", self.cw_callsign_and_satellite_name, self._io, u"/types/cw/seq/0")
            self.cw_batt_v = self._io.read_u1()
            self.cw_batt_i = self._io.read_u1()
            self.cw_batt_t = self._io.read_u1()
            self.cw_bpb_t = self._io.read_u1()
            self.cw_raw_i = self._io.read_u1()
            self.cw_power_5v0 = self._io.read_bits_int_be(1) != 0
            self.cw_pwr_ant_dep = self._io.read_bits_int_be(1) != 0
            self.cw_power_com = self._io.read_bits_int_be(1) != 0
            self.cw_sap_minus_x = self._io.read_bits_int_be(1) != 0
            self.cw_sap_plus_y = self._io.read_bits_int_be(1) != 0
            self.cw_sap_minus_y = self._io.read_bits_int_be(1) != 0
            self.cw_sap_plus_z = self._io.read_bits_int_be(1) != 0
            self.cw_sap_minus_z = self._io.read_bits_int_be(1) != 0
            self.cw_reserve_cmd_counter = self._io.read_bits_int_be(4)
            self.cw_gmsk_cmd_counter = self._io.read_bits_int_be(3)
            self.cw_kill_sw = self._io.read_bits_int_be(1) != 0
            self.cw_kill_counter = self._io.read_bits_int_be(2)
            self.cw_mission_pic_on_off = self._io.read_bits_int_be(1) != 0
            self.cw_mis_error_flag = self._io.read_bits_int_be(1) != 0
            self.cw_mis_end_flag = self._io.read_bits_int_be(1) != 0
            self.cw_aprs_flag = self._io.read_bits_int_be(1) != 0
            self.cw_current_mis = self._io.read_bits_int_be(2)

        @property
        def data_1_dec_value_5(self):
            if hasattr(self, '_m_data_1_dec_value_5'):
                return self._m_data_1_dec_value_5

            self._m_data_1_dec_value_5 = (8 if int(self.cw_sap_plus_y) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_5', None)

        @property
        def raw_i_hex_left_digit(self):
            if hasattr(self, '_m_raw_i_hex_left_digit'):
                return self._m_raw_i_hex_left_digit

            self._m_raw_i_hex_left_digit = (u"a" if str(self.raw_i_hex_left) == u"10" else (u"b" if str(self.raw_i_hex_left) == u"11" else (u"c" if str(self.raw_i_hex_left) == u"12" else (u"d" if str(self.raw_i_hex_left) == u"13" else (u"e" if str(self.raw_i_hex_left) == u"14" else (u"f" if str(self.raw_i_hex_left) == u"15" else str(self.raw_i_hex_left)))))))
            return getattr(self, '_m_raw_i_hex_left_digit', None)

        @property
        def data_1_dec(self):
            if hasattr(self, '_m_data_1_dec'):
                return self._m_data_1_dec

            self._m_data_1_dec = (((((((self.data_1_dec_value_1 + self.data_1_dec_value_2) + self.data_1_dec_value_3) + self.data_1_dec_value_4) + self.data_1_dec_value_5) + self.data_1_dec_value_6) + self.data_1_dec_value_7) + self.data_1_dec_value_8)
            return getattr(self, '_m_data_1_dec', None)

        @property
        def data_1_dec_value_4(self):
            if hasattr(self, '_m_data_1_dec_value_4'):
                return self._m_data_1_dec_value_4

            self._m_data_1_dec_value_4 = (16 if int(self.cw_sap_minus_x) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_4', None)

        @property
        def batt_t_hex(self):
            if hasattr(self, '_m_batt_t_hex'):
                return self._m_batt_t_hex

            self._m_batt_t_hex = self.batt_t_hex_left_digit + self.batt_t_hex_right_digit
            return getattr(self, '_m_batt_t_hex', None)

        @property
        def data_2_hex_left(self):
            if hasattr(self, '_m_data_2_hex_left'):
                return self._m_data_2_hex_left

            self._m_data_2_hex_left = self.data_2_dec // 16
            return getattr(self, '_m_data_2_hex_left', None)

        @property
        def data_3_hex_right_digit(self):
            if hasattr(self, '_m_data_3_hex_right_digit'):
                return self._m_data_3_hex_right_digit

            self._m_data_3_hex_right_digit = (u"a" if str(self.data_3_hex_right) == u"10" else (u"b" if str(self.data_3_hex_right) == u"11" else (u"c" if str(self.data_3_hex_right) == u"12" else (u"d" if str(self.data_3_hex_right) == u"13" else (u"e" if str(self.data_3_hex_right) == u"14" else (u"f" if str(self.data_3_hex_right) == u"15" else str(self.data_3_hex_right)))))))
            return getattr(self, '_m_data_3_hex_right_digit', None)

        @property
        def data_1_dec_value_6(self):
            if hasattr(self, '_m_data_1_dec_value_6'):
                return self._m_data_1_dec_value_6

            self._m_data_1_dec_value_6 = (4 if int(self.cw_sap_minus_y) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_6', None)

        @property
        def raw_i_hex(self):
            if hasattr(self, '_m_raw_i_hex'):
                return self._m_raw_i_hex

            self._m_raw_i_hex = self.raw_i_hex_left_digit + self.raw_i_hex_right_digit
            return getattr(self, '_m_raw_i_hex', None)

        @property
        def batt_i_hex(self):
            if hasattr(self, '_m_batt_i_hex'):
                return self._m_batt_i_hex

            self._m_batt_i_hex = self.batt_i_hex_left_digit + self.batt_i_hex_right_digit
            return getattr(self, '_m_batt_i_hex', None)

        @property
        def data_1_hex_left(self):
            if hasattr(self, '_m_data_1_hex_left'):
                return self._m_data_1_hex_left

            self._m_data_1_hex_left = self.data_1_dec // 16
            return getattr(self, '_m_data_1_hex_left', None)

        @property
        def data_1_dec_value_7(self):
            if hasattr(self, '_m_data_1_dec_value_7'):
                return self._m_data_1_dec_value_7

            self._m_data_1_dec_value_7 = (2 if int(self.cw_sap_plus_z) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_7', None)

        @property
        def data_3_hex(self):
            if hasattr(self, '_m_data_3_hex'):
                return self._m_data_3_hex

            self._m_data_3_hex = self.data_3_hex_left_digit + self.data_3_hex_right_digit
            return getattr(self, '_m_data_3_hex', None)

        @property
        def data_2_dec(self):
            if hasattr(self, '_m_data_2_dec'):
                return self._m_data_2_dec

            self._m_data_2_dec = ((self.data_2_dec_value_1 + self.data_2_dec_value_2) + self.data_2_dec_value_3)
            return getattr(self, '_m_data_2_dec', None)

        @property
        def data_1_hex_left_digit(self):
            if hasattr(self, '_m_data_1_hex_left_digit'):
                return self._m_data_1_hex_left_digit

            self._m_data_1_hex_left_digit = (u"a" if str(self.data_1_hex_left) == u"10" else (u"b" if str(self.data_1_hex_left) == u"11" else (u"c" if str(self.data_1_hex_left) == u"12" else (u"d" if str(self.data_1_hex_left) == u"13" else (u"e" if str(self.data_1_hex_left) == u"14" else (u"f" if str(self.data_1_hex_left) == u"15" else str(self.data_1_hex_left)))))))
            return getattr(self, '_m_data_1_hex_left_digit', None)

        @property
        def data_2_dec_value_2(self):
            if hasattr(self, '_m_data_2_dec_value_2'):
                return self._m_data_2_dec_value_2

            self._m_data_2_dec_value_2 = (self.cw_gmsk_cmd_counter * 2)
            return getattr(self, '_m_data_2_dec_value_2', None)

        @property
        def data_3_hex_right(self):
            if hasattr(self, '_m_data_3_hex_right'):
                return self._m_data_3_hex_right

            self._m_data_3_hex_right = (self.data_3_dec % 16)
            return getattr(self, '_m_data_3_hex_right', None)

        @property
        def bpb_t_hex_right_digit(self):
            if hasattr(self, '_m_bpb_t_hex_right_digit'):
                return self._m_bpb_t_hex_right_digit

            self._m_bpb_t_hex_right_digit = (u"a" if str(self.bpb_t_hex_right) == u"10" else (u"b" if str(self.bpb_t_hex_right) == u"11" else (u"c" if str(self.bpb_t_hex_right) == u"12" else (u"d" if str(self.bpb_t_hex_right) == u"13" else (u"e" if str(self.bpb_t_hex_right) == u"14" else (u"f" if str(self.bpb_t_hex_right) == u"15" else str(self.bpb_t_hex_right)))))))
            return getattr(self, '_m_bpb_t_hex_right_digit', None)

        @property
        def batt_t_hex_left_digit(self):
            if hasattr(self, '_m_batt_t_hex_left_digit'):
                return self._m_batt_t_hex_left_digit

            self._m_batt_t_hex_left_digit = (u"a" if str(self.batt_t_hex_left) == u"10" else (u"b" if str(self.batt_t_hex_left) == u"11" else (u"c" if str(self.batt_t_hex_left) == u"12" else (u"d" if str(self.batt_t_hex_left) == u"13" else (u"e" if str(self.batt_t_hex_left) == u"14" else (u"f" if str(self.batt_t_hex_left) == u"15" else str(self.batt_t_hex_left)))))))
            return getattr(self, '_m_batt_t_hex_left_digit', None)

        @property
        def data_2_dec_value_1(self):
            if hasattr(self, '_m_data_2_dec_value_1'):
                return self._m_data_2_dec_value_1

            self._m_data_2_dec_value_1 = (self.cw_reserve_cmd_counter * 16)
            return getattr(self, '_m_data_2_dec_value_1', None)

        @property
        def data_3_dec_value_3(self):
            if hasattr(self, '_m_data_3_dec_value_3'):
                return self._m_data_3_dec_value_3

            self._m_data_3_dec_value_3 = (16 if int(self.cw_mis_error_flag) == 1 else 0)
            return getattr(self, '_m_data_3_dec_value_3', None)

        @property
        def data_1_dec_value_1(self):
            if hasattr(self, '_m_data_1_dec_value_1'):
                return self._m_data_1_dec_value_1

            self._m_data_1_dec_value_1 = (128 if int(self.cw_power_5v0) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_1', None)

        @property
        def data_3_dec_value_6(self):
            if hasattr(self, '_m_data_3_dec_value_6'):
                return self._m_data_3_dec_value_6

            self._m_data_3_dec_value_6 = self.cw_current_mis
            return getattr(self, '_m_data_3_dec_value_6', None)

        @property
        def batt_i_hex_right_digit(self):
            if hasattr(self, '_m_batt_i_hex_right_digit'):
                return self._m_batt_i_hex_right_digit

            self._m_batt_i_hex_right_digit = (u"a" if str(self.batt_i_hex_right) == u"10" else (u"b" if str(self.batt_i_hex_right) == u"11" else (u"c" if str(self.batt_i_hex_right) == u"12" else (u"d" if str(self.batt_i_hex_right) == u"13" else (u"e" if str(self.batt_i_hex_right) == u"14" else (u"f" if str(self.batt_i_hex_right) == u"15" else str(self.batt_i_hex_right)))))))
            return getattr(self, '_m_batt_i_hex_right_digit', None)

        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = (u"CW" if 0 == 0 else u"CW")
            return getattr(self, '_m_beacon_type', None)

        @property
        def data_3_dec_value_4(self):
            if hasattr(self, '_m_data_3_dec_value_4'):
                return self._m_data_3_dec_value_4

            self._m_data_3_dec_value_4 = (8 if int(self.cw_mis_end_flag) == 1 else 0)
            return getattr(self, '_m_data_3_dec_value_4', None)

        @property
        def batt_v_hex_left_digit(self):
            if hasattr(self, '_m_batt_v_hex_left_digit'):
                return self._m_batt_v_hex_left_digit

            self._m_batt_v_hex_left_digit = (u"a" if str(self.batt_v_hex_left) == u"10" else (u"b" if str(self.batt_v_hex_left) == u"11" else (u"c" if str(self.batt_v_hex_left) == u"12" else (u"d" if str(self.batt_v_hex_left) == u"13" else (u"e" if str(self.batt_v_hex_left) == u"14" else (u"f" if str(self.batt_v_hex_left) == u"15" else str(self.batt_v_hex_left)))))))
            return getattr(self, '_m_batt_v_hex_left_digit', None)

        @property
        def data_2_hex_right(self):
            if hasattr(self, '_m_data_2_hex_right'):
                return self._m_data_2_hex_right

            self._m_data_2_hex_right = (self.data_2_dec % 16)
            return getattr(self, '_m_data_2_hex_right', None)

        @property
        def data_3_dec_value_1(self):
            if hasattr(self, '_m_data_3_dec_value_1'):
                return self._m_data_3_dec_value_1

            self._m_data_3_dec_value_1 = (self.cw_kill_counter * 64)
            return getattr(self, '_m_data_3_dec_value_1', None)

        @property
        def batt_t_hex_right(self):
            if hasattr(self, '_m_batt_t_hex_right'):
                return self._m_batt_t_hex_right

            self._m_batt_t_hex_right = (self.cw_batt_t % 16)
            return getattr(self, '_m_batt_t_hex_right', None)

        @property
        def data_1_dec_value_2(self):
            if hasattr(self, '_m_data_1_dec_value_2'):
                return self._m_data_1_dec_value_2

            self._m_data_1_dec_value_2 = (64 if int(self.cw_pwr_ant_dep) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_2', None)

        @property
        def data_3_dec_value_2(self):
            if hasattr(self, '_m_data_3_dec_value_2'):
                return self._m_data_3_dec_value_2

            self._m_data_3_dec_value_2 = (32 if int(self.cw_mission_pic_on_off) == 1 else 0)
            return getattr(self, '_m_data_3_dec_value_2', None)

        @property
        def data_2_hex_left_digit(self):
            if hasattr(self, '_m_data_2_hex_left_digit'):
                return self._m_data_2_hex_left_digit

            self._m_data_2_hex_left_digit = (u"a" if str(self.data_2_hex_left) == u"10" else (u"b" if str(self.data_2_hex_left) == u"11" else (u"c" if str(self.data_2_hex_left) == u"12" else (u"d" if str(self.data_2_hex_left) == u"13" else (u"e" if str(self.data_2_hex_left) == u"14" else (u"f" if str(self.data_2_hex_left) == u"15" else str(self.data_2_hex_left)))))))
            return getattr(self, '_m_data_2_hex_left_digit', None)

        @property
        def batt_i_hex_left_digit(self):
            if hasattr(self, '_m_batt_i_hex_left_digit'):
                return self._m_batt_i_hex_left_digit

            self._m_batt_i_hex_left_digit = (u"a" if str(self.batt_i_hex_left) == u"10" else (u"b" if str(self.batt_i_hex_left) == u"11" else (u"c" if str(self.batt_i_hex_left) == u"12" else (u"d" if str(self.batt_i_hex_left) == u"13" else (u"e" if str(self.batt_i_hex_left) == u"14" else (u"f" if str(self.batt_i_hex_left) == u"15" else str(self.batt_i_hex_left)))))))
            return getattr(self, '_m_batt_i_hex_left_digit', None)

        @property
        def data_2_hex_right_digit(self):
            if hasattr(self, '_m_data_2_hex_right_digit'):
                return self._m_data_2_hex_right_digit

            self._m_data_2_hex_right_digit = (u"a" if str(self.data_2_hex_right) == u"10" else (u"b" if str(self.data_2_hex_right) == u"11" else (u"c" if str(self.data_2_hex_right) == u"12" else (u"d" if str(self.data_2_hex_right) == u"13" else (u"e" if str(self.data_2_hex_right) == u"14" else (u"f" if str(self.data_2_hex_right) == u"15" else str(self.data_2_hex_right)))))))
            return getattr(self, '_m_data_2_hex_right_digit', None)

        @property
        def batt_v_hex_right_digit(self):
            if hasattr(self, '_m_batt_v_hex_right_digit'):
                return self._m_batt_v_hex_right_digit

            self._m_batt_v_hex_right_digit = (u"a" if str(self.batt_v_hex_right) == u"10" else (u"b" if str(self.batt_v_hex_right) == u"11" else (u"c" if str(self.batt_v_hex_right) == u"12" else (u"d" if str(self.batt_v_hex_right) == u"13" else (u"e" if str(self.batt_v_hex_right) == u"14" else (u"f" if str(self.batt_v_hex_right) == u"15" else str(self.batt_v_hex_right)))))))
            return getattr(self, '_m_batt_v_hex_right_digit', None)

        @property
        def batt_t_hex_left(self):
            if hasattr(self, '_m_batt_t_hex_left'):
                return self._m_batt_t_hex_left

            self._m_batt_t_hex_left = self.cw_batt_t // 16
            return getattr(self, '_m_batt_t_hex_left', None)

        @property
        def raw_i_hex_left(self):
            if hasattr(self, '_m_raw_i_hex_left'):
                return self._m_raw_i_hex_left

            self._m_raw_i_hex_left = self.cw_raw_i // 16
            return getattr(self, '_m_raw_i_hex_left', None)

        @property
        def bpb_t_hex_right(self):
            if hasattr(self, '_m_bpb_t_hex_right'):
                return self._m_bpb_t_hex_right

            self._m_bpb_t_hex_right = (self.cw_bpb_t % 16)
            return getattr(self, '_m_bpb_t_hex_right', None)

        @property
        def data_3_hex_left(self):
            if hasattr(self, '_m_data_3_hex_left'):
                return self._m_data_3_hex_left

            self._m_data_3_hex_left = self.data_3_dec // 16
            return getattr(self, '_m_data_3_hex_left', None)

        @property
        def bpb_t_hex_left_digit(self):
            if hasattr(self, '_m_bpb_t_hex_left_digit'):
                return self._m_bpb_t_hex_left_digit

            self._m_bpb_t_hex_left_digit = (u"a" if str(self.bpb_t_hex_left) == u"10" else (u"b" if str(self.bpb_t_hex_left) == u"11" else (u"c" if str(self.bpb_t_hex_left) == u"12" else (u"d" if str(self.bpb_t_hex_left) == u"13" else (u"e" if str(self.bpb_t_hex_left) == u"14" else (u"f" if str(self.bpb_t_hex_left) == u"15" else str(self.bpb_t_hex_left)))))))
            return getattr(self, '_m_bpb_t_hex_left_digit', None)

        @property
        def bpb_t_hex_left(self):
            if hasattr(self, '_m_bpb_t_hex_left'):
                return self._m_bpb_t_hex_left

            self._m_bpb_t_hex_left = self.cw_bpb_t // 16
            return getattr(self, '_m_bpb_t_hex_left', None)

        @property
        def cw_beacon(self):
            if hasattr(self, '_m_cw_beacon'):
                return self._m_cw_beacon

            self._m_cw_beacon = self.batt_v_hex + self.batt_i_hex + self.batt_t_hex + self.bpb_t_hex + self.raw_i_hex + self.data_1_hex + self.data_2_hex + self.data_3_hex
            return getattr(self, '_m_cw_beacon', None)

        @property
        def data_3_hex_left_digit(self):
            if hasattr(self, '_m_data_3_hex_left_digit'):
                return self._m_data_3_hex_left_digit

            self._m_data_3_hex_left_digit = (u"a" if str(self.data_3_hex_left) == u"10" else (u"b" if str(self.data_3_hex_left) == u"11" else (u"c" if str(self.data_3_hex_left) == u"12" else (u"d" if str(self.data_3_hex_left) == u"13" else (u"e" if str(self.data_3_hex_left) == u"14" else (u"f" if str(self.data_3_hex_left) == u"15" else str(self.data_3_hex_left)))))))
            return getattr(self, '_m_data_3_hex_left_digit', None)

        @property
        def data_3_dec(self):
            if hasattr(self, '_m_data_3_dec'):
                return self._m_data_3_dec

            self._m_data_3_dec = (((((self.data_3_dec_value_1 + self.data_3_dec_value_2) + self.data_3_dec_value_3) + self.data_3_dec_value_4) + self.data_3_dec_value_5) + self.data_3_dec_value_6)
            return getattr(self, '_m_data_3_dec', None)

        @property
        def batt_t_hex_right_digit(self):
            if hasattr(self, '_m_batt_t_hex_right_digit'):
                return self._m_batt_t_hex_right_digit

            self._m_batt_t_hex_right_digit = (u"a" if str(self.batt_t_hex_right) == u"10" else (u"b" if str(self.batt_t_hex_right) == u"11" else (u"c" if str(self.batt_t_hex_right) == u"12" else (u"d" if str(self.batt_t_hex_right) == u"13" else (u"e" if str(self.batt_t_hex_right) == u"14" else (u"f" if str(self.batt_t_hex_right) == u"15" else str(self.batt_t_hex_right)))))))
            return getattr(self, '_m_batt_t_hex_right_digit', None)

        @property
        def data_1_dec_value_3(self):
            if hasattr(self, '_m_data_1_dec_value_3'):
                return self._m_data_1_dec_value_3

            self._m_data_1_dec_value_3 = (32 if int(self.cw_power_com) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_3', None)

        @property
        def data_2_hex(self):
            if hasattr(self, '_m_data_2_hex'):
                return self._m_data_2_hex

            self._m_data_2_hex = self.data_2_hex_left_digit + self.data_2_hex_right_digit
            return getattr(self, '_m_data_2_hex', None)

        @property
        def batt_i_hex_right(self):
            if hasattr(self, '_m_batt_i_hex_right'):
                return self._m_batt_i_hex_right

            self._m_batt_i_hex_right = (self.cw_batt_i % 16)
            return getattr(self, '_m_batt_i_hex_right', None)

        @property
        def raw_i_hex_right(self):
            if hasattr(self, '_m_raw_i_hex_right'):
                return self._m_raw_i_hex_right

            self._m_raw_i_hex_right = (self.cw_raw_i % 16)
            return getattr(self, '_m_raw_i_hex_right', None)

        @property
        def data_1_dec_value_8(self):
            if hasattr(self, '_m_data_1_dec_value_8'):
                return self._m_data_1_dec_value_8

            self._m_data_1_dec_value_8 = (1 if int(self.cw_sap_minus_z) == 1 else 0)
            return getattr(self, '_m_data_1_dec_value_8', None)

        @property
        def raw_i_hex_right_digit(self):
            if hasattr(self, '_m_raw_i_hex_right_digit'):
                return self._m_raw_i_hex_right_digit

            self._m_raw_i_hex_right_digit = (u"a" if str(self.raw_i_hex_right) == u"10" else (u"b" if str(self.raw_i_hex_right) == u"11" else (u"c" if str(self.raw_i_hex_right) == u"12" else (u"d" if str(self.raw_i_hex_right) == u"13" else (u"e" if str(self.raw_i_hex_right) == u"14" else (u"f" if str(self.raw_i_hex_right) == u"15" else str(self.raw_i_hex_right)))))))
            return getattr(self, '_m_raw_i_hex_right_digit', None)

        @property
        def data_1_hex(self):
            if hasattr(self, '_m_data_1_hex'):
                return self._m_data_1_hex

            self._m_data_1_hex = self.data_1_hex_left_digit + self.data_1_hex_right_digit
            return getattr(self, '_m_data_1_hex', None)

        @property
        def batt_v_hex_left(self):
            if hasattr(self, '_m_batt_v_hex_left'):
                return self._m_batt_v_hex_left

            self._m_batt_v_hex_left = self.cw_batt_v // 16
            return getattr(self, '_m_batt_v_hex_left', None)

        @property
        def bpb_t_hex(self):
            if hasattr(self, '_m_bpb_t_hex'):
                return self._m_bpb_t_hex

            self._m_bpb_t_hex = self.bpb_t_hex_left_digit + self.bpb_t_hex_right_digit
            return getattr(self, '_m_bpb_t_hex', None)

        @property
        def batt_v_hex_right(self):
            if hasattr(self, '_m_batt_v_hex_right'):
                return self._m_batt_v_hex_right

            self._m_batt_v_hex_right = (self.cw_batt_v % 16)
            return getattr(self, '_m_batt_v_hex_right', None)

        @property
        def data_2_dec_value_3(self):
            if hasattr(self, '_m_data_2_dec_value_3'):
                return self._m_data_2_dec_value_3

            self._m_data_2_dec_value_3 = (1 if int(self.cw_kill_sw) == 1 else 0)
            return getattr(self, '_m_data_2_dec_value_3', None)

        @property
        def batt_v_hex(self):
            if hasattr(self, '_m_batt_v_hex'):
                return self._m_batt_v_hex

            self._m_batt_v_hex = self.batt_v_hex_left_digit + self.batt_v_hex_right_digit
            return getattr(self, '_m_batt_v_hex', None)

        @property
        def batt_i_hex_left(self):
            if hasattr(self, '_m_batt_i_hex_left'):
                return self._m_batt_i_hex_left

            self._m_batt_i_hex_left = self.cw_batt_i // 16
            return getattr(self, '_m_batt_i_hex_left', None)

        @property
        def data_1_hex_right_digit(self):
            if hasattr(self, '_m_data_1_hex_right_digit'):
                return self._m_data_1_hex_right_digit

            self._m_data_1_hex_right_digit = (u"a" if str(self.data_1_hex_right) == u"10" else (u"b" if str(self.data_1_hex_right) == u"11" else (u"c" if str(self.data_1_hex_right) == u"12" else (u"d" if str(self.data_1_hex_right) == u"13" else (u"e" if str(self.data_1_hex_right) == u"14" else (u"f" if str(self.data_1_hex_right) == u"15" else str(self.data_1_hex_right)))))))
            return getattr(self, '_m_data_1_hex_right_digit', None)

        @property
        def data_1_hex_right(self):
            if hasattr(self, '_m_data_1_hex_right'):
                return self._m_data_1_hex_right

            self._m_data_1_hex_right = (self.data_1_dec % 16)
            return getattr(self, '_m_data_1_hex_right', None)

        @property
        def data_3_dec_value_5(self):
            if hasattr(self, '_m_data_3_dec_value_5'):
                return self._m_data_3_dec_value_5

            self._m_data_3_dec_value_5 = (4 if int(self.cw_aprs_flag) == 1 else 0)
            return getattr(self, '_m_data_3_dec_value_5', None)


    class GyroOrCam(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.check_2
            if _on == 208:
                self.type_check_2 = Botan.Gyro(self._io, self, self._root)
            else:
                self.type_check_2 = Botan.Cam(self._io, self, self._root)

        @property
        def check_2(self):
            if hasattr(self, '_m_check_2'):
                return self._m_check_2

            _pos = self._io.pos()
            self._io.seek(19)
            self._m_check_2 = self._io.read_u1()
            self._io.seek(_pos)
            return getattr(self, '_m_check_2', None)


    class Hk(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.hk_callsign_header_1 = self._io.read_u8be()
            if not self.hk_callsign_header_1 == 10711357282986385556:
                raise kaitaistruct.ValidationNotEqualError(10711357282986385556, self.hk_callsign_header_1, self._io, u"/types/hk/seq/0")
            self.hk_callsign_header_2 = self._io.read_u8be()
            if not self.hk_callsign_header_2 == 11989341561103123440:
                raise kaitaistruct.ValidationNotEqualError(11989341561103123440, self.hk_callsign_header_2, self._io, u"/types/hk/seq/1")
            self.hk_callsign_header_3 = self._io.read_u2be()
            if not self.hk_callsign_header_3 == 16913:
                raise kaitaistruct.ValidationNotEqualError(16913, self.hk_callsign_header_3, self._io, u"/types/hk/seq/2")
            self.hk_callsign_header_4 = self._io.read_u1()
            if not self.hk_callsign_header_4 == 255:
                raise kaitaistruct.ValidationNotEqualError(255, self.hk_callsign_header_4, self._io, u"/types/hk/seq/3")
            self.hk_packet_sequence_number = self._io.read_bits_int_be(24)
            self._io.align_to_byte()
            self.hk_header = self._io.read_u1()
            if not self.hk_header == 51:
                raise kaitaistruct.ValidationNotEqualError(51, self.hk_header, self._io, u"/types/hk/seq/5")
            self.seconds = self._io.read_u1()
            self.minutes = self._io.read_u1()
            self.hours = self._io.read_u1()
            self.days = self._io.read_u2be()
            self.temp_plus_x = self._io.read_u2be()
            self.temp_minus_x = self._io.read_u2be()
            self.temp_plus_y = self._io.read_u2be()
            self.temp_minus_y = self._io.read_u2be()
            self.temp_plus_z = self._io.read_u2be()
            self.temp_minus_z = self._io.read_u2be()
            self.temp_cigs = self._io.read_u1()
            self.bpb_t = self._io.read_u2be()
            self.voltage_minus_x = self._io.read_u2be()
            self.voltage_plus_y = self._io.read_u2be()
            self.voltage_minus_y = self._io.read_u2be()
            self.voltage_plus_z = self._io.read_u2be()
            self.voltage_minus_z = self._io.read_u2be()
            self.current_minus_x = self._io.read_u1()
            self.current_plus_y = self._io.read_u1()
            self.current_minus_y = self._io.read_u1()
            self.current_plus_z = self._io.read_u1()
            self.current_minus_z = self._io.read_u1()
            self.batt_t = self._io.read_u1()
            self.batt_v = self._io.read_u1()
            self.batt_i = self._io.read_u2be()
            self.raw_v = self._io.read_u1()
            self.raw_i = self._io.read_u2be()
            self.src_v = self._io.read_u1()
            self.src_i = self._io.read_u2be()
            self.kill_sw = self._io.read_u1()
            self.raw_v_1 = self._io.read_u1()
            self.q3v3_1_i = self._io.read_u1()
            self.q3v3_2_i = self._io.read_u1()
            self.com_i = self._io.read_u1()
            self.ant_dep_i = self._io.read_u1()
            self.q5v0_i = self._io.read_u1()
            self.reset_raw_v_mon = self._io.read_bits_int_be(1) != 0
            self.power_com = self._io.read_bits_int_be(1) != 0
            self.power_5v0 = self._io.read_bits_int_be(1) != 0
            self.dcdc_3v3_1 = self._io.read_bits_int_be(1) != 0
            self.pwr_ant_dep = self._io.read_bits_int_be(1) != 0
            self.pwr_3v3_2 = self._io.read_bits_int_be(1) != 0
            self.pwr_3v3_1 = self._io.read_bits_int_be(1) != 0
            self.dcdc_5v0 = self._io.read_bits_int_be(1) != 0
            self.dcdc_3v3_2 = self._io.read_bits_int_be(1) != 0
            self.pwr_compic = self._io.read_bits_int_be(1) != 0
            self.pwr_mainpic = self._io.read_bits_int_be(1) != 0
            self.empty = self._io.read_bits_int_be(5)
            self._io.align_to_byte()
            self.mp_reset_counter = self._io.read_u1()
            self.rssi = self._io.read_u1()
            self.com_t = self._io.read_u1()
            self.com_seq_counter = self._io.read_u1()
            self.mis_ack = self._io.read_u1()
            self.n_a_2 = self._io.read_u1()
            self.current_mis = self._io.read_u1()
            self.mis_counter = self._io.read_u1()
            self.checksum = self._io.read_u1()

        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = (u"HK" if 0 == 0 else u"HK")
            return getattr(self, '_m_beacon_type', None)


    class Digi(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Botan.Digi.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Botan.Digi.Ax25Header(self._io, self, self._root)
                self._raw_ax25_info = self._io.read_bytes_full()
                _io__raw_ax25_info = KaitaiStream(BytesIO(self._raw_ax25_info))
                self.ax25_info = Botan.Digi.Ax25InfoData(_io__raw_ax25_info, self, self._root)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Botan.Digi.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Botan.Digi.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Botan.Digi.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Botan.Digi.SsidMask(self._io, self, self._root)
                if (self.src_ssid_raw.ssid_mask & 1) == 0:
                    self.repeater = Botan.Digi.Repeater(self._io, self, self._root)

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
                self.rpt_callsign_raw = Botan.Digi.CallsignRaw(self._io, self, self._root)
                self.rpt_ssid_raw = Botan.Digi.SsidMask(self._io, self, self._root)


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
                    _ = Botan.Digi.Repeaters(self._io, self, self._root)
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
                self.callsign_ror = Botan.Digi.Callsign(_io__raw_callsign_ror, self, self._root)


        class Ax25InfoData(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.digi_message = (self._io.read_bytes_full()).decode(u"utf-8")


        @property
        def beacon_type(self):
            if hasattr(self, '_m_beacon_type'):
                return self._m_beacon_type

            self._m_beacon_type = (u"DIGI" if 0 == 0 else u"DIGI")
            return getattr(self, '_m_beacon_type', None)


    class SatelliteT(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.check
            if _on == 1651471457:
                self.type_check = Botan.Cw(self._io, self, self._root)
            elif _on == 2493932210:
                self.type_check = Botan.DigitalBeacon(self._io, self, self._root)
            else:
                self.type_check = Botan.Digi(self._io, self, self._root)

        @property
        def check(self):
            if hasattr(self, '_m_check'):
                return self._m_check

            _pos = self._io.pos()
            self._io.seek(0)
            self._m_check = self._io.read_u4be()
            self._io.seek(_pos)
            return getattr(self, '_m_check', None)


    class DigitalBeacon(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.check_1
            if _on == 17:
                self.type_check_1 = Botan.Hk(self._io, self, self._root)
            elif _on == 204:
                self.type_check_1 = Botan.GyroOrCam(self._io, self, self._root)
            else:
                self.type_check_1 = Botan.Discard(self._io, self, self._root)

        @property
        def check_1(self):
            if hasattr(self, '_m_check_1'):
                return self._m_check_1

            _pos = self._io.pos()
            self._io.seek(17)
            self._m_check_1 = self._io.read_u1()
            self._io.seek(_pos)
            return getattr(self, '_m_check_1', None)



