import ibm2ieee
import numpy as np
from numpy.lib import recfunctions as rfn
from typing import Literal
from pathlib import Path
from enum import Enum
from .base.base_class import CVDFile
from concurrent.futures import ThreadPoolExecutor
import os
import functools
from rich.progress import track, Progress


def iter_chunks_slice(itrace, n, chunk_size, progressbar=''):
    a, b, st = (slice(None) if itrace is Ellipsis else itrace).indices(n)
    total_len = max(0, (b - a + (st - 1)) // st if st > 0 else (a - b + (-st - 1)) // (-st))
    cnt_chunk = (total_len + chunk_size - 1) // chunk_size
    chunk_iters = track(range(cnt_chunk), description=progressbar, refresh_per_second=1, update_period=2) if progressbar else range(cnt_chunk)
    for i in chunk_iters:
        start = a + i * chunk_size * st
        end   = a + min((i+1) * chunk_size, total_len) * st
        # 计算 slice 的真实长度
        if (st > 0 and start >= b) or (st < 0 and start <= b):
            continue
        yield slice(start, end, st)

def iter_chunks_idxs(itrace, chunk_size, progressbar=''):
    idxs = [itrace] if np.isscalar(itrace) else itrace
    cnt_chunk = (len(idxs) + chunk_size - 1) // chunk_size
    chunk_iters = track(range(cnt_chunk), description=progressbar, refresh_per_second=1, update_period=2) if progressbar else range(cnt_chunk)
    for i in chunk_iters:
        chunk = idxs[i*chunk_size:(i+1)*chunk_size]
        if len(chunk) == 0:
            continue
        yield chunk


def iter_broadcast_chunks(itrace, item=None, chunk_size=1024, progressbar=''):
    """
    按 chunk 迭代广播索引，简洁高效版本。
    """
    # 用占位保证可以广播
    item = np.arange(1) if item is None else item

    # 广播 itrace 和 item
    b = np.broadcast(np.asarray(itrace), np.asarray(item))
    out_shape = b.shape
    total_len = np.prod(out_shape)

    chunks = range((total_len + chunk_size - 1) // chunk_size)
    if progressbar:
        chunks = track(chunks, description=progressbar)

    for i in chunks:
        start, end = i*chunk_size, min((i+1)*chunk_size, total_len)
        lin_idx = np.arange(start, end)
        yield np.unravel_index(lin_idx, out_shape)

def parallelize_io(min_items_for_parallel=100000):
    """
    一个装饰器，用于将针对长序列的IO操作并行化。
    它会检查被装饰方法的第二个参数(假定为'itrace')的长度，
    如果超过阈值，则使用线程池进行并行处理。
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, itrace, *args, **kwargs):
            # 检查itrace是否为标量或长度小于阈值，如果是，则直接调用原函数
            if np.isscalar(itrace) or len(itrace) < min_items_for_parallel:
                return func(self, itrace, *args, **kwargs)

            # 对于长序列，启用多线程
            max_workers = os.cpu_count() or 1
            chunk_size = (len(itrace) + max_workers - 1) // max_workers
            chunks = [itrace[i:i + chunk_size] for i in range(0, len(itrace), chunk_size)]

            # 使用线程池并行执行原函数
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 每个线程调用的是原始的、未被装饰的函数逻辑
                results = list(executor.map(lambda chunk: func(self, chunk, *args, **kwargs), chunks))

            # 将所有线程返回的numpy数组堆叠成一个
            return np.vstack(results)
        return wrapper
    return decorator


def field_to_dtype(type_field, maxsize: int, endian: str):
    """根据字段获取对应的numpy数据类型"""
    dtype_list = []
    fields = list(type_field)
    for i, field in enumerate(fields):
        # 通过字节位置差值确定数据类型
        byte_size = (fields[i + 1].value if i < len(fields) - 1 else (maxsize + 1)) - field.value
        # dtype = (endian + str(byte_size // 4) + 'i4') if byte_size % 4 == 0 else (endian + str(byte_size // 2) + 'i2')
        num_bytes = byte_size // 4 if byte_size % 4 == 0 else byte_size // 2
        dtype = (endian + 'i4') if byte_size % 4 == 0 else (endian + 'i2')
        dtype_list.append(
            (field.name, dtype, num_bytes) if num_bytes != 1 else (field.name, dtype)  # (名称, 数据类型, 个数)
        )
    return dtype_list


class BinField(Enum):
    """二进制头字段枚举类"""
    k1 = 1
    StartInlineID = 5
    k9 = 9
    k13 = 13
    k15 = 15
    SampleRate = 17     # μs
    k19 = 19
    SamplePoints = 21
    k23 = 23
    DataCode = 25
    k27 = 27
    k29 = 29
    k31 = 31
    k33 = 33
    k35 = 35
    k37 = 37
    k39 = 39
    k41 = 41
    k43 = 43
    k45 = 45
    k47 = 47
    k49 = 49
    k51 = 51
    k53 = 53
    CoordUnit = 55
    k57 = 57
    k59 = 59
    k61 = 61
    StartTime = 63
    Unassigned = 67


class TraceField(Enum):
    """道头字段枚举类"""
    Index = 1
    TraceIndex = 5
    InlineID = 9
    k13 = 13
    k17 = 17
    XlineID = 21
    k25 = 25
    TraceValid = 29
    k31 = 31
    k33 = 33
    k35 = 35
    TraceAngle = 37
    TraceAzimuth = 41
    k45 = 45
    k49 = 49
    k53 = 53
    k57 = 57
    k61 = 61
    k65 = 65
    k69 = 69
    CoordScale = 71
    CoordX = 73
    CoordY = 77
    XRCoord = 81
    YRCoord = 85
    CoordUnit = 89
    k91 = 91
    k93 = 93
    k95 = 95
    k97 = 97
    k99 = 99
    k101 = 101
    k103 = 103
    k105 = 105
    k107 = 107
    k109 = 109
    StartTime = 111
    EndTime = 113
    SamplePoints = 115
    SampleRate = 117
    k119 = 119
    k121 = 121
    k123 = 123
    k125 = 125
    k127 = 127
    k129 = 129
    k131 = 131
    k133 = 133
    k135 = 135
    k137 = 137
    k139 = 139
    k141 = 141
    k143 = 143
    k145 = 145
    k147 = 147
    k149 = 149
    k151 = 151
    k153 = 153
    k155 = 155
    Year = 157
    Day = 159
    Hour = 161
    Minute = 163
    Second = 165
    k167 = 167
    k169 = 169
    k171 = 171
    k173 = 173
    k175 = 175
    k177 = 177
    k179 = 179
    k181 = 181
    k185 = 185
    k189 = 189
    k193 = 193
    k197 = 197
    k201 = 201
    k203 = 203
    k205 = 205
    k209 = 209
    k213 = 213
    k217 = 217
    k219 = 219
    k221 = 221
    k225 = 225
    k229 = 229
    k233 = 233
    k237 = 237


class Trace(Enum):
    Header = TraceField
    Data = None


class SEGYConfig:
    """SEG-Y文件格式配置类"""

    def __init__(self, endian):
        # 默认字节序为大端
        self.endian = endian

        # 文本头配置
        self.text_header_size = 3200
        self.text_header_encoding = 'cp500'     # cp037 、 'cp500'、
        self.binary_header_size = 400
        self.trace_header_size = 240

        # 二进制头和道头配置, 默认是大端顺序进行存储
        self._binary_header_dtype = field_to_dtype(BinField, self.binary_header_size, self.endian)
        self._trace_header_dtype = field_to_dtype(TraceField, self.trace_header_size, self.endian)
        self._trace_data_dtype = f'{self.endian}f4'

    def add_binary_field(self, name, dtype, byte_loc):
        """添加二进制头字段"""
        self._binary_header_dtype.append((name, dtype, byte_loc))

    @property
    def binary_header_dtype(self):
        return np.dtype(self._binary_header_dtype)

    def add_trace_field(self, name, dtype, byte_loc):
        """添加道头字段"""
        self._trace_header_dtype.append((name, dtype, byte_loc))

    @property
    def trace_header_dtype(self):
        return np.dtype(self._trace_header_dtype)

    @property
    def trace_data_dtype(self):
        return np.dtype(self._trace_data_dtype)


_MemMapModeKind = Literal[
    "readonly", "r",
    "copyonwrite", "c",
    "readwrite", "r+",
    "write", "w+",
]


def ieee2ibm32(ieee_binary):
    ieee_binary = ieee_binary
    sign = (ieee_binary >> np.uint32(31)) & np.uint32(0x1)
    exponent = ((ieee_binary >> np.uint32(23)) & np.uint32(0xFF)) - np.uint32(127)
    mantissa = (ieee_binary & np.uint32(0x7FFFFF)) | np.uint32(0x800000)  # 补齐隐含位

    ibm_exponent = (exponent // np.uint32(4)) + np.uint32(64)
    ibm_mantissa = mantissa << (exponent % np.uint32(4))

    ibm_int = (sign << np.uint32(31)) | (ibm_exponent << np.uint32(24)) | (ibm_mantissa & np.uint32(0xFFFFFF))
    return ibm_int

# ieee = np.array([1,2,3,4], dtype='f4')
# # ibm = ieee2ibm32(ieee.view('u4')[:])[:]
# # t = ibm.tobytes(), ibm[0].view('>u4').tobytes()
# ieee.dtype.byteorder
# ibm = np.vectorize(ieee2ibm32)(ieee.view('u4')[:])
# a = ibm2ieee.ibm2float32(ibm.view('u4')[:])[:]
# print()


class SEGYKey(object):
    """"""
    decoder = {
        0: lambda x: x,     # 新建segy数据时，默认用此模式
        1: lambda x: ibm2ieee.ibm2float32(x.view(dtype='>u4')),  # 支持IBM格式数据读取
        5: lambda x: x
    }
    encoder = {
        0: lambda x: x,     # 保存新建的segy数据时，默认用此模式
        1: lambda x: ieee2ibm32(x),    # 目前还没有解决这个问题
        5: lambda x: x,
    }
    d = {
        0: "4-byte IEEE float",     # 保存新建的segy数据时，默认用此模式
        -2: "4-byte native big-endian float",
        -1: "4-byte native little-endian float",
        1: "4-byte IBM float",
        2: "4-byte signed integer",
        3: "2-byte signed integer",
        4: "4-byte fixed point with gain",
        5: "4-byte IEEE float",
        6: "8-byte IEEE float",
        7: "3-byte signed integer",
        8: "1-byte signed char",
        9: "8-byte signed integer",
        10: "4-byte unsigned integer",
        11: "2-byte unsigned integer",
        12: "8-byte unsigned integer",
        15: "3-byte unsigned integer",
        16: "1-byte unsigned char"
    }

    slots = ['floatformat', 'smp_rate', 'smp_cnt', 'smp_start', 'smp_stop', 'smp_seq', 'trace_cnt', 'coord_scale']
    def __init__(self):
        self.floatformat = None
        # 获取基本信息
        self.smp_rate = None    # ms
        self.smp_cnt = None

        # 计算采样序列
        self.smp_start = None
        self.smp_stop = None
        self.smp_seq = None

        # 道数等
        self.trace_cnt = None
        self.coord_scale = None


class SEGYMap(CVDFile, SEGYKey):
    """基于numpy.memmap的SEG-Y文件读取类"""
    chunk_size = 1000 # 读取道头时，每次读取的道数

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._trace is not None:
            self._trace.flush()
            self._trace = None


    slots = CVDFile.slots + SEGYKey.slots + ['endian', 'config', '_file_path', '_mode', '_cache_text_header', '_cache_binary_header', '_trace_memmap']
    def __init__(self, file_path, endian='>', mode: _MemMapModeKind = 'r'):
        CVDFile.__init__(self)
        SEGYKey.__init__(self)
        self.endian = endian
        self.config = SEGYConfig(endian)
        self._file_path = Path(file_path)
        self._mode: _MemMapModeKind = mode
        self._cache_text_header = None
        self._cache_binary_header = None
        self._cache_trace : np.memmap = None    # 用于缓存道数据内存映射
        self._trace_memmap: functools.partial = None  # 用于创建道数据内存映射
        # 关键信息获取,建立与道的映射关系
        self.ReadKeyInfo()
        self.SetTraceMapping()


    @property
    def _trace(self):
        if self._cache_trace is None:
            self._cache_trace = self._trace_memmap()
        return self._cache_trace

    # def CopyNew(self, new_file_path):
    #     """w+模式，会自动创建文件，并以r+模式修改数据
    #     :param new_file_path:
    #     :return:
    #     """
    #     instance: SEGYMap = CVDFile.new(self, self.__class__)
    #     # 创建对应的segy文件
    #     instance._file_path = Path(new_file_path)
    #     instance._mode = 'w+'
    #     # 写入数据
    #     instance.text_header = self.text_header
    #     instance.binary_header = self.binary_header
    #     offset = instance.config.text_header_size + instance.config.binary_header_size
    #     dtype = np.dtype([(Trace.Header.name, instance.config.trace_header_dtype),  # 道头部分
    #                       (Trace.Data.name, self.config.trace_data_dtype, (instance.smp_cnt,))  # 道数据部分
    #                       ])
    #     instance._trace = np.memmap(instance._file_path, dtype=dtype, mode=instance.mode, offset=offset, shape=(instance.trace_cnt,))
    #     a = instance.traceHeader(0, TraceField.CoordScale)
    #     instance.text_header = instance.text_header
    #     instance.binary_header = instance.binary_header
    #     return instance

    @property
    def mode(self) -> _MemMapModeKind:
        if self._mode in ["w+", "write"]:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            open(self._file_path, mode=self._mode).close()
            self._mode: _MemMapModeKind = 'r+'
            print(f"Warning: you should use {self.__class__.__name__}.SetTraceMapping to set trace_cnt after setting binary header while using 'w+' mode, and binary header must set the SamplePoints value.")
        return self._mode

    @property
    def text_header(self):
        """
        动态读取, 只能采用该方式得到数据
        :return:
        """
        # 文本头映射
        if self._cache_text_header is None:
            fp = np.memmap(self._file_path, dtype=f'S{self.config.text_header_size}', mode=self.mode, shape=(1,))
            self._cache_text_header = fp.tobytes().decode(self.config.text_header_encoding, errors='ignore')
            del fp  # 删除对象以确保关闭内存映射
        return self._cache_text_header.replace('\0', '')

    @text_header.setter
    def text_header(self, text: str):
        """
        动态更新，只能采用该方式更新数据
        :param text:
        :return:
        """
        if len(text) <= 3200:
            self._cache_text_header = text
            fp = np.memmap(self._file_path, dtype=f'S{self.config.text_header_size}', mode=self.mode, shape=(1,))
            fp[:] = self._cache_text_header.encode(self.config.text_header_encoding)
            fp.flush()
            del fp  # 删除对象以确保关闭内存映射
        else:
            raise IOError('the size of text must be 3200!')

    @property
    def binary_header(self):
        """
        动态读取, 只能采用该方式得到数据
        :return:
        """
        if self._cache_binary_header is None:
            # 二进制头映射
            fp = np.memmap(self._file_path, dtype=self.config.binary_header_dtype, mode=self.mode, offset=self.config.text_header_size, shape=(1,))
            self._cache_binary_header = np.void(fp[0])
            del fp  # 删除对象以确保关闭内存映射
        return self._cache_binary_header

    @binary_header.setter
    def binary_header(self, value):
        """
        动态更新，只能采用该方式更新数据
        :param value:
        :return:
        """
        if value.nbytes == self.config.binary_header_size:
            self._cache_binary_header = value.copy()
            # 二进制头映射
            fp = np.memmap(self._file_path, dtype=self.config.binary_header_dtype, mode=self.mode,
                           offset=self.config.text_header_size, shape=(1,))
            fp[:] = self._cache_binary_header
            fp.flush()
            del fp  # 删除对象以确保关闭内存映射
            self.ReadKeyInfo()  # 更新关键字参数
        else:
            raise IOError(f'the size of value must be {self.config.binary_header_size}!')

    # @parallelize_io(min_items_for_parallel=100000)
    def traceData(self, itrace, item=None, progressbar=''):
        """
        用接口来读取对应地震数据
        :param itrace:  地震数据读取索引
        :param item: 对读取的地震数据进行切片或者花式索引操作, 有切片、整数、花式索引、Ellipsis, None。 a[i, j, k] 和 a[i, j][..., k] 结果一样
        :return: 一定是矩阵数据（四四方方）
        """
        views = self._trace[Trace.Data.name][itrace, item if item is not None else Ellipsis]
        if np.isscalar(views):
            return  self.decoder[self.floatformat](views)
        cnt_chunk = (len(views) + self.chunk_size - 1) // self.chunk_size
        output = np.empty(views.shape, dtype=views.dtype)
        iter_chunks = track(range(cnt_chunk), description=progressbar, refresh_per_second=1, update_period=2) if progressbar else range(cnt_chunk)
        # for i in iter_chunks:
        #     view = views[i*self.chunk_size:(i+1)*self.chunk_size]
        #     if len(view) == 0:
        #         continue
        #     np.copyto(output[i*self.chunk_size:i*self.chunk_size+len(view)], view, casting='no')
        [np.copyto(output[i*self.chunk_size:i*self.chunk_size+len(view)], view, casting='no') for i in iter_chunks 
         for view in [views[i*self.chunk_size:(i+1)*self.chunk_size]]]
        return self.decoder[self.floatformat](output)



        # 根据itrace类型，获取对应的迭代器和大小
        # if itrace is Ellipsis or isinstance(itrace, slice): # 切片
        #     iter_chunks = iter_chunks_slice(itrace, self.trace_cnt, self.chunk_size, progressbar=progressbar)
        #     a, b, st  = (slice(None) if itrace is Ellipsis else itrace).indices(self.trace_cnt)
        #     total_len = max(0, (b - a + (st - 1)) // st if st > 0 else (a - b + (-st - 1)) // (-st))
        #     cnt_chunk = (total_len + self.chunk_size - 1) // self.chunk_size
        # else: # 整数或数组, 考虑到花式索引，所以不能计算size了
        #     iter_chunks = iter_chunks_idxs(itrace, self.chunk_size, progressbar=progressbar)
        #     cnt_chunk = ((1 if np.isscalar(itrace) else len(itrace)) + self.chunk_size - 1) // self.chunk_size

        # get_view = lambda chunk : self._trace[Trace.Data.name][chunk] if item is None or item is Ellipsis else self._trace[Trace.Data.name][chunk, item]
        # output =  None
        # offset = 0
        # for i, chunk in enumerate(iter_chunks):
        #     view = get_view(chunk=chunk)
        #     output = np.empty((cnt_chunk, *view.shape), dtype=view.dtype) if output is None else output
        #     chunk_len = len(view)
        #     if chunk_len == 0:
        #         continue
        #     np.copyto(output[i], view, casting='no')
        
        # output = output.reshape(-1, *output.shape[2:])
      
        # return output[0] if np.isscalar(itrace) and np.isscalar(item) else output




        # if item is None:
        #     return self.decoder[self.floatformat](self._trace[itrace][Trace.Data.name])
        # else:
        #     return self.decoder[self.floatformat](self._trace[itrace][Trace.Data.name][*item])
    
    def SetTraceData(self, itrace, traceData, item=None, progressbar=''):
        """

        :param itrace:
        :param traceData: 迭代器或者矩阵， 且迭代器可以len()
        :return:
        """
        if self.floatformat == 1:
            self.binary_header[BinField.DataCode.name] = 5
            self.binary_header = self.binary_header
            import warnings
            warnings.warn('雷达encoder中，保存为IBMfloat32格式代码还没写好，暂时以IEEE格式保存')
            self.SetTraceData(itrace, traceData, item)
            return True
        
        views = self._trace[Trace.Data.name][itrace, item if item is not None else Ellipsis]
        if np.isscalar(views):
            views = traceData
            return views
        cnt_chunk = (len(views) + self.chunk_size - 1) // self.chunk_size
        iter_chunks = track(range(cnt_chunk), description=progressbar, refresh_per_second=1, update_period=2) if progressbar else range(cnt_chunk)
        # for i in iter_chunks:
        #     view = views[i*self.chunk_size:(i+1)*self.chunk_size]
        #     if len(view) == 0:
        #         continue
        #     np.copyto(output[i*self.chunk_size:i*self.chunk_size+len(view)], view, casting='no')
        [np.copyto(view, traceData[i*self.chunk_size:(i+1)*self.chunk_size], casting='no') for i in iter_chunks 
         for view in [views[i*self.chunk_size:(i+1)*self.chunk_size]]]
        self._trace.flush()
        return True


        # if item is None:
        #     for idx, data in zip(itrace, self.encoder[self.floatformat](traceData)):
        #         self._trace[idx][Trace.Data.name] = data
        #     # self._trace[itrace][Trace.Data.name] = self.encoder[self.floatformat](traceData) 不能这样赋值
        # else:
        #     for idx, data in zip(itrace, self.encoder[self.floatformat](traceData)):
        #         self._trace[idx][Trace.Data.name][*item] = data
        # self._trace.flush()
        # return True

    def traceHeader(self, itrace, *keys: TraceField, progressbar=''):
        """

        :param itrace:   地震数据读取索引: 数组、切片、整数、Ellipsis
        :param keys:  枚举类型的关键字
        :param progressbar:  进度条描述, 空字符串不显示进度条
        :return:
        """
        fields = [k.name for k in keys]
        views = self._trace[[itrace] if np.isscalar(itrace) else itrace][Trace.Header.name][fields]
        cnt_chunk = (len(views) + self.chunk_size - 1) // self.chunk_size
        output = np.empty(len(views), dtype=self.config.trace_header_dtype[fields])
        iter_chunks = track(range(cnt_chunk), description=progressbar, refresh_per_second=1, update_period=2) if progressbar else range(cnt_chunk)
        for i in iter_chunks:
            view = views[i*self.chunk_size:(i+1)*self.chunk_size]
            if len(view) == 0:
                continue
            np.copyto(output[i*self.chunk_size:i*self.chunk_size+len(view)], view, casting='no')
        # [np.copyto(output[i*self.chunk_size:i*self.chunk_size+len(view)], view, casting='no') for i in iter_chunks 
        #  for view in [views[i*self.chunk_size:(i+1)*self.chunk_size]]]
        return output[0][0] if np.isscalar(itrace) and len(keys) == 1 else output
    

        # if itrace is Ellipsis or isinstance(itrace, slice): # 切片
        #     iter_chunks = iter_chunks_slice(itrace, self.trace_cnt, self.chunk_size, progressbar=progressbar)
        #     a, b, st  = (slice(None) if itrace is Ellipsis else itrace).indices(self.trace_cnt)
        #     size = max(0, (b - a + (st - 1)) // st if st > 0 else (a - b + (-st - 1)) // (-st))
        # else: # 整数或数组
        #     iter_chunks = iter_chunks_idxs(itrace, self.chunk_size, progressbar=progressbar)
        #     size = len([itrace] if np.isscalar(itrace) else itrace)
        # fields = [k.name for k in keys]
        # output = np.empty(size, dtype=self.config.trace_header_dtype[fields])
        # offset = 0
        # for chunk in iter_chunks:
        #     view  = self._trace[chunk][Trace.Header.name]
        #     chunk_len = len(view)
        #     if chunk_len == 0:
        #         continue
        #     np.copyto(output[offset:offset+chunk_len][fields], view[fields], casting='no')
        #     offset += chunk_len
      
        # return output[0][0] if output.size == 1 and len(fields) == 1 else output

    def SetTraceHeader(self, itrace, traceHeader, progressbar=''):
        """
        :param itrace:
        :param traceHeader:
        :param progressbar:  进度条描述, 空字符串不显示进度条
        :return:
        """
        if itrace is Ellipsis or isinstance(itrace, slice): # 切片
            iter_chunks = iter_chunks_slice(itrace, self.trace_cnt, self.chunk_size, progressbar=progressbar)
            a, b, st  = (slice(None) if itrace is Ellipsis else itrace).indices(self.trace_cnt)
            size = max(0, (b - a + (st - 1)) // st if st > 0 else (a - b + (-st - 1)) // (-st))
        else: # 整数或数组
            iter_chunks = iter_chunks_idxs(itrace, self.chunk_size, progressbar=progressbar)
            size = len([itrace] if np.isscalar(itrace) else itrace)

        # 按 memmap 内部顺序获取字段
        aligned_fields = [f for f in self.config.trace_header_dtype.names if f in traceHeader.dtype.names]

        if size != len(traceHeader):
            raise ValueError(f"the size of traceHeader must be {size}!")

        # 对 traceHeader 生成按 memmap 顺序排列的视图，不复制数据
        traceHeader_view = rfn.repack_fields(traceHeader[aligned_fields])

        # 直接赋值到 memmap
        offset = 0
        for chunk in iter_chunks:
            view = self._trace[chunk][Trace.Header.name]
            chunk_len = len(view)
            if chunk_len == 0:
                continue
            view[aligned_fields] = traceHeader_view[offset:offset+chunk_len]
            offset += chunk_len

        self._trace.flush()

    def SetTraceMapping(self, set_trace_cnt: int = 1):
        """
        初始化道数据内存映射, 只能在设置了二进制头后调用
        :param set_trace_cnt: ①创建segy时默认道数为1，读取segy会自动读取对应道数
        :return:
        """
        # 数据区映射
        offset = self.config.text_header_size + self.config.binary_header_size
        dtype = np.dtype([(Trace.Header.name, self.config.trace_header_dtype),  # 道头部分
                          (Trace.Data.name, f'{self.endian}f4', (self.smp_cnt,))  # 道数据部分
                          ])
        # 计算道数
        trace_size = self.config.trace_header_size + self.smp_cnt * 4
        file_trace_cnt = (self._file_path.stat().st_size - (
                    self.config.text_header_size + self.config.binary_header_size)) // trace_size
        self.trace_cnt = max(file_trace_cnt, set_trace_cnt)     #  ①创建segy时默认道数为1，读取segy会自动读取对应道数
        self._trace_memmap = functools.partial(np.memmap, filename=self._file_path, dtype=dtype, mode=self.mode, offset=offset, shape=(self.trace_cnt,))
        self.coord_scale = self.traceHeader(0, TraceField.CoordScale)
        # self.coord_scale = 1 if not self.coord_scale else pow(abs(self.coord_scale) + 0.0,  1 if self.coord_scale > 0 else -1)
        self.coord_scale = 1 if not self.coord_scale else abs(self.coord_scale)
        return self

    def ReadKeyInfo(self):
        """读取关键信息"""
        # 地震数据加密格式
        self.floatformat = self.binary_header[BinField.DataCode.name]
        try:
            format_str = 'unknown format!'
            format_str = self.d[self.floatformat]
        except KeyError:
            raise Warning(f"Warning! Unsupported data format: {format_str}, there are may be some problems!")

        # 获取基本信息
        self.smp_rate = self.binary_header[BinField.SampleRate.name] / 1000  # μs to ms
        self.smp_cnt = int(self.binary_header[BinField.SamplePoints.name])

        # 计算采样序列
        self.smp_start = self.binary_header[BinField.StartTime.name]  # 默认从0开始
        self.smp_stop = float(self.smp_start + (self.smp_cnt - 1) * self.smp_rate)
        self.smp_seq = np.arange(self.smp_start, self.smp_stop + 1, self.smp_rate) if self.smp_start != self.smp_stop else None

    @staticmethod
    def Data2Segy(sgy_path: str | Path, inlineIDs: list, xlineIDs: list, smp_seq: list, smp_rate, tracesData: np.ndarray, text_header: str):
        """
        保存道数据
        :param sgy_path: sgy文件路径
        :param inlineIDs: 道数
        :param xlineIDs: 道数
        :param smp_seq: 样本数
        :param smp_rate: 采样率 (ms)
        :param tracesData: 道数据 shape=(n_inline, n_xline, n_smp)
        :param text_header: 文本头
        :return: sgy_writer
        """

        n_inline, n_xline, n_smp = len(inlineIDs), len(xlineIDs), len(smp_seq)
        # a. 创建SGY文件
        sgy_writer = SEGYMap(sgy_path, mode='w+')

        # b. 设置文本头
        sgy_writer.text_header = text_header

        # c. 设置二进制文件头、道头和道数据
        bh = sgy_writer.binary_header
        bh[BinField.SamplePoints.name] = n_smp
        bh[BinField.SampleRate.name] = 2000 # μs in binary header
        sgy_writer.binary_header = bh   # 更新二进制文件头
        sgy_writer.SetTraceMapping(set_trace_cnt=n_inline * n_xline)
        
        # d. 创建道头
        headers = np.zeros(n_xline, dtype=sgy_writer.config.trace_header_dtype)
        headers[TraceField.SamplePoints.name] = n_smp
        headers[TraceField.SampleRate.name] = smp_rate * 1000  # 2ms in trace header

        
        print(f'    Saving data to : {sgy_path}')
        itr_lines = track(range(n_inline), description=f'    processing', refresh_per_second=1, update_period=2)

        for i in itr_lines:
            headers[TraceField.InlineID.name] = inlineIDs[i]
            headers[TraceField.XlineID.name] = xlineIDs
            sgy_writer.SetTraceHeader(i * n_xline + np.arange(n_xline), headers)
            sgy_writer.SetTraceData(i * n_xline + np.arange(n_xline), tracesData[i])
        
        return sgy_writer

    def __len__(self):
        """返回道数"""
        return self.trace_cnt
    

    def __getstate__(self) -> object:
        state = super().__getstate__()
        state['_cache_trace'] = None    # 避免序列化道数据内存映射
        return state
    
