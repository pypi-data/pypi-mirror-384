
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class RSRegression(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://www.real-statistics.com/regression/hypothesis-testing-significance-regression-line-slope/'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T'
        e.z           = -3.67092
        e.df          = (1, 13)
        e.p           = 0.002822
        e.tol.z       = 1e-05
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'regress'
        self.params.args             = self.y, self.x
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict(two_tailed=True)
        self.params.inference_kwargs5 = dict(method='param', dirn=0)
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict(two_tailed=True)
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=0)


