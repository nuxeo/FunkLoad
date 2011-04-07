import shlex, re
from subprocess import *
from funkload.MonitorPlugins import MonitorPlugin, Plot

""" 
NOTES:
 - all values are converted to float
 - charts unit will be set to the unit of first label returned by nagios plugin
 - nagios plugin name can not contain characters that are invalid for xml attribute name
 - nagios plugins should return data immediately otherwise you may have problems (long running plugins)
 - nagios plugins return codes are ignored

in monitor.conf:
[plugins.monitornagios]
command1 = check_load;/usr/lib/nagios/plugins/check_load -w 5.0,4.0,3.0 -c 10.0,6.0,4.0
command2 = check_ping;/usr/lib/nagios/plugins/check_ping -H localhost -w 10,10% -c 10,10% -p 1
commandN = command_name;full_path [args]
"""

class MonitorNagios(MonitorPlugin):
    def __init__(self, conf=None):
        super(MonitorNagios, self).__init__(conf)
        if conf==None or not conf.has_section('plugins.monitornagios'):
            return

        self.commands={}
        for opt in conf.options('plugins.monitornagios'):
            if re.match(r'^command\d+$', opt):
                config=conf.get('plugins.monitornagios', opt).split(";")
                self.commands[config[0]]=config[1]

        for cmd in self.commands.keys():
            data=self._parsePerf(cmd, self.commands[cmd])
            p={}
            for d in data:
                p[d[1]]=['lines lw 2', d[0]]
            if len(p)!=0:
                self.plots.append(Plot(p, unit=data[0][3], title=cmd))

    def _nameResult(self, cmd, label):
        return "%s_%s_%s" % (self.name, cmd, label)

    def _parsePerf(self, name, cmd):
        output = Popen(shlex.split(cmd), stdout=PIPE).communicate()[0]
        perfs=output.split('|')[-1]
        data=re.findall(r'([^=]+=[^;]+);\S+\s?', perfs)
        ret=[]
        i=0
        for d in data:
            groups=re.match(r"'?([^']+)'?=([\d\.\,]+)(.+)?$", d).groups("")
            ret.append((groups[0], self._nameResult(name, i), groups[1], groups[2]))
            i+=1
        return ret

    def getStat(self):
        ret={}
        for cmd in self.commands.keys():
            data=self._parsePerf(cmd, self.commands[cmd])
            for d in data:
                ret[d[1]]=d[2]
        return ret

    def parseStats(self, stats):
        if len(self.plots)==0:
            return None
        for plot in self.plots:
            for p in plot.plots.keys():
                if not (hasattr(stats[0], p)):
                   return None
        ret={}
        for plot in self.plots:
            for p in plot.plots.keys():
                ret[p]=[float(getattr(x, p)) for x in stats]

        return ret

