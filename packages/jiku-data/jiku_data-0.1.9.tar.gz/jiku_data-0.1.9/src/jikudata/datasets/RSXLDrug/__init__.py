
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class RSXLDrug(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://www.real-statistics.com/anova-repeated-measures/one-between-subjects-factor-and-one-within-subjects-factor/'

    def _set_expected(self):
        z             = (8.301316, 114.6323, 2.164584)
        df            = ((2, 18), (4, 72), (8, 72))
        p             = (0.002789, 1.91e-30, 0.040346)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.0001
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova2onerm'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


