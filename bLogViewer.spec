# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


import os
import sys
import sysconfig
import glob

# Ensure Streamlit's package metadata (.dist-info) is bundled so that
# importlib.metadata.version("streamlit") works inside the frozen app.
site_pkgs = sysconfig.get_paths().get("purelib", "")
streamlit_metadata: list[tuple[str, str]] = []
if site_pkgs:
	for path in glob.glob(os.path.join(site_pkgs, "streamlit-*.dist-info")):
		streamlit_metadata.append((path, os.path.basename(path)))

# Extra binary dependencies (e.g. Conda's libffi for _ctypes)
extra_binaries: list[tuple[str, str]] = []

# If running under Conda, bundle libffi DLLs that _ctypes may depend on
conda_prefix = os.environ.get("CONDA_PREFIX") or ""
if conda_prefix:
	for pattern in [
		os.path.join(conda_prefix, "Library", "bin", "libffi-*.dll"),
		os.path.join(conda_prefix, "Library", "bin", "ffi-*.dll"),
	]:
		for dll_path in glob.glob(pattern):
			# Place DLL next to the executable inside the bundle
			extra_binaries.append((dll_path, "."))

# Also try common locations for python.org installs (DLLs/ffi-*.dll)
base_prefix = getattr(sys, "base_prefix", "") or getattr(sys, "prefix", "")
if base_prefix:
	# Check DLLs directory
	for pattern in [
		os.path.join(base_prefix, "DLLs", "ffi-*.dll"),
		os.path.join(base_prefix, "DLLs", "libffi-*.dll"),
	]:
		for dll_path in glob.glob(pattern):
			extra_binaries.append((dll_path, "."))
	
	# Check Library/bin directory (common in conda environments)
	lib_bin = os.path.join(base_prefix, "Library", "bin")
	if os.path.exists(lib_bin):
		for pattern in [
			os.path.join(lib_bin, "ffi-*.dll"),
			os.path.join(lib_bin, "libffi-*.dll"),
			os.path.join(lib_bin, "ffi.dll"),  # Also check for exact ffi.dll
			os.path.join(lib_bin, "libcrypto-*.dll"),  # For _ssl.pyd
			os.path.join(lib_bin, "libssl-*.dll"),     # For _ssl.pyd
			os.path.join(lib_bin, "crypto*.dll"),      # Alternative pattern
			os.path.join(lib_bin, "ssl*.dll"),         # Alternative pattern
		]:
			for dll_path in glob.glob(pattern):
				extra_binaries.append((dll_path, "."))

	# Explicitly include the _ctypes extension module if present
	ctypes_pyd = os.path.join(base_prefix, "DLLs", "_ctypes.pyd")
	if os.path.exists(ctypes_pyd):
		extra_binaries.append((ctypes_pyd, "."))

a = Analysis(
	['run_blogviewer.py'],
	pathex=['.'],
	binaries=extra_binaries,
	datas=[
		# Bundle the main app.py file
		('app.py', '.'),
		# Bundle sample/raw log data folder next to the executable
		#('logs_raw_data', 'logs_raw_data'),
		# Bundle Streamlit metadata so importlib.metadata can find it
		*streamlit_metadata,
		# Bundle Streamlit static files
		('venv/Lib/site-packages/streamlit/static', 'streamlit/static'),
	],
	hiddenimports=[
		'streamlit.runtime.scriptrunner.magic_funcs',
		'streamlit.runtime.scriptrunner',
		'streamlit.runtime',
		'streamlit.web',
		'streamlit.elements',
		'streamlit.commands',
		'streamlit.components',
		'streamlit.connections',
		'streamlit.navigation',
		'streamlit.proto',
		'streamlit.runtime.scriptrunner.script_runner',
		'streamlit.runtime.scriptrunner.exec_code',
		'ansi2html',
		'regex',
		'openpyxl',
		'xlsxwriter',
		'pandas',
	],
	hookspath=[],
	hooksconfig={},
	runtime_hooks=[],
	excludes=[],
	noarchive=False,
)

pyz = PYZ(
	a.pure,
	a.zipped_data,
	cipher=block_cipher,
)

exe = EXE(
	pyz,
	a.scripts,
	a.binaries,
	a.zipfiles,
	a.datas,
	[],
	name='LogViewer',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	console=True,  # show console window; set False if you prefer none
	disable_windowed_traceback=False,
	argv_emulation=False,
	target_arch=None,
	codesign_identity=None,
	entitlements_file=None,
	colllect=False,  # This creates a single-file executable
)

