
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class RSXLHotellings1(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.real-statistics.com/multivariate-statistics/hotellings-t-square-statistic/one-sample-hotellings-t-square/'
        self.notes      = 'data are pre-subtracted from the hypothesized mean: [7, 8, 5, 7, 9]'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T2'
        e.z           = 52.6724
        e.df          = (5, 24)
        e.p           = 0.000155
        e.tol.z       = 0.0001
        e.tol.df      = 1e-05
        e.tol.p       = 1e-06
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'hotellings'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


