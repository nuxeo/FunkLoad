from setuptools import setup
PLUGINNAME="FunkloadExamplePlugin"
PACKAGE=PLUGINNAME

setup(
    name=PLUGINNAME,
    description="Funkload example monitor plugin.",
    author="Krzysztof A. Adamski",
    author_email="k@japko.eu",
    version="1.0",
    packages=[PACKAGE],
    entry_points= {
        'funkload.plugins.monitor' : [
            '%s = %s.example:Example' % (PLUGINNAME, PACKAGE)
        ]
    }
)
