
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class FitnessClub(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://support.sas.com/documentation/cdl/en/statug/63033/HTML/default/viewer.htm#statug_cancorr_sect020.htm'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'X2'
        e.z           = 5.1458
        e.df          = (1, 3)
        e.p           = 0.1614
        e.tol.z       = 0.0001
        e.tol.df      = 1e-05
        e.tol.p       = 0.0001
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'cca'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')


