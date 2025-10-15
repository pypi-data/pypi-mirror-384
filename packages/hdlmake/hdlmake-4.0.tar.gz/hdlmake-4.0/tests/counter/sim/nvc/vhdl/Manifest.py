action = "simulation"
sim_tool = "nvc"
sim_top = "counter_tb"

sim_post_cmd = "nvc -r counter_tb --stop-time=6us --format=vcd --wave=counter_tb.vcd"

modules = {
  "local" : [ "../../../testbench/counter_tb/vhdl" ],
}
