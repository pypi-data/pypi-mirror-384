import math
import warnings
import numpy as np
from scipy.optimize import root_scalar
from scipy.interpolate import RegularGridInterpolator
from numpy import linalg as LA
from math import sqrt, atan, sin, cos, tan
from numba import njit
import importlib
from enum import Enum


class reservoir_types(Enum):
    """
    Enum class for reservoir types.
    """
    STAGESTORAGE = 0
    RECTANGULAR = 1
    TRAPEZOIDAL = 2

class riverbank_loc(Enum):
    """
    Enum class for riverbank location.
    """
    RIGHT = 0
    LEFT = 1


# Hydrodynamics module
def Hydrodynamics(z_b,z_s,z_t,b_top,btop_effMax,b_down,db_down,h_top_prev,h_down_prev,H,m_up,m_down,m_mean,dx,Su,Sd,lambda_loss,c1,c2,c_eff,h_d,rho,g,reservoir_shape,lmc,wmc,S_lat,Qin,Qd,dt,n,dam,Qo,Ar,GI_Vres,GI_VFP,V_FP):
    """
    :param z_b: Breach bottom elevation [m]
    :param z_s: Water level in the main channel [m]
    :param z_t: Water level in the floodplain [m]
    :param b_top: Breach bottom width on flat top reach [m]
    :param btop_effMax: Maximum effective breach width on flat top reach [m]
    :param b_down: Breach bottom width on D/S reach [m]
    :param db_down: Breach bottom width variation on D/S reach [m]
    :param h_top_prev: Flow depth at the breach on the flat top reach at the previous time step [m]
    :param h_down_prev: Flow depth at the breach on the D/S reach at the previous time step [m]
    :param H: Water head in the main channel [m]
    :param m_up: Slope of the upstream side of the breach [-]
    :param m_down: Slope of the downstream side of the breach [-]
    :param m_mean: Mean slope of the breach [-]
    :param dx: Breach bottom length on flat top reach [m]
    :param Su: Upstream slope (H/V) [-]
    :param Sd: Downstream slope (H/V) [-]
    :param lambda_loss: Loss coefficient [-]
    :param c1: Coefficient for the breach discharge calculation [-]
    :param c2: Coefficient for the breach discharge calculation [-]
    :param c_eff: Coefficient for the breach discharge calculation [-]
    :param h_d: Dike height [m]
    :param rho: Water density [kg/m^3]
    :param g: Gravitational acceleration [m/s^2]
    :param lmc: Main channel length [m]
    :param wmc: Main channel width [m]
    :param Qin: Inflow discharge [m^3/s]
    :param Qd: Drain discharge [m^3/s]
    :param dt: Time step [s]
    :param n: Manning roughness coefficient [s/m^(1/3)]
    :param dam: Dam or dike [boolean]
    :param Qo: float or dictionary: Outflow discharge [m^3/s] or contains path to module that computes it
    :param Ar: Water surface area in the main channel/reservoir [m^2]
    :param GI_Vres: Volume-water level curve in the main channel/reservoir
    :param GI_VFP: Volume-water level curve in the floodplain
    :param V_FP: Volume in the floodplain [m^3]

    :return: z_s_new: Updated water level in the main channel [m]
    :return: z_t_new: Updated water level in the floodplain [m]
    :return: V_FP_new: Updated volume in the floodplain [m^3]
    :return: Qb: Breach discharge [m^3/s]
    :return: B_w_down: Breach width at water free surface on D/S reach [m]
    :return: A_down: Flow area on D/S reach [m^2]
    :return: R_down: Hydraulic radius on D/S reach [m]
    :return: tau_b_down: Bed shear stress on D/S reach [N/m^2]
    :return: B_w_top: Breach width at water free surface on flat top reach [m]
    :return: A_top: Flow area on flat top reach [m^2]
    :return: R_top: Hydraulic radius on flat top reach [m]
    :return: tau_b_top: Bed shear stress on flat top reach [N/m^2]
    :return: h_top: Flow depth at the breach on the flat top reach [m]
    :return: h_down: Flow depth at the breach on the D/S reach [m]
    """

    if z_s<z_t and z_s>z_b:
        warnings.warn("$z_t$ is larger than $z_s$: water cannot flow from flood plain to main channel.")
        return
    # 1.1) Breach discharge (first erosion period considered only)
    # ------------------------------------------------------------
    if z_s>z_b: # Formulas adapted for z_s >= z_t + Non-erodible channel bottom
        if z_b==0 and (z_s-z_t)<1/3*z_s: # Keulegan equation for second erosion period (=general erosion period)
            A=b_top*h_top_prev+0.5*(abs(m_up)+abs(m_down))*h_top_prev**2  #[m^2] Flow area
            P=b_top+h_top_prev*(sqrt(1+m_up**2)+sqrt(1+m_down**2))        #[m] Wet breach perimeter
            R=A/P                                                         #[m] Hydraulic radius
            Qb=sqrt((max((z_s-z_t),0)*2*g*A**2)/((2*g*(n**2)*dx)/R**(4/3)+lambda_loss))
            print(Qb)
        else: # We are in the first erosion period -> always in this case if z_t=0
            k_sm = 1   #[-] Submergence correction for tailwater effects on weir outflow
            '''if (z_s-z_t)<1/3*z_s:
                k_sm = max(1-27.8*((z_t-z_b)/(z_s-z_b) - 2/3)**3,0)
                if k_sm<1:
                    print(k_sm)
                    warnings.warn("$k_sm$ is smaller than 1.")'''

            Qb = k_sm*c_eff*(c1*b_top*min(H,z_s-z_t)**1.5+c2*m_mean*min(H,z_s-z_t)**2.5) #[m^3/s] Breach discharge
    else:
        Qb=0

    # 1.2.1) Representative flow depth at the breach (h_top)
    # -----------------------------------------------
    if z_s>z_b:
        h_top = max([2/3*(z_s-z_b), 0.5*((z_s-z_b)+max(z_t-z_b,0))]) #[m]
    else:
        h_top=0

    # 1.2.2) Flow depth on the downstream slope (h_down)
    # --------------------------------------------------
    bdown_eff = btop_effMax+db_down # Effective channel width on the downstream slope
    if z_s>z_b and z_b>0 and z_s>z_t: # and dx>dx_min # THIS LAST CONDITION SHOULD BE ANALYSED CAREFULLY
        #eqn = Qb-1/n*A*R**(2/3)*Sd**(-1/2) == 0
        cst_a = Qb*n*sqrt(Sd)
        if b_top<btop_effMax: # Breach width smaller than the maximum effective breach width
            cst_b = sqrt(1+m_up**2)+sqrt(1+m_down**2)
            [b_down_,m_up_] = [b_down, m_up]
        else:
            cst_b = sqrt(1+m_down**2)
            [b_down_,m_up_] = [bdown_eff, 0]

        def h_down_fun(h): # If b_top>btop_effMax: b_down=b_down_eff and m_up=0
            return cst_a-h*(b_down_+(m_up_+m_down)*h/2)*(h*(b_down_+(m_up_+m_down)*h/2.)/(b_down_+h*cst_b))**(2./3.)
        h_down = root_scalar(h_down_fun, bracket=np.asarray([0.,z_s], dtype=np.float64),fprime=False,x0=h_down_prev,xtol=1e-8,method='brentq').root
    else:
        h_down=h_top

    # 1.3) Bed shear stress on downstream slope/breach top (tau_b)
    # (Breach flow area (A); Hydraulic radius (R))
    # ------------------------------------------------------------
    if z_s>z_b and z_s>z_t:
        if b_top<btop_effMax: # Breach width smaller than the maximum effective breach width
            [A_down,R_down,tau_b_down] = Bed_Shear_Stress(h_down,b_down,m_up,m_down,Qb,rho,g,n)
            [A_top,R_top,tau_b_top] = Bed_Shear_Stress(h_top,b_top,m_up,m_down,Qb,rho,g,n)
        else:
            [A_down,R_down,tau_b_down] = Bed_Shear_Stress(h_down,bdown_eff,-1,m_down,Qb,rho,g,n)
            [A_top,R_top,tau_b_top] = Bed_Shear_Stress(h_top,btop_effMax,-1,m_down,Qb,rho,g,n)
    else:
        [A_down,R_down,tau_b_down]=[0,0,0]
        [A_top,R_top,tau_b_top]=[0,0,0]

    # 1.4)  Evolution of the main channel water level (Mass conservation)
    # -------------------------------------------------------------------
    z_s_new, z_t_new, V_FP_new = BC(Ar,GI_Vres,z_s,dam,reservoir_shape,lmc,wmc,S_lat,Su,Qb,Qo,c1,h_d,Qin,Qd,dt,z_b,z_t,GI_VFP,V_FP)
    if b_top < btop_effMax:
        B_w_top = (z_s>z_b) * (b_top+h_top*(abs(m_up)+abs(m_down)))
        B_w_down = (z_s>z_b) * (b_down+h_down*(abs(m_up)+abs(m_down)))
    else:
        B_w_top = (z_s>z_b) * (btop_effMax+h_top*abs(m_down))
        B_w_down = (z_s>z_b) * (bdown_eff+h_down*abs(m_down))

    return z_s_new,z_t_new,V_FP_new,Qb,B_w_down,A_down,R_down,tau_b_down,B_w_top,A_top,R_top,tau_b_top,h_top,h_down




# Boundary conditions (computation of the water level in the main channel)
def BC(Ar,GI_Vres,z_s,dam,reservoir_shape,lmc,wmc,S_lat,Su,Qb,Qo,c1,h_d,Qin,Qd,dt,z_b,z_t,GI_VFP,V_FP):
    """
    :param Ar: Water surface area in the main channel/reservoir [m^2]
    :param GI_Vres: Volume-water level curve in the main channel/reservoir
    :param z_s: Water level in the main channel [m]
    :param dam: Dam or dike [boolean]
    :param lmc: Main channel length [m]
    :param wmc: Main channel width [m]
    :param Su: Upstream slope (H/V) [-]
    :param Qb: Breach discharge [m^3/s]
    :param Qo: float or dictionary: Outflow discharge [m^3/s] or contains path to module that computes it
    :param c1: Coefficient for the breach discharge calculation [-]
    :param h_d: Dike height [m]
    :param Qin: Inflow discharge [m^3/s]
    :param Qd: Drain discharge [m^3/s]
    :param dt: Time step [s]
    :param z_b: Breach bottom elevation [m]
    :param z_t: Water level in the floodplain [m]
    :param GI_VFP: Volume-water level curve in the floodplain
    :param V_FP: Volume in the floodplain [m^3]

    :return: z_s_new: Updated water level in the main channel [m]
    :return: z_t_new: Updated water level in the floodplain [m]
    :return: V_FP_new: Updated volume in the floodplain [m^3]
    """
    # Water level in the floodplain
    if GI_VFP != 0:
        V_FP_new = V_FP + Qb*dt
        z_t_new = GI_VFP(V_FP_new)
    else:
        z_t_new = 0
        V_FP_new = 0

    if reservoir_shape == reservoir_types.STAGESTORAGE.value:  # Volume-water level curve provided - Stage storage curve
        V_ref1=GI_Vres(z_s*0.9999)
        V_ref2=GI_Vres(z_s*1.0001)
        dVdz=(V_ref2-V_ref1)/(z_s*1.0001-z_s*0.9999)
    elif reservoir_shape == reservoir_types.RECTANGULAR.value: # Rectangular shape
        dVdz = Ar # Given water surface area
    elif reservoir_shape == reservoir_types.TRAPEZOIDAL.value: # Trapezoidal shape
        if dam==False:
            dVdz = lmc*(wmc+(Su+S_lat)*z_s)
        else:
            dVdz = wmc*(lmc+(Su+S_lat)*z_s)
    else:
        AssertionError('Reservoir shape of type '+str(reservoir_shape)+' not supported.\nChoose from irregular, rectangular, or trapz.')

    if dVdz <= 0:
        AssertionError('The derivatibe dV/dz is smaller or equal to zero. This is aberrant. Please chack your inputs.')

    if isinstance(Qo, dict):
        module = importlib.import_module(Qo["Qo_moduleName"])
        Qo = module.qout(z_s,**Qo) # Pass dictionary as keyword arguments
    else:
        Qo=0
    if dam == False:
        Qsc=c1*wmc*(max(z_s-h_d,0))**1.5
    else:
        Qsc=0

    if dVdz==0:
        z_s_new=z_s
    else:
        z_s_new = max((Qin-Qb-Qo-Qd-Qsc)*dt/dVdz+z_s,0)

    if z_s_new<z_t and z_s_new>z_b:
        z_s_new=z_t
        warnings.warn("$z_s$ dropped below $z_t$ but $z_s$=$z_t$ enforced.")

    return z_s_new, z_t_new, V_FP_new



# Hydrodynamics module
def Hydrodynamics2D(hbreach,zbbreach,z_b,z_s,z_t,Qb,b_top,btop_effMax,b_down,db_down,h_down_prev,m_up,m_down,m_mean,dx,Su,Sd,rho,g,n):
    """
    Only relevant if possible to couple with 2D hydrodynamic software
    """

    # 1.2.1) Representative flow depth at the breach (h_top)
    # -----------------------------------------------
    zw_temp = hbreach + zbbreach - min(zbbreach) # zbbreach = breach bathy along crest centerline
    max_hbreach = max(hbreach)
    if max_hbreach < 10**-3:
        h_top = 0
    else:
        h_top = zw_temp[hbreach>(5*10**-2)*max_hbreach].mean()

    # 1.2.2) Flow depth on the downstream slope (h_down)
    # --------------------------------------------------
    bdown_eff = btop_effMax+db_down # Effective channel width on the downstream slope
    if abs(Qb)>0 and z_b>0 and z_s>z_t: # and dx>dx_min
        #eqn = Qb-1/n*A*R**(2/3)*Sd**(-1/2) == 0
        cst_a = Qb*n*sqrt(Sd)
        if b_top<btop_effMax: # Breach width smaller than the maximum effective breach width
            cst_b = sqrt(1+m_up**2)+sqrt(1+m_down**2)
            [b_down_,m_up_] = [b_down, m_up]
        else:
            cst_b = sqrt(1+m_down**2)
            [b_down_,m_up_] = [bdown_eff, 0]

        def safe_root_finding():
            def h_down_fun(h): # If b_top>btop_effMax: b_down=b_down_eff and m_up=0
                return cst_a-h*(b_down_+(m_up_+m_down)*h/2)*(h*(b_down_+(m_up_+m_down)*h/2.)/(b_down_+h*cst_b))**(2./3.)
            try:
                # Try to find the root using root_scalar
                result = root_scalar(h_down_fun, bracket=np.asarray([0,1.5*max_hbreach], dtype=np.float64),fprime=False,x0=h_down_prev,xtol=1e-8,method='brentq')
                return result.root  # If successful, return the root
            except ValueError as e:
                if "f(a) and f(b) must have different signs" in str(e):
                    # Handle the specific error where f(a) and f(b) have the same sign
                    print(f"Warning: f(0) and f({1.5*max_hbreach}) must have different signs when searching for h_down. To avoid crashing, h_down = h_top.")
                    return h_top
                else:
                    # Raise other unexpected errors
                    raise
        h_down = safe_root_finding()
    else:
        h_down=h_top

    # 1.3) Bed shear stress on downstream slope/breach top (tau_b)
    # (Breach flow area (A); Hydraulic radius (R))
    # ------------------------------------------------------------
    if z_s>z_t and abs(Qb)>0:
        if b_top<btop_effMax: # Breach width smaller than the maximum effective breach width
            [A_down,R_down,tau_b_down] = Bed_Shear_Stress(h_down,b_down,m_up,m_down,Qb,rho,g,n)
            [A_top,R_top,tau_b_top] = Bed_Shear_Stress(h_top,b_top,m_up,m_down,Qb,rho,g,n)
        else:
            [A_down,R_down,tau_b_down] = Bed_Shear_Stress(h_down,bdown_eff,-1,m_down,Qb,rho,g,n)
            [A_top,R_top,tau_b_top] = Bed_Shear_Stress(h_top,btop_effMax,-1,m_down,Qb,rho,g,n)
    else:
        [A_down,R_down,tau_b_down]=[0,0,0]
        [A_top,R_top,tau_b_top]=[0,0,0]

    # 1.4)  Width of the water free surface on each reach
    # ---------------------------------------------------
    H = max(z_s-z_b,0)
    if b_top < btop_effMax:
        B_w_top = (max_hbreach>1e-3) * (b_top+h_top*(abs(m_up)+abs(m_down)))
        B_w_down = (max_hbreach>1e-3) * (b_down+h_down*(abs(m_up)+abs(m_down)))
    else:
        B_w_top = (max_hbreach>1e-3) * (btop_effMax+h_top*abs(m_down))
        B_w_down = (max_hbreach>1e-3) * (bdown_eff+h_down*abs(m_down))

    return H,B_w_down,A_down,R_down,tau_b_down,B_w_top,A_top,R_top,tau_b_top,h_top,h_down



# Bed shear stress computation
def Bed_Shear_Stress(h,b,m_up,m_down,Qb,rho,g,n):
    """
    :param h: Water level above the part of dike considered [m]
    :param b: Breach bottom width [m]
    :param m_up: Breach upstream side slope (H/V) [-]
    :param m_down: Breach downstream side slope (H/V) [-]
    :param Qb: Breach discharge [m^3/s]
    :param rho: Water density [kg/m^3]
    :param g: Gravitational acceleration [m/s^2]
    :param n: Manning roughness coefficient [s/m^(1/3)]

    :return: A: Flow area [m^2]
    :return: R: Hydraulic radius [m]
    :return: tau_b: Bed shear stress [N/m^2]
    """

    if m_up != -1:
        A = h*(b+m_down*h/2+m_up*h/2)
        P = b+h*(sqrt(1+m_up**2)+sqrt(1+m_down**2)) #[m] Wet breach perimeter
    else:
        A = h*(b+m_down*h/2)
        P = b+h*(1+sqrt(1+m_down**2))
    R = A/P
    tau_b = (rho*g*n**2*Qb**2)/(A**2*R**(1/3))
    return A,R,tau_b





# Sediment transport capacity (Ct_star)
def Sediment_Transport_Capacity(Qb,A,R,rho_s,rho,g,w_s,d50,B_w,n,n_prime,tau_b,theta_cr,Sd,phi,C_stara,C_starb,C_starc,C_stard,qb_stara,qb_starb,lambda0a,lambda0b,suspension):

    """"
    :param Qb: Breach discharge [m^3/s]
    :param A: Flow area [m^2]
    :param R: Hydraulic radius [m]
    :param rho_s: Sediment density [kg/m^3]
    :param rho: Water density [kg/m^3]
    :param g: Gravitational acceleration [m/s^2]
    :param w_s: Settling velocity of sediments [m/s]
    :param d50: Median grain size [m]
    :param B_w: Breach top width [m]
    :param n: Manning roughness coefficient [s/m^(1/3)]
    :param tau_b: Bed shear stress [N/m^2]
    :param theta_cr: Critical Shield parameter [-]
    :param Sd: D/S slope (H/V)
    :param phi: Sediment repose angle [deg]

    :return: Ct_star: Total sediment transport capacity [-]
    :return: qb_star: Bed-load transport rate by volume per unit time [m^2/s]
    :return: C_star: Suspended-load concentration at equilibrium [-]
    """

    # 1) Suspended-load concentration at equilibrium (C_star)
    if A==0:
        Ct_star=0
        qb_star=0
        C_star=0
        U_b=0
        return Ct_star,qb_star,C_star,U_b

    U_b = Qb/A;             #[m/s] Flow velocity
    C_star = 1/C_stara*(U_b**3/(g*R*w_s))**C_starb/(1+(1/C_starc*U_b**3/(g*R*w_s))**C_stard)
    C_star = C_star/rho_s

    # 2) Bed-load transport rate by volume per unit time (qb_star)
    tau_c = theta_cr*(rho_s-rho)*g*d50
    tau_b_prime=(n_prime/n)**(3/2)*tau_b
    if Sd!=math.inf: # -> This part of the code induces strange behaviour for qbstar_b=2.5703 (only this specific value?!!) When removed, normal behaviour
        lambda0=1+lambda0a*(tau_b_prime/tau_c)**lambda0b*math.exp(2*sin(atan(1/Sd))/sin(math.radians(phi))) # To be verified
        tau_b_prime=tau_b_prime+lambda0*tau_c*sin(atan(1/Sd))/sin(math.radians(phi)) # Effective shear stress + To be verified
    qb_star = qb_stara*(max(tau_b_prime/tau_c-1,0))**qb_starb * sqrt((rho_s/rho-1)*g*d50**3) #[m^2/s]
    if Qb==0:
        q_star = 0 #[(m^3/s) / (m^3/s)]
    else:
        q_star = B_w*qb_star/Qb

    # 3) Total-load transport capacity (Ct_star)
    if suspension==False:
        C_star=0

    Ct_star = C_star + q_star

    return Ct_star,q_star,C_star,U_b





# Sediment concentrations
def Sediment_Concentrations(t, dx, ds, lbda, B_w_top, B_w_down, instant_equilibrium, Ct_star_top, Ct_star_down, Ct_in_top):
    """
    :param t: Time index
    :param dx: Breach bottom length on flat top reach [m]
    :param ds: Breach bottom length on D/S reach [m]
    :param lbda: Sediment transport capacity coefficient [-]
    :param B_w_top: Breach width at water free surface on flat top reach [m]
    :param B_w_down: Breach width at water free surface on D/S reach [m]
    :param instant_equilibrium: Instantaneous equilibrium assumption
    :param Ct_star_top: Sediment concentration on flat top reach at equilibrium [-]
    :param Ct_star_down: Sediment concentration on D/S reach at equilibrium [-]
    :param Ct_in_top: Sediment concentration at the inlet of the flat top reach [kg/m^3]

    :return: Ct_out_top: Sediment concentration at the outlet of the flat top reach [kg/m^3]
    :return: Ct_out_down: Sediment concentration at the outlet of the D/S reach [kg/m^3]
    :return: Ct_in_down: Sediment concentration at the inlet of the D/S reach [kg/m^3]
    """
    # Adaptation length (Ls)
    Ls_top = lbda*B_w_top    #[m] Adaptation length characterizing the adjustment of sediment from a non-equilibrium state to the equilibrium state
    Ls_down = lbda*B_w_down

    # Sediment concentrations on flat top reach
    if dx[t]==0:
        Ct_out_top=0
    elif instant_equilibrium==False and Ls_top > 0:
        Ct_out_top = Ct_star_top[t+1] + (Ct_in_top-Ct_star_top[t+1])*math.exp(-dx[t]/Ls_top)
    else:
        Ct_out_top = Ct_star_top[t+1]

    # Sediment concentrations on downstream slope
    if Ct_out_top > Ct_star_down[t+1]:
        Ct_in_down = Ct_star_down[t+1]
    else:
        Ct_in_down = Ct_out_top
    if instant_equilibrium==False and Ls_down > 0:
        Ct_out_down = Ct_star_down[t+1] + (Ct_in_down-Ct_star_down[t+1])*math.exp(-ds[t]/Ls_down)
    else:
        Ct_out_down = Ct_star_down[t+1]

    return Ct_out_top, Ct_out_down, Ct_in_down




# Breach morphodynamics
#@njit()
def Dike_Morpho(ptsDS:np.ndarray, ptsUS:np.ndarray, dx, dx_min, ds, alpha, m_up, m_down, cb_coef, Lk, Su, Sd, h_d, h_b, z_b, dz_b, b_top, b_down, btop_effMax, \
                 Ae_tot_top, Ae_tot_down, dVb_top, dVb_down, dze_top, dze_down, b_top_down, b_down_down, b_down_up, B_down_up, B_down_down, t):
    """
    :param ptsDS: Points located upstream from the breach centerline
    :param ptsUS: Points located downstream from the breach centerline
    :param dx: Breach bottom length on flat top reach [m]
    :param dx_min: Minimum breach bottom length on flat top reach [m]
    :param ds: Breach bottom length on D/S reach [m]
    :param alpha: Slope of the downstream slope [-]
    :param m_up: Slope of the upstream side of the breach [-]
    :param m_down: Slope of the downstream side of the breach [-]
    :param cb_coef: Coefficient for the breach bottom width calculation [-]
    :param Lk: Dike crest width [m]
    :param Su: Upstream slope (H/V) [-]
    :param Sd: Downstream slope (H/V) [-]
    :param h_d: Dike height [m]
    :param h_b: Breach depth [m]
    :param z_b: Breach bottom elevation [m]
    :param dz_b: Breach bottom elevation variation [m]
    :param b_top: Breach bottom width on flat top reach [m]
    :param b_down: Breach bottom width on D/S reach [m]
    :param btop_effMax: Maximum effective breach width on flat top reach [m]
    :param Ae_tot_top: Total erodible surface at the breach location on flat top reach [m^2]
    :param Ae_tot_down: Total erodible surface at the breach location on D/S reach [m^2]
    :param dVb_top: Volume of sediment to be eroded on flat top reach [m^3]
    :param dVb_down: Volume of sediment to be eroded on D/S reach [m^3]
    :param dze_top: Eroded depth on flat top reach [m]
    :param dze_down: Eroded depth on D/S reach [m]
    :param b_top_down: Location of the D/S extremity of the breach bottom width on flat top reach [m]
    :param b_down_down: Location of the D/S extremity of the breach bottom width on D/S reach [m]
    :param b_down_up: Location of the U/S extremity of the breach bottom width on D/S reach [m]
    :param B_down_up: Location of the U/S extremity of the breach top width on D/S reach [m]
    :param t: Time index

    :return: update most of the inputs
    """

    p1d, p2d, p3d, p4d, p5d, p6d, p7d, p8d, p9d, p10d, p11d, p12d, p7d_bis, p12d_bis=ptsDS[0,:], ptsDS[1,:], ptsDS[2,:], ptsDS[3,:], ptsDS[4,:], ptsDS[5,:], ptsDS[6,:],\
        ptsDS[7,:], ptsDS[8,:], ptsDS[9,:], ptsDS[10,:], ptsDS[11,:], ptsDS[12,:], ptsDS[13,:]
    p1u, p2u, p3u, p4u, p5u, p6u, p7u, p8u, p9u, p10u, p11u, p12u, p7u_bis, p12u_bis=ptsUS[0,:], ptsUS[1,:], ptsUS[2,:], ptsUS[3,:], ptsUS[4,:], ptsUS[5,:], ptsUS[6,:],\
        ptsUS[7,:], ptsUS[8,:], ptsUS[9,:], ptsUS[10,:], ptsUS[11,:], ptsUS[12,:], ptsUS[13,:]

    # 3.1) Erosion depth on Flat Top Reach
    # ------------------------------------
    if dx[t]>0:
        if -Lk/2-Su*h_b+dx[t]+h_b/Sd[t]>Lk/2:
            As_up = 0.5*(LA.norm(np.cross((p6u-p7u),(p6u-p9u)))
            +LA.norm(np.cross((p7u_bis-p8u),(p7u_bis-p7u)))+LA.norm(np.cross((p9u-p7u),(p8u-p9u))))   #[m^2] Breach upstream side area at top reach
            As_down = As_up
#             As_down = 0.5*(LA.norm(np.cross(p6d-p7d,p6d-p9d))+LA.norm(np.cross(p7d_bis-p8d,p7d_bis-p7d))+LA.norm(np.cross(p9d-p7d,p8d-p9d))) #[m^2] Breach downstream side area at top reach
        elif -Lk/2-Su*h_b+dx[t]+h_b/Sd[t]>-Lk/2:
            As_up = 0.5*(LA.norm(np.cross((p6u-p7u),(p6u-p9u)))+LA.norm(np.cross((p8u-p7u),(p8u-p9u))))
            As_down = As_up
#             As_down = 0.5*(LA.norm(np.cross(p6d-p7d,p6d-p9d))+LA.norm(np.cross(p8d-p7d,p8d-p9d)))
        else:
            As_up = 0.5*(LA.norm(np.cross((p6u-p7u),(p6u-p9u)))+LA.norm(np.cross((p7u-p8u),(p8u-p9u))))
            As_down = As_up
#             As_down = 0.5*(LA.norm(np.cross(p6d-p7d,p6d-p9d))+LA.norm(np.cross(p7d-p8d,p8d-p9d)))
        if z_b[t]==0:
            As_bot=0
        else:
            As_bot = dx[t]*np.minimum(b_top[t],btop_effMax)
        if b_top[t]>b_down[t]:
            A_interf_up = 0.5*(LA.norm(np.cross((p8u-p11u),(p8u-p9u)))+LA.norm(np.cross((p10u-p9u),(p10u-p11u))))
            A_interf_down = 0.5*(LA.norm(np.cross((p8d-p11d),(p8d-p9d)))+LA.norm(np.cross((p10d-p9d),(p10d-p11d))))
        else:
            A_interf_up=0; A_interf_down=0
        if b_top[t] < btop_effMax:
            Ae_tot_top[t]=As_bot+As_up+As_down+A_interf_up+A_interf_down #[m^2] Total erodible surface at the breach location
        else:
            Ae_tot_top[t]=As_bot+As_down+A_interf_down
        # Corr1 & 2 are negligible but should be taken into account if rigourous
#         Corr1 = dx[t]*(1/tan((pi-np.arctan(1/abs(m_up)))/2) + abs(m_up)/2) #[m] Multiply by dze_top to get volume to be not considered when computing erosion depth (see small triangles in fig. 4.5 in Technical Report of Wu, page 41)
#         Corr2 = dx[t]*(1/tan((pi-np.arctan(1/abs(m_down)))/2) + abs(m_down)/2)
#         Delta = Ae_tot_top[t]**2-4*(Corr1+Corr2)*dVb_top
#         dze_top[t] = (Ae_tot_top[t]-np.sqrt(Delta))/(2*(Corr1+Corr2))   #[m] Breach bed level variation on flat top reach
        dze_top[t+1] = dVb_top/Ae_tot_top[t] # Without taking into account small triangles
    else:
        dze_top[t+1]=0

    # 3.2) Erosion depth on Downstream Slope Reach ->
    # assumed as triangular erosion: max at dike top; 0 at dike toe
    # -------------------------------------------------------------
    if b_top[t]<b_down[t]:
        A_interf_up = 0.5*(LA.norm(np.cross((p8u-p11u),(p8u-p9u)))+LA.norm(np.cross((p10u-p9u),(p10u-p11u))))
        A_interf_down = 0.5*(LA.norm(np.cross((p8d-p11d),(p8d-p9d)))+LA.norm(np.cross((p10d-p9d),(p10d-p11d))))
    else:
        A_interf_up=0
        A_interf_down=0
    if -Lk/2-Su*h_b+dx[t]+h_b/Sd[t]>Lk/2:
        As_up=0.5*(LA.norm(np.cross((p10u-p11u),(p10u-p1u))))    #[m^2] Breach upstream side area at Downstream Slope Reach
    elif -Lk/2-Su*h_b+dx[t]+h_b/Sd[t]>-Lk/2:
        As_up=0.5*(LA.norm(np.cross((p10u-p11u),(p10u-p1u)))+LA.norm(np.cross((p12u-p11u),(p12u-p1u))))
    else:
        As_up=0.5*(LA.norm(np.cross((p10u-p11u),(p10u-p1u)))+LA.norm(np.cross((p11u-p12u_bis),(p11u-p1u)))+LA.norm(np.cross((p12u-p12u_bis),(p12u-p1u))))
    As_down = As_up #[m^2] Breach downstream side area at Downstream Slope Reach
    if z_b[t]==0:
        As_bot=0  #[m^2] Breach downstream bottom area at Downstream Slope Reach
    else:
        As_bot = ds[t]*np.minimum(b_down[t],btop_effMax+np.abs(b_top_down[t]-b_down_down[t]))
    if b_top[t] < btop_effMax:
        Ae_tot_down[t]=As_bot+As_up+As_down+A_interf_up+A_interf_down    #[m^2] Total erodible surface at the breach downstream slope
    else:
        Ae_tot_down[t]=As_bot+As_down+A_interf_down;    #[m^2] Total erodible surface at the breach downstream slope
    if Ae_tot_down[t]==0:
        dze_down[t+1]=0
    else:
        dze_down[t+1]=dVb_down/Ae_tot_down[t]   #[m] Mean breach bed variation on downstream slope (perpendicular to the slope)
    dze_max=2*dze_down[t+1]                     #[m] Max erosion at breach flat top reach (triangular erosion -> no erosion at dam toe)
    # Downstream slope change
    alpha[t+1] = np.degrees(np.arctan(1/Sd[t]))                 #[deg] Angle between horizontal and downstream slope
    if alpha[t+1]<0:
        alpha[t+1]=0
    dalpha = np.degrees(np.arctan(np.abs(dze_max/ds[t]))) #[deg] Incremental angle induced by erosion
    if alpha[t+1]-dalpha<=0 or z_b[t]==0:
        Sd[t+1]=np.inf
    else:
        Sd[t+1]= 1/np.tan(np.radians(alpha[t+1]-dalpha))

    # 3.3) Breach Morphology Changes
    # ------------------------------
    if Sd[t+1]!=np.inf:
        if dx[t]>dx_min:
            dz_b[t+1]=dze_top[t+1]
        else:
            dz_b[t+1]=dze_max*np.cos(np.arctan(1/Sd[t+1]))
        # Erosion in the effective channel spread over the entire breach width
        dz_b[t+1] = dz_b[t+1]/b_top[t] * np.minimum(b_top[t],btop_effMax)
        z_b[t+1]=np.maximum(z_b[t]+dz_b[t+1],0)
    else:
        z_b[t+1]=0
        dz_b[t+1]=0

    # Downstream side reach (dB at flat top intersection)
    cb=np.minimum(1,np.maximum(0,cb_coef*b_top[t]/b_down[t]-(cb_coef-1)))       #[-] Correction factor
    h=(h_d-Sd[0]*h_d/Sd[t+1])*np.cos(np.arctan(1/Sd[t+1]))
    if b_top[t]<btop_effMax:
        delta_up=h*m_up
        db_down_up = dze_down[t+1]*(np.maximum(cb/np.sin(np.abs(np.arctan(1/m_up))),m_up)-m_up)#[m] Breach bottom width variation (upstream)
        dB_down_up = b_down_up[t]-np.abs(db_down_up)-delta_up-B_down_up         #[m] Breach top width variation (upstream)
    else:
        delta_up=0
        db_down_up = 0
        dB_down_up = 0
    delta_down=h*m_up
    db_down_down = dze_down[t+1]*(np.maximum(cb/np.sin(np.abs(np.arctan(1/m_down))),m_down)-m_down) #[m] Breach bottom width variation (downstream)
    dB_down_down = b_down_down[t]+np.abs(db_down_down)+delta_down-B_down_down;     #[m] Breach top width variation (downstream)
    # The following two lines are used by Wu (2016) but seem strange
#     db_down_up = cb*dze_down[t+1]*np.tan(np.arctan(1/m_up)/2)
#     db_down_down = cb*dze_down[t+1]*np.tan(np.arctan(1/m_down)/2)

#     if z_b[t+1]==zb_min
#         db_down_up = dB_down_up;                         #[m] Breach bottom width variation (upstream)
#         db_down_down = dB_down_down;                     #[m] Breach bottom width variation (downstream)
#     else
#         db_down_up = dze_down[t+1]*tan(np.arctan(1/m_up)/2)
#         db_down_down = dze_down[t+1]*tan(np.arctan(1/m_down)/2)
#     end
    # Flat top reach
    dB_top_up = dze_top[t+1]/np.sin(np.abs(np.arctan(1/m_up)))       #[m] Breach top width variation (upstream)
    dB_top_down = dze_top[t+1]/np.sin(np.abs(np.arctan(1/m_down)))   #[m] Breach top width variation (downstream)
    if z_b[t+1]!=0:
        db_top_up = dze_top[t+1]*np.tan(np.arctan(1/m_up)/2)      #[m] Breach bottom width variation (upstream)
        db_top_down = dze_top[t+1]*np.tan(np.arctan(1/m_down)/2)  #[m] Breach bottom width variation (downstream)
#         db_top_up = dze_top[t+1]*(1/np.sin(abs(np.arctan(1/m_up)))-m_up)     #[m] Breach bottom width variation (upstream)
#         db_top_down = dze_top[t+1]*(1/np.sin(abs(np.arctan(1/m_down)))-m_down) #[m] Breach bottom width variation (downstream)
    else:
        db_top_up = dB_top_up
        db_top_down = dB_top_down
    if b_top[t]>=btop_effMax:
        dB_top_up = 0
        db_top_up = 0

    return Ae_tot_top, Ae_tot_down, dze_top, dze_down, alpha, Sd, dz_b, z_b, delta_up, db_down_up, dB_down_up,\
        delta_down, db_down_down, dB_down_down, db_top_down, dB_top_down, db_top_up, dB_top_up