import os
import matplotlib
from scapy.all import *  # this import also some graphical libs, that cause error when there is no X1$


__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


RATE_MCS_ANT_A_MSK = 0x04000
RATE_MCS_ANT_B_MSK = 0x08000
RATE_MCS_ANT_C_MSK = 0x10000
RATE_MCS_HT_MSK = 0x00100
RATE_MCS_HT40_MSK = 0x00800


class WiFiTransmitter(object):
    """docstring for WiFiTransmitter"""
    def __init__(self, interfaceName):
        super(WiFiTransmitter).__init__()
        self.interfaceName = interfaceName
        self.phyName = None
        self.monitor_tx_rate = 0x0
        self.txRateChanged = False
        self.txAntStr = "A"
        self.txAntNum = 1
        self.txAntMask = 0
        self.streamNum = 1
        self.mcs = 0
        self.bwMask = 0x0

        self.phyName = self.get_device_phy_name(interfaceName)
        self.filePath = None
        # in Intel 9260
        filePath_Intel9260 = "/sys/kernel/debug/ieee80211/{}/iwlwifi/iwlmvm/monitor_tx_rate".format(self.phyName)        
        filePath_Intel5300 = "/sys/kernel/debug/ieee80211/{}/iwlwifi/iwldvm/debug/monitor_tx_rate".format(self.phyName)        
        if os.path.isfile(filePath_Intel9260):
            print("Intel 9260 found")
            self.filePath = filePath_Intel9260
        elif os.path.isfile(filePath_Intel5300):
            print("Intel 5300 found")
            self.filePath = filePath_Intel5300
        else:
            print("No Intel card found!")

        # default rate
        # has to be 802.11n
        self.monitor_tx_rate |= RATE_MCS_HT_MSK
        self.monitor_tx_rate |= RATE_MCS_ANT_A_MSK
        self.monitor_tx_rate |= self.mcs

        # frame generation
        self.addr1 = "00:16:ea:12:34:56"
        self.addr2 = "00:16:ea:12:34:56"
        self.addr3 = "ff:ff:ff:ff:ff:ff"

    def _read_file(self, fn):
        fd = open(fn, 'r')
        dat = fd.read()
        fd.close()
        return dat

    def _write_file(self, fn, msg):
        f = open(fn, 'w')
        f.write(msg)
        f.close()
        return None

    def get_device_phy_name(self,iface):
        ''' get phy id for this interface '''
        fn = '/sys/class/net/{}/phy80211/name'.format(iface)
        if (os.path.isfile(fn)):
            phyid = self._read_file(fn).strip()
            return phyid
        return None

    def set_tx_antennas(self, txChains):
        self.txRateChanged = True

        self.txAntStr = txChains.upper()
        txChains = txChains.lower()

        mask = 0x0
        self.txAntNum = 0
        self.txAntMask = 0

        if "a" in txChains:
            mask |= RATE_MCS_ANT_A_MSK
            self.txAntNum += 1
        if "b" in txChains:
            mask |= RATE_MCS_ANT_B_MSK
            self.txAntNum += 1
        if "c" in txChains:
            mask |= RATE_MCS_ANT_C_MSK
            self.txAntNum += 1

        self.txAntMask |= mask

    def set_mcs(self, mcs):
        self.txRateChanged = True
        self.streamNum = 1
        if(mcs > 8):
            self.streamNum = 2

        if (mcs > 16):
            self.streamNum = 3

        if self.streamNum > self.txAntNum:
            print("Cannot use MCS: {} ({} streams) with {} antennas".format(mcs, self.streamNum, self.txAntNum))
            print("Set MCS to 0")
            mcs = 0

        self.mcs = mcs

    def set_bandwidth(self, bw):
        self.bwMask = RATE_MCS_HT_MSK
        if bw == 20:
            self.bwMask = RATE_MCS_HT_MSK

        if bw == 40:
            self.bwMask |= RATE_MCS_HT40_MSK

    def set_mac_addresses(self, addr1, addr2, addr3):
        self.addr1 = addr1
        self.addr2 = addr2
        self.addr3 = addr3

    def _check_configuration(self):
        return True

    def _configure_tx_rate(self):
        if(self.txRateChanged):
            if (not self._check_configuration()):
                print("Cannot send a frame with given configuration:")
                print("---MCS: {}".format(self.mcs))
                print("---StreamNum: {}".format(self.streamNum))
                print("---AntennaNum: {} ({})".format(self.txAntNum, self.txAntStr))
                print("Send with default config: {}".format(self.txAntNum))
                print("---MCS: 0")
                print("---StreamNum: 1")
                print("---AntennaNum: 1 (A)")
                return

            self.monitor_tx_rate = 0x0
            self.monitor_tx_rate |= self.bwMask
            self.monitor_tx_rate |= self.txAntMask
            self.monitor_tx_rate |= self.mcs

        mask = "0x{:05x}".format(self.monitor_tx_rate)
        print("Set TX mask: ", mask)
        self._write_file(self.filePath, mask)

    def send(self, frameSize=100, interval=1, count=1):
        self._configure_tx_rate()

        rt = RadioTap()
        dot11 = Dot11(addr1=self.addr1,
                      addr2=self.addr2,
                      addr3=self.addr3)

        DOT11_SUBTYPE_QOS_DATA = 0x28
        ds=0x01
        dot11 = Dot11(type="Data", subtype=DOT11_SUBTYPE_QOS_DATA, addr1=self.addr1, addr2=self.addr2, addr3=self.addr3, SC=0x3060, FCfield=ds)
        payload = Raw(RandString(size=frameSize))
        frame = rt / dot11 / payload

        sendp(frame, iface="mon0", inter=interval, count=count)