
import os,inspect
from abc import ABCMeta, abstractmethod, abstractproperty
from .. util import DisplayParams, array2shortstr


class _Dataset(metaclass=ABCMeta):

    def __init__(self, _load_data=True):
        self._autotest    = True   # execute automated testing via pytest ** should be true except for in-development datasets
        self._dir0        = os.path.dirname( inspect.getfile( self.__class__) )
        # self._spm1dv      = None   # force spm1d version for v0.4 and v0.5 testing
        self.dim          = 0      # data dimensionality
        self.x            = None   # IVs
        self.y            = None   # DV
        self.cite         = None   # literature citation (if relevant)
        self.datafile     = None   # data file path
        self.expected     = None   # expected results
        self.params       = None   # parameters for reproducing in another software package
        self.www          = None   # web source (if available)
        self.notes        = None   # extra dataset details
        self.__set_datafile()
        self.__set_expected()
        self._set_attrs()               # (abstract method)
        self._set_data( _load_data )    # (abstract method)
        self._set_expected( ) # (abstract method)
        # self._set_expected( _load_data) # (abstract method)
        self._set_params()              # (abstract method)


    def __repr__(self):
        dp      = DisplayParams( self, default_header=True )
        dp.set_subclassverbose(False)
        dp.add( 'design' )
        dp.add( 'dim' )
        dp.add( 'y', fmt=array2shortstr )
        dp.addcls( 'expected' )
        return dp.asstr()

    # ----- local methods -----

    def __set_datafile(self):
        fpath  = os.path.join( self._dir0, 'data.csv' )
        if os.path.exists(fpath):
            self.datafile    = fpath

    def __set_expected(self):
        fpath  = os.path.join( self._dir0, 'expected_results.npz' )
        if os.path.exists(fpath):
            from .. io import load_expected_results_1d
            self.expected = load_expected_results_1d( fpath )

    # ----- abstract methods -----

    @abstractmethod
    def _set_attrs(self):     # set non-data attributes (e.g. cite, www)
        pass
    # @abstractmethod
    # def _set_data(self):      # load all dependent and independent variables
    #     pass
    @abstractmethod
    def _set_expected(self):  # expected results
        pass
    @abstractmethod
    def _set_params(self):    # parameters for reproducing results in an external package (e.g. spm1d)
        pass
    @abstractmethod
    def get_exec_str(self, aslist=False):  # get executable string to reproduce expected results
        return self.params.get_exec_str( self, aslist=aslist )

    def _set_data(self, _load_data=True):
        if _load_data and (self.datafile is not None):
            from .. io import JikuCSVParser
            parser   = JikuCSVParser( self.datafile )
            self.y   = parser.y
            self.x   = parser.x


    # ----- properties -----

    # @property
    # def _spm_version(self):
    #     import spm1d
    #     return int( spm1d.__version__.split('.')[1] )
    
    @property
    def design(self):
        return self.params.test_description
        # return self.params.description

    @property
    def hasdatafile(self):
        return self.datafile is not None
    @property
    def haslink(self):
        return self.www is not None
    @property
    def haspaper(self):
        return self.cite is not None
    @property
    def ismultivariate(self):
        return not self.isunivariate
    @property
    def ismv(self):
        return self.ismultivariate
    @property
    def isunivariate(self):
        return (self.y.ndim - self.dim) == 1
    @property
    def isuv(self):
        return self.isunivariate

    @property
    def links(self):
        d = {}
        if self.www is not None:
            if isinstance(self.www, dict):
                d.update( self.www )
            else:
                d.update( {'www':self.www} )
        if self.hasdatafile:
            d.update( {'datafile':self.datafile} )
        if len(d)==0:
            d = None
        return d

    @property
    def name(self):
        return self.__class__.__name__


    # ----- methods -----

    def get_summary_table(self):
        a = []
        a.append( ('name', self.name) )
        a.append( ('dim', self.dim) )
        a.append( ('STAT', self.expected.STAT) )
        a.append( ('fnname', self.params.fnname) )
        a.append( ('test_description', self.params.test_description) )
        a.append( ('y', array2shortstr(self.y)) )
        a.append( ('x', array2shortstr(self.x)) )
        return a

    def get_exec_str(self, full=True, aslist=False):
        return self.params.get_exec_str(self)


    def open_links(self):   # open link in default web browser
        import webbrowser
        if isinstance(self.www, str):
            webbrowser.open(self.www, new=0, autoraise=True)
        elif isinstance(self.www, (tuple,list)):
            for s in self.www:
                webbrowser.open(s, new=0, autoraise=True)
        elif isinstance(self.www, dict):
            for s in self.www.values():
                webbrowser.open(s, new=0, autoraise=True)


    def print_verbose(self):
        dp      = DisplayParams( self, default_header=True )
        dp.set_subclassverbose(True)
        dp.add( 'design' )
        dp.add( 'dim' )
        dp.add( 'ismultivariate' )
        dp.add( 'y', fmt=array2shortstr )
        dp.add( 'datafile' )
        dp.add( 'cite' )
        dp.add( 'www' )
        dp.add( 'notes' )
        dp.addcls( 'expected' )
        print( dp.asstr() )


    def run(self, kwargs={}, ikwargs={}, spm1d_version=None):
        # if spm1d_version is not None:
        #     self._spm1dv = spm1d_version
        return self.params.run(kwargs=kwargs, ikwargs=ikwargs, spm1d_version=spm1d_version)


    def runtest(self, verbose=True, kwargs={}, ikwargs={}, spm1d_version=None):
        results  = self.params.run(kwargs=kwargs, ikwargs=ikwargs, spm1d_version=spm1d_version)
        if isinstance(self.expected, list):
            for e,r in zip(self.expected, results):
                e.tol = self.expected.tol
                if verbose:
                    e.print_comparison(self, r)
                e.assert_equal( r )
        else:
            if verbose:
                self.expected.print_comparison(self, results)
            self.expected.assert_equal( results )




#
#
# class DatasetANOVA1(_DatasetANOVA):
# 	def __init__(self):
# 		self.rm       = False  #repeated measures
# 		super(DatasetANOVA1, self).__init__()
# 		self.design = 'One-way ANOVA'
# 	def get_data(self):
# 		return self.Y, self.A
# 	# def get_expected_df(self, type='sphericity_assumed'):
# 	# 	if type=='sphericity_assumed':
# 	# 		return self.df
# 	# 	if type=='GG':
# 	# 		return self.dfGG
# 	# 	elif type=='GGX':
# 	# 		return self.dfGGX
# 	# 	elif type=='HF':
# 	# 		return self.dfHF
# 	# def get_expected_p_value(self, type='sphericity_assumed'):
# 	# 	if type=='sphericity_assumed':
# 	# 		return self.p
# 	# 	if type=='GG':
# 	# 		return self.pGG
# 	# 	elif type=='GGX':
# 	# 		return self.pGGX
# 	# 	elif type=='HF':
# 	# 		return self.pHF



