from setuptools import setup, find_packages

setup(
    name="m3d",
    version="1.0.1",
    description="Python3 3D transformation library with object oriented API and MIT licensed",
    author="Olivier Roulet-Dubonnet",
    author_email="olivier.roulet@gmail.com",
    url="https://gitlab.com/kurant-open/m3d",
    package_data={
        "": ["py.typed"],
    },
    packages=find_packages(),
    provides=["m3d"],
    license="MIT",
    install_requires=[
        "numpy",
    ],
    extras_require={
        "orientation-mean": ["scipy"],
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
