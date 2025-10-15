files = [
    "zedboard_top.v",
    "sync_reset.v",
]

constraints = [
    "../zedboard_top.xdc",
    "../sync_reset.tcl",
]

modules = {
  "local" : [ "../../../modules/counter/verilog" ],
}
