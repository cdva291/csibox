import os
import sys
import logging
import numpy as np
from pyroute2 import IPRoute
from pyroute2.iwutil import IW
from pyroute2.netlink import NLM_F_REQUEST
from pyroute2.netlink import NLM_F_ACK
from pyroute2.netlink.nl80211 import nl80211cmd
from pyroute2.netlink.nl80211 import NL80211_NAMES


__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


DTYPE_CSI_HEADER_TLV = np.dtype([
    ('reserved_0', np.uint32),
    ('csi_msg_size', np.uint32),
    ('reserved_1', np.uint32),
    ("timestamp_1", np.uint32),
    ('zeros_0', np.uint32, (7,)),
    ('reserved_2', np.uint16),
    ('bw_idx', np.uint8),
    ('streamNum', np.uint8),
    ('reserved_3', np.uint8, (8,)),
    ('scNum', np.uint8),
    ('zeros_1', np.uint8, (7,)),
    ('rssi_1', np.uint32),
    ('rssi_2', np.uint32),
    ('srcMac', np.uint8, (6,)),
    ('zeros_2', np.uint16),
    ('counter', np.uint8),
    ('zeros_3', np.uint8, (2,)),
    ('reserved_4', np.uint8),
    ('zeros_4', np.uint8, (8,)),
    ('timestamp_2', np.uint32),
    ('mcs', np.uint8),
    ('channelMask', np.uint8),
    ('zeros_5', np.uint16),
    ('reserved_A', np.uint8, (20,)),
    ('reserved_B', np.uint8, (20,)),
    ('reserved_C', np.uint8, (20,)),
    ('reserved_D', np.uint8, (20,)),
    ('reserved_5', np.uint8, (4,)),
    ('reserved_6_1', np.uint8, (4,)),
    ('reserved_7', np.uint16),
    ('zeros_6', np.uint16),
    ('reserved_6_2', np.uint8, (4,)),
    ('counter_2', np.uint16),
    ('zeros_7', np.uint16),
    ('timestamp_3', np.uint32),
    ('reserved', np.uint8, (68,)),
]).newbyteorder('<')

DTYPE_CSI_DATA_TLV = np.dtype(np.int16).newbyteorder('<')


class WifiCsiEntry(object):
    """docstring for WifiCsiEntry"""
    def __init__(self):
        super(WifiCsiEntry, self).__init__()
        self.correct = True
        self.code = None
        self.wiphyIdx = None
        self.counter = None
        self.srcMac = None
        self.Nrx = None
        self.Ntx = None
        self.bwIdx = None
        self.bandwidth = None
        self.mcs = None
        self.scNum = None
        self.rssiA = None
        self.rssiB = None
        self.noise = None
        self.agc = None
        self.antenna_sel = None
        self.length = None
        self.rssiA_db = None
        self.rssiB_db = None
        self.csi = None
        self.perm = None
        self.csi_pwr = None
        self.rssi_pwr_db = None
        self.rssi_pwr = None
        self.scale = None
        self.noise_db = None
        self.quant_error_pwr = None
        self.total_noise_pwr = None
        self.timestamp = None

    def __str__(self):
        myString = "CSI Entry:\n"    
        if not self.correct:
            myString += "\t Invalid data\n"
            return myString

        myString += "\t wiphy idx: " + str(self.wiphyIdx) + "\n"
        myString += "\t Counter: " + str(self.counter) + "\n"
        myString += "\t Src MAC address: " + str(self.srcMac) + "\n"
        myString += "\t Ntx: " + str(self.Ntx) + "\n"
        myString += "\t Nrx: " + str(self.Nrx) + "\n"
        myString += "\t MCS: " + str(self.mcs) + "\n"
        myString += "\t Bw Idx: " + str(self.bwIdx) + "\n"
        myString += "\t Bandwidth: " + str(self.bandwidth) + " MHz\n"
        myString += "\t Subcarrier Num: " + str(self.scNum) + "\n"
        myString += "\t Rssi A [dB]: " + str(self.rssiA_db) + "\n"
        myString += "\t Rssi B [dB]: " + str(self.rssiB_db) + "\n"
        myString += "\t Timestamp: " + str(self.timestamp) + "\n"
        myString += "\t CSI matrix shape: " + str(self.csi.shape) + "\n"
        return myString


class WiFiCsiReceiver(object):
    """docstring for WiFiCsiReceiver"""
    def __init__(self, interfaceName):
        self.interfaceName = interfaceName
        self.phyName = self.get_device_phy_name(interfaceName)
        self.phyIdx = self.get_device_phy_id(interfaceName)
        self.fileBasePath = None
        self.iw = None
        # in Intel 9260
        filePath_Intel9260 = "/sys/kernel/debug/ieee80211/{}/iwlwifi/iwlmvm/csi_enabled".format(self.phyName)        
        if os.path.isfile(filePath_Intel9260):
            self.fileBasePath = "/sys/kernel/debug/ieee80211/{}/iwlwifi/iwlmvm/".format(self.phyName)
        else:
            print("No Intel card found!")

        # csi collection config
        self.csi_addresses = None
        self.csi_count = None
        self.csi_enabled = None
        self.csi_frame_types = None
        self.csi_interval = None
        self.csi_rate_n_flags_mask = None
        self.csi_rate_n_flags_val = None
        self.csi_timeout = None
        self.scalingEnabled = True

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

    def set_rx_antennas(self, rxChains):
        rxChains = rxChains.lower()
        mask = 0x0
        aMask = 0x1
        bMask = 0x2
        cMask = 0x4

        if "a" in rxChains:
            mask |= aMask
        if "b" in rxChains:
            mask |= bMask
        if "c" in rxChains:
            mask |= cMask

        mask = "0x{:01x}".format(mask)
        fn = self.fileBasePath + 'rx_chains_msk'
        if (os.path.isfile(fn)):
            print("Set RX antenna mask: ", mask)
            self._write_file(self.fileBasePath, mask)
        else:
            print("Setting RX chains not supported")

    def set_mac_address_filter(self, macAddress):
        if type(macAddress) == list:
            macAddress = ' '.join(macAddress)

        self.csi_addresses = macAddress
        fn = self.fileBasePath + "csi_addresses"
        macAddress = macAddress+"\n"  # add new line as intel expects it
        self._write_file(fn, macAddress)

    def set_interval(self, value):
        fn = self.fileBasePath + "csi_interval"
        value = str(value)+"\n"  # add new line as intel expects it
        self._write_file(fn, value)

    def _disable_scaling(self):
        self.scalingEnabled = False

    def _start_netlink_connection(self):
        ip = IPRoute()
        ifindex = ip.link_lookup(ifname=self.interfaceName)[0]
        ip.close()

        msg = nl80211cmd()
        msg['cmd'] = NL80211_NAMES['NL80211_CMD_VENDOR']
        msg['attrs'] = [['NL80211_ATTR_IFINDEX', ifindex],['NL80211_ATTR_VENDOR_ID', 0x001735],['NL80211_ATTR_VENDOR_SUBCMD', 0x24]]

        self.iw = IW()
        resp = self.iw.nlm_request(msg, msg_type=self.iw.prid, msg_flags=NLM_F_REQUEST | NLM_F_ACK)
        #print(resp)

    def start(self):
        fn = self.fileBasePath + "csi_enabled"
        msg = "1"+"\n"  # add new line as intel expects it
        self._write_file(fn, msg)
        self._start_netlink_connection()

    def stop(self):
        fn = self.fileBasePath + "csi_enabled"
        msg = "0"+"\n"  # add new line as intel expects it
        self._write_file(fn, msg)

    def receive(self):
        wiphyIdx = -1
        headerSize = 272
        csiEntry = None
        csiArray = None
        msg = self.iw.get()

        if len(msg) == 0:
            return None

        msg = msg[0]
        attrs = msg.get('attrs', None)

        if attrs is None:
            return None

        csiEntry = WifiCsiEntry()

        for attr in attrs:
            if attr[0] == 'NL80211_ATTR_WIPHY':
                wiphyIdx = attr[1]
                csiEntry.wiphyIdx = wiphyIdx

            if attr[0] == 'NL80211_ATTR_VENDOR_DATA':
                data = attr[1]
                data = data.replace(':','')
                data = bytearray.fromhex(data)

                header = np.frombuffer(data[0:DTYPE_CSI_HEADER_TLV.itemsize], dtype=DTYPE_CSI_HEADER_TLV)[0]       
                csiData = np.frombuffer(data[272:], dtype=DTYPE_CSI_DATA_TLV)

                # decode header
                csiMsg_size = header["csi_msg_size"]
                timestamp_1 = header["timestamp_1"]
                bwIdx = header["bw_idx"]
                streamNum = header["streamNum"]
                scNum = header["scNum"]
                rssi_1 = header["rssi_1"]
                rssi_2 = header["rssi_2"]
                srcMac = header["srcMac"]
                counter = header["counter"]
                timestamp_2 = header["timestamp_2"]
                mcs = header["mcs"]
                channelMask = header["channelMask"]
                timestamp_3 = header["timestamp_3"]

                # prepare header
                Nrx = 2
                if streamNum == 1:
                    Ntx = 1
                else:
                    Ntx = 2
                # prepare csi array
                csiArray = np.zeros(shape=(Ntx,Nrx,scNum), dtype=np.complex)

                csiEntry.counter = counter
                csiEntry.Ntx = Ntx
                csiEntry.Nrx = Nrx
                csiEntry.mcs = mcs
                csiEntry.scNum = scNum
                csiEntry.bwIdx = bwIdx
                if bwIdx == 1:
                    csiEntry.bandwidth = 20
                elif bwIdx == 2:
                    csiEntry.bandwidth = 40
                elif bwIdx == 3:
                    csiEntry.bandwidth = 80
                elif bwIdx == 4:
                    csiEntry.bandwidth = 160
                else:
                    csiEntry.bandwidth = -1

                # non HT bandwidth
                if scNum == 52:
                    csiEntry.bandwidth = 20

                srcMacStr = ':'.join([hex(x)[2:].zfill(2) for x in srcMac])
                csiEntry.srcMac = srcMacStr
                csiEntry.timestamp = timestamp_2

                csiEntry.rssiA_db = mcs
                csiEntry.rssiB_db = mcs

                # decode CSI
                Q = csiData[::2]
                I = csiData[1::2]
                csiDataIQ = I + 1j*Q

                ant1 = csiDataIQ[::2]
                ant2 = csiDataIQ[1::2]

                if self.scalingEnabled:
                    # power scaling
                    csiAbs = np.absolute(csiDataIQ)
                    ant1 = csiAbs[::2]
                    ant2 = csiAbs[1::2]

                    sumAnt1 = np.real(np.sum(ant1))
                    sumAnt2 = np.real(np.sum(ant2))

                    rssi_db_ant1 = -1.0*rssi_1
                    rssi_db_ant2 = -1.0*rssi_2

                    csiEntry.rssiA_db = rssi_db_ant1
                    csiEntry.rssiB_db = rssi_db_ant2

                    rssi_lin_ant1 = np.power(10, rssi_db_ant1/10)
                    rssi_lin_ant2 = np.power(10, rssi_db_ant2/10)

                    scaleAnt1 = rssi_lin_ant1 / sumAnt1;
                    scaleAnt2 = rssi_lin_ant2 / sumAnt2;

                    noise_db = -92
                    noise_db = np.float(noise_db)
                    thermal_noise_pwr  = np.power(10.0, noise_db/10);

                    quant_error_pwr = 0
                    #quant_error_pwr = scale * (Nrx * Ntx)
                    # Total noise and error power
                    total_noise_pwr = thermal_noise_pwr + quant_error_pwr;
                    #ant1 = ant1 * np.sqrt(scaleAnt1 / total_noise_pwr);
                    #ant2 = ant2 * np.sqrt(scaleAnt2 / total_noise_pwr);

                    if 1:
                        # RSSI
                        ant1 = ant1 * scaleAnt1
                        ant2 = ant2 * scaleAnt2

                    else:
                        # SNR
                        ant1 = ant1 * scaleAnt1/total_noise_pwr
                        ant2 = ant2 * scaleAnt2/total_noise_pwr


                    if Ntx == 2:
                        ant1 = ant1 * np.sqrt(2);
                        ant2 = ant2 * np.sqrt(2);

                    ant1 = csiDataIQ[::2] * scaleAnt1
                    ant2 = csiDataIQ[1::2] * scaleAnt2

                if Ntx == 1:
                    csiArray[0,0,:] = ant1
                    csiArray[0,1,:] = ant2

                if Ntx == 2:
                    csiArray[0,0,:] = ant1[::2]
                    csiArray[1,0,:] = ant1[1::2]
                    csiArray[0,1,:] = ant2[::2]
                    csiArray[1,1,:] = ant2[1::2]

                # permute subcarriers as pilots are always in the first positions
                if scNum == 52:
                    # take correct subcarriers
                    permutation = np.arange(4,52)
                    # insert pilots correctly
                    curPilotPositions = np.arange(4)
                    # -21, -7, 7, 21
                    correctpilotPositions = [5,18,30,43]
                    permutation = np.insert(permutation, correctpilotPositions, curPilotPositions)
                    # in-place modification of csiArray
                    csiArray[:] = csiArray[:,:, permutation]

                if scNum == 56:
                    # take correct subcarriers
                    permutation = np.arange(4,56)
                    # insert pilots correctly
                    curPilotPositions = np.arange(4)
                    # -21, -7, 7, 21
                    correctpilotPositions = [7,20,32,45]
                    permutation = np.insert(permutation, correctpilotPositions, curPilotPositions)
                    # in-place modification of csiArray
                    csiArray[:] = csiArray[:,:, permutation]

                if scNum == 114:
                    # take correct subcarriers
                    permutation = np.arange(6,114)
                    # insert pilots correctly
                    curPilotPositions = np.arange(6)
                    #-53, -25, -11, 11, 25, 53
                    correctpilotPositions = [5,32,45,63,76,103]
                    permutation = np.insert(permutation, correctpilotPositions, curPilotPositions)
                    # in-place modification of csiArray
                    csiArray[:] = csiArray[:,:, permutation]

                if scNum == 242:
                    pass

                if scNum == 484:
                    pass

        csiEntry.csi = csiArray
        return csiEntry