.PHONY: build pkg install clean rpm doc

HTML_DOCS := README.html INSTALL.html CHANGES.html
CSS_FILE := src/data/funkload.css

RST2HTML := rst2html.py -t --stylesheet-path=$(CSS_FILE) --embed-stylesheet

build: build_src egg

build_src:
	python setup.py build

pkg:
	python setup.py sdist

egg:
	python setup.py bdist_egg

rpm:
	python setup.py bdist_rpm

distrib: doc
	-scp dist/funkload-*.tar.gz cvs.in.nuxeo.com:~/public_public_html/funkload/
	scp ${HTML_DOCS} cvs.in.nuxeo.com:~/public_public_html/funkload/

install:
	python setup.py install --install-scripts=/usr/local/bin --install-data=/usr/local

doc: ${HTML_DOCS}

%.html: %.txt  $(CSS_FILE)
	${RST2HTML} $< $@

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST
	rm -f ${HTML_DOCS}
