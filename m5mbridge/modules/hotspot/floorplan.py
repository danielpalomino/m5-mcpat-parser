'''This file stores the floorplan we use for hotspot.

Unfortunately the Gem5 build system has no support for additional files and
thus there's no easy way to copy files like a floor plan into the build
directory of Gem5, where all source files are copied to. Instead of using an
ordinary file, we use a Python file to store the floorplan as a string and load
the floorplan for Hotspot from it.
'''

flp = '''
# Floorplan close to the Alpha EV6 processor
# Line Format: <unit-name>\t<width>\t<height>\t<left-x>\t<bottom-y>
# all dimensions are in meters
# comment lines begin with a '#'
# comments and empty lines are ignored

L2_left	0.004900	0.006200	0.000000	0.009800
L2	0.016000	0.009800	0.000000	0.000000
L2_right	0.004900	0.006200	0.011100	0.009800
Icache	0.003100	0.002600	0.004900	0.009800
Dcache	0.003100	0.002600	0.008000	0.009800
Bpred_0	0.001033	0.000700	0.004900	0.012400
Bpred_1	0.001033	0.000700	0.005933	0.012400
Bpred_2	0.001033	0.000700	0.006967	0.012400
DTB_0	0.001033	0.000700	0.008000	0.012400
DTB_1	0.001033	0.000700	0.009033	0.012400
DTB_2	0.001033	0.000700	0.010067	0.012400
FPAdd_0	0.001100	0.000900	0.004900	0.013100
FPAdd_1	0.001100	0.000900	0.006000	0.013100
FPReg_0	0.000550	0.000380	0.004900	0.014000
FPReg_1	0.000550	0.000380	0.005450	0.014000
FPReg_2	0.000550	0.000380	0.006000	0.014000
FPReg_3	0.000550	0.000380	0.006550	0.014000
FPMul_0	0.001100	0.000950	0.004900	0.014380
FPMul_1	0.001100	0.000950	0.006000	0.014380
FPMap_0	0.001100	0.000670	0.004900	0.015330
FPMap_1	0.001100	0.000670	0.006000	0.015330
IntMap	0.000900	0.001350	0.007100	0.014650
IntQ	0.001300	0.001350	0.008000	0.014650
IntReg_0	0.000900	0.000670	0.009300	0.015330
IntReg_1	0.000900	0.000670	0.010200	0.015330
IntExec	0.001800	0.002230	0.009300	0.013100
FPQ	0.000900	0.001550	0.007100	0.013100
LdStQ	0.001300	0.000950	0.008000	0.013700
ITB_0	0.000650	0.000600	0.008000	0.013100
ITB_1	0.000650	0.000600	0.008650	0.013100
'''
