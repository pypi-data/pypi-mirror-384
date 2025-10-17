
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class Southampton3tworm(_Dataset):

    def _set_attrs(self):
        self.cite       = 'Doncaster, C. P. & Davey, A. J. H. (2007) Analysis of Variance and Covariance: How to Choose and Construct Models for the Life Sciences. Cambridge: Cambridge University Press.'
        self.www        = 'https://www.southampton.ac.uk/~cpd/anovas/datasets/Doncaster&Davey%20-%20Model%206_5%20Three%20factor%20model%20with%20RM%20on%20two%20cross%20factors.txt'

    def _set_expected(self):
        z             = (44.34, 0.01, 1.1, 5.21, 0.47, 1.04, 2.33)
        df            = ((2, 3), (1, 3), (1, 3), (2, 3), (2, 3), (1, 3), (2, 3))
        p             = (0.006, 0.921, 0.371, 0.106, 0.666, 0.383, 0.245)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.01
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova3tworm'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param', dirn=1)
        


