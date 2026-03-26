from frcm.METKlient import hent_weatherdata_fra_met
from frcm.fireriskmodel.compute import compute

wd = hent_weatherdata_fra_met(60.3691, 5.3495)
prediction = compute(wd)

print(prediction)