# GridSeisPy

# Usage (基于 examples/usage.py 的完整演练)

以下示例演示 GridSeisPy 的核心工作流：创建一个示例 SEG-Y 文件 → 加载并保存会话 → 从会话恢复对象 → 创建层位并进行运算与切片 → 可视化结果。

步骤概览
- 创建输出目录与示例 `SEG-Y` 文件
- 加载数据，保存工作流会话，并从会话恢复
- 创建顶/底层位并进行层位运算（时间厚度）
- 获取剖面、沿层切片、层间数据与区域提取
- 可视化

示例代码（可直接运行）：
```python
import sys
from pathlib import Path
import numpy as np

# 设置 Matplotlib 后端（如本地运行可使用 TkAgg）
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# 字体/显示设置（可按需调整）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

from GridSeisPy import SeisData, Horiz, BinField, TraceField, CVDFile

def main():
    # 0) 输出目录与示例 SGY 路径
    output_dir = Path(__file__).resolve().parent / "GridSeisPy" / "examples" / "usage_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sgy_path = str(output_dir / "demo_seismic.sgy")

    # 设置会话保存路径（用于保存/恢复对象）
    CVDFile.SetVDPath(output_dir)

    # 1) 创建示例 SEG-Y 文件
    n_il, n_xl, n_smp = 50, 60, 120
    trace_cnt = n_il * n_xl
    tracesData = np.array([
        np.sin(np.linspace(0, 2 * np.pi, n_smp)) * (i / trace_cnt)
        for i in range(trace_cnt)
    ], dtype='f4').reshape(n_il, n_xl, n_smp)

    SeisData.Data2Segy(
        sgy_path,
        inlineIDs=list(range(n_il)),
        xlineIDs=list(range(n_xl)),
        smp_seq=list(range(n_smp)),
        smp_rate=2000,
        tracesData=tracesData,
        text_header="",
    )

    # 2) 加载数据并保存/恢复会话
    sgy = SeisData(sgy_path).load()
    sgy.Update2VDFile('my_demo_sgy')
    sgy = None  # 模拟新会话
    sgy = SeisData.GetObjByName('my_demo_sgy')

    # 3) 创建顶/底层位并进行运算
    top_horiz = sgy.getSeiHoriz()
    btm_horiz = sgy.getSeiHoriz()

    xx, yy = np.meshgrid(
        np.linspace(0, 1, sgy.shape[1]),
        np.linspace(0, 1, sgy.shape[0])
    )
    top_time = 40 + (np.sin(xx * 2 * np.pi) + np.cos(yy * 2 * np.pi)) * 10
    btm_time = top_time + 20
    top_horiz.elems['time'] = top_time.astype('i4')
    btm_horiz.elems['time'] = btm_time.astype('i4')

    # 4) 获取剖面、沿层切片、层间数据
    inline_to_show = sgy.arrInlines[sgy.shape[0] // 2]
    inline_slice = sgy.getInline(inline_to_show)
    slice_along_top = sgy[..., top_horiz]
    data_between = sgy[..., top_horiz:btm_horiz]
    trace_between = data_between[sgy.shape[0] // 2, sgy.shape[1] // 2]

    # 5) 可视化
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("GridSeisPy usage walkthrough")

    # a) 剖面
    axes[0].imshow(
        inline_slice.T, cmap='seismic', aspect='auto',
        extent=[sgy.arrXlines[0], sgy.arrXlines[-1], sgy.smp_stop, sgy.smp_start]
    )
    axes[0].set_title(f"Inline {inline_to_show}")
    axes[0].set_xlabel("Xline")
    axes[0].set_ylabel("Time (ms)")

    # b) 沿顶层位切片
    im = axes[1].imshow(
        slice_along_top, cmap='viridis', aspect='auto',
        extent=[sgy.arrXlines[0], sgy.arrXlines[-1], sgy.arrInlines[-1], sgy.arrInlines[0]]
    )
    axes[1].set_title("Slice Along Top Horizon")
    axes[1].set_xlabel("Xline")
    axes[1].set_ylabel("Inline")
    fig.colorbar(im, ax=axes[1], label="Amplitude")

    # c) 层间单道（相对时间轴）
    time_axis = np.arange(len(trace_between)) * (sgy.smp_rate / 1000) + top_horiz.elems['time'].min()
    axes[2].plot(trace_between, time_axis)
    axes[2].set_title("Trace Between Horizons")
    axes[2].set_xlabel("Amplitude")
    axes[2].set_ylabel("Relative Time (ms)")
    axes[2].invert_yaxis()
    axes[2].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == '__main__':
    main()
```

要点小结
- 会话管理：`CVDFile.SetVDPath` 设置持久化路径，`Update2VDFile` 保存对象，`GetObjByName` 恢复对象。
- 读写 I/O：`SeisData.Data2Segy` 可快速写出示例 `SEG-Y`；`SeisData(...).load()` 读取并构建网格化数据。
- 层位对象：`getSeiHoriz()` 创建层位，可直接做差得到时间厚度等派生量。
- 切片索引：支持 inline/xline、沿层切片、层间区间以及区域提取（参见 `examples/usage.py` 更多演示）。

A Python library for seismic data processing and visualization, designed for efficiency and ease of use.

## Features

-   **Workflow Session Management**: Automatically save and restore processed objects (`SeisData`, `Horiz`) to disk, allowing you to resume your work across different sessions.
-   **Fast I/O**: Efficiently read and write SEG-Y files.
-   **Intuitive Slicing**: Slice data by inline/crossline, time/depth, or along and between horizons (e.g., `sgy.getInline(100)`, `sgy[..., top:btm]`).
-   **Advanced Indexing**: Supports `numpy`-style regional extraction using `np.ogrid`.
-   **Horizon Arithmetic**: Perform calculations directly on horizon objects (e.g., `thickness = btm_horiz - top_horiz`).
-   **Grid & Coordinate Tools**: Built-in utilities for grid and coordinate transformations.
-   **Easy Visualization**: The library's outputs are standard NumPy arrays, making it straightforward to integrate with plotting libraries like Matplotlib.

## Installation

You can install GridSeisPy via pip:

```bash
pip install GridSeisPy
```

## Complete Walkthrough

This example demonstrates the core workflow: creating a SEG-Y file, loading it, saving and restoring the session, performing advanced operations (like slicing, horizon math, and coordinate conversion), and finally visualizing the results with Matplotlib.

This code is self-contained and runnable.

```python
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from GridSeisPy import SeisData, Horiz, BinField, TraceField, CVDFile

# --- Plotting Setup ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# --- 1. Setup Session and Paths ---
print("--- 1. Setting up session and paths ---")
output_dir = Path("usage_output")
output_dir.mkdir(exist_ok=True)
sgy_path = output_dir / "demo_seismic.sgy"
CVDFile.SetVDPath(output_dir)
print(f"Session files will be saved in: {output_dir.resolve()}\\n")

# --- 2. Create a Demo SEG-Y File ---
print(f"--- 2. Creating a new SEG-Y file at '{sgy_path}' ---")
n_il, n_xl, n_smp = 50, 60, 120
trace_cnt = n_il * n_xl

with SeisData(str(sgy_path), mode='w+') as sgy_writer:
    headers = np.zeros(trace_cnt, dtype=sgy_writer.config.trace_header_dtype)
    headers[TraceField.InlineID.name] = np.repeat(np.arange(100, 100 + n_il), n_xl)
    headers[TraceField.XlineID.name] = np.tile(np.arange(500, 500 + n_xl), n_il)
    headers[TraceField.SamplePoints.name] = n_smp
    headers[TraceField.SampleRate.name] = 2000

    data = np.array([np.sin(np.linspace(0, 2 * np.pi, n_smp)) * (i / trace_cnt)
                     for i in range(trace_cnt)], dtype='f4')

    bh = sgy_writer.binary_header
    bh[BinField.SamplePoints.name] = n_smp
    bh[BinField.SampleRate.name] = 2000
    sgy_writer.binary_header = bh
    
    sgy_writer.SetTraceMapping(set_trace_cnt=trace_cnt)
    sgy_writer.SetTraceHeader(np.arange(trace_cnt), headers)
    sgy_writer.SetTraceData(np.arange(trace_cnt), data)
print("SEG-Y file created successfully.\\n")

# --- 3. Load Data, Save, and Restore Session ---
print("--- 3. Loading, saving, and restoring session ---")
sgy = SeisData(str(sgy_path)).load()
sgy.Update2VDFile('my_demo_sgy')
sgy_restored = SeisData.GetObjByName('my_demo_sgy')
print(f"Loaded and restored data with shape: {sgy_restored.shape}\\n")

# --- 4. Create Horizons and Perform Operations ---
print("--- 4. Performing horizon operations and advanced slicing ---")
top_horiz = sgy_restored.getSeiHoriz()
btm_horiz = sgy_restored.getSeiHoriz()
xx, yy = np.meshgrid(np.linspace(0, 1, sgy_restored.shape[1]), np.linspace(0, 1, sgy_restored.shape[0]))
top_time = 40 + (np.sin(xx * 2 * np.pi) + np.cos(yy * 2 * np.pi)) * 10
btm_time = top_time + 20
top_horiz.elems['time'] = top_time.astype('i4')
btm_horiz.elems['time'] = btm_time.astype('i4')

# Operations
inline_to_show = sgy_restored.arrInlines[sgy_restored.shape[0] // 2]
inline_slice = sgy_restored.getInline(inline_to_show)
slice_along_top = sgy_restored[..., top_horiz]
time_thickness = btm_horiz - top_horiz

center_i, center_j = sgy_restored.shape[0] // 2, sgy_restored.shape[1] // 2
center_x, center_y = sgy_restored.elems[sgy_restored.kX][center_i, center_j], sgy_restored.elems[sgy_restored.kY][center_i, center_j]
converted_i, converted_j = sgy_restored.xy2ij([center_x], [center_y])
print(f"Coordinate ({center_x:.2f}, {center_y:.2f}) converts to grid index ({converted_i[0]}, {converted_j[0]})\\n")


# --- 5. Visualization ---
print("--- 5. Visualizing the results ---")
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("GridSeisPy 'usage.py' 演示")

# a. Inline Profile
sgy = sgy_restored
axes[0].imshow(inline_slice.T, cmap='seismic', aspect='auto',
               extent=[sgy.arrXlines[0], sgy.arrXlines[-1], sgy.smp_stop, sgy.smp_start])
axes[0].set_title(f"剖面: Inline {inline_to_show}")
axes[0].set_xlabel("Xline")
axes[0].set_ylabel("Time (ms)")

# b. Slice Along Horizon
im = axes[1].imshow(slice_along_top, cmap='viridis', aspect='auto',
                    extent=[sgy.arrXlines[0], sgy.arrXlines[-1], sgy.arrInlines[-1], sgy.arrInlines[0]])
axes[1].set_title("沿顶层位切片")
axes[1].set_xlabel("Xline")
axes[1].set_ylabel("Inline")
fig.colorbar(im, ax=axes[1], label="Amplitude")

# c. Time Thickness Map
im_thick = axes[2].imshow(time_thickness.elems[time_thickness.kField], cmap='jet', aspect='auto',
                         extent=[sgy.arrXlines[0], sgy.arrXlines[-1], sgy.arrInlines[-1], sgy.arrInlines[0]])
axes[2].set_title("层位时间厚度图 (btm - top)")
axes[2].set_xlabel("Xline")
axes[2].set_ylabel("Inline")
fig.colorbar(im_thick, ax=axes[2], label="Time Thickness (ms)")

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

```

## Future Plans

`GridSeisPy` is under active development. Here are some of the exciting features planned for the future:

*   **Easy Seismic Attribute Extraction**: We plan to add a comprehensive module for calculating various seismic attributes. The goal is to make extracting attributes like instantaneous frequency, phase, and amplitude as simple as a few lines of code.
*   **AI Integration**: A major focus will be on bridging the gap between seismic data and modern AI. We aim to provide seamless integration with popular deep learning frameworks (like PyTorch and TensorFlow) to facilitate research and application of AI in seismic interpretation.

## License

This project is licensed under the MIT License. 