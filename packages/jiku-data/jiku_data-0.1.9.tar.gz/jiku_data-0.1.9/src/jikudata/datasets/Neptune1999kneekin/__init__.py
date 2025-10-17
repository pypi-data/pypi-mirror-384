
from ... _cls import _Dataset



class Neptune1999kneekin(_Dataset):

    def _set_attrs(self):
        self.dim        = 1
        self.cite       = 'Neptune, R. R., Wright, I. C., & van den Bogert, A. J. (1999). Muscle coordination and function during cutting movements. Medicine & Science in Sports & Exercise, 31(2), 294–302.'
        self.www        = 'https://doi.org/10.1097/00005768-199902000-00014', 'https://isbweb.org/data/rrn/'
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
        self.params.testname          = 'hotellings_paired'
        self.params.args              = self.y, self.x
        self.params.inference_args    = (0.05,)
        self.params.kwargs            = dict()
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='rft')
        
        
        # if self._spm_version == 4:
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict()
        # else:
        #     # self.params.kwargs           = dict( _fwhm_method='spm1d-v04' )
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict(method='rft')
