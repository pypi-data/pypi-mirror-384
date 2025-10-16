import os
import sys
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess, sys

class CustomInstall(install):
    def run(self):
        # 1. Run normal installation
        install.run(self)
        # 2. Then run post-install script directly
        script_path = os.path.join(os.path.dirname(__file__), "src", "napari_tomodl", "post_install.py")
        if os.path.exists(script_path):
            print("Running post-install: installing correct torch version...")
            subprocess.run([sys.executable, script_path], check=True)
        else:
            print(f"⚠️  post_install.py not found at {script_path}")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="napari-tomodl",
    version="0.2.14",
    description="A plugin for optical projection tomography reconstruction with model-based neural networks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Marcos Antonio Obando, Minh Nhat Trinh, David Palecek, Germán Mato, Teresa Correia",
    author_email="marcos.obando@ib.edu.ar",
    license="MIT",
    license_files=["LICENSE"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: napari",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.10",
    install_requires=[
        "magicgui",
        "qtpy",
        "napari",
        "pyqt5",
        "opencv-python",
        "scikit-image",
        "scipy",
    ],
    extras_require={
        "testing": [
            "tox",
            "pytest",
            "pytest-cov",
            "pytest-qt",
            "napari",
            "pyqt5",
        ]
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    entry_points={
        "napari.manifest": [
            "napari-tomodl = napari_tomodl:napari.yaml",
        ]
    },
    package_data={"": ["*.yaml"], "napari_tomodl.processors": ["*.ckpt"]},
    cmdclass={"install": CustomInstall},
)
