from setuptools import (
    Extension,
    setup,
)
from Cython.Build import cythonize


extensions = [
    Extension(
        "nativelib.common.cast_dataframes",
        ["src/nativelib/common/cast_dataframes.pyx"],
    ),
    Extension(
        "nativelib.common.length",
        ["src/nativelib/common/length.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.booleans",
        ["src/nativelib/common/dtypes/functions/booleans.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.dates",
        ["src/nativelib/common/dtypes/functions/dates.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.decimals",
        ["src/nativelib/common/dtypes/functions/decimals.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.enums",
        ["src/nativelib/common/dtypes/functions/enums.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.floats",
        ["src/nativelib/common/dtypes/functions/floats.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.integers",
        ["src/nativelib/common/dtypes/functions/integers.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.ipaddrs",
        ["src/nativelib/common/dtypes/functions/ipaddrs.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.strings",
        ["src/nativelib/common/dtypes/functions/strings.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.functions.uuids",
        ["src/nativelib/common/dtypes/functions/uuids.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.objects.dtype",
        ["src/nativelib/common/dtypes/objects/dtype.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.objects.array",
        ["src/nativelib/common/dtypes/objects/array.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.objects.lowcardinality",
        ["src/nativelib/common/dtypes/objects/lowcardinality.pyx"],
    ),
    Extension(
        "nativelib.common.dtypes.parse",
        ["src/nativelib/common/dtypes/parse.pyx"],
    ),
    Extension(
        "nativelib.common.columns.info",
        ["src/nativelib/common/columns/info.pyx"],
    ),
    Extension(
        "nativelib.common.columns.column",
        ["src/nativelib/common/columns/column.pyx"],
    ),
    Extension(
        "nativelib.common.blocks.reader",
        ["src/nativelib/common/blocks/reader.pyx"],
    ),
    Extension(
        "nativelib.common.blocks.writer",
        ["src/nativelib/common/blocks/writer.pyx"],
    ),
]

setup(
    name="nativelib",
    package_dir={"": "src"},
    ext_modules=cythonize(extensions, language_level="3"),
    packages=[
        "nativelib.common",
        "nativelib.common.dtypes.functions",
        "nativelib.common.dtypes.objects",
        "nativelib.common.dtypes",
        "nativelib.common.columns",
        "nativelib.common.blocks",
    ],
    package_data={
        "nativelib": [
            "**/*.pyx",
            "**/*.pyi",
            "**/*.pxd",
            "*.pyx",
            "*.pyi",
            "*.pxd",
            "*.md",
            "*.txt",
        ]
    },
    exclude_package_data={
        "": ["*.c"],
        "nativelib": ["**/*.c"],
    },
    include_package_data=True,
    setup_requires=["Cython>=3.0"],
    zip_safe=False,
)
