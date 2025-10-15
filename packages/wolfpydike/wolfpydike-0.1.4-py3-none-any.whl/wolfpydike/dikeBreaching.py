"""
Author: HECE - University of Liege, Vincent Schmitz
Date: 2025

Copyright (c) 2025 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import sys
import math
import time
import os
import json
from os.path import join
from pathlib import Path
import scipy.io as spio
import pandas as pd
import numpy as np
from math import sqrt, atan, sin, cos, tan
from scipy.interpolate import interp1d

from . import DLBreach_Modules
from . import PointsCoordinates
from .DLBreach_Modules import reservoir_types, riverbank_loc

class pyDike:

    def __init__(self, name=None):
        """
        :param name: [str] Name of the test
        :param store_dir: [str] Directory where the parameters are stored
        """

        # SET DEFAULT PARAMETERS
        # ----------------------

        # TEST DEFINITION
        # ---------------
        if name is not None:
            self.Test_ID=name
        else:
            self.Test_ID='pyDike0D' # Test default name

        # TIME PARAMETERS
        # ---------------
        self.dt=5 # [s] Default constant time step
        self.t_end=15000 # [s] End of the dike breaching simulation
        self.t_end_idx = int(self.t_end/self.dt)

        # SAVE RESULTS
        # ------------
        self.exportMainResults=False # Save evolution of breach extremities, discharge and main channel water level
        self.extractTriangulation=False # Triangulate the dike and save triangulation
        self.path_saveOutputs='' # Path to save triangulation data

        # PHYSICAL PARAMETERS
        # -------------------
        self.g=9.81          #[m/s^2] Gravitational acceleration
        self.d50=4.75*10**-3 #[m] Median grain size
        self.nu=10**-6       #[m^2/s] Water kinematic viscosity
        self.rho=1000        #[kg/m^3] Water density
        self.rho_s=2156      #[kg/m^3] Sediment density
        self.p = 0.22        #[-] Material porosity
        self.phi = 42        #[deg] Friction angle
        self.suspension=True # Specifies if suspension considered in the total sediment concentration

        # GEOMETRICAL PARAM.
        # ------------------
        # Dike geometry
        self.dam=True           # Dam or dike
        self.Su=2               #[-] Upstream slope (H/V)
        self.Sd_ini=2           #[-] Initial downstream slope (H/V)
        self.Lk=1               #[m] Initial crest width
        self.h_d=3              #[m] Dike height
        self.complete_erosion=False # Specifies if erosion can reach embankment bottom (if true -> classical Wu model)
        self.dx_min=self.d50
        self.xnotch_ini = 0      #[m] Position of the initial notch with respect to the local reference # Not very accurate, should be modified according to 2D simu
        self.ynotch_ini = 0      #[m]
        self.end_up =  -50       #[m] Position of the upstream extremity of the interpolation area w/r to the initial breach center line
        self.end_down = 50       #[m] Position of the downstream extremity of the interpolation area w/r to the initial breach center line
        # Location of the dike (rectangular in 2D) : corner (xmin;ymin) located at the dike upstream/left extremity, on the river/reservoir side !
        self.xmin_dike = self.xnotch_ini+self.end_up #[m] Xmin of the erodible dike
        self.ymin_dike = self.ynotch_ini-self.Su*self.h_d + self.Lk/2  #[m] Ymin of the erodible dike
        self.slope = 0                               #(V/H) Slope of the dike/dam foundation
        self.elevation_shift = 0                     #[m] Shift the altitude of the entire dike triangulation to fit the underlying topo
        self.riverbank = riverbank_loc.RIGHT.value   # On which side of the dam/dike is the reservoir/channel (left or right). By default, the structure crest is aligned with x axis.
        self.horiz_rotation = 0 #[deg] Rotation of the dike/dam in the horizontal plane.

        # Breach geometry
        self.m=1/tan(math.radians(self.phi))  #[-] Breach side slope (H/V)
        self.m_up=self.m         #[-] Upstream side slope of the breach (H/V)
        self.m_down=self.m       #[-] Downstream side slope of the breach (H/V)
        self.m_mean=(abs(self.m_down)+abs(self.m_up))/2
        self.h_b_ini=1      #[m] Initial breach depth
        self.b_ini=1        #[m] Initial breach bottom width

        # Main channel geometry
        self.reservoir_shape = reservoir_types.RECTANGULAR.value        # Shape of the main channel (dike) or reservoir (dam)
        # Param. if reservoir shape = 0 --> StageStorage (Stage storage curve available in the main channel/reservoir)
        self.pathStageStorage = ''       # Path to stage storage curve
        self.GI_Vres = 0
        # Param. if reservoir shape = 1 --> rectangular
        self.Ar = 10**4                 #[m^2] Reservoir surface area (constant)
        # Param. if reservoir shape = 2 --> trapezoidal
        self.lmc = 0                    #[m] Length
        self.wmc = 0                    #[m] Width at channel bottom
        self.S_lat = 0                  #[-] Lateral slope of the reservoir opposite to the dike/dam (H/V)

        # Floodplain geometry
        self.StageStorage_FP = False    # Stage storage curve available in the floodplain
        self.pathStageStorage_FP = ''   # Path to floodplain stage storage curve
        self.GI_VFP = 0

        # FLOW PARAMETERS
        # ---------------
        self.Qd=0               #[m^3/s] Drain discharge
        self.Qin=0              #[m^3/s] Inflow discharge
        self.z_s_ini=-999       #[m] Initial water level in the main channel
        self.z_t_ini=0          #[m] Tailwater level
        self.Qin_coef=1         # Multiplicative coefficient of Qin
        self.Qo_module=False    # Use a module to compute the outflow discharge
        self.Qo=0               # [m^3/s] Outflow discharge

        # EMPIRICAL PARAMETERS
        # --------------------
        self.c1 = 1.7 #[-] Parameter: 1.7 for Wu (Singh 1996); Morris et al. (2009): varies from 1.5 to 2.2 (sharped-edged to round-shaped broad crest)
        self.c2 = 1.3 #[-] Parameter: 1.3 for Wu (Singh 1996)
        self.c_eff = 1#[-] Modification of weir efficiency
        self.lambda_in=0    # Head water loss at breach inlet (used in Keulegan equation)
        self.lambda_out=1   # Head water loss at breach outlet (used in Keulegan equation)
        self.lambda_loss=self.lambda_in+self.lambda_out
        self.An=12          #[-] Empirical coef. (=16 for lab; =12 for field test) -> p.24 Wu 2016)
        self.An_prime=20    #[-] Empirical coef. in particule Manning's coef. formula
        self.n_min=0.016    #[-] Minimum value of Manning's coefficient
        self.lbda = 6       #[-] Adaptation length param. Wu=2; Wu mentioned also 3 for small-scale dyke breach (6 for field cases)
        self.instant_equilibrium = True
        self.theta_cr=0.049 #[-] Critical Shields parameter (Meyer-Peter and Müller)
        self.Sp=0.7         #[-] Corey shape factor (used in settling velocity)
        [self.C_stara, self.C_starb, self.C_starc, self.C_stard]=[20,1.5,45,1.15] # Suspended load coef
        [self.qb_stara, self.qb_starb]=[0.0053, 2.2]  # Bed load coef
        [self.lambda0a, self.lambda0b]=[0.22,0.15]    # Shear stress coef
        self.cb_coef=1.8
        self.b_eff_frac=np.inf # Fraction of the breach width considered as effective (cfr effective breach width). If >=1, full breach used

        self.params_dict = self.get_params()

    def run_initialization(self, params_dir = Path.cwd()):
        """
        Parameters initialization from external file .json
        :param params_dir: directory where the parameters enforced by the user are stored
        """

        self.set_params(file_name = self.Test_ID, store_dir = params_dir)

        # Data initialization
        self.h_down, self.h_top, self.Ve_tot, self.Ct_star_top, self.Ct_star_down, self.C_star_top, self.C_star_down, self.q_star_top, self.q_star_down, self.dV_top, self.dV_down, self.Ae_tot_down,\
            self.Ae_tot_top, self.dze_down, self.dze_top, self.alpha, self.dz_b, self.z_s, self.z_t, self.Qin_, self.Qb, self.z_b, self.U_b_top, self.U_b_down, self.Sd, self.ds, self.dx, self.db_top_up, self.db_top_down, self.db_down_up, self.db_down_down,\
            self.b_top_up, self.b_top_down, self.b_down_up, self.b_down_down, self.B_down, self.b_down, self.B_down_up, self.B_down_down, self.B_top, self.b_top, self.B_top_up,\
            self.B_top_down, self.Ct_out_top, self.Ct_out_down, self.n, self.n_prime, self.w_s, self.h_b, self.ze_down, self.H, self.V_FP, self.breach_activated, self.btop_effMax = self.initializeVectors(self.t_end_idx, self.d50, self.An, \
            self.An_prime, self.n_min, self.rho_s, self.rho, self.g, self.nu, self.Sp, self.h_b_ini, self.Sd_ini, self.Su, self.Lk, self.z_s_ini, self.z_t_ini, self.h_d, self.b_ini, self.m_up, self.m_down)

        # Initial dike geometry (defined by 28 points) --> t = 0
        self.ptsUS, self.ptsDS, self.coord_tri, self.idx_tri = PointsCoordinates.initialize(self.end_up, self.end_down, self.b_down[0], self.b_down_down, self.b_down_up, self.b_top[0], self.b_top_down, self.b_top_up, self.Lk, self.Sd[0], self.Su, self.h_d, self.h_b, self.z_b, self.m_down, self.m_up, self.dx)
        self.coord_tri = PointsCoordinates.adaptTriangulation(self.coord_tri, self.slope, flip=(self.riverbank == riverbank_loc.LEFT.value), horiz_rotation=self.horiz_rotation, elevation_shift=self.elevation_shift)
        self.coord_tri[:,0] = self.coord_tri[:,0]+self.xnotch_ini
        self.coord_tri[:,1] = self.coord_tri[:,1]+self.ynotch_ini

        # Output storage attributes
        self.triangulation_dict = {}
        self.data_export = np.zeros((self.t_end_idx,12))

    def run(self, t, dt=None, cur_time=None, coupled=False):

        ## 0. Class variables to local variables
        # --------------------------------------
        if dt is None or cur_time is None:
            dt = self.dt
            cur_time = t*dt

        #The following parameters are not modified during the simulation
        g, d50, rho, rho_s, p, phi, dam, Su, Sd_ini, Lk, h_d, dx_min, end_up, end_down, m, m_up, m_down, m_mean,\
        reservoir_shape, lmc, wmc, S_lat, slope, Qd, Qin, z_s_ini, z_t_ini, c1, c2, c_eff, lambda_loss, lbda, theta_cr, C_stara, \
        C_starb, C_starc, C_stard, qb_stara, qb_starb, lambda0a, lambda0b, cb_coef, b_eff_frac, Qo, Qin_coef, GI_Vres, Ar, GI_VFP = \
        self.g, self.d50, self.rho, self.rho_s, self.p, self.phi, self.dam, self.Su, self.Sd_ini, self.Lk, self.h_d, self.dx_min, self.end_up, self.end_down, self.m, self.m_up, self.m_down, self.m_mean,\
        self.reservoir_shape, self.lmc, self.wmc, self.S_lat, self.slope, self.Qd, self.Qin, self.z_s_ini, self.z_t_ini, self.c1, self.c2, self.c_eff, self.lambda_loss, self.lbda, self.theta_cr, self.C_stara, \
        self.C_starb, self.C_starc, self.C_stard, self.qb_stara, self.qb_starb, self.lambda0a, self.lambda0b, self.cb_coef, self.b_eff_frac, self.Qo, self.Qin_coef, self.GI_Vres, self.Ar, self.GI_VFP

        # The following parameters are modified during the simulation
        h_down, h_top, Ve_tot, Ct_star_top, Ct_star_down, C_star_top, C_star_down, q_star_top, q_star_down, dV_top, dV_down, Ae_tot_down,\
        Ae_tot_top, dze_down, dze_top, alpha, dz_b, z_s, z_t, Qin_, Qb, z_b, U_b_top, U_b_down, Sd, ds, dx, db_top_up, db_top_down, db_down_up, db_down_down,\
        b_top_up, b_top_down, b_down_up, b_down_down, B_down, b_down, B_down_up, B_down_down, B_top, b_top, B_top_up,\
        B_top_down, Ct_out_top, Ct_out_down, n, n_prime, w_s, h_b, ze_down, H, V_FP, btop_effMax =\
        self.h_down, self.h_top, self.Ve_tot, self.Ct_star_top, self.Ct_star_down, self.C_star_top, self.C_star_down, self.q_star_top, self.q_star_down, self.dV_top, self.dV_down, self.Ae_tot_down,\
        self.Ae_tot_top, self.dze_down, self.dze_top, self.alpha, self.dz_b, self.z_s, self.z_t, self.Qin_, self.Qb, self.z_b, self.U_b_top, self.U_b_down, self.Sd, self.ds, self.dx, self.db_top_up, self.db_top_down, self.db_down_up, self.db_down_down,\
        self.b_top_up, self.b_top_down, self.b_down_up, self.b_down_down, self.B_down, self.b_down, self.B_down_up, self.B_down_down, self.B_top, self.b_top, self.B_top_up,\
        self.B_top_down, self.Ct_out_top, self.Ct_out_down, self.n, self.n_prime, self.w_s, self.h_b, self.ze_down, self.H, self.V_FP, self.btop_effMax

        ## 1. Hydrodynamics
        # -----------------
        if coupled:
            [H,B_w_down,A_down,R_down,tau_b_down,B_w_top,A_top,R_top,tau_b_top,h_top[t+1],h_down[t+1]] =\
                DLBreach_Modules.Hydrodynamics2D(self.hbreach[t+1,:],self.zbbreach[t+1,:],z_b[t],z_s[t+1],z_t[t+1],Qb[t+1],b_top[t],btop_effMax,b_down[t],abs(b_top_down[t]-b_down_down[t]),h_down[t],m_up,m_down,m_mean,dx[t],Su,Sd[t],rho,g,n)
            if self.breach_activated==False and abs(Qb[t+1])>0:
                self.breach_activated=True
        else:
            if isinstance(Qin, interp1d):
                Qin_[t]=Qin(max(cur_time,0))
            else:
                Qin_[t]=Qin
            Qin_[t] = max([Qin_[t]*Qin_coef,0])

            if isinstance(Qd, interp1d):
                Qd_=Qd(max(cur_time,0))
            else:
                Qd_=Qd
            [z_s[t+1],z_t[t+1],V_FP,Qb[t+1],B_w_down,A_down,R_down,tau_b_down,B_w_top,A_top,R_top,tau_b_top,h_top[t+1],h_down[t+1]]=\
                    DLBreach_Modules.Hydrodynamics(z_b[t],z_s[t],z_t[t],b_top[t],btop_effMax,b_down[t],abs(b_top_down[t]-b_down_down[t]),h_top[t],h_down[t],\
                        H,m_up,m_down,m_mean,dx[t],Su,Sd[t],lambda_loss,c1,c2,c_eff,h_d,rho,g,reservoir_shape,lmc,wmc,S_lat,Qin_[t],Qd_,dt,n,dam,Qo,Ar,GI_Vres,GI_VFP,V_FP)

            if self.breach_activated==False and z_s[t]>z_b[t]:
                self.breach_activated=True

        ## 2. Sediment transport
        # ----------------------

        # 2.1) Settling velocity of sediments (w_s)
        # -----------------------------------------
        w_s_top = (1-Ct_out_top[t]/2)**4*w_s # Exponent -> [2.3;4.9] =4 for Wu
        w_s_down = (1-(Ct_out_down[t]+Ct_out_top[t])/2)**4*w_s

        # 2.2) Sediment Transport Capacity (downstream slope/top)
        # -------------------------------------------------------
        [Ct_star_top[t+1],q_star_top[t+1],C_star_top[t+1],U_b_top[t+1]] = DLBreach_Modules.Sediment_Transport_Capacity(Qb[t+1],A_top,R_top,rho_s,rho,g,w_s_top,d50,B_w_top,n,n_prime,tau_b_top,theta_cr,math.inf,phi,C_stara,C_starb,C_starc,C_stard,qb_stara,qb_starb,lambda0a,lambda0b,self.suspension)
        [Ct_star_down[t+1],q_star_down[t+1],C_star_down[t+1],U_b_down[t+1]]= DLBreach_Modules.Sediment_Transport_Capacity(Qb[t+1],A_down,R_down,rho_s,rho,g,w_s_down,d50,B_w_down,n,n_prime,tau_b_down,theta_cr,Sd[t],phi,C_stara,C_starb,C_starc,C_stard,qb_stara,qb_starb,lambda0a,lambda0b,self.suspension)

        # 2.3) Sediment concentrations
        # ----------------------------
        Ct_in_top=0               #[-] Hypo: clear water condition at the breach inlet
        [Ct_out_top[t+1], Ct_out_down[t+1], Ct_in_down] = DLBreach_Modules.Sediment_Concentrations(t, dx, ds, lbda, B_w_top, B_w_down, self.instant_equilibrium, Ct_star_top, Ct_star_down, Ct_in_top)

        # 2.4) Dike volume variation
        # --------------------------
        dV_top[t+1] = Qb[t+1]*(Ct_in_top-Ct_out_top[t+1])*dt/(1-p)      # Top
        dV_down[t+1] = Qb[t+1]*(Ct_in_down-Ct_out_down[t+1])*dt/(1-p)   # Downstream slope
        Ve_tot[t+1] = Ve_tot[t]+dV_top[t+1]+dV_down[t+1] # Total eroded volume

        ## 3. Morphodynamics
        # ------------------
        Ae_tot_top, Ae_tot_down, dze_top, dze_down, alpha, Sd, dz_b, z_b, delta_up, db_down_up, dB_down_up, delta_down, \
        db_down_down, dB_down_down, db_top_down, dB_top_down, db_top_up, dB_top_up = DLBreach_Modules.Dike_Morpho(np.array(self.ptsDS, dtype=np.float64), np.array(self.ptsUS, dtype=np.float64),\
                    dx, dx_min, ds, alpha, m_up, m_down, cb_coef, Lk, Su, Sd, h_d, h_b, z_b, dz_b, b_top, b_down, btop_effMax,\
                    Ae_tot_top, Ae_tot_down, dV_top[t+1], dV_down[t+1], dze_top, dze_down, b_top_down, b_down_down, b_down_up, B_down_up, B_down_down, t)

        ## 4. Update of geom. variables
        # -----------------------------
        H, h_b, dx, ds, m_up, m_down, m_mean, b_down_up, b_down_down, b_down, B_down, b_top_up, b_top_down, b_top, B_top, btop_effMax =\
            self.updateGeomVariables(t, z_s, z_b, h_d, ds, dx, dx_min, Lk, Sd, Su, m, b_top, b_down_up, db_down_up, b_down_down, db_down_down,\
                delta_up, delta_down, B_down, b_down, B_down_up, b_top_up, b_top_down, db_top_up, db_top_down, B_top, btop_effMax, b_eff_frac)


        ## 5. Triangulation and data storage
        # ----------------------------------

        ## 5.1 Compute points coordinates + triangulation
        # -----------------------------------------------
        if self.breach_activated==False: # Initial shape of the dike
            self.ptsUS, self.ptsDS, self.coord_tri, self.idx_tri = PointsCoordinates.initialize(end_up, end_down, b_down[0], b_down_down, b_down_up, b_top[0], b_top_down, b_top_up, Lk, Sd[0], Su, h_d, h_b, z_b, m_down, m_up, dx, t+1)
        else: # Altered shape of the dike
            self.ptsUS, self.ptsDS, self.coord_tri, self.idx_tri = PointsCoordinates.update(end_up, end_down, b_down[0], b_down_down, b_down_up, b_top[0], b_top_down, b_top_up, Lk, Sd, Su, h_d, h_b, z_b, m_down, m_up, dx, t)

        ## 5.2 Store triangulation and main outputs
        # -----------------------------------------
        # Origin of the coordinates = U/S extremity of the dike, at its toe located on the river/reservoir side
        self.coord_tri = PointsCoordinates.adaptTriangulation(self.coord_tri, slope, flip=(self.riverbank == riverbank_loc.LEFT.value), horiz_rotation=self.horiz_rotation, elevation_shift=self.elevation_shift)
        self.coord_tri[:,0] = self.coord_tri[:,0]+self.xnotch_ini
        self.coord_tri[:,1] = self.coord_tri[:,1]+self.ynotch_ini

        self.triangulation_dict[str(int(t))] = {"time": float(cur_time),"XYZ": self.coord_tri.tolist(),"idx_triangles": self.idx_tri.tolist()}
        self.data_export[t,:] = [cur_time, Qin_[t], b_top_up[t]-m*h_b, b_top_down[t]+m*h_b, z_b[t], Qb[t+1],z_s[t],z_t[t], dV_top[t+1], dV_down[t+1], dx[t], Sd[t]]


        ## 6. Update class variables
        # --------------------------
        self.h_down, self.h_top, self.Ve_tot, self.Ct_star_top, self.Ct_star_down, self.C_star_top, self.C_star_down, self.q_star_top, self.q_star_down, self.dV_top, self.dV_down, self.Ae_tot_down,\
        self.Ae_tot_top, self.dze_down, self.dze_top, self.alpha, self.dz_b, self.z_s, self.z_t, self.Qin_, self.Qb, self.z_b, self.U_b_top, self.U_b_down, self.Sd, self.ds, self.dx, self.db_top_up, self.db_top_down, self.db_down_up, self.db_down_down,\
        self.b_top_up, self.b_top_down, self.b_down_up, self.b_down_down, self.B_down, self.b_down, self.B_down_up, self.B_down_down, self.B_top, self.b_top, self.B_top_up,\
        self.B_top_down, self.Ct_out_top, self.Ct_out_down, self.n, self.n_prime, self.w_s, self.h_b, self.ze_down, self.H, self.V_FP, self.btop_effMax =\
        h_down, h_top, Ve_tot, Ct_star_top, Ct_star_down, C_star_top, C_star_down, q_star_top, q_star_down, dV_top, dV_down, Ae_tot_down,\
        Ae_tot_top, dze_down, dze_top, alpha, dz_b, z_s, z_t, Qin_, Qb, z_b, U_b_top, U_b_down, Sd, ds, dx, db_top_up, db_top_down, db_down_up, db_down_down,\
        b_top_up, b_top_down, b_down_up, b_down_down, B_down, b_down, B_down_up, B_down_down, B_top, b_top, B_top_up,\
        B_top_down, Ct_out_top, Ct_out_down, n, n_prime, w_s, h_b, ze_down, H, V_FP, btop_effMax

        ## 7. Save final results
        # ----------------------
        if t==self.t_end_idx-2:
            self.saveResults()

            [Qb_peak, t_peak] = self.get_peakDischargeFeatures()
            print('Qb_peak = ' + str(round(Qb_peak*1000,2)) + ' [l/s]')
            print('t_peak = ' + str(t_peak) + '[s]')
            print('B_top_final = ' + str(B_top[np.nonzero(B_top)[0][-1]]) + '[m]')

    def initializeVectors(self, t_end_idx, d50, An, An_prime, n_min, rho_s, rho, g, nu, Sp, h_b_ini, Sd_ini, Su, Lk, z_s_ini, z_t_ini, h_d, b_ini, m_up, m_down):
        """ Data initialization

        :param t_end_idx: [int] Number of time steps
        :param d50: [float] Median grain size
        :param An: [float] Empirical coef. (=16 for lab; =12 for field test) -> p.24 Wu 2016)
        :param An_prime: [float] Empirical coef. in particule Manning's coef. formula
        :param n_min: [float] Minimum value of Manning's coefficient
        :param rho_s: [float] Sediment density
        :param rho: [float] Water density
        :param g: [float] Gravitational acceleration
        :param nu: [float] Water kinematic viscosity
        :param Sp: [float] Corey shape factor (used in settling velocity)
        :param h_b_ini: [float] Initial breach depth
        :param Sd_ini: [float] Initial downstream slope (H/V)
        :param Su: [float] Upstream slope (H/V)
        :param Lk: [float] Dike crest width
        :param z_s_ini: [float] Initial water level in the main channel
        :param z_t_ini: [float] Initial water level in the floodplain
        :param h_d: [float] Dike height
        :param b_ini: [float] Initial breach bottom width
        :param m_up: [float] Upstream side slope of the breach (H/V)
        :param m_down: [float] Downstream side slope of the breach (H/V)
        :return: [np.array] Initialized vectors
        """

        # Memory preallocation (CPU optimization)
        time_length = t_end_idx+1
        h_down = np.zeros(time_length) # Initial water level on the downstream slope
        h_top = np.zeros(time_length)  # Initial water level on the flat top reach
        Ve_tot = np.zeros(time_length) # Initial eroded volume
        Ct_star_top = np.zeros(time_length)
        Ct_star_down = np.zeros(time_length)
        C_star_top = np.zeros(time_length)
        C_star_down = np.zeros(time_length)
        q_star_top = np.zeros(time_length)
        q_star_down = np.zeros(time_length)
        Ct_out_top = np.zeros(time_length) # Initial sediment concentrations
        Ct_out_down = np.zeros(time_length)
        dV_top = np.zeros(time_length)
        dV_down = np.zeros(time_length)
        Ae_tot_down = np.zeros(time_length)
        Ae_tot_top = np.zeros(time_length)
        dze_down = np.zeros(time_length)
        dze_top = np.zeros(time_length)
        alpha = np.zeros(time_length)
        dz_b = np.zeros(time_length)
        z_s= np.zeros(time_length)
        z_t= np.zeros(time_length)
        Qin_ = np.zeros(time_length)
        Qb = np.zeros(time_length)
        z_b = np.zeros(time_length)
        U_b_top = np.zeros(time_length)
        U_b_down = np.zeros(time_length)
        Sd = np.zeros(time_length)
        ds = np.zeros(time_length)
        dx = np.zeros(time_length)
        db_top_up = np.zeros(time_length)   #[m] Upstream breach bottom width increment
        db_top_down = np.zeros(time_length) #[m] Downstream breach bottom width increment
        b_down_up = np.zeros(time_length)
        b_top_up = np.zeros(time_length)
        b_down_down = np.zeros(time_length)
        b_top_down = np.zeros(time_length)
        B_down = np.zeros(time_length)
        B_top = np.zeros(time_length)
        b_down = np.zeros(time_length)
        b_top = np.zeros(time_length)

        # Manning roughness coefficient
        n=max(d50**(1./6.)/An,n_min)    #[s/m^(1/3)] Equal to 0.018 for Ismail p.39 Thesis
        n_prime = max(d50**(1./6.)/An_prime,n_min) #[s/m^(1/3)] Particule Manning coefficient

        # Settling velocity of sediments parameters
        # -----------------------------------------
        d_star = ((rho_s-rho)/rho*g/nu**2)**(1./3)*d50# [-] Adim. grain median size
        M=53.5*math.exp(-0.65*Sp)
        N=5.65*math.exp(-2.5*Sp)
        nn=0.7+0.9*Sp
        w_s = M*nu/(N*d50)*(sqrt(1./4+(4*N*d_star**3/(3*M**2))**(1./nn))-0.5)**nn #[m/s] Book "Computational River Dynamics", p.66 -> Used by Wu
        #w_s = nu/d50*(sqrt(25+1.2*d_star**2)-5)**1.5;#[m/s] Cheng (1997) + book Computational River Dynamics, p.62
        #w_s = 1.1*sqrt(g*(rho_s-rho)/rho*d50);     #[m/s] Used by Mike Eve

        # Geometrical parameters initialization
        # -------------------------------------
        h_b=h_b_ini      #[m] Breach depth
        ze_down=0        #[m] Mean erosion depth on downstream slope (perpendicular to the slope)
        Sd[0] = Sd_ini   #[-] Dike upstream slope
        z_s[0] = z_s_ini #[m] Water level in the main channel
        z_t[0] = z_t_ini #[m] Water level in the floodplain
        z_b[0] = h_d-h_b #[m] Breach bottom elevation (at flat top reach)
        H=z_s[0]-z_b[0]  #[m] Headwater level above the breach bottom
        V_FP = 0               #[m^3] Initial water volume in the floodplain
        breach_activated=False # Defines if breaching has been initiated
        # Flat top reach
        B_ini=b_ini+h_b_ini*(m_up+m_down) #[m] Initial breach top width
        b_top_up[0]=-b_ini/2              #[m] Initial location of breach upstream extremity (bottom)
        b_top_down[0]=b_top_up[0]+b_ini   #[m] Initial location of breach downstream extremity (bottom)
        B_top_up=b_top_up-m_up*h_b_ini    #[m] Initial location of breach upstream extremity (top)
        B_top_down=B_top_up+B_ini         #[m] Initial location of breach downstream extremity (top)
        dB_top_up=0        #[m] Upstream breach top width increment
        dB_top_down=0      #[m] Downstream breach top width increment
        B_top[0] = B_ini+dB_top_down-dB_top_up           #[m] Breach top width
        b_top[0] = b_ini+db_top_down[0]-db_top_up[0]  #[m] Breach bottom width
        btop_effMax = math.inf # Maximum effective breach width on flat top reach (used for erosion)
        dx[0]=Lk+h_d*Sd[0]-Sd[0]*z_b[0]+Su*h_b #[m] Initial breach bottom width (perpendicular to the main channel)
        # Downstream slope reach (no initial erosion on this side)
        b_down_up[0]=b_top_up[0]          #[m] Initial location of breach upstream extremity (bottom)
        b_down_down[0]=b_down_up[0]+b_ini #[m] Initial location of breach downstream extremity (bottom)
        B_down_up=b_down_up[0]            #[m] Initial location of breach upstream extremity (top)
        B_down_down=b_down_down[0]        #[m] Initial location of breach downstream extremity (top)
        db_down_up=0        #[m] Upstream breach bottom width increment
        db_down_down=0      #[m] Downstream breach bottom width increment
        b_down[0] = b_ini+db_down_down-db_down_up    #[m] Breach bottom width
        B_down[0] = b_down[0]                        #[m] Breach top width
        ds[0]=z_b[0]*sqrt(1+Sd[0]**2)          #[m] Initial length of the breach downstream side slope (perpendicular to the main channel)

        return h_down, h_top, Ve_tot, Ct_star_top, Ct_star_down, C_star_top, C_star_down, q_star_top, q_star_down, dV_top, dV_down, Ae_tot_down,\
            Ae_tot_top, dze_down, dze_top, alpha, dz_b, z_s, z_t, Qin_, Qb, z_b, U_b_top, U_b_down, Sd, ds, dx, db_top_up, db_top_down, db_down_up, db_down_down,\
            b_top_up, b_top_down, b_down_up, b_down_down, B_down, b_down, B_down_up, B_down_down, B_top, b_top, B_top_up,\
            B_top_down, Ct_out_top, Ct_out_down, n, n_prime, w_s, h_b, ze_down, H, V_FP, breach_activated, btop_effMax

    def updateGeomVariables(self, t, z_s, z_b, h_d, ds, dx, dx_min, Lk, Sd, Su, m, b_top, b_down_up, db_down_up, b_down_down, db_down_down, delta_up, delta_down,\
        B_down, b_down, B_down_up, b_top_up, b_top_down, db_top_up, db_top_down, B_top, btop_effMax, b_eff_frac):
        """
        :param t: int Current time step
        :param z_s: np.array Water level in the main channel
        :param z_b: np.array Breach bottom elevation (at flat top reach)
        :param h_d: float Dike height
        :param ds: np.array Length of the breach downstream side slope (perpendicular to the main channel)
        :param dx: np.array Breach bottom length (perpendicular to the main channel)
        :param dx_min: float Minimum breach bottom length
        :param Lk: float Length of the breach
        :param Sd: np.array Dike upstream slope
        :param Su: float Dike downstream slope
        :param m: float Breach side slope
        :param b_top: np.array Breach bottom width on the flat top reach
        :param b_down_up: np.array Location of breach upstream extremity (bottom)
        :param db_down_up: float Upstream breach bottom width increment
        :param b_down_down: np.array Location of breach downstream extremity (bottom)
        :param db_down_down: float Downstream breach bottom width increment
        :param delta_up: float Upstream breach top width increment
        :param delta_down: float Downstream breach top width increment
        :param B_down: np.array Breach top width
        :param b_down: np.array Breach bottom width on the downstream slope
        :param B_down_up: np.array Location of breach upstream extremity (top)
        :param b_top_up: np.array Location of breach upstream extremity (bottom)
        :param b_top_down: np.array Location of breach downstream extremity (bottom)
        :param db_top_up: np.array Upstream breach top width increment
        :param db_top_down: np.array Downstream breach top width increment
        :param B_top: np.array Breach top width
        :param btop_effMax: float Maximum effective breach width on flat top reach (used for erosion)
        :param b_eff_frac: float Fraction of the breach width considered as effective (cfr effective breach width). If >=1, full breach used
        :return: float, float, np.array, np.array, float, float, float, np.array, np.array, np.array, np.array, np.array, np.array, np.array, np.array, np.array, float
        """

        # General
        H = max(z_s[t+1]-z_b[t+1],0)
        h_b = h_d-z_b[t+1]
        if dx[t]==dx_min:
            dx[t+1]=dx_min
        else:
            if Sd[t+1]==math.inf:
                dx[t+1]=dx[t]
            else:
                dx[t+1]=max(Lk+h_d*Sd[0]-Sd[t+1]*z_b[t+1]+Su*h_b,dx_min)
        ds[t+1]=max(0,((Lk+(Sd[0]+Su)*h_d)-dx[t+1]-z_b[t+1]*Su)/cos(atan(1./Sd[t+1])))
        if z_b[t+1]==0:
            m_up = m   #(B_down_up[t+1]-b_down_up[t+1])/h_b;
            m_down = m #(B_down_down[t+1]-b_down_down[t+1])/h_b;
        else:
            m_up = m   #(B_top_up[t+1]-b_top_up[t+1])/h_b;
            m_down = m #(B_top_down[t+1]-b_top_down[t+1])/h_b;
        m_mean = (abs(m_down)+abs(m_up))/2

        # Downstream slope reach
        if b_top[t]< btop_effMax:
            b_down_up[t+1]= b_down_up[t]-abs(db_down_up)
            B_down_up = b_down_up[t+1]-delta_up
        else: # Breach upstream extremities are unchanged
            b_down_up[t+1] = b_down_up[t]
        b_down_down[t+1] = b_down_down[t]+abs(db_down_down)
        B_down_down = b_down_down[t+1]+delta_down
        B_down[t+1] = B_down_down-B_down_up
        b_down[t+1] = b_down_down[t+1]-b_down_up[t+1]
        # Flat top reach
        if dx[t+1]==0 or z_b[t+1]==0:
            if z_b[t+1]==0:
                b_top_up[t+1] = b_down_up[t+1]
                b_top_down[t+1] = b_down_down[t+1]
                b_top[t+1] = b_down[t+1]
                B_top_up = b_top_up[t+1]-m_up*(h_d-z_b[t+1])
                B_top_down = b_top_down[t+1]+m_down*(h_d-z_b[t+1])
                B_top[t+1] = B_top_down-B_top_up
                B_down[t+1] = B_top[t+1]
            else: # Not super rigorous
                B_top_up = B_down_up
                B_top_down = B_down_down
                B_top[t+1] = B_down[t+1]
                b_top_up[t+1] = b_down_up[t+1]
                b_top_down[t+1] = b_down_down[t+1]
                b_top[t+1] = b_down[t+1] # b_down can become HUGE when Ae_tot_down -> 0 : dangerous condition
        else:
            if b_top[t]< btop_effMax:
                b_top_up[t+1] = max(b_top_up[t]-abs(db_top_up),b_down_up[t+1])         # Breach bottom width on flat top reach is always smaller than breach bottom width on D/S reach
                B_top_up = b_top_up[t+1]-m_up*(h_d-z_b[t+1])
            else: # Breach upstream extremities are unchanged
                b_top_up[t+1] = b_top_up[t]
            b_top_down[t+1] = min(b_top_down[t]+abs(db_top_down),b_down_down[t+1])
            b_top[t+1] = b_top_down[t+1]-b_top_up[t+1]
            B_top_down = b_top_down[t+1]+m_down*(h_d-z_b[t+1])
            B_top[t+1] = B_top_down-B_top_up
        if z_b[t+1]>0:
            btop_effMax = math.inf # Symmetric breach expansion
        else:
            btop_effMax = b_top[t+1]*b_eff_frac # Non-symmetric breach expansion

        return H, h_b, dx, ds, m_up, m_down, m_mean, b_down_up, b_down_down, b_down, B_down, b_top_up, b_top_down, b_top, B_top, btop_effMax

    def get_peakDischargeFeatures(self):
        Qb_peak = max(self.Qb)
        t_peak = ((np.where(self.Qb==Qb_peak)-next((x for x in self.Qb if x>=0), 0))*self.dt)[0][0]
        return Qb_peak, t_peak

    def get_VolumeFP(self):
        '''
        return: Time evolution of the water volume in the floodplain
        '''
        time = np.arange(0,self.t_end_idx)
        Volume_FP = np.cumsum(self.Qb)
        return np.column_stack([time, Volume_FP])

    def get_series_toDict(self):
        """ Returns time evolution of the main outputs as a dictionary
        Time [s] / Qin [m^3/s] / Btop_US [m] / Btop_DS [m] / z_b [m] / Qb [m^3/s] / z_s [m] / z_t [m] / dV_top [m^3] / dV_down [m^3] / dx [m] / Sd [-]
        :return: dict Dictionary containing the main outputs
        """
        mainOutputs_dict = {}
        mainOutputs_dict['Time [s]'] = self.data_export[:,0].tolist()
        mainOutputs_dict['Qin [m^3/s]'] = self.data_export[:,1].tolist()
        mainOutputs_dict['Btop_US [m]'] = self.data_export[:,2].tolist()
        mainOutputs_dict['Btop_DS [m]'] = self.data_export[:,3].tolist()
        mainOutputs_dict['z_b [m]'] = self.data_export[:,4].tolist()
        mainOutputs_dict['Qb [m^3/s]'] = self.data_export[:,5].tolist()
        mainOutputs_dict['z_s [m]'] = self.data_export[:,6].tolist()
        mainOutputs_dict['z_t [m]'] = self.data_export[:,7].tolist()
        mainOutputs_dict['dV_top [m^3]'] = self.data_export[:,8].tolist()
        mainOutputs_dict['dV_down [m^3]'] = self.data_export[:,9].tolist()
        mainOutputs_dict['dx [m]'] = self.data_export[:,10].tolist()
        mainOutputs_dict['Sd [-]'] = self.data_export[:,11].tolist()
        return mainOutputs_dict

    def set_series_fromDict(self, mainOutputs_dict):
        """
        Store simulation results from a dictionary to a ND array associated to the dikeBreaching class
        :param outputDict: dict Dictionary containing the simulation results
        """
        self.data_export = np.zeros((len(np.array(mainOutputs_dict['Time [s]'])),12))
        self.data_export[:,0] = np.array(mainOutputs_dict['Time [s]'])
        self.data_export[:,1] = np.array(mainOutputs_dict['Qin [m^3/s]'])
        self.data_export[:,2] = np.array(mainOutputs_dict['Btop_US [m]'])
        self.data_export[:,3] = np.array(mainOutputs_dict['Btop_DS [m]'])
        self.data_export[:,4] = np.array(mainOutputs_dict['z_b [m]'])
        self.data_export[:,5] = np.array(mainOutputs_dict['Qb [m^3/s]'])
        self.data_export[:,6] = np.array(mainOutputs_dict['z_s [m]'])
        self.data_export[:,7] = np.array(mainOutputs_dict['z_t [m]'])
        self.data_export[:,8] = np.array(mainOutputs_dict['dV_top [m^3]'])
        self.data_export[:,9] = np.array(mainOutputs_dict['dV_down [m^3]'])
        self.data_export[:,10] = np.array(mainOutputs_dict['dx [m]'])
        self.data_export[:,11] = np.array(mainOutputs_dict['Sd [-]'])
        return

    def saveResults(self):
        '''
        Save simu parametrization (.json) + main outputs and/or triangulation data in .txt/.json file
        '''
        self.save_params(file_name=str(self.Test_ID)+'_paramsDike.json', store_dir=Path(self.path_saveOutputs))
        if self.exportMainResults:
            np.savetxt(self.path_saveOutputs+'\\' +str(self.Test_ID)+ '_mainOutputs.txt', self.data_export, delimiter="\t", header="Time [s]\tQin [m^3/s]\tBtop_US [m]\tBtop_DS [m]\tz_b [m]\tQb [m^3/s]\tz_s [m]\tz_t [m]\tdV_top [m^3]\tdV_down [m^3]\tdx [m]\tSd [-]", comments='', fmt="%.3f")
            print('Main outputs saved to '+self.path_saveOutputs+'\\' +str(self.Test_ID)+ '_mainOutputs.txt')
        if self.extractTriangulation:
            with open(self.path_saveOutputs+'\\' +str(self.Test_ID)+ '_triangulation.json', "w") as f:
                json.dump(self.triangulation_dict, f, indent=4)
            print('Triangulation data saved to '+self.path_saveOutputs+'\\' +str(self.Test_ID)+ '_triangulation.json')
        return

    def update_paramsDict(self, params_dict):
        """
        Update the parameters dictionary with new values

        :param params_dict: dict Dictionary containing the parameters
        """
        self.params_dict = params_dict
        self.set_params()

    def set_params(self, file_name='', store_dir=None):
        """
        Set simulation parameters (modified from default values) based on a parameters dictionary or .json file

        :param file_name: str Name of the file containing the parameters
        :param store_dir: str Directory where the file is stored
        """

        if file_name != '' and store_dir != None:
            # Updates self.params_dict based on a .json file
            self.read_params(file_name, store_dir)

        # Load the parameters
        self.Test_ID = self.params_dict["TEST DEFINITION"]["Test_ID"]["value"]

        self.dt = self.params_dict["TIME PARAMETERS"]["dt"]["value"]
        self.t_end = self.params_dict["TIME PARAMETERS"]["t_end"]["value"]
        self.t_end_idx = int(self.t_end/self.dt)

        self.exportMainResults = str(self.params_dict["SAVE OUTPUTS"]["exportMainResults"]["value"]).lower()=="true"
        self.extractTriangulation = str(self.params_dict["SAVE OUTPUTS"]["extractTriangulation"]["value"]).lower()=="true"
        self.path_saveOutputs = self.params_dict["SAVE OUTPUTS"]["path_saveOutputs"]["value"]

        self.g = self.params_dict["PHYSICAL PARAMETERS"]["g"]["value"]
        self.d50 = self.params_dict["PHYSICAL PARAMETERS"]["d50"]["value"]
        self.nu = self.params_dict["PHYSICAL PARAMETERS"]["nu"]["value"]
        self.rho = self.params_dict["PHYSICAL PARAMETERS"]["rho"]["value"]
        self.rho_s = self.params_dict["PHYSICAL PARAMETERS"]["rho_s"]["value"]
        self.p = self.params_dict["PHYSICAL PARAMETERS"]["p"]["value"]
        self.phi = self.params_dict["PHYSICAL PARAMETERS"]["phi"]["value"]
        self.suspension = self.params_dict["PHYSICAL PARAMETERS"]["suspension"]["value"]

        self.dam = str(self.params_dict["GEOMETRICAL PARAM. DIKE"]["dam"]["value"]).lower()=="true"
        self.Su = self.params_dict["GEOMETRICAL PARAM. DIKE"]["Su"]["value"]
        self.Sd_ini = self.params_dict["GEOMETRICAL PARAM. DIKE"]["Sd_ini"]["value"]
        self.Lk = self.params_dict["GEOMETRICAL PARAM. DIKE"]["Lk"]["value"]
        self.h_d = self.params_dict["GEOMETRICAL PARAM. DIKE"]["h_d"]["value"]
        self.complete_erosion = str(self.params_dict["GEOMETRICAL PARAM. DIKE"]["complete_erosion"]["value"]).lower()=="true"
        if self.complete_erosion:
            self.dx_min=0
        else:
            self.dx_min=self.d50
        self.end_up = self.params_dict["GEOMETRICAL PARAM. DIKE"]["end_up"]["value"]
        self.end_down = self.params_dict["GEOMETRICAL PARAM. DIKE"]["end_down"]["value"]
        self.xnotch_ini = self.params_dict["GEOMETRICAL PARAM. DIKE"]["xnotch_ini"]["value"]
        self.ynotch_ini = self.params_dict["GEOMETRICAL PARAM. DIKE"]["ynotch_ini"]["value"]
        self.xmin_dike = self.xnotch_ini+self.end_up #[m] Xmin of the erodible dike
        self.ymin_dike = self.ynotch_ini-self.Su*self.h_d + self.Lk/2 #[m] Ymin of the erodible dike
        self.slope = self.params_dict["GEOMETRICAL PARAM. DIKE"]["slope"]["value"]
        self.elevation_shift = self.params_dict["GEOMETRICAL PARAM. DIKE"]["elevation_shift"]["value"]
        self.riverbank = self.params_dict["GEOMETRICAL PARAM. DIKE"]["riverbank"]["value"]
        self.horiz_rotation = self.params_dict["GEOMETRICAL PARAM. DIKE"]["horiz_rotation"]["value"]


        self.h_b_ini = self.params_dict["GEOMETRICAL PARAM. BREACH"]["h_b_ini"]["value"]
        self.b_ini = self.params_dict["GEOMETRICAL PARAM. BREACH"]["b_ini"]["value"]
        self.m=1/tan(math.radians(self.phi))  #[-] Breach side slope (H/V)
        self.m_up=self.m         #[-] Upstream side slope of the breach (H/V)
        self.m_down=self.m       #[-] Downstream side slope of the breach (H/V)
        self.m_mean=(abs(self.m_down)+abs(self.m_up))/2 #[-] Mean side slope of the breach (H/V)

        self.reservoir_shape = self.params_dict["GEOMETRICAL PARAM. MAIN CHANNEL"]["reservoir_shape"]["value"]
        self.lmc = self.params_dict["GEOMETRICAL PARAM. MAIN CHANNEL"]["lmc"]["value"]
        self.wmc = self.params_dict["GEOMETRICAL PARAM. MAIN CHANNEL"]["wmc"]["value"]
        self.Ar = self.params_dict["GEOMETRICAL PARAM. MAIN CHANNEL"]["Ar"]["value"]
        if self.reservoir_shape == reservoir_types.STAGESTORAGE.value: # 'stagestorage'
            self.pathStageStorage = self.params_dict["GEOMETRICAL PARAM. MAIN CHANNEL"]["pathStageStorage"]["value"]
            if self.pathStageStorage.endswith(".mat"):
                Vres = spio.loadmat(self.pathStageStorage)
                Vres = Vres[Path(self.pathStageStorage).stem] # %[m^3/s] z_s as a function of the volume in the reservoir
            elif self.pathStageStorage.endswith(".txt"):
                # Load text file (assumes tab or space separation)
                Vres = np.loadtxt(self.pathStageStorage, delimiter=None) # Auto-detects delimiter (tab/space)
            self.GI_Vres = interp1d(Vres[:,0]-Vres[-1,0]+self.h_d,Vres[:,1]) #[m^3/s] Volume in the reservoir as a function of z_s !! The max water level is at the level of the dike crest !!
        else:
            self.GI_Vres = 0

        self.StageStorage_FP = str(self.params_dict["GEOMETRICAL PARAM. FLOODPLAIN"]["StageStorage_FP"]["value"]).lower() == "true"
        if self.StageStorage_FP == True:
            self.pathStageStorage_FP = self.params_dict["GEOMETRICAL PARAM. FLOODPLAIN"]["pathStageStorage_FP"]["value"]
            if self.pathStageStorage_FP.endswith(".mat"):
                V_FP = spio.loadmat(self.pathStageStorage_FP)
                V_FP = V_FP[Path(self.pathStageStorage_FP).stem]
            elif self.pathStageStorage_FP.endswith(".txt"):
                # Load text file (assumes tab or space separation)
                V_FP = np.loadtxt(self.pathStageStorage_FP, delimiter=None) # Auto-detects delimiter (tab/space)
            self.GI_VFP = interp1d(V_FP[:,0],V_FP[:,1]) #[m^3/s] Volume in the floodplain as a function of z_t !! z_t is measured from the erodible dike toe elevation !!
        else:
            self.GI_VFP = 0

        self.Qin = self.params_dict["FLOW PARAMETERS"]["Qin"]["value"]
        self.Qd = self.params_dict["FLOW PARAMETERS"]["Qd"]["value"]
        if isinstance(self.Qin, str):
            file = spio.loadmat(self.Qin)
            self.Qin = file[Path(self.Qin).stem] # [Time;Qin]
            if self.t_end_idx/self.dt>self.Qin[-1,0]:
                self.Qin=interp1d(np.append(self.Qin[:,0], self.t_end_idx*self.dt),np.append(self.Qin[:,1], self.Qin[-1,1]))
            else:
                self.Qin=interp1d(self.Qin[:,0],self.Qin[:,1])
        if isinstance(self.Qd, str):
            file = spio.loadmat(self.Qd)
            self.Qd = file[Path(self.Qd).stem] # [Time;Qd]
            if self.t_end_idx/self.dt>self.Qd[-1,0]:
                self.Qd=interp1d(np.append(self.Qd[:,0], self.t_end_idx*self.dt),np.append(self.Qd[:,1], self.Qd[-1,1]))
            else:
                self.Qd=interp1d(self.Qd[:,0],self.Qd[:,1])
        self.z_s_ini = self.params_dict["FLOW PARAMETERS"]["z_s_ini"]["value"]
        if self.z_s_ini == -999:
            self.z_s_ini=0.999*self.h_d  #[m] Initial water level in the main channel
        self.z_t_ini = self.params_dict["FLOW PARAMETERS"]["z_t_ini"]["value"]
        self.Qin_coef = self.params_dict["FLOW PARAMETERS"]["Qin_coef"]["value"]

        self.Qo_module = str(self.params_dict["OUTFLOW DISCHARGE"]["Qo_module"]["value"]).lower() == "true"
        if self.Qo_module == False:
            self.Qo = 0
        else:
            self.Qo = self.params_dict["OUTFLOW DISCHARGE"]["Qo"]["value"]

        self.c1 = self.params_dict["EMPIRICAL PARAMETERS"]["c1"]["value"]
        self.c2 = self.params_dict["EMPIRICAL PARAMETERS"]["c2"]["value"]
        self.c_eff = self.params_dict["EMPIRICAL PARAMETERS"]["c_eff"]["value"]
        self.lambda_in = self.params_dict["EMPIRICAL PARAMETERS"]["lambda_in"]["value"]
        self.lambda_out = self.params_dict["EMPIRICAL PARAMETERS"]["lambda_out"]["value"]
        self.lambda_loss = self.lambda_in+self.lambda_out
        self.An = self.params_dict["EMPIRICAL PARAMETERS"]["An"]["value"]
        self.An_prime = self.params_dict["EMPIRICAL PARAMETERS"]["An_prime"]["value"]
        self.n_min = self.params_dict["EMPIRICAL PARAMETERS"]["n_min"]["value"]
        self.lbda = self.params_dict["EMPIRICAL PARAMETERS"]["lbda"]["value"]
        if self.lbda==0:
            self.instant_equilibrium = True
        else:
            self.instant_equilibrium = False
        self.theta_cr = self.params_dict["EMPIRICAL PARAMETERS"]["theta_cr"]["value"]
        self.Sp = self.params_dict["EMPIRICAL PARAMETERS"]["Sp"]["value"]
        self.C_stara = self.params_dict["EMPIRICAL PARAMETERS"]["C_stara"]["value"]
        self.C_starb = self.params_dict["EMPIRICAL PARAMETERS"]["C_starb"]["value"]
        self.C_starc = self.params_dict["EMPIRICAL PARAMETERS"]["C_starc"]["value"]
        self.C_stard = self.params_dict["EMPIRICAL PARAMETERS"]["C_stard"]["value"]
        self.qb_stara = self.params_dict["EMPIRICAL PARAMETERS"]["qb_stara"]["value"]
        self.qb_starb = self.params_dict["EMPIRICAL PARAMETERS"]["qb_starb"]["value"]
        self.lambda0a = self.params_dict["EMPIRICAL PARAMETERS"]["lambda0a"]["value"]
        self.lambda0b = self.params_dict["EMPIRICAL PARAMETERS"]["lambda0b"]["value"]
        self.cb_coef = self.params_dict["EMPIRICAL PARAMETERS"]["cb_coef"]["value"]
        if self.dam==False:
            self.b_eff_frac = self.params_dict["EMPIRICAL PARAMETERS"]["b_eff_frac"]["value"]
        else:
            self.b_eff_frac = math.inf

        return

    def get_params(self):
        """
        :return: dict Dictionary containing the parameters"""

        self.params_dict = {
            "TEST DEFINITION": {
                "Test_ID": {
                    "value": self.Test_ID,
                    "explicit name": "Test name",
                    "description": "Test name",
                    "type": "String",
                    "choices": None,
                    "mandatory": True
                }
            },
            "TIME PARAMETERS": {
                "dt": {
                    "value": self.dt,
                    "explicit name": "Time step [s]",
                    "description": "Time step (constant) [s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "t_end": {
                    "value": self.t_end,
                    "explicit name": "Simu. duration [s]",
                    "description": "Simulated time [s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                }
            },
            "SAVE OUTPUTS": {
                "exportMainResults": {
                    "value": self.exportMainResults,
                    "explicit name": "Save results?",
                    "description": "Save results in .txt file? True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": True
                },
                "extractTriangulation": {
                    "value": self.extractTriangulation,
                    "explicit name": "Save triangulation?",
                    "description": "Save triangulation in .json file? True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": True
                },
                "path_saveOutputs": {
                    "value": self.path_saveOutputs,
                    "explicit name": "Output folder",
                    "description": "Path where to store the output data (main outputs and/or triangulation)",
                    "type": "Directory",
                    "choices": None,
                    "mandatory": True
                }
            },
            "PHYSICAL PARAMETERS": {
                "g": {
                    "value": self.g,
                    "explicit name": "Gravitational acceleration [m/s^2]",
                    "description": "Gravitational acceleration [m/s^2]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "d50": {
                    "value": self.d50,
                    "explicit name": "Median grain size [m]",
                    "description": "Median grain size [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "nu": {
                    "value": self.nu,
                    "explicit name": "Water kinematic viscosity [m^2/s]",
                    "description": "Water kinematic viscosity [m^2/s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "rho": {
                    "value": self.rho,
                    "explicit name": "Water density [kg/m^3]",
                    "description": "Water density [kg/m^3]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "rho_s": {
                    "value": self.rho_s,
                    "explicit name": "Sediment density [kg/m^3]",
                    "description": "Sediment density [kg/m^3]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "p": {
                    "value": self.p,
                    "explicit name": "Material porosity [-]",
                    "description": "Material porosity [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "phi": {
                    "value": self.phi,
                    "explicit name": "Friction angle [deg]",
                    "description": "Friction angle [deg]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "suspension": {
                    "value": self.suspension,
                    "explicit name": "Activate suspension?",
                    "description": "Should sediment suspension be considered in erosion process? True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": False
                }
            },
            "GEOMETRICAL PARAM. DIKE": {
                "dam": {
                    "value": self.dam,
                    "explicit name": "Dam or fluvial dike?",
                    "description": "Is it a dam? True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": True
                },
                "Su": {
                    "value": self.Su,
                    "explicit name": "Upstream slope (H/V) [-]",
                    "description": "Dike/dam slope directed toward the reservoir (H/V) [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "Sd_ini": {
                    "value": self.Sd_ini,
                    "explicit name": "Initial downstream slope (H/V) [-]",
                    "description": "Initial dike/dam slope directed toward the floodplain(H/V) [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "Lk": {
                    "value": self.Lk,
                    "explicit name": "Crest width [m]",
                    "description": "Dike/dam crest width [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "h_d": {
                    "value": self.h_d,
                    "explicit name": "Dike height [m]",
                    "description": "Dike height considered as erodible [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "complete_erosion": {
                    "value": self.complete_erosion,
                    "explicit name": "Complete erosion?",
                    "description": "Specifies if erosion can reach embankment bottom. True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": False
                },
                "xnotch_ini": {
                    "value": self.xnotch_ini,
                    "explicit name": "Notch position along x-axis [m]",
                    "description": "Position of the initial notch center along the x-axis [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "ynotch_ini": {
                    "value": self.ynotch_ini,
                    "explicit name": "Notch position along y-axis [m]",
                    "description": "Position of the initial notch center along the y-axis [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "end_up": {
                    "value": self.end_up,
                    "explicit name": "Erodible upstream extremity [m]",
                    "description": "Upstream extremity of the interpolation area w/r to the initial breach center line [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "end_down": {
                    "value": self.end_down,
                    "explicit name": "Erodible downstream extremity [m]",
                    "description": "Downstream extremity of the interpolation area w/r to the initial breach center line [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "slope": {
                    "value": self.slope,
                    "explicit name": "Dam/dike bottom slope (V/H)",
                    "description": "Slope of the dam/dike foundation along the structure crest (V/H)",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "elevation_shift": {
                    "value": self.elevation_shift,
                    "explicit name": "Elevation shift [m]",
                    "description": "Shift the altitude of the entire dike triangulation to fit the underlying topo. The reference is the center of the initial notch.",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "riverbank": {
                    "value": self.riverbank,
                    "explicit name": "Location of the reservoir/channel",
                    "description": "On which side of the dam/dike is the reservoir/channel? By default, the structure crest is aligned with x axis.",
                    "type": "Integer",
                    "choices": {"Right":0,"Left":1},
                    "mandatory": False
                },
                "horiz_rotation": {
                    "value": self.horiz_rotation,
                    "explicit name": "Horizontal rotation [deg]",
                    "description": "Rotation of the dike/dam in the horizontal plane [deg]. By default, the structure crest is aligned with x axis.",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                }

            },
            "GEOMETRICAL PARAM. BREACH": {
                "h_b_ini": {
                    "value": self.h_b_ini,
                    "explicit name": "Initial breach depth [m]",
                    "description": "Initial breach depth [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "b_ini": {
                    "value": self.b_ini,
                    "explicit name": "Initial breach bottom width [m]",
                    "description": "Initial breach bottom width [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                }
            },
            "GEOMETRICAL PARAM. MAIN CHANNEL": {
                "reservoir_shape": {
                    "value": self.reservoir_shape,
                    "explicit name": "Reservoir shape",
                    "description": "Shape of the main channel (dike) or reservoir (dam). Irregular, rectangular, or trapezoidal.",
                    "type": "Integer",
                    "choices": {"Stage storage curve":0,"Rectangular":1,"Trapezoidal":2},
                    "mandatory": True
                },
                "Ar": {
                    "value": self.Ar,
                    "explicit name": "Reservoir surface area [m^2]",
                    "description": "Reservoir surface area (constant) [m^2]. Used if reservoir_shape = 'rectangular'",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "lmc": {
                    "value": self.lmc,
                    "explicit name": "Main channel length [m]",
                    "description": "Main channel length [m]. Parallel to dike, perpendicular to dam. Used if reservoir_shape = 'trapezoidal'",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "wmc": {
                    "value": self.wmc,
                    "explicit name": "Main channel width [m]",
                    "description": "Main channel width [m]. Parallel to dam, perpendicular to dike.",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "pathStageStorage": {
                    "value": self.pathStageStorage,
                    "explicit name": "Stage storage curve path",
                    "description": "Path to stage storage curve. Used if reservoir_shape = 'irregular'",
                    "type": "File",
                    "choices": None,
                    "mandatory": True
                }
            },
            "GEOMETRICAL PARAM. FLOODPLAIN": {
                "StageStorage_FP": {
                    "value": self.StageStorage_FP,
                    "explicit name": "Stage storage in floodplain?",
                    "description": "Is stage storage curve available in the floodplain? True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": True
                },
                "pathStageStorage_FP": {
                    "value": self.pathStageStorage_FP,
                    "explicit name": "Floodplain stage storage curve path",
                    "description": "Path to floodplain stage storage curve",
                    "type": "File",
                    "choices": None,
                    "mandatory": True
                }
            },
            "FLOW PARAMETERS": {
                "Qd": {
                    "value": self.Qd,
                    "explicit name": "Drain discharge [m^3/s]",
                    "description": "Drain discharge [m^3/s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "Qin": {
                    "value": self.Qin,
                    "explicit name": "Inflow discharge [m^3/s]",
                    "description": "Inflow discharge [m^3/s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "z_s_ini": {
                    "value": self.z_s_ini,
                    "explicit name": "Initial water level in main channel [m]",
                    "description": "Initial water level in the main channel [m]. If -999, 0.999 * Dike height is used.",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "z_t_ini": {
                    "value": self.z_t_ini,
                    "explicit name": "Initial water level in floodplain [m]",
                    "description": "Initial water level in the floodplain [m]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "Qin_coef": {
                    "value": self.Qin_coef,
                    "explicit name": "Inflow discharge coefficient",
                    "description": "Multiplicative coefficient of Qin. Only used for sensitivity analysis.",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                }
            },
            "OUTFLOW DISCHARGE": {
                "Qo_module": {
                    "value": self.Qo_module,
                    "explicit name": "Outflow discharge?",
                    "description": "Use a module to compute the outflow discharge? True or False",
                    "type": "Logical",
                    "choices": None,
                    "mandatory": True
                }
            },
            "EMPIRICAL PARAMETERS": {
                "c1": {
                    "value": self.c1,
                    "explicit name": "Breach discharge parameter (c1) [-]",
                    "description": "Empirical parameter c1 [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "c2": {
                    "value": self.c2,
                    "explicit name": "Breach discharge parameter (c2) [-]",
                    "description": "Empirical parameter c2 [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "c_eff": {
                    "value": self.c_eff,
                    "explicit name": "Weir efficiency coefficient [-]",
                    "description": "Modification of weir efficiency coefficients so that c1,2=c1,2*c_eff [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "lambda_in": {
                    "value": self.lambda_in,
                    "explicit name": "Head water loss at breach inlet [-]",
                    "description": "Head water loss at breach inlet (used in Keulegan equation) [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "lambda_out": {
                    "value": self.lambda_out,
                    "explicit name": "Head water loss at breach outlet [-]",
                    "description": "Head water loss at breach outlet (used in Keulegan equation) [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "An": {
                    "value": self.An,
                    "explicit name": "Manning related coefficient An [-]",
                    "description": "Empirical coefficient An [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "An_prime": {
                    "value": self.An_prime,
                    "explicit name": "Manning related coefficient An_prime [-]",
                    "description": "Empirical coefficient An_prime [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "n_min": {
                    "value": self.n_min,
                    "explicit name": "Minimum Manning's coefficient [-]",
                    "description": "Minimum value of Manning's coefficient [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "lbda": {
                    "value": self.lbda,
                    "explicit name": "Adaptation length parameter [-]",
                    "description": "Related to distance taken by the flow to be fully charged in sediments [-]. 0 = instantaneous equilibrium. 6 is a large value.",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "theta_cr": {
                    "value": self.theta_cr,
                    "explicit name": "Critical Shields parameter [-]",
                    "description": "Critical Shields parameter [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "Sp": {
                    "value": self.Sp,
                    "explicit name": "Corey shape factor [-]",
                    "description": "Corey shape factor (used in settling velocity) [-]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "C_stara": {
                    "value": self.C_stara,
                    "explicit name": "Suspended load coefficient C_stara",
                    "description": "Suspended load coefficient C_stara",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "C_starb": {
                    "value": self.C_starb,
                    "explicit name": "Suspended load coefficient C_starb",
                    "description": "Suspended load coefficient C_starb",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "C_starc": {
                    "value": self.C_starc,
                    "explicit name": "Suspended load coefficient C_starc",
                    "description": "Suspended load coefficient C_starc",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "C_stard": {
                    "value": self.C_stard,
                    "explicit name": "Suspended load coefficient C_stard",
                    "description": "Suspended load coefficient C_stard",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "qb_stara": {
                    "value": self.qb_stara,
                    "explicit name": "Bed load coefficient qb_stara",
                    "description": "Bed load coefficient qb_stara",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "qb_starb": {
                    "value": self.qb_starb,
                    "explicit name": "Bed load coefficient qb_starb",
                    "description": "Bed load coefficient qb_starb",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "lambda0a": {
                    "value": self.lambda0a,
                    "explicit name": "Shear stress coefficient lambda0a",
                    "description": "Shear stress coefficient lambda0a",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "lambda0b": {
                    "value": self.lambda0b,
                    "explicit name": "Shear stress coefficient lambda0b",
                    "description": "Shear stress coefficient lambda0b",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "cb_coef": {
                    "value": self.cb_coef,
                    "explicit name": "Coefficient cb",
                    "description": "Coefficient that artificially limits the difference btw breach width on flat top and D/S reaches",
                    "type": "Float",
                    "choices": None,
                    "mandatory": False
                },
                "b_eff_frac": {
                    "value": self.b_eff_frac,
                    "explicit name": "Effective breach width fraction",
                    "description": "Fraction of the breach width considered as effective. If >=1, full breach used",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                }
            }
        }

        return self.params_dict

    def read_params(self, file_name:str, store_dir: Path = None):
        '''
        Read the model parameters from a .json file and store them in a dictionary
        :param file_name: name of the file to read
        :param store_dir: directory where to read the file
        :return self.params_dict: dictionary containing the parameters
        '''

        assert isinstance(store_dir, Path), 'I need a Path !, you provide {}'.format(type(store_dir))
        assert isinstance(file_name, str), 'I need a string !, you provide {}'.format(type(file_name))

        data = {}
        json_file_path = store_dir / (file_name + "_paramsDike.json")

        with open(json_file_path, 'r', encoding='ISO-8859-1') as file:
            data = json.load(file)
            for current_section in data.keys():
                if current_section not in self.params_dict:
                    if current_section.lower() == 'outflow discharge':
                        self.params_dict[current_section] = {}
                    elif current_section not in self.params_dict:
                        raise ValueError(f"Unexpected section {current_section} found in the parameter file.")
                else:
                    for key, value in data[current_section].items():
                        if key not in self.params_dict[current_section]:
                            if current_section.lower() == 'outflow discharge':
                                self.params_dict[current_section][key] = {}
                            else:
                                raise ValueError(f"Unexpected parameter {key} found in the parameter file.")
                        if isinstance(value, dict):
                            value = value["value"]
                        self.params_dict[current_section][key]["value"] = value
        self.set_params()

    def save_params(self, file_name:str, store_dir: Path = Path.cwd()):
        '''
        Save the parameters in a JSON text file

        :param file_name: name of the file to save
        :param store_dir: directory where to save the file
        :return: None
        '''
        assert isinstance(store_dir, Path), 'I need a Path !, you provide {}'.format(type(store_dir))
        assert isinstance(file_name, str), 'I need a string !, you provide {}'.format(type(file_name))

        params_dict = self.get_params()

        with open(store_dir / file_name, "w") as f:
            f.write(json.dumps(params_dict, indent=4))

        return



class injector: # FIRST DRAFT
    def __init__(self):
        """
        !!! UNDER DEVELOPMENT !!!
        :param params_dict: dictionary containing the parameters
        """
        # INITIATE ALL PARAMETERS

        # TEST DEFINITION
        self.Test_ID = "Test_ID"
        # TIME PARAMETERS
        self.dt = 2
        self.t_end = 10
        self.t_end_idx = int(self.t_end / self.dt)
        # UPDATED ZONE PARAMETERS (topo on which the dike interpolation is applied)
        self.xmin_topo, self.ymin_topo = 7046,6286 # (154665m;241001m) # [idx_X,idx_Y] With respect to the reference of the global MNT (-> absolute coordinates)
        self.xrange_topo, self.yrange_topo = 85, 145 # [idx_X,idx_Y] -> range of the dike in the topo array
        # Global area in which the dike is located (can be larger than the dike)
        self.updated_zone = [self.ymin_topo-1+[0,self.yrange_topo], self.xmin_topo-1+[0,self.xrange_topo]] # [idx_Y,idx_X] -> reference for the rest of the modifications (same reference for qx, qy, and h)
        # OUTPUTS PARAMETERS
        self.zs_loc = [7096,6300,55.0663]# (X;Y;bathy)
        self.zt_loc = [7050,6330,57.413] # (X;Y;bathy)
        self.dikeCrest = pd.read_excel(r'..\Wolf array for interpolation\PLOTO\DikeCrest.xlsx')
        self.dikeCrest = np.asarray(self.dikeCrest)
        self.dikeCrest[:,0] -= self.xmin_topo
        self.dikeCrest[:,1] -= self.ymin_topo

        self.params_dict = self.get_params()

    def set_params(self):
        """
        !!! UNDER DEVELOPMENT !!!
        Set the parameters from the dictionary
        :return: None
        """
        # TEST DEFINITION
        self.Test_ID = self.params_dict["INJECTOR ID"]["ID"]["value"]
        # TIME PARAMETERS
        # self.dt = self.params_dict["UPDATE TIMES"]["dt"]["value"]
        # self.t_end = self.params_dict["UPDATE TIMES"]["t_end"]["value"]
        # self.t_end_idx = int(self.t_end / self.dt)
        # UPDATED ZONE PARAMETERS
        self.xmin_topo = self.params_dict["UPDATED ZONE PARAM."]["xmin_topo"]["value"]
        self.ymin_topo = self.params_dict["UPDATED ZONE PARAM."]["ymin_topo"]["value"]
        self.xrange_topo = self.params_dict["UPDATED ZONE PARAM."]["xrange_topo"]["value"]
        self.yrange_topo = self.params_dict["UPDATED ZONE PARAM."]["yrange_topo"]["value"]

    def get_params(self):
        """
        :return: dict Dictionary containing the parameters"""

        self.params_dict = {
            "INJECTOR ID": {
                "ID": {
                    "value": self.ID,
                    "explicit name": "Injector name",
                    "description": "Injector name",
                    "type": "String",
                    "choices": None,
                    "mandatory": True
                }
            },
            "UPDATE TIMES": {
                "firstUpdate": {
                    "value": self.firstUpdate,
                    "explicit name": "Time to first update [s]",
                    "description": "Time to first call of the injector [s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                },
                "updateFrequency": {
                    "value": self.updateFrequency,
                    "explicit name": "Update frequency [s]",
                    "description": "Frequency at which the injector is called [s]",
                    "type": "Float",
                    "choices": None,
                    "mandatory": True
                }
            },
            "UPDATED AREA": {
                "update_zone": {
                    "value": self.updated_zone,
                    "explicit name": "Updated area coordinates",
                    "description": "X/Y indices of the two vertices that define the rectangular updated area ([[idx_ymin, idx_ymax], [idx_xmin, idx_xmax]]).",
                    "type": "Array",
                    "choices": None,
                    "mandatory": True
                }
            }
        }

        return self.params_dict