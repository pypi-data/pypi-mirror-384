
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class ConstructionUnequalSampleSizes(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://stackoverflow.com/questions/8320603/how-to-do-one-way-anova-in-r-with-unequal-sample-sizes'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'F'
        e.z           = 3.4971
        e.df          = (3, 24)
        e.p           = 0.03098
        e.tol.z       = 0.0001
        e.tol.df      = 1e-05
        e.tol.p       = 1e-05
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'anova1'
        self.params.args             = self.y, self.x
        self.params.kwargs           = dict(equal_var=True)
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')
        


