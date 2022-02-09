#!/usr/bin/env python3
from csiBox import get_phy_info_list
import pyric             # pyric errors
import pyric.pyw as pyw  # iw functionality

print("Wireless devices:")
phyInfoList = get_phy_info_list()
for p in phyInfoList:
    print(p)

print("\nMAC addresses:")
for iface in pyw.winterfaces():
    card = pyw.getcard(iface)
    macAddress = pyw.macget(card)
    print(iface,"\t", macAddress)