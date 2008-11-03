# (C) Copyright 2008 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
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
"""Classes that render a differential report

$Id$
"""
import os
from shutil import copyfile
from tempfile import mkdtemp
from ReportRenderRst import rst_title
from ReportRenderHtmlBase import RenderHtmlBase
from ReportRenderHtmlGnuPlot import gnuplot

class RenderDiff(RenderHtmlBase):
    """ """
    report_dir1 = None
    report_dir2 = None
    header = None
    sep = ', '
    date_file = None
    output_dir = None

    def __init__(self, report_dir1, report_dir2, output_dir=None, css_file=None):
        self.report_dir1 = report_dir1
        self.report_dir2 = report_dir2
        self.output_dir = output_dir
        self.report_dir = output_dir
        self.css_file = css_file

    def prepareReportDirectory(self):
        """Create a folder to save the report."""
        # init output dir
        if self.output_dir is not None:
            output_dir = os.path.abspath(self.output_dir)
        else:
            # TODO: compute diff_b2_vs_b1
            output_dir = mkdtemp(prefix='fl-diff_')
        if not os.access(output_dir, os.W_OK):
            os.mkdir(output_dir, 0775)
        output_dir = os.path.abspath(output_dir)
        self.output_dir = output_dir
        self.report_dir = output_dir
        print "Using output dir: " + output_dir

    def createCharts(self):
        """Render stats."""
        self.createGnuplotData()
        self.createGnuplotScript()
        gnuplot(self.script_file)

    def createRstFile(self):
        """Create the ReST file."""
        rst_path = os.path.join(self.output_dir, 'index.rst')
        lines = []
        lines.append(rst_title("FunkLoad diff report: %s vs %s" % (self.report_dir2, self.report_dir1)))
        lines.append(" * Reference bench report **B1**: " + self.report_dir1 + "_")
        lines.append(" * Challenger bench report **B2**: " + self.report_dir2 + "_")
        lines.append("")
        # TODO: fix path compute relative path
        lines.append(".. _" + self.report_dir1 + ": " +
                     os.path.join("..", self.report_dir1, 'index.html'))
        lines.append(".. _" + self.report_dir2 + ": " +
                     os.path.join("..", self.report_dir2, 'index.html'))
        lines.append("")
        lines.append(rst_title("Requests", level=2))
        lines.append(" .. image:: rps_diff.png")
        lines.append(" .. image:: request.png")
        lines.append(rst_title("Pages", level=2))
        lines.append(" .. image:: spps_diff.png")
        lines.append("")
        f = open(rst_path, 'w')
        f.write('\n'.join(lines))
        f.close()
        self.rst_path = rst_path

    def copyXmlResult(self):
        pass

    def __repr__(self):
        return self.render()

    def extract_stat(self, tag, output_dir):
        lines = open(os.path.join(output_dir, "index.rst")).readlines()
        try:
            idx = lines.index("%s stats\n" % tag)
        except ValueError:
            print "ERROR tag %s not found in rst report %s" % (tag, output_dir)
            return []
        delim = 0
        ret =  []
        for line in lines[idx:]:
            if line.startswith(" ====="):
                delim += 1
                continue
            if delim == 1:
                self.header = line.strip().split()
            if delim < 2:
                continue
            if delim == 3:
                break
            ret.append([x.replace("%","") for x in line.strip().split()])
        return ret

    def createGnuplotData(self):
        """Render rst stat."""

        def output_stat(tag, rep):
            stat = self.extract_stat(tag, rep)
            text = []
            text.append('# ' + tag + " stat for: " + rep)
            text.append('# ' + ' '.join(self.header))
            for line in stat:
                text.append(' '.join(line))
            return '\n'.join(text)


        def output_stat_diff(tag, rep1, rep2):
            stat1 = self.extract_stat(tag, rep1)
            stat2 = self.extract_stat(tag, rep2)
            text = []
            text.append('# ' + tag + " stat for: " + rep1 + " and " + rep2)
            text.append('# ' + ' '.join(self.header) + ' ' + ' '.join([x+ "-2" for x in self.header]))
            for s1 in stat1:
                for s2 in stat2:
                    if s1[0] == s2[0]:
                        text.append(' '.join(s1) + ' ' + ' '.join(s2))
                        break
                if s1[0] != s2[0]:
                    text.append(' '.join(s1))
            return '\n'.join(text)

        rep1 = self.report_dir1
        rep2 = self.report_dir2

        data_file = os.path.join(self.output_dir, 'diffbench.dat')
        self.data_file = data_file
        f = open(data_file, 'w')
        f.write('# ' + rep1 + ' vs ' + rep2 + '\n')
        for tag, rep in (('Page', rep1), ('Page', rep2),
                         ('Request', rep1), ('Request', rep2)):
            f.write(output_stat(tag, rep) + '\n\n\n')
        f.write(output_stat_diff('Page', rep1, rep2) + '\n\n\n')
        f.write(output_stat_diff('Request', rep1, rep2))
        f.close()


    def createGnuplotScript(self):
        script_file = os.path.join(self.output_dir, 'script.gplot')
        print "Creating gnuplot %s" % script_file
        self.script_file = script_file
        f = open(script_file, 'w')
        rep1 = self.report_dir1
        rep2 = self.report_dir2
        f.write('# ' + rep1 + ' vs ' + rep2 + '\n')

        f.write('''# COMMON SETTINGS
set grid  back
set xlabel "Concurrent Users"
set boxwidth 0.9 relative
set style fill solid 1

# SPPS
set output "spps_diff.png"
set terminal png size 640,380
set title "Successful Pages Per Second"
set ylabel "SPPS"
plot "diffbench.dat" i 4 u 1:2:15 w filledcurves above t "B2<B1", "" i 4 u 1:2:15 w filledcurves below t "B2>B1", "" i 4 u 1:2 w lines lw 2 t "B1", "" i 4 u 1:15 w lines lw 2 t "B2"

# RPS
set output "rps_diff.png"
set terminal png size 640,380
set multiplot title "Requests Per Second (Scalability)"
set title "Requests Per Second" offset 0, -2
set size 1, 0.67
set origin 0, 0.3
set ylabel ""
set format x ""
set xlabel ""
plot "diffbench.dat" i 5 u 1:2:15 w filledcurves above t "B2<B1", "" i 5 u 1:2:15 w filledcurves below t "B2>B1", "" i 5 u 1:2 w lines lw 2 t "B1", "" i 5 u 1:15 w lines lw 2 t "B2"

# % RPS
set title "RPS B2/B1 %"  offset 0, -2
set size 1, 0.33
set origin 0, 0
set format y "% g%%"
set format x "% g"
set xlabel "Concurrent Users"

plot "diffbench.dat" i 5 u 1:($15<$2?((($15*100)/$2) - 100): 0) w boxes notitle, "" i 5 u 1:($15>=$2?((($15*100)/$2)-100): 0) w boxes notitle
unset multiplot


# RESPONSE TIMES
set output "request.png"
set terminal png size 640,640
set multiplot title "Request Response time"

# AVG
set title "Average"  offset 0, -2
set size 0.5, 0.67
set origin 0, 0.30
set ylabel ""
set format y "% gs"
set xlabel ""
set format x ""
plot "diffbench.dat" i 5 u 1:21:8 w filledcurves above t "B2<B1", "" i 5 u 1:21:8 w filledcurves below t "B2>B1", "" i 5 u 1:8 w lines lw 2 t "B1", "" i 5 u 1:21 w lines lw 2 t "B2

# % AVG
set title "Average B2/B1 %"  offset 0, -2
set size 0.5, 0.31
set origin 0, 0
set format y "% g%%"
set format x "% g"
set xlabel "Concurrent Users"
plot "diffbench.dat" i 5 u 1:($21>$8?(100 - (($21*100)/$8)): 0) w boxes notitle, "" i 5 u 1:($21<=$8?(100 - (($21*100)/$8)): 0) w boxes notitle

# MEDIAN
set size 0.5, 0.31
set format y "% gs"
set xlabel ""
set format x ""

set title "Median"
set origin 0.5, 0.66
plot "diffbench.dat" i 5 u 1:24:11 w filledcurves above notitle, "" i 5 u 1:24:11 w filledcurves below notitle, "" i 5 u 1:11 w lines lw 2 notitle, "" i 5 u 1:24 w lines lw 2 notitle

# P90
set title "p90"
set origin 0.5, 0.33
plot "diffbench.dat" i 5 u 1:25:12 w filledcurves above notitle, "" i 5 u 1:25:12 w filledcurves below notitle, "" i 5 u 1:12 w lines lw 2 notitle, "" i 5 u 1:25 w lines lw 2 notitle

# MAX
set title "Max"
set origin 0.5, 0
set format x "% g"
set xlabel "Concurrent Users"
plot "diffbench.dat" i 5 u 1:22:9 w filledcurves above notitle, "" i 5 u 1:22:9 w filledcurves below notitle, "" i 5 u 1:9 w lines lw 2 notitle, "" i 5 u 1:22 w lines lw 2 notitle
unset multiplot
''')

        f.close()

