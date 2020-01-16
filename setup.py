from __future__ import print_function, absolute_import
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from distutils.file_util import copy_file
from distutils.dir_util import mkpath
from distutils import log
import os
import subprocess


cmdclass = {}
try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    pass
else:

    class UniversalBdistWheel(bdist_wheel):
        def get_tag(self):
            return ("py2.py3", "none") + bdist_wheel.get_tag(self)[2:]

    cmdclass["bdist_wheel"] = UniversalBdistWheel


class Executable(Extension):

    if os.name == "nt":
        suffix = ".exe"
    else:
        suffix = ""

    def __init__(self, name, build_cmd, output_dir=".", cwd=None, env=None):
        Extension.__init__(self, name, sources=[])
        self.target = self.name.split(".")[-1] + self.suffix
        self.build_cmd = build_cmd
        self.output_dir = output_dir
        self.cwd = cwd
        self.env = env


class ExecutableBuildExt(build_ext):
    def finalize_options(self):
        from distutils.ccompiler import get_default_compiler

        build_ext.finalize_options(self)

        if self.compiler is None:
            self.compiler = get_default_compiler(os.name)
        self._compiler_env = dict(os.environ)

    def get_ext_filename(self, ext_name):
        for ext in self.extensions:
            if isinstance(ext, Executable):
                return os.path.join(*ext_name.split(".")) + ext.suffix
        return build_ext.get_ext_filename(self, ext_name)

    def run(self):
        if self.compiler == "msvc":
            self.call_vcvarsall_bat()

        build_ext.run(self)

    def call_vcvarsall_bat(self):
        import struct
        from distutils._msvccompiler import _get_vc_env

        arch = "x64" if struct.calcsize("P") * 8 == 64 else "x86"
        vc_env = _get_vc_env(arch)
        self._compiler_env.update(vc_env)

    def build_extension(self, ext):
        if not isinstance(ext, Executable):
            build_ext.build_extension(self, ext)
            return

        exe_fullpath = os.path.join(ext.output_dir, ext.target)
        if not os.path.exists(exe_fullpath) or self.force:
            cmd = ext.build_cmd
            if self.force:
                cmd += " --force"
            log.debug("running '{}'".format(cmd))
            if not self.dry_run:
                env = self._compiler_env.copy()
                if ext.env:
                    env.update(ext.env)
                p = subprocess.run(cmd, cwd=ext.cwd, env=env, shell=True)
                if p.returncode != 0:
                    from distutils.errors import DistutilsExecError

                    raise DistutilsExecError(
                        "running '{}' command failed".format(ext.build_cmd)
                    )

        dest_path = self.get_ext_fullpath(ext.name)
        mkpath(os.path.dirname(dest_path), verbose=self.verbose, dry_run=self.dry_run)

        copy_file(exe_fullpath, dest_path, verbose=self.verbose, dry_run=self.dry_run)


cmdclass["build_ext"] = ExecutableBuildExt

cargo_root = os.path.join("build", "cargo")
bin_path = os.path.join(cargo_root, "bin")
usvg = Executable(
    "usvg.usvg",
    build_cmd="cargo install --root '{}' usvg-cli".format(cargo_root),
    output_dir=bin_path,
)

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="usvg",
    use_scm_version={"write_to": "src/usvg/_version.py"},
    description=("Python wrapper for the resvg/usvg tool"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cosimo Lupo",
    author_email="cosimo@anthrotype.com",
    url="https://github.com/anthrotype/usvg-python",
    license="OpenSource, BSD-style",
    platforms=["posix", "nt"],
    package_dir={"": "src"},
    packages=find_packages("src"),
    ext_modules=[usvg],
    zip_safe=False,
    cmdclass=cmdclass,
    install_requires=["importlib_resources; python_version < '3.7'"],
    setup_requires=["setuptools_scm"],
    extras_require={"testing": ["pytest"]},
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Text Processing :: Fonts",
        "Topic :: Multimedia :: Graphics",
    ],
)
