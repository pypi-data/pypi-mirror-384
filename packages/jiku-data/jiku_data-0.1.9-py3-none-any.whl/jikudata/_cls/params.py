
from .. util import DisplayParams, tuple2simplestr

spm1d_descriptions = {
    'ttest'             : 'One-sample t-test',
    'ttest2'            : 'Two-sample t-test',
    'ttest_paired'      : 'Paired t-test',
    'regress'           : 'Linear regression',

    'anova1'            : 'One-way ANOVA',
    'anova1rm'          : 'One-way repeated measures ANOVA',
    'anova2'            : 'Two-way ANOVA',
    'anova2nested'      : 'Two-way ANOVA (nested)',
    'anova2rm'          : 'Two-way repeated measures ANOVA',
    'anova2onerm'       : 'Two-way ANOVA (repeated measures on one factor)',
    'anova3'            : 'Three-way ANOVA',
    'anova3nested'      : 'Three-way ANOVA (nested)',
    'anova3rm'          : 'Three-way ANOVA (repeated measures on all factors)',
    'anova3onerm'       : 'Three-way ANOVA (repeated measures on one factor)',
    'anova3tworm'       : 'Three-way ANOVA (repeated measures on two factors)',

    'cca'               : 'Canonical correlation analysis',
    'hotellings'        : "One-sample Hotelling's T2-test",
    'hotellings2'       : "Two-sample Hotelling's T2-test",
    'hotellings_paired' : "Paired Hotelling's T2-test",
    'manova1'           : 'One-way MANOVA',

    'ci_onesample'      : 'One-sample confidence interval',
    'ci_pairedsample'   : 'Paired-sample confidence interval',
    'ci_twosample'      : 'Two-sample confidence interval',

    'normality'         : "Normality test",
    'normality_k2'      : "Normality test (D'Agostino-Pearson K2)",
    'normality_sw'      : 'Normality test (Shapiro-Wilk)',
    
    'normality_residuals' : "Normality test (D'Agostino-Pearson K2)",

}



# class Parameters(object):
#     def __init__(self):
#         self._spm1dv           = None   # None 4 or 5
#         self.packagename       = None   # package name (e.g. "spm1d")
#         self.packageroot       = None   # module / subpackage root (e.g. "spm1d.stats.c")
#         self.fn                = None   # function name
#         self.args              = ()
#         self.kwargs            = {}
#         self.inference_args    = ()
#         self.inference_kwargs4 = {}     # inference arguments for spm1d v0.4
#         self.inference_kwargs5 = {}     # inference arguments for spm1d v0.5
#
#     def __repr__(self):
#         dp      = DisplayParams( self, default_header=True )
#         dp.add( 'fn' )
#         dp.add( 'fn_description' )
#         dp.add( 'args', tuple2simplestr )
#         dp.add( 'kwargs' )
#         return dp.asstr()
#
#     @property
#     def fnname(self):
#         return self.packageroot + '.' + self.fn
#     @property
#     def iargs(self):
#         return self.inference_args
#     @property
#     def inference_kwargs(self):
#         v = self._spm1dv
#
#         print( v )
#         if v is None:
#             import spm1d
#             v = int( spm1d.__version__.split('.')[1] )
#         if v==4:
#             return self.inference_kwargs4
#         elif v == 5:
#             return self.inference_kwargs5
#
#     @property
#     def ikwargs(self):
#         return self.inference_kwargs
#     @property
#     def fn_description(self):
#         return ""
#     @property
#     def test_description(self):
#         return self.fn_description
#     @property
#     def testname(self):
#         return self.fn
#
#
#     def get_exec_str(self, dataset, aslist=False):
#         pass
#         # s = []
#         # if dataset.dim==1:
#         #     s.append('import matplotlib.pyplot as plt')
#         # s.append(  'import jikudata as jd')
#         # s.append( f'import {self.packageroot}' )
#         # s.append( '' )
#         # s.append( f'dataset = jd.{dataset.name}()' )
#         # s.append( '' )
#         # s.append(  'args    = dataset.params.args')
#         # s.append(  'kwargs  = dataset.params.kwargs')
#         # s.append(  'iargs   = dataset.params.iargs')
#         # s.append(  'ikwargs = dataset.params.ikwargs')
#         # s.append( f'spmi    = {self.packageroot}.{self.testname}(*args, **kwargs).inference(*iargs, **ikwargs)')
#         # s.append( '' )
#         # if dataset.dim==0:
#         #     s.append( 'print( spmi )' )
#         # elif dataset.dim==1:
#         #     s.append( 'plt.figure()' )
#         #     s.append( 'ax = plt.axes()' )
#         #     s.append( 'spmi.plot( ax=ax )')
#         #     s.append( 'plt.show()')
#         # if not aslist:
#         #     s = '\n'.join( s )
#         # return s
#
#
#     def get_function(self):
#         exec(   f'import {self.packageroot}'   )
#         return eval(  self.fnname )
#
#     def run(self, kwargs={}, ikwargs=None):
#         fn  = self.get_function()
#         kwa = self.kwargs
#         kwa.update( kwargs )
#         return fn( *self.args , **kwa )




class ParametersSPM1D(object):
    def __init__(self):
        self.packagename      = 'spm1d'
        self.packageroot      = 'spm1d.stats.c'
        self.testname         = None   # spm1d.stats function name
        self.args             = ()
        self.kwargs           = {}
        self.inference_args   = ()
        # self.inference_kwargs = {}
        self.inference_kwargs4 = {}     # inference arguments for spm1d v0.4
        self.inference_kwargs5 = {}     # inference arguments for spm1d v0.5
        

    def __repr__(self):
        dp      = DisplayParams( self, default_header=True )
        dp.add( 'testname' )
        dp.add( 'test_description' )
        dp.add( 'args', tuple2simplestr )
        dp.add( 'kwargs' )
        return dp.asstr()

    @property
    def fnname(self):
        return self.packageroot + '.' + self.testname
    @property
    def iargs(self):
        return self.inference_args
    @property
    def inference_kwargs(self):
        v = self._spm1dv
        if v is None:
            import spm1d
            v = int( spm1d.__version__.split('.')[1] )
        if v==4:
            return self.inference_kwargs4
        elif v == 5:
            return self.inference_kwargs5
    @property
    def ikwargs(self):
        return self.inference_kwargs
    @property
    def isrm(self):
        return self.testname.endswith('rm')
    @property
    def test_description(self):
        return spm1d_descriptions[ self.testname ]


    def get_exec_str(self, dataset, aslist=False):
        s = []
        if dataset.dim==1:
            s.append('import matplotlib.pyplot as plt')
        s.append(  'import jikudata as jd')
        s.append( f'import {self.packageroot}' )
        s.append( '' )
        s.append( f'dataset = jd.{dataset.name}()' )
        s.append( '' )
        s.append(  'args    = dataset.params.args')
        s.append(  'kwargs  = dataset.params.kwargs')
        s.append(  'iargs   = dataset.params.iargs')
        s.append(  'ikwargs = dataset.params.ikwargs')
        s.append( f'spmi    = {self.packageroot}.{self.testname}(*args, **kwargs).inference(*iargs, **ikwargs)')
        s.append( '' )
        if dataset.dim==0:
            s.append( 'print( spmi )' )
        elif dataset.dim==1:
            s.append( 'plt.figure()' )
            s.append( 'ax = plt.axes()' )
            s.append( 'spmi.plot( ax=ax )')
            s.append( 'plt.show()')
        if not aslist:
            s = '\n'.join( s )
        return s


    def get_function(self):
        if self._spm1dv in [None, 5]:
            import spm1d.stats.c
            return eval(  f'spm1d.stats.c.{self.testname}' )
        elif self._spm1dv==4:
            import spm1d_v4.stats.c
            return eval(  f'spm1d_v4.stats.c.{self.testname}' )

    def run(self, kwargs={}, ikwargs={}, spm1d_version=None):
        self.set_spm1d_version( spm1d_version )
        fn = self.get_function()
        a0 = self.args
        k0 = self.kwargs
        a1 = self.inference_args
        k1 = self.inference_kwargs
        k0.update( kwargs )
        k1.update( ikwargs )
        return fn( *a0 , **k0 ).inference(*a1, **k1)


    def set_spm1d_version(self, v):
        self._spm1dv = v
