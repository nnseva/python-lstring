from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys

ext_modules = [
    Extension(
        name='_lstring',
        sources=[
            'src/lstring.cxx',
            'src/lstring_concat.cxx',
            'src/lstring_methods.cxx',
            'src/lstring_utils.cxx',
            'src/lstring_module.cxx',
            'src/buffer.cxx',
        ],
        include_dirs=['.', './include'],
        depends=[
            'src/join_buffer.hxx',
            'src/mul_buffer.hxx',
            'src/slice_buffer.hxx',
            'src/str_buffer.hxx',
            'src/tptr.hxx',
            'lstring/include/lstring/lstring.hxx',
            'src/_lstring.hxx',
            'src/lstring_utils.hxx',
            'src/charset.hxx',
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
            ext.include_dirs.insert(0, 'lstring/include')

            extra_compile_args = list(getattr(ext, 'extra_compile_args', []) or [])
            extra_link_args = list(getattr(ext, 'extra_link_args', []) or [])

            if ct == 'unix':
                # clang on macOS may default to an older C++ dialect; this project requires
                # at least C++11 (constexpr, override, make_unique, etc).
                if '-std=c++17' not in extra_compile_args:
                    extra_compile_args.append('-std=c++17')
                if sys.platform == 'darwin':
                    if '-stdlib=libc++' not in extra_compile_args:
                        extra_compile_args.append('-stdlib=libc++')
                    if '-stdlib=libc++' not in extra_link_args:
                        extra_link_args.append('-stdlib=libc++')
            elif ct == 'msvc':
                if '/std:c++17' not in extra_compile_args:
                    extra_compile_args.append('/std:c++17')

            ext.extra_compile_args = extra_compile_args
            ext.extra_link_args = extra_link_args

        build_ext.build_extensions(self)

setup(
    name='lstring',
    use_scm_version=True,
    python_requires='>=3.10',
    # build-time requirements are declared in pyproject.toml
    description='True Python lazy string implemented as a C++ extension',
    author='Vsevolod Novikov',
    author_email='nnseva@gmail.com',
    url='https://github.com/nnseva/python-lstring',
    project_urls={
        'Source': 'https://github.com/nnseva/python-lstring',
        'Issues': 'https://github.com/nnseva/python-lstring/issues',
    },
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: 3.15',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: C++',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Topic :: Software Development :: Libraries',
    ],
    keywords=[
        'string',
        'lazy',
        'lazy-string',
        'concatenation',
        'unicode',
        'substring',
        'c-extension',
        'c++-extension',
        'cpython',
        'slicing',
        'extension',
        'performance',
        'memory-efficient',
    ],
    license='LGPLv3',
    packages=['lstring'],
    package_data={'lstring': ['include/lstring/lstring.hxx']},
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
)
