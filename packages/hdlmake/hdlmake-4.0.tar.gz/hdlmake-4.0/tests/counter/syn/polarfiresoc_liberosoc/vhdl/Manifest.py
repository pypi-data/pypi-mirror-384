target = "microsemi"
action = "synthesis"

syn_family = "PolarFireSoC"
syn_device = "MPFS250T_ES"
syn_grade = ""
syn_package = "FCVG484"
syn_top = "polarfiresoc_top"
syn_project = "test"
syn_tool = "liberosoc"

modules = {
  "local" : [ "../../../top/polarfire_sk/vhdl" ],
}


