# Ultimate Vocal Remover GUI v6.0.0

Version 6.0 updates UVR for Windows 11 and Python 3.12. Existing separation
workflows, model formats, the interface, and the model download system are
unchanged. This release updates model loading, audio processing, NVIDIA GPU
support, dependencies, and Windows packaging.

## Download and installation

This release uses an original-style Windows setup package. Because the complete
CUDA application is larger than GitHub's 2 GiB per-file limit, the installer is
split into three required files:

- `UVR_v6.0.0_setup.exe`
- `UVR_v6.0.0_setup-1.bin`
- `UVR_v6.0.0_setup-2.bin`

Download all three files into the same folder. Do not rename them. Run
`UVR_v6.0.0_setup.exe`; the setup program reads both numbered data files
automatically. `SHA256SUMS.txt` is provided for integrity verification.

The installer window must say `Setup - Ultimate Vocal Remover v6.0.0`. If it
says version 5.6.1, cancel the installation. That is an older setup package and
is not one of the files attached to this release. The SHA-256 value for the v6.0
setup EXE is:

```text
A6393BCE4524F5FBACAFE66777741E2EE2C1F9EF93D52F92D106552268884DEF
```

The installer is 64-bit, targets Windows 10 build 17763 or newer (including
Windows 11), installs per user by default, creates a Start Menu entry, offers an
optional Desktop shortcut, and registers a normal Windows uninstaller. No
separate Python installation is required.

The setup package uses the original UVR Windows installer identity. Running it
over version 5.6.1 upgrades the existing installation and its Installed Apps
entry instead of registering a separate copy.

## Runtime modernization

- Moved the supported application runtime to Python 3.12.
- Updated the Windows ML stack to PyTorch 2.9.1 with CUDA 12.6 support.
- Updated ONNX Runtime GPU execution and retained CPU fallback.
- Updated Librosa and adapted calls whose modern APIs require keyword-only
  arguments.
- Updated NumPy, SciPy, SoundFile, Audioread, OpenCV headless, and supporting
  audio/runtime packages to current compatible versions.
- Added explicitly declared packages used by the source but missing or
  unreliable in the legacy requirements, including OmegaConf, tqdm, and
  pyrubberband.
- Added an exact resolved Windows dependency lock for repeatable rebuilds.

## Model loading and core compatibility

- Centralized PyTorch checkpoint loading so application-owned state dictionaries
  use the safer modern loading path.
- Preserved compatibility with UVR VR, MDX, Demucs, and ensemble metadata and
  existing user model files.
- Removed legacy NumPy aliases and adapted modern library interfaces where old
  APIs were removed.
- Preserved CPU execution on machines without a compatible NVIDIA GPU.
- Left the trained separation models and algorithms unchanged: this release
  improves reliability, compatibility, acceleration, and distribution, but does
  not claim newly trained models or inherently different separation quality.

## Windows build and packaging

- Added `UVR-Windows.spec`, a checked-in PyInstaller definition that collects
  PyTorch, ONNX Runtime, Librosa, Demucs, GUI themes/assets, model metadata,
  FFmpeg, and Rubber Band into a windowed 64-bit application.
- Added `build_windows.ps1` to validate Python 3.12, create the virtual
  environment, install locked dependencies, stage native tools, build the
  portable application, and invoke the installer compiler.
- Added `UVR-Windows.iss`, an Inno Setup definition that turns the portable
  directory into the release installer, shortcuts, and uninstall registration.
- Added file discovery that works both from source and from the packaged
  `_internal` runtime directory.
- Excluded generated 5+ GB build and installer outputs from Git history; release
  assets are published separately.

## Verification completed

- Six core compatibility tests pass: safe checkpoint loading, modern Librosa
  resampling, STFT round trip, real VR neural inference, release-version
  reporting, and preservation of the original Windows installer upgrade ID.
- The bundled `UVR-DeNoise-Lite.pth` model completed actual inference with
  finite, shape-correct output.
- PyTorch CUDA inference was verified on an NVIDIA GeForce RTX 4090.
- ONNX Runtime executed a graph with `CUDAExecutionProvider` active and CPU
  fallback available.
- FFmpeg 9.0.1 and Rubber Band 3.3.0 executed from the packaged runtime.
- Application source passed Python bytecode compilation.
- The portable GUI remained healthy during a 20-second startup smoke test.
- The exact split installer artifacts completed an isolated installation; the
  installed GUI remained healthy during a second 20-second startup test; the
  registered uninstaller exited successfully and removed installed binaries.
- The replacement installer completed a real in-place upgrade of the registered
  v5.6.1 application. Windows reported v6.0.0 afterward, both legacy launch
  executables were removed, the Start Menu shortcut targeted the v6 executable,
  and the installed executable matched the tested build hash.

## Known limitations

- These files are not Authenticode-signed, so Windows SmartScreen may display an
  unknown-publisher warning.
- NVIDIA CUDA acceleration requires a compatible current NVIDIA driver.
- TensorRT remains optional and is not bundled; ONNX Runtime uses its CUDA
  provider directly.
- Only the small denoising model already tracked by the upstream repository is
  bundled. Other models continue to download through UVR's existing model
  manager.
- UVR creates a small settings file and temporary working directories at
  runtime. An uninstall may leave those user-created state items behind while
  removing the installed application binaries.

For the complete file-by-file technical record, build commands, dependency
decisions, and verification detail, read the expanded project README,
`WINDOWS_11_MODERNIZATION.md`, and `WINDOWS_BUILD.md` in the repository.
