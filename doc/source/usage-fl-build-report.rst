Report builder ``fl-build-report`` usage
=========================================

fl-build-report [options] xmlfile [xmlfile...]

or

fl-build-report --diff REPORT_PATH1 REPORT_PATH2

fl-build-report analyze a FunkLoad bench xml result file and output a report.
If there are more than one file the xml results are merged.

See http://funkload.nuxeo.org/ for more information.

Examples
---------
  fl-build-report funkload.xml
                        ReST rendering into stdout.
  fl-build-report --html -o /tmp funkload.xml
                        Build an HTML report in /tmp
  fl-build-report --html node1.xml node2.xml node3.xml
                        Build an HTML report merging test result from 3 nodes.
  fl-build-report --diff /tmp/test_reader-20080101 /tmp/test_reader-20080102
                        Build a differential report to compare 2 bench reports,
                        requires gnuplot.
  fl-build-report -h
                        More options.


Options
---------
--version               show program's version number and exit
--help, -h              show this help message and exit
--html, -H              Produce an html report.
--with-percentiles, -P  Include percentiles in tables, use 10%, 50% and 90%
                        for charts, default option.
--no-percentiles        No percentiles in tables display min, avg and max in
                        charts (gdchart only).
--diff, -d              Create differential report.
--output-directory=OUTPUT_DIR, -o OUTPUT_DIR
                        Parent directory to store reports, the directoryname
                        of the report will be generated automatically.
--report-directory=REPORT_DIR, -r REPORT_DIR
                        Directory name to store the report.
--apdex-T=APDEX_T, -T APDEX_T
                        Apdex T constant in second, default is set to 1.5s.
                        Visit http://www.apdex.org/ for more information.
