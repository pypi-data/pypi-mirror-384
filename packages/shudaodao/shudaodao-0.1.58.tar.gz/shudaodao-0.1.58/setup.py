#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from setuptools import find_namespace_packages, setup


def _get_c_extensions():
    from pathlib import Path
    import os
    from setuptools import Extension

    setup_dir = Path(__file__).parent
    ext_modules = []

    for c_file in (setup_dir / "src").rglob("*.c"):
        # 跳过不在 src 下的文件（安全）
        try:
            rel_path = c_file.relative_to(setup_dir)
        except ValueError:
            continue

        # 模块名：去掉 .c，用点分隔
        module_name = str(rel_path.with_suffix("")).replace(os.sep, ".").replace("src.", "", 1)

        # 关键：sources 必须是相对路径字符串
        ext_modules.append(Extension(
            name=module_name,
            sources=[str(rel_path)],  # e.g., "src/shudaodao_core/app/base_app.c"
            extra_compile_args=[] if os.name == 'nt' else [
                "-Wno-unreachable-code-fallthrough",
                "-Wno-unused-function",
            ]
        ))
    return ext_modules


# ext_modules = _get_c_extensions()
# for ext in ext_modules:
#     for src in ext.sources:
#         if os.path.isabs(src):
#             raise ValueError(f"Absolute path not allowed: {src}")

setup(
    name="shudaodao",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "": ["*.pyi"],  # 包含所有包中的 .pyi 文件
    },
    ext_modules=_get_c_extensions(),  # ← 直接传 Extension，不 cythonize
    zip_safe=False,
)
