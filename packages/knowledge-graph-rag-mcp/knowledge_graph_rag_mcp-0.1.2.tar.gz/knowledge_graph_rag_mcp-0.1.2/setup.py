from __future__ import annotations

import os
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler
from distutils import log


class build_py(_build_py):
    """Extend build_py to compile the bfsvtab sqlite extension."""

    def run(self) -> None:  # type: ignore[override]
        super().run()
        self._build_bfsvtab()

    def _build_bfsvtab(self) -> None:
        source = Path("vendor/bfsvtab/bfsvtab.c")
        if not source.exists():
            log.warn("bfsvtab source not found at %s; skipping build", source)
            return

        include_dir = Path("vendor/bfsvtab/sqlite")
        build_lib = Path(self.build_lib)
        target_dir = build_lib / "knowledge_graph_rag_mcp" / "native"
        target_dir.mkdir(parents=True, exist_ok=True)

        compiler = new_compiler()
        customize_compiler(compiler)

        extra_postargs = []
        if os.name != "nt":
            extra_postargs.append("-fPIC")

        log.info("compiling bfsvtab extension")
        objects = compiler.compile(
            [str(source)],
            include_dirs=[str(include_dir.resolve())],
            extra_postargs=extra_postargs,
        )

        output_name = "bfsvtab.dll" if os.name == "nt" else "bfsvtab.so"
        output_path = target_dir / output_name
        log.info("linking bfsvtab -> %s", output_path)
        compiler.link_shared_object(objects, str(output_path))

        # Clean up intermediate object files
        for obj in objects:
            try:
                Path(obj).unlink()
            except OSError:
                pass


setup(cmdclass={"build_py": build_py})
