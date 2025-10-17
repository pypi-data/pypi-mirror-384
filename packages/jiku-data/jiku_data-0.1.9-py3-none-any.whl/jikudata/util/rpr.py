

'''
Utility classes for working with classes' __repr__ method
'''



class DisplayParams(list):
    def __init__(self, obj, default_header=True):
        super().__init__( [ ] )
        self.obj             = obj
        self.subclassverbose = False
        if default_header:
            self.add_header( obj.__class__.__name__ + ':' )

    @property
    def keys(self):
        for a in self:
            if isinstance(a, tuple):
                k,v = a
                if v is not None:
                    yield k

    def add_header(self, s):
        self.append( (s, None) )

    def add(self, key, fmt='%s'):
        self.append( (key,fmt) )

    def addcls(self, x):
        self.append(x)

    def asstr(self, indent=0):
        s = '\n'
        ind = '    ' * indent
        n = max( [len(k)  for k in self.keys] )
        for a in self:
            if isinstance(a, tuple):
                k,v = a
                if v is None:
                    ss = f'{k}'
                elif isinstance(v, str):
                    x  = getattr(self.obj, k)
                    ss = f'    {k:<{n}} : {v%x}'
                elif callable(v):
                    x  = getattr(self.obj, k)
                    ss = f'    {k:<{n}} : {v(x)}'
                # else:
                #     x  = getattr(self.obj, k)
                #     if isinstance(x, (tuple,list)):
                #         ss = '(' + ','.join(x) + ')'
            else:
                k   = a
                v   = getattr(self.obj, k)
                sss = v.asstr(indent=2, verbose=self.subclassverbose)
                ss  = f'    {k:<{n}} : {sss}'
            s += ind + ss + '\n'
        return s[:-1]

    def set_subclassverbose(self, state=True):
        self.subclassverbose = state