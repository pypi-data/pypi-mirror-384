
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Antidepressant(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.pc.rhul.ac.uk/staff/J.Larsson/teaching/pdfs/repeatedmeasures.pdf'

    def _set_expected(self):
        z             = (1.459, 530.842, 192.667)
        df            = ((1, 3), (1, 3), (1, 3))
        p             = (0.314, 0.0, 0.001)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.001
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'anova2rm'
        self.params.args             = self.y, self.x
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')



