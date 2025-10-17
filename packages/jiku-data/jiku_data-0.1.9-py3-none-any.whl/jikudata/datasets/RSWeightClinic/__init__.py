
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class RSWeightClinic(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://www.real-statistics.com/students-t-distribution/paired-sample-t-test/'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T'
        e.z           = 6.6896995
        e.df          = (1, 14)
        e.p           = 1.028e-05
        e.tol.z       = 1e-7
        e.tol.p       = 1e-7
        e.tol.df      = 1e-5
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'ttest_paired'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict(two_tailed=True)
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=0)


