
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Southampton3onerm(_Dataset):

    def _set_attrs(self):
        self.www        = 'https://www.southampton.ac.uk/~cpd/anovas/datasets/Doncaster&Davey%20-%20Model%206_7%20Three%20factor%20model%20with%20RM%20on%20a%20cross%20factor.txt'

    def _set_expected(self):
        z             = (34.42, 0.01, 1.11, 6.37, 0.47, 1.03, 2.3)
        df            = ((2, 6), (1, 6), (1, 6), (2, 6), (2, 6), (1, 6), (2, 6))
        p             = (0.001, 0.909, 0.332, 0.033, 0.645, 0.35, 0.181)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.01
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova3onerm'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)
        


