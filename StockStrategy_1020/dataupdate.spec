# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['d:\\trae_projects\\Stock_strategies\\StockStrategy_1020\\update_data.py'],
    pathex=['d:\\trae_projects\\Stock_strategies\\StockStrategy_1020'],
    binaries=[],
    datas=[
        ('A股上市公司名单\\A股上市公司名单.csv', 'A股上市公司名单'),
    ],
    hiddenimports=[
        'config',
        'config.settings',
        'config.tushare_token',
        'services',
        'services.data_service',
        'services.data_updater',
        'services.progress_ui',
        'utils',
        'utils.logger',
        'utils.path_helper',
        'models',
        'models.stock',
        'tushare',
        'pandas',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dataupdate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
