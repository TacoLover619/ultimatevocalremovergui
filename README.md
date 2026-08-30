# Ultimate Vocal Remover GUI v6.0

[![Release](https://img.shields.io/github/release/TacoLover619/ultimatevocalremovergui.svg)](https://github.com/TacoLover619/ultimatevocalremovergui/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/TacoLover619/ultimatevocalremovergui/total.svg)](https://github.com/TacoLover619/ultimatevocalremovergui/releases)

## What's new in version 6.0

Version 6.0 updates the UVR runtime and Windows packaging. The interface,
trained separation models, and separation methods have not been replaced. The
VR, MDX-Net, MDX23C, and Demucs pipelines now run with current Windows 11,
Python, PyTorch, Librosa, ONNX, and CUDA versions.

### Tested runtime

The current Windows build was compiled and tested with:

| Component | Tested version |
| --- | --- |
| Operating system | Windows 11, 64-bit |
| Python | 3.12.13 |
| PyInstaller | 6.22.2 |
| PyTorch | 2.9.1+cu126 |
| Torchvision | 0.24.1+cu126 |
| CUDA runtime | 12.6 |
| ONNX | 1.22.0 |
| ONNX Runtime GPU | 1.29.0 |
| Librosa | 0.11.0 |
| NumPy | 2.5.2 |
| SciPy | 1.18.1 |
| SoundFile | 0.14.0 |
| FFmpeg | 9.0.1 essentials build |
| Rubber Band | 3.3.0 GPL executable |

The complete resolved dependency graph is checked in as
[`requirements-windows.lock.txt`](requirements-windows.lock.txt). The package
uses NVIDIA CUDA when it is available and retains CPU execution as a fallback.

### Model-loading changes

PyTorch 2.6 changed the default behavior of `torch.load` by making
`weights_only=True` the default. UVR's original implicit calls were written for
the older behavior and could fail when loading models on a current PyTorch
release.

The loading paths in `UVR.py`, `separate.py`, `lib_v5/mdxnet.py`, and
`demucs/states.py` now explicitly select the correct behavior for each model
format:

- State dictionaries, mixer weights, and compatible model metadata use
  `weights_only=True`.
- Legacy Demucs v1 packages use `weights_only=False` because those files
  serialize a Python model class in addition to tensor weights.
- The legacy loader is documented as a trusted-model-only boundary. Files used
  with that path should come from UVR's official model source.

This keeps older UVR model formats working while applying PyTorch's restricted,
safer checkpoint loader wherever the stored format supports it.

### Librosa and audio-processing compatibility

The original source pinned Librosa 0.9.2 and passed several arguments
positionally. Current Librosa versions make those arguments keyword-only. The
old calls could import successfully and then fail only when a user started an
actual conversion.

The affected code in `separate.py` and `lib_v5/spec_utils.py` now explicitly
uses:

- `orig_sr` and `target_sr` for resampling.
- `n_fft` for short-time Fourier transforms.
- `sr`, `mono`, `dtype`, and `res_type` for audio loading.

These corrections cover:

- Multiband VR input preparation.
- Inter-band sample-rate conversion.
- Pitch adjustment.
- Legacy VR spectrogram construction.
- Denoising and dereverberation helpers.
- Waveform-to-spectrogram conversion used during real model inference.

The last of these was found by running the bundled neural model end to end; it
would not have been detected by an import-only smoke test.

### Modern PyTorch STFT handling

`lib_v5/tfc_tdf_v3.py` previously requested the deprecated real/imaginary
layout from `torch.stft(return_complex=False)`.

The updated path now:

1. Calls `torch.stft` with `return_complex=True`.
2. Converts the native complex tensor with `torch.view_as_real`.
3. Rearranges it into the same channel layout expected by the existing trained
   MDX network.
4. Preserves the established inverse-STFT conversion and output layout.

The model therefore receives the same logical real/imaginary channel data
without depending on a deprecated PyTorch return format.

### Removed inference-only training framework

`lib_v5/mdxnet.py` inherited from
`pytorch_lightning.LightningModule`, even though UVR does not use a Lightning
trainer, callbacks, training loop, logger, or distributed training runtime.

`AbstractMDXNet` now inherits directly from `torch.nn.Module`. Model parameters,
state dictionaries, forward inference, and optimizer helper methods remain
available, while the Windows application no longer needs to load or package the
full PyTorch Lightning training framework.

### FFmpeg and Rubber Band reliability

UVR depends on FFmpeg for compressed audio decoding/encoding and Rubber Band
for time stretching and pitch shifting. Previously these executables could be
missed depending on the installation directory and the user's global `PATH`.

`separate.py` now configures the executable search path before importing Pydub:

- A packaged application uses the PyInstaller runtime directory exposed through
  `sys._MEIPASS`.
- A source checkout uses `third_party/bin`.

The PyInstaller package includes:

- `ffmpeg.exe`
- `rubberband.exe`
- `sndfile.dll`

This prevents Pydub's missing-FFmpeg startup warning and lets both Pydub and
Pyrubberband find the bundled tools without a separate machine-wide install.

### Dependency cleanup

The Windows dependency definition was rebuilt around the imports and execution
paths the application actually uses:

- PyTorch and Torchvision are a matched CUDA 12.6 pair.
- `onnxruntime-gpu` provides both CUDA and CPU execution providers; the
  conflicting simultaneous installation of `onnxruntime` and
  `onnxruntime-gpu` was removed.
- `pytorch_lightning` was removed after the MDX inference class was converted to
  `torch.nn.Module`.
- Previously undeclared or unreliable direct dependencies, including
  `pyrubberband`, `omegaconf`, and `tqdm`, are now declared.
- `opencv-python-headless` is used because UVR does not require OpenCV's separate
  GUI toolkit.
- Direct requirements live in `requirements-windows.in`.
- Exact tested versions live in `requirements-windows.lock.txt`.

### Reproducible Windows packaging

The branch adds [`UVR-Windows.spec`](UVR-Windows.spec), a checked-in PyInstaller
definition that:

- Builds `UVR.py` as a windowed 64-bit application.
- Applies the existing UVR icon.
- Includes GUI images, fonts, themes, sounds, saved-settings placeholders, and
  model metadata.
- Includes the bundled VR denoising model and MDX mixer checkpoint.
- Collects Librosa and ONNX Runtime data and required native libraries.
- Includes FFmpeg and Rubber Band in the packaged runtime.
- Excludes unrelated notebook, test, and distributed-training components where
  doing so is safe.
- Produces a directory distribution instead of a one-file executable.

The directory format is intentional. A one-file build would unpack several
gigabytes of Python, PyTorch, CUDA, ONNX, and audio libraries into a temporary
directory every time UVR starts.

[`build_windows.ps1`](build_windows.ps1) automates the complete build:

#### Windows build requirements

Use a 64-bit Windows 11 machine with the following software:

- Git for Windows.
- 64-bit Python 3.12.
- Inno Setup 6.5 or newer.
- PowerShell 7 or Windows PowerShell 5.1.
- Internet access for Python packages, FFmpeg, and Rubber Band.
- At least 15 GB of free disk space for downloads, the virtual environment,
  PyInstaller work files, the portable application, and installer files.

Python 3.12 and Inno Setup can be installed from an elevated PowerShell window:

```powershell
winget install --id Python.Python.3.12 --exact
winget install --id JRSoftware.InnoSetup --exact
```

Close and reopen PowerShell after installing Python so the updated `PATH` is
available.

#### Clone and build

Run these commands in PowerShell:

```powershell
git clone https://github.com/TacoLover619/ultimatevocalremovergui.git
Set-Location .\ultimatevocalremovergui
.\build_windows.ps1 -CleanEnvironment
```

If Python 3.12 is installed but is not the default `python` command, pass its
full path:

```powershell
.\build_windows.ps1 -CleanEnvironment `
    -PythonBootstrap 'C:\Users\YOUR-NAME\AppData\Local\Programs\Python\Python312\python.exe'
```

The `-CleanEnvironment` switch removes only the `.venv` directory inside this
repository and recreates it. Omit the switch to reuse an existing environment:

```powershell
.\build_windows.ps1
```

#### What the build script does

The script performs these steps in order:

1. Resolves the repository directory and `.venv` path.
2. Checks that any environment selected for removal is inside the repository.
3. Creates `.venv` with the selected Python 3.12 executable.
4. Updates `pip` inside the isolated environment.
5. Creates `third_party\downloads` and `third_party\bin`.
6. Downloads the FFmpeg essentials archive from gyan.dev when `ffmpeg.exe` is
   not already staged.
7. Extracts and copies `ffmpeg.exe` into `third_party\bin`.
8. Downloads the Rubber Band 3.3.0 Windows archive when `rubberband.exe` is not
   already staged.
9. Extracts and copies `rubberband.exe` and `sndfile.dll` into
   `third_party\bin`.
10. Installs the exact package versions from `requirements-windows.lock.txt`.
11. Runs PyInstaller with `UVR-Windows.spec` and a clean analysis cache.
12. Locates Inno Setup in the current user's program directory or either
    standard Program Files directory.
13. Runs Inno Setup with `UVR-Windows.iss` to create the release installer.

PyInstaller gathers the application source, GUI resources, bundled model data,
PyTorch, CUDA libraries, ONNX Runtime, Librosa, FFmpeg, Rubber Band, and their
required native libraries. It builds a directory-based application because a
single-file package would extract several gigabytes every time UVR starts.

#### Build outputs

The portable application is written to:

```text
dist\Ultimate Vocal Remover\Ultimate Vocal Remover.exe
```

The whole `Ultimate Vocal Remover` directory must remain together because the
executable depends on its `_internal` directory.

Inno Setup writes the release files to:

```text
installer\UVR_v6.0.0_setup.exe
installer\UVR_v6.0.0_setup-1.bin
installer\UVR_v6.0.0_setup-2.bin
```

The exact number of `.bin` files can change if the compressed application size
changes. `UVR-Windows.iss` limits each payload file to 1,900,000,000 bytes so it
stays below GitHub's 2 GiB release asset limit. The setup EXE and every numbered
`.bin` file must remain together in the same directory.

The installer targets 64-bit Windows 10 build 17763 or newer, including Windows
11. It installs per user under `%LOCALAPPDATA%\Programs\Ultimate Vocal Remover`,
adds a Start Menu shortcut, offers an optional Desktop shortcut, and registers
a Windows uninstaller. It retains the original UVR Windows installer identity,
so running v6.0 over an existing v5.6.1 installation performs an in-place
upgrade and updates the existing Installed Apps entry.

#### Verify the completed build

Run the source and inference tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q UVR.py separate.py demucs lib_v5 gui_data tests
```

Confirm the portable application starts:

```powershell
& '.\dist\Ultimate Vocal Remover\Ultimate Vocal Remover.exe'
```

Test the actual installer from an empty directory. Keep all installer parts in
that directory, run `UVR_v6.0.0_setup.exe`, start UVR from the Start Menu, and
confirm that it can be removed from Windows Installed Apps.

Generate release checksums with:

```powershell
Get-ChildItem .\installer\UVR_v6.0.0_setup* -File |
    Get-FileHash -Algorithm SHA256 |
    Format-Table Hash, Path
```

The executable and installer are not Authenticode-signed by this build process.
Sign the setup EXE and any other executable files before publishing if a code
signing certificate is available. Unsigned builds can trigger a Windows
SmartScreen warning.

[`WINDOWS_BUILD.md`](WINDOWS_BUILD.md) contains the same short command reference
for developers who already know the full process.

### Automated core tests

[`tests/test_core_compat.py`](tests/test_core_compat.py) contains six focused
tests:

1. Loads the bundled VR model and MDX mixer checkpoint using the modern safe
   PyTorch state-dictionary loader.
2. Runs the current Librosa resampling path used for pitch changes and validates
   finite stereo output.
3. Runs an STFT/inverse-STFT round trip and validates shape and finite samples.
4. Runs actual neural inference with `UVR-DeNoise-Lite.pth`, then validates that
   the result matches the input shape and contains only finite samples.
5. Verifies that the packaged application reports the v6.0.0 release version.
6. Verifies that the Windows installer retains the original UVR installer ID
   and removes the two legacy v5.6.1 launch executables during an upgrade.

These tests can be run with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Completed verification

The modernization was verified with more than a GUI import check:

- All six core compatibility tests pass.
- Python bytecode compilation passes for `UVR.py`, `separate.py`, `demucs/`,
  `lib_v5/`, `gui_data/`, and the tests.
- The bundled UVR denoising model completes real inference with finite,
  shape-correct output.
- PyTorch CUDA inference is active on a tested NVIDIA GeForce RTX 4090.
- ONNX Runtime successfully executes a graph through
  `CUDAExecutionProvider`, with `CPUExecutionProvider` retained as fallback.
- FFmpeg 9.0.1 executes from the packaged runtime.
- Rubber Band 3.3.0 executes from the packaged runtime.
- The packaged GUI remains healthy through a 20-second startup smoke test and
  is then stopped by the test harness.
- The split release installer completes a full isolated installation, launches
  the installed GUI successfully, and registers a working uninstaller.
- `git diff --check` passes.

The locally tested CUDA package is approximately 5.28 GB. Its executable hash
was:

```text
SHA-256: 0B801BD739152604ADF4E607A6B0300C8209688C4385F9D2EB7A1D8284AE27C8
```

The hash identifies that local build only. PyInstaller is not currently
configured for deterministic byte-for-byte output, so a rebuild can have a
different hash even when built from the same source.

### Git and release artifact policy

Generated and downloaded files are deliberately excluded from Git:

- `.venv/`
- `build/`
- `dist/`
- `installer/`
- `third_party/`
- Python bytecode caches
- UVR's generated `data.pkl` settings file

The 5.28 GB CUDA distribution does not belong in normal Git history. It should
be uploaded separately as a GitHub release asset or hosted externally after any
desired Authenticode signing step.

Third-party redistribution notes are recorded in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

### Known limitations

- Version 6.0 adds an Inno Setup installer around the portable directory. The
  portable build remains available as the installer input and debugging form.
- The locally generated executable is not Authenticode-signed.
- NVIDIA CUDA and ONNX CUDA execution were verified. TensorRT is optional and
  is not bundled.
- The repo includes the small VR denoising model already present upstream.
  Other UVR models continue to use the existing in-application download system.
- CUDA 12.6 requires a compatible NVIDIA driver. CPU fallback remains available
  on systems without a compatible NVIDIA GPU.
- The trained models and separation algorithms were preserved. These changes
  improve compatibility, loading reliability, packaging, and acceleration; they
  do not claim newly trained models or inherently different separation quality.
- The GUI and unrelated utilities were intentionally not redesigned.

### File-level summary

| File | Change |
| --- | --- |
| `README.md` | Detailed modernization, verification, packaging, and limitation record |
| `UVR.py` | Explicit safe loading for model metadata |
| `separate.py` | Modern model loading, Librosa calls, and bundled binary discovery |
| `lib_v5/spec_utils.py` | Modern Librosa resampling and STFT calls |
| `lib_v5/tfc_tdf_v3.py` | Native complex PyTorch STFT handling |
| `lib_v5/mdxnet.py` | Removed Lightning runtime and safely loaded mixer state |
| `demucs/states.py` | Explicit legacy Demucs package loading behavior |
| `gui_data/error_handling.py` | Python 3.12-safe error signature string |
| `requirements-windows.in` | Direct modern Windows/CUDA dependencies |
| `requirements-windows.lock.txt` | Exact tested dependency graph |
| `UVR-Windows.spec` | Reproducible PyInstaller package definition |
| `UVR-Windows.iss` | Inno Setup v6.0 installer definition |
| `build_windows.ps1` | Automated Windows build workflow |
| `tests/test_core_compat.py` | Core transform, model-loading, and inference tests |
| `.gitignore` | Excludes generated, downloaded, runtime, and package files |
| `THIRD_PARTY_NOTICES.md` | FFmpeg and Rubber Band redistribution notice |
| `WINDOWS_BUILD.md` | Concise rebuild instructions |
| `WINDOWS_11_MODERNIZATION.md` | Extended standalone technical record |

## About

This application uses state-of-the-art source separation models to remove vocals from audio files. UVR's core developers trained all of the models provided in this package (except for the Demucs v3 and v4 4-stem models).

- **Core Developers**
    - [Anjok07](https://github.com/anjok07)
    - [aufr33](https://github.com/aufr33)

- **Support the Project**
    - [Donate](https://www.buymeacoffee.com/uvr5)

## Installation

These bundles contain the UVR interface, Python, PyTorch, and other dependencies needed to run the application effectively. No prerequisites are required.

### Windows Installation

- Please Note:
    - This installer is intended for those running Windows 10 or higher. 
    - Application functionality for systems running Windows 7 or lower is not guaranteed.
    - Application functionality for Intel Pentium & Celeron CPUs systems is not guaranteed.
    - You must install UVR to the main C:\ drive. Installing UVR to a secondary drive will cause instability.

- Download all three v6.0 files below into the same folder, then run the setup
  EXE. The two `.bin` files are required installer data, not optional downloads:
    - [`UVR_v6.0.0_setup.exe`](https://github.com/TacoLover619/ultimatevocalremovergui/releases/download/v6.0.0/UVR_v6.0.0_setup.exe)
    - [`UVR_v6.0.0_setup-1.bin`](https://github.com/TacoLover619/ultimatevocalremovergui/releases/download/v6.0.0/UVR_v6.0.0_setup-1.bin)
    - [`UVR_v6.0.0_setup-2.bin`](https://github.com/TacoLover619/ultimatevocalremovergui/releases/download/v6.0.0/UVR_v6.0.0_setup-2.bin)
    - [`SHA256SUMS.txt`](https://github.com/TacoLover619/ultimatevocalremovergui/releases/download/v6.0.0/SHA256SUMS.txt)
- Before installing, confirm that the setup filename is
  `UVR_v6.0.0_setup.exe`. Its SHA-256 value is:

  ```text
  A6393BCE4524F5FBACAFE66777741E2EE2C1F9EF93D52F92D106552268884DEF
  ```

- The installer window must say `Setup - Ultimate Vocal Remover v6.0.0`. If it
  says version 5.6.1, cancel it because that is an older installer and is not
  part of this release.
- The old v5.6 DirectML installer and v5.6 patch links have been removed from
  this Windows section to prevent them from being mistaken for v6.0 downloads.
- To build from source, follow the complete
  [Windows build procedure](#reproducible-windows-packaging) on this page.

### MacOS Installation
- Please Note:
    - The MacOS Sonoma mouse clicking issue has been fixed.
    - MPS (GPU) acceleration for Mac M1 has been expanded to work with Demucs v4 and all MDX-Net models.
    - This bundle is intended for those running macOS Big Sur and above.
    - Application functionality for systems running macOS Catalina or lower is not guaranteed.
    - Application functionality for older or budget Mac systems is not guaranteed.
    - Once everything is installed, the application may take up to 5-10 minutes to start for the first time (depending on your Macbook).

- Download the UVR dmg for MacOS via one of the links below:
    - Mac M1 (arm64) users:
       - [Main Download Link](https://github.com/Anjok07/ultimatevocalremovergui/releases/download/v5.6/Ultimate_Vocal_Remover_v5_6_MacOS_arm64.dmg)
       - [Main Download Link mirror](https://www.mediafire.com/file_premium/u3rk54wsqadpy93/Ultimate_Vocal_Remover_v5_6_MacOS_arm64.dmg/file)

    - Mac Intel (x86_64) users:
       - [Main Download Link](https://github.com/Anjok07/ultimatevocalremovergui/releases/download/v5.6/Ultimate_Vocal_Remover_v5_6_MacOS_x86_64.dmg)
       - [Main Download Link mirror](https://www.mediafire.com/file_premium/2gf1werx5ly5ylz/Ultimate_Vocal_Remover_v5_6_MacOS_x86_64.dmg/file)

<details id="CannotOpen">
  <summary>MacOS Users: Having Trouble Opening UVR?</summary>

> Due to Apples strict application security, you may need to follow these steps to open UVR.
>
> First, run the following command via Terminal.app to allow applications to run from all sources (it's recommended that you re-enable this once UVR opens properly.)
> 
> ```bash
> sudo spctl --master-disable
> ```
> 
> Second, run the following command to bypass Notarization: 
> 
> ```bash
> sudo xattr -rd com.apple.quarantine /Applications/Ultimate\ Vocal\ Remover.app
> ```

</details>

<details id="MacInstall">
  <summary>Manual MacOS Installation</summary>

### Manual MacOS Installation

- Download and save this repository [here](https://github.com/Anjok07/ultimatevocalremovergui/archive/refs/heads/master.zip)
- Download and install Python 3.10 [here](https://www.python.org/ftp/python/3.10.9/python-3.10.9-macos11.pkg)
- From the saved directory run the following - 

```
pip3 install -r requirements.txt
```

- If your Mac is running with an M1, please run the following command next. If not, skip this step. - 

```
cp /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/_soundfile_data/libsndfile_arm64.dylib /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/_soundfile_data/libsndfile.dylib
```

**FFmpeg Installation**

- Once everything is done installing, download the correct FFmpeg binary for your system [here](http://www.osxexperts.net) and place it into the main application directory.

**Rubber Band Installation**

In order to use the Time Stretch or Change Pitch tool, you'll need Rubber Band.

- Download the precompiled build [here](https://breakfastquay.com/files/releases/rubberband-3.1.2-gpl-executable-windows.zip)
- From the archive, extract the following files to the UVR/lib_v5 application directory:
   - ```rubberband-3.1.2-gpl-executable-macos/rubberband```

This process has been tested on a MacBook Pro 2021 (using M1) and a MacBook Air 2017 and is confirmed to be working on both.

</details>


### Linux Installation (Updated Instructions)

<details id="LinuxInstall">
  <summary>See Linux Installation Instructions</summary>

<br />

**These installation instructions are for Debian & Arch-based Linux systems.**

---

#### **Step 1: Download the Repository**
- Download and save this repository from [GitHub](https://github.com/Anjok07/ultimatevocalremovergui/archive/refs/heads/master.zip).
- Extract the downloaded file to a directory of your choice.

---

#### **Step 2: Install Dependencies**
Use the following commands based on your system type:

**For Debian-based systems (Ubuntu, Mint, etc.):**
```bash
sudo apt update && sudo apt upgrade
sudo apt-get install -y ffmpeg python3-pip python3-tk
```

**For Arch-based systems (EndeavourOS):**
```bash
sudo pacman -Syu
sudo pacman -S ffmpeg python-pip tk
```

---

#### **Step 3: Set Up a Virtual Environment (Recommended)**
Setting up a virtual environment (venv) ensures that the program's dependencies do not interfere with system-wide Python packages.

1. **Navigate to the extracted repository directory:**
   ```bash
   cd /path/to/ultimatevocalremovergui
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   - For **Debian-based and Arch-based systems:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies in the virtual environment:**
   ```bash
   pip install -r requirements.txt
   ```

---

#### **Step 4: Run the Application**
While the virtual environment is activated, start the application:
```bash
python UVR.py
```

---

#### **Important Notes**
1. **Avoid Modifying System Files:**  
   Previous instructions suggested deleting the `/usr/lib/python3.11/EXTERNALLY-MANAGED` file, which is dangerous and can break Python package management. Do **NOT** delete this file.

2. **Why Use Virtual Environments?**  
   Virtual environments isolate the program's dependencies, preventing conflicts with system Python packages. More information is available [here](https://stackoverflow.com/questions/75602063/pip-install-r-requirements-txt-is-failing-this-environment-is-externally-mana/75696359#75696359).

3. **Known Issues and Discussions:**  
   - [Issue #1578](https://github.com/Anjok07/ultimatevocalremovergui/issues/1578)  
   - [Pull Request #1068](https://github.com/Anjok07/ultimatevocalremovergui/pull/1068)

---

If you encounter issues, refer to the [GitHub Issues](https://github.com/Anjok07/ultimatevocalremovergui/issues) page for help. 

</details>

### Other Application Notes
- Nvidia GTX 1060 6GB is the minimum requirement for GPU conversions.
- Nvidia GPUs with at least 8GBs of V-RAM are recommended.
- AMD Radeon GPU supported is limited at this time.
   - There is currently a working branch for AMD GPU users [here](https://github.com/Anjok07/ultimatevocalremovergui/tree/v5.6-amd-gpu)
- This application is only compatible with 64-bit platforms. 
- This application relies on the Rubber Band library for the Time-Stretch and Pitch-Shift options.
- This application relies on FFmpeg to process non-wav audio files.
- The application will automatically remember your settings when closed.
- Conversion times will significantly depend on your hardware. 
- These models are computationally intensive. 

### Performance:
- Model load times are faster.
- Importing/exporting audio files is faster.

## Troubleshooting

### Common Issues

- If FFmpeg is not installed, the application will throw an error if the user attempts to convert a non-WAV file.
- Memory allocation errors can usually be resolved by lowering the "Segment" or "Window" sizes.

#### MacOS Sonoma Left-click Bug
There's a known issue on MacOS Sonoma where left-clicks aren't registering correctly within the app. This was impacting all applications built with Tkinter on Sonoma and has since been resolved. Please download the latest version via the following link if you are still experiencing issues - [link](https://github.com/Anjok07/ultimatevocalremovergui/releases/tag/v5.6)

This issue was being tracked [here](https://github.com/Anjok07/ultimatevocalremovergui/issues/840).

### Issue Reporting

Please be as detailed as possible when posting a new issue. 

If possible, click the "Settings Button" to the left of the "Start Processing" button and click the "Error Log" button for detailed error information that can be provided to us.

## License

The **Ultimate Vocal Remover GUI** code is [MIT-licensed](LICENSE). 

- **Please Note:** For all third-party application developers who wish to use our models, please honor the MIT license by providing credit to UVR and its developers.

## Credits
- [ZFTurbo](https://github.com/ZFTurbo) - Created & trained the weights for the new MDX23C models. 
- [DilanBoskan](https://github.com/DilanBoskan) - Your contributions at the start of this project were essential to the success of UVR. Thank you!
- [Bas Curtiz](https://www.youtube.com/user/bascurtiz) - Designed the official UVR logo, icon, banner, and splash screen.
- [tsurumeso](https://github.com/tsurumeso) - Developed the original VR Architecture code. 
- [Kuielab & Woosung Choi](https://github.com/kuielab) - Developed the original MDX-Net AI code. 
- [Adefossez & Demucs](https://github.com/facebookresearch/demucs) - Developed the original Demucs AI code. 
- [KimberleyJSN](https://github.com/KimberleyJensen) - Advised and aided the implementation of the training scripts for MDX-Net and Demucs. Thank you!
- [Hv](https://github.com/NaJeongMo/Colab-for-MDX_B) - Helped implement chunks into the MDX-Net AI code. Thank you!

## Contributing

- For anyone interested in the ongoing development of **Ultimate Vocal Remover GUI**, please send us a pull request, and we will review it. 
- This project is 100% open-source and free for anyone to use and modify as they wish. 
- We only maintain the development and support for the **Ultimate Vocal Remover GUI** and the models provided. 

## References
- [1] Takahashi et al., "Multi-scale Multi-band DenseNets for Audio Source Separation", https://arxiv.org/pdf/1706.09588.pdf
