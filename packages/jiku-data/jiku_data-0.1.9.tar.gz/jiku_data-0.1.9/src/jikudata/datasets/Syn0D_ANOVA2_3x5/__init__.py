
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Syn0D_ANOVA2_3x5(_Dataset):

    def _set_attrs(self):
        self.www        = None

    def _set_expected(self):
        z             = (2.066, 0.654, 0.77)
        df            = ((2, 90), (4, 90), (8, 90))
        p             = (0.133, 0.626, 0.63)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.001
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'anova2'
        self.params.args             = self.y, self.x
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')

