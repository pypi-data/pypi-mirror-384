#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2025 CERN
# Author: Vladisav Borshch (borchsh.vn@gmail.com)
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
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.
#

"""Module providing support for Gowin IDE synthesis"""


from __future__ import absolute_import
from .makefilesyn import MakefileSyn
from ..sourcefiles.srcfile import VHDLFile, VerilogFile, SDCFile, IPCFile, CSTFile, MODFile


class ToolGowin(MakefileSyn):

    """Class providing the interface for Gowin IDE synthesis"""

    TOOL_INFO = {
        'name': 'Gowin',
        'id': 'gowin',
        'windows_bin': 'gw_sh.exe',
        'linux_bin': 'gw_sh',
        'project_ext': 'gprj'}

    STANDARD_LIBS = ['ieee', 'std']

    _GOWIN_SOURCE = 'add_file -type {0} {{srcfile}}'
    _GOWIN_LIB = 'set_file_prop -lib {{library}} {{srcfile}}'

    SUPPORTED_FILES = {
        SDCFile: _GOWIN_SOURCE.format('sdc'),
        CSTFile: _GOWIN_SOURCE.format('cst'),
        IPCFile: _GOWIN_SOURCE.format('ipc'),
        MODFile: _GOWIN_SOURCE.format('mod')}

    HDL_FILES = {
        VHDLFile: _GOWIN_SOURCE.format('vhdl'),
        VerilogFile: _GOWIN_SOURCE.format('verilog')}

    CLEAN_TARGETS = {'clean': ["$(PROJECT)", ".user"],
                     'mrproper': ["*.bin", "*.fi"]}
    
    _GOWIN_RUN = 'source files.tcl\n' \
                'set_device {device}{grade}{package} {family}\n' \
                'set_option -output_base_name {project}'
    
    TCL_CONTROLS = {
                    'create': 'create_project -dir . -name {project} -pn {device}{grade}{package} -device_version {family}',
                    'open': 'open_project {$(PROJECT)/$(PROJECT_FILE)}',
                    'close': 'run close',
                    'project': '$(TCL_CREATE)\n'
                               'cd ..\n' # change working directory to align with relative paths
                               'source files.tcl\n'
                               '$(TCL_CLOSE)',
                    'synthesize': '$(TCL_OPEN)\n' + 'run syn',
                    'par': '$(TCL_OPEN)\n' + 'run pnr',
                    'bitstream': '$(TCL_OPEN)\n' + 'run all'}

    # Override the build command, because no space is expected between TCL_INTERPRETER and the tcl file
    MAKEFILE_SYN_BUILD_CMD="""\
{0}.tcl:
{3}

{0}: {1} {0}.tcl
\t$(SYN_PRE_{2}_CMD)
\t$(TCL_INTERPRETER) $@.tcl
\t$(SYN_POST_{2}_CMD)
\t{4} $@
"""

    def __init__(self):
        super(ToolGowin, self).__init__()
        self._tcl_controls.update(ToolGowin.TCL_CONTROLS)

    def _makefile_syn_tcl(self):
        """Create a Gowin synthesis project by TCL"""
        syn_project = self.manifest_dict["syn_project"]
        syn_device = self.manifest_dict["syn_device"]
        syn_grade = self.manifest_dict["syn_grade"]
        syn_package = self.manifest_dict["syn_package"]
        syn_family = "NA"
        if "syn_family" in self.manifest_dict:
            syn_family = "{0}".format(self.manifest_dict["syn_family"])
        # Template substitute for 'create'.
        create_tmp = self._tcl_controls["create"]
        self._tcl_controls["create"] = create_tmp.format(project=syn_project,
                                                             device=syn_device,
                                                             package=syn_package,
                                                             family=syn_family,
                                                             grade=syn_grade)
        super(ToolGowin, self)._makefile_syn_tcl()
