# Validation record

校验日期：2026-08-20。

在无图形界面的 Matplotlib 后端下执行：

```bash
MPLBACKEND=Agg python3 plotting/run_all.py
```

结果：`ALL_PLOTTING_PIPELINES_PASS count=23 elapsed_s=42.9`。

最终静态清点：909 个结果数据/日志文件（约 153 MB），25 个集中存放的 Python 文件（其中 23 个可运行流程，另含统一路径模块和一键入口），33 个论文 `fig/` 文件、47 个修订图片归档、53 个重绘图片文件和 31 个重绘表格。包内 C/C++/CUDA、可执行文件及原始 `.bin`/`.vtk` 文件数均为 0；最大单文件约 25.8 MB。

另执行 `python3 verify_release.py` 检查目录结构、论文图片引用、Python 语法、路径可移植性、禁止扩展名、可执行权限、二进制文件魔数、单文件大小、关键生成结果和 SHA-256 清单。校验脚本应输出 `RELEASE_VALIDATION_PASS`。

说明：42.9 秒是本次整理环境中的实测值，仅用于说明全流程已运行；其他机器的耗时会不同。
