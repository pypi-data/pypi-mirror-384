#!/usr/bin/python
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
#

"""Module providing the Classes used to provide and handle dependable files"""

from __future__ import absolute_import
from __future__ import print_function
import os
import logging

from ..util import path as path_mod


class DepRelation(object):

    """Class used to create instances representing HDL dependency relations"""

    # rel_type
    ENTITY = 1
    PACKAGE = 2
    ARCHITECTURE = 3
    CONTEXT = 4
    PACKAGE_BODY = 5
    MODULE = ENTITY

    def __init__(self, obj_name, lib_name, rel_type):
        assert rel_type in [
            DepRelation.ENTITY,
            DepRelation.PACKAGE,
            DepRelation.PACKAGE_BODY,
            DepRelation.ARCHITECTURE,
            DepRelation.CONTEXT,
            DepRelation.MODULE]
        self.rel_type = rel_type
        self.obj_name = obj_name.lower()
        self.lib_name = None if lib_name is None else lib_name.lower()
        # Set of DepFile provided/required by this relation.
        # A unit can be provided only by one file, but required by many.
        self.provided_by = None
        self.required_by = set()

    def satisfies(self, rel_b):
        """Check if the current dependency relation matches the provided one"""
        return (rel_b.rel_type == self.rel_type
                and rel_b.obj_name == self.obj_name
                and (self.lib_name is None or rel_b.lib_name == self.lib_name))

    def __repr__(self):
        ostr = {
            self.ENTITY: "entity",
            self.PACKAGE: "package",
            self.PACKAGE_BODY: "package body",
            self.ARCHITECTURE: "architecture",
            self.CONTEXT: "context",
            self.MODULE: "module"}
        return "%s '%s.%s'" % (ostr[self.rel_type],
                               self.lib_name or '',
                               self.obj_name)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.rel_type == other.rel_type
                and self.obj_name == other.obj_name
                and self.lib_name == other.lib_name)

    def __ne__(self, other):
        return not self.__eq__(other)


class File(object):

    """This is the base class for all of the different files in HDLMake"""

    def __init__(self, path, module=None):
        self.path = path
        assert not isinstance(module, str)
        self.module = module

    @property
    def name(self):
        """Property defined as a method that gets the basename of the file
        path, i.e. it strips the path and takes the full file name"""
        return os.path.basename(self.path)

    @property
    def purename(self):
        """Property defined as a method that gets the name of the file
        and strips put the extension from the file"""
        return os.path.splitext(self.name)[0]

    @property
    def dirname(self):
        """Property defined as a method that gets the name of the directory
        in which the file is stored"""
        return os.path.dirname(self.path)

    def rel_path(self, directory=None):
        """Returns the relative path for the file calculated with (directory)
        as the origin reference -- if none, it will be defaulted to current
        folder from which we are launching the program"""
        if directory is None:
            directory = os.getcwd()
        return path_mod.relpath(self.path, directory)

    def __str__(self):
        return self.path

    def __hash__(self):
        return hash(self.path)

    def extension(self):
        """Method that gets the extension for the file instance"""
        tmp = self.path.rsplit('.')
        ext = tmp[len(tmp) - 1]
        return ext


class ParamFile(File):
    """Class that serves as base to all parameter files.  Those files
    doesn't create or need dependencies.  Avoid a 'not parseable'
    warning"""

    def __init__(self, path, module):
        File.__init__(self, path=path, module=module)


class DepFile(File):

    """Class that serves as base to all those HDL files that can be
    parsed and solved (Verilog, SystemVerilog, VHDL).  Inherit from
    File but also provides dependencies"""

    def __init__(self, path, module):
        assert isinstance(path, str)
        File.__init__(self, path=path, module=module)
        # Relations provided/required by this file
        self.provides = set()
        self.requires = set()

        # File dependences.  Both are set of files.
        # depends_on is for file required dependency, like module if it is
        #   instantiated, packages used...
        # top_depends_on is for design dependency, like package body or
        #   architecture.  The file doesn't depend on it, but they are needed
        #   for the whole design
        self.depends_on = set()
        self.top_depends_on = set()

        self.included_files = set()
        self.dep_level = None

    def satisfies(self, rel_b):
        """Check if any of the file object relations match any of the relations
        listed in the parameter (rel_b)"""
        assert isinstance(rel_b, DepRelation)
        # self._parse_if_needed()
        return any([x.satisfies(rel_b) for x in self.provides])

    def get_dep_level(self):
        """Get the dependency level for the file instance, so we can order
        later the full fileset"""
        if self.dep_level is None:
            if len(self.depends_on) == 0:
                # No dependency for this file
                self.dep_level = 0
            else:
                # set dep_level to a negative value so we can detect
                # if the recusion below brings us back to
                # this file in a circular reference, that would otherwise
                # result in an infinite loop.
                self.dep_level = -1
                # recurse, to find the largest number of levels below.
                self.dep_level = 1 + \
                    max([dep.get_dep_level() for dep in self.depends_on])
        elif self.dep_level < 0:
            logging.warning("Probably run into a circular reference of file "
                            "dependencies. It appears %s depends on itself, "
                            "indirectly via atleast one other file.",
                            self.path)
            self.show_circular_dependency([self])
        return self.dep_level

    def show_circular_dependency(self, stack):
        for dep in self.depends_on:
            if dep is stack[0]:
                # Loop found
                for f in stack:
                    logging.warning("file %s depends on...", f)
                logging.warning("itself (%s)", dep)
                return True
        for dep in self.depends_on:
            stack.append(dep)
            if dep.show_circular_dependency(stack):
                return True
            stack.pop()
        return False


class ManualFile(DepFile):
    """Class that serves as base to binary HDL files with
    dependencies and provided units manually added by the user"""

    def __init__(self, path, module, provide=None, depends=[]):
        DepFile.__init__(self, path=path, module=module)
        self.library = module.library
        self.provide_units = provide
        self.depends_units = depends

    def extract(self, unit):
        u = unit.split('.')
        if len(u) == 1:
            ent = u[0]
            lib = self.library
        else:
            assert(len(u) == 2)
            lib = u[0]
            ent = u[1]
        return (ent, lib)

    def parse(self, graph):
        for unit in self.provide_units:
            (ent, lib) = self.extract(unit)
            graph.add_provide(self, DepRelation(ent, lib, DepRelation.ENTITY))
        for unit in self.depends_units:
            (ent, lib) = self.extract(unit)
            graph.add_require(self, DepRelation(ent, lib, DepRelation.ENTITY))
