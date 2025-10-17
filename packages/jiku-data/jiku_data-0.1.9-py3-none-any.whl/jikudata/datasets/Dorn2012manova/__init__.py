
from ... _cls import _Dataset



class Dorn2012manova(_Dataset):

    def _set_attrs(self):
        self.dim        = 1
        self.cite       = 'Dorn, T. W., Schache, A. G., & Pandy, M. G. (2012). Muscular strategy shift in human running: dependence of running speed on hip and ankle muscle performance. Journal of Experimental Biology, 215(11), 1944–1956.'
        self.www        = 'https://doi.org/10.1242/jeb.064527', 'https://simtk.org/home/runningspeeds'
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
        self.params.testname          = 'manova1'
        self.params.args              = self.y, self.x
        self.params.kwargs            = dict()
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='rft')
        
        # self.params.inference_args   = (0.05,)
        # if self._spm_version == 4:
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict()
        # else:
        #     # self.params.kwargs           = dict( _fwhm_method='spm1d-v04' )
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict(method='rft')

