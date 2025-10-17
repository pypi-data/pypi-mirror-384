
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Syn0D_ANOVA3RM_2x2x2(_Dataset):

    def _set_attrs(self):
        self.www        = None

    def _set_expected(self):
        z             = (0.393, 2.286, 0.136, 0.05, 0.083, 0.958, 0.01)
        df            = ((1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4), (1, 4))
        p             = (0.565, 0.205, 0.731, 0.834, 0.788, 0.383, 0.924)
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

