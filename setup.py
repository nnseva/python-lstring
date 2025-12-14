from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

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
        build_ext.build_extensions(self)

setup(
    name='lstring',
    version='0.0.1',
    python_requires='>=3.5',
    setup_requires=[
        'setuptools',
        'cppy'
    ],
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
)
