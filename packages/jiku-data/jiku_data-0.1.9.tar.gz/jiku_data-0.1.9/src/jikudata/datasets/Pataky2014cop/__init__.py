
from ... _cls import _Dataset



class Pataky2014cop(_Dataset):

    def _set_attrs(self):
        self.dim        = 1
        self.cite       = 'Pataky, T. C., Robinson, M. A., Vanrenterghem, J., Savage, R., Bates, K. T., & Crompton, R. H. (2014). Vector field statistics for objective center-of-pressure trajectory analysis during gait, with evidence of scalar sensitivity to small coordinate system rotations. Gait and Posture, 1–4.'
        self.www        = 'https://doi.org/10.1016/j.gaitpost.2014.01.023'
        self.notes      = None

    def _set_expected(self):  # expected_results.npz loaded automatically
        self.expected.tol.z                 = 1e-5
        self.expected.tol.df                = 1e-3
        self.expected.tol.fwhm              = 1e-5
        self.expected.tol.resels            = 1e-5
        self.expected.tol.zc                = 1e-5
        self.expected.tol.p                 = 1e-5
        self.expected.tol.cluster_centroid  = 3
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
