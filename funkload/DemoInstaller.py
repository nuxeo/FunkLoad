"""Extract the demo from the funkload egg into the current path."""

import os
from shutil import copytree
from pkg_resources import resource_filename, cleanup_resources

def main():
    """main."""
    demo_path = 'funkload-demo'
    print "Extract FunkLoad examples into ./%s : ... " % demo_path,
    cache_path = resource_filename('funkload', 'demo')
    demo_path = os.path.join(os.path.abspath(os.path.curdir), demo_path)
    copytree(cache_path, demo_path)
    cleanup_resources()
    print "done."


if __name__ == '__main__':
    main()
