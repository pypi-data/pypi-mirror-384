import jikudata as jd



# dataset   = jd.AnimalDepression()
dataset   = jd.RSFlavor()
# dataset   = jd.ConstructionUnequalSampleSizes()
# dataset   = jd.Groceries()
# dataset   = jd.PlantarArchAngle()
# dataset   = jd.SpeedGRFcategoricalRM()
# dataset   = jd.Random()
# dataset   = jd.SPM1D_ANOVA2_2x2()
print( dataset )

y   = dataset.y
x   = dataset.x

spm = dataset.run(  kwargs=dict(equal_var=True)  )

dataset.runtest()
