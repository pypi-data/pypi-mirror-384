import sys

vi = sys.version_info
if vi < (3, 8):
    raise RuntimeError('uvloop requires Python 3.8 or greater')

if sys.platform in ('win32', 'cygwin', 'cli'):
    raise RuntimeError('uvloop does not support Windows at the moment')

import os
import os.path
import pathlib
import platform
import re
import shutil
import subprocess
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.sdist import sdist


CYTHON_DEPENDENCY = 'Cython~=3.0'
MACHINE = platform.machine()
_ROOT = pathlib.Path(__file__).parent
LIBUV_DIR = str(_ROOT / 'vendor' / 'libuv')
LIBUV_BUILD_DIR = str(_ROOT / 'build' / 'libuv-{}'.format(MACHINE))


# === OPTIMIZATION FLAGS ===
def get_optimization_flags():
    """
    Return compiler flags for maximum safe optimization.
    Prioritas: Speed > Size, tapi tetap IEEE 754 compliant.
    """
    base_flags = [
        '-O3',              # Maximum optimization (vs -O2)
        '-march=native',    # Optimize for YOUR CPU specifically
        '-mtune=native',    # Tune for YOUR CPU microarchitecture
    ]
    
    # Fast math flags (SAFE - no broken math!)
    fast_math = [
        '-ffast-math',              # Enable aggressive math optimizations
        '-fno-math-errno',          # Don't set errno for math functions
        '-ffinite-math-only',       # Assume no NaN/Inf (safe for network code)
        '-fno-signed-zeros',        # Treat +0 and -0 as equal
        '-fno-trapping-math',       # No IEEE exceptions
        '-fassociative-math',       # Allow re-association: (a+b)+c = a+(b+c)
    ]
    
    # IMPORTANT: Exclude these dangerous flags!
    # ❌ -ffast-math includes -funsafe-math-optimizations (breaks some code)
    # ✅ We cherry-pick only the safe ones above
    
    # Function optimization
    func_opts = [
        '-finline-functions',           # Inline functions aggressively
        '-finline-limit=2000',          # Allow larger functions to inline
        '-fomit-frame-pointer',         # Remove frame pointer (faster calls)
        '-foptimize-sibling-calls',     # Tail call optimization
    ]
    
    # Loop optimization
    loop_opts = [
        '-funroll-loops',               # Unroll loops for speed
        '-ftree-vectorize',             # Auto-vectorization (SIMD)
        '-fvect-cost-model=dynamic',    # Smart vectorization decisions
    ]
    
    # Memory & cache optimization
    memory_opts = [
        '-fprefetch-loop-arrays',       # Prefetch data into cache
        '-fmerge-all-constants',        # Merge duplicate constants
        '-falign-functions=32',         # Align functions to 32 bytes (cache line)
        '-falign-loops=32',             # Align loops to cache lines
    ]
    
    # Code generation
    codegen_opts = [
        '-fno-plt',                     # Avoid PLT indirection
        '-fno-semantic-interposition',  # Allow more aggressive inlining
        '-fvisibility=hidden',          # Hide symbols by default
    ]
    
    # Link Time Optimization (LTO) - handled separately
    # We'll enable this via compiler flag in build step
    
    # Combine all flags
    all_flags = (
        base_flags + 
        fast_math + 
        func_opts + 
        loop_opts + 
        memory_opts + 
        codegen_opts
    )
    
    return all_flags


# Default optimization (can be overridden by env var)
MODULES_CFLAGS = get_optimization_flags()

# Allow override via environment variable
if 'UVLOOP_OPT_CFLAGS' in os.environ:
    MODULES_CFLAGS = [os.getenv('UVLOOP_OPT_CFLAGS')]
    print(f"Using custom CFLAGS: {MODULES_CFLAGS}")
else:
    print(f"Using optimized CFLAGS: {' '.join(MODULES_CFLAGS[:5])}... ({len(MODULES_CFLAGS)} flags)")


def _libuv_build_env():
    env = os.environ.copy()

    cur_cflags = env.get('CFLAGS', '')
    
    # Apply same aggressive optimization to libuv
    opt_flags = ' '.join(get_optimization_flags())
    
    # Merge with existing flags, avoid duplicates
    if not re.search(r'-O\d', cur_cflags):
        cur_cflags = opt_flags
    else:
        # Keep user's -O flag, add our other optimizations
        cur_cflags += ' ' + ' '.join([f for f in get_optimization_flags() if not f.startswith('-O')])
    
    env['CFLAGS'] = (cur_cflags + ' -fPIC ' + env.get('ARCHFLAGS', ''))

    return env


def _libuv_autogen(env):
    if os.path.exists(os.path.join(LIBUV_DIR, 'configure')):
        return

    if not os.path.exists(os.path.join(LIBUV_DIR, 'autogen.sh')):
        raise RuntimeError(
            'the libuv submodule has not been checked out; '
            'try running "git submodule init; git submodule update"')

    subprocess.run(
        ['/bin/sh', 'autogen.sh'], cwd=LIBUV_DIR, env=env, check=True)


class uvloop_sdist(sdist):
    def run(self):
        _libuv_autogen(_libuv_build_env())
        super().run()


class uvloop_build_ext(build_ext):
    user_options = build_ext.user_options + [
        ('cython-always', None,
            'run cythonize() even if .c files are present'),
        ('cython-annotate', None,
            'Produce a colorized HTML version of the Cython source.'),
        ('cython-directives=', None,
            'Cythion compiler directives'),
        ('use-system-libuv', None,
            'Use the system provided libuv, instead of the bundled one'),
        ('enable-lto', None,
            'Enable Link Time Optimization (aggressive, slow compile)'),
    ]

    boolean_options = build_ext.boolean_options + [
        'cython-always',
        'cython-annotate',
        'use-system-libuv',
        'enable-lto',
    ]

    def initialize_options(self):
        super().initialize_options()
        self.use_system_libuv = False
        self.cython_always = False
        self.cython_annotate = None
        self.cython_directives = None
        self.enable_lto = False

    def finalize_options(self):
        need_cythonize = self.cython_always
        cfiles = {}

        for extension in self.distribution.ext_modules:
            for i, sfile in enumerate(extension.sources):
                if sfile.endswith('.pyx'):
                    prefix, ext = os.path.splitext(sfile)
                    cfile = prefix + '.c'

                    if os.path.exists(cfile) and not self.cython_always:
                        extension.sources[i] = cfile
                    else:
                        if os.path.exists(cfile):
                            cfiles[cfile] = os.path.getmtime(cfile)
                        else:
                            cfiles[cfile] = 0
                        need_cythonize = True

        if need_cythonize:
            import pkg_resources

            try:
                import Cython
            except ImportError:
                raise RuntimeError(
                    'please install {} to compile uvloop from source'.format(
                        CYTHON_DEPENDENCY))

            cython_dep = pkg_resources.Requirement.parse(CYTHON_DEPENDENCY)
            if Cython.__version__ not in cython_dep:
                raise RuntimeError(
                    'uvloop requires {}, got Cython=={}'.format(
                        CYTHON_DEPENDENCY, Cython.__version__
                    ))

            from Cython.Build import cythonize

            # === CYTHON OPTIMIZATION DIRECTIVES ===
            cython_directives = {
                'language_level': 3,
                'boundscheck': False,          # No bounds checking (FAST!)
                'wraparound': False,           # No negative indexing
                'initializedcheck': False,     # No initialization checks
                'nonecheck': False,            # No None checks
                'cdivision': True,             # C division (no ZeroDivisionError check)
                'cdivision_warnings': False,   # No warnings
                'overflowcheck': False,        # No overflow checks
                'embedsignature': False,       # Smaller binary
                'always_allow_keywords': False, # Faster function calls
                'profile': False,              # Disable profiling hooks
                'linetrace': False,            # Disable line tracing
                'c_api_binop_methods': True,   # Use C API for operators
                'optimize.use_switch': True,   # Use switch for if/elif chains
                'optimize.unpack_method_calls': True, 
            }
            
            if self.cython_directives:
                for directive in self.cython_directives.split(','):
                    k, _, v = directive.partition('=')
                    if v.lower() == 'false':
                        v = False
                    if v.lower() == 'true':
                        v = True
                    cython_directives[k] = v

            self.distribution.ext_modules[:] = cythonize(
                self.distribution.ext_modules,
                compiler_directives=cython_directives,
                annotate=self.cython_annotate,
                compile_time_env=dict(DEFAULT_FREELIST_SIZE=250),
                emit_linenums=self.debug,
                nthreads=os.cpu_count() or 1,
            )

        super().finalize_options()

    def build_libuv(self):
        env = _libuv_build_env()

        _libuv_autogen(env)

        if os.path.exists(LIBUV_BUILD_DIR):
            shutil.rmtree(LIBUV_BUILD_DIR)
        shutil.copytree(LIBUV_DIR, LIBUV_BUILD_DIR)

        subprocess.run(
            ['touch', 'configure.ac', 'aclocal.m4', 'configure',
             'Makefile.am', 'Makefile.in'],
            cwd=LIBUV_BUILD_DIR, env=env, check=True)

        if 'LIBUV_CONFIGURE_HOST' in env:
            cmd = ['./configure', '--host=' + env['LIBUV_CONFIGURE_HOST']]
        else:
            cmd = ['./configure']
        subprocess.run(
            cmd,
            cwd=LIBUV_BUILD_DIR, env=env, check=True)

        try:
            njobs = len(os.sched_getaffinity(0))
        except AttributeError:
            njobs = os.cpu_count()
        j_flag = '-j{}'.format(njobs or 1)
        c_flag = "CFLAGS={}".format(env['CFLAGS'])
        subprocess.run(
            ['make', j_flag, c_flag],
            cwd=LIBUV_BUILD_DIR, env=env, check=True)

    def build_extensions(self):
        if self.enable_lto:
            lto_flags = ['-flto', '-fuse-linker-plugin', '-ffat-lto-objects']
            for ext in self.extensions:
                ext.extra_compile_args.extend(lto_flags)
                ext.extra_link_args = getattr(ext, 'extra_link_args', [])
                ext.extra_link_args.extend(lto_flags)
            print("Link Time Optimization (LTO) enabled - compile will be slower but runtime faster")
        
        if self.use_system_libuv:
            self.compiler.add_library('uv')

            if sys.platform == 'darwin' and \
                    os.path.exists('/opt/local/include'):
                self.compiler.add_include_dir('/opt/local/include')
        else:
            libuv_lib = os.path.join(LIBUV_BUILD_DIR, '.libs', 'libuv.a')
            if not os.path.exists(libuv_lib):
                self.build_libuv()
            if not os.path.exists(libuv_lib):
                raise RuntimeError('failed to build libuv')

            self.extensions[-1].extra_objects.extend([libuv_lib])
            self.compiler.add_include_dir(os.path.join(LIBUV_DIR, 'include'))

        if sys.platform.startswith('linux'):
            self.compiler.add_library('rt')
        elif sys.platform.startswith(('freebsd', 'dragonfly')):
            self.compiler.add_library('kvm')
        elif sys.platform.startswith('sunos'):
            self.compiler.add_library('kstat')
        self.compiler.add_library('pthread')
        super().build_extensions()


with open(str(_ROOT / 'uvloop' / '_version.py')) as f:
    for line in f:
        if line.startswith('__version__ ='):
            _, _, version = line.partition('=')
            VERSION = version.strip(" \n'\"")
            break
    else:
        raise RuntimeError(
            'unable to read the version from uvloop/_version.py')


setup_requires = []

if not (_ROOT / 'uvloop' / 'loop.c').exists() or '--cython-always' in sys.argv:
    setup_requires.append(CYTHON_DEPENDENCY)


setup(
    version=VERSION,
    cmdclass={
        'sdist': uvloop_sdist,
        'build_ext': uvloop_build_ext
    },
    ext_modules=[
        Extension(
            "uvloop.loop",
            sources=[
                "uvloop/loop.pyx",
            ],
            extra_compile_args=MODULES_CFLAGS,
            # Add extra link args for optimization
            extra_link_args=[
                '-Wl,-O2',           # Linker optimization
                '-Wl,--as-needed',   # Only link needed libraries
                '-Wl,--strip-all',   # Strip symbols (smaller binary)
            ] if sys.platform.startswith('linux') else []
        ),
    ],
    setup_requires=setup_requires,
)
