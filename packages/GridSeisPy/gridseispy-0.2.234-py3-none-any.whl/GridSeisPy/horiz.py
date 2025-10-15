import numpy as np
# from pandas import read_csv, read_excel, read_table
from numpy import nan, zeros, full, dtype, ndarray
from numpy import float64, bool_
from pathlib import Path
from rich.progress import track
import copy
from .base.base_class import CVDFile
from .grid import SeisGrid
from .base.io import loadtxt


class Horiz(CVDFile, SeisGrid):
    """"""
    KEY_TIME = 'time'
    KEY_DEPTH = 'depth'

    slots = CVDFile.slots + SeisGrid.slots
    def __init__(self, field: int = 0):
        """"""
        CVDFile.__init__(self)
        SeisGrid.__init__(self, field)

    def __getitem__(self, item):
        """"""
        return self.elems[item][self.kField]

    def __setitem__(self, key, value):
        """"""
        self.elems[key][self.kField] = value

    def __add__(self, other):
        if isinstance(other, Horiz):
            self.elems[self.kTIME] += other.elems[self.kTIME]
        elif isinstance(other, (int, float, np.int32, np.int64, np.float64, np.float32)):
            self.elems[self.kTIME] += other

    def __sub__(self, other):
        cls = copy.deepcopy(self)
        if isinstance(other, Horiz):
            cls.bool, cls.path = self.bool & other.bool, None
            cls.elems[self.kTIME] = self.elems[self.kTIME] - other.elems[self.kTIME]
        elif isinstance(other, (int, float, np.int32, np.int64, np.float64, np.float32)):
            cls.elems[self.kTIME], cls.path = self.elems[self.kTIME] - other, None
        return cls

    def __mul__(self, other):
        if isinstance(other, Horiz):
            self.elems[self.kTIME] *= other.elems[self.kTIME]
        elif isinstance(other, (int, float, np.int32, np.int64, np.float64, np.float32)):
            self.elems[self.kTIME] *= other

    def __truediv__(self, other):
        if isinstance(other, Horiz):
            self.elems[self.kTIME] /= other.elems[self.kTIME]
        elif isinstance(other, (int, float, np.int32, np.int64, np.float64, np.float32)):
            self.elems[self.kTIME] /= other

    def setTimeByTXT(self, path, skiprows=2, usecols: list or tuple = None, skipInvVal='-999.25', **kwargs):
        """"""
        # 2.加载地震层位数据
        self.path, self.skiprows = path, skiprows
        keysCol, data = loadtxt(self.path, skiprows=self.skiprows, usecols=usecols, **kwargs, skipInvVal=skipInvVal,
                                convert=tuple)
        dataCols = np.array(data, dtype=np.dtype({'names': keysCol, 'formats': self.ks2fmts(keysCol)}))

        # 计算索引，并赋值
        i = self.inlineID2i(dataCols[self.kINLINE])  # <= 前, > 后
        j = self.xlineID2j(dataCols[self.kXLINE])
        self.elems[self.kField][i, j] = dataCols[self.kField]
        state = np.full(self.bool.shape, fill_value=False, dtype=bool)
        state[i, j] = True
        self.bool = self.bool & state
        return self

    def setByTXT(self, path, skiprows=2, useCols: list or tuple = None, comments: str = '#', skipInvVal: str = '-999.25'):
        """"""
        # with (open(self.path) as f):
        #     # 1.获取可用列索引
        #     *massage, keysLine = [f.readline() for i in range(self.skiprows + 1)]
        #     useKeys = [key.lower() for i, key in enumerate(keysLine.split()) if
        #                i in UseCols or key.lower() in UseCols] if UseCols is not None else keysLine.lower().split()
        #     UseColsIndex = [i for i, key in enumerate(keysLine.split()) if
        #                     i in UseCols or key.lower() in UseCols] if UseCols is not None else None
        #     if UseCols is not None and len(UseCols) != len(UseColsIndex):
        #         raise ValueError(
        #             f"Input columns:{UseCols} does not match the columns:{keysLine.lower().split()} in skiprows file")
        #
        #     # 2.设置结构体类型
        #     keysCol = [key for key in useKeys]
        #     formats = ['i4' if key in [self.INLINE, self.KEY_XLINE] else 'f4' for i, key in enumerate(keysCol)]
        #     self.dType = np.dtype({'names': keysCol, 'formats': formats})
        #
        #     getRow = lambda x: tuple(x.split()) if UseCols is None else tuple(
        #         value for i, value in enumerate(x.split()) if i in UseColsIndex)
        #
        #     dataRows = np.array([getRow(rowData)
        #                          for rowData in f.readlines()
        #                          if not rowData.startswith(comments) and invalidValue not in rowData], dtype=self.dType)
        # dataRows = np.loadtxt(self.path, comments='#', skiprows=self.skiprows + 1, usecols=UseColsIndex, dtype=self.dType)
        self.path, self.skiprows = path, skiprows
        keysCol, data = loadtxt(fname=self.path, skiprows=self.skiprows, usecols=useCols, comments=comments,
                                skipInvVal=skipInvVal, convert=tuple)
        DType = np.dtype({'names': keysCol, 'formats': self.ks2fmts(keysCol)})
        # choose = np.random.randint(0, len(data), int(len(data)*0.1))
        # data = [data[i] for i in choose]
        self.setByRows(np.array(data, dtype=DType))
        return self

    def inlineID2iTrace(self, inlineIDs: ndarray or int) -> ndarray or int:
        """"""
        if self.kITRACE in self.dtype.names:
            return self.elems[self.kITRACE][self.inlineID2i(inlineIDs)]
        else:
            raise ValueError("'iTrace' haven't in dtypes'")

    def xlineID2iTrace(self, xlineIDs: ndarray or int) -> ndarray or int:
        """"""
        if self.kITRACE in self.dtype.names:
            return self.elems[self.kITRACE][:, self.xlineID2j(xlineIDs)]
        else:
            raise ValueError("'iTrace' haven't in dtypes'")

