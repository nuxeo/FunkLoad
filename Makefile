# FunkLoad Makefile
# $Id: $
#
.PHONY: build pkg sdist egg install clean rpm doc

HTML_DOCS := README.html INSTALL.html CHANGES.html
CSS_FILE := src/data/funkload.css
RST2HTML := rst2html.py -t --stylesheet-path=$(CSS_FILE) --embed-stylesheet
TARGET := cvs.in.nuxeo.com:~/public_public_html/funkload/

# a for alpha, b for beta
PKGTAG := egg_info --tag-build=a --tag-svn-revision

build:
	python setup.py build

pkg: sdist egg

sdist:
	python setup.py $(PKGTAG) sdist

egg:
	python setup.py $(PKGTAG) bdist_egg


distrib: doc
	-scp dist/funkload-*.tar.gz $(TARGET)
	-scp dist/funkload-*.egg $(TARGET)
	scp ${HTML_DOCS} $(TARGET)

install:
	python setup.py install

doc: ${HTML_DOCS}

%.html: %.txt  $(CSS_FILE)
	${RST2HTML} $< $@

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST
	rm -f ${HTML_DOCS}
