
from ... _cls import _Dataset



class SpeedGRFcategoricalRM(_Dataset):

    def _set_attrs(self):
        self.dim        = 1
        self.cite       = 'Pataky, T. C., Caravaggi, P., Savage, R., Parker, D., Goulermas, J., Sellers, W., & Crompton, R. (2008). New insights into the plantar pressure correlates of walking speed using pedobarographic statistical parametric mapping (pSPM). Journal of Biomechanics, 41(9), 1987–1994.'
        self.www        = 'https://doi.org/10.1016/j.jbiomech.2008.03.034'
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
        self.params.testname          = 'anova1rm'
        self.params.args              = self.y, self.x
        self.params.kwargs            = dict(equal_var=True)
        self.params.inference_kwargs4 = dict()
        self.params.inference_kwargs5 = dict(method='rft')
        
        # if self._spm_version == 4:
        #     self.params.kwargs           = dict(equal_var=True)
        #     self.params.inference_kwargs = dict()
        # else:
        #     # self.params.kwargs           = dict( equal_var=True, _fwhm_method='spm1d-v04' )
        #     self.params.kwargs           = dict( equal_var=True )
        #     self.params.inference_kwargs = dict(method='rft')
