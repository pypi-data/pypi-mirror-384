
from ... _cls import _Dataset



class Random(_Dataset):

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
        self.expected.tol.cluster_centroid  = 1e-5
        self.expected.tol.cluster_endpoints = 1e-5
        self.expected.tol.cluster_extent    = 1e-5
        self.expected.tol.cluster_p         = 1e-5

    def _set_params(self):
        from ... _cls import ParametersSPM1D
        self.params                   = ParametersSPM1D()
        self.params.testname          = 'ttest'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.kwargs            = dict()
        self.params.inference_kwargs4 = dict(two_tailed=False)
        self.params.inference_kwargs5 = dict(method='rft', dirn=1)
        
        # if self._spm_version == 4:
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict(two_tailed=False)
        # else:
        #     # self.params.kwargs           = dict( _fwhm_method='spm1d-v04' )
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict(method='rft', dirn=1)
