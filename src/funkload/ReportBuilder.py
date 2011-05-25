# (C) Copyright 2005-2011 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
# Contributors:
#   Krzysztof A. Adamski
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""Create an ReST or HTML report with charts from a FunkLoad bench xml result.

Producing html and png chart require python-docutils and gnuplot

$Id: ReportBuilder.py 24737 2005-08-31 09:00:16Z bdelbosc $
"""

USAGE = """%prog [options] xmlfile [xmlfile...]

or

  %prog --diff REPORT_PATH1 REPORT_PATH2

%prog analyze a FunkLoad bench xml result file and output a report.
If there are more than one file the xml results are merged.

See http://funkload.nuxeo.org/ for more information.

Examples
========
  %prog funkload.xml
                        ReST rendering into stdout.
  %prog --html -o /tmp funkload.xml
                        Build an HTML report in /tmp
  %prog --html node1.xml node2.xml node3.xml
                        Build an HTML report merging test results from 3 nodes.
  %prog --diff /path/to/report-reference /path/to/report-challenger
                        Build a differential report to compare 2 bench reports,
                        requires gnuplot.
  %prog --trend /path/to/report-dir1 /path/to/report-1 ... /path/to/report-n
                        Build a trend report using multiple reports.
  %prog -h
                        More options.
"""
try:
    import psyco
    psyco.full()
except ImportError:
    pass
import os
import xml.parsers.expat
from optparse import OptionParser, TitledHelpFormatter
from tempfile import NamedTemporaryFile

from ReportStats import AllResponseStat, PageStat, ResponseStat, TestStat
from ReportStats import MonitorStat, ErrorStat
from ReportRenderRst import RenderRst
from ReportRenderHtml import RenderHtml
from ReportRenderDiff import RenderDiff
from ReportRenderTrend import RenderTrend
from MergeResultFiles import MergeResultFiles
from utils import trace, get_version


# ------------------------------------------------------------
# Xml parser
#
class FunkLoadXmlParser:
    """Parse a funkload xml results."""
    def __init__(self, apdex_t):
        """Init setup expat handlers."""
        self.apdex_t = apdex_t
        parser = xml.parsers.expat.ParserCreate()
        parser.CharacterDataHandler = self.handleCharacterData
        parser.StartElementHandler = self.handleStartElement
        parser.EndElementHandler = self.handleEndElement
        parser.StartCdataSectionHandler = self.handleStartCdataSection
        parser.EndCdataSectionHandler = self.handleEndCdataSection
        self.parser = parser
        self.current_element = [{'name': 'root'}]
        self.is_recording_cdata = False
        self.current_cdata = ''

        self.cycles = None
        self.cycle_duration = 0
        self.stats = {}                 # cycle stats
        self.monitor = {}               # monitoring stats
        self.monitorconfig = {}         # monitoring config
        self.config = {}
        self.error = {}

    def parse(self, xml_file):
        """Do the parsing."""
        try:
            self.parser.ParseFile(file(xml_file))
        except xml.parsers.expat.ExpatError, msg:
            if (self.current_element[-1]['name'] == 'funkload'
                and str(msg).startswith('no element found')):
                print "Missing </funkload> tag."
            else:
                print 'Error: invalid xml bench result file'
                if len(self.current_element) <= 1 or (
                    self.current_element[1]['name'] != 'funkload'):
                    print """Note that you can generate a report only for a
                    bench result done with fl-run-bench (and not on a test
                    resu1lt done with fl-run-test)."""
                else:
                    print """You may need to remove non ascii characters which
                    come from error pages caught during the bench test. iconv
                    or recode may help you."""
                print 'Xml parser element stack: %s' % [
                    x['name'] for x in self.current_element]
                raise

    def handleStartElement(self, name, attrs):
        """Called by expat parser on start element."""
        if name == 'funkload':
            self.config['version'] = attrs['version']
            self.config['time'] = attrs['time']
        elif name == 'config':
            self.config[attrs['key']] = attrs['value']
            if attrs['key'] == 'duration':
                self.cycle_duration = attrs['value']
        elif name == 'header':
            # save header as extra response attribute
            headers = self.current_element[-2]['attrs'].setdefault(
                'headers', {})
            headers[str(attrs['name'])] = str(attrs['value'])
        self.current_element.append({'name': name, 'attrs': attrs})

    def handleEndElement(self, name):
        """Processing element."""
        element = self.current_element.pop()
        attrs = element['attrs']
        if name == 'testResult':
            cycle = attrs['cycle']
            stats = self.stats.setdefault(cycle, {'response_step': {}})
            stat = stats.setdefault(
                'test', TestStat(cycle, self.cycle_duration,
                                 attrs['cvus']))
            stat.add(attrs['result'], attrs['pages'], attrs.get('xmlrpc', 0),
                     attrs['redirects'], attrs['images'], attrs['links'],
                     attrs['connection_duration'], attrs.get('traceback'))
            stats['test'] = stat
        elif name == 'response':
            cycle = attrs['cycle']
            stats = self.stats.setdefault(cycle, {'response_step':{}})
            stat = stats.setdefault(
                'response', AllResponseStat(cycle, self.cycle_duration,
                                            attrs['cvus'], self.apdex_t))
            stat.add(attrs['time'], attrs['result'], attrs['duration'])
            stats['response'] = stat

            stat = stats.setdefault(
                'page', PageStat(cycle, self.cycle_duration, attrs['cvus'], 
                                 self.apdex_t))
            stat.add(attrs['thread'], attrs['step'], attrs['time'],
                     attrs['result'], attrs['duration'], attrs['type'])
            stats['page'] = stat

            step = '%s.%s' % (attrs['step'], attrs['number'])
            stat = stats['response_step'].setdefault(
                step, ResponseStat(attrs['step'], attrs['number'],
                                   attrs['cvus'], self.apdex_t))
            stat.add(attrs['type'], attrs['result'], attrs['url'],
                     attrs['duration'], attrs.get('description'))
            stats['response_step'][step] = stat
            if attrs['result'] != 'Successful':
                result = str(attrs['result'])
                stats = self.error.setdefault(result, [])
                stats.append(ErrorStat(
                    attrs['cycle'], attrs['step'], attrs['number'],
                    attrs.get('code'), attrs.get('headers'),
                    attrs.get('body'), attrs.get('traceback')))
        elif name == 'monitor':
            host = attrs.get('host')
            stats = self.monitor.setdefault(host, [])
            stats.append(MonitorStat(attrs))
        elif name =='monitorconfig':
            host = attrs.get('host')
            config = self.monitorconfig.setdefault(host, {})
            config[attrs.get('key')]=attrs.get('value')


    def handleStartCdataSection(self):
        """Start recording cdata."""
        self.is_recording_cdata = True
        self.current_cdata = ''

    def handleEndCdataSection(self):
        """Save CDATA content into the parent element."""
        self.is_recording_cdata = False
        # assume CDATA is encapsulate in a container element
        name = self.current_element[-1]['name']
        self.current_element[-2]['attrs'][name] = self.current_cdata
        self.current_cdata = ''

    def handleCharacterData(self, data):
        """Extract cdata."""
        if self.is_recording_cdata:
            self.current_cdata += data



# ------------------------------------------------------------
# main
#
def main():
    """ReportBuilder main."""
    parser = OptionParser(USAGE, formatter=TitledHelpFormatter(),
                          version="FunkLoad %s" % get_version())
    parser.add_option("-H", "--html", action="store_true", default=False,
                      dest="html", help="Produce an html report.")
    parser.add_option("--org", action="store_true", default=False,
                      dest="org", help="Org-mode report.")
    parser.add_option("-P", "--with-percentiles", action="store_true",
                      default=True, dest="with_percentiles",
                      help=("Include percentiles in tables, use 10%, 50% and"
                            " 90% for charts, default option."))
    parser.add_option("--no-percentiles", action="store_false",
                      dest="with_percentiles",
                      help=("No percentiles in tables display min, "
                            "avg and max in charts."))
    cur_path = os.path.abspath(os.path.curdir)
    parser.add_option("-d", "--diff", action="store_true",
                      default=False, dest="diffreport",
                      help=("Create differential report."))
    parser.add_option("-t", "--trend", action="store_true",
                      default=False, dest="trendreport",
                      help=("Build a trend reprot."))
    parser.add_option("-o", "--output-directory", type="string",
                      dest="output_dir",
                      help="Parent directory to store reports, the directory"
                      "name of the report will be generated automatically.",
                      default=cur_path)
    parser.add_option("-r", "--report-directory", type="string",
                      dest="report_dir",
                      help="Directory name to store the report.",
                      default=None)
    parser.add_option("-T", "--apdex-T", type="float",
                      dest="apdex_t",
                      help="Apdex T constant in second, default is set to 1.5s. "
                      "Visit http://www.apdex.org/ for more information.",
                      default=1.5)

    options, args = parser.parse_args()
    if options.diffreport:
        if len(args) != 2:
            parser.error("incorrect number of arguments")
        trace("Creating diff report ... ")
        output_dir = options.output_dir
        html_path = RenderDiff(args[0], args[1], options)
        trace("done: \n")
        trace("%s\n" % html_path)
    elif options.trendreport:
        if len(args) < 2:
            parser.error("incorrect number of arguments")
        trace("Creating trend report ... ")
        output_dir = options.output_dir
        html_path = RenderTrend(args, options)
        trace("done: \n")
        trace("%s\n" % html_path)
    else:
        if len(args) < 1:
            parser.error("incorrect number of arguments")
        if len(args) > 1:
            trace("Merging results files: ")
            f = NamedTemporaryFile(prefix='fl-mrg-', suffix='.xml')
            tmp_file = f.name
            f.close()
            MergeResultFiles(args, tmp_file)
            trace("Results merged in tmp file: %s\n" % os.path.abspath(tmp_file))
            args = [tmp_file]
        options.xml_file = args[0]
        xml_parser = FunkLoadXmlParser(options.apdex_t)
        xml_parser.parse(options.xml_file)
        if options.html:
            trace("Creating html report: ...")
            html_path = RenderHtml(xml_parser.config, xml_parser.stats,
                                   xml_parser.error, xml_parser.monitor,
                                   xml_parser.monitorconfig, options)()
            trace("done: \n")
            trace(html_path + "\n")
        elif options.org:
            from ReportRenderOrg import RenderOrg
            print unicode(RenderOrg(xml_parser.config, xml_parser.stats,
                                xml_parser.error, xml_parser.monitor,
                                xml_parser.monitorconfig, options)).encode("utf-8")
        else:
            print unicode(RenderRst(xml_parser.config, xml_parser.stats,
                                xml_parser.error, xml_parser.monitor,
                                xml_parser.monitorconfig, options)).encode("utf-8")


if __name__ == '__main__':
    main()
