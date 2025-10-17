
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D
# from ... io import load_csv



class RSWeightReduction(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://www.real-statistics.com/students-t-distribution/one-sample-t-test/'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T'
        e.z           = 1.449255
        e.df          = 1, 11
        e.p           = 0.087585
        e.tol.z       = 1e-5
        e.tol.p       = 1e-5
        e.tol.df      = 1e-5
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'ttest'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict(two_tailed=False)
        self.params.inference_kwargs5 = dict(method='param', dirn=1)
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict(two_tailed=False)
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)


