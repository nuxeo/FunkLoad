# FunkLoad Makefile
# $Id: $
#
.PHONY: build pkg sdist egg install clean rpm

TARGET := cvs.in.nuxeo.com:~/public_public_html/funkload

# use TAG=a for alpha, b for beta, rc for release candidate
ifdef TAG
	PKGTAG := egg_info --tag-build=$(TAG) --tag-svn-revision
else
    PKGTAG :=
endif


build:
	python setup.py $(PKGTAG) build

test:
	python setup.py test

pkg: sdist egg

sdist:
	python setup.py $(PKGTAG) sdist

egg:
	python setup.py $(PKGTAG) bdist_egg
	-python2.4 setup.py $(PKGTAG) bdist_egg


distrib:
	-scp dist/funkload-*.tar.gz $(TARGET)/snapshots
	-scp dist/funkload-*.egg $(TARGET)/snapshots

install:
	python setup.py $(PKGTAG) install

register:
	python setup.py register sdist bdist_egg upload --sign
	-python2.4 setup.py register bdist_egg upload --sign


uninstall:
	-easy_install -m funkload
	-rm -rf /usr/lib/python2.3/site-packages/funkload*
	-rm -rf /usr/local/funkload/
	-rm -f /usr/local/bin/fl-*
	-rm -f /usr/bin/fl-*

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST ./funkload.egg-info
