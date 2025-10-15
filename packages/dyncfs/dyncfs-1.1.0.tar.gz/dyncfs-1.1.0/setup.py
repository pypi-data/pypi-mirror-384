import os
import glob
import platform
import shutil
import subprocess
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py

project_root = os.path.dirname(os.path.abspath(__file__))

# req_file = os.path.join(project_root, "requirements.txt")
# with open(req_file, encoding="utf-8") as f:
#     requirements = [
#         line.strip() for line in f if line.strip() and not line.startswith("#")
#     ]

platform_exec = "exe" if platform.system() == "Windows" else "bin"


class CustomBuildPy(_build_py):
    def run(self):
        _build_py.run(self)

        if not shutil.which("gfortran"):
            raise ValueError(
                "Please install gfortran and ensure "
                "that command 'gfortran' can be directly called"
            )
        if not shutil.which("jar"):
            raise ValueError(
                "Please install java and ensure that "
                "command 'jar' can be directly called"
            )

        exec_dir = os.path.join(project_root, "dyncfs", "exec")
        os.makedirs(exec_dir, exist_ok=True)

        fortran_src_root = os.path.join(project_root, "fortran_src_codes")
        fortran_subdirs = {
            "edgrn2.0_src": f"edgrn2.{platform_exec}",
            "edcmp2.0_src": f"edcmp2.{platform_exec}",
            "qssp2020_src": f"qssp2020.{platform_exec}",
            "qseis2025_src": f"qseis2025.{platform_exec}",
        }

        for src_folder, bin_name in fortran_subdirs.items():
            fortran_src_dir = os.path.join(fortran_src_root, src_folder)
            output_binary = os.path.join(exec_dir, bin_name)

            patterns = ["*.f", "*.for", "*.f90", "*.F", "*.F90"]
            files = []
            for pat in patterns:
                files.extend(glob.glob(os.path.join(fortran_src_dir, pat)))
            if not files:
                raise RuntimeError(f"No Fortran sources found in {fortran_src_dir}")

            extra_fflags = os.environ.get("DYNCS_FFLAGS", "")
            extra_list = extra_fflags.split() if extra_fflags else []

            args = ["gfortran", "-O3", "-I", fortran_src_dir, *extra_list]
            if src_folder == "qseis2025_src":
                args.append("-ffixed-line-length-none")
            args += files + ["-o", output_binary]

            print("[dyncfs] Compiling", src_folder, "->", output_binary)
            proc = subprocess.run(args, cwd=fortran_src_dir, text=True, capture_output=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                raise RuntimeError(f"Fortran compilation failed for {src_folder} (exit {proc.returncode})")


setup(
    url="https://github.com/Zhou-Jiangcheng/dyncfs",
    packages=find_packages(),
    include_package_data=True,
    package_data={"dyncfs": ["exec/*"]},
    # install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    entry_points={"console_scripts": ["dyncfs=dyncfs.main:main"]},
    cmdclass={"build_py": CustomBuildPy},  # type: ignore
)
