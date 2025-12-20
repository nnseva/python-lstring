from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import shutil
import urllib.request
import tarfile
import tempfile

ext_modules = [
    Extension(
        name='lstring',
        sources=[
            'src/lstring.cxx',
            'src/lstring_methods.cxx',
            'src/lstring_utils.cxx',
            'src/lstring_module.cxx'
        ],
        include_dirs=['.'],
        depends=[
            'src/buffer.hxx',
            'src/join_buffer.hxx',
            'src/mul_buffer.hxx',
            'src/slice_buffer.hxx',
            'src/str_buffer.hxx',
            'src/lstring.hxx',
            'src/lstring_utils.hxx',
        ],
        language='c++',
    ),
]

class BuildExt(build_ext):
    def build_extensions(self):
        # Delayed import of cppy to let setup_requires install it if
        # necessary
        import cppy

        ct = self.compiler.compiler_type
        for ext in self.extensions:
            # cppy.get_include() collect the path of the header files
            ext.include_dirs.insert(0, cppy.get_include())
            # Embedding-only flow: ensure boost headers exist (download if needed)
            boost_inc = None
            # prefer user-specified BOOST_ROOT pointing to boost root containing 'boost' dir
            boost_root = os.environ.get('BOOST_ROOT')
            if boost_root:
                # Accept either a layout where BOOST_ROOT/boost exists (headers) or
                # a full extracted source tree (BOOST_ROOT/libs/regex/include present)
                if os.path.isdir(os.path.join(boost_root, 'boost')) or os.path.isdir(os.path.join(boost_root, 'libs', 'regex', 'include')):
                    boost_inc = boost_root

            # if not provided, check build/_boost_include
            if not boost_inc:
                candidate = os.path.abspath(os.path.join('build', '_boost_include'))
                if os.path.isdir(candidate):
                    boost_inc = candidate

            # also check for an already-extracted boost_<ver> or boost-<ver> in build/
            if not boost_inc and os.path.isdir('build'):
                for d in os.listdir('build'):
                    if d.startswith('boost_') or d.startswith('boost-'):
                        extracted_root = os.path.join('build', d)
                        if os.path.isdir(extracted_root):
                            # Accept either layout: nested 'boost' dir or the root boost-<ver> tree
                            boost_inc = extracted_root
                            break

            # download boost and extract full boost/ into build/_boost_include if necessary
            if not boost_inc:
                # Try a small set of likely URLs (user can override with BOOST_URL)
                user_url = os.environ.get('BOOST_URL')
                candidates = []
                if user_url:
                    candidates.append(user_url)
                # canonical GitHub release (dash and underscore variants)
                candidates.extend([
                    'https://github.com/boostorg/boost/releases/download/boost-1.82.0/boost-1.82.0.tar.gz',
                    'https://github.com/boostorg/boost/releases/download/boost-1.82.0/boost_1_82_0.tar.gz',
                    # jfrog mirror as fallback
                    'https://boostorg.jfrog.io/artifactory/main/release/1.82.0/source/boost_1_82_0.tar.gz',
                ])
                last_exc = None
                tmpname = None
                for url in candidates:
                    try:
                        target = os.path.abspath(os.path.join('build', '_boost_include'))
                        print('Attempting to download Boost from', url)
                        os.makedirs('build', exist_ok=True)
                        tmpfd, tmpname = tempfile.mkstemp(suffix='.tar.gz')
                        os.close(tmpfd)
                        # Use a Request with a User-Agent to avoid some mirrors returning HTML pages
                        req = urllib.request.Request(url, headers={'User-Agent': 'python-urllib/3.x (embed-boost)'})
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
                        if boost_inc:
                            # success
                            break
                    except Exception as e:
                        last_exc = e
                        if tmpname and os.path.exists(tmpname):
                            try:
                                os.unlink(tmpname)
                            except Exception:
                                pass
                        tmpname = None
                        continue
                if not boost_inc:
                    # surface a clearer error including the last exception
                    raise RuntimeError('Failed to download and extract Boost; last error: %r' % (last_exc,))

            if not boost_inc:
                raise RuntimeError('Boost headers not available; set BOOST_ROOT or ensure download works')

            # Determine base root of boost sources for includes and sources
            base_root = boost_inc
            # If boost_inc points to a 'boost' subdir, base_root should be its parent
            if os.path.isdir(os.path.join(boost_inc, 'boost')):
                # boost_inc is a directory that contains 'boost' (maybe the root)
                base_root = boost_inc
            # collect include dirs to add: root (if contains 'boost') and libs/*/include where present
            include_dirs_added = []
            if os.path.isdir(os.path.join(base_root, 'boost')):
                include_dirs_added.append(base_root)
            # also add libs/regex/include if present
            regex_inc = os.path.join(base_root, 'libs', 'regex', 'include')
            if os.path.isdir(regex_inc):
                include_dirs_added.append(regex_inc)

            # fallback: if none found but boost_inc exists, add it
            if not include_dirs_added:
                include_dirs_added.append(boost_inc)

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
            # disable Boost auto-linking to avoid conflicts
            ext.define_macros.append(('BOOST_ALL_NO_LIB', None))

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

setup(
    name='lstring',
    version='0.0.1',
    python_requires='>=3.5',
    # build-time requirements are declared in pyproject.toml
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
)
