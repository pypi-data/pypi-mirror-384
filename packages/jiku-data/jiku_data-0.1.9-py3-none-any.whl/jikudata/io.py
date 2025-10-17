
import os
import numpy as np



def _flattenx(x):
    if x.shape[1]==1:
        x  = x[:,0]
    if np.all( x%1==0 ):
        x  = np.asarray(x, dtype=int)
    return x


class JikuCSVParser(object):
    def __init__(self, fpath):
        self._null_x  = 0
        self.dim      = None
        self.y        = None
        self.x        = None
        self.labels_y = None
        self.labels_x = None
        self._load(fpath)

    def __repr__(self):
        s  = 'JikuCSVParser\n'
        s += f'   dim       = {self.dim}\n'
        s += f'   mv        = {self.mv}\n'
        s += f'   labels_x  = {self.labels_x}\n'
        s += f'   labels_y  = {self.labels_y}\n'
        s += f'   x         = {self._x_str}\n'
        s += f'   y         = {self._y_str}\n'
        return s

    @property
    def _x_str(self):
        if isinstance(self.x, np.ndarray):
            s = f'{self.x.shape} array'
        else:
            s = str(self.x)
        return s
    @property
    def _y_str(self):
        return f'{self.y.shape} array'
    @property
    def nx(self):
        return len( self.labels_x )
    @property
    def ny(self):
        return len( self.labels_y )



    def _load(self, fpath):
        dim,mv        = 0, False
        nUPPER,nlower = 0, 0
        labels_x      = []
        labels_y      = []
        with open(fpath, 'r') as f:
            line = f.readline()
            for i,s in enumerate( line.strip().split(',') ):
                if s.startswith('_IND'):
                    i0     = i + 1
                    dim,mv = 1, True
                    break
                elif s.startswith('_q'):
                    i0 = i
                    dim = 1
                    break
                else:
                    if s.isupper():
                        nUPPER += 1
                        labels_x.append( s )
                    else:
                        nlower += 1
                        labels_y.append( s )
            lines = f.readlines()
        a         = np.asarray([line.strip().split(',')  for line in lines], dtype=float)
        if dim==0:
            mv    = nlower > 1
        self.labels_x = labels_x
        self.labels_y = labels_y
        self.dim      = dim
        self.mv       = mv

        if dim==0:
            if mv:
                self._parse_mv0d(a)
            else:
                self._parse_uv0d(a)
        elif dim==1:
            if mv:
                self._parse_mv1d(a)
            else:
                self._parse_uv1d(a)

    def _parse_uv0d(self, a):
        if a.shape[1]==1:
            self.x  = self._null_x
            self.y  = a.flatten()
        else:
            self.x  = _flattenx( a[:,:-1] )
            self.y  = a[:,-1]

    def _parse_uv1d(self, a):
        return self._parse_mv0d(a)

    def _parse_mv0d(self, a):
        nx = self.nx
        if nx==0:
            self.x  = self._null_x
            self.y  = a
        else:
            self.x  = _flattenx( a[:,:nx] )
            self.y  = a[:,nx:]

    def _parse_mv1d(self, a):
        nx = self.nx
        if nx==0:
            self.x  = self._null_x
            ind     = a[:,0]
            yy      = a[:,1:]
        else:
            self.x  = _flattenx( a[:,:nx] )
            ind     = a[:,nx]
            yy      = a[:,(nx+1):]
        self.y      = np.dstack(  [yy[ind==u]  for u in np.unique(ind)] )
        if nx!=0:
            J       = self.y.shape[0]
            self.x  = self.x[ :J ]


def loadh5(fpath, nodename='y'):
    import tables
    with tables.open_file(fpath, mode='r') as f:
        node = f.get_node( f'/{nodename}' )
        y    = np.asarray( node.read(), node.atom.dtype )
    return y



def load_expected_results_1d(fpath):
    from . _cls import ExpectedResultsSPM1D_1D
    with np.load(fpath, allow_pickle=True) as d:
        if d['z'].ndim==1:
            e             = ExpectedResultsSPM1D_1D()
            e.STAT        = str( d['STAT'] )
            e.z           = d['z']
            e.df          = tuple( d['df'] )
            e.fwhm        = float( d['fwhm'] )
            e.resels      = tuple( d['resels'] )
            e.zc          = float( d['zc'] )
            e.clusters    = list( d['clusters'] )
            for c in e.clusters:
                for k,v in c.items():
                    if isinstance(v, tuple):
                        c[k] = tuple( map(float, v) )
                    else:
                        c[k] = float(v)
        else:
            from . _cls import ExpectedResultsListSPM1D_1D
            e             = ExpectedResultsListSPM1D_1D()
            for i in range( d['z'].shape[0] ):
                ee            = ExpectedResultsSPM1D_1D()
                ee.STAT       = str( d['STAT'] )
                ee.z          = d['z'][i]
                ee.df         = tuple( d['df'][i] )
                ee.fwhm       = float( d['fwhm'] )
                ee.resels     = tuple( d['resels'] )
                ee.zc         = float( d['zc'][i] )
                ee.clusters   = list( d['clusters'][i] )
                e.append( ee )
    return e
