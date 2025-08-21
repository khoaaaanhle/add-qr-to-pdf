# qrpdf.spec
# PyInstaller spec để build app từ app/main.py

block_cipher = None

a = Analysis(
    ['a.py'],      # file entry chính
    pathex=[],
    binaries=[],
    datas=[
        ('themes/*.qss', 'themes'),   # copy thư mục themes
        ('icon.ico', '.'),            # copy icon
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='qrpdf',          # tên app
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # False = app GUI
    icon='icon.ico'        # thêm icon cho file exe
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='qrpdf'
)
