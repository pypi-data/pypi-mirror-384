
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class RSItalian(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.real-statistics.com/two-way-anova/anova-more-than-two-factors/'

    def _set_expected(self):
        z             = (0.01749, 16.8113, 0.51854, 0.70169, 9.2541, 0.47708, 26.6077)
        df            = [(1, 88), (1, 88), (1, 88), (1, 88), (1, 88), (1, 88), (1, 88)]
        p             = (0.89508, 9.2e-05, 0.47337, 0.40449, 0.0031, 0.49157, 1.5e-06)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.0001
        e.tol.df      = 1e-05
        e.tol.p       = 1e-05
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova3'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


