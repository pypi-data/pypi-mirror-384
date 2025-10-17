
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class SouthamptonFullyCrossedMixed(_Dataset):

    def _set_attrs(self):
        self.cite       = 'Doncaster, C. P. & Davey, A. J. H. (2007) Analysis of Variance and Covariance: How to Choose and Construct Models for the Life Sciences. Cambridge: Cambridge University Press.'
        self.www        = 'https://www.southampton.ac.uk/~cpd/anovas/datasets/Doncaster&Davey%20-%20Model%203_2%20Three%20factor%20fully%20cross%20factored.txt'

    def _set_expected(self):
        z             = (38.12, 0.02, 0.99, 7.06, 0.42, 0.92, 2.06)
        df            = ((2, 12), (1, 12), (1, 12), (2, 12), (2, 12), (1, 12), (2, 12))
        p             = (1e-05, 0.902, 0.338, 0.009, 0.665, 0.357, 0.171)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.01
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova3'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)
        #


