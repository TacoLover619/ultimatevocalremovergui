# Windows 11 build

The Windows build uses Python 3.12, PyInstaller 6, PyTorch 2.9.1 with CUDA
12.6, and ONNX Runtime GPU. CUDA execution falls back to CPU on systems that
do not have a compatible NVIDIA GPU or driver.

## Build

Install 64-bit Python 3.12, then run from PowerShell:

```powershell
.\build_windows.ps1 -CleanEnvironment
```

To use a specific Python installation:

```powershell
.\build_windows.ps1 -CleanEnvironment -PythonBootstrap 'C:\Python312\python.exe'
```

The script creates an isolated environment, installs the locked dependencies,
downloads FFmpeg and Rubber Band, and builds the portable application at:

```text
dist\Ultimate Vocal Remover\Ultimate Vocal Remover.exe
```

Keep the entire `Ultimate Vocal Remover` directory together when moving the
application. The executable depends on its `_internal` directory.

## Verify source changes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q UVR.py separate.py demucs lib_v5 gui_data tests
```

The build intentionally uses PyInstaller's directory layout. A single-file
bundle would unpack several gigabytes of model runtimes on every launch and
would substantially increase startup time.
