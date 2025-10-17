
import jikudata as jd


# for dataset in jd.datasets.iter_all():
# 	dataset.runtest( verbose=True )



# for dataset in jd.datasets.iter_all():
# 	if dataset.dim == 0:
# 		if dataset.name == 'SPM1D_ANOVA3ONERM_2x3x4':
# 			continue
# 		dataset.runtest( verbose=True )


def test_all():
    for dataset in jd.datasets.iter_all():
        if dataset._autotest:
            if dataset.params.testname in ['ttest', 'ttest_paired', 'ttest2', 'anova1']:
                dataset.runtest( verbose=True, spm1d_version=None )

# test_all()