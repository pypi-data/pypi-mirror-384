
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Syn0D_ANOVA2ONERM_3x5(_Dataset):

    def _set_attrs(self):
        self.www        = None

    def _set_expected(self):
        z             = (1.806, 0.678, 0.799)
        df            = ((2, 18), (4, 72), (8, 72))
        p             = (0.193, 0.609, 0.606)
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

