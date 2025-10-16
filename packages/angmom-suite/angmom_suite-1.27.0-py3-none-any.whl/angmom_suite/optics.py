import sys
import numpy as np
import jax.numpy as jnp
import pandas as pd
import h5py
from molcas_suite.extractor import make_extractor as make_molcas_extractor
from .basis import sf2ws, sf2ws_amfi, unitary_transform, \
    dissect_array, extract_blocks, make_angmom_ops_from_mult


np.set_printoptions(precision=17)


def optics(h5name, property, orientation, states, degeneracy, Zeeman):
    """
    Core code, execute other defined functions to evaluate the optical properties requested.

    Args:
        h5name (str): name of the rassi HDF5 file from which the electronic quantum information is extracted
        property (str): evaluated property which can be either luminescence, absorption, CPL or CD
        orientation (str): feature not yet available, but slightly present in code for future improvement
        states (int): integer value identifying the restricted states for which transitions are evaluated
        degeneracy (float): cut-off energy (eV) to distinguish degenerate states

    Returns:
        None
    """

    ESO, EDxyzSO, MDxyzSO = transition_moments_SO(h5name, Zeeman)
    fEDl, fMD = oscilator_strengths(ESO, EDxyzSO, MDxyzSO)
    if property == 'hdf5':
        write_optics_hdf5(ESO, EDxyzSO, MDxyzSO)
    elif property in ['abs', 'lum']:
        Bed, Bmd, Btot = Einstein_coefficients(orientation, ESO, EDxyzSO, MDxyzSO)
        print_data(property, states, degeneracy, ESO, Btot, Bed, Bmd, fEDl, fMD)
    elif property in ['cd', 'cpl']:
        R, ed2, md2 = cpl(orientation, ESO, EDxyzSO, MDxyzSO)
        print_data(property, states, degeneracy, ESO, R, ed2, md2, fEDl, fMD)

    return None

### Unitary transformation for energies
au2ev = 2.7211386021e1
au2cm = 2.1947463e5
ev2au = (1.0 / au2ev)
ev2cm = 8065.02
au2si = 4.359744722206048e-18 # J
    
### Physical constants
ge = 2.00231930436182
muB_au = 2.127191057440e-6 # Eh/Tesla
ge = 2.00231930436182
hPlanck = 4.135667516e-15  # Planck's constant in eV.s
celerity = 299792458  # speed of the ligth in m/s
c_au = 137.035999084  # 1/fine_structure_constant  which is also the speed of ligth in au units
alpha = 0.0072973525693  # fine_structure_constant which is e**2/(4pi epsilon0 hbar c) in SI units or e**2/(hbar c) in CGS units
magic_alpha = 471.44364  # it is actually 10**-40 erg-esu-cm/Gauss
# i.e. numerically: au2erg * e_cgs_esu * ao / au2standard_magnetic_field * 1e40

# Other physical constants in cgs units
ao_cgs = 5.29177210903e-9  # cm
d_au2cgs = 6.46047500576e-36  # (hbar * e)**2 / (me * E)
hbar_cgs = 1.054571817e-27  # erg.s
e_cgs_esu = 4.80320427e-10  # Fr = statC
me_cgs = 9.1093837015e-28  # g
c_cgs = 2.99792458e10  # cm/s
muB_cgs_esu = 2.780278273e-10 # Fr.cm**2 / s = statA.cm**2
muB_cgs_emu = 9.274010078328e-21 # erg/gauss
au2erg = 4.3597440000000005e-11
au2gauss_cgs = 1.72e7 # e/(ao**2 * c) 
au2gauss_SI = 2.35e9 # hbar/(ao**2 * e)

# Other physical constants in SI units
ao = 5.2917721054482e-11  # m
hbar = 6.582119569e-16  # eV.s
hbar_si = 1.054571817e-34 # J.s
e_si = 1.602176634e-19  # C = A.s
me_si = 9.109383713928e-31  # kg
muB_si = 9.274010065729e-24  # J/T  = m2.A
vac_permittivity_si = 8.854187818814e-12  # F/m = kg-1.m-3.s4.A2
vac_permeability_si = 1.2566370612720e-6  # N.A-2 = kg.m.s-2.A-2
au2gauss_SI = 2.35e9 # hbar/(ao**2 * e)
d_au2si = (hbar_si * e_si)**2 / (me_si * au2si)


def transition_moments_SO(h5name, Zeeman):
    """ 
    In the spin-orbit state-basis, collect all the transition moments required to compute optical poperties;
    that is the electric dipoles (ED) and magnetic dipoles (MD) transition moments 
    as well as the energies of the states.

    Parameters
    ----------
        h5name : str
            name of rassi HDF5 file

    Returns
    -------
        ESO : list of float [nSO]
            energies of the SO states
        EDxyzSO : complex matrix [3,nSO,nSO]
            3 matrices of the EDTM along x, y and z-axis respectively in the SO-basis in the length representation
        MDxyzSO : complex matrix [3,nSO,nSO]
            3 matrices of the MDTM along x, y and z-axis respectively in the SO-basis
    """

    angm = make_molcas_extractor(h5name, ("rassi", "SFS_angmom"))[()]  # get L = -i r x nabla (Hermitian)
    ener = make_molcas_extractor(h5name, ("rassi", "SFS_energies"))[()]
    amfi = make_molcas_extractor(h5name, ("rassi", "SFS_AMFIint"))[()]
    edipmom = make_molcas_extractor(h5name, ("rassi", "SFS_edipmom"))[()]  # get -r
    spin_mult = make_molcas_extractor(h5name, ("rassi", "spin_mult"))[()]
    # spin-free energies; reference to ground state of lowest multiplicity
    sf_ener = list(extract_blocks(ener, spin_mult))
    ops = {
        'sf_angm': list(extract_blocks(angm, spin_mult, spin_mult)),
        'sf_mch': list(map(lambda e: np.diag(e - sf_ener[0][0]), sf_ener)),
        'sf_amfi': list(map(list, dissect_array(amfi, spin_mult, spin_mult))),
        'sf_edipmom': list(extract_blocks(edipmom, spin_mult, spin_mult))
    }
    sf_mult = dict(zip(*np.unique(spin_mult, return_counts=True)))
    smult = np.repeat(list(sf_mult.keys()), list(sf_mult.values()))
    ws_angm = sf2ws(ops['sf_angm'], sf_mult)
    ws_spin = np.array(make_angmom_ops_from_mult(smult)[0:3])
    ws_mch = sf2ws(ops['sf_mch'], sf_mult)
    ws_amfi = sf2ws_amfi(ops['sf_amfi'], sf_mult)
    ws_edipmom = sf2ws(ops['sf_edipmom'], sf_mult)
    
    ### optional magnetic field to define eigenstates
    if Zeeman != None:
        Bfield = [Zeeman[0], Zeeman[1], Zeeman[2]]
        ws_zee = np.zeros(ws_mch.shape)
        for axis, field in enumerate(Bfield):
            ws_zee += muB_au * field * (ws_angm[axis] + ge*ws_spin[axis])
        ws_hamiltonian = ws_mch + ws_amfi + ws_zee
        print(f'a Zeeman splitting is considered with an external magnetic field of {Zeeman} T')
    
    else:
        ws_hamiltonian = ws_mch + ws_amfi
    so_eig, so_vec = jnp.linalg.eigh(ws_hamiltonian)
    so_spin = unitary_transform(ws_spin, so_vec)
    so_angmom = unitary_transform(ws_angm, so_vec)
    so_edipmom = unitary_transform(ws_edipmom, so_vec)

    ### calculation of the transition moments in a.u. units 
    MDxyzSO = -0.5 * np.array([(so_angmom[0] + ge*so_spin[0]), so_angmom[1] + ge*so_spin[1], so_angmom[2] + ge*so_spin[2]])
    EDxyzSO = np.array([so_edipmom[0], so_edipmom[1], so_edipmom[2]])

    # so_eig corresponds to SO state energy in Hartree

    return so_eig, EDxyzSO, MDxyzSO


def oscilator_strengths(En, EDTM, MDTM):
    """
    Calculate the oscilator strength from the transition moments (TM).

    Args:
        En : [float]
            SO state energy in Hartree
        EDTM : [int, float, float]
            electric dipole transition moment tensor in a.u. units
            (!) ED is in length representation
        MDTM : [int, float, float]
            electric dipole transition moment tensor in a.u. units

    Returns:
        fEDl, fMD : [float, float]
            oscilator strengths
    """
    
    ### Number of states implied in the calculations
    nSO = En.size
    # print("Number of spin-orbit coupled state =", nSO)

    ### Calculations of the oscilators strengths
    fEDl = np.zeros([nSO,nSO])
    fMD = np.zeros([nSO,nSO])
    for i in range(0,nSO):
        for j in range(i+1,nSO):  # if we assume that the state j is always higher in energy than i = it is a matter of reading the results
            for k in range(0,3):
                # Eq. 19 of DeBeer George, S. et. al. Inorganica Chimica Acta 361, 965–972 (2008)
                fEDl[i][j] += (2.0 / 3.0) * abs(En[j] - En[i]) * (EDTM[k][i][j] * EDTM[k][i][j].conjugate()).real
                # Eq. 20 of DeBeer George, S. et. al. Inorganica Chimica Acta 361, 965–972 (2008)
                fMD[i][j] += ((2.0 * abs(En[j] - En[i])) / 3.0) * (alpha** 2) * (MDTM[k][i][j] * MDTM[k][i][j].conjugate()).real
    
    return fEDl, fMD


def cpl(orientation, En, EDTM, MDTM):
    """ 
    Evaluate the CPL or the CD property.

    Parameters
    ----------
        orientation : str
            feature not yet availabe;
            values = iso, x, y, z; only isotropic evaluation is currently possible
        En : [float]
            SO state energy in a.u.
        EDTM : [int, float, float]
            electric dipole transition moment tensor in a.u. units
        MDTM : [int, float, float]
            magnetic dipole transition moment tensor in a.u. units

    Returns
    -------
        R_cgs, m2ed, m2md : [float, float]
            rotatory strength, squared value of the EDTM and of the MDTM in cgs units

    """

    ### Number of states implied in the calculations
    nSO = En.size
    # print("Number of spin-orbit coupled state =", nSO)
    
    ### CPL or CD evaluation
    if orientation == 'iso':

        ### Calculation of the rotatory strength in the isotropic case
        # R(i->j) = Im[<i|ED|f><f|MD|i>] according to Eq 5.2.28a of Barron, L. D. Molecular Light Scattering and Optical Activity. (Cambridge University Press, 2004).
        # NB: only make sense for j>i, so only a triangular matrix is constructed
        # otherwise, to have a symmetric R matrix, hence we can add * np.sign(j - i)
        R_au = np.zeros([nSO,nSO])
        for i in range(0,nSO):
            for j in range(i+1,nSO):
                for k in range(0,3):
                    R_au[i][j] += (EDTM[k][i][j] * MDTM[k][i][j].conjugate()).imag
        R_cgs = R_au * magic_alpha * 10 ** (-40)

    elif orientation == 'x' or orientation == 'y' or orientation == 'z':  # TODO
        print('(x) sorry this evaluation is not yet available')
        sys.exit()
        
    ### Squared value of the EDTM and MDTM in cgs units
    m2ed = np.zeros([nSO,nSO])
    m2md = np.zeros([nSO,nSO])
    for i in range(0,nSO):
        for j in range(i+1,nSO):  #if we assume that the state j is always higher in energy than i = it is a matter of reading the results
            for k in range(0,3):
                
                m2ed[i][j] += (EDTM[k][i][j] * EDTM[k][i][j].conjugate()).real
                m2md[i][j] += (MDTM[k][i][j] * MDTM[k][i][j].conjugate()).real
                
                # alternative way to evaluate the TM from the oscilator strength
                # #Eq. 19 of DeBeer George, S. et. al. Inorganica Chimica Acta 361, 965–972 (2008)
                # m2med[i][j] = (3 * fEDl[i][j]) / (2 * abs(En[j] - En[i]))
                # #Eq. 20 of DeBeer George, S. et. al. Inorganica Chimica Acta 361, 965–972 (2008)
                # m2md[i][j] = (3 * fMD[i][j]) / (2 * abs(En[j] - En[i]))
                
    # EDTM
    m2ed = m2ed * (ao_cgs * e_cgs_esu)**2
    
    # MDTM
    m2md = m2md * (muB_cgs_emu * 2)**2  # the factor 1/2 of muB has been counted in a.u. evaluation of MDTM above
    # m2md = m2md * (hbar_cgs * e_cgs_esu / (me_cgs * c_cgs))**2
        
    return R_cgs, m2ed, m2md


def Einstein_coefficients(orientation, En, EDTM, MDTM):
    """
    Evaluate the electric and magnetic B Einstein coefficients.

    Args:
        orientation : str
            feature not yet availabe;
            values = iso, x, y, z; only isotropic evaluation is currently possible
        En : [float]
            SO state energy in a.u.
        EDTM : [int, float, float]
            electric dipole transition moment tensor in a.u. units
        MDTM : [int, float, float]
            magnetic dipole transition moment tensor in a.u. units

    Returns:
        Bed, Bmd, Btot : [float, float]
            electric dipole, magnetic dipole and summation of both, Einstein coefficient
    """
    
    ### Number of states implied in the calculations
    nSO = En.size
    
    ### Axis along which the property is evaluated TODO
    # if orientation == 'iso':
    axis = [0,1,2]
    # elif orientation == 'x':
    #     axis = [0]
    # elif orientation == 'y':
    #     axis = [1]
    # elif orientation == 'z':
    #     axis = [2]
    
    ### B Einstein coefficients
    Bed = np.zeros([nSO,nSO])
    Bmd = np.zeros([nSO,nSO])
    
    ### Squared of the TMs in a.u.
    for i in range(0,nSO):
        for j in range(i+1,nSO):  #if we assume that the state j is always higher in energy than i = it is a matter of reading the results
            for k in axis:
                Bed[i][j] += (EDTM[k][i][j] * EDTM[k][i][j].conjugate()).real
                Bmd[i][j] += (MDTM[k][i][j] * MDTM[k][i][j].conjugate()).real
    
    ### TMs in SI
    # EDTM
    Bed = Bed * (ao * e_si)**2
    # MDTM without celerity in the def of the magnetic dipole operator = in SI
    Bmd = Bmd * (muB_si * 2)**2
    
    ### calculations of the B Einstein coefficients
    # Einstein_si = (2.0 * np.pi) / (3.0 * hbar_si ** 2 * celerity ** 2)  # B in m/J; Kragskow, J. G. C. et al. Nat. Commun. 13, 825 (2022)
    # Einstein_si = (2.0 * np.pi) / (3.0 * hbar_si ** 2 * celerity)  # Mihalas
    Einstein_si = (np.pi) / (3.0 * hbar_si ** 2)  # Einstein (B in m3/(Js2))
    #Eq. 13 of 1. Kragskow, J. G. C. et al. Nat. Commun. 13, 825 (2022)
    Bed = Bed * Einstein_si / vac_permittivity_si
    #Eq. 12 of 1. Kragskow, J. G. C. et al. Nat. Commun. 13, 825 (2022)
    Bmd = Bmd * Einstein_si * vac_permeability_si
    # total Einstein coeff
    Btot = Bed + Bmd
    
    # ### Cross section
    # sigma = np.zeros([nSO,nSO])
    # for i in range(0,nSO):
    #     for j in range(i+1,nSO):
    #         sigma[i][j] = (Bed[i][j] + Bmd[i][j]) * abs(En[j] - En[i]) * au2si / celerity
    
    # ### molar absorption coefficient in M−1.cm−1
    # Na =  6.02214076e23
    # # print(np.log(10) *1e3 / Na)
    # eps = Na / (np.log(10) * 1e3) * sigma * 1e4
    
    return  Bed, Bmd, Btot


def print_data(property, states, degeneracy, En, prop, med, mmd, fed, fmd):
    """ 
    Print the evaluated optical properties and saved them in a text file.
    
    The programme is written primarily in terms of absorption properties;
    emission properties are calculated by transposing the key matrices.

    Parameters
    ----------
        property : str
            type of property under investigation
            values = abs, lum, cd, cpl
        
        states : int, int, int
            specify the states for which the chiroptical properties are to be calculated
            take 3 int corresponding to:
                the reference state, either emitting or absorbing
                the lowest and highest states, which form the range between which the transitions are evaluated
            (!) Note that the lowest state is 0
            by default, all transitions are calculated (which can be a lot).
       
        degeneracy : float
            allow to consider the degeneracy of the states implied in the transitions and sum the results accordingly.
            by default, the programme does not take this into account, in order to give the user more flexibility in handling the data,
            although it is mandatory to consider it for physical interpretation
            if the argument is switched on, a default threshold of 1e-5 eV is considered, but the user can set a different value.
        
        En : [float]
            list of energy of the states in a.u.
        
        prop : [float, float]
            key physical values for the property under investigation, 
            that is rotatory strength in cgs if evaluation of CD or CPL;
            total Einstein coeff. if evaluation of absortion or luminescence
        
        med, mmd : [float, float]
            either squared of the transition dipole in cgs unit for CD and CPL
            or electric and magnetic B Einstein coefficient in m3/(J.s2)
        
        fed, fmd : [float, float]
            electric and magnetic dipole oscilator strength, respectively
            
    Returns
    -------
        None

    """
    

    ####################################
    ###   Printing out of the data   ###
    ####################################

    if property in ['abs','lum']:
        var = ["Btot(m3/Js2)", "Bed(m3/Js2)", "Bmd(m3/Js2)"]  # def Einstein
    elif property in ['cd','cpl']:
        var = ["R (cgs)", "ED2 (cgs)", "MD2 (cgs)"]
    dict_key = ["from", "to", "E(eV)", "E(cm-1)"] + var + ["fED", "fMD"]
    df = {key:[] for key in dict_key}
  
    ### Number of spin-orbit states
    nSO = En.size
    
    emission = ['cpl', 'lum']
    absorption = ['cd', 'abs']

    if property in emission:
        
        # to deal with emission properties
        prop = prop.transpose() 
        med = med.transpose()
        mmd = mmd.transpose()
        fed = fed.transpose()
        fmd = fmd.transpose()
        
        # specify the states
        if states != None: 
            refState = states[0]
            lowState = states[1]
            highState = states[2]
            stopState = refState 
            if refState < highState :
                sys.exit(f'(x) the specified states are wrong, state {refState} cannot emit to states {lowState} - {highState}.')
            elif lowState > highState :
                sys.exit(f'(x) the ordering of states is wrong, state {lowState} need to be lower than {highState}.')
        else:
            refState = 1 
            lowState = 0
            highState = refState
            stopState = nSO - 1 #all the transtions will be calculated
    

    elif property in absorption:

        # specify the states
        if states != None:
            refState = states[0]
            lowState = states[1]
            highState = states[2]
            stopState = refState
            if refState > lowState :
                sys.exit(f'(x) the specified states are wrong, state {refState} cannot absorb to states {lowState} - {highState}.')
            elif lowState > highState :
                sys.exit(f'(x) the ordering of states is wrong, state {lowState} need to be lower than {highState}.')
        else:
            refState = 0
            lowState = 1
            highState = nSO -1
            stopState = highState #all the transtions will be calculated

    else:
        print('(x) problem with the property keyword')
        sys.exit()


    state_degenated = False
    num_level = -1  # count the number of states which are not degenerated
    ldegenlevel = []  # store temporaly the level number of degenerate states
    ldegendonor = []  # store temporaly the level number of the absorbing/emitting states
    degendonor = 1
    strdonor : str


    for i in range(refState, stopState+1):

        if degeneracy != 0.0 :
            for k in range(0, nSO):
                if (au2ev * abs(En[k] - En[i])) < degeneracy:
                    ldegendonor.append(k)
            
            if states == None:
                degendonor = 1
                strdonor = f'{i}'
                if i != min(ldegendonor):
                    print(f'(!) note that state {max(ldegendonor)} is degenerated with {min(ldegendonor)}') # and that is not considered in the \'from state\'')
                
            else: # states != None
                degendonor = len(ldegendonor) # should be always done for i = donor_state
                strdonor = f'{min(ldegendonor)}-{max(ldegendonor)}'
                print(f'degeneracy of the reference state {refState} is ', degendonor, '(which is included in the calculations)')
                
                # verify the limit set by the user
                ldegendonor = []
                for k in range(0, nSO):
                    if (au2ev * abs(En[k] - En[lowState])) < degeneracy and k < lowState :
                        ldegendonor.append(k)
                        print(f'(!) please consider another lower state than {lowState} in your evaluation:')
                    elif (au2ev * abs(En[k] - En[highState])) < degeneracy and k > highState :
                        ldegendonor.append(k)
                        print(f'(!) please consider another higher state than {highState} in your evaluation:')
                    else:
                        continue
                if len(ldegendonor) != 0:
                    print('(!) degeneracy is evaluated as the best as possible,\n(!) but the range chosen does not allow it to be properly taken into account.')
            
        else :
            strdonor = f'{i}'
            degendonor = 1

        # degeneracy of the donor state implies :
        prop *= degendonor
        med *= degendonor
        mmd *= degendonor
        fed *= degendonor
        fmd *= degendonor
        # /!\ please note that is only considering when a specific state is chosen as a ref.
        # otherwise degendonor always equals 0

        for f in range(lowState, highState+1):

            if f in ldegendonor:
                # do nothing
                # print('no evaluation for', i, f)
                continue
            else:

                if degeneracy != 0.0 and f > lowState and (En[f] - En[f-1])*au2ev < degeneracy:
                    state_degenated = True
                    ldegenlevel.append(f)
                    df['to'][num_level] = f'{min(ldegenlevel)}-{max(ldegenlevel)}'
                    E_au = abs(np.mean(En[min(ldegenlevel):max(ldegenlevel)+1]) - En[i]) #transition energy
                    df['E(eV)'][num_level] = E_au * au2ev
                    df['E(cm-1)'][num_level] = E_au * au2cm
                    if states != None:
                        print(f'state {max(ldegenlevel)} is degenerated with {min(ldegenlevel)}')

                else:
                    state_degenated = False
                    num_level += 1
                    ldegenlevel = []
                    ldegenlevel.append(f)
                    df['to'].append(f)
                    E_au = abs(En[f]-En[i]) #transition energy
                    E_ev = E_au * au2ev
                    E_cm = E_au * au2cm
                
                if state_degenated:
                    df[f'{var[0]}'][num_level] += prop[i,f]
                    df['fED'][num_level] += fed[i,f]
                    df['fMD'][num_level] += fmd[i,f]
                    df[f'{var[1]}'][num_level] += med[i,f]
                    df[f'{var[2]}'][num_level] += mmd[i,f]
                else:  
                    df['from'].append(strdonor)
                    df['E(eV)'].append(E_ev)
                    df['E(cm-1)'].append(E_cm)
                    df[f'{var[0]}'].append(prop[i,f])
                    df['fED'].append(fed[i,f])
                    df['fMD'].append(fmd[i,f])
                    df[f'{var[1]}'].append(med[i,f])
                    df[f'{var[2]}'].append(mmd[i,f])
                

        if highState != lowState:
            if property in emission:
                highState += 1
            else: #cd or abs
                lowState +=1
        ldegendonor = [] # energy level must be sorted


    ### Let's now print all the results in a table
    
    # pandas dataframe into PrettyTable
    pandf = pd.DataFrame(df)
    table_data = pandf.to_markdown(headers='keys', tablefmt='psql', index=False, stralign='center', floatfmt=(str, str, '8.5f','9.2f','.6e','.6e','.6e','.4e','.4e'))
    print(table_data)

    # save them in an output file
    if states != None:
        output = open(f'data-{property}_from{refState}to{lowState}-{highState}.txt','w+')
    else:
        output = open(f'data-{property}.txt','w+')
    output.write(table_data)
    
    # generate a table ready for a LaTeX document
    output.write('\n')
    output.write('\n+----------------------+\n')
    output.write('|   in LaTeX format:   |')
    output.write('\n+----------------------+\n')
    # output.write(pandf.to_latex(header=True, index=False, column_format='ccrrrrrrr', float_format='%.6e', caption=f'cdvvvjv {property}, with {var[0]} in ...'))
    latex_data = pandf.to_markdown(headers='keys', tablefmt='latex', index=False, stralign='center', floatfmt=(str, str, '8.5f','9.2f','.6e','.6e','.6e','.4e','.4e'))
    output.write(latex_data)
    
    # convert them into a universal format for any future treatment
    output.write('\n')
    output.write('\n+--------------------+\n')
    output.write('|   in CSV format:   |')
    output.write('\n+--------------------+\n')
    output.write(pandf.to_csv(sep=';',index=False))
    
    output.close()


    return None


def write_optics_hdf5(ESO, EDTM, MDTM):
    with h5py.File("optics.hdf5", 'w') as f:
        f.create_dataset("ESO", data=ESO, dtype=np.complex128)
        f.create_dataset("EDTM", data=EDTM, dtype=np.complex128)
        f.create_dataset("MDTM", data=MDTM, dtype=np.complex128)
