"""BLOCKS required for LLNL thermo database."""

NAMED_EXPRESSIONS = """
NAMED_EXPRESSIONS
#
# formation of O2 from H2O
# 2H2O =  O2 + 4H+ + 4e-
#
    Log_K_O2
        log_k      -85.9951
        -delta_H	559.543	kJ/mol	# Calculated enthalpy of reaction	O2
#	Enthalpy of formation:	-2.9 kcal/mol
            -analytic   38.0229    7.99407E-03   -2.7655e+004  -1.4506e+001  199838.45
#	Range:  0-300
"""

LLNL_AQUEOUS_MODEL_PARAMETERS = """
LLNL_AQUEOUS_MODEL_PARAMETERS
-temperatures
         0.0100   25.0000   60.0000  100.0000
       150.0000  200.0000  250.0000  300.0000
#debye huckel a (adh)
-dh_a
         0.4939    0.5114    0.5465    0.5995
         0.6855    0.7994    0.9593    1.2180
#debye huckel b (bdh)
-dh_b
         0.3253    0.3288    0.3346    0.3421
         0.3525    0.3639    0.3766    0.3925
-bdot
         0.0374    0.0410    0.0438    0.0460
         0.0470    0.0470    0.0340    0.0000
#cco2   (coefficients for the Drummond (1981) polynomial)
-co2_coefs
        -1.0312              0.0012806
          255.9                 0.4445
      -0.001606
"""
