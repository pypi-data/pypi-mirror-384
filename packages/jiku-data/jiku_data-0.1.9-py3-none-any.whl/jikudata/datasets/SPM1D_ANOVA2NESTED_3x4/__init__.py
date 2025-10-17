
from ... _cls import _Dataset



class SPM1D_ANOVA2NESTED_3x4(_Dataset):

    def _set_attrs(self):
        self.dim        = 1
        self.cite       = None
        self.www        = None
        self.notes      = None

    def _set_expected(self):  # expected_results.npz loaded automatically
        self.expected.tol.z                 = 1e-5
        self.expected.tol.df                = 1e-3
        self.expected.tol.fwhm              = 1e-5
        self.expected.tol.resels            = 1e-5
        self.expected.tol.zc                = 1e-5
        self.expected.tol.p                 = 1e-5
        self.expected.tol.cluster_centroid  = 0.5
        self.expected.tol.cluster_endpoints = 1e-5
        self.expected.tol.cluster_extent    = 1e-5
        self.expected.tol.cluster_p         = 1e-5

    def _set_params(self):
        from ... _cls import ParametersSPM1D
        self.params                  = ParametersSPM1D()
        self.params.testname         = 'anova2nested'
        self.params.args             = self.y, self.x
        self.params.inference_args   = (0.05,)
        self.params.kwargs            = dict(equal_var=True)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='rft')
        
        # if self._spm_version == 4:
        #     self.params.kwargs           = dict(equal_var=True)
        #     self.params.inference_kwargs = dict()
        # else:
        #     # self.params.kwargs           = dict(equal_var=True, _fwhm_method='spm1d-v04' )
        #     self.params.kwargs           = dict( equal_var=True )
        #     self.params.inference_kwargs = dict(method='rft')
