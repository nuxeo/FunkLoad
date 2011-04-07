from funkload.MonitorPlugins import MonitorPlugin, Plot
GNUPLOTSTYLE='lines lw 3'
DATALABEL1='EXAMPLE1'
DATATITLE1='example1'
PLOTTITLE1='Example plot1 - single data'

PLOTTITLE2='Example plot2 - multiple data'
DATALABEL21='EXAMPLE21'
DATATITLE21='example21'
DATALABEL22='EXAMPLE22'
DATATITLE22='example22'

class Example(MonitorPlugin):
    plots=[Plot({DATALABEL1: [GNUPLOTSTYLE, DATATITLE1]}, title=PLOTTITLE1),
           Plot({
                  DATALABEL21: [GNUPLOTSTYLE, DATATITLE21],
                  DATALABEL22: [GNUPLOTSTYLE, DATATITLE22]
                }, title=PLOTTITLE2)]
    def getStat(self):
        return {DATALABEL1: 70, DATALABEL21: 80, DATALABEL22: 90}

    def parseStats(self, stats):
        if not (hasattr(stats[0], DATALABEL1) and \
                hasattr(stats[0], DATALABEL21) and \
                hasattr(stats[0], DATALABEL22)):
            return None
        data1=[int(getattr(stats[0], DATALABEL1)) for x in stats]
        data21=[int(getattr(stats[0], DATALABEL21)) for x in stats]
        data22=[int(getattr(stats[0], DATALABEL22)) for x in stats]

        return {DATALABEL1: data1, DATALABEL21: data21, DATALABEL22: data22}
