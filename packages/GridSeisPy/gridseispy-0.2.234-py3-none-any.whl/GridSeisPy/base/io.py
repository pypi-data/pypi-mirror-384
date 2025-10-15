from pathlib import Path

from numpy import dtype, array, ndarray
import numpy as np
# from numba import njit, jit
from rich.progress import track
from functools import partial
import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        return encoding, confidence


def loadtxt(fname: Path or str, skiprows: int = 0, usecols: list or tuple = None, comments: str = '#',
            delimiter: str = None, skipInvVal: str = '\t', convert=list, progress=False):
    """

    :param progress:
    :param convert:
    :param fname:
    :param skiprows:
    :param usecols: 根据关键字序列/索引序列选取数据, 关键字是小写后匹配
    :param comments:
    :param delimiter:
    :param skipInvVal: skipInvalidValue，选中的cols中，如果存在该值，就跳过
    :return:
    """
    fname = fname if isinstance(fname, Path) else Path(fname)
    detected_encoding, confidence = detect_encoding(fname)
    usecols = [key.lower() for key in usecols]

    with (open(fname, encoding=detected_encoding) as file):
        # 获取可用列索引
        *massage, keysLine = [file.readline() for i in range(skiprows + 1)]
        keysCol = keysLine.lower().split() if usecols is None else [
            key.lower() for i, key in enumerate(keysLine.split()) if i in usecols or key.lower() in usecols]
        UseColsIndex = list(range(len(keysCol))) if usecols is None else [
            i for i, key in enumerate(keysLine.split()) if i in usecols or key.lower() in keysCol]
        if len(keysCol) == 0:
            raise ValueError(
                f"Input columns:{usecols} does not match the columns:{keysLine.lower().split()} in header file")

        # 获取每行有效数据select
        sel_rows = lambda str_list: convert(str_list) if usecols is None else convert([str_list[i] for i in UseColsIndex])
        itr_rows = track(iter(lambda: next(file).split(delimiter), []), description=f'    loading: {fname.stem} ',
                         refresh_per_second=1, update_period=2) if progress else iter(
            lambda: next(file).split(delimiter), [])
        # dataRows = [useCols(row) for row in rows if skipline(row) and len(row) >= len(keysCol)]
        dataRows = [use_rows for str_rows in itr_rows if not str_rows[0].startswith(comments) for use_rows in
                    [sel_rows(str_rows)] if skipInvVal not in use_rows and len(use_rows) == len(keysCol)]
                    # 2024.11.19 增加跳过选定列中存在特殊值的行, 保证convert后的数据也要有对应数量的rows
    return keysCol, dataRows


def savetxt(path, KeysRow, DataRow, Header="Write by: Redo\n"):
    """加载测井解释结论数据
    :param path:
    :param DataRow:
    :param KeysRow:
    :param Header:
    :return:
    """
    with open(path, 'w') as f:
        # 写入Header
        f.write(Header)
        # 写入关键字行
        [f.write(str(value) + '\t') if i + 1 < len(KeysRow) else f.write(value + '\n') for i, value in
         enumerate(KeysRow)]
        # 写入数据行
        [f.write(str(dataRow[i]) + '\t') if i + 1 < len(dataRow) else f.write(str(dataRow[i]) + '\n')
         for dataRow in DataRow for i in range(len(KeysRow))]


def loadgrid(fname: Path or str, skiprows: int, dimens: list or ndarray or tuple = None, dtype='f4',
             encoding: str = 'utf-8', compressed: bool = True, read_array=False, order='F', norm=None):
    """

    :param fname:
    :param skiprows:
    :param dimens:
    :param dtype:
    :param encoding:
    :param compressed:
    :param read_array:
    :param order:
    :return:
    """
    fname = fname if isinstance(fname, Path) else Path(fname)

    with open(fname, encoding=encoding) as file:
        # 获取可用列索引
        _ = [file.readline() for i in range(skiprows)]
        # 获取每行有效数据
        lines = track(file.readlines(), description=f'    loading: {fname.stem} ', refresh_per_second=1,
                      update_period=2)
        # resetRow = lambda line: line.split('/')[0].split() if '/' in line else line.split()
        if read_array:
            from deepfield.field import parse_utils
            grid = parse_utils.read_array(file, dtype=dtype, compressed=compressed)
            return grid.reshape(dimens, order=order) if dimens is not None else grid
        if compressed:
            grid = array([s for line in lines for v in line.split() for s in
                          (int(v.split('*')[0]) * v.split('*')[1:] if '*' in v else [v])][:np.prod(dimens, dtype=int)],
                         dtype=dtype)
            # grid = array([v.split('*')[-1] for line in lines for v in resetRow(line)
            #               for _ in (range(int(v.split('*')[0])) if '*' in v else range(1))], dtype=dtype)
        else:
            # grid = array([v for line in lines for v in resetRow(line)], dtype=dtype)
            grid = array([v for line in lines for v in line.split()][:np.prod(dimens, dtype=int)], dtype=dtype)
    grid = grid if norm is None else norm(grid)
    return grid.reshape(dimens, order=order) if dimens is not None else grid


def savegrid(fname: Path or str, data: np.ndarray, attr='attr', compressed=True, cnt_line=20):
    """

    :param cnt_line:
    :param data:
    :param fname:
    :param attr:
    :param compressed:
    :return:
    """

    def doCompress(f, array: np.ndarray, fmt='%f ', n=0, items_written=0):
        while n < len(array):
            count = 1
            while (n + count < len(array)) and (array[n + count] == array[n]):
                count += 1
            if count <= 4:
                f.write(''.join([fmt % array[n]] * count))
                items_written += count
            else:
                f.write(('' + str(count) + '*' + fmt % array[n])[:])
                items_written += 1
            n += count
            if items_written > cnt_line:
                f.write('\n')
                items_written = 0
            else:
                f.write(' ')

    np.set_printoptions(suppress=True)
    data = data if data.flags == 'F' and data.ndim == 1 else data.reshape((-1,), order='F')
    fname = fname if isinstance(fname, Path) else Path(fname)
    with open(fname, 'w') as file:
        task = track(range(len(data)), description=f'    saving: {fname.stem} ', refresh_per_second=1, update_period=2)
        file.write(attr + '\n')
        if compressed:
            """"""
            doCompress(file, data)
        else:
            [file.write(f'{data[i]:>.6f} ') if (i + 1) % cnt_line else file.write(f'{data[i]:>.6f}\n') for i in task]
        file.write('/\n')

