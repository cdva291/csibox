import os
import pyric             # pyric errors
import pyric.pyw as pyw  # iw functionality


__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


# create helper class to match the PyRIC API
class MyCard(tuple):
    """
    A wireless network interface controller - Wrapper around a tuple
    t = (physical index,device name, interface index)
    Exposes the following properties: (callable by '.'):
        phy: physical index
        dev: device name
        idx: interface index (ifindex)
    """
    # noinspection PyInitNewSignature
    def __new__(cls, p, d, i):
        return super(MyCard, cls).__new__(cls, tuple((p, d, i)))
    def __repr__(self):
        return "Card(phy={0},dev={1},ifindex={2})".format(self.phy,self.dev,self.idx)
    @property
    def phy(self): return self[0]
    @property
    def dev(self): return self[1]
    @property
    def idx(self): return self[2]


class PhyInfo(object):
    """docstring for PhyInfo"""
    def __init__(self):
        super(PhyInfo, self).__init__()
        self.phyidx = None
        self.phyName = None
        self.type = None
        self.bands = []
        self.interfaces = []
        self.csiSupport = False

    def __str__(self):
        myString = "PhyIdx: {}".format(self.phyidx)
        myString += "\t PhyName: {}".format(self.phyName)
        myString += "\t Type: {}".format(self.type)
        bands = ",".join(self.bands)
        myString += "\t Bands: " + bands
        interfaces = []
        for iface in self.interfaces:
            interfaces.append(iface.name)
        interfaces = ",".join(interfaces)
        if self.csiSupport:
            myString += "\t CSI Support: True"
        else:
            myString += "\t CSI Support: False"
        myString += "\t Interfaces: " + interfaces
        return myString

class IfaceInfo(object):
    """docstring for IfaceInfo"""
    def __init__(self):
        super(IfaceInfo, self).__init__()
        self.phyIdx = None
        self.idx = None
        self.name = None
        self.type = None

def get_phy_info_list():
    phyInfoList = []
    if 0:
        for ifname in pyw.winterfaces():
            w0 = pyw.getcard(ifname)
            iinfo = pyw.ifinfo(w0)
            dinfo = pyw.devinfo(w0)
            pinfo = pyw.phyinfo(w0)
            #print(pinfo)
            #print(phy, pinfo['bands'].keys())

    for phy in pyw.phylist():
        # phy is a dict, take only name
        idx = phy[0]
        phy = phy[1]

        card = MyCard(idx, idx, idx)
        pinfo = pyw.phyinfo(card)
        bands = list(pinfo['bands'].keys())

        phyInfo = PhyInfo()
        phyInfo.phyidx = idx
        phyInfo.phyName = phy

        if '60GHz' in bands:
            phyInfo.type = "WiGig"
        else:
            phyInfo.type = "WiFi"

        phyInfo.bands = bands

        # check csi file for intel
        filePath_Intel9260 = "/sys/kernel/debug/ieee80211/{}/iwlwifi/iwlmvm/csi_enabled".format(phy)
        if os.path.isfile(filePath_Intel9260):
            phyInfo.csiSupport = True

        # check csi file for wigig
        filePath_wil6210 = "/sys/kernel/debug/ieee80211/{}/wil6210/tof_aoa".format(phy)
        if os.path.isfile(filePath_wil6210):
            phyInfo.csiSupport = True

        ifaces = pyw.ifaces(card)
        ifaceList = []
        for iface in ifaces:
            card = iface[0]
            infoObj = IfaceInfo()
            infoObj.phyIdx = card.phy
            infoObj.idx = card.idx
            infoObj.name = card.dev
            infoObj.type = iface[1]
            ifaceList.append(infoObj)

        phyInfo.interfaces = ifaceList

        phyInfoList.append(phyInfo)

    return phyInfoList