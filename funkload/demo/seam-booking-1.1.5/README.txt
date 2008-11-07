===============================
FunkLoad demo/seam-bookin-1.1.5
===============================
$Id$

Simple test of the Seam Booking application that comes with the JBoss Seam
Framework 1.1.5

This script register a new user, search an hotel and book a room.

To install seam booking application refer to the
http://www.seamframework.org/, the script works with version 1.1.5 along
with a jboss 4.0.5.

Run test on a local instance:

  make

Run test on a remote instance:

  make URL=http://another.seam.booking:8080

Run test in debug mode viewing all queries::

  make debug

Run test and view each fetched page into a running firefox::

  make debug_firefox

Run a small bench and produce a report::

  make bench


When you have 2 reports you can generate a differential report:

  fl-build-report --diff path/to/report/reference path/to/report/challenger

More info on the http://funkload.nuxeo.org/ site.
