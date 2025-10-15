# %matplotlib ipympl # Allow to interact with figures in Jupyter Notebooks (Alternative = %matplotlib widget)
#%%

import sys
print(sys.version)
import math
import os
import scipy.io as spio
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
from math import sqrt, atan, sin, cos, tan

from InteractionPythGPU import dike_coupled

from wolfhece.wolf_array import WolfArray, header_wolf

from wolfgpu.SimulationRunner import SimulationRunner, SimulationInjector, SimulationProxy
from wolfgpu.simple_simulation import SimulationDuration, SimpleSimulation
from wolfgpu.results_store import ResultsStore
from wolfhece.PyTranslate import _


class KakinumaInjector(SimulationInjector):

    def __init__(self, period, firstUpdate, dike_obj, update_zone, TestID):
        self.period = period
        self.firstUpdate = firstUpdate
        self.dike = dike_obj
        self.update_zone = update_zone
        self.TestID = TestID
        self.firstCall = True

    def active_zone(self):
        return (slice(update_zone[0][0],update_zone[0][1]), slice(update_zone[1][0],update_zone[1][1]))

    def time_to_first_injection(self, current_iteration, current_time) -> SimulationDuration:
        return SimulationDuration.from_seconds(self.firstUpdate)

    def do_updates(self, proxy: SimulationProxy):
        # Update the features of the dike object
        self.dike.t += 1
        self.dike.time[self.dike.t] = proxy.current_sim_time

        # We change the infiltration quantities
        ic = proxy.get_active_infiltration_quantities()
        h = proxy.get_h() # [m] Water depth
        if self.TestID == 1:
            Qout = 2/3 * 0.5826 * np.sqrt(2*9.81*np.mean(h[20:28, 584])**3)* 8
        elif self.TestID == 2:
            Qout = 2/3 * 0.2637 * np.sqrt(2*9.81*np.mean(h[20:28, 584])**3)* 8
        ic [1] = -Qout
        proxy.set_active_infiltration_quantities(ic)

        # Update hydro variables in dike object !!! IN THIS SECTION, THE CELLS DEFINING THE DIKE CREST CROSS SECTION SHOULD BE DEFINED MANUALLY
        dike_crest = 12
        qy = proxy.get_qy() # [m] Water discharge
        b = proxy.get_bathymetry()
        self.dike.Qb[self.dike.t] = np.abs(np.sum(qy[dike_crest,self.dike.xmin_topo:self.dike.xmin_topo+self.dike.nbx_topo])) * self.dike.dxy
        self.dike.zbbreach[self.dike.t,:] = b[dike_crest,self.dike.xmin_topo:self.dike.xmin_topo+self.dike.nbx_topo]
        self.dike.hbreach[self.dike.t,:] = h[dike_crest,self.dike.xmin_topo:self.dike.xmin_topo+self.dike.nbx_topo]
        if self.TestID == 1:
            self.dike.z_s[self.dike.t] = np.mean(h[20:28, 446])
            self.dike.z_t[self.dike.t] = np.mean(h[0:5, 487:507])
        elif self.TestID == 2:
            self.dike.z_s[self.dike.t] = np.mean(h[20:28, 565])
            self.dike.z_t[self.dike.t] = np.mean(h[0:5, 583:595])

        # We launch the erosion module
        self.dike.runDLBreach_plus()

        # Update the bathymetry
        if self.firstCall:
            self.dike_cells = np.transpose(np.nonzero(self.dike.topoArray[self.dike.t,:,:]-1))
            self.idx_dike_x = ((self.dike.xmin_topo-update_zone[1][0])/self.dike.dxy + self.dike_cells[:,0]).astype(int)
            self.idx_dike_y = ((self.dike.ymin_topo-update_zone[0][0])/self.dike.dxy + self.dike_cells[:,1]).astype(int)
            self.firstCall = False

        b[self.idx_dike_y, self.idx_dike_x] = self.dike.topoArray[self.dike.t,self.dike_cells[:,0],self.dike_cells[:,1]]
        proxy.set_bathymetry(b)

        return SimulationDuration.from_seconds(self.period)

class PLOTOInjector(SimulationInjector):

    def __init__(self, period, firstUpdate, dike_obj, update_zone, dikeCrest, zs_loc, zt_loc):
        self.period = period
        self.firstUpdate = firstUpdate
        self.dike = dike_obj
        self.update_zone = update_zone
        self.dikeCrest = dikeCrest
        self.zs_loc = zs_loc
        self.zt_loc = zt_loc
        self.firstCall = True

    def active_zone(self):
        return (slice(update_zone[0][0],update_zone[0][1]), slice(update_zone[1][0],update_zone[1][1]))

    def time_to_first_injection(self, current_iteration, current_time) -> SimulationDuration:
        return SimulationDuration.from_seconds(self.firstUpdate)

    def do_updates(self, proxy: SimulationProxy):
        # Update the features of the dike object
        self.dike.t += 1
        self.dike.time[self.dike.t] = proxy.current_sim_time

        # Update hydro variables in dike object !!! IN THIS SECTION, THE CELLS DEFINING THE DIKE CREST CROSS SECTION SHOULD BE DEFINED MANUALLY
        qx = proxy.get_qx() # [m] Water discharge
        qy = proxy.get_qy()
        h = proxy.get_h() # [m] Water dept
        b = proxy.get_bathymetry()

        if self.firstCall: # Identifies the dike crest cells that have a left AND upper free border -> Qx and Qy should be considered, not only Qx
            self.idx_qy = [len(self.dikeCrest[:,0])-1]
            for k in range(len(self.dikeCrest[:,0])-1):
                if self.dikeCrest[k+1,0] != self.dikeCrest[k,0]:
                    self.idx_qy.append(k)

        self.dike.z_t[self.dike.t] = max(0,h[self.zt_loc[1]-self.update_zone[0][0], self.zt_loc[0]-self.update_zone[1][0]] - (self.dike.elevation_shift - self.zt_loc[2]))
        self.dike.z_s[self.dike.t] = max(0,h[self.zs_loc[1]-self.update_zone[0][0], self.zs_loc[0]-self.update_zone[1][0]] - (self.dike.elevation_shift - self.zs_loc[2]))
        Qx = np.abs(np.sum(qx[self.dikeCrest[:,1],self.dikeCrest[:,0]])) * self.dike.dxy
        Qy = np.abs(np.sum(qy[self.dikeCrest[self.idx_qy,1],self.dikeCrest[self.idx_qy,0]])) * self.dike.dxy
        self.dike.Qb[self.dike.t] = Qx + Qy
        self.dike.zbbreach[self.dike.t,:] = b[self.dikeCrest[:,1],self.dikeCrest[:,0]]
        self.dike.hbreach[self.dike.t,:] = h[self.dikeCrest[:,1],self.dikeCrest[:,0]]

        # We launch the erosion module
        self.dike.runDLBreach_plus()

        # Update the bathymetry
        if self.firstCall:
            self.dike_cells = np.transpose(np.nonzero(self.dike.topoArray[self.dike.t,:,:]-1))
            self.idx_dike_x = ((self.dike.xmin_topo-update_zone[1][0])/self.dike.dxy + self.dike_cells[:,0]).astype(int)
            self.idx_dike_y = ((self.dike.ymin_topo-update_zone[0][0])/self.dike.dxy + self.dike_cells[:,1]).astype(int)
            self.firstCall = False

            '''header = header_wolf()
            header.origx = 0.0
            header.origy = 0.0
            header.dx = 1.0
            header.dy = 1.0
            header.nbx = 10
            header.nby = 10
            srs = WolfArray(srcheader=header)
            srs.array(b)'''

        b[self.idx_dike_y, self.idx_dike_x] = self.dike.topoArray[self.dike.t,self.dike_cells[:,0],self.dike_cells[:,1]]
        proxy.set_bathymetry(b)

        # if self.dike.breach_activated:
        #     self.period = 60

        return SimulationDuration.from_seconds(self.period)

def main():
    os.chdir(os.path.dirname(__file__)) # Make the current directory = the directory in which "main.py" is

if __name__=='__main__':
    main()

# # Kakinuma
# # --------

# TestID = 1

# sim = SimpleSimulation.load(Path(r"C:\Users\vincent\WOLF_GPU\Kakinuma_Test"+str(TestID)+r"_modifiedForGPU\simul\simulations\sim_infiltration"))
# print(sim)
# simu_duration = int(3600*4) # [s]
# sim.param_duration = SimulationDuration.from_seconds(simu_duration)
# sim.param_report_period = SimulationDuration.from_seconds(60)
# tempdir = r"C:\Users\vincent\WOLF_GPU\Kakinuma_Test"+str(TestID)+r"_modifiedForGPU\simul\simulations\sim_infiltration\Results"
# #tempdir = r'C:\Users\vincent\WOLF_GPU\TempStorage'

# updateFrequency, firstUpdate = 0.5, 60
# update_zone = [[153,203], [0,640]] # [idx_Y,idx_X] -> reference for the rest of the modifications (same reference for qx, qy, and h)
# # Global area in which the dike is located (can be larger than the dike)
# if TestID == 1:
#     XMINTOPO, YMINTOPO = 447, 158 # [idx_X,idx_Y] With respect to the reference of the global MNT (-> absolute coordinates)
# elif TestID == 2:
#     XMINTOPO, YMINTOPO = 545, 158 # [idx_X,idx_Y] With respect to the reference of the global MNT (-> absolute coordinates)
# # Location of the dike (rectangular in 2D) : corner located at the dike upstream extremity, on the floodplain side
# dike_origin = [0,0] # [X,Y] in meters. With respect to the origin of the array on which triangulation is applied : XMINTOPO, YMINTOPO
# rotation = 0 # [°] Trigono direction OR provide 2nd point = corner located at the downstream extremity, on the floodplain side
# riverbank = 'right' # On which side of the river is the dike located ? 'right' or 'left'
# dxy = 1 #[m] Spatial discretization
# t_end_idx = int(1.5 * simu_duration/updateFrequency) # Length of the storage vector (might be longer than required, not problematic)
# path_TriangArray = r'..\Wolf array for interpolation\Kakinuma\Emprise_Case'+str(TestID)+r'_1m.bin' # Where to load Wolf array on which interpolation is applied
# interpMatrix = WolfArray(fname = path_TriangArray)
# injector = KakinumaInjector(period=updateFrequency, firstUpdate=firstUpdate, dike_obj = dike(interpMatrix, XMINTOPO, YMINTOPO, dxy, dike_origin, rotation, riverbank, simu_duration, t_end_idx), update_zone=update_zone, TestID=TestID)


# PLOTO
# -----
sim = SimpleSimulation.load(Path(r"C:\Users\vincent\WOLF_GPU\Albert_Canal\2m\simul\simulations\sim_discharges"))
print(sim)
simu_duration = int(3600*48) # [s]
sim.param_duration = SimulationDuration.from_seconds(simu_duration)
sim.param_report_period = SimulationDuration.from_seconds(600)
tempdir = r'C:\Users\vincent\WOLF_GPU\Albert_Canal\2m\simul\simulations\sim_discharges\Results'

updateFrequency, firstUpdate = 30,1#120, 600
update_zone = [[6285,6285+145], [7045,7045+85]] # [idx_Y,idx_X] -> reference for the rest of the modifications (same reference for qx, qy, and h)
# Global area in which the dike is located (can be larger than the dike)
XMINTOPO, YMINTOPO = 7046,6286 # (154665m;241001m) # [idx_X,idx_Y] With respect to the reference of the global MNT (-> absolute coordinates)
zs_loc = [7096,6300,55.0663]# (X;Y;bathy)
zt_loc = [7050,6330,57.413] # (X;Y;bathy)
dikeCrest = pd.read_excel(r'..\Wolf array for interpolation\PLOTO\DikeCrest.xlsx')
dikeCrest = np.asarray(dikeCrest)
dikeCrest[:,0] -= XMINTOPO
dikeCrest[:,1] -= YMINTOPO
# Location of the dike (rectangular in 2D) : corner located at the dike upstream extremity, on the floodplain side
dike_origin = [25.5,10] # [X,Y] in meters. With respect to the origin of the array on which triangulation is applied : XMINTOPO, YMINTOPO
rotation = 62#60.87 # [°] Trigono direction
riverbank = 'left' # On which side of the river is the dike located ? 'right' or 'left'
t_end_idx = int(simu_duration/updateFrequency) # Length of the storage vector (might be longer than required, not problematic)

path_TriangArray = r'..\Wolf array for interpolation\PLOTO\emprise_dike_2m.bin' # Where to load Wolf array on which interpolation is applied
interpMatrix = WolfArray(fname = path_TriangArray)
dxy = interpMatrix.dx # [m] Spatial discretization (= 2m in this case)
injector = PLOTOInjector(period=updateFrequency, firstUpdate=firstUpdate, dike_obj = dike_coupled(interpMatrix, XMINTOPO, YMINTOPO, dxy, dike_origin, rotation, riverbank, simu_duration, t_end_idx, dikeCrest_nCells = len(dikeCrest[:,0])), update_zone=update_zone, dikeCrest = dikeCrest, zs_loc = zs_loc, zt_loc = zt_loc)


result_store: ResultsStore = SimulationRunner.quick_run(sim, tempdir, injector=injector)
print(f"We recorded {result_store.nb_results} results")
h, qx, qy = result_store.get_last_named_result(["h","qx","qy"])

