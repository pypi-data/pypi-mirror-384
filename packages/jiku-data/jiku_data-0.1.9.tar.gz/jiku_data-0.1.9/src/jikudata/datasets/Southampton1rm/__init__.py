
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsSPM1D, ParametersSPM1D



class Southampton1rm(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.southampton.ac.uk/~cpd/anovas/datasets/Doncaster&Davey%20-%20Model%206_1%20One%20factor%20repeated%20measures.txt'

    def _set_expected(self):
        e             = ExpectedResultsSPM1D()
        e.STAT        = 'F'
        e.z           = 12.36
        e.df          = (2, 6)
        e.p           = 0.007
        e.tol.z       = 0.01
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova1rm'
        self.params.args              = self.y, self.x
        self.params.kwargs            = dict(equal_var=True)
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)
        


