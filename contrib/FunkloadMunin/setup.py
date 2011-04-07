from setuptools import setup
PLUGINNAME="FunkloadMunin"
PACKAGE=PLUGINNAME

setup(
    name=PLUGINNAME,
    description="Funkload monitor plugin for Munin plugins.",
    author="Krzysztof A. Adamski",
    author_email="k@japko.eu",
    version="0.1",
    packages=[PACKAGE],
    entry_points= {
        'funkload.plugins.monitor' : [
            '%s = %s.MonitorPluginMunin:MonitorMunin' % (PLUGINNAME, PACKAGE)
        ]
    }
)
