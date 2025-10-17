import os
import sys
from shutil import rmtree
from sys import platform

from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

PKG_BIN_DIR = "applitools/core_universal/bin"
USDK_BUILD_DIR = os.getenv("USDK_BUILD_DIR", "applitools/core_universal/built_bins")

PLAT_EXECUTABLE = {
    "macosx_10_7_x86_64": "core-macos",
    "macosx_11_0_arm64": "core-macos-arm64",
    "manylinux1_x86_64": "core-linux",
    "manylinux2014_aarch64": "core-linux-arm64",
    "musllinux_1_2_x86_64": "core-alpine",
    "win_amd64": "core-win.exe",
}


def get_included_platforms():
    """Get the list of platforms to include in source distribution.

    Can be specified via:
    - INCLUDE_PLATFORMS environment variable (comma-separated)
    - --include-platforms command-line argument (comma-separated)

    Examples:
        INCLUDE_PLATFORMS=manylinux1_x86_64,manylinux2014_aarch64 python setup.py sdist
        python setup.py sdist --include-platforms=manylinux1_x86_64,manylinux2014_aarch64

    If not specified, all platforms are included.
    """
    # Check environment variable first
    if "INCLUDE_PLATFORMS" in os.environ:
        platforms = os.environ["INCLUDE_PLATFORMS"].split(",")
        return [p.strip() for p in platforms if p.strip()]

    # Check command-line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--include-platforms" and i + 1 < len(sys.argv):
            platforms = sys.argv[i + 1].split(",")
            return [p.strip() for p in platforms if p.strip()]
        elif arg.startswith("--include-platforms="):
            platforms = arg.split("=", 1)[1].split(",")
            return [p.strip() for p in platforms if p.strip()]

    # Default: include all platforms
    return list(PLAT_EXECUTABLE.keys())


def current_plat():
    if platform == "darwin":
        if os.uname().machine == "arm64":
            return "macosx_11_0_arm64"
        return "macosx_10_7_x86_64"
    elif platform == "win32":
        return "win_amd64"
    elif platform in ("linux", "linux2"):
        if os.uname().machine == "aarch64":
            return "manylinux2014_aarch64"
        if os.path.exists("/etc/alpine-release"):
            return "musllinux_1_2_x86_64"
        else:
            return "manylinux1_x86_64"
    else:
        raise Exception("Platform is not supported", platform)


def get_target_platform():
    """Get the target platform from environment variable, build command arguments, or fall back to current platform."""
    # Check if PLAT_NAME is specified in environment variable
    if "PLAT_NAME" in os.environ:
        return os.environ["PLAT_NAME"]

    # Check if --plat-name is specified in command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--plat-name" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        elif arg.startswith("--plat-name="):
            return arg.split("=", 1)[1]

    # Fall back to current platform
    return current_plat()


# Select executable based on target platform
target_platform = get_target_platform()
selected_executable = PLAT_EXECUTABLE.get(
    target_platform, PLAT_EXECUTABLE[current_plat()]
)
commands = set()

# Download previously selected executable.
# It is downloaded to the source tree (so editable setup works).
@commands.add
class build_py(_build_py):  # noqa
    def get_data_files(self):
        if not self.dry_run and os.path.isdir(PKG_BIN_DIR):
            rmtree(PKG_BIN_DIR)

        # Use os.makedirs instead of self.mkpath for better reliability
        os.makedirs(PKG_BIN_DIR, exist_ok=True)

        _, ext = os.path.splitext(selected_executable)
        target_name = os.path.join(PKG_BIN_DIR, "core" + ext)
        if USDK_BUILD_DIR:
            built_file_name = os.path.join(USDK_BUILD_DIR, selected_executable)
            self.copy_file(built_file_name, target_name)
        else:
            version = self.distribution.get_version()
            self.announce(
                "downloading version %s of %s executable"
                % (version, selected_executable),
                2,
            )
        os.chmod(target_name, 0o755)
        return _build_py.get_data_files(self)

    def run(self):
        """Run build_py and then remove built_bins from build directory (for wheels only)."""
        _build_py.run(self)
        # Remove built_bins from build directory after the build completes
        built_bins_in_build = os.path.join(
            self.build_lib, "applitools", "core_universal", "built_bins"
        )
        if os.path.isdir(built_bins_in_build):
            self.announce(f"Removing {built_bins_in_build} from wheel build", 2)
            rmtree(built_bins_in_build)


@commands.add
class bdist_wheel(_bdist_wheel):  # noqa
    def finalize_options(self):
        super().finalize_options()
        # Always set the platform name to match the target platform
        self.plat_name = target_platform
        # Also ensure the root_is_pure is False since we have platform-specific binaries
        self.root_is_pure = False

    def get_tag(self):
        # Force the platform tag to match our target platform
        # Use py3 tag to make wheels compatible with all Python 3.x versions
        impl, abi, plat = super().get_tag()
        return "py3", "none", target_platform


@commands.add
class sdist(_sdist):  # noqa
    def make_release_tree(self, base_dir, files):
        # Create the source tree
        super().make_release_tree(base_dir, files)

        # Remove bin/ directory from source distribution
        # The universal sdist should only contain built_bins/ with all platform binaries
        # Wheels will create bin/ with platform-specific binary during build
        bin_dir_in_sdist = os.path.join(base_dir, "applitools", "core_universal", "bin")
        if os.path.isdir(bin_dir_in_sdist):
            self.announce(f"Removing {bin_dir_in_sdist} from source distribution", 2)
            rmtree(bin_dir_in_sdist)

        # Filter built_bins based on included platforms
        included_platforms = get_included_platforms()
        built_bins_dir = os.path.join(
            base_dir, "applitools", "core_universal", "built_bins"
        )

        if os.path.isdir(built_bins_dir):
            # Get list of executables to keep
            executables_to_keep = [
                PLAT_EXECUTABLE[plat]
                for plat in included_platforms
                if plat in PLAT_EXECUTABLE
            ]

            # Remove executables not in the included list
            for filename in os.listdir(built_bins_dir):
                filepath = os.path.join(built_bins_dir, filename)
                if os.path.isfile(filepath) and filename not in executables_to_keep:
                    self.announce(
                        f"Removing {filename} from source distribution (not in included platforms)",
                        2,
                    )
                    os.remove(filepath)

            # Log which platforms are included
            self.announce(
                f"Including binaries for platforms: {', '.join(included_platforms)}",
                2,
            )


setup(cmdclass={c.__name__: c for c in commands})
