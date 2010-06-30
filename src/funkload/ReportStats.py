# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
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
"""Classes that collect statistics submitted by the result parser.

$Id: ReportStats.py 24737 2005-08-31 09:00:16Z bdelbosc $
"""
class MonitorStat:
    """Collect system monitor info."""
    def __init__(self, attrs):
        for key, value in attrs.items():
            setattr(self, key, value)


class ErrorStat:
    """Collect Error or Failure stats."""
    def __init__(self, cycle, step, number, code, header, body, traceback):
        self.cycle = cycle
        self.step = step
        self.number = number
        self.code = code
        self.header = header and header.copy() or {}
        self.body = body or None
        self.traceback = traceback


class Percentiles:
    """ Calculate Percentiles with the given stepsize. """

    def __init__(self, stepsize=10, name ="UNKNOWN", results=None):
        self.stepsize = stepsize
        self.name = name
        if results is None:
            self.results = []
        else:
            self.results = results

    def addResult(self, newresult):
        """Add a new result."""
        self.results.append(newresult)

    def calcPercentiles(self):
        """Compute percentiles."""
        results = self.results
        results.sort()
        len_results = len(results)
        old_value = -1
        for perc in range(0, 100, self.stepsize):
            index = int(perc / 100.0 * len_results)
            try:
                value = results[index]
            except IndexError:
                value = -1.0
            setattr(self, "perc%02d" % perc, float(value))
            old_value = value

    def __str__(self):
        self.calcPercentiles()
        fmt_string = ["Percentiles: %s" % self.name]
        for perc in range(0, 100, self.stepsize):
            name = "perc%02d" % perc
            fmt_string.append("%s=%s" % (name, getattr(self, name)))
        return ", ".join(fmt_string)

    def __repr__(self):
        return "Percentiles(stepsize=%r, name=%r, results=%r)" % (
            self.stepsize, self.name, self.results)

class ApdexStat:
    def __init__(self, apdex_t):
        self.apdex_satisfied = 0
        self.apdex_tolerating = 0
        self.apdex_frustrating = 0
        self.apdex_satisfied_t = apdex_t
        self.apdex_tolerating_t = 4*apdex_t 
        self.apdex_t = apdex_t
        self.count = 0

    def add(self, duration):
        if duration < self.apdex_satisfied_t:
            self.apdex_satisfied += 1
        elif duration < self.apdex_tolerating_t:
            self.apdex_tolerating += 1
        else:
            self.apdex_frustrating += 1
        self.count += 1

    def getScore(self):
        score = 0
        if self.count:
            score = (self.apdex_satisfied + (self.apdex_tolerating/2.0)) / self.count
        return score


class AllResponseStat:
    """Collect stat for all response in a cycle."""
    def __init__(self, cycle, cycle_duration, cvus, apdex_t):
        self.cycle = cycle
        self.cycle_duration = cycle_duration
        self.cvus = int(cvus)
        self.per_second = {}
        self.max = 0
        self.min = 999999999
        self.avg = 0
        self.total = 0
        self.count = 0
        self.success = 0
        self.error = 0
        self.error_percent = 0
        self.rps = 0
        self.rps_min = 0
        self.rps_max = 0
        self.finalized = False
        self.percentiles = Percentiles(stepsize = 5, name = cycle)
        self.apdex = ApdexStat(apdex_t)
        self.apdex_score = None

    def add(self, date, result, duration):
        """Add a new response to stat."""
        date_s = int(float(date))
        self.per_second [date_s] = self.per_second.setdefault(
            int(date_s), 0) + 1
        self.count += 1
        if result == 'Successful':
            self.success += 1
        else:
            self.error += 1
        duration_f = float(duration)
        self.max = max(self.max, duration_f)
        self.min = min(self.min, duration_f)
        self.total += duration_f
        self.finalized = False
        self.percentiles.addResult(duration_f)
        self.apdex.add(duration_f)

    def finalize(self):
        """Compute avg times."""
        if self.finalized:
            return
        if self.count:
            self.avg = self.total / float(self.count)
        self.min = min(self.max, self.min)
        if self.error:
            self.error_percent = 100.0 * self.error / float(self.count)

        rps_min = rps_max = 0
        for date in self.per_second.keys():
            rps_max = max(rps_max, self.per_second[date])
            rps_min = min(rps_min, self.per_second[date])
        if self.cycle_duration:
            rps = self.count / float(self.cycle_duration)
            if rps < 1:
                # average is lower than 1 this means that sometime there was
                # no request during one second
                rps_min = 0
            self.rps = rps
        self.rps_max = rps_max
        self.rps_min = rps_min
        self.percentiles.calcPercentiles()
        self.apdex_score = self.apdex.getScore()
        self.finalized = True


class SinglePageStat:
    """Collect stat for a single page."""
    def __init__(self, step):
        self.step = step
        self.count = 0
        self.date_s = None
        self.duration = 0.0
        self.result = 'Successful'

    def addResponse(self, date, result, duration):
        """Add a response to a page."""
        self.count += 1
        if self.date_s is None:
            self.date_s = int(float(date))
        self.duration += float(duration)
        if result != 'Successful':
            self.result = result

    def __repr__(self):
        """Representation."""
        return 'page %s %s %ss' % (self.step,
                                   self.result, self.duration)

class PageStat(AllResponseStat):
    """Collect stat for asked pages in a cycle."""
    def __init__(self, cycle, cycle_duration, cvus, apdex_t):
        AllResponseStat.__init__(self, cycle, cycle_duration, cvus, apdex_t)
        self.threads = {}

    def add(self, thread, step,  date, result, duration, rtype):
        """Add a new response to stat."""
        thread = self.threads.setdefault(thread, {'count': 0,
                                                  'pages': {}})
        if str(rtype) in ('post', 'get', 'xmlrpc'):
            new_page = True
        else:
            new_page = False
        if new_page:
            thread['count'] += 1
            self.count += 1
        if not thread['count']:
            # don't take into account request that belongs to a staging up page
            return
        stat = thread['pages'].setdefault(thread['count'],
                                          SinglePageStat(step))
        stat.addResponse(date, result, duration)
        self.apdex.add(float(duration))
        self.finalized = False

    def finalize(self):
        """Compute avg times."""
        if self.finalized:
            return
        for thread in self.threads.keys():
            for page in self.threads[thread]['pages'].values():
                if str(page.result) == 'Successful':
                    if page.date_s:
                        count = self.per_second.setdefault(page.date_s, 0) + 1
                        self.per_second[page.date_s] = count
                    self.success += 1
                    self.total += page.duration
                    self.percentiles.addResult(page.duration)
                else:
                    self.error += 1
                    continue
                duration = page.duration
                self.max = max(self.max, duration)
                self.min = min(self.min, duration)
        AllResponseStat.finalize(self)
        if self.cycle_duration:
            # override rps to srps
            self.rps = self.success / float(self.cycle_duration)
        self.percentiles.calcPercentiles()
        self.finalized = True

class ResponseStat:
    """Collect stat a specific response in a cycle."""
    def __init__(self, step, number, cvus, apdex_t):
        self.step = step
        self.number = number
        self.cvus = int(cvus)
        self.max = 0
        self.min = 999999999
        self.avg = 0
        self.total = 0
        self.count = 0
        self.success = 0
        self.error = 0
        self.error_percent = 0
        self.url = '?'
        self.description = ''
        self.type = '?'
        self.finalized = False
        self.percentiles = Percentiles(stepsize=5, name=step)
        self.apdex = ApdexStat(apdex_t)
        self.apdex_score = None

    def add(self, rtype, result, url, duration, description=None):
        """Add a new response to stat."""
        self.count += 1
        if result == 'Successful':
            self.success += 1
        else:
            self.error += 1
        self.max = max(self.max, float(duration))
        self.min = min(self.min, float(duration))
        self.total += float(duration)
        self.percentiles.addResult(float(duration))
        self.url = url
        self.type = rtype
        if description is not None:
            self.description = description
        self.finalized = False
        self.apdex.add(float(duration))

    def finalize(self):
        """Compute avg times."""
        if self.finalized:
            return
        if self.total:
            self.avg = self.total / float(self.count)
        self.min = min(self.max, self.min)
        if self.error:
            self.error_percent = 100.0 * self.error / float(self.count)
        self.percentiles.calcPercentiles()
        self.apdex_score = self.apdex.getScore()
        self.finalized = True

class TestStat:
    """Collect test stat for a cycle.

    Stat on successful test case.
    """
    def __init__(self, cycle, cycle_duration, cvus):
        self.cycle = cycle
        self.cycle_duration = float(cycle_duration)
        self.cvus = int(cvus)
        self.max = 0
        self.min = 999999999
        self.avg = 0
        self.total = 0
        self.count = 0
        self.success = 0
        self.error = 0
        self.error_percent = 0
        self.traceback = []
        self.pages = self.images = self.redirects = self.links = 0
        self.xmlrpc = 0
        self.tps = 0
        self.finalized = False
        self.percentiles = Percentiles(stepsize=5, name=cycle)

    def add(self, result, pages, xmlrpc, redirects, images, links,
            duration, traceback=None):
        """Add a new response to stat."""
        self.finalized = False
        self.count += 1
        if traceback is not None:
            self.traceback.append(traceback)
        if result == 'Successful':
            self.success += 1
        else:
            self.error += 1
            return
        self.max = max(self.max, float(duration))
        self.min = min(self.min, float(duration))
        self.total += float(duration)
        self.pages = max(self.pages, int(pages))
        self.xmlrpc = max(self.xmlrpc, int(xmlrpc))
        self.redirects = max(self.redirects, int(redirects))
        self.images = max(self.images, int(images))
        self.links = max(self.links, int(links))
        self.percentiles.addResult(float(duration))

    def finalize(self):
        """Compute avg times."""
        if self.finalized:
            return
        if self.success:
            self.avg = self.total / float(self.success)
        self.min = min(self.max, self.min)
        if self.error:
            self.error_percent = 100.0 * self.error / float(self.count)
        if self.cycle_duration:
            self.tps = self.success / float(self.cycle_duration)
        self.percentiles.calcPercentiles()
        self.finalized = True
