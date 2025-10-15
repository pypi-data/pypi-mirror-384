#!/usr/bin/python
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

"""This module provides a Xilinx block design parser for HDLMake.
 Well, not really.  It just add a 'provide' link.
 It might be more interesting to parse the associated .bxml file,
 which gives all the source files referenced by the block design.
 But the format of this file may not be stable.
"""

from __future__ import absolute_import
import os.path
import logging

from .new_dep_solver import DepParser
from .dep_file import DepRelation
from ..sourcefiles.srcfile import create_source_file

class BDParser(DepParser):
    """Class providing the Xilinx BD parser"""

    def parse(self, dep_file, graph):
        """Extract the provided module from a BD file"""
        filename = os.path.basename(dep_file.path)
        module_name, _ = os.path.splitext(filename)
        logging.debug("found module %s.%s", dep_file.library, module_name)
        graph.add_provide(
            dep_file,
            DepRelation(module_name, dep_file.library, DepRelation.MODULE))

