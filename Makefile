.PHONY: build pkg install clean rpm doc

# In order to generate HTML docs, you will need to install
# Docutils (http://docutils.sourceforge.net/).
# For example on a Debian system:
# $ sudo apt-get install python-docutils
HTML_DOCS := README.html INSTALL.html CHANGES.html
CSS_FILE := data/funkload.css

RST2HTML := rst2html -t --stylesheet-path=$(CSS_FILE) --embed-stylesheet

build:
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
