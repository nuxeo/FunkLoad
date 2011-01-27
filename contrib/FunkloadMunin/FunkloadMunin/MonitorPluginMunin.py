import shlex, re, os
from subprocess import *
from funkload.MonitorPlugins import MonitorPlugin, Plot

RE_ENTRY=r'[a-zA-Z_][a-zA-Z0-9_]+\.[a-zA-Z0-9_]+'

""" 
NOTES:
- watch out for plugins running for a long time
- no arguments can be passed to munin plugins (they should not need it anyway)
- munin plugins written as shell scripts may need MUNIN_LIBDIR env defined
- some munin plugins may need root priviledges
in monitor.conf:
[plugins.monitormunin]
command1 = /usr/share/munin/plugins/vmstat;MUNIN_LIBDIR=/usr/share/munin/
command2 = /etc/munin/plugins/if_eth0
commandN = plugin_full_path;ENV_VAR=VALUE ENV_VAR2=VALUE2
"""

class MonitorMunin(MonitorPlugin):
    def __init__(self, conf=None):
        super(MonitorMunin, self).__init__(conf)
        if conf==None or not conf.has_section('plugins.monitormunin'):
            return

        self.commands={}
        for opt in conf.options('plugins.monitormunin'):
            if re.match(r'^command\d+$', opt):
                config=conf.get('plugins.monitormunin', opt).split(";")
                if len(config)==1:
                    config=(config[0], "")
                self.commands[os.path.basename(config[0])]=(config[0], config[1])

        for cmd in self.commands.keys():
            data=self._getConfig(cmd, self.commands[cmd][0], self.commands[cmd][1])
            p={}
            negatives=[]
            counters=[]
            for d in data[1]:
                p[d[0]]=['lines lw 2', d[1]]
                if d[2]:
                    negatives.append(d[2])
                if d[3]:
                    counters.append(d[0])
            if len(p)==0:
                continue

            title=cmd
            if data[0]:
                title=re.sub(r'\$\{graph_period\}', 'second', data[0])

            self.plots.append(Plot(p, title=title, negatives=negatives, counters=counters))

    def _nameResult(self, cmd, label):
        return "%s_%s_%s" % (self.name, cmd, label)

    def _parseOutput(self, output):
        ret={}
        for line in output.split('\n'):
            splited=line.split(' ')
            if len(splited)>=2:
                ret[splited[0]]=" ".join(splited[1:])
        return ret

    def _parseEnv(self, env):
        environment=os.environ
        for entry in env.split(' '):
            splited=entry.split('=')
            if len(splited)>=2:
                environment[splited[0]]="=".join(splited[1:])
        return environment

    def _getConfig(self, name, cmd, env):
        output = Popen('%s config' % cmd, shell=True, stdout=PIPE, env=self._parseEnv(env)).communicate()[0]
        output_parsed=self._parseOutput(output)

        fields=[]
        for entry in output_parsed.keys():
            if re.match(RE_ENTRY, entry):
                field=entry.split('.')[0]
                if field not in fields:
                    fields.append(field)

        ret=[]
        for field in fields:
            label=""
            neg=False
            count=False
            data_name=self._nameResult(name, field)

            if output_parsed.has_key("%s.label"%field):
                label=output_parsed["%s.label"%field]
#            if output_parsed.has_key("%s.info"%field):
#                label=output_parsed["%s.info"%field]
            
            if output_parsed.has_key("%s.negative"%field):
                neg=self._nameResult(name, output_parsed["%s.negative"%field])

            if output_parsed.has_key("%s.type"%field):
                t=output_parsed["%s.type"%field]
                if t=='COUNTER' or t=='DERIVE':
                    count=True

            ret.append((data_name, label, neg, count))

        title=None
        if output_parsed.has_key('graph_vlabel'):
            title=output_parsed['graph_vlabel']
            
        return [title, ret]

    def _parseStat(self, name, cmd, env):
        output = Popen([cmd], shell=True, stdout=PIPE, env=self._parseEnv(env)).communicate()[0]
        ret={}
        for line in output.split('\n'):
            splited=line.split(' ')
            if len(splited)==2 and re.match(RE_ENTRY, splited[0]):
                data_name=self._nameResult(name, splited[0].split('.')[0])
                ret[data_name]=splited[1]

        return ret

    def getStat(self):
        ret={}
        for cmd in self.commands.keys():
            data=self._parseStat(cmd, self.commands[cmd][0], self.commands[cmd][1])
            for key in data.keys():
                ret[key]=data[key]
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
                if p in plot.counters:
                    parsed=[]
                    for i in range(1, len(stats)):
                        delta=float(getattr(stats[i], p))-float(getattr(stats[i-1], p))
                        time=float(stats[i].time)-float(stats[i-1].time)
                        parsed.append(delta/time)
                    ret[p]=parsed
                else:
                    ret[p]=[float(getattr(x, p)) for x in stats]

                if p in plot.negatives:
                    ret[p]=[x*-1 for x in ret[p]]
        return ret
