from setuptools import setup, find_packages, Extension
import pybind11

ext_modules = [
    Extension(
        "scheduler_cpp",
        [
            "backend/cpp/scheduler/pybind_module.cpp",
            "backend/cpp/scheduler/scheduler.cpp",
        ],
        include_dirs=[
            pybind11.get_include(),
            "backend/cpp/scheduler",
        ],
        language="c++",
        extra_compile_args=["-std=c++17"],
    )
]

setup(
    name="os-scheduler-atlas",
    version="0.2.0",
    author="Will Swinson",
    description="OS Scheduling Algorithms with ML Prediction",
    packages=find_packages(),
    ext_modules=ext_modules,
    python_requires=">=3.8",
    install_requires=["pybind11>=2.6.0"],
)
