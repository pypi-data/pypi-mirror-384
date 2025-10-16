from setuptools import (
    Extension,
    setup,
)
from Cython.Build import cythonize


extensions = [
    Extension(
        "dbhose_utils.common",
        ["src/dbhose_utils/common.pyx"],
    ),
]


setup(
    name="dbhose_utils",
    package_dir={"": "src"},
    ext_modules=cythonize(extensions, language_level="3"),
    packages=[
        "dbhose_utils.common",
    ],
    package_data={
        "dbhose_utils.common": [
            "**/*.pyx",
            "**/*.pyi",
            "**/*.pxd",
            "*.pxd",
            "*.pyd",
            "*.md",
            "*.txt",
        ]
    },
    exclude_package_data={
        "": ["*.c"],
        "dbhose_utils.common": ["**/*.c"],
    },
    include_package_data=True,
    setup_requires=["Cython>=3.0"],
    zip_safe=False,
)
