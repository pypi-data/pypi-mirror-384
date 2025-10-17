
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Syn0D_ANOVA2ONERM_3x3(_Dataset):

    def _set_attrs(self):
        self.www        = None

    def _set_expected(self):
        z             = (0.204, 0.04, 1.832)
        df            = ((2, 12), (2, 24), (4, 24))
        p             = (0.819, 0.961, 0.156)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.001
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'anova2onerm'
        self.params.args             = self.y, self.x
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')

