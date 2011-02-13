# (C) Copyright 2010 Nuxeo SAS <http://nuxeo.com>
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
"""Merge FunkLoad result files to produce a report for distributed bench
reports."""
import os
import xml.parsers.expat
from utils import trace

class EndOfConfig(Exception):
    pass

class FunkLoadConfigXmlParser:
    """Parse the config part of a funkload xml results file."""
    def __init__(self):
        """Init setup expat handlers."""
        self.current_element = [{'name': 'root'}]
        self.cycles = None
        self.cycle_duration = 0
        self.nodes = {}
        self.config = {}
        self.files = []
        self.current_file = None

    def parse(self, xml_file):
        """Do the parsing."""
        self.current_file = xml_file
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.handleStartElement
        try:
            parser.ParseFile(file(xml_file))
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
                    result done with fl-run-test)."""
                else:
                    print """You may need to remove non ascii char that comes
                    from error pages catched during the bench. iconv
                    or recode may help you."""
                print 'Xml parser element stack: %s' % [
                    x['name'] for x in self.current_element]
                raise
        except EndOfConfig:
            return

    def handleStartElement(self, name, attrs):
        """Called by expat parser on start element."""
        if name == 'funkload':
            self.config['version'] = attrs['version']
            self.config['time'] = attrs['time']
        elif name == 'config':
            self.config[attrs['key']] = attrs['value']
            if attrs['key'] == 'duration':
                if self.cycle_duration and attrs['value'] != self.cycle_duration:
                    trace('Skipping file %s with different cycle duration %s' % (self.current_file, attrs['value']))
                    raise EndOfConfig
                self.cycle_duration = attrs['value']
            elif attrs['key'] == 'cycles':
                if self.cycles and attrs['value'] != self.cycles:
                    trace('Skipping file %s with different cycles %s != %s' % (self.current_file, attrs['value'], self.cycles))
                    raise EndOfConfig
                self.cycles = attrs['value']
            elif attrs['key'] == 'node':
                self.nodes[self.current_file] = attrs['value']
        else:
            self.files.append(self.current_file)
            raise EndOfConfig

def replace_all(text, dic):
    for i, j in dic.iteritems():
        if isinstance(text, str):
            text = text.decode('utf-8', 'ignore')
        text = text.replace(i, j)
    return text.encode('utf-8')


class MergeResultFiles:
    def __init__(self, input_files, output_file):
        xml_parser = FunkLoadConfigXmlParser()
        for input_file in input_files:
            trace (".")
            xml_parser.parse(input_file)

        node_count = len(xml_parser.files)

        # compute cumulated cycles
        node_cycles = [int(item) for item in xml_parser.cycles[1:-1].split(',')]
        cycles = map(lambda x: x * node_count, node_cycles)

        # node names
        node_names = []
        i = 0
        for input_file in xml_parser.files:
            node_names.append(xml_parser.nodes.get(input_file, 'node-' + str(i)))
            i += 1
        trace("\nnodes: %s\n" % ', '.join(node_names))
        trace("cycles for a node:    %s\n" % node_cycles)
        trace("cycles for all nodes: %s\n" % cycles)

        output = open(output_file, 'w+')
        i = 0
        for input_file in xml_parser.files:
            dic = {xml_parser.cycles: str(cycles),
                   'host="localhost"': 'host="%s"' % node_names[i],
                   'thread="': 'thread="' + str(i)}
            if i == 0:
                dic['key="node" value="%s"' % node_names[0]] = 'key="node" value="%s"' % (
                    ', '.join(node_names))
            c = 0
            for cycle in node_cycles:
                dic['cycle="%3.3i" cvus="%3.3i"' % (c, node_cycles[c])] = 'cycle="%3.3i" cvus="%3.3i"' % (c, cycles[c])
                c += 1

            f = open(input_file)
            for line in f.xreadlines():
                if "</funkload>" in line:
                    continue
                elif i > 0 and ('<funkload' in line or '<config' in line):
                    continue
                output.write(replace_all(line, dic))
            f.close()
            i += 1
        output.write("</funkload>\n")
        output.close()



