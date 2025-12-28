from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import shutil
import urllib.request
import tarfile
import tempfile

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

        ct = self.compiler.compiler_type
        for ext in self.extensions:
            # cppy.get_include() collect the path of the header files
            ext.include_dirs.insert(0, cppy.get_include())
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

setup(
    name='lstring',
    version='0.0.1',
    python_requires='>=3.5',
    # build-time requirements are declared in pyproject.toml
    py_modules=['lstring'],
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
)
