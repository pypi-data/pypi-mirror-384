import shutil
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

def sync_hcom():
    """Sync hcom.py to src/hcom/__main__.py"""
    root = Path(__file__).parent
    src_file = root / 'hcom.py'
    dst_file = root / 'src' / 'hcom' / '__main__.py'

    if src_file.exists():
        print(f"Syncing {src_file} → {dst_file}")
        shutil.copy2(src_file, dst_file)
    else:
        print(f"Warning: {src_file} not found, skipping sync")

class BuildWithSync(build_py):
    """Custom build that syncs hcom.py to src/hcom/__main__.py before building"""
    def run(self):
        sync_hcom()
        super().run()

class SdistWithSync(sdist):
    """Custom sdist that syncs hcom.py before creating source distribution"""
    def run(self):
        sync_hcom()
        super().run()

setup(
    cmdclass={
        'build_py': BuildWithSync,
        'sdist': SdistWithSync,
    }
)
