import os
import sys
import time
import logging
import numpy as np


__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


WMI_AOA_MAX_DATA_SIZE = 128
WMI_AOA_MAX_DATA_U16_32_SIZE = 32
WMI_AOA_MAX_DATA_U16_64_SIZE = 64
DTYPE_AOA_MEAS_TLV = np.dtype([
    ("mac_0", np.uint8),
    ("mac_1", np.uint8),
    ("mac_2", np.uint8),
    ("mac_3", np.uint8),
    ("mac_4", np.uint8),
    ("mac_5", np.uint8),
    ("channel", np.uint8),
    ("aoa_meas_type", np.uint8),
    ("meas_rf_mask", np.uint32),
    ("meas_status", np.uint8),
    ("reserved", np.uint8),
    ("length", np.uint16),
    ('aoa_data', np.uint16, (0,))
]).newbyteorder('<')

# WMI_AOA_MEAS_EVENTID */
#struct wmi_aoa_meas_event {
#    u8 mac_addr[WMI_MAC_LEN];
#    /* channels IDs:
#     * 0 - 58320 MHz
#     * 1 - 60480 MHz
#     * 2 - 62640 MHz
#     */
#    u8 channel;
#    /* enum wmi_aoa_meas_type */
#    u8 aoa_meas_type;
#    /* Measurments are from RFs, defined by the mask */
#    __le32 meas_rf_mask;
#    /* enum wmi_aoa_meas_status */
#    u8 meas_status;
#    u8 reserved;
#    /* Length of meas_data in bytes */
#    __le16 length;
#    u8 meas_data[WMI_AOA_MAX_DATA_SIZE];
#} __packed;

#    QCA_WLAN_VENDOR_ATTR_LOC_ANTENNA_ARRAY_MASK = 24,
#    /* AOA measurement data. Its contents depends on the AOA measurement
#     * type and antenna array mask:
#     * QCA_WLAN_VENDOR_ATTR_AOA_TYPE_TOP_CIR_PHASE: array of U16 values,
#     * phase of the strongest CIR path for each antenna in the measured
#     * array(s).
#     * QCA_WLAN_VENDOR_ATTR_AOA_TYPE_TOP_CIR_PHASE_AMP: array of 2 U16
#     * values, phase and amplitude of the strongest CIR path for each
#     * antenna in the measured array(s).
#     */


class WiGigCirEntry(object):
    """docstring for CsiEntry"""
    def __init__(self):
        super(WiGigCirEntry, self).__init__()
        self.srcMac = None
        self.channel = None
        self.aoa_meas_type = None
        self.meas_rf_mask = None
        self.meas_status = None
        self.length = None
        self.amplitude = None
        self.phase = None

    def __str__(self):
        myString = "CIR Entry:\n"
        myString += "\t Src MAC address: " + str(self.srcMac)
        #myString += "\t Channel: " + str(self.channel)
        #myString += "\t AOA meas type: " + str(self.aoa_meas_type) + "\n"
        #myString += "\t Meas RF mask: " + str(self.meas_rf_mask) + "\n"
        #myString += "\t Meas status: " + str(self.meas_status) + "\n"
        #myString += "\t Length: " + str(self.length) + "\n"
        return myString


class WiGigCirReceiver(object):
    """docstring for WiGigCirReceiver"""
    def __init__(self, interfaceName):
        self.interfaceName = interfaceName
        self.phyName = self.get_device_phy_name(interfaceName)
        self.phyIdx = self.get_device_phy_id(interfaceName)
        self.fileBasePath = None

        # in WIL6210 card
        filePath = "/sys/kernel/debug/ieee80211/{}/wil6210/tof_aoa".format(self.phyName)
        if os.path.isfile(filePath):
            self.fileBasePath = "/sys/kernel/debug/ieee80211/{}/wil6210/".format(self.phyName)
        else:
            print("No WiGig card found!")

        # cir collection config
        self.cir_addresses_list = []
        self.current_mac_idx = 0
        self.cir_interval = 1
        self.cir_channel = 0
        self.aoaMeasFd = None

    def _read_file(self, fn):
        fd = open(fn, 'r')
        dat = fd.read()
        fd.close()
        return dat

    def _write_file(self, fn, msg):
        f = open(fn, 'w')
        f.write(msg)
        f.close()

    def get_device_phy_name(self,iface):
        ''' get phy id for this interface '''
        fn = '/sys/class/net/{}/phy80211/name'.format(iface)
        if (os.path.isfile(fn)):
            phyid = self._read_file(fn).strip()
            return phyid
        return None

    def get_device_phy_id(self,iface):
        ''' get phy id for this interface '''
        fn = '/sys/class/net/{}/phy80211/index'.format(iface)
        if (os.path.isfile(fn)):
            phyid = self._read_file(fn).strip()
            return int(phyid)
        return None

    def _set_aoa_type(self,aoaType=1):
        # set AoA type
        #   0 -> only phase
        #   1 -> phase and amplitude
        aoaType = str(aoaType)
        filePath = self.fileBasePath + "tof_aoa_type"
        self._write_file(filePath, aoaType)

    def _set_aoa_meas_rf_mask(self,value=0):
        value = str(value)
        filePath = self.fileBasePath + "tof_aoa_meas_rf_mask"
        self._write_file(filePath, value)

    def _set_aoa_meas_channel(self,value=0):
        value = str(value)
        filePath = self.fileBasePath + "tof_aoa_meas_channel"
        self._write_file(filePath, value)

    def _set_aoa_meas_address(self, macAddress):
        macAddress = str(macAddress)
        filePath = self.fileBasePath + "tof_aoa_meas_address"
        self._write_file(filePath, macAddress)

    def _trigger_aoa_measurements(self):
        filePath = self.fileBasePath + "tof_aoa"
        self._read_file(filePath)

    def _open_aoa_measuement_fd(self):
        filePath = self.fileBasePath + "aoa_meas0"
        self.aoaMeasFd = open(filePath, 'rb')

    def _close_aoa_measuement_fd(self):
        self.aoaMeasFd.close()

    def set_mac_address_filter(self, macAddressList):
        self.cir_addresses_list = macAddressList

    def set_channel(self, channel):
        self.cir_channel = channel

    def set_measurement_interval(self, interval):
        self.cir_interval = interval

    def start(self):
        self._set_aoa_type(1)
        self._open_aoa_measuement_fd()

    def stop(self):
        self._close_aoa_measuement_fd()

    def receive(self):
        time.sleep(self.cir_interval)

        # set src mac address
        currentMac = self.cir_addresses_list[self.current_mac_idx]
        self._set_aoa_meas_address(currentMac)

        self.current_mac_idx += 1
        if (self.current_mac_idx >= len(self.cir_addresses_list)):
            self.current_mac_idx = 0

        # set proper MAC address
        self._trigger_aoa_measurements()
        # read AoA measurements data
        data = self.aoaMeasFd.read()

        if (len(data) == 0):
            return None

        # Decode relayFS data
        s = 0
        e = DTYPE_AOA_MEAS_TLV.itemsize
        aoaData = np.frombuffer(data[s:e], dtype=DTYPE_AOA_MEAS_TLV)

        # mac address
        macAddr = '{:02x}'.format(aoaData['mac_0'][0])+":"
        macAddr += '{:02x}'.format(aoaData['mac_1'][0])+":"
        macAddr += '{:02x}'.format(aoaData['mac_2'][0])+":"
        macAddr += '{:02x}'.format(aoaData['mac_3'][0])+":"
        macAddr += '{:02x}'.format(aoaData['mac_4'][0])+":"
        macAddr += '{:02x}'.format(aoaData['mac_5'][0])

        channel = aoaData["channel"][0]
        aoa_meas_type = aoaData["aoa_meas_type"][0]
        meas_rf_mask = aoaData["meas_rf_mask"][0]
        meas_status = aoaData["meas_status"][0]
        length = aoaData["length"][0]
        aoa_data = aoaData["aoa_data"][0]
        aoa_data = np.frombuffer(data[e:], dtype=np.uint16)

        # the phase values are represented using 10 bits, ranging between 0 and 1023, to encode phase values between 0 and 2π radians;
        # the amplitude values range between 0 and 178
        phase = aoa_data[:32]
        phase = phase / 1023
        phase = phase * 2*np.pi
        ampl = []
        if aoa_meas_type == 1:
            ampl = aoa_data[32:]

        cirEntry = WiGigCirEntry()
        cirEntry.srcMac = macAddr
        cirEntry.channel = channel
        cirEntry.aoa_meas_type = aoa_meas_type
        cirEntry.meas_rf_mask = meas_rf_mask
        cirEntry.meas_status = meas_status
        cirEntry.length = length
        cirEntry.amplitude = ampl
        cirEntry.phase = phase

        return cirEntry