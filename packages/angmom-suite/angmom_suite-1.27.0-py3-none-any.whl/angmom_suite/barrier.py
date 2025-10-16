"""
This module contains functions for plotting barrier figures
"""

import numpy as np
import matplotlib.pyplot as plt
import jax.numpy as jnp
from molcas_suite.extractor import make_extractor as make_molcas_extractor
from .basis import sf2ws, sf2ws_amfi, unitary_transform, \
    dissect_array, extract_blocks, make_angmom_ops_from_mult
from . import utils as ut
from .magnetism import compute_eprg_tensors

def barrier(h5name, Zeeman=None, num_states=None,
            trans_colour="#ff0000", state_colour="black", show=False,
            save=True, save_name="barrier.png",
            xlabel=r"$\langle \hat{J}_{z} \rangle$",
            ylabel=r"Energy (cm$^{-1}$)", yax2_label="Energy (K)",
            yax2=False, yax2_conv=1.4, print_datafile=True, verbose=True,
            allowed_trans="forwards", scale_trans=True, normalise_trans=True):
    """
    Creates barrier figure from OpenMolcas rassi.h5 file

    Parameters
    ----------
        h5name : str
            Name of the MOLCAS rassi.h5 file.
        Zeeman : float, default=None
            Magnetic field strength in Tesla (default 0,0,25 uT)
        num_states : int
            Number of states to include
        trans_colour : str, defualt "#ff0000" (red)
            Hex code or name specifying arrow colours
        state_colour: str, default "black"
            Hex code or name specifying state colours
        show : bool, default False
            If True, show plot on screen - disabled with `ax_in`
        save : bool, default True
            If True, save plot to file - disabled with `ax_in`
        save_name : str, default "barrier.pdf"
            Filename for saved image
        yax2 : bool, default False
            If True use secondary y (energy) axis
        yax2_conv : float, default 1.4 (cm-1 --> Kelvin)
            Conversion factor from primary to secondary y axis
        yax2_label : str, default "Energy (K)"
            Label for secondary y axis (requires `yax2=True`)
        xlabel : str, default "$\langle \ \hat{J}_{z} \ \rangle$"
            x label
        ylabel : str, default "Energy (cm$^{-1}$)"
            x label
        print_datafile : bool, default True
            If True, save datafile containing energies, Bz, Jz, k_max
            to barrier_data.dat in execution directory
        verbose : bool, default True
            If True, print all saved filenames to screen
        allowed_trans : str {'forwards','all'}
            Which transitions should be plotted:
            forwards: Only those which move up and over barrier
            all : All transitions
        scale_trans : bool, default True
            If true, scale all outgoing transitions from a state by
            amount coming in.
        normalise : bool, default True
            If true, normalise all transitions from a state by their sum1~
    Returns
    -------
        None
    """ # noqa

    muB_au = 2.127191057440e-6 # Eh/Tesla
    ge = 2.00231930436182
    au2cm = 2.1947463e5

    #get data from rassi.h5 file
    angm = make_molcas_extractor(h5name, ("rassi", "SFS_angmom"))[()]  # get L = -i r x nabla (Hermitian)
    ener = make_molcas_extractor(h5name, ("rassi", "SFS_energies"))[()]
    amfi = make_molcas_extractor(h5name, ("rassi", "SFS_AMFIint"))[()]
    spin_mult = make_molcas_extractor(h5name, ("rassi", "spin_mult"))[()]

    # spin-free energies; reference to ground state of lowest multiplicity
    sf_ener = list(extract_blocks(ener, spin_mult))

    # build required operators
    ops = {
        'sf_angm': list(extract_blocks(angm, spin_mult, spin_mult)),
        'sf_mch': list(map(lambda e: np.diag(e - sf_ener[0][0]), sf_ener)),
        'sf_amfi': list(map(list, dissect_array(amfi, spin_mult, spin_mult))),
    }
    sf_mult = dict(zip(*np.unique(spin_mult, return_counts=True)))
    smult = np.repeat(list(sf_mult.keys()), list(sf_mult.values()))
    ws_angm = sf2ws(ops['sf_angm'], sf_mult)
    ws_spin = np.array(make_angmom_ops_from_mult(smult)[0:3])
    ws_mch = sf2ws(ops['sf_mch'], sf_mult)
    ws_amfi = sf2ws_amfi(ops['sf_amfi'], sf_mult)

    if num_states is None:
        num_states = ws_amfi.shape[0]

    #if magnetic field not specified, find prinipal axis and set 25 uT field along it
    if Zeeman is None:
        ws_hamiltonian = ws_mch + ws_amfi
        so_eig, so_vec = jnp.linalg.eigh(ws_hamiltonian)
        so_spin = unitary_transform(ws_spin, so_vec)
        so_angmom = unitary_transform(ws_angm, so_vec)
        gtensors = compute_eprg_tensors(so_spin, so_angmom, ener=so_eig)
        gvals, frames = zip(*map(np.linalg.eigh, gtensors))
        gnd_g = np.sqrt(gvals[0])
        Zeeman = (25e-6)*frames[0][:,gnd_g.argmax()]

    # add magnetic field and obtain eigenstates
    ws_zee = np.zeros(ws_mch.shape)
    for axis, field in enumerate(Zeeman):
        ws_zee += muB_au * field * (ws_angm[axis] + ge*ws_spin[axis])
    ws_hamiltonian = ws_mch + ws_amfi + ws_zee
    so_eig, so_vec = jnp.linalg.eigh(ws_hamiltonian)
    so_spin = unitary_transform(ws_spin, so_vec)
    so_angmom = unitary_transform(ws_angm, so_vec)
    tot_val = (so_eig - so_eig[0])*au2cm

    # get expectation of J along quantisation axis and magnetic moment matrices including two perpendicular axes
    Zee_length = np.sqrt(Zeeman[0]**2 + Zeeman[1]**2 + Zeeman[2]**2)
    Jz = (1.0/Zee_length)*(Zeeman[0]*(so_spin[0,:,:]+so_angmom[0,:,:]) + Zeeman[1]*(so_spin[1,:,:]+so_angmom[1,:,:]) + Zeeman[2]*(so_spin[2,:,:]+so_angmom[2,:,:]))
    Jz = np.real(np.diag(Jz))
    MuZ = muB_au * (1.0/Zee_length)*(Zeeman[0]*(ge*so_spin[0,:,:]+so_angmom[0,:,:]) + Zeeman[1]*(ge*so_spin[1,:,:]+so_angmom[1,:,:]) + Zeeman[2]*(ge*so_spin[2,:,:]+so_angmom[2,:,:]))
    VecX = [0.0, 0.0, 0.0]
    VecY = [0.0, 0.0, 0.0]
    if Zeeman[2] != 0.0:
        VecX[0] = 1.0
        VecX[1] = 1.0
        VecX[2] = (-Zeeman[0]-Zeeman[1])/Zeeman[2]
    else:
        VecX[0] = 0.0
        VecX[1] = 0.0
        VecX[2] = 1.0
    VecX_length = np.sqrt(VecX[0]**2 + VecX[1]**2 + VecX[2]**2)
    VecY[0] = VecX[1]*Zeeman[2] - VecX[2]*Zeeman[1]
    VecY[1] = VecX[2]*Zeeman[0] - VecX[0]*Zeeman[2]
    VecY[2] = VecX[0]*Zeeman[1] - VecX[1]*Zeeman[0]
    VecY = VecY/Zee_length
    VecY_length = np.sqrt(VecY[0]**2 + VecY[1]**2 + VecY[2]**2)
    MuX = (1.0/VecX_length)*(VecX[0]*(ge*so_spin[0,:,:]+so_angmom[0,:,:]) + VecX[1]*(ge*so_spin[1,:,:]+so_angmom[1,:,:]) + VecX[2]*(ge*so_spin[2,:,:]+so_angmom[2,:,:]))
    MuY = (1.0/VecY_length)*(VecY[0]*(ge*so_spin[0,:,:]+so_angmom[0,:,:]) + VecY[1]*(ge*so_spin[1,:,:]+so_angmom[1,:,:]) + VecY[2]*(ge*so_spin[2,:,:]+so_angmom[2,:,:]))

    # Overall transition probabilties as average of each dipole moment squared
    trans = (np.abs(MuX) ** 2 + np.abs(MuY) ** 2 + np.abs(MuZ) ** 2) * 1. / 3.

    # Create barrier figure
    barrier_figure(
        num_states,
        tot_val[0:num_states],
        Jz[0:num_states],
        trans=trans[0:num_states,0:num_states],
        show=show,
        save=save,
        save_name=save_name,
        trans_colour=trans_colour,
        state_colour=state_colour,
        yax2=yax2,
        yax2_conv=yax2_conv,
        yax2_label=yax2_label,
        ylabel=ylabel,
        xlabel=xlabel,
        allowed_trans=allowed_trans,
        scale_trans=scale_trans,
        normalise_trans=normalise_trans
    )

    if save and verbose:
        print(
            "Barrier figure saved to {} in ".format(save_name) +
            "execution directory"
        )

    # Create output datafile

    if print_datafile:
        with open("barrier_data.dat", "w") as df:

            df.write("Barrier figure data for {}\n".format(h5name))
            df.write("\n")

            df.write("Energies with Zeeman term (cm^-1)\n")
            df.write("------------------------------------------------\n")
            for i in range(num_states):
                df.write("{:14.7f}\n".format(tot_val[i]))

            df.write("\n")

            df.write("Jz expectation values with Zeeman term:\n")
            df.write("---------------------------------------\n")
            for i in range(num_states):
                df.write("{: .7f}\n".format(Jz[i]))

    if verbose:
        print("Datafile saved to barrier_data.dat in execution directory")

    return

def _evolve_trans_mat(n_states, Jz_expect, trans, allowed_trans="forwards",
                      scale_trans=True, normalise=True):
    """
    Scales transition matrix by "amount" coming into each state
    and removes backwards or downwards transitions

    Parameters
    ----------
    n_states : int
        Number of states
    Jz_expect : np.ndarray
        1D array of <Jz> in eigenbasis of HCF
    trans : np.ndarray
        Matrix representation of magnetic transition dipole moment
        operator
    allowed_trans : str {'forwards','all'}
        Which transitions should be plotted:
            forwards: Only those which move up and over barrier
            all : All transitions
    scale_trans : bool, default True
        If true, scale all outgoing transitions from a state by
        amount coming in.
    normalise : bool, default True
        If true, normalise all transitions from a state by their sum

    Returns
    -------
    np.ndarray
        Matrix representation of magnetic transition dipole moment
        operator after scaling
    """

    # Remove self transitions
    np.fill_diagonal(trans, 0.)

    # Remove all transitions backwards over the barrier
    # or downwards between states
    if allowed_trans == "forwards":
        for i in range(n_states):  # from
            for f in range(n_states):  # to
                if Jz_expect[i] > Jz_expect[f]:
                    trans[f, i] = 0.  # No backwards or downwards steps

    # Normalise each column so transition probability is a fraction of 1
    if normalise:
        for i in range(n_states):
            total = 0.
            total = sum(trans[:, i])
            if total > 0.:
                trans[:, i] = trans[:, i] / total

    # Find indexing which relates the current arrrangement of the array
    # Jz_expect to the arrangement it would
    # have if it was written in descending order (largest first)
    # This is done because our pathway consists only of transitions which
    # increase (-ve to eventually +ve) <Jz>
    index = Jz_expect.argsort()

    # Scale transition probability by amount coming into each state
    # Assume unit "population" of ground state (Jz=-J)
    # i.e. trans[:,index[0]] is already 1
    if scale_trans:
        for ind in index:
            if ind == 0:
                continue
            else:
                # scale outward by inward
                trans[:, ind] *= np.sum(trans[ind, :])

    # Scale matrix to be a percentage
    trans = 100. * trans

    # Find transitions with >1% probability
    # write their indices to an array along with the probabilty as a decimal
    # this is used to set the transparency of the arrows on the plot
    num_trans = 0
    output_trans = []
    for row in range(n_states):
        for col in range(n_states):
            if trans[row, col] > 1.:
                alpha = float(trans[row, col] / 100.0)
                if alpha > 1.:
                    alpha = 1.
                output_trans.append([row, col, alpha])
                num_trans += 1

    return output_trans, num_trans


def barrier_figure(n_states, energies, Jz_expect, trans=False, ax_in=False,
                   trans_colour="#ff0000", state_colour="black",
                   yax2=False, yax2_conv=1.4, figsize=[7, 5.5],
                   show=False, save=True, save_name="barrier.pdf",
                   scale_trans=True, allowed_trans="forwards",
                   normalise_trans=True, levels_name="",
                   xlabel=r"$\langle \ \hat{J}_{z} \ \rangle$",
                   ylabel=r"Energy (cm$^{-1}$)", yax2_label="Energy (K)"):
    """
    Plots barrier figure with transition intensities from user provided matrix
    Y axis is Energy in cm-1, x axis is <Jz> of each state
    Arrows are transitions with intensity specified by specified by trans array

    Parameters
    ----------
    n_states : int
        Number of states
    energies : array_like
        List of state energies
    Jz_expect : array_like
        List of <Jz> for each state
    trans : np.ndarray
        Matrix of transition probabilities between states
    ax_in : pyplot axis object
        Axis to use for plot
    trans_colour : str, default "#ff0000" (red)
        Hex code or name specifying arrow colours
    state_colour : str, default "black"
        Hex code or name specifying state colours
    yax2 : bool, default True
        If True use secondary y (energy) axis
    yax2_conv : float, default 1.4 (cm-1 --> K)
        conversion factor from primary to secondary y axis
    figsize : array_like, default [7, 5.5]
        Size of figure [width, height] in inches
    show : bool, default False
        If True, show plot on screen - disabled with ax_in
    save : bool, default True
        If True, save plot to file - disabled with ax_in
    save_name : str, default "barrier.pdf"
        Filename for saved image
    allowed_trans : str {'forwards','all'}
        Which transitions should be plotted:
            forwards: Only those which move up and over barrier
            all : All transitions
    normalise_trans : bool, default True
        If True, normalise all transitions out of a state by their sum
    scale_trans : bool, default True
        If true, scale all outgoing transitions from a state by amount
        coming in.
    levels_name : str, default ""
        Legend label name for energy levels
    xlabel : str, default "hat{J}_z"
        Plot x label
    ylabel : str, default "Energy (cm-1)"
        Plot y label
    yax2_label : str, default "Energy (K)"
        Label for secondary y (energy) axis

    Returns
    -------
    pyplot figure object
        Figure window handle
    pyplot axis object
        Axes for current plot
    """

    # Set font size
    plt.rcParams.update({'font.size': 18})

    # Create plot and axes
    if not ax_in:
        fig, ax = plt.subplots(1, 1, sharey='all', figsize=figsize)
    else:
        fig = None
        ax = ax_in

    if yax2:
        ax2 = ax.twinx()
        axes = [ax, ax2]
    else:
        axes = [ax]

    # Draw energy level lines
    ax.plot(
        Jz_expect,
        energies,
        marker='_',
        markersize='25',
        mew='2.5',
        linewidth=0,
        color=state_colour,
        label=levels_name
    )

    # Plot transition arrows
    if isinstance(trans, np.ndarray):

        # Evolve transition matrix and find allowed transitions
        output_trans, num_trans = _evolve_trans_mat(
            n_states,
            Jz_expect,
            trans,
            allowed_trans=allowed_trans,
            normalise=normalise_trans,
            scale_trans=scale_trans
        )

        np.savetxt("inputtrans.dat", trans)
        np.savetxt("outputtrans.dat", output_trans)

        # Final <Jz>
        Jz_expect_final = [
            Jz_expect[output_trans[row][1]]
            for row in range(num_trans)
        ]

        # Difference between initial and final <Jz>
        Jz_expect_diff = [
            Jz_expect[output_trans[row][0]]-Jz_expect[output_trans[row][1]]
            for row in range(num_trans)
        ]

        # Final energies
        energies_final = [
            energies[output_trans[row][1]]
            for row in range(num_trans)
        ]

        # Difference between initial and final energies
        energies_diff = [
            energies[output_trans[row][0]] - energies[output_trans[row][1]]
            for row in range(num_trans)
        ]

        # Alpha channel values
        alphas = [output_trans[row][2] for row in range(num_trans)]

        # Make colours array
        # Columns are red, green, blue, alpha
        t_rgba_colors = np.zeros((num_trans, 4))

        # Convert user hex to rgb
        if trans_colour != "None":
            t_rgba_colors[:, 0:3] = ut.hex_to_rgb(trans_colour)
            t_rgba_colors[:, 3] = np.asarray(alphas)
        else:
            t_rgba_colors[:, 0:3] = ut.hex_to_rgb("#ff0000")
            t_rgba_colors[:, 3] = 0.0


        # Draw lines between levels
        ax.quiver(
            Jz_expect_final,
            energies_final,
            Jz_expect_diff,
            energies_diff,
            scale_units='xy',
            angles='xy',
            scale=1,
            color=t_rgba_colors
        )

    # Set x axis options
    ax.set_xlabel(xlabel)
    ax.tick_params(axis='both', which='both', length=2.0)
    ax.xaxis.set_major_locator(plt.MaxNLocator(8))

    # Set y axis options for cm-1
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_locator(plt.MaxNLocator(7))

    # Set y axis options for K
    if yax2:
        ax2.set_ylabel(yax2_label)
        ax2.set_ylim(
            ax.get_ylim()[0] * yax2_conv,
            ax.get_ylim()[1] * yax2_conv
        )
        ax2.yaxis.set_major_locator(plt.MaxNLocator(7))

    # Set axis limits
    ax.set_xlim([np.min(Jz_expect) * 1.1, np.max(Jz_expect) * 1.1])

    # Set number and position of x axis ticks
    limit = max(abs(int(np.min(Jz_expect))),int(np.max(Jz_expect)))
    ax.set_xticks(np.arange(-limit-1, limit+2, 1))

    # Set x axis tick labels
    labels = []

    # Set lables
    for it in np.arange(-limit-1, limit+2, 1):
        labels.append(str(it))

    ax.set_xticklabels(labels, rotation=45)

    if not ax_in:
        fig.tight_layout()
        # Save or show plot
        if save:
            fig.savefig(save_name, dpi=500)
        if show:
            plt.show()

    return fig, axes
