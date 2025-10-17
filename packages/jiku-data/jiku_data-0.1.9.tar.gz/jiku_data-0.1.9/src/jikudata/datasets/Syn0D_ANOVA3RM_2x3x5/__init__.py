
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Syn0D_ANOVA3RM_2x3x5(_Dataset):

    def _set_attrs(self):
        self.www        = None

    def _set_expected(self):
        z             = (0.387, 1.195, 0.272, 0.064, 0.695, 0.88, 0.75)
        df            = ((1, 11), (2, 22), (4, 44), (2, 22), (4, 44), (8, 88), (8, 88))
        p             = (0.547, 0.322, 0.895, 0.938, 0.6, 0.537, 0.648)
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

