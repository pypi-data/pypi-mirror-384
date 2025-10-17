
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class RSNormality(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://real-statistics.com/tests-normality-and-symmetry/statistical-tests-normality-symmetry/dagostino-pearson-test/'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'X2'
        e.z           = 1.12645
        e.df          = (1, 2)
        e.p           = 0.56937
        e.tol.z       = 1e-05
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
        self.expected = e

    def _set_params(self):
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'normality'
        self.params.args             = self.y
        self.params.inference_args   = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        


