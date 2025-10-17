
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class HELPHomeless(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://sas-and-r.blogspot.jp/2010/05/example-737-calculation-of-hotellings.html'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T2'
        e.z           = 6.132267
        e.df          = (3, 451)
        e.p           = 0.1082217
        e.tol.z       = 1e-06
        e.tol.df      = 1e-05
        e.tol.p       = 1e-07
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'hotellings2'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')



