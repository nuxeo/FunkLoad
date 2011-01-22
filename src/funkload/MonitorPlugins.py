import pkg_resources, re
ENTRYPOINT = 'funkload.plugins.monitor'

class MonitorPlugins():
    MONITORS = {}
    def __init__(self, conf=None):
        self.conf = conf

    def registerPlugins(self):
        for entrypoint in pkg_resources.iter_entry_points(ENTRYPOINT):
            p=entrypoint.load()(self.conf)
            self.MONITORS[p.name]=p
        print self.MONITORS

class MonitorPlugin(object):
    name = None
    def __init__(self, conf=None):
        if self.name == None:
            self.name=self.__class__.__name__
        self._conf = conf
