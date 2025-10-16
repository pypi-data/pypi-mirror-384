from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="napari-tomodl",
    version="0.2.9",
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.10",
    install_requires=[
        "qtpy",
        "napari",
        "pyqt5",
        "opencv-python",
        "scikit-image",
        "scipy",
        "torch",
        "QBI-radon",
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
)
