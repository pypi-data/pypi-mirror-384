import os

openkimmodel = "EMT_Asap_Standard_JacobsenStoltzeNorskov_1996_AlAgAuCuNiPdPt__MO_115316750986_001"

if 'ASAP_KIM_DIR' in os.environ:
    _d = os.path.join(os.environ['ASAP_KIM_DIR'], 'src/models')
elif 'ASAP_KIM_LIB' in os.environ:
    _d  = os.path.join(os.environ['ASAP_KIM_LIB'], 'kim-api/models')
elif 'KIM_HOME' in os.environ:
    _d  = os.path.join(os.environ['KIM_HOME'], 'lib/kim-api/models')
else:
    _d = None

if _d is not None and os.path.exists(_d):
    openkimmodels = [x for x in os.listdir(_d) if os.path.isdir(os.path.join(_d,x))]
    openkimmodels.sort()
else:
    openkimmodels = []
    
if __name__ == "__main__":
    print(openkimmodels)
    print("\n\nThis it not a test, but a module imported from a few tests.")
    
    
