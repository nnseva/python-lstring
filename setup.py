from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
import os
import shutil
import urllib.request
import tarfile
import tempfile
import subprocess


def _run(cmd, cwd=None, env=None):
    print('Running:', ' '.join(cmd), 'cwd=', cwd or os.getcwd())
    subprocess.check_call(cmd, cwd=cwd, env=env)


def _is_windows():
    return os.name == 'nt'


def _find_first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def _safe_extract_tar(tar, path):
    # Basic tar traversal protection.
    abs_path = os.path.abspath(path)
    for member in tar.getmembers():
        member_path = os.path.abspath(os.path.join(path, member.name))
        if not member_path.startswith(abs_path + os.sep) and member_path != abs_path:
            raise RuntimeError('Blocked unsafe path in tar: %r' % member.name)
    tar.extractall(path=path)


def _collect_sources(root_dir, exts=('.c', '.cc', '.cpp', '.cxx')):
    sources = []
    root_dir = os.path.abspath(root_dir)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # prune common non-library directories if present
        parts = set(dirpath.split(os.sep))
        if parts.intersection({'test', 'tests', 'samples', 'example', 'examples', 'doc', 'docs'}):
            continue

        for fname in filenames:
            if fname.endswith(exts):
                sources.append(os.path.join(dirpath, fname))

    sources.sort()
    return sources


def _ensure_icu_extracted(icu_version, icu_url):
    os.makedirs('build', exist_ok=True)
    icu_build_root = os.path.abspath(os.path.join('build', f'icu4c-{icu_version}'))

    # Reuse an existing extraction if present.
    if os.path.isdir(os.path.join(icu_build_root, 'icu', 'source')):
        icu_source_dir = os.path.abspath(os.path.join(icu_build_root, 'icu', 'source'))
        return icu_build_root, icu_source_dir

    print('ICU predownloaded build not found; will attempt to download')
    print('Attempting to download ICU from', icu_url)

    tmpfd, tmpname = tempfile.mkstemp(suffix='.tgz')
    os.close(tmpfd)
    req = urllib.request.Request(icu_url, headers={'User-Agent': 'python-urllib/3.x (embed-icu)'})
    with urllib.request.urlopen(req) as resp:
        if getattr(resp, 'status', 200) != 200:
            raise RuntimeError(f'HTTP error downloading ICU: {getattr(resp, "status", None)}')
        with open(tmpname, 'wb') as out:
            shutil.copyfileobj(resp, out)

    with tarfile.open(tmpname, 'r:gz') as tf:
        os.makedirs(icu_build_root, exist_ok=True)
        _safe_extract_tar(tf, path=icu_build_root)

    if not os.path.isdir(os.path.join(icu_build_root, 'icu', 'source')):
        raise RuntimeError('Unexpected ICU tarball layout after extraction (expected icu/source)')

    icu_source_dir = os.path.abspath(os.path.join(icu_build_root, 'icu', 'source'))
    return icu_build_root, icu_source_dir


def _pick_icu_data_dat(icu_source_dir, icu_version):
    # Prefer a prebuilt versioned ICU data file already shipped in the ICU source tarball.
    # For ICU 75_1 this is typically: icu/source/data/in/icudt75l.dat
    icu_data_in = os.path.join(icu_source_dir, 'data', 'in')
    if not os.path.isdir(icu_data_in):
        raise RuntimeError('ICU data/in directory not found at %s' % icu_data_in)

    major = (icu_version.split('_', 1)[0] or '').strip()
    preferred = None
    if major.isdigit():
        preferred = f'icudt{int(major)}l.dat'

    if preferred:
        candidate = os.path.join(icu_data_in, preferred)
        if os.path.isfile(candidate):
            return candidate, preferred

    # Fallback: pick any icudt*.dat found.
    for fname in sorted(os.listdir(icu_data_in)):
        if fname.startswith('icudt') and fname.endswith('.dat'):
            return os.path.join(icu_data_in, fname), fname

    raise RuntimeError('No icudt*.dat found under %s' % icu_data_in)


def _ensure_icu_data_in_package(icu_source_dir, icu_version):
    src_dat, dat_name = _pick_icu_data_dat(icu_source_dir, icu_version)
    pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'lstring', '_icu_data'))
    os.makedirs(pkg_dir, exist_ok=True)
    dst_dat = os.path.join(pkg_dir, dat_name)

    # Copy only if missing or changed in size.
    if not os.path.isfile(dst_dat) or os.path.getsize(dst_dat) != os.path.getsize(src_dat):
        print('Copying ICU data into package:', dat_name)
        shutil.copy2(src_dat, dst_dat)
    return dst_dat

ext_modules = [
    Extension(
        name='_lstring',
        sources=[
            'src/lstring.cxx',
            'src/lstring_methods.cxx',
            'src/lstring_utils.cxx',
            'src/lstring_module.cxx',
            'src/lstring_re_module.cxx',
            'src/lstring_re_pattern.cxx',
            'src/lstring_re_match.cxx',
        ],
        include_dirs=['.'],
        depends=[
            'src/buffer.hxx',
            'src/join_buffer.hxx',
            'src/mul_buffer.hxx',
            'src/slice_buffer.hxx',
            'src/str_buffer.hxx',
            'src/tptr.hxx',
            'src/lstring.hxx',
            'src/lstring_utils.hxx',
            'src/lstring_re.hxx',
            'src/lstring_re_iterator.hxx',
            'src/lstring_re_regex.hxx',
            'src/lstring_re_pattern.hxx',
            'src/lstring_re_match.hxx',
        ],
        language='c++',
    ),
]

class BuildExt(build_ext):
    def build_extensions(self):
        # Delayed import of cppy to let setup_requires install it if
        # necessary
        import cppy

        # --- ICU ---
        # Single build mode (Linux only): compile ICU common sources directly into the extension (Boost-like).
        # No ICU configure/make/install step is run. ICU data is taken from the ICU source tarball
        # (icudtXXl.dat) and shipped as Python package data under lstring/_icu_data/.
        icu_inc_dir = None
        icu_common_src_dir = None
        icu_common_sources = []
        icu_stubdata_source = None

        if _is_windows():
            raise RuntimeError('ICU sources build is not configured for Windows in this setup.py')

        # Download/extract ICU4C similarly to how we embed Boost.
        # Use ICU source release tarball.
        icu_version = os.environ.get('ICU_VERSION') or '75_1'
        icu_url = os.environ.get('ICU_URL')
        if not icu_url:
            # unicode-org/icu release naming convention.
            icu_url = f'https://github.com/unicode-org/icu/releases/download/release-{icu_version.replace("_", "-")}/icu4c-{icu_version}-src.tgz'

        icu_build_root, icu_source_dir = _ensure_icu_extracted(icu_version, icu_url)

        # Ensure the ICU data file is available as package data.
        _ensure_icu_data_in_package(icu_source_dir, icu_version)

        # Use ICU headers directly from the source tree.
        # Public headers are under: icu/source/common/unicode/*
        icu_inc_dir = os.path.join(icu_source_dir, 'common')

        icu_common_src_dir = os.path.join(icu_source_dir, 'common')
        if not os.path.isdir(icu_common_src_dir):
            raise RuntimeError('ICU common sources not found at %s' % icu_common_src_dir)
        icu_common_sources = _collect_sources(icu_common_src_dir)
        if not icu_common_sources:
            raise RuntimeError('No ICU common sources found under %s' % icu_common_src_dir)

        # ICU common references the ICU data entry point symbol (icudtXX_dat) which is
        # normally provided by libicudata. We avoid linking system ICU by compiling
        # ICU's stubdata implementation into the extension. Runtime data comes from the
        # packaged icudt*.dat file loaded via u_setDataDirectory/u_init.
        icu_stubdata_source = os.path.join(icu_source_dir, 'stubdata', 'stubdata.cpp')
        if not os.path.isfile(icu_stubdata_source):
            raise RuntimeError('ICU stubdata source not found at %s' % icu_stubdata_source)

        print('Embedded ICU include dir:', icu_inc_dir)
        print('Will compile ICU common sources:', len(icu_common_sources))
        print('Will compile ICU stubdata source:', icu_stubdata_source)

        ct = self.compiler.compiler_type
        for ext in self.extensions:
            # cppy.get_include() collect the path of the header files
            ext.include_dirs.insert(0, cppy.get_include())

            # Wire ICU include/lib into the extension build.
            if icu_inc_dir and icu_inc_dir not in ext.include_dirs:
                ext.include_dirs.insert(0, icu_inc_dir)

            if icu_common_src_dir:
                # Needed for ICU internal headers included by its .cpp files
                if icu_common_src_dir not in ext.include_dirs:
                    ext.include_dirs.insert(0, icu_common_src_dir)

            if not hasattr(ext, 'extra_link_args') or ext.extra_link_args is None:
                ext.extra_link_args = []
            # ICU common uses pthreads/stdlib bits on Linux.
            for arg in ['-pthread', '-ldl', '-lm']:
                if arg not in ext.extra_link_args:
                    ext.extra_link_args.append(arg)
            # Embedding-only flow: ensure boost headers exist (download if needed)
            boost_inc = None
            # prefer user-specified BOOST_ROOT pointing to boost root containing 'boost' dir
            boost_root = os.environ.get('BOOST_ROOT')
            if boost_root:
                # Accept a layout where BOOST_ROOT/libs/regex/include present)
                if not os.path.isdir(os.path.join(boost_root, 'libs', 'regex', 'include')):
                    raise RuntimeError('BOOST_ROOT does not contain Boost regex headers')
                boost_inc = boost_root
            elif os.path.isdir('build'):
                # check for an already-extracted boost_<ver> or boost-<ver> in build/
                for d in os.listdir('build'):
                    if d.startswith('boost_') or d.startswith('boost-'):
                        print('Found existing Boost extraction in build/', d)
                        extracted_root = os.path.join('build', d)
                        if os.path.isdir(extracted_root):
                            # Accept layout the root boost-<ver> tree
                            boost_inc = extracted_root
                            break
            if not boost_inc:
                print('Boost predownloaded build not found; will attempt to download')
                boost_url = os.environ.get('BOOST_URL')
                if not boost_url:
                    # canonical GitHub 1.82.0 release
                    boost_url = 'https://github.com/boostorg/boost/releases/download/boost-1.82.0/boost-1.82.0.tar.gz'

                print('Attempting to download Boost from', boost_url)
                os.makedirs('build', exist_ok=True)
                tmpfd, tmpname = tempfile.mkstemp(suffix='.tar.gz')
                os.close(tmpfd)
                # Use a Request with a User-Agent to avoid some mirrors returning HTML pages
                req = urllib.request.Request(boost_url, headers={'User-Agent': 'python-urllib/3.x (embed-boost)'})
                with urllib.request.urlopen(req) as resp:
                    if getattr(resp, 'status', 200) != 200:
                        raise RuntimeError(f'HTTP error downloading Boost: {getattr(resp, "status", None)}')
                    with open(tmpname, 'wb') as out:
                        shutil.copyfileobj(resp, out)
                # quick gzip signature check
                with open(tmpname, 'rb') as f:
                    sig = f.read(2)
                if sig != b'\x1f\x8b':
                    raise RuntimeError('Downloaded file is not gzip')
                with tarfile.open(tmpname, 'r:gz') as tf:
                    tf.extractall(path='build')
                # set boost_inc if we can detect extracted tree
                for d in os.listdir('build'):
                    if d.startswith('boost_') or d.startswith('boost-'):
                        extracted_root = os.path.join('build', d)
                        if os.path.isdir(extracted_root):
                            boost_inc = extracted_root
                            break

            if not boost_inc:
                raise RuntimeError('Boost headers not available; set BOOST_ROOT to the Boost root or ensure download works')

            # Determine base root of boost sources for includes and sources
            base_root = boost_inc
            # collect include dirs to add: libs/*/include
            include_dirs_added = [
                os.path.join(base_root, 'libs', 'config', 'include'),
                os.path.join(base_root, 'libs', 'assert', 'include'),
                os.path.join(base_root, 'libs', 'predef', 'include'),
                os.path.join(base_root, 'libs', 'throw_exception', 'include'),
                os.path.join(base_root, 'libs', 'core', 'include'),
                os.path.join(base_root, 'libs', 'mpl', 'include'),
                os.path.join(base_root, 'libs', 'type_traits', 'include'),
                os.path.join(base_root, 'libs', 'indirect_traits', 'include'),
                os.path.join(base_root, 'libs', 'detail', 'include'),
                os.path.join(base_root, 'libs', 'static_assert', 'include'),
                os.path.join(base_root, 'libs', 'preprocessor', 'include'),
                os.path.join(base_root, 'libs', 'iterator', 'include'),
                os.path.join(base_root, 'libs', 'regex', 'include'),
            ]

            # insert discovered include dirs at front
            for p in reversed(include_dirs_added):
                ext.include_dirs.insert(0, p)
            print('Embedded Boost include dirs:', include_dirs_added)

            # Find regex implementation sources inside boost and add to extension sources
            regex_src_dir = os.path.join(base_root, 'libs', 'regex', 'src')

            if not regex_src_dir or not os.path.isdir(regex_src_dir):
                # It is possible that the extracted 'boost' only contains headers and no libs/regex/src
                # In that case, raise, because embedding needs implementation files.
                raise RuntimeError('Boost regex implementation sources not found under extracted Boost; embedding requires full boost source tree')

            # collect .cpp files
            cpp_files = [os.path.join(regex_src_dir, f) for f in os.listdir(regex_src_dir) if f.endswith('.cpp')]
            if not cpp_files:
                raise RuntimeError('No Boost.Regex .cpp files found in %s' % regex_src_dir)

            # Insert regex cpp files to extension sources
            # put them after our own sources to ensure include dirs are set
            ext.sources.extend(cpp_files)
            print('Will compile Boost.Regex sources:', len(cpp_files))

            # Ensure macros and compile args to avoid autolinking and set C++ standard
            if not hasattr(ext, 'define_macros') or ext.define_macros is None:
                ext.define_macros = []

            # ICU build configuration
            # We compile ICU common objects into the same shared object.
            # U_COMMON_IMPLEMENTATION is required for ICU's internal symbol visibility.
            ext.define_macros.append(('U_COMMON_IMPLEMENTATION', '1'))

            # Add ICU common sources into this extension (Boost-like embedding)
            ext.sources.extend(icu_common_sources)
            ext.sources.append(icu_stubdata_source)
            # disable Boost auto-linking to avoid conflicts
            ext.define_macros.append(('BOOST_ALL_NO_LIB', None))
            # setup Boost locale to C++ locale
            ext.define_macros.append(('BOOST_REGEX_USE_CPP_LOCALE', '1'))

            # set C++ standard flags
            if not hasattr(ext, 'extra_compile_args') or ext.extra_compile_args is None:
                ext.extra_compile_args = []
            # use MSVC flag on Windows
            if ct == 'msvc':
                if '/std:c++17' not in ext.extra_compile_args:
                    ext.extra_compile_args.append('/std:c++17')
            else:
                if '-std=c++17' not in ext.extra_compile_args:
                    ext.extra_compile_args.append('-std=c++17')

        build_ext.build_extensions(self)


class BuildPy(build_py):
    def run(self):
        # Ensure ICU data file is present as package data before packaging.
        if _is_windows():
            raise RuntimeError('ICU sources build is not configured for Windows in this setup.py')

        icu_version = os.environ.get('ICU_VERSION') or '75_1'
        icu_url = os.environ.get('ICU_URL')
        if not icu_url:
            icu_url = f'https://github.com/unicode-org/icu/releases/download/release-{icu_version.replace("_", "-")}/icu4c-{icu_version}-src.tgz'
        _, icu_source_dir = _ensure_icu_extracted(icu_version, icu_url)
        _ensure_icu_data_in_package(icu_source_dir, icu_version)

        super().run()

setup(
    name='lstring',
    version='0.0.1',
    python_requires='>=3.5',
    # build-time requirements are declared in pyproject.toml
    packages=['lstring'],
    package_data={'lstring': ['_icu_data/*.dat']},
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt, 'build_py': BuildPy},
)
