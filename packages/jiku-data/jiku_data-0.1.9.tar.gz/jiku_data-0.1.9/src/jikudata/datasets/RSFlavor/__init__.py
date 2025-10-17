
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResults, ExpectedResultsSPM1D, ParametersSPM1D



class RSFlavor(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://www.real-statistics.com/students-t-distribution/two-sample-t-test-equal-variances/'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T'
        e.z           = 2.176768
        e.df          = (1, 18)
        e.p           = 0.021526
        e.tol.z       = 1e-06
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'ttest2'
        self.params.args              = self.y, self.x
        self.params.kwargs            = dict(equal_var=True)
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict(two_tailed=False)
        self.params.inference_kwargs5 = dict(method='param', dirn=1)
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict(two_tailed=False)
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)


