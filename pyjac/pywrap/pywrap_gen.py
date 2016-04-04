from ..libgen import generate_library
import sys
import os
import subprocess
from string import Template

def generate_setup(setupfile, home_dir, build_dir, out_dir, libname):
    """
    Helper method to fill in the template .in files
    """
    with open(setupfile, 'r') as file:
        src = Template(file.read())
    file_data = {'homepath' : home_dir,
                 'buildpath' : build_dir,
                 'libname' : libname,
                 'outpath' : out_dir}
    src = src.safe_substitute(file_data)
    with open(setupfile[:setupfile.rindex('.in')], 'w') as file:
        file.write(src)

def generate_wrapper(lang, source_dir, out_dir=None, auto_diff=False):
    """
    Generates a python wrapper for the given language and source files
    """

    #import pdb
    #pdb.set_trace()

    source_dir = os.path.normpath(source_dir)
    home_dir = os.path.abspath(os.path.dirname(__file__))

    if out_dir is None:
        out_dir = os.getcwd()

    shared = False
    ext = '.so' if shared else '.a'
    if lang != 'tchem':
        #first generate the library
        lib = generate_library(lang, source_dir, out_dir=out_dir, shared=shared,
                    finite_difference=auto_diff)
        lib = os.path.normpath(lib)
        if shared:
            lib = lib[lib.index('lib') + len('lib'):lib.index(ext)]

    setupfile = None
    if lang == 'c':
        setupfile = 'pyjacob_setup.py.in'
        if auto_diff:
            setupfile = 'adjacob_setup.py.in'
    elif lang == 'cuda':
        setupfile = 'pyjacob_cuda_setup.py.in'
    elif lang == 'tchem':
        setupfile = 'pytchem_setup.py.in'
    else:
        print('Language {} not recognized'.format(lang))
        sys.exit(-1)

    generate_setup(os.path.join(home_dir, setupfile), home_dir, source_dir,
                        out_dir, lib)
    subprocess.check_call(['python2.7', os.path.join(home_dir, 
                        setupfile[:setupfile.index('.in')]), 
                       'build_ext', '--build-lib', out_dir
                       ])

