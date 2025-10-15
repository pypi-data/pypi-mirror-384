from numpy import nan
from .settings import DefaultSetting


class SeisKeys(DefaultSetting):
    """关键字全部小写"""

    # MD, TVD, SSTVD, TWT = ['md', 'tvd', 'sstvd', 'twt']
    # INLINE, XLINE, X, Y = ['inline', 'xline', 'x', 'y']
    # ITRACE, TIME, DEPTH = ['itrace', 'time', 'depth']
    # INVVAL_S, INVVAL_V, NAN = ['-999.25', -999.25, nan]
    # FORMATS = {'i4': [INLINE, XLINE, ITRACE], 'f4': [MD, TVD, SSTVD, TWT, X, Y, TIME, DEPTH]}

    slots = ['_kMD', '_kTVD', '_kSSTVD', '_kTWT', '_kINLINE', '_kXLINE', '_kX', '_kY', '_kField', '_kITRACE', '_kTIME', '_kDEPTH', '_vINV', '_sINV', '_vNAN', '_format']

    def __init__(self, field):
        self._kMD, self._kTVD, self._kSSTVD, self._kTWT = ['md', 'tvd', 'sstvd', 'twt']  # 关键字k
        self._kINLINE, self._kXLINE, self._kX, self._kY = ['inline', 'xline', 'x', 'y']  # 关键字ij
        self._kField, self._kITRACE, self._kTIME, self._kDEPTH = [field, 'itrace', 'time', 'depth']  # filed
        self._vINV, self._sINV, self._vNAN = [-999.25, '-999.25', nan]
        self._format = {'i4': [self.kINLINE, self.kXLINE, self.kITRACE],
                         'f4': [self.kMD, self.kTVD, self.kSSTVD, self.kTWT, self.kX, self.kY, self.kTIME, self.kDEPTH],}

    def ks2fmts(self, keys):
        """keys to formats"""
        dtype = ['O'] * len(keys)
        for i, k in enumerate(keys):
            for item in self._format.items():
                if k in item[1]:
                    dtype[i] = item[0]
        return dtype

    @property
    def vINV(self): return self._vINV

    @property
    def sINV(self): return self._sINV

    @property
    def vNAN(self): return self._vNAN

    @property
    def kMD(self): return self._kMD

    @property
    def kTVD(self): return self._kTVD

    @property
    def kSSTVD(self): return self._kSSTVD

    @property
    def kTWT(self): return self._kTWT

    @property
    def kINLINE(self): return self._kINLINE

    @property
    def kXLINE(self): return self._kXLINE

    @property
    def kX(self): return self._kX

    @property
    def kY(self): return self._kY

    @property
    def kITRACE(self): return self._kITRACE

    @property
    def kTIME(self): return self._kTIME

    @property
    def kDEPTH(self): return self._kDEPTH

    @property
    def kField(self): return self.kDEPTH if self._kField else self.kTIME
