#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  2 11:58:17 2025

@author: roman
"""

from scipy.optimize import fsolve
from sympy import Symbol, diff, Function, Derivative
from scipy.special import jv

import numpy as np
import math

import warnings

from ninatool.circuits.base_circuits import loop, J
from matplotlib import pyplot as plt




der_sym_array=[]

pi=np.pi
omega_d = 2.


class Circuit:
    
    def __init__(self, M, xJ, N, alpha, phi_ext, energy_jj, energy_c_large, config, asym_arr=[0.,0.], withDelta=False, maxorder=8):
        self.M = M
        self.xJ = xJ
        self.N = N
        self.alpha = alpha
        self.phi_ext= phi_ext
        self.energy_c_large = energy_c_large
        self.energy_jj = energy_jj
        self.config = config
        self.withDelta = withDelta
        self.maxorder = maxorder
        self.asym_arr= asym_arr
        self.update_cn_arr()
        
        
          
    def update_cn_arr(self, forceorder=-1):
        #TODO rewrite with/without stray inductance functionality
        order = forceorder if forceorder > 2 else (self.maxorder if self.maxorder > 0  else 2)
        self.cn_arr = cn_S_arr_holder(self.M, self.xJ if self.maxorder > 0  else 1000., self.N, self.alpha, self.phi_ext, order, ra=self.asym_arr[0], rb=self.asym_arr[1])
        self.phi_zpf = np.power(2*self.energy_c_large/(self.energy_jj*self.cn_arr[2]), 0.25)

    
    def print(self):
        print('M:', self.M, ', xJ:', self.xJ, ', N:', self.N, ', alpha:', self.alpha, ' ,phi_ext:', self.phi_ext, ' ,asym_arr:', self.asym_arr)


############################################################
########    Circuit potential and topology    ##########
############################################################

def fluxonium_potential(x,alpha,th_e,N):   
    return -alpha*np.cos(x)-N*np.cos((x-2*np.pi*th_e)/N)

def fluxonium_potential_diff(x,alpha,th_e,N):   
    return alpha*np.sin(x)+np.sin((x-2*np.pi*th_e)/N)

def fluxonium_potential_diff2_at_min(alpha,th_e,N):   
    x =  fsolve(fluxonium_potential_diff, (2*np.pi*th_e), args=(alpha,th_e,N))
    #print(x)
    return alpha*np.cos(x)+np.cos((x-2*np.pi*th_e)/N)/N

def fluxonium_potential_diffM(x,alpha,th_e,N,M):   
    return alpha*np.sin(x/M)+np.sin((x/M-2*np.pi*th_e)/N)

def fluxonium_potential_diff2M_at_min(alpha,th_e,N,M):   
    x =  fsolve(fluxonium_potential_diffM, (2*np.pi*th_e), args=(alpha,th_e,N,M))[0]
    return alpha*np.cos(x/M)+np.cos((x/M-2*np.pi*th_e)/N)/(M*N)

def fluxonium_potential_diff_k(x,alpha,th_e,N,M, kmax, Ej_arr=[1.] ):   
    order =1
    return (-1)**(order//2)*sum(alpha*Ej_arr[k-1]*M*np.sin(x/M)*(k/M)**(order)+Ej_arr[k-1]*N*M*np.sin((x/M-2*np.pi*th_e)/N)*(k/(N*M))**(order)\
              for k in np.arange(1,kmax+2))

def fluxonium_potential_diff_k_at_min(alpha,th_e,N,M, kmax, Ej_arr=[1.] ):   
    x =  fsolve(fluxonium_potential_diff_k, (2*np.pi*th_e), args=(alpha,th_e,N,M, kmax))[0]
    # print(x)
    order =2
    return (-1)**(order//2+1)*sum(alpha*Ej_arr[k-1]*M*np.cos(x/M)*(k/M)**(order)+Ej_arr[k-1]*N*M*np.cos((x/M-2*np.pi*th_e)/N)*(k/(N*M))**(order)\
              for k in np.arange(1,kmax+2))

#Nonlinear coefficient for fluxoium-like elements (N=3 is SNAIL)
def cn(N,alpha,th_e,order):
    x =  fsolve(fluxonium_potential_diff, (2*np.pi*th_e), args=(alpha,th_e,N))[0]

    if(np.mod(order,2)==0):
        res = (-1)**(order//2+1)*(alpha*np.cos(x)+N*np.cos((x-2*np.pi*th_e)/N)/N**(order))#/2**(order-1)
    else:
        res = (-1)**(order//2)*(alpha*np.sin(x)+N*np.sin((x-2*np.pi*th_e)/N)/N**(order))#/2**(order-1)
    return res

#Nonlinear coefficient for an array of M fluxoium-like elements (M=1, N=3 is SNAIL)
def cnM(N,M,alpha,th_e,order):
    x =  fsolve(fluxonium_potential_diffM, (2*np.pi*th_e), args=(alpha,th_e,N,M))[0]
#     x=2*x
    if(np.mod(order,2)==0):
        res = (-1)**(order//2+1)*(alpha*M*np.cos(x/M)/M**(order)+N*M*np.cos((x/M-2*np.pi*th_e)/N)/(N*M)**(order))#/2**(order-1)
    else:
        res = (-1)**(order//2)*(alpha*M*np.sin(x/M)/M**(order)+N*M*np.sin((x/M-2*np.pi*th_e)/N)/(N*M)**(order))#/2**(order-1)
    return res

#Nonlinear coefficient for an array of M fluxoium-like elements accounting for higher-order harmonics of JJs (M=1, N=3, kmax=0 is SNAIL)
def cnMk(N,M,alpha,th_e,order, kmax=0, Ej_arr=[1.]):
    x =  fsolve(fluxonium_potential_diff_k, (np.pi*th_e), args=(alpha,th_e,N,M, kmax))[0]
    if(np.mod(order,2)==0):
        res = (-1)**(order//2+1)*sum(alpha*Ej_arr[k-1]*M*np.cos(x/M)*(k/M)**(order)+Ej_arr[k-1]*N*M*np.cos((x/M-2*np.pi*th_e)/N)*(k/(N*M))**(order)\
              for k in np.arange(1,kmax+2))
    else:
        res = (-1)**(order//2)*sum(alpha*Ej_arr[k-1]*M*np.sin(x/M)*(k/M)**(order)+Ej_arr[k-1]*N*M*np.sin((x/M-2*np.pi*th_e)/N)*(k/(N*M))**(order)\
              for k in np.arange(1,kmax+2) )
    return res



def cnM_asym(M,alpha, ra, rb, th_e, order):
    N=1
    x =  lambda_prime(alpha, 0, 0, 0, ra, rb, th_e,True)*M

    if(np.mod(order,2)==0):
        res = (-1)**(order//2+1)*(alpha*M*np.cos(x/M-ra*2*np.pi*th_e)/M**(order)+N*M*np.cos((x/M+rb*2*np.pi*th_e)/N)/(N*M)**(order))#/2**(order-1)
    else:
        res = (-1)**(order//2)*(alpha*M*np.sin(x/M-ra*2*np.pi*th_e)/M**(order)+N*M*np.sin((x/M+rb*2*np.pi*th_e)/N)/(N*M)**(order))#/2**(order-1)
    return res



def phi_S_diff_n_arr(M, xJ, N, alpha, phi_e, order,kmax=0):

    x = Symbol('x')
    g = Function('g')(x)
    f = Function('f')(x)
    # Define the composite function
    h0 = g.subs({'x':f}) # U_s(phi_s)  - single SNAIL potential as a function of function phi_s(phi)

    h = xJ/(M*xJ+diff(h0, f, 2))#  d_phi_s/d_phi = xJ/(M*xJ+d^2U_s/d_phi_s^2)

   
    if(order==1):
        return h
    else:# higher order of derivatives for d^n_phi_s/d^n_phi, where n>=2
        hdiff = diff(h, x, order-1)
        replacements = [(Derivative(f, (x, n)), phi_S_diff_n_arr(M, xJ, N, alpha, phi_e, n)) for n in np.linspace(order-1,1,order-1, dtype=int)]
        new  = hdiff.subs(replacements) 
        replacements = [(Derivative(g.subs({'x':f}), (f, n)), cnMk(N,1,alpha,phi_e,n,kmax)) for n in np.linspace(order+1,1,order+1, dtype=int)]
        res  = new.subs(replacements)
        return float(res)

def cn_S_arr(M, xJ, N, alpha, phi_e, order, ra=0, rb=0, kmax=0):
    dphi_s_dphi = xJ/(fluxonium_potential_diff_k_at_min(alpha,phi_e,N,1, kmax)+M*xJ)
    if(order<2):
        raise ValueError('order should be larger or equal to 2, order:'+str(order)+'was used as input')
    elif(N>1 and xJ>500):
        return cnMk(N,M,alpha,phi_e,order,kmax)
    elif(N==1 and xJ>500):
        return cnM_asym(M,alpha, ra, rb,phi_e,order)
    elif(order==2):
        return xJ*(1-M*dphi_s_dphi)
    else:
        return -xJ*M*phi_S_diff_n_arr(M, xJ, N, alpha, phi_e, order-1,kmax)  
        
def cn_S_arr_holder(M, xJ, N, alpha, phi_e, maxorder,  ra=0., rb=0., kmax=0):
    res = np.zeros(maxorder+1)
    if(xJ>500.): # while NINA capable to calculate for this case for SNAILs since in array of SQUIDs originally we use
    # irrotational condition which influences the partition of the flux bias between nodes (ra and rb), we use exact differentiation
    # for the array of SQUIDs potential
        for i in range(2,maxorder+1):
            res[i]=cn_S_arr_opt(M, xJ, N, alpha, phi_e, i, ra, rb, kmax)
    else:
        # 
        res[2:] = cn_S_arr_nina(M, xJ, N, alpha, phi_e, maxorder-1)
    return res
        

def cn_S_arr_nina(M, xJ, N, alpha, phi_e, maxorder):
    """
    Calculates dimensionless nonlinear coefficients using NINA (10.1103/PRXQuantum.4.030324, https://github.com/sandromiano/ninatool)

    Parameters
    ----------
    M : int      number of identical loops (for example, SNAILs) in  element
    xJ : float   ratio between individual large JJ inductance and stray (parasitic) indactance, LJ/Lstray
    N : int
        Number of large JJs in the single loop
    alpha : float
        asymmetry ration between black sheep JJ and large JJs.
    phi_e : float
        normalized external flux, 2*pi*PHI_EXT/PHI_0, where PHI_0 is the magnetic flux quantum.
    maxorder : int
        maximum order of precalculated nonlinear coefficients, cn.

    Returns
    -------
    list
        Returns the list of cn's starting fron c2 to c_maxorder.

    """
    J_small= J(alpha, order = maxorder, name = 'Jsmall')
    J_left = [J(1, order=maxorder, name=f"J{i}0") for i in range(N)]
    loop0 = loop(J_left, [J_small], name = 'loop0', stray_inductance=True)
    loop0.Nloops = M
    loop0.Lstray.L0 = 1/xJ
    loop0.interpolate_results(phi_grid = [phi_e*2*np.pi])
    
    return loop0.adm[:].squeeze()

    
#optimized symbolic expression for derivatives of phi_s(phi) ( see Appendix B2 
#or N. Frattini, Three-wave Mixing in Superconducting Circuits: Stabilizing Cats with SNAILs (Yale
#University, thesis, 2021))
#required for calculation of nonlinear coeffs of an array of fluxonium-like elements with geometric inductance
def phi_S_diff_n_arr_opt(order):
    #print("Order: ", order )
    x = Symbol('x')
    g = Function('g')(x)
    f = Function('f')(x)
    M = Symbol('M')
    xJ = Symbol('xJ')
    # Define the composite function
    h0 = g.subs({'x':f}) # U_s(phi_s)  - single SNAIL potential as a function of function phi_s(phi)

    h = xJ/(M*xJ+diff(h0, f, 2))#  d_phi_s/d_phi = xJ/(M*xJ+d^2U_s/d_phi_s^2)

    if(np.size(der_sym_array)>=order):
        return der_sym_array[order]
    if(order==1):
        return h
    else:# higher order of derivatives for d^n_phi_s/d^n_phi, where n>=2
        hdiff = diff(h, x, order-1)
        
        replacements = [(Derivative(f, (x, n)),  phi_S_diff_n_arr_opt(n)) for n in np.linspace(order-1,1,order-1, dtype=int)]
        new  = hdiff.subs(replacements)
        
        return new
    
# container for different derivative orders of phi_s(phi) 
def phi_S_diff_n_arr_holder(maxorder):
    res = [0]
    for i in range(1,maxorder):
        res.append(phi_S_diff_n_arr_opt(i))
    return res

#Old functionality, replaced with NINA functionality
# der_sym_array = phi_S_diff_n_arr_holder(8)# holding symbolic representaion of derivatives up to order 11



# Nonlinear coeffs of an array of fluxonium-like elements with geometric inductance (optimized)
def cn_S_arr_opt(M, xJ, N, alpha, phi_e, order, ra=0, rb=0, kmax=0):
    dphi_s_dphi = xJ/(fluxonium_potential_diff_k_at_min(alpha,phi_e,N,1, kmax)+M*xJ)

    x = Symbol('x')
    g = Function('g')(x)
    f = Function('f')(x)
    M_s = Symbol('M')
    xJ_s = Symbol('xJ')
    # # Define the composite function
    # h0 = g.subs({'x':f}) # U_s(phi_s)  - single SNAIL potential as a function of function phi_s(phi)
     
    
    if(order<2):
        raise ValueError('Order should be larger or equal to 2, order:' + str(order) +' was used as input')
    elif(N>1 and xJ>500):
        return cnMk(N,M,alpha,phi_e,order,kmax)
    elif(N==1 and xJ>500):
        if(ra==0 and rb==0):
            raise ValueError('ra, rb are not set')
        return cnM_asym(M,alpha, ra, rb,phi_e,order)
    elif(order==2):
        return xJ*(1-M*dphi_s_dphi)
    else:
        replacements =[(Derivative(g.subs({'x':f}), (f, n)), cnMk(N,1,alpha,phi_e,n,kmax)) for n in np.linspace(order,1,order, dtype=int)]
        res  = der_sym_array[order-1].subs(replacements)
    
        replacements = [(xJ_s, xJ), (M_s, M)] 

        res  = -xJ*M*res.subs(replacements)
    
        return float(res)




############################################################
########    Supercoefficients    ##########
############################################################


def asym_drive(model):
    """
    Calculates Pi_a and Pi_b for the array of SQUIDs (see Appendices A1 and B3 in paper) 

    """
    ra = model.asym_arr[0] 
    rb = model.asym_arr[1]
    phi_ext = model.phi_ext
    c2 = model.cn_arr[2]
    alpha= model.alpha
    M=model.M

    x0 =  lambda_prime(model.alpha, 0, 0, 0, ra, rb, phi_ext,True)*M    
    asym_dr_arr = [-ra+(alpha*np.cos(x0/M-ra*2*np.pi*phi_ext)/M/c2-np.cos(x0/M+rb*2*np.pi*phi_ext)/M/c2)/(4*(omega_d**2-1)),\
                   rb+(alpha*np.cos(x0/M-ra*2*np.pi*phi_ext)/M/c2-np.cos(x0/M+rb*2*np.pi*phi_ext)/M/c2)/(4*(omega_d**2-1))]
    return asym_dr_arr

               
def Cnl(n,l,phi_zpf):
    return np.exp(-phi_zpf**2/2)/(math.factorial(n)*math.factorial(n+l))*phi_zpf**(2*n+l)

def Cnl_reduced(n,l,phi_zpf):
    return 1/(math.factorial(n)*math.factorial(n+l))*phi_zpf**(2*n+l)


def Cnlp(model, Pi, n,l,p):
    """
    General method for calculation of the supercoefficients for array of SNAILs and SQUIDs

    Parameters
    ----------
    model : Circuit
        Circuit model
    Pi : float
        Effective drive amplitude, Tilde{Pi}(independent of zero-point fluctuations for charge and flux) in paper
    n : int
        number of oscillator pairs
    l : int
       the number of oscillator responsible for the coupling of different oscillator states
    p : int
        the number of drive photons responsible for the coupling of different oscillator states

    Returns
    -------
    float
        Value of the supercoefficint for sought parameters.

    """
    return Cnlp_all(model,Pi, n,l,p) if model.maxorder<0 else Cnlp_sum(model, Pi, n,l,p, model.maxorder)

def Cnlp_all(model, Pi, n,l,p):
    if(model.config ==0):
        return Cnlp_all_MN(model,n,l,p, Pi)
    elif(model.config==1):
        asym_dr_arr = asym_drive(model) 
        return Cnlp_all_SQUIDs(model, n,l,p, asym_dr_arr[0]*Pi, asym_dr_arr[1]*Pi, model.asym_arr[0], model.asym_arr[1]) 

def Cnlp_sum(model,Pi, n,l,p, max_order):
    if(model.config==0):
        if(model.xJ<500):            
            return Cnlp_sum_MN(model,n,l,p, max_order, Pi)
        else:
            return Cnlp_all_MN(model,n,l,p, Pi)
    raise Exception("Incorrect call of Cnlp_sum which currently implemented only for model.config=0 (Array of SNAILs)")
    


def Cnlp_all_MN(model,n,l,p, Pd):
    coeff_arr = [model.phi_zpf, 0, 0]
    return Cnlp_all_MN_3modes(model,n,l,0,0,0,0,p,coeff_arr, Pd)

def Cnlp_sum_MN(model, n,l,p, max_order, Pd):
    coeff_arr = [model.phi_zpf, 0, 0]
    return Cnlp_sum_MN_3modes(model,n,l,0,0,0,0,p,coeff_arr, max_order, Pd)

def Cnlp_all_SQUIDs(model,n,l,p, Pi_a, Pi_b, r_a, r_b):
    coeff_arr = [model.phi_zpf, 0, 0]
    return Cnlp_all_3modes_SQUIDs(model, n,l,0,0,0,0,p,coeff_arr, Pi_a, Pi_b, r_a, r_b)
    


def Cnlp_all_MN_3modes(model, n1,l1,n2,l2,n3,l3,p,coeff_arr, Pd):
    alpha = model.alpha
    phi_ext =  model.phi_ext
    N=model.N
    M=model.M
    energy_jj=model.energy_jj
    phi0 = fsolve(fluxonium_potential_diffM, (2*np.pi*phi_ext), args=(alpha,phi_ext,N,M))

    Pi_l=Pd

    coeff1 = coeff_arr[0]
    coeff2 = coeff_arr[1]
    coeff3 = coeff_arr[2]
    if(not check_index_of_Cnlp(n1,l1,n2,l2,n3,l3, p)):
        if(np.mod(p+l1+l2+l3,2)==0):
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2)+1)*(alpha*M*Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*np.cos(phi0/M)*jv(p,Pi_l/M)+N*M*Cnl(n1,l1,coeff1/(N*M))*Cnl(n2,l2,coeff2/(N*M))*Cnl(n3,l3,coeff3/(N*M))*np.cos((phi0/M-phi_ext*2*pi)/N)*jv(p,Pi_l/(N*M)))
        else:
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2))*(alpha*M*Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*np.sin(phi0/M)*jv(p,Pi_l/M)+N*M*Cnl(n1,l1,coeff1/(N*M))*Cnl(n2,l2,coeff2/(N*M))*Cnl(n3,l3,coeff3/(N*M))*np.sin((phi0/M-phi_ext*2*pi)/N)*jv(p,Pi_l/(N*M)))
    else:
        if(np.mod(p+l1+l2+l3,2)==0):
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2)+1)*(alpha*M*(Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*jv(p,Pi_l/M)-Cnl_reduced(n1,l1,coeff1/M)*Cnl_reduced(n2,l2,coeff2/M)*Cnl_reduced(n3,l3,coeff3/M)*(Pi_l/2/M)**p)*np.cos(phi0/M)\
                                                                       +N*M*(Cnl(n1,l1,coeff1/(N*M))*Cnl(n2,l2,coeff2/(N*M))*Cnl(n3,l3,coeff3/(N*M))*jv(p,Pi_l/(N*M))-Cnl_reduced(n1,l1,coeff1/(N*M))*Cnl_reduced(n2,l2,coeff2/(N*M))*Cnl_reduced(n3,l3,coeff3/(N*M))*(Pi_l/2/(N*M))**p)*np.cos((phi0/M-phi_ext*2*pi)/N))
        else:
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2))*(alpha*M*(Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*jv(p,Pi_l/M)-Cnl_reduced(n1,l1,coeff1/M)*Cnl_reduced(n2,l2,coeff2/M)*Cnl_reduced(n3,l3,coeff3/M)*(Pi_l/2/M)**p)*np.sin(phi0/M)\
                                                                       +N*M*(Cnl(n1,l1,coeff1/(N*M))*Cnl(n2,l2,coeff2/(N*M))*Cnl(n3,l3,coeff3/(N*M))*jv(p,Pi_l/(N*M))-Cnl_reduced(n1,l1,coeff1/(N*M))*Cnl_reduced(n2,l2,coeff2/(N*M))*Cnl_reduced(n3,l3,coeff3/(N*M))*(Pi_l/2/(N*M))**p)*np.sin((phi0/M-phi_ext*2*pi)/N))

    return res 
      

def Cnlp_all_3modes_SQUIDs(model,n1,l1,n2,l2,n3,l3,p,coeff_arr, Pi_a, Pi_b, r_a, r_b):
    if(model.N>0 and model.N!= 1):
        warnings.warn('The N='+str(model.N)+' is ignored for an array of SQUIDs, where N is always equal to 1')
    phi_ext = model.phi_ext
    alpha= model.alpha
    M=model.M

    energy_jj=model.energy_jj
    phi0 = lambda_prime(alpha, 0, 0, 0, r_a, r_b, phi_ext,True)*M

    Pi_a=Pi_a/M
    Pi_b=Pi_b/M
    coeff1 = coeff_arr[0]
    coeff2 = coeff_arr[1]
    coeff3 = coeff_arr[2]
    lambda_term = lambda_prime(alpha, p, Pi_a, Pi_b, r_a, r_b, phi_ext,False)
    A_p = drive_func(alpha, p, Pi_a, Pi_b, phi_ext,False)

    res = 0.
    if(not check_index_of_Cnlp(n1,l1,n2,l2,n3,l3, p)):
        if(np.mod(p+l1+l2+l3,2)==0):
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2)+1)*(M*Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*A_p*np.cos(phi0/M-lambda_term))
        else:

            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2))*(M*Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*A_p*np.cos(phi0/M-lambda_term-pi/2))
    else:
        lambda_term_reduced = lambda_prime(alpha, p, Pi_a, Pi_b, r_a, r_b, phi_ext,True)
        A_p_reduced = drive_func(alpha, p, Pi_a, Pi_b, phi_ext,True)
        if(np.mod(p+l1+l2+l3,2)==0):
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2)+1)*(M*Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*A_p*np.cos(phi0/M-lambda_term)-\
                                                                      M*Cnl_reduced(n1,l1,coeff1/M)*Cnl_reduced(n2,l2,coeff2/M)*Cnl_reduced(n3,l3,coeff3/M)*A_p_reduced*np.cos(phi0/M-lambda_term_reduced))
        else:
            res = energy_jj*(-1)**(math.floor((2*n1+l1+2*n2+l2+2*n3+l3+p)/2))*(M*Cnl(n1,l1,coeff1/M)*Cnl(n2,l2,coeff2/M)*Cnl(n3,l3,coeff3/M)*A_p*np.cos(phi0/M-lambda_term-pi/2)-\
                                                                      M*Cnl_reduced(n1,l1,coeff1/M)*Cnl_reduced(n2,l2,coeff2/M)*Cnl_reduced(n3,l3,coeff3/M)*A_p_reduced*np.cos(phi0/M-lambda_term_reduced-pi/2))
    return res

def lambda_prime(alpha_s, p, Pi_a, Pi_b, r_a, r_b, phi_e, reduced):

    phi_e = 2*pi*phi_e
    drive_term_a=0
    drive_term_b=0

    if(not reduced):
        drive_term_a= jv(p,Pi_a)
        drive_term_b= jv(p,Pi_b)
    else:
        drive_term_a= (Pi_a/2)**p
        drive_term_b= (Pi_b/2)**p

    return np.arctan((alpha_s*drive_term_a*np.sin(r_a*phi_e)-drive_term_b*np.sin(r_b*phi_e))\
                   /(alpha_s*drive_term_a*np.cos(r_a*phi_e)+drive_term_b*np.cos(r_b*phi_e)))

def drive_func(alpha_s, p, Pi_a, Pi_b, phi_e, reduced):
    phi_e = 2*pi*phi_e
    drive_term_a=0
    drive_term_b=0
    if(not reduced):
        drive_term_a= jv(p,Pi_a)
        drive_term_b= jv(p,Pi_b)
    else:
        drive_term_a= (Pi_a/2)**p
        drive_term_b= (Pi_b/2)**p

    if(alpha_s**2*drive_term_a**2+drive_term_b**2+2*alpha_s*drive_term_a*drive_term_b*np.cos(phi_e)<0):
        # print(alpha_s**2*drive_term_a**2+drive_term_b**2+2*alpha_s*drive_term_a*drive_term_b*np.cos(phi_e))
        return 0
    return np.sign(Pi_b-Pi_a)**p*np.sqrt(alpha_s**2*drive_term_a**2+drive_term_b**2+2*alpha_s*drive_term_a*drive_term_b*np.cos(phi_e))


def Cnlp_sum_MN_3modes(model, n1,l1,n2,l2,n3,l3, p,coeff_arr, max_order, Pd):  
    cn_arr = model.cn_arr
    energy_jj = model.energy_jj
    coeff1 = coeff_arr[0]
    coeff2 = coeff_arr[1]
    coeff3 = coeff_arr[2]

    res = energy_jj*sum(Cnl_reduced(n1,l1,coeff1)*Cnl_reduced(n2,l2,coeff2)*Cnl_reduced(n3,l3,coeff3)*((coeff1**2+coeff2**2+coeff3**2)/2)**m*(Pd/2)**(2*k+p)*cn_arr[2*(n1+n2+n3)+l1+l2+l3+2*k+p+2*m]\
              /(math.factorial(m)*math.factorial(k)*math.factorial(k+p))\
              for k in np.arange(0,max_order//2) for m in np.arange(0,max_order//2) if 2*(n1+n2+n3)+l1+l2+l3+2*k+p+2*m>2 and 2*(n1+n2+n3)+l1+l2+l3+2*k+p+2*m <= max_order )
    
    return res   

def check_index_of_Cnlp(n1,l1, n2,l2, n3,l3, p):
    if((n1+n2+n3 == 0 and l1+l2+l3 == 1 and p == 0) or (2*(n1+n2+n3)+l1+l2+l3+p == 2)):
            return True
    else:
            return False
        
        
        
        
        
        
        