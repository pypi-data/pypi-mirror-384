
from argparse import ArgumentParser, Action, RawDescriptionHelpFormatter, \
    ArgumentTypeError, BooleanOptionalAction
from itertools import zip_longest
from warnings import warn
import h5py
import numpy as np
from scipy.spatial.transform import Rotation as R
import hpc_suite as hpc
from .barrier import barrier
from .optics import optics
from .basis import parse_termsymbol, couple, unitary_transform
from .multi_electron import Ion
from .model import SpinHamiltonian, ZeemanHamiltonian, read_params, \
    HARTREE2INVCM, print_basis, make_proj_evaluator, make_operator_storage, \
    MagneticSusceptibilityFromFile, EPRGtensorFromFile, \
    TintFromFile, make_broken_symmetry_exchange_storage


# Action for secondary help message
class SecondaryHelp(hpc.SecondaryHelp):
    def __init__(self, option_strings, dest=None, const=None, default=None,
                 help=None):
        super().__init__(option_strings, dest=dest, const=const,
                         default=default, help=help)

    def __call__(self, parser, values, namespace, option_string=None):
        read_args([self.const, '--help'])


class QuaxAction(Action):
    def __init__(self, option_strings, dest, nargs=1, default=None, type=None,
                 choices=None, required=False, help=None, metavar=None):

        super().__init__(
            option_strings=option_strings, dest=dest, nargs=nargs,
            default=default, type=type, choices=choices, required=required,
            help=help, metavar=metavar
        )

    def __call__(self, parser, namespace, value, option_string=None):

        try:  # import from HDF5 database
            with h5py.File(value[0], 'r') as h:
                quax = h["quax"][...]
        except FileNotFoundError:  # choose coordinate system axis
            # cyclic permutation
            perm = {"x": [1, 2, 0], "y": [2, 0, 1], "z": [0, 1, 2]}[value[0]]
            quax = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])[perm]
        except OSError:
            quax = np.loadtxt(value[0])
        except:
            raise ValueError("Invalid QUAX specification.")

        setattr(namespace, self.dest, quax)


def parse_coupling(string):
    j, j1j2 = hpc.make_parse_dict(str, str)(string)
    j1, j2 = tuple(j1j2.split(','))

    if not j2:
        raise ArgumentTypeError("Expected comma separated angmom symbols.")

    return (j, (j1, j2))


def parse_term(string):
    term, ops = hpc.make_parse_dict(str, str)(string)
    return (term, tuple(ops.split(',')))


def parse_index(x):
    return int(x) - 1


def barrier_func(args):
    """
    Wrapper function for command line interface call to barrier

    Parameters
    ----------
    args : argparser object
        command line arguments

    Returns
    -------
    None

    """

    if args.raw == False:
        barrier(
            h5name=args.molcas_rassi,
            Zeeman=args.Zeeman,
            num_states=args.num_states,
            trans_colour=args.trans_colour,
            state_colour=args.state_colour,
            show=args.show,
            save=args.save,
            save_name=args.save_name,
            xlabel=args.x_label,
            ylabel=args.y_label,
            yax2=args.yax2,
            yax2_label=args.yax2_label,
            yax2_conv=args.yax2_conv,
            print_datafile=not args.no_datafile,
	    verbose=not args.quiet,
            allowed_trans="forwards",
            scale_trans=True,
            normalise_trans=True
            )
    else:
        barrier(
            h5name=args.molcas_rassi,
            Zeeman=args.Zeeman,
            num_states=args.num_states,
            trans_colour=args.trans_colour,
            state_colour=args.state_colour,
            show=args.show,
            save=args.save,
            save_name=args.save_name,
            xlabel=args.x_label,
            ylabel=args.y_label,
            yax2=args.yax2,
            yax2_label=args.yax2_label,
            yax2_conv=args.yax2_conv,
            print_datafile=not args.no_datafile,
            verbose=not args.quiet,
            allowed_trans="all",
            scale_trans=False,
            normalise_trans=False
            )

def optics_func(args):
    """
    Wrapper function for command line interface call to optical property evaluation

    Parameters
    ----------
        args : argparser object
            command line arguments
        unknown_args : list
            unknown command line flags to be passed on to a secondary parser

    Returns
    -------
        None
    """

    optics(
        h5name=args.molcas_rassi,
        property=args.property,
        orientation=args.orientation,
        states=args.states,
        degeneracy=args.degeneracy,
        Zeeman=args.Zeeman
    )
    return


model_parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        add_help=False
)

model_parser.add_argument(
    '--model_space',
    type=parse_termsymbol,
    help='Symbol of the model space.'
)

model_parser.add_argument(
    '--coupling',
    nargs='*',
    default={},
    action=hpc.action.ParseKwargs,
    type=parse_coupling,
    metavar="j=j1,j2",
    help='Coupling dictionary connecting the basis space to the model space.'
)

model_parser.add_argument(
    '--terms',
    nargs='*',
    default={},
    action=hpc.action.ParseKwargsAppend,
    type=parse_term,
    metavar="term=j1,j2,...",
    help='Dictionary of spin Hamiltonian terms.'
)

model_print_parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        add_help=False
)

model_print_parser.add_argument(
    '--comp_thresh',
    default=0.05,
    type=float,
    help='Amplitude threshold for composition contribution printing.'
)

model_print_parser.add_argument(
    '--field',
    type=float,
    help=('Apply magnetic field (in mT) to split input states. If zero, '
          'Kramers doublets are rotated into eigenstates of Jz.')
)

model_print_parser.add_argument(
    '--verbose',
    action='store_true',
    help='Print out angular momentum matrices and extra information.'
)

model_print_parser.add_argument(
    '--shift',
    action=BooleanOptionalAction,
    default=True,
    help='Shift eigenvalues in basis print-out.'
)

model_full_parser = ArgumentParser(
        parents=[model_parser],
        formatter_class=RawDescriptionHelpFormatter,
        add_help=False
)

model_full_parser.add_argument(
    '--k_max',
    type=int,
    default=6,
    help='Maximum Stevens operator rank.'
)

model_full_parser.add_argument(
    '--theta',
    action='store_true',
    help='Factor out operator equivalent factors.'
)

model_full_parser.add_argument(
    '--ion',
    type=Ion.parse,
    # choices=[Ion.parse('Dy3+')],
    help='Central ion.'
)

model_full_parser.add_argument(
    '--quax',
    action=QuaxAction,
    help='Quantisation axes. Given either as x, y or z,'
         'or as a 3x3 matrix in a text file using SINGLE_ANISO format.'
         'That is, (Rz(a)Ry(b)Rz(g))^T, where Rz and Ry are rotation'
         'matrices around z and y, and a, b, g are the Euler angles.'
         'e.g. --quax quax.txt'
)

model_full_parser.add_argument(
    '--zeeman',
    action='store_true',
    help=('By default construct the Zeeman Hamiltonian from the canonical '
          'total spin and orbital angular momentum operators. '
          'Alternatively, Hzee may be constructed using the effective '
          'g-values of the model angular momentum operators.')
)

proj_parser = ArgumentParser(
        parents=[model_full_parser],
        formatter_class=RawDescriptionHelpFormatter,
        add_help=False
)

proj_parser.add_argument(
    '--basis',
    default='l',
    choices=['l', 'j'],
    help='Intermediate ab initio basis representation.'
)

proj_parser.add_argument(
    '--truncate',
    type=int,
    nargs='+',
    help='Truncate ab initio space before constucting the angmom basis.'
)

proj_parser.add_argument(
    '--orbital_reduction',
    action='store_true',
    help='Determine and employ orbital reduction factors in basis construction.'
)

proj_parser.add_argument(
    '--tp_equivalence',
    action='store_true',
    help='Carry out projection based on T-P equivalence model.'
)

proj_parser.add_argument(
    '--comp_thresh',
    default=0.05,
    type=float,
    help='Amplitude threshold for composition contribution printing.'
)

proj_parser.add_argument(
    '--field',
    type=float,
    help=('Apply magnetic field (in mT) to split input states. If zero, '
          'Kramers doublets are rotated into eigenstates of Jz.')
)

proj_parser.add_argument(
    '--verbose',
    action='store_true',
    help='Print out angular momentum matrices and extra information.'
)


def proj_func(args, unknown_args):
    """
    Wrapper function for command line interface call to spin Hamiltonian
    parameter projection.

    Parameters
    ----------
    args : argparser object
        command line arguments
    unknown_args : list
        unknown command line flags to be passed on to a secondary parser

    Returns
    -------
    None
    """

    store_args = hpc.read_args(['store'] + unknown_args + ['--row_names'])
    options = hpc.filter_parser_args(args)

    if '-i' in unknown_args:
        raise ValueError("Use package specific input flags instead of -i!")

    hpc.store_func(store_args, make_proj_evaluator, (None,), **options)


def model_func(args, unknown_args):

    model = SpinHamiltonian(
        args.model_space,
        **args.terms,
        k_max=args.k_max,
        theta=args.theta,
        ion=args.ion,
        time_reversal_symm="even",
        diag=False
    )

    # read parameters
    params = dict(p for f, m in zip_longest(args.input, args.map, fillvalue={})
                  for p in read_params(f, **dict(m)))

    basis_space, cg_vec = couple(args.model_space, **args.coupling)

    # compute trafo from model basis to coupled (and rotated) angmom basis
    # ===================================================================
    # The aim of the quax rotation is to redefine the coordinate frame, and in particular the orientation of the z-axis
    # First approach: Active rotation of the physical system, i.e. all vector operators (angm, spin) via:
    #                 quax * vector = D^dagger(quax) vector D(quax)
    #                 -> The basis states remain eigenstates of the angular momentum operators of the unrotated system!
    # Second approach: Passive rotation (= "unrotation") of the Hamiltonian basis via: D^dagger(quax.T) H D(quax.T),
    #                  and leaving the angular momentum operators untouched.
    # The second approach corresponds effectively to the overall rotation of the physical system AND basis through:
    # D^dagger(quax.T) D^dagger(quax) vector D(quax) D(quax.T).
    # The advantage is that the rotated angular momentum operators in the rotated basis have the same structure
    # as the unrotated angular momentum operators in the unrotated basis
    # (e.g. correspondence between third component of rotated operator and z-component of original operator).
    # This facilitates a straightforward interpretation of the state composition and direct analogy
    # to the calculation with the quax rotation applied at the proj stage. Hence, the second approach is employed.

    def trafo(op, rot=False):
        if args.quax is not None and rot:  # compute basis change from basis rotation
            rotation = args.model_space.rotate(R.from_matrix(args.quax.T))
            return unitary_transform(op, rotation @ cg_vec)
        else:
            return unitary_transform(op, cg_vec)

    hamiltonian = model.parametrise(
        params, scale=args.scale, verbose=args.verbose) / HARTREE2INVCM

    if args.zeeman:
        spin, angm = ZeemanHamiltonian(args.model_space).resolve_zeeman_ops(params, verbose=True)

    else:
        spin = np.sum([args.model_space.get_op(op)
                       for op in args.model_space.elementary_ops('spin')], axis=0)

        if spin.size == 1:
            warn("No spin momenta present assuming S=0!")

        angm = np.sum([args.model_space.get_op(op)
                       for op in args.model_space.elementary_ops('angm')], axis=0)

        if angm.size == 1:
            warn("No orbital momenta present assuming L=0!")

    # print trafo from diagonal basis to coupled + rotated angmom basis
    print_basis(trafo(hamiltonian, rot=True), trafo(spin), trafo(angm),
                basis_space, comp_thresh=args.comp_thresh, shift=args.shift,
                field=args.field)

    store_args = hpc.read_args(['store'] + unknown_args)

    ops = {"hamiltonian": trafo(hamiltonian, rot=True), "spin": trafo(spin), "angm": trafo(angm)}

    hpc.store_func(store_args, make_operator_storage, list(ops.keys()), **ops)


def sus_func(args, unknown_args):

    store_args = hpc.read_args(['store'] + unknown_args)
    kwargs = hpc.filter_parser_args(args)

    hpc.store_func(store_args, lambda f, store, **kwargs: store(f, **kwargs),
                   (MagneticSusceptibilityFromFile,), **kwargs)


def eprg_func(args, unknown_args):

    store_args = hpc.read_args(['store'] + unknown_args)
    kwargs = hpc.filter_parser_args(args)

    hpc.store_func(store_args, lambda f, store, **kwargs: store(f, **kwargs),
                   (EPRGtensorFromFile,), **kwargs)


def tint_func(args, unknown_args):

    store_args = hpc.read_args(['store'] + unknown_args)
    kwargs = hpc.filter_parser_args(args)

    hpc.store_func(store_args, lambda f, store, **kwargs: store(f, **kwargs),
                   (TintFromFile,), **kwargs)


def bs_func(args, unknown_args):

    store_args = hpc.read_args(['store'] + unknown_args)
    kwargs = hpc.filter_parser_args(args)

    def extract_orca_energies(f_orca_list):
        from orca_suite.extractor import make_extractor as make_orca_extractor

        def generate_orca_energies():
            for det, file in f_orca_list:
                if all(p == 'u' for p in det) or all(p == 'd' for p in det):  # HS determinant
                    yield from make_orca_extractor(file, ('scf', 'energy'))
                else:  # Broken-symmetry determinants
                    yield from make_orca_extractor(file, ('scf', 'bs_energy'))

        return {det: float(ener) for (det, file), (mult, ener) in zip(f_orca_list, generate_orca_energies())}

    if kwargs['orca_out'] is not None:
        eners = extract_orca_energies(kwargs['orca_out'])

    if kwargs['energies'] is not None:
        eners = dict(kwargs['energies'])

    del kwargs['orca_out']
    del kwargs['energies']

    hpc.store_func(store_args, make_broken_symmetry_exchange_storage, ("Broken symmetry exchange",), eners=eners, **kwargs)


def read_args(arg_list=None):

    description = '''
    A package for angular momentum related functionalities.
    '''

    epilog = '''
    Lorem ipsum.
    '''

    parser = ArgumentParser(
            description=description,
            epilog=epilog,
            formatter_class=RawDescriptionHelpFormatter
            )

    subparsers = parser.add_subparsers(dest='prog')

    # Barrier figure

    barrier = subparsers.add_parser(
        'barrier',
        description="""
        Creates barrier figure of lowest lying J multiplet.
        Transition probabilities are given by magnetic moment operator.
        Note a small quantisation field is applied along the z axis to give
        correct <Jz> values
        """
    )

    barrier.set_defaults(func=barrier_func)

    barrier.add_argument(
        '--molcas_rassi',
        type=str,
        help='OpenMolcas rassi HDF5 file name'
    )

    barrier.add_argument(
        '--Zeeman',
        type=float,
        nargs=3,
        default=None,
        help='Magnetic field applied in Tesla: this is used to add a field to define the eigenstates, as well as defining the orientation of the quantisation axis (default 0 0 25e-6)'
    )

    barrier.add_argument(
        '--num_states',
        type=int,
        default=None,
        help='Choose the number of states to inlcude in the barrier figure. Default is all states.'
    )

    barrier.add_argument(
        "--trans_colour",
        type=str,
        default="#ff0000",
        metavar="value",
        help="Colour for transition arrows as hex or name (default red) - can be None to hide arrows"
    )

    barrier.add_argument(
        "--state_colour",
        type=str,
        default="black",
        metavar="value",
        help="Colour for states as hex or name"
    )

    barrier.add_argument(
        "--show",
        action="store_true",
        default=False,
        help="If true, show barrier figure on screen"
    )

    barrier.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="If true, save barrier figure to current directory"
    )

    barrier.add_argument(
        "--save_name",
        type=str,
        default="barrier.pdf",
        help="File to save barrier figure to"
    )

    barrier.add_argument(
        "--x_label",
        type=str,
        default=r"$\langle \ \hat{J}_{z} \ \rangle$",
        help="Label for x axis"
    )

    barrier.add_argument(
        "--y_label",
        type=str,
        default=r"Energy (cm$^{-1}$)",
        help="Label for primary (left) y axis"
    )

    barrier.add_argument(
        "--yax2",
        action="store_true",
        default=False,
        help="If true, include secondary (left) y axis"
    )

    barrier.add_argument(
        "--yax2_label",
        type=str,
        default=r"Energy (K)",
        help="Label for secondary (right) y axis"
    )

    barrier.add_argument(
        "--yax2_conv",
        type=float,
        default=1.4,
        help="Conversion factor between left --> right y axes"
             + "(default is cm-1 --> K)"
    )

    barrier.add_argument(
        "--no_datafile",
        action="store_true",
        default=False,
        help="Disable printing of datafile to execution directory"
    )

    barrier.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Prevent output of file names to screen"
    )

    #barrier.add_argument(
    #    "--no_normalise",
    #    action="store_true",
    #    default=False,
    #    help="Do not normalise transitions"
    #)

    #barrier.add_argument(
    #    "--no_scale",
    #    action="store_true",
    #    default=False,
    #    help="Do not scale transitions"
    #)

    #barrier.add_argument(
    #    "--allowed_trans",
    #    type=str,
    #    default="forward",
    #    help="Allow only 'forward' transitions (default) or 'all' transitions"
    #)

    barrier.add_argument(
        "--raw",
        action="store_true",
        default=False,
        help="Show all transitions with no scaling or normalisation"
    )

    # optical property evaluation

    optics = subparsers.add_parser(
        'optics',
        description="""
        Evaluate optical properties.
        """
    )

    optics.set_defaults(func=optics_func)

    optics.add_argument(
        '--molcas_rassi',
        type=str,
        help='OpenMolcas rassi HDF5 file name'
    )

    optics.add_argument(
        '-p', '--property',
        type=str,
        nargs='?',
        choices=['abs', 'lum', 'cpl', 'cd', 'hdf5'],
        const='abs', 
        default='abs',
        help='evaluated property which can be either absorption, luminescence, circularly polarised luminescence or circular dichroism, respectively'
    )

    optics.add_argument( # currently useless TODO
        '-o', '--orientation',
        type=str,
        nargs='?',
        choices=['iso', 'x', 'y', 'z'],
        const='iso', 
        default='iso',
        # help='type of CPL evaluation desired, for either isotropic calculation or evaluation along an axis.'
        help='feature not yet available; default = isotropic evaluation'
    )
 
    optics.add_argument(
        '-s', '--states',
        type=int,
        nargs=3,
        default=None,
        help='starting from 0, labels of the states in the following order: \nthe reference state (either emitting or absorbing), \
            the lowest and highest states which form the range between which the transitions are evaluated. \
            By default, all transitions are calculated (which can be a lot!)'
    )

    optics.add_argument(
        '-d', '--degeneracy',
        type=float,
        nargs='?',
        default=0.0,
        const=1e-5,
        help='enable to consider the degeneracy of the states; a default threshold of 1e-5 eV is considered, \
            but the user can set a different value (float)'
    ) 
    
    optics.add_argument(
        '-z', '--Zeeman',
        type=float,
        nargs=3,
        default=None,
        # const=[0.0, 0.0, 1.0],
        help='enable to consider a Zeeman effect on the SO states. \
            Enter the external magnetic field vector in Tesla by its three components Bx By Bz, respectively; \
            e.g. to apply a magnetic field of 1 T along the z-axis, enter 0 0 1'
    ) 

    proj = subparsers.add_parser('proj', parents=[proj_parser])
    proj.set_defaults(func=proj_func)

    proj_input = proj.add_mutually_exclusive_group()

    proj_input.add_argument(
        '--molcas_rassi',
        type=str,
        help='Molcas *.rassi file containing angm and amfi operators.'
    )
    proj.add_argument(
        '-H', '--Help', const='store',
        action=hpc.SecondaryHelp,
        help='show help message for additional arguments and exit'
    )

    ham = subparsers.add_parser('model', parents=[model_full_parser, model_print_parser])
    ham.set_defaults(func=model_func)

    ham.add_argument(
        '--input', '-i',
        default=[],
        nargs='+',
        help='HDF5 data bases containing the spin Hamiltonian parameters.'
    )

    ham.add_argument(
        '--map',
        nargs='+',
        type=hpc.make_parse_dict(str, str),
        default=[],
        action='append',
        help=('Mapping of angular momentum quantum numbers to unique '
              'identifiers in order of input files. Necessary when combining '
              'parameter files with overlapping identifiers.')
    )

    ham.add_argument(
        '--scale',
        nargs='*',
        default={},
        action=hpc.action.ParseKwargs,
        type=hpc.make_parse_dict(str, float),
        help='Scale model term by factor.'
    )

    sus = subparsers.add_parser('sus')
    sus.set_defaults(func=sus_func)

    sus.add_argument(
        '--temperatures',
        nargs='+',
        type=float,
        help='Temperatures at which chi is calculated.'
    )

    sus.add_argument(
        '--field',
        default=0.0,
        type=float,
        help=('Determine susceptibility at finite field (in mT). '
              'If zero calculate differential susceptibility.')
    )

    sus.add_argument(
        '--differential',
        action=BooleanOptionalAction,
        help='Calculate differential susceptibility.'
    )

    sus.add_argument(
        '--iso',
        action='store_true',
        help='Compute isotropic susceptibility from full tensor.'
    )

    sus.add_argument(
        '--chi_T',
        action=BooleanOptionalAction,
        help='Calculate susceptibility times temperature.'
    )

    eprg = subparsers.add_parser('eprg')
    eprg.set_defaults(func=eprg_func)

    eprg_output = eprg.add_mutually_exclusive_group(required=True)

    eprg.add_argument(
        '--multiplets',
        nargs='+',
        type=int,
        help='Manually define multiplets of the ground electronic manifold.'
    )

    eprg_output.add_argument(
        '--eprg_values',
        action='store_true',
        help='Compute principal values of the G-tensor'
    )

    eprg_output.add_argument(
        '--eprg_vectors',
        action='store_true',
        help='Compute principal axes of the G-tensor'
    )

    eprg_output.add_argument(
        '--eprg_tensors',
        action='store_true',
        help='Compute G-tensor in the Cartesian frame'
    )

    tint = subparsers.add_parser('tint')
    tint.set_defaults(func=tint_func)

    tint.add_argument(
        '--field',
        default=0.,
        type=float,
        help='Determine tint at finite field (in mT along z).'
    )

    tint.add_argument(
        '--states',
        type=parse_index,
        nargs='+',
        help='Subset of states for which the tint will be computed.'
    )

    bs = subparsers.add_parser('bs', parents=[model_parser, model_print_parser])
    bs.set_defaults(func=bs_func)

    bs_energies = bs.add_mutually_exclusive_group(required=True)

    bs_energies.add_argument(
        '--energies',
        nargs='+',
        type=hpc.make_parse_dict(str, float),
        help='Energies (in hartree) corresponding to each determinant, e.g. "uud=123.45".'
    )

    bs_energies.add_argument(
        '--orca_out',
        nargs='+',
        type=hpc.make_parse_dict(str, str),
        help='ORCA output files corresponding to a set of broken-symmetry calculations, e.g. "uud=orca.out".'
    )

    # read sub-parser
    parser.set_defaults(func=lambda args: parser.print_help())
    args, hpc_args = parser.parse_known_args(arg_list)

    # select parsing option based on sub-parser

    if arg_list:
        return hpc.filter_parser_args(args)

    if args.prog in ['proj', 'model', 'sus', 'eprg', 'tint', 'bs']:
        args.func(args, hpc_args)

    else:
        args.func(args)


def main():
    read_args()
