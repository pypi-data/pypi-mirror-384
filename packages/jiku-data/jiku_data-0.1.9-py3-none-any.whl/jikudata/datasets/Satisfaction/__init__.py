
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Satisfaction(_Dataset):

    def _set_attrs(self):
        self.www        = 'http://www2.webster.edu/~woolflm/8canswer.html'

    def _set_expected(self):
        z             = (16.36, 49.09, 0.0)
        df            = ((1, 24), (2, 24), (2, 24))
        p             = (0.00047, 3.3e-09, 1.0)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.01
        e.tol.df      = 1e-05
        e.tol.p       = 1e-05
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova2'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


