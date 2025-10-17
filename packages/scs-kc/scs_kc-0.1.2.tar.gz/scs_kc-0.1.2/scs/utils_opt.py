from scipy.optimize import brentq
import numpy as np
from scs.supercoeffs import Cnlp_sum, Cnlp, Circuit
from swg.sw_procedure import Hamiltonian
import numbers
import sympy as sp






pi=np.pi
# Ratio omega_d/omega_0 for two-photon squeezing
omega_d = 2.

model_name = 'Kerr-cat'


FINAL_MONOMS = {
    "DETUNING":          ((1,),(1,)),   
    "KERR":              ((2,),(2,)),
    "2PH_SQUEEZING":    ((2,),(0,))
}
kerr_cat_idx_arr=[]

def load_or_initialize_kerr_cat_model():
    #TODO refactor to get rid of global variable
    global kerr_cat_idx_arr;
    
    # Load if exists, otherwise generate and save through hamiltonian.build_model
    hamiltonian = Hamiltonian(f'{model_name}', 1, sw_order=1, max_order=4)
    hamiltonian.add_freqs_condition([2],[1])# the condition 2*\omega^prime=omega_d is ensured 
    kerr_cat_idx_arr =  hamiltonian.build_model(FINAL_MONOMS.values(), recalculate=False)





def effective_hamiltonian_coeff_to_latex(idx_arr, omega0sp, omegadsp):
    """
    Return representation of supercoefficients corrections for particular monomial 
    and Schrieffer-Wolff order in LaTeX format

    Parameters
    ----------
    idx_arr : list
        subarray of the model, for example, model_arr[((k1,),(k2,))][sw_order] .
    omega0sp : sympy Symbol
        symbolic notation for a fundamental frequency omega_0.
    omegadsp : Symbol or list(Symbol)
        symbolic notation for a drive frequency omega_d..

    Returns
    -------
    LaTeX formatted string of SW corrections

    """
    sympy_terms = []

    # Keep track of symbols already defined to avoid redefining
    defined_symbols = {}
    if isinstance(omegadsp, sp.Symbol):
        omegadsp = [omegadsp]
        

    for elem in idx_arr:
        # Build the factors for this term
        factors = []

        # Create or reuse symbols for each C_{n,l,p}
        for indices in elem[1:]:
            n, l = int(indices[0][0][0]), int(indices[0][0][1])
            p = indices[1]  # tuple of drive indices

            # make sure p is iterable
            if not isinstance(p, tuple):
                p = (p,)

            # compact string for latex and name
            x_str = ''.join(str(xi) for xi in p)
            name = f"C_{n}_{l}_{'_'.join(str(xi) for xi in p)}"
            latex_name = f"C_{{{n}{l},{x_str}}}"


            if name not in defined_symbols:
                defined_symbols[name] = sp.Symbol(name=latex_name)
            factors.append(defined_symbols[name])

        # Handle the function/expression
        expr = sp.simplify(elem[0](omega0sp, *omegadsp))

        factors.append(expr)
        # Multiply all factors
        term_expr = sp.Mul(*factors)
        sympy_terms.append(term_expr)

    # Sum all terms
    total_expr = sp.Add(*sympy_terms)

    # Convert to LaTeX
    latex_str = sp.latex(total_expr)
    return latex_str, total_expr

        
def effective_hamiltonian_coeff(idx_arr, model:Circuit, Pi, omega_0, omega_d):
    """
    Compute the coefficient for a given monomial of the effective Hamiltonian
    
    Parameters:
    idx_arr : list          List representing parametric amplitude in terms of supercoefficients from SW procedure
                            Each list consists of individual terms for the corrections in format:
                                [f(omega0, omega_d1, omega_d2,...), [[n1,l1,p1],[n2,l2,p2],...]], 
                                where f(...) is lambdified function representing frequency prefactor of each correction term
                                and indices [n,l,p] represent indices of Cnlp's constituting the product.  
    model : Circuit         Circuit model representing its tomology
    Pi :                    effective drive amplitudes
    phi_zpf:                zero-point flictuations of the phase
    omega_0:                quantum mode frequency
    omega_d:                drive mode frequencies
    
    Returns:
     Calculated effective Hamiltonian coefficient for though dynamic parameters
    
    """
    
    freq_values = np.concatenate((as_array(omega_0), as_array(omega_d)))

    

    res = 0.
    
    for i in range(len(idx_arr)):   
        
        for elem in idx_arr[i]:

            prefactor = elem[0](*freq_values)
            
            
            supercoeff_prod = 1.0
            for k in range(1, len(elem)):
                term = compute_cnlp(model,elem[k][0], elem[k][1], Pi)

                supercoeff_prod *= term


            res+=prefactor * supercoeff_prod

            
            
    return res


def compute_cnlp(model,mode_indices_nl, drive_indices, Pi):
    """
    
        Computes individual supercoefficients Cnlp's

    """

    n, l = mode_indices_nl[0]
    p = drive_indices[0]
    return Cnlp(model, Pi, n,l, p)
   



def eps2_order_1(model, Pi, omega_d): # eps2 second order Shriffer-Wolff corrections
    if(kerr_cat_idx_arr==[]):
        raise Exception('Model for Kerr-cat is not initialized. Call load_or_initialize_kerr_cat_model() first.')
    return effective_hamiltonian_coeff([kerr_cat_idx_arr[FINAL_MONOMS["2PH_SQUEEZING"]][1]], model, Pi, omega_d/2, omega_d)
    # eps2_2_sum = (-2*Cnlp_sum(model, Pi,0, 1, 1,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,0, 3, 0,phi_zpf_l,maxorder) 
    #               - 6*Cnlp_sum(model, Pi,0, 1, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,0, 3, 1,phi_zpf_l,maxorder) 
    #               - 6*Cnlp_sum(model, Pi,0, 1, 2,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,0, 3, 1,phi_zpf_l,maxorder)/5 
    #               - 6*Cnlp_sum(model, Pi,0, 2, 1,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,0, 4, 0,phi_zpf_l,maxorder) 
    #               - 2*Cnlp_sum(model, Pi,0, 2, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 0, 1,phi_zpf_l,maxorder) 
    #               + 2*Cnlp_sum(model, Pi,0, 2, 2,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 0, 1,phi_zpf_l,maxorder) 
    #               - Cnlp_sum(model, Pi,0, 2, 1,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 0, 2,phi_zpf_l,maxorder) 
    #               + 2*Cnlp_sum(model, Pi,0, 1, 1,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 0,phi_zpf_l,maxorder) 
    #               - 12*Cnlp_sum(model, Pi,0, 3, 1,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 0,phi_zpf_l,maxorder)
    #               - 2*Cnlp_sum(model, Pi,0, 1, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 1,phi_zpf_l,maxorder) 
    #               + 2*Cnlp_sum(model, Pi,0, 1, 2,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 1,phi_zpf_l,maxorder)/3 
    #               - 4*Cnlp_sum(model, Pi,0, 3, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 1,phi_zpf_l,maxorder))/omega_d #*[(a**+a**+)+a*a,1,maxorder) Squeezing

    # return eps2_2_sum




def kerr_order_1(model,Pi, omega_d): # K first order Shriffer-Wolff corrections
    if(kerr_cat_idx_arr==[]):
        raise Exception('Model for Kerr-cat is not initialized. Call load_or_initialize_kerr_cat_model() first.')
    # K2_sum = -(-6*Cnlp_sum(model, Pi,0, 3, 0,phi_zpf_l,maxorder)**2 - 108*Cnlp_sum(model, Pi,0, 3, 1,phi_zpf_l,maxorder)**2/5 
    #            - 36*Cnlp_sum(model, Pi,0, 4, 0,phi_zpf_l,maxorder)**2 - 6*Cnlp_sum(model, Pi,1, 1, 0,phi_zpf_l,maxorder)**2 
    #            + 4*Cnlp_sum(model, Pi,1, 1, 1,phi_zpf_l,maxorder)**2 
    #            - 12*Cnlp_sum(model, Pi,0, 2, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 2, 0,phi_zpf_l,maxorder) 
    #            - 18*Cnlp_sum(model, Pi,1, 2, 0,phi_zpf_l,maxorder)**2)/omega_d #*a**+a**+aa  Kerr
    # return K2_sum
    return -effective_hamiltonian_coeff([kerr_cat_idx_arr[FINAL_MONOMS["KERR"]][1]], model, Pi, omega_d/2, omega_d)


def detuning_order_1(model, Pi, omega_d):# detuning first order Shriffer-Wolff corrections
    if(kerr_cat_idx_arr==[]):
        raise Exception('Model for Kerr-cat is not initialized. Call load_or_initialize_kerr_cat_model() first.')
    return effective_hamiltonian_coeff([kerr_cat_idx_arr[FINAL_MONOMS["DETUNING"]][1]], model, Pi, omega_d/2, omega_d)
    # Delta_drive2_sum = (-4*Cnlp_sum(model, Pi,0, 2, 0,phi_zpf_l,maxorder)**2 
    #                     - 2*Cnlp_sum(model, Pi,0, 2, 1,phi_zpf_l,maxorder)**2 
    #                     + 8*Cnlp_sum(model, Pi,0, 2, 2,phi_zpf_l,maxorder)**2/3 
    #                     - 12*Cnlp_sum(model, Pi,0, 3, 0,phi_zpf_l,maxorder)**2
    #                     - 216*Cnlp_sum(model, Pi,0, 3, 1,phi_zpf_l,maxorder)**2/5 
    #                     - 48*Cnlp_sum(model, Pi,0, 4, 0,phi_zpf_l,maxorder)**2 
    #                     - 8*Cnlp_sum(model, Pi,0, 1, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 0,phi_zpf_l,maxorder) 
    #                     - 4*Cnlp_sum(model, Pi,1, 1, 0,phi_zpf_l,maxorder)**2 
    #                     + 16*Cnlp_sum(model, Pi,0, 1, 1,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 1, 1,phi_zpf_l,maxorder)/3 
    #                     + 8*Cnlp_sum(model, Pi,1, 1, 1,phi_zpf_l,maxorder)**2/3 
    #                     - 12*Cnlp_sum(model, Pi,0, 2, 0,phi_zpf_l,maxorder)*Cnlp_sum(model, Pi,1, 2, 0,phi_zpf_l,maxorder) 
    #                     -  6*Cnlp_sum(model, Pi,1, 2, 0,phi_zpf_l,maxorder)**2)/(omega_d) #*a**+*a Detuning
    # return Delta_drive2_sum



def calculate_omega_d(model, Pi):
    c2 = model.cn_arr[2]
    omega_0 = 2*model.phi_zpf**2*model.energy_jj*c2
    if(model.withDelta):   
        Delta_drive2_all = detuning_order_1(model,Pi, omega_d*(omega_0+Cnlp(model,Pi,1, 0, 0)))
        return omega_d*(omega_0+Cnlp(model,Pi,1, 0, 0)+Delta_drive2_all)     
    return omega_d*omega_0
   


def size_kc(model,x):
    #TODO only works with 2-node Kerr-cat

    delta=0
    n_zpf_inv = 2*model.phi_zpf
    res  = np.zeros(len(x))
    for i in range(0, len(x)):
        
        Pi=x[i]*n_zpf_inv
        if(model.withDelta):
            Delta_drive2_sum = detuning_order_1(model,Pi, calculate_omega_d(model,x))
            delta = (Cnlp(model,Pi,1, 0, 0)+Delta_drive2_sum)
        # Delta_drive2_sum = detuning_order_1(model, Pi,phi_zpf_l, omega_d*phi_zpf_l**2,maxorder)
        omega_d_l  = calculate_omega_d(model,Pi)
        K2_sum = kerr_order_1(model,Pi, omega_d_l)
        eps2_2sum = eps2_order_1(model,Pi, omega_d_l)
        res[i]=(Cnlp(model,Pi,0, 2, 1)+eps2_2sum+0.5*delta)/(-Cnlp(model,Pi,2, 0, 0)+K2_sum)
    return res


def kerr(model,x):
    """
    Calculates self-Kerr for sought circuit topology and dynamic parameters

    """

    n_zpf_inv = 2*model.phi_zpf
    res  = np.zeros(len(x))

    for i in range(0, len(x)):
        
        Pi=x[i]*n_zpf_inv
        
        omega_d_l  = calculate_omega_d(model, Pi)
        K2_sum = kerr_order_1(model,Pi, omega_d_l)
        
        res[i]=(-Cnlp(model,Pi,2, 0, 0)+K2_sum)

    
    return res




def K_approx(model,x):

    n_zpf_inv = 2*model.phi_zpf
    res  = np.zeros(len(x))
    for i in range(0, len(x)):
        Pi=x[i]*n_zpf_inv
        omega_d_l  = calculate_omega_d(model, Pi,4)        
       
        res[i]=(-Cnlp_sum(model, Pi,2, 0, 0, 4)+(6*Cnlp_sum(model, Pi,0, 3, 0,4)**2 + 6*Cnlp_sum(model, Pi,1, 1, 0,4)**2)/omega_d_l)

    return res 


def eps2(model,x):

    res  = np.zeros(len(x))
    n_zpf_inv = 2*model.phi_zpf
    for i in range(0, len(x)):
        
        Pi=x[i]*n_zpf_inv
            

        omega_d_l  = calculate_omega_d(model, Pi) 
        eps2_2sum = eps2_order_1(model, Pi, omega_d_l)
        res[i]=(Cnlp(model, Pi,0, 2, 1)+eps2_2sum)
              
    return res 

def detuning(model,x):

    delta=0
    res  = np.zeros(len(x))
    n_zpf_inv = 2*model.phi_zpf
    for i in range(0, len(x)):
        
        Pi=x[i]*n_zpf_inv
        Delta_drive2_sum = detuning_order_1(model, Pi, calculate_omega_d(model, Pi))
        delta = (Cnlp(model, Pi,1, 0, 0)+Delta_drive2_sum)        
        res[i]=delta+Delta_drive2_sum        
              
    return res

def detuning_approx(model,x):
    
    res  = np.zeros(len(x))
    n_zpf_inv = 2*model.phi_zpf
    for i in range(0, len(x)):

        Pi=x[i]*n_zpf_inv
        res[i]=Cnlp_sum(model, Pi, 1, 0, 0,4)
    return res 




############################################################
########    Optimization of Kerr-cat parameters   ##########
############################################################

def phi_ext_for_K_zero(model:Circuit, max_drive_amp, K=0):
    """
    Finds flux bias corresponding to self-Kerr K value and drive amlitude

    Parameters
    ----------
    model : Circuit
        Circuit model representing its tomology.
    max_drive_amp : : float, optional
         Maximum drive amplitude to consider for the search of maximum Kerr-cat sizes. 
         The default is Pi = 0.5 (see Fig. 1 and Eq. (6) in paper)

    K : float, optional
        Self-Kerr value to look flux bias for. The default is 0.

    Returns
    -------
    Flux bias for sought K value or -1 if there is no such value for particular topology.

    """
    min_phi_ext = 0.001
    max_phi_ext = 0.5
    def deltaK(x):
        model.phi_ext=x
        model.update_cn_arr(forceorder=9)
        return kerr(model,[max_drive_amp])-K
    
    #Check whether deltaK changes the sign for a range phi_ext=[0.001,0,5]
    if(np.sign(deltaK(min_phi_ext))==np.sign(deltaK(max_phi_ext))):
        return -1.
    #Solves for deltaK=0
    res =  brentq(deltaK, min_phi_ext, max_phi_ext)
    return res





def lazy_size_max(model:Circuit, max_drive_amp = 0.5):# 
    """
    Softly checks for maximum of Kerr-cat size. If there is self-Kerr K=0 estimates the corresponding flux bias 
    which futher used for fine-tuning to point with K=>Klim

    Parameters
    ----------
    model : Circuit     Circuit model representing its tomology
        
    max_drive_amp : float, optional
         Maximum drive amplitude to consider for the search of maximum Kerr-cat sizes. 
         The default is Pi = 0.5 (see Fig. 1 and Eq. (6) in paper)

    Returns
    -------
    (float: max_size, float: flux bias )
    Returns max Kerr-cat size for particular circuit scheme and corresponding flux bias

    """
    energy_c_large = model.energy_c_large
    energy_jj = model.energy_jj
   

    th_e = np.linspace(0.0001,0.5,25)
    out = np.zeros((len(th_e)+1,2))    
    idx=0
    phiK0 = phi_ext_for_K_zero(model, max_drive_amp) 

    for th_ext in th_e: 
        model.phi_ext = th_ext
        model.update_cn_arr()
        temp = np.abs(size_kc(model,[max_drive_amp]))[0]
        out[idx,0] = temp #K 
        out[idx,1] = th_ext #K

        idx = idx+1
    if(phiK0>0):
        model.phi_ext = phiK0
        model.update_cn_arr()
        #Avoid division by exact zero
        out[-1,0] =  np.abs(size_kc(model,[max_drive_amp]))[0] \
            if kerr(model,[max_drive_amp])[0]>1e-10 else 1e10 #K
        out[-1,1] = phiK0 #K    

    index_max = out[:,0].argmax()
    return out[index_max,0],out[index_max,1]



def maxSize_opt(model:Circuit, phi_e_max, max_drive_amp = 0.5, Klim = 1e-3):# returns max positive kerr nnoninearity value for particular scheme
    """    

     Parameters
     ----------
     model : Circuit
         Circuit model representing its tomology
     phi_e_max : float
         deferred flux bias for maximum Kerr-cat size (K \approx 0) 
     max_drive_amp : float, optional
          Maximum drive amplitude to consider for the search of maximum Kerr-cat sizes. 
          The default is Pi = 0.5 (see Fig. 1 and Eq. (6) in paper)
     Klim : float, optional
         The minimal value of Kerr nonlinearity considered.  The default is 1e-3.

     Returns
     -------
     Returns max Kerr-cat size for minimal self-Kerr magnitude for particular circuit scheme

     """
     
    model.phi_ext=phi_e_max
    model.update_cn_arr()
    energy_c_large = model.energy_c_large
    energy_jj = model.energy_jj
    intv = 0.000005

    

    

    out = np.zeros((2,2))

    K=kerr(model,[max_drive_amp])[0]
    if(abs(K)>=Klim):
        return np.abs(size_kc(model,[max_drive_amp])[0]), model.phi_ext

    #positive K    
    count=0
    while (abs(K)<Klim):
        
        phi_ext=model.phi_ext+intv
        
        if((phi_ext<0.) or (phi_ext>0.5)):
            phi_ext=phi_ext-intv
            break
        model.phi_ext= phi_ext
        model.update_cn_arr()
        K2 = kerr(model,[max_drive_amp])[0]
        diffs = abs(K2-K)
        if(diffs<0.125*Klim):
            intv=intv*2
        elif(diffs>0.25*Klim):
            intv=intv/1.5
        K=K2    
        count=count+1 
    temp = np.abs(size_kc(model,[max_drive_amp])[0])


    
    out[0,0]=temp if (abs(K)>=Klim) else 0
    out[0,1]=model.phi_ext
    
    #negative K
    #RESET local vars
    model.phi_ext=phi_e_max
    K=0
    count=0
    intv = 0.000005
    temp= 0
    while (abs(K)<Klim):

        phi_ext=model.phi_ext-intv 

        if((phi_ext<0.) or (phi_ext>0.5)):
            phi_ext=phi_ext+intv
            break
        model.phi_ext=phi_ext
        model.update_cn_arr()
        K2 = kerr(model,[max_drive_amp])[0]
        diffs = abs(K2-K)
        if(diffs<0.125*Klim):
            intv=intv*2
        elif(diffs>0.25*Klim):
            intv=intv/1.5
        K=K2
        count=count+1   
    temp = np.abs(size_kc(model,[max_drive_amp])[0])


    
    out[1,0]=temp if (abs(K)>=Klim) else 0
    out[1,1]=model.phi_ext

    index_max = out[:,0].argmax()
    return out[index_max,0],out[index_max,1]




# An umbrella method for calculation of the maximal Kerr-cat size for minimal self-Kerr magnitude for particular circuit scheme
def maxsize(model:Circuit, alpha, xJ):
    model.alpha=alpha
    model.xJ=xJ
    print('Circuit parameters: alpha:',model.alpha,', xJ:',model.xJ,', M:',model.M,', N:',model.N)
    model.update_cn_arr()    
    _, lazy_phi_e_max = lazy_size_max(model)
    max_size, phi_e_max = maxSize_opt(model, lazy_phi_e_max)
    print('Max size and its phi_ext:', max_size, phi_e_max)
    return max_size, phi_e_max

#Vectorized version of the maxsize() method       
vmaxSize = np.vectorize(pyfunc=maxsize,otypes=[float,float])



def as_array(x):
    """Convert float/int or tuple/list/ndarray into a 1D numpy array."""
    if isinstance(x, numbers.Real):   # float or int
        return np.array([x], dtype=float)
    else:
        return np.array(x, dtype=float)


