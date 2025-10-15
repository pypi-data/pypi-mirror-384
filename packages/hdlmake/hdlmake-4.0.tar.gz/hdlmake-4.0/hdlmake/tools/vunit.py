#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 CERN
# Author: David Belohrad (david.belohrad@cern.ch)
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

"""Module providing support for VUnit simulation"""

from __future__ import print_function
from __future__ import absolute_import

import logging
from os.path import join, dirname

from .makefilesim import MakefileSim
from ..sourcefiles.srcfile import VerilogFile, VHDLFile, SVFile


def _check_simulation_manifest(top_manifest):
    """Check if the simulation keys are provided by the top manifest"""
    if top_manifest.manifest_dict.get("vunit_script") is None:
        raise Exception("vunit_script variable must be set in the top"
                        " manifest, Use name of VUnit simulation script.")

def _check_system_libs_manifest(top_manifest):
    if top_manifest.manifest_dict.get("target") is None:
        raise Exception("target variable must be set in the"
                        " top manifest. Set to altera, xilinx")

    if top_manifest.manifest_dict.get("syn_family") is None:
        raise Exception("syn_family variable must be set in the top"
                        " manifest. Set to Arria V, Cyclone V ...")

    if top_manifest.manifest_dict.get("tool") is None:
        raise Exception("tool variable must be set in the top"
                        " manifest to reflect which simulator"
                        " VUnit uses. Supported values: modelsim,"
                        " mentor_vhdl_only, questasim, vcs, vcsmx,"
                        " ncsim, activehdl, rivierapro")

def makefile_target_stamp(target, rule=[], prerequisites=[]):
    pre = " ".join(prerequisites)
    r = "\n\t".join(rule)
    new_rule = f"\t{r}\n" if rule else ""
    return (f"{target}: {pre}\n"
            f"{new_rule}")

def makefile_var_stamp(name, value):
    return f"{name.upper()} := {value}"

def shell_if_statement(cond, cmds):
    c = "\n\t\t".join(cmds)
    return f"@if [ {cond} ]; then\\\n\t\t{c}\n\tfi"

class ToolVunitSim(MakefileSim):

    """Class providing the interface for VUnit unit test framework"""

    TOOL_INFO = {'name': 'VUnit',
                 'id': 'vunit'}

    CLEAN_TARGETS = {'clean': ["vunit_out", "work"],
                     'mrproper': []}

    STANDARD_LIBS = ['std', 'vunit_pkg']

    HDL_FILES = {VerilogFile: '',
                 VHDLFile: '',
                 SVFile: ''}


    def __init__(self):
        super(ToolVunitSim, self).__init__()

        # VUnit does not require top-level testbench because it parses
        # all the testbenches in the given verification
        # directories. Following will dismiss warnings
        self.requires_top_level = False
        # following is dictionary of command functions which write
        # portions of makefile responsible for generation of standard
        # simulation libraries into ./sim_libs
        self.STD_LIBS_COMPILER_COMMAND = {
                "altera": self.get_altera_compilation_script,
                "xilinx": self.get_xilinx_compilation_script}

        self.vars = {} # storages of all the created variables
        # storage for all generated files and dirs 
        # (here are the ones which vunit creates)
        self.generated = {"clean" : ["vunit_out"], "mrproper" : []} 

    def write_makefile(self, top_manifest, fileset, filename=None, 
                       system_libs=[]):
        """ 
        Writes makefile exploiting VUnit simulation target. If
        system_libs list contain 'altera', 'xilinx'... , makefile 
        generates commands to compile platform-dependent libraries. 
        For this syn_family and target have to be known
        """
        # vunit params are checked:
        self.system_libs = system_libs

        _check_simulation_manifest(top_manifest)
        # following dependencies in sim manifest are only needed
        # when system libs are used. Compilation requires compiler
        # target architecture and chip

        compile_cmd = self.STD_LIBS_COMPILER_COMMAND.keys()
        # check if system libs include any of known keys
        if any(x in compile_cmd for x in system_libs):
            _check_system_libs_manifest(top_manifest)

        def insert_lib(lib):
            logging.info("Inserting into makefile commands to compile"
                         f" system libraries for {lib} architecture")
            return self.STD_LIBS_COMPILER_COMMAND[lib.lower()]

        keys = self.STD_LIBS_COMPILER_COMMAND.keys()
        self.compile_targets = [insert_lib(x) for x in system_libs if x in keys]

        # create makefile
        self.makefile_setup(top_manifest, fileset, filename=filename)

        # we don't check VUnit here, we know it exists as it is
        # installed with this package and already loaded -> no issue.
        self._makefile_sim_vunit(top_manifest)
        self._makefile_sim_command()
        self._makefile_sim_clean_vunit()
        self._makefile_syn_phony()
        self.makefile_open_write_close()

    def get_xilinx_compilation_script(self, top_manifest):
        # mk_target = "compile.tcl" 
        # #TODO variable number of libraries

        mf_dict = top_manifest.manifest_dict
        name = mf_dict.get("target")

        vars = {"libs_compiled" : "compile.tcl"}

        prev = "."
        for k,v in vars.items():
            id = f"{name.upper()}_{k.upper()}"
            self.writeln(makefile_var_stamp(id, join(prev, v)))
            prev = f"$({id})"
            self.vars[k] = prev

        # generated paths which has to be cleaned
        self.generated["clean"].extend(["compile"]) 
        self.generated["mrproper"].extend([ "*.jou *.log", "libraries", 
            "modelsim.ini", self.vars["libs_compiled"]]) 

        def compile_libs():
            return ("compile_simlib -directory libraries -library unisim"
                    f" -simulator {self.vars['simulator']}"
                    f" -family {self.vars['family']}"
                    f" -language {self.vars['language']}")

        body = [f"@echo \"{compile_libs()}\" >> $@;\\",
                f"vivado -mode batch -source $@;"]
        mk_target = makefile_target_stamp(self.vars["libs_compiled"], body)
        return mk_target

    def get_altera_compilation_script(self, top_manifest):
        """ produces makefile lines reponsible to generate
        sim_libs. sim_libs are generated for both VHDL and
        Verilog. Reason being that whem mixed designs are involved
        they both have to be compiled in altera because basic
        libraries have different way of configuration when VHDL and
        verilog is used """

        mf_dict = top_manifest.manifest_dict
        name = mf_dict.get("target")
        
        # family has to be in lower case without any white spaces 
        vars = { "std_libs" : f"{name}_sim_libs",
                "libs_compiled" : ".compiled"}

        # This generates definitions of vars, 
        # using the previously defined variable
        prev = "."
        for k,v in vars.items():
            id = f"{name.upper()}_{k.upper()}"
            self.writeln(makefile_var_stamp(id, join(prev, v)))
            prev = f"$({id})"
            self.vars[k] = prev

        self.generated["clean"].extend(["work", "compile"]) 
        self.generated["mrproper"].extend([
            self.vars['std_libs'], "libraries", "modelsim.ini"]) 

        def quartus_sh(lang):
            return ("quartus_sh --simlib_comp"
                    f" -tool {self.vars['simulator']}"
                    f" -language {lang}"
                    f" -family {self.vars['family']}"
                    f" -directory {self.vars['std_libs']}")

        quartus_v = quartus_sh("verilog")
        quartus_vhd = quartus_sh("vhdl")
        body = [f"rm -rf {self.vars['std_libs']};\\",
                f"mkdir {self.vars['std_libs']};\\",
                f"{quartus_v};\\",
                f"{quartus_vhd};\\",
                f"touch $@;"]

        mk_target = makefile_target_stamp( self.vars["libs_compiled"], body)
        return mk_target

    def _makefile_general_variables(self, top_manifest):
        mf_dict = top_manifest.manifest_dict

        # HERE YOU CAN DEFINE YOUR NAMES OF GENERAL VARIABLES
        family_low = mf_dict.get("syn_family").lower()
        vars = {"sim_script" : join(".", mf_dict.get("vunit_script")),
                "simulator" : mf_dict.get("tool"),
                "family" : "".join(family_low.split()),
                "language" : mf_dict.get("language")} 

        for k,v in vars.items(): 
            name = k.upper()
            self.writeln(makefile_var_stamp(name,v))
            # from now on, we need just the variable name
            self.vars[k] = f"$({name})"

    def _makefile_sim_vunit(self, top_manifest):
        """Writes down the core part of the makefile"""

        self._makefile_general_variables(top_manifest)

        stamps = ["\n"]
        stamps.append(makefile_target_stamp(
            "all", [], ["sim_pre_cmd", "simulate", "sim_post_cmd"]))

        pre = []
        # include the platform specific targets
        for ct in self.compile_targets:
            stamps.append(ct(top_manifest))
            pre.append(self.vars["libs_compiled"])

        if not pre:
            pre.append("sim_pre_cmd")

        compile_rule = [f"@$(SIM_SCRIPT) --clean --compile;\\", 
                        "touch $@;"]

        stamps.append(makefile_target_stamp(
            "compile", compile_rule, pre))
        stamps.append(makefile_target_stamp(
            "simulate", ["@$(SIM_SCRIPT)"], ["compile"]))

        for s in stamps:
            self.writeln(s)

    def _makefile_sim_clean_vunit(self):
        """ Cleaning """

        def rm_stamp(paths, pre="@", post=""):
            return  [f"{pre}rm -rf {p}{post}" for p in paths]

        pre = []
        for k,v in self.generated.items():
            s = makefile_target_stamp(k, rm_stamp(v), pre)
            pre.append(k)
            self.writeln(s)

    def _makefile_syn_phony(self):
        """Print synthesis PHONY target list to the Makefile"""
        self.writeln(makefile_target_stamp( ".PHONY", [], ["mrproper", 
            "clean", "all", "sim_pre_cmd", "sim_post_cmd", "simulate"]))

    def is_verilog(self, fl):
        """Returns True if given file has pattern of verilog or
        systemverilog file."""
        if any((isinstance(fl, VerilogFile),
                isinstance(fl, SVFile))):
            return True
        return False

    def pre_build_file_set_hook(self, file_set):
        """Modifies the files to contain path for system-wide
        installed VUnit include vunit_defines.svh"""

        import vunit

        include_path = join(dirname(vunit.__file__), "verilog")
        vunit_include = join(include_path, "include")

        if file_set is not None:
            for fl in file_set:
                if self.is_verilog(fl):
                    logging.debug(f"Modifying to include dirs of"
                                  f" {fl.purename} to include VUnit")
                    fl.include_dirs.append(vunit_include)
                    logging.debug(f"INCLUDE_DIRS: {repr(fl.include_dirs)}")

        return file_set
