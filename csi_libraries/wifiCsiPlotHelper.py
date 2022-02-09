import numpy as np
import matplotlib
import matplotlib.pyplot as plt

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2020 Piotr Gawlowicz"
__version__ = "1.0.0"
__email__ = "gawlowicz.p@gmail.com"


class WiFiCsiPlotHelper(object):
    """docstring for WiFiCsiPlotHelper"""
    def __init__(self):
        self._isAxesCreated = False
        self.Ntx = None
        self.Nrx = None
        self.bwId = -1

        # figure handlers
        self.fig = plt.figure()
        self.axs = []
        self.amplitudeLines = []
        self.phaseLines = []
        self.ampl_ylimMin = -110
        self.ampl_ylimMax = -30
        self.phase_ylimMin = -60
        self.phase_ylimMax = 60

    def set_amplitude_limits(self, minValue, maxValue):
        self.ampl_ylimMin = minValue
        self.ampl_ylimMax = maxValue

    def set_phase_limits(self, minValue, maxValue):
        self.phase_ylimMin = minValue
        self.phase_ylimMax = maxValue

    def plot(self, csiEntry):
            csiData = csiEntry.csi
            Ntx = csiEntry.Ntx
            Nrx = csiEntry.Nrx

            bwId = csiEntry.bwIdx
            # check if bandwidth was changed
            if (self.bwId > -1 and self.bwId != bwId):
                print("Bandwitdh changed -> need to reset figure!")
                if self._isAxesCreated:
                    self.fig.clf()
                    self._isAxesCreated = False
                self.Ntx = None
                self.Nrx = None
                self.axs = []
                self.amplitudeLines = []
                self.phaseLines = []

            if self._isAxesCreated == False:
                # always create 2x2
                Ntx = 2
                Nrx = 2
                self.Ntx = 2
                self.Nrx = 2
                self.bwId = csiEntry.bwIdx

                # create figure
                self._isAxesCreated = True
                #self.fig, self.axs = plt.subplots(2, 2)

                for i in range(0,4):
                    ax = self.fig.add_subplot(2,2,i+1)
                    self.axs.append(ax)

                # transp
                self.axsList = None
                ampl_ylimMin = self.ampl_ylimMin
                ampl_ylimMax = self.ampl_ylimMax
                phase_ylimMin = self.phase_ylimMin
                phase_ylimMax = self.phase_ylimMax

                # only to get CSI array shape
                tmpCsiData = np.real(csiData[0,0,:])
                tmpCsiData.fill(0)

                titles = ["Stream 1, Ant A","Stream 1, Ant B","Stream 2, Ant A","Stream 2, Ant B"]
                for idx in range(0,4):
                        ax = self.axs[idx]
                        ax.grid(True, linestyle='--')
                        ax.set_title(titles[idx])
                        ax.set_ylim(ampl_ylimMin,ampl_ylimMax)

                        ampl_line, = ax.plot(tmpCsiData, 'r-', label="Amplitude")
                        self.amplitudeLines.append(ampl_line)

                        phase_ax = ax.twinx()
                        phase_ax.set_ylim(phase_ylimMin,phase_ylimMax)
                        phase_line, = phase_ax.plot(tmpCsiData, 'b-', label="Phase")
                        self.phaseLines.append(phase_line)

                        # added labels
                        ax.set_xlabel("Subcarriers")
                        ax.set_ylabel("RSSI")
                        phase_ax.set_ylabel("Angle")
                        lines = [ampl_line,phase_line]
                        labels = [l.get_label() for l in lines]
                        ax.legend(lines, labels, loc='upper right')

                self.fig.show()

            else:
                idx = 0
                for t in range(0,Ntx):
                    for r in range(0,Nrx):
                        tmpCsi = csiData[t,r,:]
                        amplitude = np.absolute(tmpCsi)
                        amplitude_db = 10*np.log10(amplitude)
                        phase = np.angle(tmpCsi)
                        phase = np.unwrap(phase)

                        ampl_line = self.amplitudeLines[idx]
                        ampl_line.set_ydata(amplitude_db)
                        phase_line = self.phaseLines[idx]
                        phase_line.set_ydata(phase)

                        idx += 1

                # if no data then set zeros
                for i in range(idx,4):
                    tmpCsiData = np.real(csiData[0,0,:])
                    tmpCsiData.fill(0)
                    ampl_line = self.amplitudeLines[i]
                    ampl_line.set_ydata(tmpCsiData)
                    phase_line = self.phaseLines[i]
                    phase_line.set_ydata(tmpCsiData)

                self.fig.canvas.draw()
                self.fig.canvas.flush_events()