
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Southampton2rm(_Dataset):

    def _set_attrs(self):
        self.cite       = 'Doncaster, C. P. & Davey, A. J. H. (2007) Analysis of Variance and Covariance: How to Choose and Construct Models for the Life Sciences. Cambridge: Cambridge University Press.'
        self.www        = 'https://www.southampton.ac.uk/~cpd/anovas/datasets/Doncaster&Davey%20-%20Model%206_2%20Two%20factor%20repeated%20measures.txt'

    def _set_expected(self):
        z             = (67.58, 4.13, 7.82)
        df            = ((2, 6), (1, 3), (2, 6))
        p             = (0.00008, 0.135, 0.021)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 1e-02
        e.tol.df      = 1e-05
        e.tol.p       = 1e-03
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova2rm'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)
        


