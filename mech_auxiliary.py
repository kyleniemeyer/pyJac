"""Writes mechanism header and output testing files"""

# Python 2 compatibility
from __future__ import division
from __future__ import print_function

# Standard libraries
import sys
import math
import itertools

# Local imports
import chem_utilities as chem
import utils
import CUDAParams


def __write_kernels(file, have_rev_rxns, have_pdep_rxns):
    """
    Writes kernels that simply act as shells to call the various reaction/species/jacobian
    """
    if not CUDAParams.is_global():
        if have_rev_rxns:
            file.write('#ifdef PROFILER\n'
                       '__global__ void k_eval_rxn_rates(const double T) {\n'
                       '    double conc_local[NSP] = {[0 ... NSP - 1] = 1.0};\n'
                       '    double fwd_rates_local[FWD_RATES];\n'
                       '    double rev_rates_local[REV_RATES];\n'
                       '    eval_rxn_rates(T, conc_local, fwd_rates_local, rev_rates_local);\n'
                       '}\n'
                       '#elif RATES_TEST\n'
                       '__global__ void k_eval_rxn_rates(const int NUM, const double T, const double* conc, double* fwd_rates, double* rev_rates) {\n'
                       '    double conc_local[NSP];\n'
                       '    double fwd_rates_local[FWD_RATES];\n'
                       '    double rev_rates_local[REV_RATES];\n'
                       '    //copy in\n'
                       '    for (int i = 0; i < NSP; i++) {\n'
                       '        conc_local[i] = conc[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                       '    eval_rxn_rates(T, conc_local, fwd_rates_local, rev_rates_local);\n'
                       '    //copy back\n'
                       '    for (int i = 0; i < FWD_RATES; i++) {\n'
                       '        fwd_rates[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = fwd_rates_local[i];\n'
                       '    }\n'
                       '    for (int i = 0; i < REV_RATES; i++) {\n'
                       '        rev_rates[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = rev_rates_local[i];\n'
                       '    }\n'
                       '}\n'
                       '#endif\n'
                       )
        else:
            file.write('#ifdef PROFILER\n'
                       '__global__ void k_eval_rxn_rates(const double T) {\n'
                       '    double conc_local[NSP] = {[0 ... NSP - 1] = 1.0};\n'
                       '    double rates_local[RATES];\n'
                       '    eval_rxn_rates(T, conc_local, rates_local);\n'
                       '}\n'
                       '#elif RATES_TEST\n'
                       '__global__ void k_eval_rxn_rates(const int NUM, const double T, const double* conc, double* rates) {\n'
                       '    double conc_local[NSP];\n'
                       '    double rates_local[RATES];\n'
                       '    //copy in\n'
                       '    for (int i = 0; i < NSP; i++) {\n'
                       '        conc_local[i] = conc[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                       '    eval_rxn_rates(T, conc_local, rates_local);\n'
                       '    //copy back\n'
                       '    for (int i = 0; i < RATES; i++) {\n'
                       '        rates[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = rates_local[i];\n'
                       '    }\n'
                       '}\n'
                       '#endif\n'
                       )
        if have_pdep_rxns:
            file.write('#ifdef PROFILER\n'
                       '__global__ void k_get_rxn_pres_mod(const double T, const double P) {\n'
                       '    double conc_local[NSP] = {[0 ... NSP - 1] = 1.0};\n'
                       '    double pres_mod_local[PRES_MOD_RATES];\n'
                       '    get_rxn_pres_mod(T, P, conc_local, pres_mod_local);\n'
                       '}\n'
                       '#elif RATES_TEST\n'
                       '__global__ void k_get_rxn_pres_mod(const int NUM, const double T, const double P, double* conc, double* pres_mod) {'
                       '    double conc_local[NSP];\n'
                       '    double pres_mod_local[PRES_MOD_RATES];\n'
                       '    //copy in\n'
                       '    for (int i = 0; i < NSP; i++) {\n'
                       '        conc_local[i] = conc[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                       '    get_rxn_pres_mod(T, P, conc_local, pres_mod_local);\n'
                       '    //copy back\n'
                       '    for (int i = 0; i < PRES_MOD_RATES; i++) {\n'
                       '        pres_mod[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = pres_mod_local[i];\n'
                       '    }\n'
                       '}\n'
                       '#endif\n'
                       )
        file.write('#ifdef PROFILER\n'
                   '__global__ void k_eval_spec_rates() {\n'
                   )
        if have_rev_rxns:
            file.write('    double fwd_rates_local[FWD_RATES] = {[0 ... FWD_RATES - 1] = 1.0};\n'
                       '    double rev_rates_local[REV_RATES] = {[0 ... REV_RATES - 1] = 1.0};\n'
                       )
        else:
            file.write('    double rates_local[RATES] = {[0 ... RATES - 1] = 1.0};\n')
        if have_pdep_rxns:
            file.write('    double pres_mod_local[PRES_MOD_RATES] = {[0 ... PRES_MOD_RATES - 1] = 1.0};\n' if have_pdep_rxns else '')
        file.write(
                   '    double dy_local[NN];\n'
                   '    eval_spec_rates('
                   )
        if have_rev_rxns:
            file.write('fwd_rates_local, rev_rates_local, ')
        else:
            file.write('rates_local, ')
        if have_pdep_rxns:
            file.write('pres_mod_local, ')
        file.write('dy_local);\n')
        file.write('}\n'
                   '#elif RATES_TEST\n'
                   '__global__ void k_eval_spec_rates(const int NUM, '
                  )
        if have_rev_rxns:
            file.write('const double* fwd_rates, const double* rev_rates, ')
        else:
            file.write('const double* rates, ')
        if have_pdep_rxns:
            file.write('const double* pres_mod, ')
        file.write('double* dy) {\n')
        file.write('    //copy in\n')
        if have_rev_rxns:
            file.write('    double fwd_rates_local[FWD_RATES];\n'
                       '    double rev_rates_local[REV_RATES];\n'
                       )
        else:
            file.write('    double rates_local[RATES];\n')
        if have_pdep_rxns:
            file.write('    double pres_mod_local[PRES_MOD_RATES];\n' if have_pdep_rxns else '')
        file.write('    double dy_local[NN];\n')
        if have_rev_rxns:
            file.write('    for (int i = 0; i < FWD_RATES; i++) {\n'
                       '        fwd_rates_local[i] = fwd_rates[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                       '    for (int i = 0; i < REV_RATES; i++) {\n'
                       '        rev_rates_local[i] = rev_rates[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                      )
        else:
            file.write('    for (int i = 0; i < RATES; i++) {\n'
                       '        rates_local[i] = rates[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                      )
        if have_pdep_rxns:
            file.write('    for (int i = 0; i < PRES_MOD_RATES; i++) {\n'
                       '        pres_mod_local[i] = pres_mod[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                       '    }\n'
                      )
        file.write('    eval_spec_rates(')
        if have_rev_rxns:
            file.write('fwd_rates_local, rev_rates_local, ')
        else:
            file.write('rates_local, ')
        if have_pdep_rxns:
            file.write('pres_mod_local, ')
        file.write('dy_local);\n')
        file.write(
                   '   //copy back\n'
                   '   for (int i = 0; i < NN; i++) {\n'
                   '        dy[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = dy_local[i];\n'
                   '    }\n'
                   '}\n'
                   )
        file.write('#endif\n')
        file.write('#ifdef PROFILER\n'
                   '__global__ void k_eval_dy(const double T, const double P) {\n'
                   '    double y_local[NN] = {T, [1 ... NN - 1] = 1.0 / NSP};\n'
                   '    double dy_local[NN];\n'
                   '    dydt(T, P, y_local, dy_local);\n'
                   '}\n'
                   '#elif RATES_TEST\n'
                   '__global__ void k_eval_dy(const int NUM, const double T, const double P, const double* y, double* dy) {\n'
                   '    double y_local[NN];\n'
                   '    double dy_local[NN];\n'
                   '    //copy in\n'
                   '    for (int i = 0; i < NN; i++) {\n'
                   '        y_local[i] = y[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                   '    }\n'
                   '    dydt(T, P, y_local, dy_local);\n'
                   '    //copy back\n'
                   '    for (int i = 0; i < NN; i++) {\n'
                   '        dy[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = dy_local[i];\n'
                   '    }\n'
                   '}\n'
                   '#endif\n'
                   )
        file.write('#ifdef PROFILER\n'
                   '__global__ void k_eval_jacob(const double T, const double P) {\n'
                   '    double y_local[NN] = {T, [1 ... NN - 1] = 1.0 / NSP};\n'
                   '    double jac_local[NN * NN];\n'
                   '    eval_jacob(0, P, y_local, jac_local);\n'
                   '}\n'
                   '#elif RATES_TEST\n'
                   '__global__ void k_eval_jacob(const int NUM, const double t, const double P, double* y, double* jac) {\n'
                   '    double y_local[NN];\n'
                   '    double jac_local[NN * NN] = {0.0};\n'
                   '    //copy in\n'
                   '    for (int i = 0; i < NN; i++) {\n'
                   '        y_local[i] = y[i * NUM + threadIdx.x + blockIdx.x * blockDim.x];\n'
                   '    }\n'
                   '    eval_jacob(0, P, y_local, jac_local);\n'
                   '    for (int i = 0; i < NN * NN; i++) {\n'
                   '        jac[i * NUM + threadIdx.x + blockIdx.x * blockDim.x] = jac_local[i];\n'
                   '    }\n'
                   '}\n'
                   '#endif\n'
                   )
        file.write('\n')
    else:
        if have_rev_rxns:
            file.write('__global__ void k_eval_rxn_rates(const double T) {\n'
                       '    eval_rxn_rates(T, memory_pointers.conc, memory_pointers.fwd_rates, memory_pointers.rev_rates);\n'
                       '}\n'
                       )
        else:
            file.write('__global__ void k_eval_rxn_rates(const double T) {\n'
                       '    eval_rxn_rates(T, memory_pointers.conc, memory_pointers.rates);\n'
                       '}\n'
                       )
        if have_pdep_rxns:
            file.write('__global__ void k_get_rxn_pres_mod(const double T, const double P) {\n'
                       '    get_rxn_pres_mod(T, P, memory_pointers.conc, memory_pointers.pres_mod);\n'
                       '}\n')
        file.write('__global__ void k_eval_spec_rates() {{\n'.format() +
                   '    eval_spec_rates({}{} memory_pointers.dy);\n'.format('memory_pointers.fwd_rates, memory_pointers.rev_rates,' if have_rev_rxns else 'memory_pointers.rates,',
                                                            ' memory_pointers.pres_mod,' if have_pdep_rxns else '') +
                   '}\n'
                   )
        file.write('__global__ void k_eval_dy(const double T, const double P) {\n'
                   '    dydt(T, P, memory_pointers.y, memory_pointers.dy);\n'
                   '}\n')
        file.write('__global__ void k_eval_jacob(const double t, const double P) {\n'
                   '    eval_jacob(t, P, memory_pointers.y, memory_pointers.jac);\n'
                   '}\n')
        file.write('\n')


def __write_c_rate_evaluator(file, have_rev_rxns, have_pdep_rxns, T, P, Pretty_P):
    file.write('    fprintf(fp, "{}K, {} atm\\n");\n'.format(T, Pretty_P) +
               '    y_host[0] = {};\n'.format(T) +
               '    get_concentrations({}, y_host, conc_host);\n'.format(P)
               )
    if have_rev_rxns:
        file.write(
            '    eval_rxn_rates({}, conc_host, fwd_rates_host, rev_rates_host);\n'.format(T))
    else:
        file.write(
            '    eval_rxn_rates({}, conc_host, rates_host);\n'.format(T))
    if have_pdep_rxns:
        file.write(
            '    get_rxn_pres_mod ({}, {}, conc_host, pres_mod_host);\n'.format(T, P))
    file.write('    eval_spec_rates ({}{} spec_rates_host);\n'.format('fwd_rates_host, rev_rates_host,' if have_rev_rxns else 'rates_host,', ' pres_mod_host,' if have_pdep_rxns else '') +
               '    dydt({}, {}, y_host, dy_host);\n'.format(T, P) +
               '    write_rates(fp,{}{} spec_rates_host, dy_host);\n'.format(' fwd_rates_host, rev_rates_host,' if have_rev_rxns else ' rates_host,', ' pres_mod_host,' if have_pdep_rxns else '') +
               '    eval_jacob(0, {}, y_host, jacob_host);\n'.format(P) +
               '    write_jacob(fp, jacob_host);\n'
               )


def __write_cuda_rate_evaluator(file, have_rev_rxns, have_pdep_rxns, T, P, Pretty_P):
    descriptor = 'd_' if not CUDAParams.is_global() else 'host_memory->'
    file.write('    fprintf(fp, "{}K, {} atm\\n");\n'.format(T, Pretty_P) +
               '    y_host[0] = {};\n'.format(T) +
               '    get_concentrations({}, y_host, conc_host);\n'.format(P))
    file.write('#ifdef CONV\n' + 
               '    double rho = getDensity({}, {}, Xi);\n'.format(T, P) +
               '#endif\n'
               '    for (int i = 0; i < padded; ++i) {\n'
               '        for (int j = 0; j < NSP; ++j) {\n'
               '            conc_host_full[i + j * padded] = conc_host[j];\n'
               '        }\n' + 
               '        y_host_full[i] = {};\n'.format(T) + 
               '#ifdef CONP\n' + 
               '        pres_host_full[i] = {};\n'.format(P) + 
               '#elif CONV\n'
               '        rho_host_full[i] = rho;\n'
               '#endif\n'
               '    }\n'
               )
    file.write(
    '    cudaErrorCheck(cudaMemcpy({}conc, conc_host_full, padded * NSP * sizeof(double), cudaMemcpyHostToDevice));\n'.format(descriptor))
    if have_rev_rxns:
        file.write('#ifdef PROFILER\n'
                   '    cuProfilerStart();\n'
                   '    k_eval_rxn_rates<<<grid_size, block_size>>>({});\n'.format(T) + 
                   '    cuProfilerStop();\n'
                   '#elif RATES_TEST\n'
                   '    k_eval_rxn_rates<<<grid_size, block_size>>>(padded, {}{});\n'.format(T, ', {0}conc, {0}fwd_rates, {0}rev_rates'.format(descriptor) if not CUDAParams.is_global() else '')
                   )
        file.write(
               '    cudaErrorCheck(cudaMemcpy(fwd_rates_host_full, {}fwd_rates, padded * FWD_RATES * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor) + 
               '    cudaErrorCheck(cudaMemcpy(rev_rates_host_full, {}rev_rates, padded * REV_RATES * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor)
               )
        file.write('    for (int j = 0; j < FWD_RATES; ++j) {\n'
                   '            fwd_rates_host[j] = fwd_rates_host_full[j * padded];\n'
                   '    }\n'
                   )
        file.write('    for (int j = 0; j < REV_RATES; ++j) {\n'
                   '        rev_rates_host[j] = rev_rates_host_full[j * padded];\n'
                   '    }\n'
                   '#endif\n'
                   )
    else:
        file.write(
            '#ifdef PROFILER\n'
            '    cuProfilerStart();\n'
            '    k_eval_rxn_rates<<<grid_size, block_size>>>({});\n'.format(T) +
            '    cuProfilerStop();\n'
            '#elif RATES_TEST\n'
            '    k_eval_rxn_rates<<<grid_size, block_size>>>(padded, {}{});\n'.format(T, ', {0}conc, {0}rates'.format(descriptor) if not CUDAParams.is_global() else '')
            )
        file.write(
        '    cudaErrorCheck(cudaMemcpy(rates_host_full, {}rates, padded * RATES * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor))

        file.write('    for (int j = 0; j < RATES; ++j) {\n'
                   '        rates_host[j] = rates_host_full[j * padded];\n'
                   '    }\n'
                   '#endif\n'
                   )
    if have_pdep_rxns:
        file.write(
            '#ifdef PROFILER\n'
            '    cuProfilerStart();\n'
            '    k_get_rxn_pres_mod<<<grid_size, block_size>>>({}, {});\n'.format(T, P) +
            '    cuProfilerStop();\n'
            '#elif RATES_TEST\n'
            '    k_get_rxn_pres_mod<<<grid_size, block_size>>>(padded, {}, {}{});\n'.format(T, P, ', {0}conc, {0}pres_mod'.format(descriptor) if not CUDAParams.is_global() else '')
            )
        file.write(
        '    cudaErrorCheck(cudaMemcpy(pres_mod_host_full, {}pres_mod, padded * PRES_MOD_RATES * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor)
        )
        file.write('    for (int j = 0; j < PRES_MOD_RATES; ++j) {\n'
                   '        pres_mod_host[j] = pres_mod_host_full[j * padded];\n'
                   '    }\n'
            '#endif\n'
                   )

    if have_rev_rxns:
        file.write('#ifdef PROFILER\n'
                   '    cuProfilerStart();\n'
                   '    k_eval_spec_rates<<<grid_size, block_size>>>();\n'
                   '    cuProfilerStop();\n'
                   '#elif RATES_TEST\n'
                   '    k_eval_spec_rates<<<grid_size, block_size>>>(padded, {});\n'.format(('{0}fwd_rates, {0}rev_rates' + (', {0}pres_mod' if have_pdep_rxns else '') + \
                        ', {0}spec_rates').format(descriptor) if not CUDAParams.is_global() else '')
                   )
    else:
        file.write(
            '#ifdef PROFILER\n'
            '    cuProfilerStart();\n'
            '    k_eval_spec_rates<<<grid_size, block_size>>>({});\n'
            '    cuProfilerStop();\n'
            '#elif RATES_TEST\n'
            '    k_eval_spec_rates<<<grid_size, block_size>>>(padded, {});\n'.format(('{0}rates' + (', {0}pres_mod' if have_pdep_rxns else '') + 
                ', {0}spec_rates').format(descriptor))
            )
    file.write(
           '    cudaErrorCheck(cudaMemcpy(spec_rates_host_full, {}spec_rates, padded * NSP * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor))
    file.write(
               '    for (int j = 0; j < NSP; ++j) {\n'
               '        spec_rates_host[j] = spec_rates_host_full[j * padded];\n'
               '    }\n'
               '#endif\n'
               )
    file.write('#ifdef PROFILER\n'
                '    cuProfilerStart();\n'
                '    k_eval_dy<<<grid_size, block_size>>>({}, {});\n'.format(T, P) + 
                '    cuProfilerStop();\n'
                '#elif RATES_TEST\n'
                '    cudaErrorCheck(cudaMemcpy({}y, y_host_full, padded * NN * sizeof(double), cudaMemcpyHostToDevice));\n'.format(descriptor) +
                '    k_eval_dy<<<grid_size, block_size>>>(padded, {}, {}, {});\n'.format(T, P, ('{0}y' + (', {0}dy' if have_pdep_rxns else '')).format(descriptor) if not CUDAParams.is_global()
                     else '')
                )
    file.write('    cudaErrorCheck(cudaMemcpy(dy_host_full, {}dy, padded * NN * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor))
    file.write(
               '    for (int j = 0; j < NN; ++j) {\n'
               '        dy_host[j] = dy_host_full[j * padded];\n'
               '    }\n'
               '#endif\n'
               )
    file.write('#ifdef RATES_TEST\n'
               '    write_rates(fp,{}{} spec_rates_host, dy_host);\n'.format(' fwd_rates_host, rev_rates_host,' if have_rev_rxns else ' rates_host,', ' pres_mod_host,' if have_pdep_rxns else '') + 
               '#endif\n'
               )
    file.write(
           '#ifdef CONP\n'
           '    cudaErrorCheck(cudaMemcpy({}pres, pres_host_full, padded * sizeof(double), cudaMemcpyHostToDevice));\n'.format(descriptor) +
           '#elif CONV\n'
           '    cudaErrorCheck(cudaMemcpy({}rho, rho_host_full, padded * sizeof(double), cudaMemcpyHostToDevice));\n'.format(descriptor) +
           '#endif\n'
           )
    file.write(
               '#ifdef PROFILER\n'
               '    cuProfilerStart();\n'
               '    k_eval_jacob<<<grid_size, block_size>>>({}, {});\n'.format(T, P) + 
               '    cuProfilerStop();\n'
               '#elif RATES_TEST\n'
               '    k_eval_jacob<<<grid_size, block_size>>>(padded, 0, {}{});\n'.format(P, ', {0}y, {0}jac'.format(descriptor) if not CUDAParams.is_global() else '') + 
               '    cudaErrorCheck(cudaMemcpy(jacob_host_full, {}jac, padded * NN * NN * sizeof(double), cudaMemcpyDeviceToHost));\n'.format(descriptor) + 
               '    for (int j = 0; j < NN * NN; ++j) {\n'
               '        jacob_host[j] = jacob_host_full[j * padded];\n'
               '    }\n'
               '    write_jacob(fp, jacob_host);\n'
               '#endif\n'
               )


def write_mechanism_initializers(path, lang, specs, reacs, initial_moles):
    if lang in ['matlab', 'fortran']:
        raise NotImplementedError

    # some information variables
    have_rev_rxns = any(reac.rev for reac in reacs)
    have_pdep_rxns = any(reac.thd or reac.pdep for reac in reacs)

    # the mechanism header defines a number of useful preprocessor defines, as
    # well as defining method stubs for setting initial conditions
    with open(path + 'mechanism.{}h'.format('cu' if lang == 'cuda' else ''), 'w') as file:

        file.write('#ifndef MECHANISM_{}H\n'.format('cu' if lang == 'cuda' else '') +
                   '#define MECHANISM_{}H\n\n'.format('cu' if lang == 'cuda' else ''))

        # convience: write species indexes
        file.write('/* Species Indexes\n')
        file.write('\n'.join('{}  {}'.format(i, spec.name)
                             for i, spec in enumerate(specs)))
        file.write('*/\n\n')

        # defines
        if lang == 'cuda' and CUDAParams.is_global():
            file.write('//Global Memory\n'
                       '#define GLOBAL_MEM\n')
        file.write("//Number of species\n")
        file.write('#define NSP {}\n'.format(len(specs)))
        file.write("//Number of variables. NN = NSP + 1 (temperature)\n")
        file.write('#define NN {}\n'.format(len(specs) + 1))
        if have_rev_rxns:
            file.write('//Number of forward reactions\n')
            file.write('#define FWD_RATES {}\n'.format(len(reacs)))
            file.write('//Number of reversible reactions\n')
            file.write('#define REV_RATES {}\n'.format(
                len([reac for reac in reacs if reac.rev])))
        else:
            file.write('//Number of reactions\n'
                       '#define RATES {}\n'.format(len(reac)))
        if have_pdep_rxns:
            file.write('//Number of reactions with pressure modified rates\n')
            file.write('#define PRES_MOD_RATES {}\n\n'.format(
                len([reac for reac in reacs if reac.pdep or reac.thd])))

        if lang == 'cuda':
            file.write('#ifdef __cplusplus\n'
                       'extern "C" {\n'
                       '#endif\n')
        file.write('    //Must be implemented by user on a per mechanism basis in mechanism.c\n'
               '    {} set_same_initial_conditions(int NUM,{} double**, double**);\n'.format(
                    'int' if lang == 'cuda' else 'void', ' int, int, double**, double**, ' if lang == 'cuda' else '')
                   )
        file.write('    #if defined (RATES_TEST) || defined (PROFILER)\n')
        if lang == 'c':
            file.write('    void write_jacobian_and_rates_output();\n')
        else:
            file.write('    void write_jacobian_and_rates_output(int NUM, int block_size, int grid_size);\n')
        file.write('#endif\n')

        if lang == 'cuda':
            # close previous extern
            file.write('#ifdef __cplusplus\n'
                       '}\n'
                       '#endif\n\n')

        file.write('#endif\n\n')

    # now the mechanism file
    with open(path + 'mechanism.c{}'.format('u' if lang == 'cuda' else ''), 'w') as file:
        file.write('#include <stdio.h>\n'
                   '#include "mass_mole.h"\n'
                   '#include "mechanism.{}h"\n'.format('cu' if lang == 'cuda' else '') +
                   '#if defined (RATES_TEST) || defined (PROFILER)\n'
                   '    #include "rates.{}h"\n'.format('cu' if lang == 'cuda' else '') +
                   '    #include "jacob.{}h"\n'.format('cu' if lang == 'cuda' else '') +
                   '    #include "dydt.{}h"\n'.format('cu' if lang == 'cuda' else '') +
                   '#endif\n')
        if lang == 'cuda':
            file.write('#include <cuda.h>\n'
                       '#include <cuda_runtime.h>\n'
                       '#include <helper_cuda.h>\n'
                       )
            file.write('#ifdef PROFILER\n'
                       '    #include "cuda_profiler_api.h"\n'
                       '    #include "cudaProfiler.h"\n'
                       '#endif\n')

            file.write('#include "gpu_macros.cuh"\n')
            file.write('#include "gpu_memory.cuh"\n')
            if CUDAParams.is_global():
                file.write('\nextern __constant__ gpuMemory memory_pointers;\n\n')
            __write_kernels(file, have_rev_rxns, have_pdep_rxns)

        needed_arr = ['y', 'pres']
        needed_arr_conv = ['y', 'rho']
        if lang == 'cuda':
            if CUDAParams.is_global():
                needed_arr = ['double** ' + a + '_host' for a in needed_arr]
                needed_arr_conv = [
                    'double** ' + a + '_host' for a in needed_arr_conv]
            else:
                needed_arr = [['double** ' + a + '_host', 'double** d_' + a]
                              for a in needed_arr]
                needed_arr = [a for a in itertools.chain(*needed_arr)]
                needed_arr_conv = [
                    ['double** ' + a + '_host', 'double** d_' + a] for a in needed_arr_conv]
                needed_arr_conv = [a for a in itertools.chain(*needed_arr_conv)]
        else:
            needed_arr = ['double** ' + a + '_host' for a in needed_arr]
            needed_arr_conv = ['double** ' + a + '_host' for a in needed_arr_conv]
        file.write('#ifdef CONP\n'
                   '{} set_same_initial_conditions(int NUM{}, {}) \n'.format('int' if lang == 'cuda' else 'void',
                                                                             ', int block_size, int grid_size' if lang == 'cuda' else '', ', '.join(needed_arr)) +
                   '#elif CONV\n'
                   '{} set_same_initial_conditions(int NUM{}, {}) \n'.format('int' if lang == 'cuda' else 'void',
                                                                             ', int block_size, int grid_size' if lang == 'cuda' else '', ', '.join(needed_arr_conv)) +
                   '#endif\n'
                   )
        file.write('{\n')
        if lang == 'cuda':
            if CUDAParams.is_global():
                file.write('gpuMemory* host_memory = NULL;\n'
                           'int padded = initialize_gpu_memory(NUM, block_size, grid_size, &host_memory);\n')
            else:
                # do cuda mem init and copying
                file.write(
                    '#ifdef CONP\n'
                    '    int padded = initialize_gpu_memory(NUM, block_size, grid_size, d_y, d_pres);\n'
                    '#elif CONV\n'
                    '    int padded = initialize_gpu_memory(NUM, block_size, grid_size, d_y, d_rho);\n'
                    '#endif\n'
                    )
        else:
            file.write('    int padded = NUM;\n')
        file.write('    double Xi [NSP] = {0.0};\n'
                   '    //set initial mole fractions here\n\n'
                   '    //Normalize mole fractions to sum to one\n'
                   '    double Xsum = 0.0;\n'
                   )
        mole_list = []
        if initial_moles != "":
            try:
                mole_list = [x.strip() for x in initial_moles.split(",")]
            except:
                print("Error in initial mole list, not comma separated")
                sys.exit(1)
            try:
                mole_list = [x.split("=") for x in mole_list]
            except:
                print("Error in initial mole list, initial moles do not follow SPECIES_NAME=VALUE format")
                sys.exit(1)
            try:
                mole_list = [(split[0], float(split[1])) for split in mole_list]
            except:
                print("Unknown (non-float) value found as initial mole number in list")
                sys.exit(1)
            try:
                mole_list = [(next(i for i, spec in enumerate(specs) if spec.name == split[0]), split[1]) for split in mole_list]
            except:
                print("Unknown species in initial mole list")
                sys.exit(1)
        for x in mole_list:
            file.write('    Xi[{}] = {}'.format(x[0], x[1]) + utils.line_end[lang])
        file.write(
                   '    for (int j = 0; j < NSP; ++ j) {\n'
                   '        Xsum += Xi[j];\n'
                   '    }\n'
                   '    if (Xsum == 0.0) {\n'
                   '        printf("Use of the set initial conditions function requires user implementation!");\n'
                   '        exit(-1);\n'
                   '    }\n'
                   '    for (int j = 0; j < NSP; ++ j) {\n'
                   '        Xi[j] /= Xsum;\n'
                   '    }\n\n'
                   '    //convert to mass fractions\n'
                   '    double Yi[NSP] = {0.0};\n'
                   '    mole2mass(Xi, Yi);\n\n'
                   '    //set initial pressure, units [dyn/cm^2]\n'
                   '    double P = 1.01325e6;\n'
                   '    // set intial temperature, units [K]\n'
                   '    double T0 = 1600;\n\n'
                   '    *y_host = (double*)malloc(padded * NN * sizeof(double));\n'
                   '#ifdef CONP\n'
                   '    *pres_host = (double*)malloc(padded * sizeof(double));\n'
                   '#elif defined(CONV)\n'
                   '    *rho_host = (double*)malloc(padded * sizeof(double));\n'
                   '#endif\n'
                   '    //load temperature and mass fractions for all threads (cells)\n'
                   '    for (int i = 0; i < padded; ++i) {\n'
                   '        (*y_host)[i] = T0;\n'
                   '        //loop through species\n'
                   '        for (int j = 1; j < NN; ++j) {\n'
                   '            (*y_host)[i + NUM * j] = Yi[j - 1];\n'
                   '        }\n'
                   '    }\n\n'
                   '#ifdef CONV\n'
                   '    //calculate density\n'
                   '    double rho = getDensity(T0, P, Xi);\n'
                   '#endif\n\n'
                   '    for (int i = 0; i < padded; ++i) {\n'
                   '#ifdef CONV\n'
                   '        (*rho_host)[i] = rho;\n'
                   '#elif defined(CONP)\n'
                   '        (*pres_host)[i] = P;\n'
                   '#endif\n'
                   '    }\n'
                   )
        if lang == 'cuda':  # copy memory over
            if CUDAParams.is_global():
                file.write('    cudaErrorCheck(cudaMemcpy(host_memory->y, y_host, padded * NN * sizeof(double), cudaMemcpyHostToDevice));\n'
                           '#ifdef CONP\n'
                           '    cudaErrorCheck(cudaMemcpy(host_memory->pres, pres_host, padded * sizeof(double), cudaMemcpyHostToDevice));\n'
                           '#elif CONV\n'
                           '    cudaErrorCheck(cudaMemcpy(host_memory->rho, rho_host, padded * sizeof(double), cudaMemcpyHostToDevice));\n' 
                           '#endif\n')
            else:
                file.write('    cudaErrorCheck(cudaMemcpy(*d_y, *y_host, padded * NN * sizeof(double), cudaMemcpyHostToDevice));\n'
                           '#ifdef CONP\n'
                           '    cudaErrorCheck(cudaMemcpy(*d_pres, *pres_host, padded * sizeof(double), cudaMemcpyHostToDevice));\n'
                           '#elif CONV\n'
                           '    cudaErrorCheck(cudaMemcpy(*d_rho, *rho_host, padded * sizeof(double), cudaMemcpyHostToDevice));\n'
                           '#endif\n')
            file.write('    return padded;\n')

        file.write('}\n\n')
        file.write('#if defined (RATES_TEST) || defined (PROFILER)\n')
        # write utility function that finds concentrations at a given state
        file.write('void get_concentrations(double P, const double* y_host, double* conc_host) {\n'
                   '    double rho;\n'
                   )

        line = '    rho = '
        isfirst = True
        for sp in specs:
            if len(line) > 70:
                line += '\n'
                file.write(line)
                line = '         '

            if not isfirst:
                line += ' + '
            line += '(y_host[{}] / {})'.format(specs.index(sp) + 1, sp.mw)
            isfirst = False

        line += ';\n'
        file.write(line)
        line = '    rho = P / ({:.8e} * y_host[0] * rho);\n\n'.format(chem.RU)
        file.write(line)

        # calculation of species molar concentrations
        file.write('    // species molar concentrations\n')
        # loop through species
        for sp in specs:
            isp = specs.index(sp)
            line = '    conc_host[{}] = rho * y_host[{}] / '.format(isp, isp + 1)
            line += '{}'.format(sp.mw) + utils.line_end[lang]
            file.write(line)

        file.write('}\n\n')

        line = 'void write_rates(FILE* fp, '
        if have_rev_rxns:
            line += ' const double* fwd_rates_host'
            line += ', const double* rev_rates_host'
        else:
            line += ' const double* rates'
        if have_pdep_rxns:
            line += ', const double* pres_mod_host'
        line += ', const double* spec_rates_host, const double* dy_host) {\n'
        file.write(line)
        # convience method to write rates to file
        if have_rev_rxns:
            file.write('    fprintf(fp, "Forward Rates\\n");\n'
                   '    for(int i = 0; i < FWD_RATES; ++i) {\n'
                   '        fprintf(fp, "%.15le\\n", fwd_rates_host[i]);\n'
                   '    }\n'
                   )
            file.write('    fprintf(fp, "Rev Rates\\n");\n')
            file.write('    for(int i = 0; i < REV_RATES; ++i) {\n'
                       '        fprintf(fp, "%.15le\\n", rev_rates_host[i]);\n'
                       '    }\n'
                       )
        else:
            file.write('    fprintf(fp, "Rates\\n");\n'
                   '    for(int i = 0; i < RATES; ++i) {\n'
                   '        fprintf(fp, "%.15le\\n", rates_host[i]);\n'
                   '    }\n'
                   )
        if have_pdep_rxns:
            file.write('    fprintf(fp, "Pres Mod Rates\\n");\n')
            file.write('    for(int i = 0; i < PRES_MOD_RATES; i++) {\n'
                       '        fprintf(fp, "%.15le\\n", pres_mod_host[i]);\n'
                       '    }\n'
                       )
        file.write('    fprintf(fp, "Spec Rates\\n");\n')
        file.write('    for(int i = 0; i < NSP; i++) {\n'
                   '        fprintf(fp, "%.15le\\n", spec_rates_host[i]);\n'
                   '    }\n'
                   )
        file.write('    fprintf(fp, "dy\\n");\n')
        file.write('    for(int i = 0; i < NN; i++) {\n'
                   '        fprintf(fp, "%.15le\\n", dy_host[i]);\n'
                   '    }\n'
                   '}\n\n'
                   )

        file.write('void write_jacob(FILE* fp, const double* jacob_host) {\n'
                   '    fprintf(fp, "Jacob\\n");\n'
                   '    for (int i = 0; i < NN * NN; ++i) {\n'
                   '        fprintf(fp, "%.15le\\n", jacob_host[i]);\n'
                   '    }\n'
                   '}\n\n'
                   )

        if lang != 'cuda':
            file.write('void write_jacobian_and_rates_output() {\n'
                       '    //set mass fractions to unity to turn on all reactions\n'
                       '    double y_host[NN] = {0.0};\n'
                       '    for (int i = 1; i < NN; ++i) {\n'
                       '        y_host[i] = 1.0 / ((double)NSP);\n'
                       '    }\n'
                       '    double conc_host[NSP] = {0.0};\n'
                       )
            if have_rev_rxns:
                file.write('    double fwd_rates_host[FWD_RATES] = {0.0};\n'
                           '    double rev_rates_host[REV_RATES] = {0.0};\n')
            else:
                file.write('    double rates_host[RATES] = {0.0};\n')
            if have_pdep_rxns:
                file.write('    double pres_mod_host[PRES_MOD_RATES] = {0.0};\n')

            file.write('    double spec_rates_host[NSP] = {0.0};\n'
                       '    double dy_host[NN] = {0.0};\n'
                       '    double jacob_host[NN * NN] = {0.0};\n'
                       '    //evaluate and write rates for various conditions\n'
                       '    FILE* fp = fopen ("rates_data.txt", "w");\n'
                       )
            __write_c_rate_evaluator(
                file, have_rev_rxns, have_pdep_rxns, '800', '1.01325e6', '1')
            __write_c_rate_evaluator(
                file, have_rev_rxns, have_pdep_rxns, '1600', '1.01325e6', '1')
            __write_c_rate_evaluator(
                file, have_rev_rxns, have_pdep_rxns, '800', '1.01325e7', '10')
            file.write('    fclose(fp);\n'
                       '}\n'
                       )
        else:
            file.write('void write_jacobian_and_rates_output(int NUM, int block_size, int grid_size) {\n'
                       '    cudaErrorCheck(cudaSetDevice(0));\n'
                       '#ifdef PROFILER\n'
                       '    //bump up shared mem bank size\n'
                       '    cudaErrorCheck(cudaDeviceSetSharedMemConfig(cudaSharedMemBankSizeEightByte));\n'
                       '    //and L1 size\n'
                       '    cudaErrorCheck(cudaDeviceSetCacheConfig(cudaFuncCachePreferL1));\n'
                       '#endif\n'
                      )
            if CUDAParams.is_global():
                file.write('    gpuMemory* host_memory = NULL;\n'
                       '    int padded = initialize_gpu_memory(NUM, block_size, grid_size, &host_memory);\n')
            else:
                file.write('    double *d_y;\n'
                           '#ifdef CONP\n'
                           '    double* d_pres;\n'
                           '    int padded = initialize_gpu_memory(NUM, block_size, grid_size, &d_y, &d_pres);\n'
                           '#elif CONV\n'
                           '    double* d_rho;\n'
                           '    int padded = initialize_gpu_memory(NUM, block_size, grid_size, &d_y, &d_rho);\n'
                           '#endif\n'
                          )
            file.write(
                       '    //set mass fractions to unity to turn on all reactions\n'
                       '    double y_host[NN] = {0.0};\n'
                       '    for (int i = 1; i < NN; ++i) {\n'
                       '        y_host[i] = 1.0 / ((double)NSP);\n'
                       '    }\n'
                       '    double* y_host_full = (double*)malloc(padded * NN * sizeof(double));\n'
                       '    for (int i = 1; i < NN; ++i) {\n'
                       '        for (int j = 0; j < padded; ++j) {\n'
                       '            y_host_full[j + i * padded] = y_host[i];\n'
                       '        }\n'
                       '    }\n'
                       '#ifdef CONP\n'
                       '    double* pres_host_full = (double*)malloc(padded * sizeof(double));\n'
                       '#elif CONV\n'
                       '    double* rho_host_full = (double*)malloc(padded * sizeof(double));\n'
                       '    double Xi[NSP] = {0.0};\n'
                       '    mass2mole(&y_host[1], Xi);\n'
                       '#endif\n'
                       '    double conc_host[NSP];\n'
                       '    double* conc_host_full = (double*)malloc(padded * NSP * sizeof(double));\n'
                       )
            file.write('#ifdef RATES_TEST\n')
            if have_rev_rxns:
                file.write('    double* fwd_rates_host_full = (double*)malloc(padded * FWD_RATES * sizeof(double));\n'
                           '    double* rev_rates_host_full = (double*)malloc(padded * REV_RATES * sizeof(double));\n'
                           '    double fwd_rates_host[FWD_RATES] = {0.0};\n'
                           '    double rev_rates_host[REV_RATES] = {0.0};\n'
                           )
            else:
                file.write('    double* rates_host_full = (double*)malloc(padded * RATES * sizeof(double));\n'
                           '    double rates_host[RATES] = {0.0};\n')
            if have_pdep_rxns:
                file.write('    double* pres_mod_host_full = (double*)malloc(padded * PRES_MOD_RATES * sizeof(double));\n'
                           '    double pres_mod_host[PRES_MOD_RATES] = {0.0};\n')

            file.write('    double spec_rates_host[NSP] = {0.0};\n'
                       '    double dy_host[NN] = {0.0};\n'
                       '    double jacob_host[NN * NN] = {0.0};\n'
                       '    double* spec_rates_host_full = (double*)malloc(padded * NSP * sizeof(double));\n'
                       '    double* dy_host_full = (double*)malloc(padded * NN * sizeof(double));\n'
                       '    double* jacob_host_full = (double*)malloc(padded * NN * NN * sizeof(double));\n'
                       )
            file.write('#endif\n'
                       '    //evaluate and write rates for various conditions\n'
                       '    FILE* fp = fopen ("rates_data.txt", "w");\n'
                       )

            if not CUDAParams.is_global():
                # need to define arrays
                file.write('    double* d_spec_rates, *d_dy, *d_conc;\n'
                           '    cudaMalloc((void**)&d_spec_rates, padded * NSP * sizeof(double));\n'
                           '    cudaMalloc((void**)&d_dy, padded * NN * sizeof(double));\n'
                           '    cudaMalloc((void**)&d_conc, padded * NSP * sizeof(double));\n'
                           )
                if have_rev_rxns:
                    file.write('    double *d_fwd_rates, *d_rev_rates;\n')
                    file.write('    cudaMalloc((void**)&d_fwd_rates, padded * FWD_RATES * sizeof(double));\n'
                               '    cudaMalloc((void**)&d_rev_rates, padded * REV_RATES * sizeof(double));\n')
                else:
                    file.write(
                        '    double* d_rates;\n'
                        '    cudaMalloc((void**)&d_rates, padded * RATES * sizeof(double));\n')
                if have_pdep_rxns:
                    file.write(
                        '    double* d_pres_mod;\n'
                        '    cudaMalloc((void**)&d_pres_mod, padded * PRES_MOD_RATES * sizeof(double));\n')
                file.write(
                    '    double* d_jac;\n'
                    '    cudaMalloc((void**)&d_jac, padded * NN * NN * sizeof(double));\n')

            __write_cuda_rate_evaluator(
                file, have_rev_rxns, have_pdep_rxns, '800', '1.01325e6', '1')
            __write_cuda_rate_evaluator(
                file, have_rev_rxns, have_pdep_rxns, '1600', '1.01325e6', '1')
            __write_cuda_rate_evaluator(
                file, have_rev_rxns, have_pdep_rxns, '800', '1.01325e7', '10')
            file.write('    fclose(fp);\n'
                       '    free(conc_host_full);\n'
                       '    free(y_host_full);\n'
                       '#ifdef RATES_TEST\n'
                       '#ifdef CONP\n'
                       '    free(pres_host_full);\n'
                       '#elif CONV\n'
                       '    free(rho_host_full);\n'
                       '#endif\n'
                       '    free(dy_host_full);\n'
                       '    free(spec_rates_host_full);\n'
                       '    free(jacob_host_full);\n'
                       )
            if have_rev_rxns:
                file.write('    free(fwd_rates_host_full);\n'
                           '    free(rev_rates_host_full);\n'
                           )
            else:
                file.write('    free(rates_host_full);\n')
            if have_pdep_rxns:
                file.write('    free(pres_mod_host_full);\n')

            if not CUDAParams.is_global():
                file.write('    cudaErrorCheck(cudaFree(d_y));\n'
                           '    cudaErrorCheck(cudaFree(d_dy));\n'
                           '    cudaErrorCheck(cudaFree(d_spec_rates));\n'
                           '    cudaErrorCheck(cudaFree(d_pres));\n'
                           '#ifdef CONV\n'
                           '    cudaErrorCheck(cudaFree(d_rho));\n'
                           '#endif\n'
                           '    cudaErrorCheck(cudaFree(d_conc));\n'
                           )
                if have_rev_rxns:
                    file.write('    cudaErrorCheck(cudaFree(d_fwd_rates));\n')
                    file.write('    cudaErrorCheck(cudaFree(d_rev_rates));\n')
                else:
                    file.write('    cudaErrorCheck(cudaFree(d_rates));\n')

                if have_pdep_rxns:
                    file.write('    cudaErrorCheck(cudaFree(d_pres_mod));\n')
                file.write('    cudaErrorCheck(cudaFree(d_jac));\n')
                file.write('#endif\n')
            else:
                file.write('#endif\n')
                file.write('    free_gpu_memory(&host_memory);\n')

            file.write('    cudaErrorCheck(cudaDeviceReset());\n')
            file.write('}\n')
        file.write('#endif\n')
    if lang == 'cuda':
        conp = [(['h', 'cp'], 'NSP'), (['pres'], '1')]
        conv = [(['u', 'cv'], 'NSP'), (['rho'], '1')]
        arrays = [(['jac'], 'NN * NN')]
        arrays.append(
            (['y', 'dy', 'f_temp', 'error'], 'NN'))
        arrays.append((['conc'], 'NSP'))
        if have_rev_rxns:
            arrays.append((['fwd_rates'], 'FWD_RATES'))
            arrays.append((['rev_rates'], 'REV_RATES'))
        else:
            arrays.append((['rates'], 'RATES'))
        if have_pdep_rxns:
            arrays.append((['pres_mod'], 'PRES_MOD_RATES'))
        flat_arrays = [
            x for x in itertools.chain(*[arr[0] for arr in arrays])]
        flat_conp = [
            x for x in itertools.chain(*[arr[0] for arr in conp])]
        flat_conv = [
            x for x in itertools.chain(*[arr[0] for arr in conv])]

        all_arrays_conv = arrays + conv
        all_arrays_conp = arrays + conp

        mem_template = 'double* {};'
        with open(path + 'gpu_memory.cuh', 'w') as file:
            file.write('#ifndef GPU_MEMORY_CUH\n'
                       '#define GPU_MEMORY_CUH\n'
                       '\n'
                       '#include "header.h"\n'
                       '#include "mechanism.cuh"\n'
                       '#include "gpu_macros.cuh"\n'
                       '\n'
                       )
            if CUDAParams.is_global():
                file.write('struct gpuMemory {\n'
                           '#ifdef CONP\n'
                           )
                file.write('\n'.join([mem_template.format(x) for x in flat_conp]))
                file.write('\n#elif CONV\n')
                file.write('\n'.join([mem_template.format(x) for x in flat_conv]))
                file.write('\n#endif\n')
                file.write('\n'.join([mem_template.format(x) for x in flat_arrays]))
                file.write('\n};\n\n')
                file.write('int initialize_gpu_memory(int NUM, int block_size, int grid_size, gpuMemory** host_memory);\n'
                           'void free_gpu_memory(gpuMemory** host_memory);\n'
                           '\n'
                           '#endif\n')
            else:
                file.write('#ifdef CONP\n'
                           'int initialize_gpu_memory(int NUM, int block_size, int grid_size, double** y_device, double** pres_device);\n'
                           'void free_gpu_memory(double* y_device, double* pres_device);\n'
                           '#else\n'
                           'int initialize_gpu_memory(int NUM, int block_size, int grid_size, double** y_device, double** rho_device);\n'
                           'void free_gpu_memory(double* y_device, double* rho_device);\n'
                           '#endif\n'
                           '\n'
                           '#endif\n')

        with open(path + 'gpu_memory.cu', 'w') as file:
            init_template = 'initialize_pointer(&{}, {});'
            free_template = 'cudaErrorCheck(cudaFree({}));'
            file.write('#include <string.h>\n'
                       '#include "gpu_memory.cuh"\n'
                       '\n')
            if CUDAParams.is_global():
              file.write('\n__constant__ gpuMemory memory_pointers;\n')
            file.write('void initialize_pointer(double** ptr, int size) {\n'
                       '    cudaErrorCheck(cudaMalloc((void**)ptr, size * sizeof(double)));\n'
                       '    cudaErrorCheck(cudaMemset(*ptr, 0, size * sizeof(double)));\n'
                       '}\n')
            if CUDAParams.is_global():
                file.write('\n')
                file.write('\nint initialize_gpu_memory(int NUM, int block_size, int grid_size, gpuMemory** host_memory) {\n'
                           '  int padded = grid_size * block_size > NUM ? grid_size * block_size : NUM;\n'
                           '  *host_memory = (gpuMemory*)malloc(sizeof(gpuMemory));\n'
                           '#ifdef CONP\n')
                for arr in all_arrays_conp:
                    for a in arr[0]:
                        file.write(
                            '  ' + init_template.format('(*host_memory)->' + a, 'padded * ' + arr[1]) + '\n')
                file.write('#elif CONV\n')
                for arr in all_arrays_conv:
                    for a in arr[0]:
                        file.write(
                            '  ' + init_template.format('(*host_memory)->' + a, 'padded * ' + arr[1]) + '\n')

                file.write('#endif\n')
                file.write('  cudaErrorCheck(cudaMemcpyToSymbol(memory_pointers, (*host_memory), sizeof(gpuMemory)));\n')
                file.write(
                    '  return padded;\n'
                    '}'
                )
                file.write('\n')
                file.write('\n\nvoid free_gpu_memory(gpuMemory** host_memory) {\n'
                           '#ifdef CONP\n  ' +
                           '\n  '.join([free_template.format('(*host_memory)->' + a) for a in flat_conp + flat_arrays]) +
                           '\n#else\n  ' +
                           '\n  '.join([free_template.format('(*host_memory)->' + a) for a in flat_conv + flat_arrays]) +
                           '\n#endif\n'
                           '  free(*host_memory);\n'
                           '}\n'
                           )
            else:
                file.write('#ifdef CONP\n'
                           'int initialize_gpu_memory(int NUM, int block_size, int grid_size, double** y_device, double** pres_device)\n'
                           '#else\n'
                           'int initialize_gpu_memory(int NUM, int block_size, int grid_size, double** y_device, double** rho_device)\n'
                           '#endif\n'
                           '{\n'
                           '    int padded = grid_size * block_size > NUM ? grid_size * block_size : NUM;\n'
                           '    cudaErrorCheck(cudaMalloc((void**)y_device, padded * NN * sizeof(double)));\n'
                           '#ifdef CONP\n'
                           '    cudaErrorCheck(cudaMalloc((void**)pres_device, padded * sizeof(double)));\n'
                           '#else\n'
                           '    cudaErrorCheck(cudaMalloc((void**)rho_device, padded * sizeof(double)));\n'
                           '#endif\n'
                           '    return padded;\n'
                           '}\n'
                           )
                file.write('#ifdef CONP\n'
                           'void free_gpu_memory(double* y_device, double* pres_device)\n'
                           '#else\n'
                           'void free_gpu_memory(double* y_device, double* rho_device)\n'
                           '#endif\n'
                           '{\n'
                           '    cudaErrorCheck(cudaFree(y_device));\n'
                           '#ifdef CONP\n'
                           '    cudaErrorCheck(cudaFree(pres_device));\n'
                           '#else\n'
                           '    cudaErrorCheck(cudaFree(rho_device));\n'
                           '#endif\n'
                           '}\n'
                           )

    if lang == 'cuda':
        with open(path + 'gpu_macros.cuh', 'w') as file:
            file.write('#ifndef GPU_MACROS_CUH\n'
                       '#define GPU_MACROS_CUH\n'
                       '#include <stdio.h>\n'
                       '#include <cuda.h>\n'
                       '#include <cuda_runtime.h>\n'
                       '#include <helper_cuda.h>\n'
                       '\n'
                       )
            if CUDAParams.is_global():
                file.write('#define GLOBAL_MEM\n')

            file.write('#define CU_LINEAR_OFFSET(I) (threadIdx.x + blockIdx.x * blockDim.x + (I) * blockDim.x * gridDim.x)\n'
                       '\n'
                       '#ifdef GLOBAL_MEM\n'
                       '    #define INDEX(I) (CU_LINEAR_OFFSET((I)))\n'
                       '#else\n'
                       '    #define INDEX(I) ((I))\n'
                       '#endif\n'
                       '\n'
                       )
            file.write('#define cudaErrorCheck(ans) { gpuAssert((ans), __FILE__, __LINE__); }\n'
                       'inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort=true)\n'
                       '{\n'
                       '    if (code != cudaSuccess)\n'
                       '    {\n'
                       '        fprintf(stderr,"GPUassert: %s %s %d\\n", cudaGetErrorString(code), file, line);\n'
                       '        if (abort) exit(code);\n'
                       '    }\n'
                       '}\n'
                       )
            file.write('#endif\n')
