# FunkLoad Makefile
# $Id: $
#
.PHONY: build pkg sdist egg install clean rpm doc

HTML_DOCS := README.html INSTALL.html CHANGES.html
CSS_FILE := src/data/funkload.css
RST2HTML := rst2html.py -t --stylesheet-path=$(CSS_FILE) --embed-stylesheet
TARGET := cvs.in.nuxeo.com:~/public_public_html/funkload/

# use TAG=a for alpha, b for beta, rc for release candidate
ifdef TAG
	PKGTAG := egg_info --tag-build=$(TAG) --tag-svn-revision
else
    PKGTAG :=
endif


build:
	python setup.py $(PKGTAG) build

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
	python setup.py $(PKGTAG) install

doc: ${HTML_DOCS}

%.html: %.txt  $(CSS_FILE)
	${RST2HTML} $< $@

clean:
	find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
	rm -rf ./build ./dist ./MANIFEST
	rm -f ${HTML_DOCS}
