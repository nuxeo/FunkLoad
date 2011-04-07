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
"""Choose the best html rendering

$Id: ReportRenderHtml.py 53544 2009-03-09 16:28:58Z tlazar $
"""

try:
    # 1/ gnuplot
    from ReportRenderHtmlGnuPlot import RenderHtmlGnuPlot as RenderHtml
except ImportError:
    # 2/ no charts
    from ReportRenderHtmlBase import RenderHtmlBase as RenderHtml

from ReportRenderHtmlGnuPlot import RenderHtmlGnuPlot as RenderHtml
