
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D


_notes = '''
Originally accessed from the following link (unavailable as of 2023-01-30):
http://www.pearsonhighered.com/assets/hip/gb/uploads/Mayers_IntroStatsSPSS_Ch14.pdf

Results verified in MATLAB using manova1
'''

class AnimalDepression(_Dataset):

    def _set_attrs(self):
        self.www        = None
        self.notes      = _notes

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'X2'
        e.z           = 23.8481
        e.df          = (1, 4)
        e.p           = 8.5673e-05
        e.tol.z       = 0.0001
        e.tol.df      = 1e-05
        e.tol.p       = 1e-09
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'manova1'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')

