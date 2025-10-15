#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2016 CERN
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

"""Module providing support for Altera Quartus synthesis"""

from __future__ import absolute_import
import os
import logging

from .makefilesyn import MakefileSyn
from ..util import path as path_mod
from ..util import shell
from ..sourcefiles.srcfile import (VHDLFile, VerilogFile, SVFile, DPFFile,
                                   SignalTapFile, SDCFile, QIPFile, QSYSFile, IPFile,
                                   QSFFile, TCLFile, BSFFile, BDFFile, TDFFile, GDFFile, HEXFile)


class ToolQuartus(MakefileSyn):

    """Class providing the interface for Altera Quartus synthesis"""

    TOOL_INFO = {
        'name': 'Quartus',
        'id': 'quartus',
        'windows_bin': 'quartus_sh.exe -t',
        'linux_bin': 'quartus_sh -t',
        'project_ext': 'qpf'}

    STANDARD_LIBS = ['altera', 'altera_mf', 'lpm', 'ieee', 'std']

    _QUARTUS_SOURCE = 'set_global_assignment -name {0} {{srcfile}}'

    SUPPORTED_FILES = {
        SignalTapFile: _QUARTUS_SOURCE.format('SIGNALTAP_FILE'),
        SDCFile: _QUARTUS_SOURCE.format('SDC_FILE'),
        QIPFile: _QUARTUS_SOURCE.format('QIP_FILE'),
        QSYSFile: _QUARTUS_SOURCE.format('QSYS_FILE'),
        IPFile: _QUARTUS_SOURCE.format('IP_FILE'),
        DPFFile: _QUARTUS_SOURCE.format('MISC_FILE'),
        QSFFile: _QUARTUS_SOURCE.format('SOURCE_TCL_SCRIPT_FILE'),
        TCLFile: _QUARTUS_SOURCE.format('SOURCE_TCL_SCRIPT_FILE'),
        BSFFile: _QUARTUS_SOURCE.format('BSF_FILE'),
        BDFFile: _QUARTUS_SOURCE.format('BDF_FILE'),
        TDFFile: _QUARTUS_SOURCE.format('AHDL_FILE'),
        GDFFile: _QUARTUS_SOURCE.format('GDF_FILE'),
        HEXFile: _QUARTUS_SOURCE.format("HEX_FILE")}

    _QUARTUS_LIBRARY = " -library {library}"

    HDL_FILES = {
        VHDLFile: _QUARTUS_SOURCE.format('VHDL_FILE') + _QUARTUS_LIBRARY,
        VerilogFile: _QUARTUS_SOURCE.format('VERILOG_FILE') + _QUARTUS_LIBRARY,
        SVFile: _QUARTUS_SOURCE.format('SYSTEMVERILOG_FILE') + _QUARTUS_LIBRARY,
        QSYSFile: _QUARTUS_SOURCE.format('QSYS_FILE') + _QUARTUS_LIBRARY,
        QIPFile: _QUARTUS_SOURCE.format("QIP_FILE") + _QUARTUS_LIBRARY}

    CLEAN_TARGETS = {'clean': ["*.rpt", "*.smsg", "*.summary",
                               "*.done", "*.jdi", "*.pin", "*.qws",
                               "db", "incremental_db",
                               "a5_pin_model_dump.txt",
                               "$(PROJECT).qsf",
                               "*.sld", "*.qpf"],
                     'mrproper': ["*.sof", "*.pof", "*.jam", "*.jbc",
                                  "*.ekp", "*.jic"]}

    TCL_CONTROLS = {'create': 'project_new $(PROJECT)',
                    'open': 'project_open $(PROJECT)',
                    'project': 'load_package flow\n'
                               '$(TCL_CREATE)\n'
                               'remove_all_global_assignments -name *_FILE\n'
                               'source files.tcl',
                    'bitstream': 'load_package flow\n'
                                 '$(TCL_OPEN)\n'
                                 'execute_flow -compile',
                    'install_source': ''}

    SET_GLOBAL_INSTANCE = 0
    SET_INSTANCE_ASSIGNMENT = 1
    SET_LOCATION_ASSIGNMENT = 2
    SET_GLOBAL_ASSIGNMENT = 3
    SET_PARAMETER_ASSIGNMENT = 4

    PROP_TYPE = {"set_global_instance": SET_GLOBAL_INSTANCE,
                 "set_instance_assignment": SET_INSTANCE_ASSIGNMENT,
                 "set_location_assignment": SET_LOCATION_ASSIGNMENT,
                 "set_global_assignment": SET_GLOBAL_ASSIGNMENT,
                 "set_parameter": SET_PARAMETER_ASSIGNMENT}

    # mapping of manifest properties to QSF commands
    PROP_DECLARATION = {"syn_properties": SET_GLOBAL_ASSIGNMENT,
                        "syn_instances": SET_GLOBAL_INSTANCE,
                        "syn_location_assignments": SET_LOCATION_ASSIGNMENT,
                        "syn_instance_assignments": SET_INSTANCE_ASSIGNMENT,
                        "syn_parameters": SET_PARAMETER_ASSIGNMENT}
    def __init__(self):
        super(ToolQuartus, self).__init__()
        self._tcl_controls.update(ToolQuartus.TCL_CONTROLS)

    def _makefile_syn_top(self):
        """Update project synthesis variables for Quartus"""
        import re

        def __get_family_string(family=None, device=None):
            """Function that looks for a existing device family name and
            try to guess the value from the device string if not defined"""
            family_names = {
                "^EP2AGX.*$": "Arria II GX",
                "^EP1C.*$": "Cyclone",
                "^EP2C.*$": "Cyclone II",
                "^EP3C.*$": "Cyclone III",
                "^EP4C.*$": "Cyclone IV",
                "^EP4CE.*$": "Cyclone IV E",
                "^EP4CGX.*$": "Cyclone IV GX",
                "^5A.*$": "Arria V",
                "^5S.*$": "Stratix V"}
            if family is None:
                for key in family_names:
                    if re.match(key, device.upper()):
                        family = family_names[key]
                        logging.debug(
                            "Auto-guessed syn_family to be %s (%s => %s)",
                            family, device, key)
            if family is None:
                raise Exception("Could not auto-guess device family, please "
                                "specify in Manifest.py using syn_family!")
            return family

        family_string = __get_family_string(
            family=self.manifest_dict.get("syn_family", None),
            device=self.manifest_dict.get("syn_device", ''))
        device_string = (self.manifest_dict["syn_device"] +
                         self.manifest_dict["syn_package"] +
                         self.manifest_dict["syn_grade"])
        self.manifest_dict["syn_family"] = family_string
        self.manifest_dict["syn_device"] = device_string
        super(ToolQuartus, self)._makefile_syn_top()

    def _manipulate_path(self, path):
        """Takes manifest string and manipulates it to be digested by
        Makefile to generate proper string. Path starting with ~ will
        automatically be enclosed into quotes, any | character will be
        replaced by \| so that path is correctly interpreted by
        makefile"""

        repla = path.replace("|", "\|")
        if repla.startswith("~"):
            return '\\"%s\\"' % (repla[1:])

        return repla


    def _emit_property(self, command, new_property):
        """Emit a formated property for Altera Quartus TCL. All
        properties starting with ~ will be enclosed into quotes"""
        property_dict = {
            'what': None,
            'name': None,
            'location': None,
            'type': None,
            'from': None,
            'to': None,
            'section_id': None,
            'edge': None,
            'tag': None}
        property_dict.update(new_property)
        words = []
        words.append(dict([(b, a) for a, b in
                     self.PROP_TYPE.items()])[command])
        if property_dict['what'] is not None:
            words.append(property_dict['what'])
        if property_dict['name'] is not None:
            words.append("-name")
            words.append(property_dict['name'])
            words.append('\\"%s\\"' % property_dict['value'])
        if property_dict['location'] is not None:
            words.append(property_dict['location'])
        if property_dict['from'] is not None:
            words.append("-from")
            words.append(property_dict['from'])
        if property_dict['tag'] is not None:
            words.append("-tag")
            words.append(property_dict['tag'])
        if property_dict['to'] is not None:
            words.append("-to")
            words.append(self._manipulate_path(property_dict['to']))
        if property_dict['section_id'] is not None:
            words.append("-section_id")
            words.append(self._manipulate_path(property_dict['section_id']))
        if property_dict['edge'] is not None:
            words.append("-" + property_dict['edge'])
        return ' '.join(words)

    def _makefile_syn_tcl(self):
        """Add initial properties to the Altera Quartus project"""
        command_list = []
        command_list.append(self._tcl_controls["project"])
        command_list.append(self._emit_property(
            self.SET_GLOBAL_ASSIGNMENT,
            {'name': 'FAMILY',
            'value': '$(SYN_FAMILY)'}))
        command_list.append(self._emit_property(
            self.SET_GLOBAL_ASSIGNMENT,
            {'name': 'DEVICE',
            'value':'$(SYN_DEVICE)'}))
        command_list.append(self._emit_property(
            self.SET_GLOBAL_ASSIGNMENT,
            {'name': 'TOP_LEVEL_ENTITY',
            'value': '$(TOP_MODULE)'}))
        # traverse through QSF assignments stored in top-level manifest
        for propkey, command in self.PROP_DECLARATION.items():
            for user_property in self.manifest_dict.get(propkey, []):
                if not isinstance(user_property, dict):
                    raise Exception("Quartus property should be defined as dict: "
                                    + str(user_property))
                command_list.append(self._emit_property(command, user_property))

        for inc in self.manifest_dict.get("include_dirs", []):
            command_list.append(self._emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                {'name': 'SEARCH_PATH',
                                'value': inc}))

        # process
        self._tcl_controls["project"] = '\n'.join(command_list)
        super(ToolQuartus, self)._makefile_syn_tcl()

    def _makefile_syn_override_prj_tcl_create(self):
        """Override the TCL create project command by the open one if
        the project already exists.  For Quartus, a project may have
        different extensions."""
        self.writeln("""\
ifneq ($(wildcard $(PROJECT).qpf $(PROJECT).qsf),)
TCL_CREATE := $(TCL_OPEN)
endif""")
        self.writeln()

    def _makefile_syn_files(self):
        # Insert the Quartus standard control TCL files
        command_list = []
        for name, filename in [("quartus_preflow", 'PRE_FLOW_SCRIPT_FILE'),
                               ("quartus_postmodule", 'POST_MODULE_SCRIPT_FILE'),
                               ("quartus_postflow", 'POST_FLOW_SCRIPT_FILE')]:
            if name in self.manifest_dict:
                path = shell.tclpath(path_mod.compose(self.manifest_dict[name]))
                if not os.path.exists(path):
                    raise Exception("{} file listed in {} doesn't exist: {}.\nExiting".format(
                        name, os.getcwd(), path))
                command_list.append(self._emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                    {'name': filename,
                                    'value': 'quartus_sh:' + path}))
        if command_list:
            self._tcl_controls["files"] = '\n'.join(command_list)
        super(ToolQuartus, self)._makefile_syn_files()
