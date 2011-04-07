from setuptools import setup
PLUGINNAME="FunkloadNagios"
PACKAGE=PLUGINNAME

setup(
    name=PLUGINNAME,
    description="Funkload monitor plugin for Nagios plugins performance data.",
    author="Krzysztof A. Adamski",
    author_email="k@japko.eu",
    version="0.1",
    packages=[PACKAGE],
    entry_points= {
        'funkload.plugins.monitor' : [
            '%s = %s.MonitorPluginNagios:MonitorNagios' % (PLUGINNAME, PACKAGE)
        ]
    }
)
