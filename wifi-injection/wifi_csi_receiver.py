
#!/usr/bin/env python3

import argparse
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from csiBox import WiFiCsiReceiver
from csiBox import WiFiCsiPlotHelper


__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set parameters')
    parser.add_argument('--interface',
                        type=str,
                        default="wlp60s0",
                        help='Select WiFi monitor interface')
    parser.add_argument('--interval',
                        type=float,
                        default=0,
                        help='CSI message interval [us]')
    parser.add_argument("-p", "--plot",help="Open real-time plot", action="store_true")

    args = parser.parse_args()
    interface = str(args.interface)
    interval = args.interval
    plotCsi = args.plot

    # plot CSI
    _isFigureCreated = False
    amplitudeLine = None
    phaseLine = None
    scNum = 0

    # plot heatmap
    plotCsiHeatmap = False
    csiNum = 500
    idx = 0
    csiBuffer = None

    # configure CSI receiver
    srcMacAddresses = ["00:16:ea:12:34:56","d8:3b:bf:69:a2:85"]
    csiReceiver = WiFiCsiReceiver(interface)
    csiReceiver.set_mac_address_filter(srcMacAddresses)
    csiReceiver.set_interval(interval)  # deliver CSI no often than X us
    csiReceiver.start()

    try:
        while True:
            csiEntry = csiReceiver.receive()
            print(csiEntry)

            # plot CSI data for channel between Tx A and Rx A
            if plotCsi:
                # save scNumer and use it for filtering
                if scNum == 0:
                    scNum = csiEntry.scNum

                if scNum != csiEntry.scNum:
                    continue

                # get CSI data
                csiData = csiEntry.csi
                csiAntA = csiData[0,0,:]
                amplitude = np.absolute(csiAntA)
                amplitude_db = 10*np.log10(amplitude)
                phase = np.angle(csiAntA)
                phase = np.unwrap(phase)

                if _isFigureCreated == False:
                    print("Create CSI figure")
                    _isFigureCreated = True
                    # create figure for CSI from one channel
                    fig, ax = plt.subplots(1, 1)
                    ylimMin = -110
                    ylimMax = -20
                    ax.grid(True, linestyle='--')
                    ax.set_title("Tx A -> Rx A")
                    ax.set_ylim(ylimMin,ylimMax)
                    amplitudeLine, = ax.plot(amplitude_db, 'r-', label="Amplitude")

                    # create second axis in the same figure
                    ylimMin = -60
                    ylimMax = 10
                    p_ax = ax.twinx()
                    p_ax.set_ylim(ylimMin,ylimMax)
                    phaseLine, = p_ax.plot(phase, 'b-', label="Phase")

                    # added labels
                    ax.set_xlabel("Subcarriers")
                    ax.set_ylabel("RSSI")
                    p_ax.set_ylabel("Angle")
                    lines = [amplitudeLine,phaseLine]
                    labels = [l.get_label() for l in lines]
                    ax.legend(lines, labels, loc=0)

                    fig.show()

                else:
                    # update figure
                    print("Update CSI figure")
                    amplitudeLine.set_ydata(amplitude_db)
                    phaseLine.set_ydata(phase)
                    fig.canvas.draw()
                    fig.canvas.flush_events()

           # plot heatmap
            if plotCsiHeatmap:
                scNum = csiEntry.scNum
                csiData = csiEntry.csi
                csiAntA = csiData[0,0,:]
                amplitude = np.absolute(csiAntA)
                amplitude_db = 10*np.log10(amplitude)

                # create buffer with proper number of subcarriers
                if csiBuffer is None:
                    csiBuffer = np.zeros(shape=(csiNum, scNum))

                # collect CSI to buffer
                csiBuffer[idx,:] = amplitude_db
                idx+=1

                # check plot condition (i.e. full buffer)
                if idx == csiNum:
                    print("Plot heat map and exit")
                    plt.imshow(csiBuffer,vmin=csiBuffer.min().min(),vmax=csiBuffer.max().max(), aspect="auto", cmap='viridis', interpolation='nearest')
                    plt.colorbar()
                    plt.show()
                    csiReceiver.stop()
                    exit()

    except KeyboardInterrupt:
        print("Ctrl+C -> Exit")
        csiReceiver.stop()