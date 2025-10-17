
import numpy as np
from ... _cls import _Dataset



class SpeedPP2DS(_Dataset):

    def __init__(self, subj=None):
        self._subj      = subj
        super().__init__()
    
    @staticmethod
    def _loadh5( fpath ):
        import tables
        with tables.open_file(fpath, mode='r') as f:
            ylist    = []
            for i in range(60):
                node = f.get_node( f'/img{i:03}' )
                y    = np.asarray( node.read(), node.atom.dtype )
                ylist.append( y )
        return np.asarray( ylist )

    def _set_attrs(self):
        self._autotest  = False
        self.dim        = 3
        self.cite       = 'Pataky, T. C., Caravaggi, P., Savage, R., Parker, D., Goulermas, J., Sellers, W., & Crompton, R. (2008). New insights into the plantar pressure correlates of walking speed using pedobarographic statistical parametric mapping (pSPM). Journal of Biomechanics, 41(9), 1987–1994.'
        self.www        = 'https://doi.org/10.1016/j.jbiomech.2008.03.034'
        self.notes      = None

    def _set_data(self):
        import os
        dir0         = os.path.dirname(__file__)
        dir_x        = os.path.join( dir0, 'data_x' )
        dir_y        = os.path.join( dir0, 'data_y' )
        fpath_conds  = os.path.join( dir_x, 'conditions.csv' )
        fpath_speeds = os.path.join( dir_x, 'speeds.csv' )

        if self._subj is None:
            self.y   = np.vstack(   [self._loadh5(  os.path.join( dir_y, f'subj{subj:03}.h5')  )  for subj in range(10)]   )
            subj     = np.hstack([[i]*60  for i in range(10)])
            cond     = np.hstack(   np.loadtxt(fpath_conds,  delimiter=',', skiprows=1, dtype=int).T[1:]   )
            speed    = np.hstack(   np.loadtxt(fpath_speeds, delimiter=',', skiprows=1).T[1:]   )
            
        else:
            fpath    = os.path.join( dir_y, f'subj{self._subj:03}.h5')
            self.y   = self._loadh5( fpath )
            subj     = np.asarray( [self._subj] * 60 )
            cond     = np.loadtxt(fpath_conds,  delimiter=',', skiprows=1, dtype=int)[:,1+self._subj]
            speed    = np.loadtxt(fpath_speeds, delimiter=',', skiprows=1)[:,1+self._subj]

        self.x   = dict(subj=subj, cond=cond, speed=speed)


    def _set_expected(self):  # expected_results.npz loaded automatically
        pass  # auto-testing not yet implemented!! 
        # self.expected.tol.z                 = 1e-5
        # self.expected.tol.df                = 1e-3
        # self.expected.tol.fwhm              = 1e-5
        # self.expected.tol.resels            = 1e-5
        # self.expected.tol.zc                = 1e-5
        # self.expected.tol.p                 = 1e-5
        # self.expected.tol.cluster_centroid  = 1e-5
        # self.expected.tol.cluster_endpoints = 1e-5
        # self.expected.tol.cluster_extent    = 1e-5
        # self.expected.tol.cluster_p         = 1e-5

    def _set_params(self):
        pass  # auto-testing not yet implemented!! 
        # from ... _cls import ParametersSPM1D
        # self.params                  = ParametersSPM1D()
        # self.params.testname         = 'regress'
        # self.params.args             = self.y, self.x
        # self.params.inference_args   = (0.05,)
        # if self._spm_version == 4:
        #     self.params.kwargs           = dict()
        #     self.params.inference_kwargs = dict(two_tailed=True)
        # else:
        #     self.params.kwargs           = dict( _fwhm_method='spm1d-v04' )
        #     self.params.inference_kwargs = dict(method='rft', dirn=0)
