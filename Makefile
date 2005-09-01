.PHONY: build pkg install clean rpm

build:
	python setup.py build

pkg:
	python setup.py sdist

rpm:
	python setup.py bdist_rpm

distrib:
	scp dist/funkload-*.tar.gz cvs.in.nuxeo.com:~/public_public_html/funkload/

install:
	python setup.py install --install-scripts=/usr/local/bin --install-data=/usr/local

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST
