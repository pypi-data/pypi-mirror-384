
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class RSUnequalSampleSizes(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://real-statistics.com/wp-content/uploads/2020/09/one-way-anova-unbalanced.png'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'F'
        e.z           = 5.864845
        e.df          = (3, 38)
        e.p           = 0.00215
        e.tol.z       = 1e-06
        e.tol.df      = 1e-05
        e.tol.p       = 1e-05
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova1'
        self.params.args              = self.y, self.x
        self.params.kwargs            = dict(equal_var=True)
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


