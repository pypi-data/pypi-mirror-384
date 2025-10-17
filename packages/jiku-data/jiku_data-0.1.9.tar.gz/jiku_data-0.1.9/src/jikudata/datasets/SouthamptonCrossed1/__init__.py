
import os
import numpy as np
from ... _cls import _Dataset, ExpectedResultsListSPM1D, ParametersSPM1D



class SouthamptonCrossed1(_Dataset):

    def _set_attrs(self):
        self.cite       = 'Doncaster, C. P. & Davey, A. J. H. (2007) Analysis of Variance and Covariance: How to Choose and Construct Models for the Life Sciences. Cambridge: Cambridge University Press.'
        self.www        = 'https://www.southampton.ac.uk/~cpd/anovas/datasets/Doncaster&Davey%20-%20Model%203_1%20Two%20factor%20fully%20cross%20factored.txt'

    def _set_expected(self):
        z             = (37.23, 9.16, 9.31)
        df            = ((2, 18), (1, 18), (2, 18))
        p             = (4.016e-07, 0.007, 0.002)
        e             = ExpectedResultsListSPM1D('F', z, df, p)
        e.tol.z       = 0.01
        e.tol.df      = 1e-05
        e.tol.p       = 0.001
        self.expected = e

    def _set_params(self):
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'anova2'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='param')
        
        # if self._spm_version == 4:
        #     self.params.inference_kwargs = dict()
        # else:
        #     self.params.inference_kwargs = dict(method='param')
        


