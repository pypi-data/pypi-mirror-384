from .keys import SeisKeys
from numpy import ndarray, array, around, nan
import numpy as np
from numpy.lib import recfunctions as rfn
import copy
import pyvista as pv


class SliceIJK:
    """获取[]内的切片信息"""
    def __getitem__(self, item): return item


class ArrayGrid(object):
    slots = ['_elems', '_bool']
    def __init__(self, field):
        self._elems = None
        self._bool = None

    @staticmethod
    def fromStructured(data):
        """
        结构体数据变成numpy
        :param data:
        :return:
        """
        return rfn.structured_to_unstructured(data)

    @property
    def shape(self): return array([*self._elems.shape])

    @property
    def dtype(self): return self._elems.dtype

    @property
    def elems(self): return self._elems

    @elems.setter
    def elems(self, item): self._elems = item

    @property
    def bool(self): return self._bool

    @bool.setter
    def bool(self, item): self._bool = item

    def initElems(self, shape: tuple, dtype: np.dtype, fill_value=nan):
        """"""
        self._elems = np.full(shape, fill_value=fill_value, dtype=dtype)

    def initBOOL(self, shape: tuple, fill_value=False):
        """"""
        self._bool = np.full(shape, fill_value=fill_value, dtype='?')

    @property
    def ijk(self): return SliceIJK()


class SeisGrid(ArrayGrid, SeisKeys):

    slots = ArrayGrid.slots + SeisKeys.slots + ['_arrInline', '_arrXline', '_arrIsASC', '_matFixCoord', '_matFixID', '_matFixIndex', '_matCoord2id', '_matCoord2ij']
    def __init__(self, field):
        """

        :param field: 设置时间域还是深度域
        """
        ArrayGrid.__init__(self, field)
        SeisKeys.__init__(self, field)
        # 工区坐标信息, _inline_seq、_xline_seq 按照升序排列, 非真实排序
        self._arrInline: ndarray = array([])
        self._arrXline: ndarray = array([])
        self._arrIsASC: ndarray = array([])  # 测线按照升序排列
        # 线性坐标转换
        self._matFixCoord: ndarray = array([])
        self._matFixID: ndarray = array([])
        self._matFixIndex: ndarray = array([])
        self._matCoord2id: ndarray = array([])
        self._matCoord2ij: ndarray = array([])
        #

    @property
    def arrInlines(self):  # 数据的真实顺序
        """符合坐标排列顺序的inline序列"""
        if not self._arrIsASC[0]:
            return np.flip(self._arrInline)
        return self._arrInline

    @property
    def arrXlines(self):  # 数据的真实顺序
        """符合坐标排列顺序的xline序列"""
        if not self._arrIsASC[-1]:
            return np.flip(self._arrXline)
        return self._arrXline

    @staticmethod
    def find_transformation_matrix(x_coords, y_coords, i_coords, j_coords):
        """
        使用最小二乘法求解坐标变换矩阵
        :param x_coords: 原始x坐标数组
        :param y_coords: 原始y坐标数组
        :param i_coords: 目标i坐标数组
        :param j_coords: 目标j坐标数组
        :return: 坐标变换矩阵（6个参数）
        """
        # 构建设计矩阵A，第一列是x坐标，第二列是y坐标，第三列是常数1
        A = np.vstack([x_coords, y_coords, np.ones(len(x_coords))]).T

        # 使用最小二乘法来解两个方程系统
        # i = A * [a, b, c]  --> 求解转换矩阵的第1行
        params_i, residuals_i, rank_i, s_i = np.linalg.lstsq(A, i_coords, rcond=None)
        # j = A * [d, e, f]  --> 求解转换矩阵的第2行
        params_j, residuals_j, rank_j, s_j = np.linalg.lstsq(A, j_coords, rcond=None)

        # 将两个求解结果组合成一个2x3维的矩阵，并转置
        transformation_matrix = np.array([params_i, params_j])
        return transformation_matrix

    def setByRows(self, dataRows: ndarray):
        """
        :param dataRows: ndarray类型的 结构体
        :return:
        """
        # inline, xline = dataCols[['inline', 'xline']]
        self._arrInline = np.unique(dataRows[self.kINLINE])
        self._arrXline = np.unique(dataRows[self.kXLINE])
        # 初始化数据
        self.initElems((self._arrInline.size, self._arrXline.size), dtype=dataRows.dtype, fill_value=self.vNAN)
        self.elems[self.kITRACE] = 0        # 默认无道区域值填充为第一道数据，以便取值
        self.bool = np.zeros(self.shape, dtype=bool)

        line0, line1 = np.array([[*v] for v in dataRows[[0, -1]][[self.kINLINE, self.kXLINE]]])
        coord0, coord1 = np.array([[*v] for v in dataRows[[0, -1]][[self.kX, self.kY]]])
        self._arrIsASC = (line1 - line0) * (coord1 - coord0) >= 0

        # 计算索引，并赋值
        iIndexs = self.inlineID2i(dataRows[self.kINLINE])  # <= 前, > 后
        jIndexs = self.xlineID2j(dataRows[self.kXLINE])
        self.elems[iIndexs, jIndexs] = dataRows
        self.bool[iIndexs, jIndexs] = True

        # 计算坐标转换矩阵  AX=Y --> X=A逆Y --> MX=MA逆Y --> MA逆=N --> A逆=M逆N, 其中M为X坐标系点， N为Y坐标系点
        """优化后，使用的是最小二乘法，求最佳的坐标转换矩阵"""
        self._matCoord2id = self.find_transformation_matrix(
            dataRows[self.kX],  dataRows[self.kY], dataRows[self.kINLINE], dataRows[self.kXLINE])
        self._matCoord2ij = self.find_transformation_matrix(
            dataRows[self.kX], dataRows[self.kY],  iIndexs, jIndexs)

        # testIndex = np.array([iIndexs[300:400], jIndexs[300:400]])
        # testCoord = dataRows[300:400][[self.kX, self.kY]]
        # testLineID = dataRows[300:400][[self.kINLINE, self.kXLINE]]
        # ij = self.xy2ij(testCoord[self.kX], testCoord[self.kY])
        # testIndex - ij
        # inl, xnl = self.xy2lineID(testCoord[self.kX], testCoord[self.kY])
        # testLineID[self.kXLINE] - xnl
        return self

    def inlineID2i(self, inlineIDs: ndarray or int) -> ndarray or int:
        """
        获取数据真实顺序索引
        :param inlineIDs:
        :return: same size of inlines
        """
        i = self._arrInline.searchsorted(inlineIDs)
        if self._arrIsASC[0]:
            return i
        else:
            return self._arrInline.size - 1 - i

    def xlineID2j(self, xlineIDs: ndarray or int) -> ndarray or int:
        """
        获取数据真实顺序索引
        :param xlineIDs:
        :return:
        """
        j = self._arrXline.searchsorted(xlineIDs)
        if self._arrIsASC[1]:
            return j
        else:
            return self._arrXline.size - 1 - j

    def lineID2ij(self, inlines: ndarray or list, xlines: ndarray or list) -> ndarray or list:
        """

        :param inlines:
        :param xlines:
        :return:
        """
        return [self.inlineID2i(inlines), self.xlineID2j(xlines)]

    def xy2lineID(self, x_coords: ndarray or list, y_coords: ndarray or list) -> ndarray:
        """"""
        A = np.array([x_coords, y_coords, np.ones(len(y_coords))])
        lines = np.round(self._matCoord2id @ A).astype('i4')
        return lines

    def xy2ij(self, x_coords: ndarray or list, y_coords: ndarray or list) -> ndarray:
        """

        :param x_coords:
        :param y_coords:
        :return:
        """
        A = np.array([x_coords, y_coords, np.ones(len(x_coords))])
        ij = np.round(self._matCoord2ij @ A).astype('i4')
        return ij

    def x2i(self, x_coords: ndarray or list):
        """"""
        A = np.array([x_coords, x_coords, np.ones(len(x_coords))])
        ij = np.round(self._matCoord2ij @ A).astype('i4')
        return ij[0]

    def y2i(self, y_coords: ndarray or list):
        """"""
        A = np.array([y_coords, y_coords, np.ones(len(y_coords))])
        ij = np.round(self._matCoord2ij @ A).astype('i4')
        return ij[1]

    def getInline(self, inlineIDs: ndarray or int or list, *args, **kwargs):
        """

        :param inlineIDs:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return self[self.inlineID2i(inlineIDs), :, *args, *kwargs]
        except ValueError as e:
            e.__str__ = f"wrong value, the range of inline is : {self._arrInline[0]} to {self._arrInline[-1]}"
            raise e

    def getXline(self, xlineIDs: ndarray or int or list, *args, **kwargs):
        """

        :param xlineIDs:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return self[:, self.xlineID2j(xlineIDs), *args, *kwargs]
        except ValueError as e:
            e.__str__ = f"wrong value, the range of xline is : {self._arrXline[0]} to {self._arrXline[-1]}"
            raise e

    def line(self, lineIDs):
        """"""
        raise NotImplementedError("{0}.line haven't being build now!".format(self.__class__.__name__))

    def inlineData(self):
        """"""
        raise NotImplementedError("{0}.inlineData haven't being build now!".format(self.__class__.__name__))

    def xlineData(self):
        """"""
        raise NotImplementedError("{0}.xlineData haven't being build now!".format(self.__class__.__name__))

    def lineData(self):
        """"""
        raise NotImplementedError("{0}.lineData haven't being build now!".format(self.__class__.__name__))

    def vis(self, scalars="value", cmap="rainbow", show_edges=False, lighting=True, ambient=0.3, diffuse=0.7, specular=0.5, specular_power=15):
        """
        使用 PyVista 可视化 SeisGrid 对象
        :param scalars: 用于上色的字段名
        :param cmap: colormap
        :param show_edges: 是否显示网格线
        :param lighting: 是否启用光照
        :param ambient, diffuse, specular, specular_power: 光照参数
        """
        # 1. Z 值
        z_vals = self.elems[self.kField]
        nrows, ncols = z_vals.shape

        # 2. 构建 (i,j) 网格点
        i_grid, j_grid = np.meshgrid(np.arange(nrows+1), np.arange(ncols+1), indexing='ij')

        # 3. (i,j) -> (x,y) 矩阵化
        A = self._matCoord2ij[:, :2]
        c = self._matCoord2ij[:, 2]
        ij_flat = np.column_stack([i_grid.ravel(), j_grid.ravel()])
        b_flat = (ij_flat - c).T
        xy_flat = np.linalg.inv(A) @ b_flat
        x_grid = xy_flat[0].reshape(i_grid.shape)
        y_grid = xy_flat[1].reshape(j_grid.shape)

        # 4. Z 值作为高度
        z_scaled = z_vals / 5.0
        z_grid = np.zeros_like(x_grid)
        z_grid[:-1, :-1] = z_scaled
        z_grid[:-1, 1:] += z_scaled
        z_grid[1:, :-1] += z_scaled
        z_grid[1:, 1:] += z_scaled
        z_grid /= 4.0  # 平均

        # 5. 创建 StructuredGrid
        grid = pv.StructuredGrid(x_grid, y_grid, z_grid)

        # 6. cell_data 对齐，删除 NaN
        cell_values = z_scaled.ravel(order="F")
        valid_mask = ~np.isnan(cell_values)
        grid = grid.extract_cells(np.where(valid_mask)[0])
        grid.cell_data[scalars] = cell_values[valid_mask]

        # 7. 绘制
        plotter = pv.Plotter()
        plotter.add_mesh(
            grid,
            scalars=scalars,
            cmap=cmap,
            show_edges=show_edges,
            lighting=lighting,
            ambient=ambient,
            diffuse=diffuse,
            specular=specular,
            specular_power=specular_power,
        )
        plotter.add_axes()
        plotter.show_grid()
        plotter.enable_trackball_style()  # Ctrl+左键平移
        plotter.show()