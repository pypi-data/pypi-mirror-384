import sys
from setuptools import setup, Extension, find_packages

extra_compile_args = ["-O3"]
if sys.platform.startswith("linux") or sys.platform == "darwin":
    extra_compile_args.append("-fPIC")
    extra_compile_args.append("-std=c++11")

voronotalt_module = Extension(
    name="voronotalt._voronotalt_python",
    sources=["voronotalt_python_wrap.cxx"],
    include_dirs=["cpp"],
    extra_compile_args=extra_compile_args,
    language="c++",
)

setup(
    name="voronotalt",
    version="0.9.5.post6",
    description="Voronota-LT Python bindings via SWIG",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Kliment Olechnovic",
    author_email="kliment.olechnovic@gmail.com",
    url="https://github.com/kliment-olechnovic/voronotalt_python",
    ext_modules=[voronotalt_module],
    packages=find_packages(include=["voronotalt", "voronotalt.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: C++",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    zip_safe=False,
)
