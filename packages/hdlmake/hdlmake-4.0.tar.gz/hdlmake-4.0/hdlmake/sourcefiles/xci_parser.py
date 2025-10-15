#!/usr/bin/python
#
# Author: Nick Brereton
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see .
#

"""This module provides a Xilinx XCI IP description parser for HDLMake"""

from __future__ import absolute_import
import re
import logging
import json
import zipfile
import io

from xml.etree import ElementTree as ET

from .new_dep_solver import DepParser
from .dep_file import DepRelation


class XCIParserBase(DepParser):
    """Base class for the Xilinx XCI(X) parser"""

    def _parse_xml_xci(self, xml_str):
        """Parse a Xilinx XCI IP description file in XML format"""

        # extract namespaces with a regex -- not really ideal, but without pulling in
        # an external xml lib I can't think of a better way.
        xmlnsre = re.compile(r'''\bxmlns:(\w+)\s*=\s*"(\w+://[^"]*)"''', re.MULTILINE)
        nsmap = dict(xmlnsre.findall(xml_str))
        value = ET.fromstring(xml_str).find('spirit:componentInstances/spirit:componentInstance/spirit:instanceName', nsmap)
        if not value is None:
            return value.text
        return None

    def _parse_json_xci(self, json_str):
        """Parse a Xilinx XCI IP description file in JSON format"""

        data = json.loads(json_str)
        ip_inst = data.get('ip_inst')
        if ip_inst is not None:
            return ip_inst.get('xci_name')
        return None

    def _parse_xci(self, dep_file, graph, file):
        """Parse a Xilinx XCI IP description file to determine the provided module(s)

        This file can either be in XML or JSON file format depending on the
        Vivado version used to create it, see Xilinx UG994:

        > Note: Starting in Vivado Design Suite version 2018.3, the block design
        > file format has changed from XML to JSON. When you open a block design
        > that uses the older XML schema in Vivado 2018.3 or later, click Save
        > to convert the format from XML to JSON. The following INFO message
        > notifies you of the schema change.
        """

        # Hacky file format detection, just check the first character of the
        # file which should be "<" for XML and "{" for JSON
        content = file.read()
        c = content.splitlines()[0].strip()[0]

        if c == "<":
            logging.debug("Parsing xci as xml format")
            module_name = self._parse_xml_xci(content)
        elif c == "{":
            logging.debug("Parsing xci as json format")
            module_name = self._parse_json_xci(content)
        else:
            logging.warning("Unknown xci format {}, skipping".format(dep_file.path))
            return

        if module_name is None:
            return
        logging.debug("Found module %s.%s", dep_file.library, module_name)
        graph.add_provide(
            dep_file,
            DepRelation(module_name, dep_file.library, DepRelation.MODULE))


class XCIParser(XCIParserBase):
    """Class providing the Xilinx XCI parser"""

    def parse(self, dep_file, graph):
        """Parse a Xilinx XCI IP description file to determine the provided module(s)"""

        logging.debug("Parsing %s", dep_file.path)
        with open(dep_file.path) as f:
            self._parse_xci(dep_file, graph, f)


class XCIXParser(XCIParserBase):
    """Class providing the Xilinx XCIX parser"""

    def _parse_cc(self, f):
        """Parse the cc.xml file to find the XCI file path"""

        xml = f.read()
        value = ET.fromstring(xml).find("CoreFile")
        if value is not None:
            return value.text
        return None

    def parse(self, dep_file, graph):
        """Parse a Xilinx XCIX IP description file to determine the provided module(s)"""

        logging.debug("Parsing %s", dep_file.path)

        with zipfile.ZipFile(dep_file.path) as zf:
            with zf.open('cc.xml') as cc:
                logging.debug("Parsing cc.xml")
                xci_path = self._parse_cc(cc)
                if xci_path is not None:
                    logging.debug("Parsing %s", xci_path)
                    with io.TextIOWrapper(zf.open(xci_path)) as f:
                        self._parse_xci(dep_file, graph, f)

