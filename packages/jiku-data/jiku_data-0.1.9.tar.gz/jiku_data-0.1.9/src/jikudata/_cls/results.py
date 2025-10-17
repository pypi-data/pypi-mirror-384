
from .. util import DisplayParams, array2shortstr, dflist2str, tuple2str, possiblytuple2str


class Tolerance(object):  # absolite tolerance (for unit tests)
    def __init__(self):
        self.z        = 1e-5

    def __repr__(self):
        return self.asstr()

    def asstr(self, indent=0, verbose=True):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'z' )
        return dp.asstr(indent=indent)

class ToleranceSPM1D(object):  # absolite tolerance (for unit tests)
    def __init__(self):
        self.z        = 1e-5
        self.p        = 1e-5
        self.df       = 1e-5

    def __repr__(self):
        return self.asstr()

    def asstr(self, indent=0, verbose=True):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'z' )
        dp.add( 'df' )
        dp.add( 'p' )
        return dp.asstr(indent=indent)



class ExpectedResults(object):

    def __init__(self):
        self.dim  = 0
        self.STAT = 'Z'    # test statistic
        self.z    = None   # expected test stat
        self.tol  = Tolerance()


    def __eq__(self, results):
        try:
            self.assert_equal(results)
            return True
        except AssertionError:
            return False

    def __repr__(self):
        return self.asstr()


    def asstr(self, indent=0, verbose=True):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'STAT' )
        dp.add( 'z', fmt=possiblytuple2str )
        if verbose:
            dp.addcls( 'tol' )
        return dp.asstr(indent=indent)[:-1]

    def assert_equal(self, results):
        import pytest
        assert self.z  == pytest.approx(results.z,  abs=self.tol.z)

    def print_comparison(self, dataset, results):
        s  = f'{dataset.name} ({self.dim}D, {dataset.params.testname})\n'
        s +=  '   Expected, Actual\n'
        s += f'   z  = {self.z}, {results.z}\n'
        print(s)



class ExpectedResultsSPM1D(object):

    def __init__(self):
        self.dim  = 0
        self.STAT = 'Z'    # test statistic
        self.z    = None   # expected test stat
        self.df   = None   # expected degrees of freedom
        self.p    = None   # expected p value
        self.tol  = ToleranceSPM1D()


    def __eq__(self, results):
        try:
            self.assert_equal(results)
            return True
        except AssertionError:
            return False

    def __repr__(self):
        return self.asstr()


    def asstr(self, indent=0, verbose=True):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'STAT' )
        dp.add( 'z', fmt=possiblytuple2str )
        dp.add( 'df', fmt=dflist2str )
        dp.add( 'p', fmt=possiblytuple2str )
        if verbose:
            dp.addcls( 'tol' )
        return dp.asstr(indent=indent)[:-1]


    def assert_equal(self, results):
        import pytest
        assert self.z  == pytest.approx(results.z,  abs=self.tol.z)
        assert self.df == pytest.approx(results.df, abs=self.tol.df)
        assert self.p  == pytest.approx(results.p,  abs=self.tol.p)

    def print_comparison(self, dataset, results):
        s  = f'{dataset.name} ({self.dim}D, {dataset.params.testname})\n'
        s +=  '   Expected, Actual\n'
        s += f'   z  = {self.z}, {results.z}\n'
        s += f'   df = {self.df}, {results.df}\n'
        s += f'   p  = {self.p}, {results.p}\n'
        print(s)


class ExpectedResultsListSPM1D(list):

    def __init__(self, STAT, z, v, p):
        super().__init__()
        self.STAT     = 'F'
        self.tol      = ToleranceSPM1D()
        for zz,vv,pp in zip(z, v, p):
            e      = ExpectedResultsSPM1D()
            e.STAT = STAT
            e.z    = zz
            e.df   = vv
            e.p    = pp
            self.append( e )

    def asstr(self, indent=None, verbose=None):
        return f'[List of {len(self)} ExpectedResults objects]'


class ToleranceSPM1D_1D(object):  # absolite tolerance (for unit tests)
    def __init__(self):
        self.z                 = 1e-5
        self.df                = 1e-5
        self.fwhm              = 1e-5
        self.resels            = 1e-5
        self.zc                = 1e-5
        self.cluster_centroid  = 1e-5
        self.cluster_endpoints = 1e-5
        self.cluster_extent    = 1e-5
        self.cluster_p         = 1e-5

    def __repr__(self):
        return self.asstr()

    def asstr(self, indent=0, verbose=True):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'z' )
        dp.add( 'df' )
        dp.add( 'fwhm' )
        dp.add( 'resels' )
        dp.add( 'zc' )
        dp.add( 'cluster_centroid' )
        dp.add( 'cluster_endpoints' )
        dp.add( 'cluster_extent' )
        dp.add( 'cluster_p' )
        return dp.asstr(indent=indent)

class ExpectedResultsSPM1D_1D(ExpectedResultsSPM1D):

    def __init__(self):
        self.dim      = 1
        self.STAT     = 'Z'    # test statistic
        self.z        = None   # expected test stat
        self.df       = None   # expected degrees of freedom
        self.fhwm     = None   # expected smoothness
        self.resels   = None   # expected resel counts
        self.zc       = None   # expected critical threshold
        self.clusters = None
        self.tol      = ToleranceSPM1D_1D()


    def asstr(self, indent=0, verbose=True):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'STAT' )
        dp.add( 'z', fmt=array2shortstr )
        dp.add( 'df', fmt=dflist2str )
        dp.add( 'fwhm', fmt='%.5f' )
        dp.add( 'resels', fmt=tuple2str )
        dp.add( 'zc', fmt='%.5f' )
        dp.add( 'clusters' )
        return dp.asstr(indent=indent)[:-1]


    def assert_equal(self, spmi):
        import pytest
        if self.fwhm != pytest.approx(spmi.fwhm, abs=self.tol.fwhm):
            import warnings
            msg = 'jikudata WARNING!  Changing FWHM from %.5f to %.5f and reconducting inference.\n' %(self.fwhm, spmi.fwhm)
            warnings.warn(msg, UserWarning, stacklevel=2)
            spmi.sm.fwhm   = self.fwhm
            spmi.sm.resels = self.resels
            spmi           = spmi.inference(0.05)

        assert self.z      == pytest.approx(spmi.z,      abs=self.tol.z)
        assert self.df     == pytest.approx(spmi.df,     abs=self.tol.df)
        assert self.fwhm   == pytest.approx(spmi.fwhm,   abs=self.tol.fwhm)
        assert self.resels == pytest.approx(spmi.resels, abs=self.tol.resels)
        assert self.zc     == pytest.approx(spmi.zc,     abs=self.tol.zc)
        for c0,c1 in zip(self.clusters, spmi.clusters):
            # print('\n\n\n\n\n')
            # print( c0['centroid'], c1.centroid )
            # print('\n\n\n\n\n')
            assert c0['centroid']  == pytest.approx(c1.centroid,  abs=self.tol.cluster_centroid)
            assert c0['endpoints'] == pytest.approx(c1.endpoints,  abs=self.tol.cluster_endpoints)
            assert c0['extent']    == pytest.approx(c1.extent,  abs=self.tol.cluster_extent)
            assert c0['p']         == pytest.approx(c1.p,  abs=self.tol.cluster_p)


    def print_comparison(self, dataset, results):
        s  = f'{dataset.name} ({self.dim}D, {dataset.params.testname})\n'
        s +=  '   Expected, Actual\n'
        s += f'   z.max() = {self.z.max()}, {results.z.max()}\n'
        s += f'   df      = {self.df}, {results.df}\n'
        s += f'   fwhm    = {self.fwhm}, {results.fwhm}\n'
        s += f'   resels  = {self.resels}, {results.resels}\n'
        s += f'   zc      = {self.zc}, {results.zc}\n'
        for i,(c0,c1) in enumerate( zip(self.clusters, results.clusters)):
            s += f'   ---Cluster {i}---\n'
            s += f'      centroid  = {c0["centroid"]}, {c1.centroid}\n'
            s += f'      endpoints = {c0["endpoints"]}, {c1.endpoints}\n'
            s += f'      extent    = {c0["extent"]}, {c1.extent}\n'
            s += f'      p         = {c0["p"]}, {c1.p}\n'
        print(s)


class ExpectedResultsListSPM1D_1D(list):

    def __init__(self):
        super().__init__()
        self.STAT     = 'F'
        self.tol      = ToleranceSPM1D_1D()

    def asstr(self, indent=None, verbose=None):
        return f'[List of {len(self)} ExpectedResults1D objects]'
