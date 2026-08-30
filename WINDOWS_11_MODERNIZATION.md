# Version 6.0 Windows 11 modernization: complete change record

## Scope

Version 6.0 modernizes the existing UVR application without redesigning
the interface or changing its source-separation workflow. Work is deliberately
limited to the core audio and model execution paths, dependency compatibility,
runtime reliability, tests, and reproducible Windows packaging.

The goal is to preserve compatibility with UVR's existing VR, MDX-Net,
MDX23C, and Demucs model families while making the application buildable and
usable on a current 64-bit Windows 11 environment.

## Runtime baseline

The tested Windows build uses:

- Windows 11, 64-bit
- Python 3.12.13
- PyInstaller 6.22.2
- PyTorch 2.9.1 with CUDA 12.6
- Torchvision 0.24.1 with CUDA 12.6
- ONNX Runtime GPU 1.29.0
- ONNX 1.22.0
- Librosa 0.11.0
- NumPy 2.5.2
- SciPy 1.18.1
- SoundFile 0.14.0
- FFmpeg 9.0.1 essentials build
- Rubber Band 3.3.0 GPL executable

The complete resolved Python dependency graph is stored in
`requirements-windows.lock.txt`. CUDA execution falls back to CPU when a
compatible NVIDIA device or driver is unavailable.

## Source changes

### Modern PyTorch checkpoint loading

PyTorch 2.6 changed the default value of `torch.load(weights_only=...)` to
`True`. The original code relied on the older implicit behavior, which could
prevent existing UVR models from loading on modern PyTorch releases.

The model-loading calls in `UVR.py`, `separate.py`, `lib_v5/mdxnet.py`, and
`demucs/states.py` now state their intent explicitly:

- Plain state dictionaries and model metadata use `weights_only=True`.
- The legacy Demucs v1 package path uses `weights_only=False` because that file
  format serializes a Python model class as part of the checkpoint.
- Comments identify the legacy paths that must only load models obtained from
  UVR's trusted model repository.

This restores compatibility while using the safer restricted loader wherever
the stored model format allows it.

### Current Librosa API compatibility

Modern Librosa releases make several parameters keyword-only. The original
code passed sample rates, FFT sizes, and mono flags positionally, causing
runtime `TypeError` exceptions once audio reached those paths.

Calls in `separate.py` and `lib_v5/spec_utils.py` now use explicit keywords:

- `orig_sr` and `target_sr` for resampling
- `n_fft` for short-time Fourier transforms
- `sr`, `mono`, `dtype`, and `res_type` for audio loading

These updates cover multiband VR preparation, waveform resampling, pitch
adjustment, spectrogram construction, denoising, and legacy VR helper paths.

An actual inference test exposed an additional positional `librosa.stft` call
that an import-only test would not catch; that execution path is now fixed and
covered by the test suite.

### Complex STFT modernization

`lib_v5/tfc_tdf_v3.py` previously requested the deprecated real/imaginary
tensor layout from `torch.stft(return_complex=False)`.

The STFT implementation now:

1. Requests a native complex tensor with `return_complex=True`.
2. Converts it to the channel layout expected by the existing MDX network with
   `torch.view_as_real`.
3. Preserves the established inverse conversion and output layout.

This removes reliance on a deprecated PyTorch representation without changing
the tensors presented to the trained model.

### Removed inference-time PyTorch Lightning dependency

`lib_v5/mdxnet.py` inherited from `pytorch_lightning.LightningModule`, although
the application only uses that class for inference and does not use a Lightning
trainer, callbacks, logging, or distributed training.

`AbstractMDXNet` now inherits directly from `torch.nn.Module`. This retains all
state-dictionary and inference behavior required by UVR while removing a large
training framework and its transitive dependencies from application startup
and packaging.

### Reliable external audio-tool discovery

The application requires FFmpeg for compressed audio formats and Rubber Band
for pitch/time processing. Previously these commands depended on installation
location and the caller's global `PATH`.

At startup, `separate.py` now adds the correct binary directory to `PATH`:

- In a PyInstaller build, binaries are located from `sys._MEIPASS`.
- In a source checkout, binaries are located under `third_party/bin`.

This happens before Pydub is imported, preventing its missing-FFmpeg warning
and allowing both Pydub and Pyrubberband to discover the bundled executables.

### Minor Python 3.12 warning correction

The audioread error signature in `gui_data/error_handling.py` is now a raw
string. This removes an invalid escape-sequence warning without altering error
matching behavior.

## Dependency changes

`requirements-windows.in` replaces the 2022-era Windows dependency assumptions
with direct dependencies compatible with the modern runtime. Important changes
include:

- A matched PyTorch/Torchvision CUDA 12.6 pair.
- Modern Librosa, NumPy, SciPy, SoundFile, ONNX, and ONNX Runtime GPU.
- Removal of `pytorch_lightning` from the runtime.
- Removal of the simultaneous `onnxruntime` and `onnxruntime-gpu` installation;
  the GPU package already supplies the CPU fallback provider.
- Addition of dependencies that the source imports but the old requirements
  did not reliably declare, including `pyrubberband`, `omegaconf`, and `tqdm`.
- Use of `opencv-python-headless` because UVR does not require OpenCV's separate
  GUI toolkit.
- An exact resolved lock file for repeatable Windows builds.

## Windows packaging

Version 6.0 adds both the portable PyInstaller application and an original-style
Inno Setup Windows installer. The installer provides Start Menu and optional
Desktop shortcuts, a standard Windows uninstall entry, per-user installation in
a writable application directory, and versioned executable metadata.

The CUDA distribution is larger than GitHub's 2 GiB per-asset limit, so Inno
Setup disk spanning produces a small `UVR_v6.0.0_setup.exe` launcher plus
numbered `.bin` payload files. All parts must be downloaded into the same folder
before running setup.

### PyInstaller specification

`UVR-Windows.spec` is a checked-in, reproducible PyInstaller definition. It:

- Builds `UVR.py` as a windowed 64-bit application.
- Applies the existing UVR icon.
- Includes GUI themes, images, fonts, sounds, model metadata, the bundled VR
  denoising model, and the MDX mixer checkpoint.
- Collects required Librosa and ONNX Runtime data.
- Includes required ONNX and PyTorch native libraries.
- Bundles FFmpeg, Rubber Band, and `sndfile.dll`.
- Excludes unrelated test, notebook, and distributed-training modules where
  safe.
- Uses PyInstaller's directory distribution rather than `--onefile` so the
  multi-gigabyte ML runtime is not unpacked on every application launch.

### Automated PowerShell build

`build_windows.ps1` performs the complete build workflow:

1. Creates or refreshes a project-local Python virtual environment.
2. Installs the locked dependencies.
3. Downloads the required FFmpeg and Rubber Band distributions.
4. Extracts the required executables into a stable local build path.
5. Runs PyInstaller using `UVR-Windows.spec`.

The script accepts `-CleanEnvironment` and an optional `-PythonBootstrap` path.
Detailed usage is documented in `WINDOWS_BUILD.md`.

### Generated artifacts intentionally excluded from Git

`.gitignore` excludes:

- `.venv/`
- `build/`
- `dist/`
- downloaded third-party archives and executables
- Python bytecode caches
- the runtime-generated `data.pkl` settings file

The compiled CUDA distribution is approximately 5.28 GB, so it is not suitable
for normal Git history. It should be distributed through a release asset or
other large-file hosting after any desired code-signing step.

## Tests and verification

`tests/test_core_compat.py` adds four focused tests:

1. Load the bundled VR and mixer state dictionaries using the safe modern
   PyTorch loader.
2. Exercise the modern Librosa resampling path used for pitch changes.
3. Perform an STFT/inverse-STFT round trip and verify finite output.
4. Run actual inference through the bundled `UVR-DeNoise-Lite.pth` neural model
   and verify output shape and finite samples.

The completed build was verified with:

- Python bytecode compilation across the application source.
- All five core compatibility tests passing, including the release-version
  assertion.
- VR denoising inference on an NVIDIA GeForce RTX 4090 through CUDA.
- ONNX Runtime session execution with `CUDAExecutionProvider` active and CPU
  fallback also available.
- FFmpeg and Rubber Band version execution from the packaged directory.
- A packaged GUI startup smoke test that remained healthy for 20 seconds and
  was then terminated by the test harness.
- A complete installation from the split Inno Setup release artifacts, a
  20-second startup test of the installed executable, and successful uninstall.

The tested executable SHA-256 was:

```text
0B801BD739152604ADF4E607A6B0300C8209688C4385F9D2EB7A1D8284AE27C8
```

That hash identifies the locally tested artifact only. Rebuilding changes the
hash because PyInstaller output is not currently configured as a deterministic
byte-for-byte build.

## Known limitations and intentional non-goals

- The release installer is split into one setup EXE and numbered `.bin` files
  to stay below GitHub's 2 GiB per-file limit; all parts are required.
- The executable is not Authenticode-signed.
- NVIDIA CUDA and ONNX CUDA execution are verified. TensorRT is not bundled and
  remains optional; ONNX Runtime uses its CUDA provider directly.
- The repository includes one small VR denoising model. Other UVR separation
  models continue to be downloaded through the application's existing model
  download workflow.
- No claim is made that model quality changes. The work improves runtime
  compatibility, loading reliability, acceleration, and packaging while
  preserving the trained models and separation algorithms.
- The interface and unrelated utilities were intentionally not redesigned.

## Files added

- `.gitignore`
- `THIRD_PARTY_NOTICES.md`
- `UVR-Windows.spec`
- `WINDOWS_BUILD.md`
- `WINDOWS_11_MODERNIZATION.md`
- `build_windows.ps1`
- `requirements-windows.in`
- `requirements-windows.lock.txt`
- `tests/test_core_compat.py`

## Files updated

- `README.md`
- `UVR.py`
- `demucs/states.py`
- `gui_data/error_handling.py`
- `lib_v5/mdxnet.py`
- `lib_v5/spec_utils.py`
- `lib_v5/tfc_tdf_v3.py`
- `separate.py`
