
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class RSXLHotellings2(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.real-statistics.com/multivariate-statistics/hotellings-t-square-statistic/hotellings-t-square-independent-samples/'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T2'
        e.z           = 4.116057
        e.df          = (3, 36)
        e.p           = 0.291687
        e.tol.z       = 1e-06
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
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


