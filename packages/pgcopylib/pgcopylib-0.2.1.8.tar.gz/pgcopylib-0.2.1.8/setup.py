from setuptools import (
    Extension,
    setup,
)
from Cython.Build import cythonize

extensions = [
    Extension(
        "pgcopylib.common.base",
        ["src/pgcopylib/common/base.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.arrays",
        ["src/pgcopylib/common/dtypes/functions/arrays.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.dates",
        ["src/pgcopylib/common/dtypes/functions/dates.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.digits",
        ["src/pgcopylib/common/dtypes/functions/digits.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.geometrics",
        ["src/pgcopylib/common/dtypes/functions/geometrics.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.ipaddrs",
        ["src/pgcopylib/common/dtypes/functions/ipaddrs.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.jsons",
        ["src/pgcopylib/common/dtypes/functions/jsons.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.strings",
        ["src/pgcopylib/common/dtypes/functions/strings.pyx"],
    ),
    Extension(
        "pgcopylib.common.dtypes.functions.uuids",
        ["src/pgcopylib/common/dtypes/functions/uuids.pyx"],
    ),
]

setup(
    name="pgcopylib",
    package_dir={"": "src"},
    ext_modules=cythonize(extensions, language_level="3"),
    packages=[
        "pgcopylib.common",
        "pgcopylib.common.dtypes.functions",
    ],
    package_data={
        "pgcopylib": [
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
        "pgcopylib": ["**/*.c"],
    },
    include_package_data=True,
    setup_requires=["Cython>=3.0"],
    zip_safe=False,
)
