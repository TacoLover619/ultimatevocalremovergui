# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


datas = [
    ('gui_data', 'gui_data'),
    ('models', 'models'),
    ('lib_v5/mixer.ckpt', 'lib_v5'),
    ('THIRD_PARTY_NOTICES.md', '.'),
]
datas += collect_data_files('librosa')
datas += collect_data_files('onnxruntime')

binaries = collect_dynamic_libs('onnxruntime')
binaries += [
    ('third_party/bin/ffmpeg.exe', '.'),
    ('third_party/bin/rubberband.exe', '.'),
    ('third_party/bin/sndfile.dll', '.'),
]

hiddenimports = collect_submodules('onnx2pytorch')

a = Analysis(
    ['UVR.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'IPython',
        'jupyter',
        'matplotlib.tests',
        'numpy.tests',
        'pytest',
        'torch._dynamo',
        'torch._inductor',
        'torch.distributed.elastic',
        'torch.testing',
        'torch.utils.benchmark',
        'torch.utils.tensorboard',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Ultimate Vocal Remover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='gui_data/img/GUI-Icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Ultimate Vocal Remover',
)
