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


class AllResponseStat:
    """Collect stat for all response in a cycle."""
    def __init__(self, cycle, cycle_duration, cvus):
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
        self.max = max(self.max, float(duration))
        self.min = min(self.min, float(duration))
        self.total += float(duration)
        self.finalized = False

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
    def __init__(self, cycle, cycle_duration, cvus):
        AllResponseStat.__init__(self, cycle, cycle_duration, cvus)
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
        self.finalized = True

class ResponseStat:
    """Collect stat a specific response in a cycle."""
    def __init__(self, step, number, cvus):
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
        self.url = url
        self.type = rtype
        if description is not None:
            self.description = description
        self.finalized = False

    def finalize(self):
        """Compute avg times."""
        if self.finalized:
            return
        if self.total:
            self.avg = self.total / float(self.count)
        self.min = min(self.max, self.min)
        if self.error:
            self.error_percent = 100.0 * self.error / float(self.count)
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
        self.finalized = True
