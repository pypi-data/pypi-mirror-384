#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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

"""This module provides the core actions to the pool"""

from __future__ import absolute_import
from __future__ import print_function
import logging
import os

from subprocess import call
from ..sourcefiles import new_dep_solver as dep_solver
from ..util import path as path_mod
from ..fetch.svn import Svn
from ..fetch.git import Git, GitSM
from ..fetch.local import Local
from .action import Action
from .gen_edalize import Edalize

class Commands(Action):

    """Class that contains the methods for core actions"""

    def __init__(self, *args):
        super(Commands, self).__init__(*args)
        self.git_backend = Git()
        self.gitsm_backend = GitSM()
        self.svn_backend = Svn()
        self.local_backend = Local()

    def _check_all_fetched(self):
        """Check if every module in the pool is fetched"""
        if any([not m.isfetched for m in self.all_manifests]):
            raise Exception(
                "Fetching should be done before continuing.\n"
                "The following modules remain unfetched:\n"
                " {}".format(
                    "\n ".join([str(m) for m in self.all_manifests
                                if not m.isfetched])))

    def makefile(self):
        """Write the Makefile for the current design"""
        # Handle --filename option.
        filename = self.options.__dict__.get('filename')
        self._check_all_fetched()
        self.build_file_set()
        self.solve_file_set()
        self.build_constraints_set()
        combined_fileset = self.parseable_fileset
        combined_fileset.add(self.privative_fileset)
        combined_constr_list = self.constr_list

        if len(self.system_libs) != 0:
            logging.info("Following system libraries were\
 detected: %s" % (', '.join(self.system_libs)))

        self.tool.write_makefile(self.top_manifest,
                                 combined_fileset,
                                 combined_constr_list,
                                 filename=filename,
                                 system_libs=self.system_libs)

    def write_edalize(self):
        filename = "run.py"
        self._check_all_fetched()
        self.build_file_set()
        self.solve_file_set()
        edl = Edalize(self)
        with open(filename, "w") as f:
            edl.generate_file(f)

    def _fetch_all(self):
        """Fetch all the modules declared in the design"""

        def _fetch_module(module):
            """Fetch the given module from the remote origin"""
            new_modules = []
            logging.debug("Fetching module: %s", str(module))
            if module.source == 'svn':
                result = self.svn_backend.fetch(module)
            elif module.source == 'git':
                result = self.git_backend.fetch(module)
            else:
                assert module.source == 'gitsm'
                result = self.gitsm_backend.fetch(module)
            if result is False:
                raise Exception("Unable to fetch module {}".format(module.url))
            module.parse_manifest()
            for m in module.modules:
                new_modules.extend(module.modules[m])
            return new_modules

        fetch_queue = self.all_manifests[:] # Need a copy of the list

        while len(fetch_queue) > 0:
            cur_mod = fetch_queue.pop()
            new_modules = []
            if cur_mod.isfetched:
                new_modules = cur_mod.submodules()
            else:
                new_modules = _fetch_module(cur_mod)
            for mod in new_modules:
                if not mod.isfetched:
                    logging.debug("Appended to fetch queue: "
                                  + str(mod.url))
                    fetch_queue.append(mod)
                else:
                    logging.debug("NOT appended to fetch queue: "
                                  + str(mod.url))

    def fetch(self):
        """Fetch the missing required modules from their remote origin"""
        logging.info("Fetching needed modules.")
        for mod in self.all_manifests:
            if mod.isfetched and not mod.manifest_dict == None:
                if 'fetch_pre_cmd' in mod.manifest_dict:
                    call(mod.manifest_dict.get("fetch_pre_cmd", ''), shell=True)
        self._fetch_all()
        for mod in self.all_manifests:
            if mod.isfetched and not mod.manifest_dict == None:
                if 'fetch_post_cmd' in mod.manifest_dict:
                    call(mod.manifest_dict.get("fetch_post_cmd", ''), shell=True)
        logging.info("All modules fetched.")

    def clean(self):
        """Delete the local copy of the fetched modules"""
        logging.info("Removing fetched modules..")
        remove_list = [mod_aux for mod_aux in self.all_manifests
                       if mod_aux.source in ['git', 'gitsm', 'svn']
                       and mod_aux.isfetched]
        remove_list.reverse()  # we will remove modules in backward order
        if len(remove_list):
            for mod_aux in remove_list:
                logging.info("... clean: " + mod_aux.url +
                             " [from: " + mod_aux.path + "]")
                mod_aux.remove_dir_from_disk()
        else:
            logging.info("There are no modules to be removed")
        logging.info("Modules cleaned.")

    def list_json(self):
        from ..sourcefiles.srcfile import VHDLFile, SVFile, VerilogFile
        from ..sourcefiles.srcfile import XDCFile, TCLFile
        self._check_all_fetched()
        self.build_file_set()
        self.build_constraints_set()
        self.solve_file_set()
        file_list = dep_solver.make_dependency_sorted_list(
            self.parseable_fileset)
        file_list += self.constr_list # add constraints, if exist
        cwd = os.getcwd()
        first=True
        print('{')
        opts = self.top_manifest.manifest_dict.get('ghdl_opt', None)
        if opts:
            print('  "options": {')
            print('    "ghdl_analysis": [', end='')
            opts = ('"{}"'.format(o) for o in opts.split(' '))
            print(', '.join(opts), end='')
            print(']')
            print('  },')
        print ('  "files": [')
        for f in file_list:
            if not first:
                print(',')
            else:
                first=False
            if isinstance(f, VHDLFile):
                lang='vhdl'
            elif isinstance(f, SVFile):
                lang='sv'
            elif isinstance(f, VerilogFile):
                lang='verilog'
            elif isinstance(f, VerilogFile):
                lang='verilog'
            elif isinstance(f, XDCFile):
                lang='xdc'
            elif isinstance(f, TCLFile):
                lang='tcl'
            else:
                lang='unknown'
            print('    {', end='')
            print(f'"file": "{f.rel_path(cwd)}", ', end='')
            print(f'"language": "{lang}"', end='')
            if hasattr(f, 'library'):
                print(f', "library": "{f.library}"', end='')
            print('}', end=''),
        print()
        print('  ]')
        print('}')

    def get_files(self, reverse = False):
        """ Returns pythonic list of all the files parsed through the
        manifest. If reverse is set True, the list of files is
        reversed pointing to top-level as first file """
        unfetched_modules = [mod_aux for mod_aux in self.all_manifests
                             if not mod_aux.isfetched]
        for mod_aux in unfetched_modules:
            logging.warning(
                "List incomplete, module %s has not been fetched!", mod_aux)
        if self.options.top != None:
            self.top_entity = self.options.top
        self.build_file_set()
        self.solve_file_set()
        file_list = dep_solver.make_dependency_sorted_list(
            self.parseable_fileset)
        files_str = [file_aux.path for file_aux in file_list]
        if reverse is True:
            files_str.reverse()
        return files_str

    def list_files(self):
        """List the files added to the design across the pool
        hierarchy"""
        files_str = self.get_files(self.options.reverse)
        if self.options.delimiter is None:
            delimiter = "\n"
        else:
            delimiter = self.options.delimiter
        print(delimiter.join(files_str))

    def _print_comment(self, message):
        """Private method that prints a message to stdout if not terse"""
        if not self.options.terse:
            print(message)

    def _print_file_list(self, file_list):
        """Print file list to standard out"""
        if not len(file_list):
            self._print_comment("# * This module has no files")
        else:
            for file_aux in file_list:
                print("%s\t%s" % (
                    path_mod.relpath(file_aux.path), "file"))

    def list_modules(self):
        """List the modules that are contained by the pool"""

        for mod_aux in self.all_manifests:
            if not mod_aux.isfetched:
                logging.warning("Module not fetched: %s", mod_aux.url)
                self._print_comment("# MODULE UNFETCHED! -> %s" % mod_aux.url)
            else:
                self._print_comment("# MODULE START -> %s" % mod_aux.url)
                if mod_aux.source in ['svn', 'git', 'gitsm']:
                    self._print_comment("# * URL: " + mod_aux.url)
                if (mod_aux.source
                        in ['svn', 'git', 'gitsm', 'local']
                        and mod_aux.parent):
                    self._print_comment("# * The parent for this module is: %s"
                                        % mod_aux.parent.url)
                else:
                    self._print_comment("# * This is the root module")
                print("%s\t%s" % (mod_aux.path, mod_aux.source))
                if self.options.withfiles:
                    self._print_file_list(mod_aux.files)
                self._print_comment("# MODULE END -> %s" % mod_aux.url)
            self._print_comment("")

    def list_deps(self):
        self.build_file_set()
        self.solve_file_set()

        from ..sourcefiles.srcfile import DepFile
        fset = self.parseable_fileset.filter(DepFile)
        for f in sorted(fset, key=(lambda x: x.path)):
            print('{}:'.format(f.path))
            for dep in sorted([str(x) for x in f.provides]):
                print(' provide {}'.format(dep))
            for dep in sorted([str(x) for x in f.requires]):
                print(' require {}'.format(dep))

    def generate_tree(self):
        from .tree import ActionTree
        t = ActionTree(self)
        t.generate_tree()
