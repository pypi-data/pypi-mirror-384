#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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

"""Module providing the classes that are used to handle Xilinx ISE"""

from __future__ import print_function
from __future__ import absolute_import


from .makefilesyn import MakefileSyn

from ..util import shell
from ..sourcefiles.srcfile import (VHDLFile, VerilogFile, SVFile,
                                   UCFFile, CDCFile, NGCFile, BMMFile, XCOFile)

FAMILY_NAMES = {
    "XC6S": "Spartan6",
    "XC3S": "Spartan3",
    "XC6V": "Virtex6",
    "XC5V": "Virtex5",
    "XC4V": "Virtex4",
    "XC7Z": "Zynq",
    "XC7V": "Virtex7",
    "XC7K": "Kintex7",
    "XC7A": "Artix7"}

ISE_STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']


class ToolISE(MakefileSyn):

    """Class providing the methods to create and build a Xilinx ISE project"""

    TOOL_INFO = {
        'name': 'ISE',
        'id': 'ise',
        'windows_bin': 'xtclsh.exe',
        'linux_bin': 'xtclsh',
        'project_ext': 'xise'}

    STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']
    SYSTEM_LIBS = ['xilinx']


    _ISE_VHDL_LIBRARY = ' -lib_vhdl {library}'
    _ISE_ADD_SRCFILE =  'xfile add {srcfile}'


    SUPPORTED_FILES = {
        UCFFile: _ISE_ADD_SRCFILE,
        CDCFile: _ISE_ADD_SRCFILE,
        BMMFile: _ISE_ADD_SRCFILE,
        NGCFile: _ISE_ADD_SRCFILE,
        XCOFile: _ISE_ADD_SRCFILE}

    HDL_FILES = {
        VHDLFile:    'HDL_FILES[VHDLFile] - NEEDS SETTING!!!',
        VerilogFile: _ISE_ADD_SRCFILE,
        SVFile:      _ISE_ADD_SRCFILE,
        NGCFile:     None}



    CLEAN_TARGETS = {'clean': ["xst", "xlnx_auto_0_xdb", "iseconfig _xmsgs",
                               "_ngo", "*.b", "*_summary.html",
                               "*.bld", "*.cmd_log", "*.drc", "*.lso", "*.ncd",
                               "*.ngc", "*.ngd", "*.ngr", "*.pad", "*.par",
                               "*.pcf", "*.prj", "*.ptwx", "*.stx", "*.syr",
                               "*.twr", "*.twx", "*.gise", "*.gise", "*.bgn",
                               "*.unroutes", "*.ut", "*.xpi", "*.xst",
                               "*.xise", "*.xwbt",
                               "*_envsettings.html", "*_guide.ncd",
                               "*_map.map", "*_map.mrp", "*_map.ncd",
                               "*_map.ngm", "*_map.xrpt", "*_ngdbuild.xrpt",
                               "*_pad.csv", "*_pad.txt", "*_par.xrpt",
                               "*_summary.xml", "*_usage.xml", "*_xst.xrpt",
                               "usage_statistics_webtalk.html", "webtalk.log",
                               "par_usage_statistics.html", "webtalk_pn.xml"],
                     'mrproper': ["*.bit", "*.bin", "*.mcs"]}

    _ISE_RUN = '''\
$(TCL_OPEN)
set process {{{0}}}
process run '$$'process
set result [process get '$$'process status]
if {{ '$$'result == \\"errors\\" }} {{
    exit 1
}}
$(TCL_SAVE)
$(TCL_CLOSE)'''

    TCL_CONTROLS = {
        'create': 'project new $(PROJECT_FILE)',
        'open': 'project open $(PROJECT_FILE)',
        'save': 'project save',
        'close': 'project close',
        'project': 'file delete $(PROJECT_FILE)\n'
                   '$(TCL_CREATE)\n'
                   'xfile remove [search \\* -type file]\n'
                   'source files.tcl\n'
                   '{0}\n'
                   'project set top $(TOP_MODULE)\n'
                   '$(TCL_SAVE)\n'
                   '$(TCL_CLOSE)',
        'synthesize': _ISE_RUN.format("Synthesize - XST"),
        'translate': _ISE_RUN.format("Translate"),
        'map': _ISE_RUN.format("Map"),
        'par': _ISE_RUN.format("Place '&' Route"),
        'bitstream': _ISE_RUN.format("Generate Programming File"),
        'install_source': "*.bit *.bin"}

    def __init__(self):
        super(ToolISE, self).__init__()
        self._tcl_controls.update(ToolISE.TCL_CONTROLS)

    def _makefile_syn_files_predefinelibs(self):
        """create libraries before adding files to the files.tcl file"""
        libraries = self.get_all_libs()
        # if there is more than one library in use, then...
        if len(libraries) > 1:
          # make sure we use the library name when adding a file!
          self.HDL_FILES[VHDLFile] = self._ISE_ADD_SRCFILE + self._ISE_VHDL_LIBRARY          
          # add a library creation tcl command for each VHDL library
          for libname in libraries:	
            self.writeln('\t\techo lib_vhdl new ' + libname + ' >> $@')
        else :
          # Else make sure that the file name is added on its own 
          self.HDL_FILES[VHDLFile] = self._ISE_ADD_SRCFILE


    def _makefile_syn_top(self):
        """Create the top part of the synthesis Makefile for ISE"""
        syn_family = self.manifest_dict.get("syn_family", None)
        if syn_family is None:
            syn_family = FAMILY_NAMES.get(
                self.manifest_dict["syn_device"][0:4].upper())
            if syn_family is None:
                raise Exception(
                    "syn_family is not defined in Manifest.py"
                    " and can not be guessed!")
        self.manifest_dict["syn_family"] = syn_family
        super(ToolISE, self)._makefile_syn_top()


    def _makefile_syn_tcl(self):
        """Create a Xilinx synthesis project by TCL"""
        syn_properties = self.manifest_dict.get("syn_properties")
        project_new = []
        project_tcl = self._tcl_controls["project"]
        if shell.check_windows_commands():
            tmpl = 'project set "{0}" "{1}"'
        else:
            # TCL needs quotes, so they must be escaped from the shell.
            # But parentheses may appear in the property name, so the name is
            # also quoted using single quote.  But the value may need
            # substitution, so they are not protected.
            # In addition to the shell, there is also python to protect against!
            tmpl = 'project set \'"{0}"\' \\"{1}\\"'
        properties = [
            ['family', '$(SYN_FAMILY)'],
            ['device', '$(SYN_DEVICE)'],
            ['package', '$(SYN_PACKAGE)'],
            ['speed', '$(SYN_GRADE)'],
            ['Manual Implementation Compile Order', 'false'],
            ['Auto Implementation Top', 'false'],
            ['Create Binary Configuration File', 'true']]
        if not syn_properties is None:
            properties.extend(syn_properties)
        for prop in properties:
            project_new.append(tmpl.format(prop[0], prop[1]))
        project_new.append('set compile_directory .')
        self._tcl_controls["project"] = project_tcl.format(
            "\n".join(project_new))
        super(ToolISE, self)._makefile_syn_tcl()

    def _makefile_syn_override_prj_tcl_create(self):
        # As the project is always deleted before being created, TCL_CREATE must not be
        # overwritten.
        pass
