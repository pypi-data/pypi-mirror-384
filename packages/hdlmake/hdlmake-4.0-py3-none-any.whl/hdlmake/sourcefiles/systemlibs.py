#!/usr/bin/python
#
# Copyright (c) 2020 CERN
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

from .dep_file import DepRelation
from .altera_libs import altera_system_libraries

def add_entity(res, name):
    res.append(DepRelation(name, None, DepRelation.ENTITY))


def add_package(res, lib, name):
    res.append(DepRelation(name, lib, DepRelation.PACKAGE))


def build_xilinx():
    """Modules and packages provided by Xilinx system libraries"""
    res = []
    add_package(res, 'unisim', 'vcomponents')
    add_package(res, 'unimacro', 'vcomponents')
    for n in [
            'ibuf', 'ibufds', 'ibufgds', 'ibufds_diff_out', 'ibufdse3', 
            'ibufe3', 'ibufds_gte2','ibufds_gte3', 'ibufds_gte4', 'ibufds_dphy',
            'obuf', 'obufds', 'obuft', 'obuftds', 'oddr',
            'oserdes2', 'oserdese2', 'iserdese2', 'iserdes2',
            'oserdese3',
            'iodelay2', 'odelaye2', 'idelaye2', 'idelayctrl',
            'odelaye3',
            'iobuf', 'iobufds',
            'pullup', 'pulldown',
            'bufio', 'bufio2', 'bufio2fb',
            'bufgmux_ctrl', 'bufgmux', 'bufg', 'bufg_gt', 'bufgt_sync', 
            'bufgce', 'bufr', 'bufpll', 'bufmr',
            'startupe2',
            'mmcme2_adv', 'mmcme2_base', 'pll_base', 'pll_adv', 'dcm_base', 'dcm_adv', 'dcm_sp',
            'mmcme3_adv', 'mmcme3_base', 'mmcme4_adv', 'mmcme4_base',
            'plle2_adv', 'plle2_base',
            'bufpll_mcb', 'mcb', 'iodrp2', 'iodrp2_mcb',
            'mmcme3_adv',
            'mmcme4_base',
            'ibufds_gte4', 'bufg_gt', 'gthe4_common', 'gthe4_channel',
            'icap_spartan6', 'bscan_spartan6',
            'gtxe2_channel', 'gtxe2_common', 'gtpa1_dual',
            'gthe3_channel', 'gthe3_common', 'gthe4_channel', 'gthe4_common',
            'gtye3_channel', 'gtye3_common', 'gtye4_channel', 'gtye4_common',
            'dsp48a1', 'dsp48e2',
            'lut1', 'lut2', 'lut3', 'lut4', 'lut5', 'lut6', 'lut6_2',
            'fdre', 'fdce', 'fdpe', 'fdse',
            'muxf7', 'muxf8', 'muxf9', 'carry4',
            'vcc', 'gnd',
            'srlc32e', 'usr_accesse2',
            'xpm_cdc_array_single', 'xpm_cdc_async_rst', 'xpm_cdc_gray',
            'xpm_cdc_handshake', 'xpm_cdc_pulse', 'xpm_cdc_single',
            'xpm_cdc_sync_rst', 'xpm_fifo_async', 'xpm_fifo_axif',
            'xpm_fifo_axil', 'xpm_fifo_axis', 'xpm_fifo_sync',
            'xpm_memory_dpdistram', 'xpm_memory_dprom', 'xpm_memory_sdpram',
            'xpm_memory_spram', 'xpm_memory_sprom', 'xpm_memory_tdpram',
        ]:
        add_entity(res, n)
    return res

def build_altera():
    res = []

    add_package(res, 'altera_mf', 'altera_mf_components')
    add_package(res, 'altera', 'altera_primitives_components')
    add_package(res, 'lpm', 'lpm_components')

    for n in altera_system_libraries:
        add_entity(res, n)
    return res

def build_smartfusion2():
    res = []
    for n in ['xtlosc', 'xtlosc_fab', 'ccc', 'sysreset',
              'clkint',
              'inbuf', 'outbuf', 'tribuff',
              'gnd', 'vcc',
              'mss_075']:
        add_entity(res, n)
    return res

def build_vhdl():
    res = []
    # TODO: dependency for any package of a library.
    for p in ['textio', 'env']:
        add_package(res, "std", p)
    for p in ['std_logic_1164', 'numeric_std',
              'math_real',
              'std_logic_arith', 'std_logic_misc']:
        add_package(res, "ieee", p)
    return res

all_system_libs = {
    'xilinx': build_xilinx,
    'vhdl': build_vhdl,
    'altera': build_altera,
    'smartfusion2': build_smartfusion2
}
