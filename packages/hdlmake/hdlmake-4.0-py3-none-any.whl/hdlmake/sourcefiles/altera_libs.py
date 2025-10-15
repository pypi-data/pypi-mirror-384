# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2022 CERN
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

""" Imports names of altera system libraries. The names of these
libraries were extracted from the compilation log
of the arriaV. By running quartus library compilation:

@quartus_sh --simlib_comp -tool modelsim -language verilog -family\
arriav -directory .

one can see a list of top-level entities contained in the particular
libs. These were imported into this list. Of course the list is not
exhaustive as it was done only for arriaV, so expect in the future
another set of names to appear here"""

altera_system_libraries =\
    ["global", "carry", "cascade", "carry_sum",
     "exp", "soft", "opndrn", "row_global",
     "TRI", "lut_input", "lut_output", "latch",
     "dlatch", "dff", "dffe", "dffea",
     "dffeas", "dffeas_pr", "tff", "tffe",
     "jkff", "jkffe", "srff", "srffe",
     "clklock", "alt_inbuf", "alt_outbuf", "alt_outbuf_tri",
     "alt_iobuf", "alt_inbuf_diff", "alt_outbuf_diff",
     "alt_outbuf_tri_diff",
     "alt_iobuf_diff", "alt_bidir_diff", "alt_bidir_buf",
     "lpm_constant", "lpm_inv", "lpm_and", "lpm_or", "lpm_xor",
     "lpm_bustri", "lpm_mux", "lpm_decode", "lpm_clshift",
     "lpm_add_sub", "lpm_compare", "lpm_mult", "lpm_divide",
     "lpm_abs", "lpm_counter", "lpm_latch", "lpm_ff",
     "lpm_shiftreg", "lpm_ram_dq", "lpm_ram_dp", "lpm_ram_io",
     "lpm_rom", "lpm_fifo", "lpm_fifo_dc", "lpm_inpad",
     "lpm_outpad", "lpm_bipad", "oper_add", "oper_addsub",
     "mux21", "io_buf_tri", "io_buf_opdrn", "oper_mult",
     "tri_bus", "oper_div", "oper_mod", "oper_left_shift",
     "oper_right_shift", "oper_rotate_left",
     "oper_rotate_right", "oper_less_than",
     "oper_mux", "oper_selector", "oper_decoder", "oper_bus_mux",
     'cyclone_asmiblock', 'cycloneii_asmiblock', 'cyclonev_asmiblock',
     'stratixii_asmiblock', 'stratixiii_asmiblock', 'stratixiv_asmiblock',
     'stratixv_asmiblock',
     "oper_latch", "lcell", "altpll", "altlvds_rx",
     "altsyncram",
     "altlvds_tx", "dcfifo", "altaccumulate", "altmult_accum",
     "dcfifo_mixed_widths",
     "altmult_add", "altfp_mult", "altsqrt", "altclklock",
     "altddio_bidir", "altdpram", "alt3pram", "parallel_add",
     "scfifo", "altshift_taps", "a_graycounter", "altsquare",
     "altera_std_synchronizer_bundle", "alt_cal",
     "alt_cal_mm", "alt_cal_c3gxb",
     'arria5_phy8', 'arria5_phy16', 'arria5_phy_reconf',
     "alt_cal_sv", "alt_cal_av", "alt_aeq_s4", "alt_eyemon",
     "alt_dfe", "sld_virtual_jtag", "sld_signaltap",
     "altstratixii_oct",
     "altparallel_flash_loader", "altserial_flash_loader",
     "alt_fault_injection", "sld_virtual_jtag_basic",
     "altsource_probe", "generic_cdr", "generic_m20k", "generic_m10k",
     "common_porta_latches",
     "generic_28nm_hp_mlab_cell_impl",
     "generic_28nm_lc_mlab_cell_impl", "generic_14nm_mlab_cell_impl",
     "generic_mux", "generic_device_pll", "altera_mult_add",
     "altera_mf_components", "generic_pll", "single_region",
     "altera_pll_reconfig_tasks",
     "altera_syncram", "altera_pll", "altera_iopll", "altddio_out",
     "fourteennm_altera_iopll",
     "fourteennm_simple_iopll", "arriav_dffe",
     "altera_xcvr_native_av", "alt_xcvr_reconfig",
     "arriav_mux41",
     "arriav_and1",
     "arriav_and16", "arriav_bmux21", "arriav_b17mux21",
     "arriav_nmux21",
     "arriav_b5mux21", "arriav_ff", "arriav_lcell_comb",
     "arriav_routing_wire",
     "arriav_ram_block", "arriav_mlab_cell",
     "arriav_io_ibuf",
     "arriav_io_obuf",
     "arriav_ddio_out", "arriav_ddio_oe", "arriav_ddio_in",
     "arriav_io_pad",
     "arriav_pseudo_diff_out", "arriav_bias_block",
     "arriav_clk_phase_select", "arriav_clkena",
     "arriav_clkselect", "arriav_delay_chain",
     "arriav_dll_offset_ctrl", "arriav_dll",
     "arriav_dqs_config", "arriav_dqs_delay_chain",
     "arriav_dqs_enable_ctrl", "arriav_duty_cycle_adjustment",
     "arriav_fractional_pll", "arriav_half_rate_input",
     "arriav_input_phase_alignment", "arriav_io_clock_divider",
     "arriav_io_config", "arriav_leveling_delay_chain",
     "arriav_pll_dll_output", "arriav_pll_dpa_output",
     "arriav_pll_extclk_output", "arriav_pll_lvds_output",
     "arriav_pll_output_counter", "arriav_pll_reconfig",
     "arriav_pll_refclk_select", "arriav_termination_logic",
     'arria2_pcie_reconf', 'arria5_pcie_reconf',
     'arria2_pcie_hip', 'arria5_pcie_hip',
     "arriav_termination", "arriav_asmiblock",
     "arriav_chipidblock", "arriav_controller",
     "arriav_crcblock", "arriav_jtag",
     "arriav_prblock", "arriav_rublock",
     "arriav_tsdblock", "arriav_read_fifo",
     "arriav_read_fifo_read_enable", "arriav_phy_clkbuf",
     "arriav_serdes_dpa", "arriav_ir_fifo_userdes",
     "arriav_read_fifo_read_clock_select", "arriav_lfifo",
     "arriav_vfifo", "arriav_mac",
     "arriav_mem_phy", "arriav_oscillator",
     "arriav_hps_interface_fpga2sdram", "arriav_hssi_8g_pcs_aggregate",
     "arriav_hssi_8g_rx_pcs", "arriav_hssi_8g_tx_pcs",
     "arriav_hssi_common_pcs_pma_interface",
     "arriav_hssi_pipe_gen1_2", "arriav_hssi_pma_aux",
     "arriav_hssi_pma_int", "arriav_hssi_pma_rx_buf",
     "arriav_hssi_pma_rx_deser", "arriav_hssi_pma_tx_buf",
     "arriav_hssi_pma_tx_cgb", "arriav_hssi_pma_tx_ser",
     "arriav_hssi_pma_cdr_refclk_select_mux",
     "arriav_hssi_rx_pcs_pma_interface",
     "arriav_hssi_rx_pld_pcs_interface", "arriav_hssi_tx_pcs_pma_interface",
     "arriav_hssi_tx_pld_pcs_interface", "arriav_hssi_refclk_divider", "arriav_pll_aux", "arriav_channel_pll",
     "arriav_hssi_avmm_interface",
     "arriav_hssi_pma_hi_pmaif",
     "arriav_hssi_pma_hi_xcvrif", "arriav_hd_altpe2_hip_top"]
