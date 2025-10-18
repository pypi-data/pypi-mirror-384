# meson.build

project(
    'PyAstronomy-ext',
    'c', 'fortran',  # Explicitly enable the Fortran compiler
    version: '2.0.0',
    license: 'MIT',
    # Requires a modern Meson version
    meson_version: '>=0.64.0',
    default_options : ['buildtype=release'],
)



py_mod = import('python')
py = py_mod.find_installation(pure: false)
py_dep = py.dependency()

numpy_dep = dependency('numpy', required: true, fallback: ['numpy', 'numpy_dep'])

# This is required for compiling modules that interact with NumPy arrays.
incdir_numpy = run_command(py,
    ['-c', 'import numpy; print(numpy.get_include())'],
    check : true
).stdout().strip()

incdir_f2py = run_command(py,
    ['-c', 'import os; os.chdir(".."); import numpy.f2py; print(numpy.f2py.get_include())'],
    check : true
).stdout().strip()

# 3. Create an include directory object for Meson
inc_np = include_directories(incdir_numpy, incdir_f2py)

f2py_exe = find_program(py.get_path('scripts') / 'f2py')

# First, install the top-level package directory and its __init__.py.
install_subdir(
    'PyAstronomy_ext',
    install_dir: py.get_install_dir(),
    # This is new: only install the __init__.py, nothing else from this level.
    # It prevents us from recursively installing subdirectories that we want to handle manually.
    exclude_directories: ['forTrans']
)


install_data(
    ['PyAstronomy_ext/forTrans/__init__.py'],
    install_dir: py.get_install_dir() / 'PyAstronomy_ext' / 'forTrans'
)

# Get the platform-specific extension suffix (e.g., .cpython-310-x86_64-linux-gnu.so)
# There is no direct Meson function, so we must ask Python's sysconfig.
ext_suffix = run_command(py,
    ['-c', 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))'],
    check: true
).stdout().strip()

# Get NumPy include path
numpy_inc = run_command(py, ['-c', 'import numpy; print(numpy.get_include())'], check: true).stdout().strip()

 

# Define the target for 'occultnl'
occultnl_module = custom_target(
    'occultnl',
    # Output filename must be exactly what Python expects
    output: 'occultnl' + ext_suffix,
    input: [
        'PyAstronomy_ext/forTrans/occultnl.pyf',
        'PyAstronomy_ext/forTrans/occultnl.f'
    ],
    # This is the command that will be run
    command: [
        f2py_exe,
        '-c', # This tells f2py to compile and build the module
        '-m', 'occultnl', # The name of the module to create
        '--quiet',
        '@INPUT@', # The list of input files
        # We need to explicitly tell it where to find NumPy headers
        '-I' + numpy_inc,
    ],
    # This tells Meson to install the resulting .so file
    install: true,
    install_dir: py.get_install_dir() / 'PyAstronomy_ext' / 'forTrans'
)



# Define the target for 'occultquad'
occultquad_module = custom_target(
    'occultquad',
    # Output filename must be exactly what Python expects
    output: 'occultquad' + ext_suffix,
    input: [
        'PyAstronomy_ext/forTrans/occultquad.pyf',
        'PyAstronomy_ext/forTrans/occultquad.f'
    ],
    # This is the command that will be run
    command: [
        f2py_exe,
        '-c', # This tells f2py to compile and build the module
        '-m', 'occultquad', # The name of the module to create
        '--quiet',
        '@INPUT@', # The list of input files
        # We need to explicitly tell it where to find NumPy headers
        '-I' + numpy_inc,
    ],
    # This tells Meson to install the resulting .so file
    install: true,
    install_dir: py.get_install_dir() / 'PyAstronomy_ext' / 'forTrans'
)

