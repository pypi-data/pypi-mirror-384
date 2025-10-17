# Timesat

**Timesat** provides Python bindings for the [TIMESAT](https://github.com/TIMESAT) algorithms — a suite of routines for analyzing time-series of satellite remote sensing data.  
This package wraps the original **Fortran-based TIMESAT core** into a modern Python interface for convenient use in data analysis and research workflows.

---

## Features

- Native Python bindings for the **TIMESAT Fortran core**
- Cross-platform precompiled binaries (macOS Intel & ARM, Linux, Windows)
- Supports **Python 3.10–3.12**
- Compatible with **NumPy ≥ 2.0**
- Provides high performance through the compiled Fortran backend
- Simple API for fitting and extracting vegetation metrics from time-series data

---

## Installation

You can install the latest release directly from PyPI:

```bash
pip install timesat
```

---

## License
See the [LICENSE](./LICENSE) file for details.

---

## Citation
If you use this package or the underlying TIMESAT algorithms in your research, please cite the official TIMESAT publication(s) and refer to the official TIMESAT repository at:

👉 https://github.com/TIMESAT/TIMESAT

Specifically, please cite the original ROI and algorithm references provided there.
At the time of writing, the primary reference is: