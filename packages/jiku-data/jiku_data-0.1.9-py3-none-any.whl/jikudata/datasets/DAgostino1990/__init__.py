
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class DAgostino1990(_Dataset):

    def _set_attrs(self):

        self.www        = 'http://www.jstor.org/stable/2684359'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'X2'
        e.z           = 14.75
        e.df          = (1, 2)
        e.p           = 0.0006
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
        


