# FunkLoad doc Makefile
# $Id: $
# to build api documentation you need epydoc (apt-get install python-epydoc)
#
.PHONY: doc epydoc clean

doc: epydoc

epydoc:
	epydoc --name FunkLoad -u http://funkload.nuxeo.org/ --html --output .  ../funkload/

clean:
	-rm -rf ./private ./public ./index.html ./epydoc.css
	-@find . "(" -name "*~" -or  -name ".#*" -or  -name "#*#" -or -name "*.pyc" ")" -print0 | xargs -0 rm -f
