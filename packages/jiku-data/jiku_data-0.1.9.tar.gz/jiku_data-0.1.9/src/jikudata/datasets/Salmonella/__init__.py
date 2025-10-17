
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D
# from ... io import load_csv



class Salmonella(_Dataset):

    def _set_attrs(self):

        self.www        = 'https://github.com/vaitybharati/P17.-Hypothesis-Testing-1-Sample-1-Tail-Test-Salmonella-Outbreak-'

    def _set_data(self, _load_data=True):
        super()._set_data( _load_data=_load_data )
        self.x          = 0.3  # mu (hypothesized value)

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'T'
        e.z           = 2.2050588385131595
        e.df          = 1, 8
        e.p           = 0.029265164842448822
        e.tol.z       = 1e-9
        e.tol.p       = 1e-5
        e.tol.df      = 1e-9
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'ttest'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict(two_tailed=False)
        self.params.inference_kwargs5 = dict(method='param', dirn=1)
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict(two_tailed=False)
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)


