
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class RSXLTraining(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.real-statistics.com/anova-repeated-measures/two-within-subjects-factors/'

    def _set_expected(self):
        z             = (33.85228, 26.95919, 12.63227)
        df            = ((1, 9), (2, 18), (2, 18))
        p             = (0.000254, 3.85e-06, 0.000373)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 1e-05
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova2rm'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


