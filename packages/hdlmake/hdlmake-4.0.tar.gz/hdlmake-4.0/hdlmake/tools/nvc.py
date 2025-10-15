#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN, 2023 CNPEM
# Authors: Pawel Szostek (pawel.szostek@cern.ch), Augusto Fraga Giachero (augusto.fraga@lnls.br)
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

"""Module providing support for NVC simulator"""

from __future__ import absolute_import

from .makefilesim import MakefileSim
from ..sourcefiles.srcfile import VHDLFile


class ToolNVC(MakefileSim):

    """Class providing the interface for NVC simulator"""

    TOOL_INFO = {
        'name': 'NVC',
        'id': 'nvc',
        'windows_bin': 'nvc',
        'linux_bin': 'nvc'}

    STANDARD_LIBS = ['ieee', 'std']

    HDL_FILES = {VHDLFile: ''}

    CLEAN_TARGETS = {'clean': ["*.cf", "*.o", "$(TOP_MODULE)", "work"],
                     'mrproper': ["*.vcd"]}

    SIMULATOR_CONTROLS = {'vlog': None,
                          'vhdl': '$(NVC) --work={work} $(NVC_OPT) -a $(NVC_ANALYSIS_OPT)  $<',
                          'compiler': '$(NVC) $(NVC_OPT) -e $(NVC_ELAB_OPT) $(TOP_MODULE)'}

    def __init__(self):
        super(ToolNVC, self).__init__()

    def _makefile_sim_options(self):
        """Print the NVC options to the Makefile"""
        self.writeln("NVC := nvc")
        nvc_opt = self.manifest_dict.get("nvc_opt", '')
        nvc_analysis_opt = self.manifest_dict.get("nvc_analysis_opt", '')
        nvc_elab_opt = self.manifest_dict.get("nvc_elab_opt", '')
        self.writeln("NVC_OPT := {nvc_opt}\n".format(nvc_opt=nvc_opt))
        self.writeln("NVC_ANALYSIS_OPT := {nvc_analysis_opt}\n".format(nvc_analysis_opt=nvc_analysis_opt))
        self.writeln("NVC_ELAB_OPT := {nvc_elab_opt}\n".format(nvc_elab_opt=nvc_elab_opt))

    def _makefile_sim_compilation(self):
        """Print the NVC simulation compilation target"""
        libs = self.get_all_libs()
        self._makefile_sim_libs_variables(libs)
        self.writeln("simulation: $(VERILOG_OBJ) $(VHDL_OBJ)")
        self.writeln("\t\t" + self.SIMULATOR_CONTROLS['compiler'])
        self.writeln('\n')
        self._makefile_sim_dep_files()
