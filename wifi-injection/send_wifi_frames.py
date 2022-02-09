
#!/usr/bin/env python3

import argparse
from csiBox.wifiTransmitter import WiFiTransmitter

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set parameters')
    parser.add_argument('--interface',
                        type=str,
                        default="mon0",
                        help='Select WiFi monitor interface')
    parser.add_argument('--txants',
                        type=str,
                        default="A",
                        help='Which TX chains should be activated, A, B or AB')
    parser.add_argument('--mcs',
                        type=int,
                        default=0,
                        help='MCS index')
    parser.add_argument('--bw',
                        type=int,
                        default=20,
                        help='Channel Bandwidth')
    parser.add_argument('--size',
                        type=int,
                        default=100,
                        help='Frame size')
    parser.add_argument('--count',
                        type=int,
                        default=1,
                        help='Number of frames to send')
    parser.add_argument('--interval',
                        type=float,
                        default=1,
                        help='Frame sending interval [s]')

    args = parser.parse_args()
    interface = str(args.interface)
    txants = args.txants
    mcs = args.mcs
    bandwidth = args.bw
    frameSize = args.size
    count = args.count
    interval = args.interval

    transmitter = WiFiTransmitter(interface)
    transmitter.set_tx_antennas(txants)
    transmitter.set_mcs(mcs)
    transmitter.set_bandwidth(bandwidth)

    dstMac = "00:16:ea:12:34:56"
    srcMac = "00:16:ea:12:34:56"
    bssid = "ff:ff:ff:ff:ff:ff"
    transmitter.set_mac_addresses(dstMac, srcMac, bssid)

    transmitter.send(frameSize=frameSize, interval=interval, count=count)
