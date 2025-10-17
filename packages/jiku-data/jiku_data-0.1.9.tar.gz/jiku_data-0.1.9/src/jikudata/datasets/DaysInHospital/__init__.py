
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class DaysInHospital(_Dataset):

    def _set_attrs(self):
        self.www       = 'https://github.com/nipy/nipy/blob/main/nipy/algorithms/statistics/models/tests/test_anova.py'
        self.notes     = 'nipy example dataset; originally from "Applied Linear Statistical Models" textbook'

    def _set_expected(self):
        z             = (7.2147, 13.1210, 1.8813)
        df            = ((1, 54), (2, 54), (2, 54))
        p             = (0.009587, 0.00002269, 0.162240)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 1e-3
        e.tol.df      = 1e-5
        e.tol.p       = 1e-5
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova2'
        self.params.args              = self.y, self.x
        self.params.kwargs            = dict(equal_var=True,)
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')



