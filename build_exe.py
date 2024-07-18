import PyInstaller.__main__
import shutil
import os

# Clean previous builds
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)

# Get the path to the streamlit binary
streamlit_path = shutil.which("streamlit")

# Package the application
PyInstaller.__main__.run([
    'app.py',
    '--onefile',
    '--add-data', f'{streamlit_path}:streamlit',
    '--name', 'hospitalStreamlit',
    '--hidden-import', 'streamlit',
    '--hidden-import', 'altair',
    '--hidden-import', 'pandas',
    '--hidden-import', 'importlib_resources',
    '--collect-submodules', 'importlib_resources',
    '--exclude-module', 'setuptools',
    '--exclude-module', 'distutils',
])

print("EXE file created successfully!")