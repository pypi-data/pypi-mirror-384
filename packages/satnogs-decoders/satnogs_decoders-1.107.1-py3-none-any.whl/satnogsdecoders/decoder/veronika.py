# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Veronika(KaitaiStruct):
    """:field uptime_total: id1.id2.uptime_total
    :field reset_number: id1.id2.reset_number
    :field temp_mcu: id1.id2.temp_mcu
    :field temp_pa: id1.id2.temp_pa
    :field cw_beacon: id1.id2.cw_beacon
    
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
    
    :field dest_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field obc_reset_cnt: id1.id2.id3.id4.ax25_frame.obc_reset_cnt
    :field obc_uptime: id1.id2.id3.id4.ax25_frame.obc_uptime
    :field obc_uptime_tot: id1.id2.id3.id4.ax25_frame.obc_uptime_tot
    :field obc_bat: id1.id2.id3.id4.ax25_frame.obc_bat
    :field obc_temp_mcu: id1.id2.id3.id4.ax25_frame.obc_temp_mcu
    :field obc_freemem: id1.id2.id3.id4.ax25_frame.obc_freemem
    
    :field dest_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field psu_reset_cnt: id1.id2.id3.id4.ax25_frame.psu_reset_cnt
    :field psu_uptime: id1.id2.id3.id4.ax25_frame.psu_uptime
    :field psu_uptime_tot: id1.id2.id3.id4.ax25_frame.psu_uptime_tot
    :field psu_battery: id1.id2.id3.id4.ax25_frame.psu_battery
    :field psu_temp_sys: id1.id2.id3.id4.ax25_frame.psu_temp_sys
    :field psu_temp_bat: id1.id2.id3.id4.ax25_frame.psu_temp_bat
    :field psu_cur_in: id1.id2.id3.id4.ax25_frame.psu_cur_in
    :field psu_cur_out: id1.id2.id3.id4.ax25_frame.psu_cur_out
    :field psu_ch_state_num: id1.id2.id3.id4.ax25_frame.psu_ch_state_num
    :field psu_ch0_state: id1.id2.id3.id4.ax25_frame.psu_ch0_state
    :field psu_ch1_state: id1.id2.id3.id4.ax25_frame.psu_ch1_state
    :field psu_ch2_state: id1.id2.id3.id4.ax25_frame.psu_ch2_state
    :field psu_ch3_state: id1.id2.id3.id4.ax25_frame.psu_ch3_state
    :field psu_ch4_state: id1.id2.id3.id4.ax25_frame.psu_ch4_state
    :field psu_ch5_state: id1.id2.id3.id4.ax25_frame.psu_ch5_state
    :field psu_ch6_state: id1.id2.id3.id4.ax25_frame.psu_ch6_state
    :field psu_sys_state: id1.id2.id3.id4.ax25_frame.psu_sys_state
    :field psu_gnd_wdt: id1.id2.id3.id4.ax25_frame.psu_gnd_wdt
    
    :field dest_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field mgs_temp_int_mag: id1.id2.id3.id4.ax25_frame.mgs_temp_int_mag
    :field mgs_temp_int_gyr: id1.id2.id3.id4.ax25_frame.mgs_temp_int_gyr
    :field mgs_int_mag_x: id1.id2.id3.id4.ax25_frame.mgs_int_mag_x
    :field mgs_int_mag_y: id1.id2.id3.id4.ax25_frame.mgs_int_mag_y
    :field mgs_int_mag_z: id1.id2.id3.id4.ax25_frame.mgs_int_mag_z
    :field mgs_int_gyr_x: id1.id2.id3.id4.ax25_frame.mgs_int_gyr_x
    :field mgs_int_gyr_y: id1.id2.id3.id4.ax25_frame.mgs_int_gyr_y
    :field mgs_int_gyr_z: id1.id2.id3.id4.ax25_frame.mgs_int_gyr_z
    :field mgs_temp_ext_mag: id1.id2.id3.id4.ax25_frame.mgs_temp_ext_mag
    :field mgs_temp_ext_gyr: id1.id2.id3.id4.ax25_frame.mgs_temp_ext_gyr
    :field mgs_ext_mag_x: id1.id2.id3.id4.ax25_frame.mgs_ext_mag_x
    :field mgs_ext_mag_y: id1.id2.id3.id4.ax25_frame.mgs_ext_mag_y
    :field mgs_ext_mag_z: id1.id2.id3.id4.ax25_frame.mgs_ext_mag_z
    :field mgs_ext_gyr_x: id1.id2.id3.id4.ax25_frame.mgs_ext_gyr_x
    :field mgs_ext_gyr_y: id1.id2.id3.id4.ax25_frame.mgs_ext_gyr_y
    :field mgs_ext_gyr_z: id1.id2.id3.id4.ax25_frame.mgs_ext_gyr_z
    
    :field dest_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field sol_temp_zp: id1.id2.id3.id4.ax25_frame.sol_temp_zp
    :field sol_temp_xp: id1.id2.id3.id4.ax25_frame.sol_temp_xp
    :field sol_temp_yp: id1.id2.id3.id4.ax25_frame.sol_temp_yp
    :field sol_temp_zn: id1.id2.id3.id4.ax25_frame.sol_temp_zn
    :field sol_temp_xn: id1.id2.id3.id4.ax25_frame.sol_temp_xn
    :field sol_temp_yn: id1.id2.id3.id4.ax25_frame.sol_temp_yn
    :field sol_diode_zp: id1.id2.id3.id4.ax25_frame.sol_diode_zp
    :field sol_diode_xp: id1.id2.id3.id4.ax25_frame.sol_diode_xp
    :field sol_diode_yp: id1.id2.id3.id4.ax25_frame.sol_diode_yp
    :field sol_diode_zn: id1.id2.id3.id4.ax25_frame.sol_diode_zn
    :field sol_diode_xn: id1.id2.id3.id4.ax25_frame.sol_diode_xn
    :field sol_diode_yn: id1.id2.id3.id4.ax25_frame.sol_diode_yn
    
    :field dest_callsign: id1.id2.id3.id4.id5.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.id5.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field uhf_uptime: id1.id2.id3.id4.id5.ax25_frame.uhf_uptime
    :field uhf_uptime_tot: id1.id2.id3.id4.id5.ax25_frame.uhf_uptime_tot
    :field uhf_reset_cnt: id1.id2.id3.id4.id5.ax25_frame.uhf_reset_cnt
    :field uhf_rf_reset_cnt: id1.id2.id3.id4.id5.ax25_frame.uhf_rf_reset_cnt
    :field uhf_trx_temp: id1.id2.id3.id4.id5.ax25_frame.uhf_trx_temp
    :field uhf_rf_temp: id1.id2.id3.id4.id5.ax25_frame.uhf_rf_temp
    :field uhf_pa_temp: id1.id2.id3.id4.id5.ax25_frame.uhf_pa_temp
    :field uhf_digipeater_cnt: id1.id2.id3.id4.id5.ax25_frame.uhf_digipeater_cnt
    :field uhf_last_digipeater: id1.id2.id3.id4.id5.ax25_frame.uhf_last_digipeater
    :field uhf_rx_cnt: id1.id2.id3.id4.id5.ax25_frame.uhf_rx_cnt
    :field uhf_tx_cnt: id1.id2.id3.id4.id5.ax25_frame.uhf_tx_cnt
    :field uhf_act_rssi_raw: id1.id2.id3.id4.id5.ax25_frame.uhf_act_rssi_raw
    :field uhf_dcd_rssi_raw: id1.id2.id3.id4.id5.ax25_frame.uhf_dcd_rssi_raw
    
    :field dest_callsign: id1.id2.id3.id4.id5.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.id5.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field vhf_uptime: id1.id2.id3.id4.id5.ax25_frame.vhf_uptime
    :field vhf_uptime_tot: id1.id2.id3.id4.id5.ax25_frame.vhf_uptime_tot
    :field vhf_reset_cnt: id1.id2.id3.id4.id5.ax25_frame.vhf_reset_cnt
    :field vhf_rf_reset_cnt: id1.id2.id3.id4.id5.ax25_frame.vhf_rf_reset_cnt
    :field vhf_trx_temp: id1.id2.id3.id4.id5.ax25_frame.vhf_trx_temp
    :field vhf_rf_temp: id1.id2.id3.id4.id5.ax25_frame.vhf_rf_temp
    :field vhf_pa_temp: id1.id2.id3.id4.id5.ax25_frame.vhf_pa_temp
    :field vhf_digipeater_cnt: id1.id2.id3.id4.id5.ax25_frame.vhf_digipeater_cnt
    :field vhf_last_digipeater: id1.id2.id3.id4.id5.ax25_frame.vhf_last_digipeater
    :field vhf_rx_cnt: id1.id2.id3.id4.id5.ax25_frame.vhf_rx_cnt
    :field vhf_tx_cnt: id1.id2.id3.id4.id5.ax25_frame.vhf_tx_cnt
    :field vhf_act_rssi_raw: id1.id2.id3.id4.id5.ax25_frame.vhf_act_rssi_raw
    :field vhf_dcd_rssi_raw: id1.id2.id3.id4.id5.ax25_frame.vhf_dcd_rssi_raw
    
    :field dest_callsign: id1.id2.id3.id4.id5.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: id1.id2.id3.id4.id5.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field veronika_message: id1.id2.id3.id4.id5.ax25_frame.veronika_message
    
    .. seealso::
       Source - https://kozmonautika.sk/2023/11/08/tretia-slovenska-druzica-mieri-do-vesmiru-vsetky-informacie-na-jednom-mieste/
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.id1 = Veronika.Type1(self._io, self, self._root)

    class NotCwMessage(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.message_type2
            if _on == 2660922028:
                self.id3 = Veronika.Digi(self._io, self, self._root)
            else:
                self.id3 = Veronika.NotDigi(self._io, self, self._root)

        @property
        def message_type2(self):
            if hasattr(self, '_m_message_type2'):
                return self._m_message_type2

            _pos = self._io.pos()
            self._io.seek(14)
            self._m_message_type2 = self._io.read_u4be()
            self._io.seek(_pos)
            return getattr(self, '_m_message_type2', None)


    class Psu(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.Psu.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.Psu.Ax25Header(self._io, self, self._root)
                self.psu_pass_packet_type = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                if not self.psu_pass_packet_type == u"PSU":
                    raise kaitaistruct.ValidationNotEqualError(u"PSU", self.psu_pass_packet_type, self._io, u"/types/psu/types/ax25_frame/seq/1")
                self.psu_rst_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_uptime_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_uptime_tot_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_bat_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_temp_sys_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_temp_bat_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_cur_in_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_cur_out_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_ch_state_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_sys_state_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.psu_gnd_wdt_str = (self._io.read_bytes_full()).decode(u"utf8")

            @property
            def psu_ch3_state(self):
                if hasattr(self, '_m_psu_ch3_state'):
                    return self._m_psu_ch3_state

                self._m_psu_ch3_state = ((self.psu_ch_state_num >> 3) & 1)
                return getattr(self, '_m_psu_ch3_state', None)

            @property
            def psu_reset_cnt(self):
                if hasattr(self, '_m_psu_reset_cnt'):
                    return self._m_psu_reset_cnt

                self._m_psu_reset_cnt = int(self.psu_rst_cnt_str)
                return getattr(self, '_m_psu_reset_cnt', None)

            @property
            def psu_uptime_tot(self):
                if hasattr(self, '_m_psu_uptime_tot'):
                    return self._m_psu_uptime_tot

                self._m_psu_uptime_tot = int(self.psu_uptime_tot_str)
                return getattr(self, '_m_psu_uptime_tot', None)

            @property
            def psu_temp_bat(self):
                if hasattr(self, '_m_psu_temp_bat'):
                    return self._m_psu_temp_bat

                self._m_psu_temp_bat = int(self.psu_temp_bat_str)
                return getattr(self, '_m_psu_temp_bat', None)

            @property
            def psu_ch5_state(self):
                if hasattr(self, '_m_psu_ch5_state'):
                    return self._m_psu_ch5_state

                self._m_psu_ch5_state = ((self.psu_ch_state_num >> 5) & 1)
                return getattr(self, '_m_psu_ch5_state', None)

            @property
            def psu_ch0_state(self):
                if hasattr(self, '_m_psu_ch0_state'):
                    return self._m_psu_ch0_state

                self._m_psu_ch0_state = ((self.psu_ch_state_num >> 0) & 1)
                return getattr(self, '_m_psu_ch0_state', None)

            @property
            def psu_gnd_wdt(self):
                if hasattr(self, '_m_psu_gnd_wdt'):
                    return self._m_psu_gnd_wdt

                self._m_psu_gnd_wdt = int(self.psu_gnd_wdt_str)
                return getattr(self, '_m_psu_gnd_wdt', None)

            @property
            def psu_uptime(self):
                if hasattr(self, '_m_psu_uptime'):
                    return self._m_psu_uptime

                self._m_psu_uptime = int(self.psu_uptime_str)
                return getattr(self, '_m_psu_uptime', None)

            @property
            def psu_sys_state(self):
                if hasattr(self, '_m_psu_sys_state'):
                    return self._m_psu_sys_state

                self._m_psu_sys_state = int(self.psu_sys_state_str)
                return getattr(self, '_m_psu_sys_state', None)

            @property
            def psu_ch_state_num(self):
                if hasattr(self, '_m_psu_ch_state_num'):
                    return self._m_psu_ch_state_num

                self._m_psu_ch_state_num = int(self.psu_ch_state_str, 16)
                return getattr(self, '_m_psu_ch_state_num', None)

            @property
            def psu_ch6_state(self):
                if hasattr(self, '_m_psu_ch6_state'):
                    return self._m_psu_ch6_state

                self._m_psu_ch6_state = ((self.psu_ch_state_num >> 6) & 1)
                return getattr(self, '_m_psu_ch6_state', None)

            @property
            def psu_cur_out(self):
                if hasattr(self, '_m_psu_cur_out'):
                    return self._m_psu_cur_out

                self._m_psu_cur_out = int(self.psu_cur_out_str)
                return getattr(self, '_m_psu_cur_out', None)

            @property
            def psu_ch2_state(self):
                if hasattr(self, '_m_psu_ch2_state'):
                    return self._m_psu_ch2_state

                self._m_psu_ch2_state = ((self.psu_ch_state_num >> 2) & 1)
                return getattr(self, '_m_psu_ch2_state', None)

            @property
            def psu_temp_sys(self):
                if hasattr(self, '_m_psu_temp_sys'):
                    return self._m_psu_temp_sys

                self._m_psu_temp_sys = int(self.psu_temp_sys_str)
                return getattr(self, '_m_psu_temp_sys', None)

            @property
            def psu_cur_in(self):
                if hasattr(self, '_m_psu_cur_in'):
                    return self._m_psu_cur_in

                self._m_psu_cur_in = int(self.psu_cur_in_str)
                return getattr(self, '_m_psu_cur_in', None)

            @property
            def psu_ch1_state(self):
                if hasattr(self, '_m_psu_ch1_state'):
                    return self._m_psu_ch1_state

                self._m_psu_ch1_state = ((self.psu_ch_state_num >> 1) & 1)
                return getattr(self, '_m_psu_ch1_state', None)

            @property
            def psu_ch4_state(self):
                if hasattr(self, '_m_psu_ch4_state'):
                    return self._m_psu_ch4_state

                self._m_psu_ch4_state = ((self.psu_ch_state_num >> 4) & 1)
                return getattr(self, '_m_psu_ch4_state', None)

            @property
            def psu_battery(self):
                if hasattr(self, '_m_psu_battery'):
                    return self._m_psu_battery

                self._m_psu_battery = int(self.psu_bat_str)
                return getattr(self, '_m_psu_battery', None)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.Psu.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.Psu.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.Psu.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.Psu.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/psu/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.Psu.Callsign(_io__raw_callsign_ror, self, self._root)



    class Mgs(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.Mgs.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.Mgs.Ax25Header(self._io, self, self._root)
                self.mgs_pass_packet_type = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                if not self.mgs_pass_packet_type == u"MGS":
                    raise kaitaistruct.ValidationNotEqualError(u"MGS", self.mgs_pass_packet_type, self._io, u"/types/mgs/types/ax25_frame/seq/1")
                self.mgs_temp_int_mag_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_temp_int_gyr_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_int_mag_x_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_int_mag_y_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_int_mag_z_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_int_gyr_x_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_int_gyr_y_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_int_gyr_z_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_temp_ext_mag_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_temp_ext_gyr_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_ext_mag_x_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_ext_mag_y_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_ext_mag_z_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_ext_gyr_x_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_ext_gyr_y_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.mgs_ext_gyr_z_str = (self._io.read_bytes_full()).decode(u"utf8")

            @property
            def mgs_int_gyr_y(self):
                if hasattr(self, '_m_mgs_int_gyr_y'):
                    return self._m_mgs_int_gyr_y

                self._m_mgs_int_gyr_y = int(self.mgs_int_gyr_y_str)
                return getattr(self, '_m_mgs_int_gyr_y', None)

            @property
            def mgs_ext_mag_x(self):
                if hasattr(self, '_m_mgs_ext_mag_x'):
                    return self._m_mgs_ext_mag_x

                self._m_mgs_ext_mag_x = int(self.mgs_ext_mag_x_str)
                return getattr(self, '_m_mgs_ext_mag_x', None)

            @property
            def mgs_ext_gyr_z(self):
                if hasattr(self, '_m_mgs_ext_gyr_z'):
                    return self._m_mgs_ext_gyr_z

                self._m_mgs_ext_gyr_z = int(self.mgs_ext_gyr_z_str)
                return getattr(self, '_m_mgs_ext_gyr_z', None)

            @property
            def mgs_ext_mag_z(self):
                if hasattr(self, '_m_mgs_ext_mag_z'):
                    return self._m_mgs_ext_mag_z

                self._m_mgs_ext_mag_z = int(self.mgs_ext_mag_z_str)
                return getattr(self, '_m_mgs_ext_mag_z', None)

            @property
            def mgs_int_gyr_x(self):
                if hasattr(self, '_m_mgs_int_gyr_x'):
                    return self._m_mgs_int_gyr_x

                self._m_mgs_int_gyr_x = int(self.mgs_int_gyr_x_str)
                return getattr(self, '_m_mgs_int_gyr_x', None)

            @property
            def mgs_temp_ext_gyr(self):
                if hasattr(self, '_m_mgs_temp_ext_gyr'):
                    return self._m_mgs_temp_ext_gyr

                self._m_mgs_temp_ext_gyr = int(self.mgs_temp_ext_gyr_str)
                return getattr(self, '_m_mgs_temp_ext_gyr', None)

            @property
            def mgs_int_mag_y(self):
                if hasattr(self, '_m_mgs_int_mag_y'):
                    return self._m_mgs_int_mag_y

                self._m_mgs_int_mag_y = int(self.mgs_int_mag_y_str)
                return getattr(self, '_m_mgs_int_mag_y', None)

            @property
            def mgs_ext_gyr_x(self):
                if hasattr(self, '_m_mgs_ext_gyr_x'):
                    return self._m_mgs_ext_gyr_x

                self._m_mgs_ext_gyr_x = int(self.mgs_ext_gyr_x_str)
                return getattr(self, '_m_mgs_ext_gyr_x', None)

            @property
            def mgs_temp_ext_mag(self):
                if hasattr(self, '_m_mgs_temp_ext_mag'):
                    return self._m_mgs_temp_ext_mag

                self._m_mgs_temp_ext_mag = int(self.mgs_temp_ext_mag_str)
                return getattr(self, '_m_mgs_temp_ext_mag', None)

            @property
            def mgs_ext_gyr_y(self):
                if hasattr(self, '_m_mgs_ext_gyr_y'):
                    return self._m_mgs_ext_gyr_y

                self._m_mgs_ext_gyr_y = int(self.mgs_ext_gyr_y_str)
                return getattr(self, '_m_mgs_ext_gyr_y', None)

            @property
            def mgs_temp_int_gyr(self):
                if hasattr(self, '_m_mgs_temp_int_gyr'):
                    return self._m_mgs_temp_int_gyr

                self._m_mgs_temp_int_gyr = int(self.mgs_temp_int_gyr_str)
                return getattr(self, '_m_mgs_temp_int_gyr', None)

            @property
            def mgs_temp_int_mag(self):
                if hasattr(self, '_m_mgs_temp_int_mag'):
                    return self._m_mgs_temp_int_mag

                self._m_mgs_temp_int_mag = int(self.mgs_temp_int_mag_str)
                return getattr(self, '_m_mgs_temp_int_mag', None)

            @property
            def mgs_int_mag_z(self):
                if hasattr(self, '_m_mgs_int_mag_z'):
                    return self._m_mgs_int_mag_z

                self._m_mgs_int_mag_z = int(self.mgs_int_mag_z_str)
                return getattr(self, '_m_mgs_int_mag_z', None)

            @property
            def mgs_int_mag_x(self):
                if hasattr(self, '_m_mgs_int_mag_x'):
                    return self._m_mgs_int_mag_x

                self._m_mgs_int_mag_x = int(self.mgs_int_mag_x_str)
                return getattr(self, '_m_mgs_int_mag_x', None)

            @property
            def mgs_ext_mag_y(self):
                if hasattr(self, '_m_mgs_ext_mag_y'):
                    return self._m_mgs_ext_mag_y

                self._m_mgs_ext_mag_y = int(self.mgs_ext_mag_y_str)
                return getattr(self, '_m_mgs_ext_mag_y', None)

            @property
            def mgs_int_gyr_z(self):
                if hasattr(self, '_m_mgs_int_gyr_z'):
                    return self._m_mgs_int_gyr_z

                self._m_mgs_int_gyr_z = int(self.mgs_int_gyr_z_str)
                return getattr(self, '_m_mgs_int_gyr_z', None)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.Mgs.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.Mgs.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.Mgs.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.Mgs.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/mgs/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.Mgs.Callsign(_io__raw_callsign_ror, self, self._root)



    class Type1(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.message_type1
            if _on == 7234224039386510949:
                self.id2 = Veronika.CwMessage(self._io, self, self._root)
            else:
                self.id2 = Veronika.NotCwMessage(self._io, self, self._root)

        @property
        def message_type1(self):
            if hasattr(self, '_m_message_type1'):
                return self._m_message_type1

            _pos = self._io.pos()
            self._io.seek(0)
            self._m_message_type1 = self._io.read_u8be()
            self._io.seek(_pos)
            return getattr(self, '_m_message_type1', None)


    class U(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.U.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.U.Ax25Header(self._io, self, self._root)
                self.uhf_packet_id_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                if not self.uhf_packet_id_str == u"U":
                    raise kaitaistruct.ValidationNotEqualError(u"U", self.uhf_packet_id_str, self._io, u"/types/u/types/ax25_frame/seq/1")
                self.uhf_uptime_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_uptime_tot_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_reset_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_rf_reset_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_trx_temp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_rf_temp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_pa_temp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_digipeater_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_last_digipeater_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_rx_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_tx_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_act_rssi_raw_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.uhf_dcd_rssi_raw_str = (self._io.read_bytes_term(0, False, True, True)).decode(u"utf8")

            @property
            def uhf_rf_reset_cnt(self):
                if hasattr(self, '_m_uhf_rf_reset_cnt'):
                    return self._m_uhf_rf_reset_cnt

                self._m_uhf_rf_reset_cnt = int(self.uhf_rf_reset_cnt_str)
                return getattr(self, '_m_uhf_rf_reset_cnt', None)

            @property
            def uhf_act_rssi_raw(self):
                if hasattr(self, '_m_uhf_act_rssi_raw'):
                    return self._m_uhf_act_rssi_raw

                self._m_uhf_act_rssi_raw = int(self.uhf_act_rssi_raw_str)
                return getattr(self, '_m_uhf_act_rssi_raw', None)

            @property
            def uhf_last_digipeater(self):
                if hasattr(self, '_m_uhf_last_digipeater'):
                    return self._m_uhf_last_digipeater

                self._m_uhf_last_digipeater = self.uhf_last_digipeater_str
                return getattr(self, '_m_uhf_last_digipeater', None)

            @property
            def uhf_pa_temp(self):
                if hasattr(self, '_m_uhf_pa_temp'):
                    return self._m_uhf_pa_temp

                self._m_uhf_pa_temp = int(self.uhf_pa_temp_str)
                return getattr(self, '_m_uhf_pa_temp', None)

            @property
            def uhf_uptime_tot(self):
                if hasattr(self, '_m_uhf_uptime_tot'):
                    return self._m_uhf_uptime_tot

                self._m_uhf_uptime_tot = int(self.uhf_uptime_tot_str)
                return getattr(self, '_m_uhf_uptime_tot', None)

            @property
            def uhf_tx_cnt(self):
                if hasattr(self, '_m_uhf_tx_cnt'):
                    return self._m_uhf_tx_cnt

                self._m_uhf_tx_cnt = int(self.uhf_tx_cnt_str)
                return getattr(self, '_m_uhf_tx_cnt', None)

            @property
            def uhf_rf_temp(self):
                if hasattr(self, '_m_uhf_rf_temp'):
                    return self._m_uhf_rf_temp

                self._m_uhf_rf_temp = int(self.uhf_rf_temp_str)
                return getattr(self, '_m_uhf_rf_temp', None)

            @property
            def uhf_dcd_rssi_raw(self):
                if hasattr(self, '_m_uhf_dcd_rssi_raw'):
                    return self._m_uhf_dcd_rssi_raw

                self._m_uhf_dcd_rssi_raw = int(self.uhf_dcd_rssi_raw_str)
                return getattr(self, '_m_uhf_dcd_rssi_raw', None)

            @property
            def uhf_uptime(self):
                if hasattr(self, '_m_uhf_uptime'):
                    return self._m_uhf_uptime

                self._m_uhf_uptime = int(self.uhf_uptime_str)
                return getattr(self, '_m_uhf_uptime', None)

            @property
            def uhf_rx_cnt(self):
                if hasattr(self, '_m_uhf_rx_cnt'):
                    return self._m_uhf_rx_cnt

                self._m_uhf_rx_cnt = int(self.uhf_rx_cnt_str)
                return getattr(self, '_m_uhf_rx_cnt', None)

            @property
            def uhf_reset_cnt(self):
                if hasattr(self, '_m_uhf_reset_cnt'):
                    return self._m_uhf_reset_cnt

                self._m_uhf_reset_cnt = int(self.uhf_reset_cnt_str)
                return getattr(self, '_m_uhf_reset_cnt', None)

            @property
            def uhf_digipeater_cnt(self):
                if hasattr(self, '_m_uhf_digipeater_cnt'):
                    return self._m_uhf_digipeater_cnt

                self._m_uhf_digipeater_cnt = int(self.uhf_digipeater_cnt_str)
                return getattr(self, '_m_uhf_digipeater_cnt', None)

            @property
            def uhf_trx_temp(self):
                if hasattr(self, '_m_uhf_trx_temp'):
                    return self._m_uhf_trx_temp

                self._m_uhf_trx_temp = int(self.uhf_trx_temp_str)
                return getattr(self, '_m_uhf_trx_temp', None)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.U.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.U.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.U.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.U.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/u/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.U.Callsign(_io__raw_callsign_ror, self, self._root)



    class CwMessage(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.de_om9ver = (self._io.read_bytes(13)).decode(u"ASCII")
            if not self.de_om9ver == u"de om9ver = u":
                raise kaitaistruct.ValidationNotEqualError(u"de om9ver = u", self.de_om9ver, self._io, u"/types/cw_message/seq/0")
            self.uptime_total_raw = (self._io.read_bytes_term(114, False, True, True)).decode(u"UTF-8")
            self.reset_number_raw = (self._io.read_bytes_term(116, False, True, True)).decode(u"UTF-8")
            self.temp_mcu_raw = (self._io.read_bytes_term(112, False, True, True)).decode(u"UTF-8")
            self.temp_pa_raw = (self._io.read_bytes_term(32, False, True, True)).decode(u"UTF-8")
            self.ar = (self._io.read_bytes(2)).decode(u"UTF-8")
            if not self.ar == u"ar":
                raise kaitaistruct.ValidationNotEqualError(u"ar", self.ar, self._io, u"/types/cw_message/seq/5")

        @property
        def temp_pa(self):
            if hasattr(self, '_m_temp_pa'):
                return self._m_temp_pa

            if  (((self.temp_pa_raw)[(len(self.temp_pa_raw) - 1):len(self.temp_pa_raw)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 2):(len(self.temp_pa_raw) - 1)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 3):(len(self.temp_pa_raw) - 2)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 4):(len(self.temp_pa_raw) - 3)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 5):(len(self.temp_pa_raw) - 4)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 6):(len(self.temp_pa_raw) - 5)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 7):(len(self.temp_pa_raw) - 6)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 8):(len(self.temp_pa_raw) - 7)] != u".") and ((self.temp_pa_raw)[(len(self.temp_pa_raw) - 9):(len(self.temp_pa_raw) - 8)] != u".")) :
                self._m_temp_pa = int(self.temp_pa_raw)

            return getattr(self, '_m_temp_pa', None)

        @property
        def temp_mcu(self):
            if hasattr(self, '_m_temp_mcu'):
                return self._m_temp_mcu

            if  (((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 1):len(self.temp_mcu_raw)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 2):(len(self.temp_mcu_raw) - 1)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 3):(len(self.temp_mcu_raw) - 2)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 4):(len(self.temp_mcu_raw) - 3)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 5):(len(self.temp_mcu_raw) - 4)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 6):(len(self.temp_mcu_raw) - 5)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 7):(len(self.temp_mcu_raw) - 6)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 8):(len(self.temp_mcu_raw) - 7)] != u".") and ((self.temp_mcu_raw)[(len(self.temp_mcu_raw) - 9):(len(self.temp_mcu_raw) - 8)] != u".")) :
                self._m_temp_mcu = int(self.temp_mcu_raw)

            return getattr(self, '_m_temp_mcu', None)

        @property
        def uptime_total(self):
            if hasattr(self, '_m_uptime_total'):
                return self._m_uptime_total

            if  (((self.uptime_total_raw)[(len(self.uptime_total_raw) - 1):len(self.uptime_total_raw)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 2):(len(self.uptime_total_raw) - 1)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 3):(len(self.uptime_total_raw) - 2)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 4):(len(self.uptime_total_raw) - 3)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 5):(len(self.uptime_total_raw) - 4)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 6):(len(self.uptime_total_raw) - 5)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 7):(len(self.uptime_total_raw) - 6)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 8):(len(self.uptime_total_raw) - 7)] != u".") and ((self.uptime_total_raw)[(len(self.uptime_total_raw) - 9):(len(self.uptime_total_raw) - 8)] != u".")) :
                self._m_uptime_total = int(self.uptime_total_raw)

            return getattr(self, '_m_uptime_total', None)

        @property
        def cw_beacon(self):
            if hasattr(self, '_m_cw_beacon'):
                return self._m_cw_beacon

            self._m_cw_beacon = u"u" + self.uptime_total_raw + u"r" + self.reset_number_raw + u"t" + self.temp_mcu_raw + u"p" + self.temp_pa_raw
            return getattr(self, '_m_cw_beacon', None)

        @property
        def reset_number(self):
            if hasattr(self, '_m_reset_number'):
                return self._m_reset_number

            if  (((self.reset_number_raw)[(len(self.reset_number_raw) - 1):len(self.reset_number_raw)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 2):(len(self.reset_number_raw) - 1)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 3):(len(self.reset_number_raw) - 2)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 4):(len(self.reset_number_raw) - 3)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 5):(len(self.reset_number_raw) - 4)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 6):(len(self.reset_number_raw) - 5)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 7):(len(self.reset_number_raw) - 6)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 8):(len(self.reset_number_raw) - 7)] != u".") and ((self.reset_number_raw)[(len(self.reset_number_raw) - 9):(len(self.reset_number_raw) - 8)] != u".")) :
                self._m_reset_number = int(self.reset_number_raw)

            return getattr(self, '_m_reset_number', None)


    class V(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.V.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.V.Ax25Header(self._io, self, self._root)
                self.vhf_packet_id_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                if not self.vhf_packet_id_str == u"V":
                    raise kaitaistruct.ValidationNotEqualError(u"V", self.vhf_packet_id_str, self._io, u"/types/v/types/ax25_frame/seq/1")
                self.vhf_uptime_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_uptime_tot_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_reset_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_rf_reset_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_trx_temp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_rf_temp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_pa_temp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_digipeater_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_last_digipeater_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_rx_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_tx_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_act_rssi_raw_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.vhf_dcd_rssi_raw_str = (self._io.read_bytes_term(0, False, True, True)).decode(u"utf8")

            @property
            def vhf_digipeater_cnt(self):
                if hasattr(self, '_m_vhf_digipeater_cnt'):
                    return self._m_vhf_digipeater_cnt

                self._m_vhf_digipeater_cnt = int(self.vhf_digipeater_cnt_str)
                return getattr(self, '_m_vhf_digipeater_cnt', None)

            @property
            def vhf_tx_cnt(self):
                if hasattr(self, '_m_vhf_tx_cnt'):
                    return self._m_vhf_tx_cnt

                self._m_vhf_tx_cnt = int(self.vhf_tx_cnt_str)
                return getattr(self, '_m_vhf_tx_cnt', None)

            @property
            def vhf_rx_cnt(self):
                if hasattr(self, '_m_vhf_rx_cnt'):
                    return self._m_vhf_rx_cnt

                self._m_vhf_rx_cnt = int(self.vhf_rx_cnt_str)
                return getattr(self, '_m_vhf_rx_cnt', None)

            @property
            def vhf_last_digipeater(self):
                if hasattr(self, '_m_vhf_last_digipeater'):
                    return self._m_vhf_last_digipeater

                self._m_vhf_last_digipeater = self.vhf_last_digipeater_str
                return getattr(self, '_m_vhf_last_digipeater', None)

            @property
            def vhf_pa_temp(self):
                if hasattr(self, '_m_vhf_pa_temp'):
                    return self._m_vhf_pa_temp

                self._m_vhf_pa_temp = int(self.vhf_pa_temp_str)
                return getattr(self, '_m_vhf_pa_temp', None)

            @property
            def vhf_uptime(self):
                if hasattr(self, '_m_vhf_uptime'):
                    return self._m_vhf_uptime

                self._m_vhf_uptime = int(self.vhf_uptime_str)
                return getattr(self, '_m_vhf_uptime', None)

            @property
            def vhf_rf_temp(self):
                if hasattr(self, '_m_vhf_rf_temp'):
                    return self._m_vhf_rf_temp

                self._m_vhf_rf_temp = int(self.vhf_rf_temp_str)
                return getattr(self, '_m_vhf_rf_temp', None)

            @property
            def vhf_uptime_tot(self):
                if hasattr(self, '_m_vhf_uptime_tot'):
                    return self._m_vhf_uptime_tot

                self._m_vhf_uptime_tot = int(self.vhf_uptime_tot_str)
                return getattr(self, '_m_vhf_uptime_tot', None)

            @property
            def vhf_trx_temp(self):
                if hasattr(self, '_m_vhf_trx_temp'):
                    return self._m_vhf_trx_temp

                self._m_vhf_trx_temp = int(self.vhf_trx_temp_str)
                return getattr(self, '_m_vhf_trx_temp', None)

            @property
            def vhf_rf_reset_cnt(self):
                if hasattr(self, '_m_vhf_rf_reset_cnt'):
                    return self._m_vhf_rf_reset_cnt

                self._m_vhf_rf_reset_cnt = int(self.vhf_rf_reset_cnt_str)
                return getattr(self, '_m_vhf_rf_reset_cnt', None)

            @property
            def vhf_dcd_rssi_raw(self):
                if hasattr(self, '_m_vhf_dcd_rssi_raw'):
                    return self._m_vhf_dcd_rssi_raw

                self._m_vhf_dcd_rssi_raw = int(self.vhf_dcd_rssi_raw_str)
                return getattr(self, '_m_vhf_dcd_rssi_raw', None)

            @property
            def vhf_reset_cnt(self):
                if hasattr(self, '_m_vhf_reset_cnt'):
                    return self._m_vhf_reset_cnt

                self._m_vhf_reset_cnt = int(self.vhf_reset_cnt_str)
                return getattr(self, '_m_vhf_reset_cnt', None)

            @property
            def vhf_act_rssi_raw(self):
                if hasattr(self, '_m_vhf_act_rssi_raw'):
                    return self._m_vhf_act_rssi_raw

                self._m_vhf_act_rssi_raw = int(self.vhf_act_rssi_raw_str)
                return getattr(self, '_m_vhf_act_rssi_raw', None)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.V.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.V.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.V.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.V.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/v/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.V.Callsign(_io__raw_callsign_ror, self, self._root)



    class VOrU(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.message_type4
            if _on == 21804:
                self.id5 = Veronika.U(self._io, self, self._root)
            elif _on == 22060:
                self.id5 = Veronika.V(self._io, self, self._root)
            else:
                self.id5 = Veronika.VeronikaMessage(self._io, self, self._root)

        @property
        def message_type4(self):
            if hasattr(self, '_m_message_type4'):
                return self._m_message_type4

            _pos = self._io.pos()
            self._io.seek(16)
            self._m_message_type4 = self._io.read_u2be()
            self._io.seek(_pos)
            return getattr(self, '_m_message_type4', None)


    class VeronikaMessage(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.VeronikaMessage.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.VeronikaMessage.Ax25Header(self._io, self, self._root)
                self.veronika_message = (self._io.read_bytes_full()).decode(u"utf8")


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.VeronikaMessage.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.VeronikaMessage.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.VeronikaMessage.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.VeronikaMessage.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/veronika_message/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.VeronikaMessage.Callsign(_io__raw_callsign_ror, self, self._root)



    class Obc(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.Obc.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.Obc.Ax25Header(self._io, self, self._root)
                self.obc_pass_packet_type = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                if not self.obc_pass_packet_type == u"OBC":
                    raise kaitaistruct.ValidationNotEqualError(u"OBC", self.obc_pass_packet_type, self._io, u"/types/obc/types/ax25_frame/seq/1")
                self.obc_rst_cnt_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.obc_uptime_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.obc_uptime_tot_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.obc_bat_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.obc_temp_mcu_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.obc_freemem_str = (self._io.read_bytes_full()).decode(u"utf8")

            @property
            def obc_uptime(self):
                if hasattr(self, '_m_obc_uptime'):
                    return self._m_obc_uptime

                self._m_obc_uptime = int(self.obc_uptime_str)
                return getattr(self, '_m_obc_uptime', None)

            @property
            def obc_freemem(self):
                if hasattr(self, '_m_obc_freemem'):
                    return self._m_obc_freemem

                self._m_obc_freemem = int(self.obc_freemem_str)
                return getattr(self, '_m_obc_freemem', None)

            @property
            def obc_bat(self):
                if hasattr(self, '_m_obc_bat'):
                    return self._m_obc_bat

                self._m_obc_bat = int(self.obc_bat_str)
                return getattr(self, '_m_obc_bat', None)

            @property
            def obc_uptime_tot(self):
                if hasattr(self, '_m_obc_uptime_tot'):
                    return self._m_obc_uptime_tot

                self._m_obc_uptime_tot = int(self.obc_uptime_tot_str)
                return getattr(self, '_m_obc_uptime_tot', None)

            @property
            def obc_reset_cnt(self):
                if hasattr(self, '_m_obc_reset_cnt'):
                    return self._m_obc_reset_cnt

                self._m_obc_reset_cnt = int(self.obc_rst_cnt_str)
                return getattr(self, '_m_obc_reset_cnt', None)

            @property
            def obc_temp_mcu(self):
                if hasattr(self, '_m_obc_temp_mcu'):
                    return self._m_obc_temp_mcu

                self._m_obc_temp_mcu = int(self.obc_temp_mcu_str)
                return getattr(self, '_m_obc_temp_mcu', None)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.Obc.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.Obc.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.Obc.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.Obc.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/obc/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.Obc.Callsign(_io__raw_callsign_ror, self, self._root)



    class Digi(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.Digi.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.Digi.Ax25Header(self._io, self, self._root)
                self._raw_ax25_info = self._io.read_bytes_full()
                _io__raw_ax25_info = KaitaiStream(BytesIO(self._raw_ax25_info))
                self.ax25_info = Veronika.Digi.Ax25InfoData(_io__raw_ax25_info, self, self._root)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.Digi.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.Digi.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.Digi.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.Digi.SsidMask(self._io, self, self._root)
                if (self.src_ssid_raw.ssid_mask & 1) == 0:
                    self.repeater = Veronika.Digi.Repeater(self._io, self, self._root)

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
                self.rpt_callsign_raw = Veronika.Digi.CallsignRaw(self._io, self, self._root)
                self.rpt_ssid_raw = Veronika.Digi.SsidMask(self._io, self, self._root)


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
                    _ = Veronika.Digi.Repeaters(self._io, self, self._root)
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
                self.callsign_ror = Veronika.Digi.Callsign(_io__raw_callsign_ror, self, self._root)


        class Ax25InfoData(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.digi_message = (self._io.read_bytes_full()).decode(u"utf-8")



    class NotDigi(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.message_type3
            if _on == 1329742636:
                self.id4 = Veronika.Obc(self._io, self, self._root)
            elif _on == 1296519980:
                self.id4 = Veronika.Mgs(self._io, self, self._root)
            elif _on == 1347638572:
                self.id4 = Veronika.Psu(self._io, self, self._root)
            elif _on == 1397705772:
                self.id4 = Veronika.Sol(self._io, self, self._root)
            else:
                self.id4 = Veronika.VOrU(self._io, self, self._root)

        @property
        def message_type3(self):
            if hasattr(self, '_m_message_type3'):
                return self._m_message_type3

            _pos = self._io.pos()
            self._io.seek(16)
            self._m_message_type3 = self._io.read_u4be()
            self._io.seek(_pos)
            return getattr(self, '_m_message_type3', None)


    class Sol(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Veronika.Sol.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Veronika.Sol.Ax25Header(self._io, self, self._root)
                self.sol_pass_packet_type = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                if not self.sol_pass_packet_type == u"SOL":
                    raise kaitaistruct.ValidationNotEqualError(u"SOL", self.sol_pass_packet_type, self._io, u"/types/sol/types/ax25_frame/seq/1")
                self.sol_temp_zp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_temp_xp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_temp_yp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_temp_zn_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_temp_xn_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_temp_yn_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_diode_zp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_diode_xp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_diode_yp_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_diode_zn_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_diode_xn_str = (self._io.read_bytes_term(44, False, True, True)).decode(u"utf8")
                self.sol_diode_yn_str = (self._io.read_bytes_full()).decode(u"utf8")

            @property
            def sol_temp_zp(self):
                if hasattr(self, '_m_sol_temp_zp'):
                    return self._m_sol_temp_zp

                self._m_sol_temp_zp = int(self.sol_temp_zp_str)
                return getattr(self, '_m_sol_temp_zp', None)

            @property
            def sol_diode_zn(self):
                if hasattr(self, '_m_sol_diode_zn'):
                    return self._m_sol_diode_zn

                self._m_sol_diode_zn = int(self.sol_diode_zn_str)
                return getattr(self, '_m_sol_diode_zn', None)

            @property
            def sol_diode_xp(self):
                if hasattr(self, '_m_sol_diode_xp'):
                    return self._m_sol_diode_xp

                self._m_sol_diode_xp = int(self.sol_diode_xp_str)
                return getattr(self, '_m_sol_diode_xp', None)

            @property
            def sol_temp_zn(self):
                if hasattr(self, '_m_sol_temp_zn'):
                    return self._m_sol_temp_zn

                self._m_sol_temp_zn = int(self.sol_temp_zn_str)
                return getattr(self, '_m_sol_temp_zn', None)

            @property
            def sol_diode_yn(self):
                if hasattr(self, '_m_sol_diode_yn'):
                    return self._m_sol_diode_yn

                self._m_sol_diode_yn = int(self.sol_diode_yn_str)
                return getattr(self, '_m_sol_diode_yn', None)

            @property
            def sol_temp_yn(self):
                if hasattr(self, '_m_sol_temp_yn'):
                    return self._m_sol_temp_yn

                self._m_sol_temp_yn = int(self.sol_temp_yn_str)
                return getattr(self, '_m_sol_temp_yn', None)

            @property
            def sol_diode_zp(self):
                if hasattr(self, '_m_sol_diode_zp'):
                    return self._m_sol_diode_zp

                self._m_sol_diode_zp = int(self.sol_diode_zp_str)
                return getattr(self, '_m_sol_diode_zp', None)

            @property
            def sol_temp_xn(self):
                if hasattr(self, '_m_sol_temp_xn'):
                    return self._m_sol_temp_xn

                self._m_sol_temp_xn = int(self.sol_temp_xn_str)
                return getattr(self, '_m_sol_temp_xn', None)

            @property
            def sol_diode_xn(self):
                if hasattr(self, '_m_sol_diode_xn'):
                    return self._m_sol_diode_xn

                self._m_sol_diode_xn = int(self.sol_diode_xn_str)
                return getattr(self, '_m_sol_diode_xn', None)

            @property
            def sol_diode_yp(self):
                if hasattr(self, '_m_sol_diode_yp'):
                    return self._m_sol_diode_yp

                self._m_sol_diode_yp = int(self.sol_diode_yp_str)
                return getattr(self, '_m_sol_diode_yp', None)

            @property
            def sol_temp_xp(self):
                if hasattr(self, '_m_sol_temp_xp'):
                    return self._m_sol_temp_xp

                self._m_sol_temp_xp = int(self.sol_temp_xp_str)
                return getattr(self, '_m_sol_temp_xp', None)

            @property
            def sol_temp_yp(self):
                if hasattr(self, '_m_sol_temp_yp'):
                    return self._m_sol_temp_yp

                self._m_sol_temp_yp = int(self.sol_temp_yp_str)
                return getattr(self, '_m_sol_temp_yp', None)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Veronika.Sol.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Veronika.Sol.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Veronika.Sol.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Veronika.Sol.SsidMask(self._io, self, self._root)
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
                if not  ((self.callsign == u"CQ    ") or (self.callsign == u"OM9VER")) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.callsign, self._io, u"/types/sol/types/callsign/seq/0")


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
                self.callsign_ror = Veronika.Sol.Callsign(_io__raw_callsign_ror, self, self._root)




