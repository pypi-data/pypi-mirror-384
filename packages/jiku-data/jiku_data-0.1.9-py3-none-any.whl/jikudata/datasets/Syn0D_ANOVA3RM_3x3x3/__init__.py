
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Syn0D_ANOVA3RM_3x3x3(_Dataset):

    def _set_attrs(self):
        self.www        = None

    def _set_expected(self):
        z             = (0.042, 3.394, 0.0, 1.048, 1.379, 2.123, 0.666)
        df            = ((2, 14), (2, 14), (2, 14), (4, 28), (4, 28), (4, 28), (8, 56))
        p             = (0.959, 0.0628, 1.0, 0.401, 0.266, 0.104, 0.719)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.001
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'anova3rm'
        self.params.args             = self.y, self.x
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')

