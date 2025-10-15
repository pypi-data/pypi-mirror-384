#%%
import numpy as np
import math
import os
import warnings

# !! idx of pts 7_bis and 12_bis are 12 and 13, respectively !!

def initialize(end_up, end_down, b_down, b_down_down, b_down_up, b_top, b_top_down, b_top_up, Lk, Sd_ini, Su, h_d, h_b, z_b, m_down, m_up, dx, t=0):
    ptsUS = np.zeros((14,3))
    ptsDS = np.zeros((14,3))

    ptsDS[0,:]=[b_down/2+b_down_down[t]-b_down_down[0], Lk/2+Sd_ini*h_d, 0]
    ptsUS[0,:]=[-b_down/2+b_down_up[t]-b_down_up[0], Lk/2+Sd_ini*h_d, 0]
    ptsDS[1,:]=[end_down,Lk/2+Sd_ini*h_d,0]
    ptsUS[1,:]=[end_up,Lk/2+Sd_ini*h_d,0]
    ptsDS[2,:]=[end_down,Lk/2,h_d]
    ptsUS[2,:]=[end_up,Lk/2,h_d]
    ptsDS[3,:]=[end_down,-Lk/2,h_d]
    ptsUS[3,:]=[end_up,-Lk/2,h_d]
    ptsDS[4,:]=[end_down,-Lk/2-Su*h_d,0]
    ptsUS[4,:]=[end_up,-Lk/2-Su*h_d,0]
    ptsDS[5,:]=[b_top/2+b_top_down[t]-b_top_down[0],-Lk/2-Su*h_b,z_b[t]]
    ptsUS[5,:]=[-b_top/2+b_top_up[t]-b_top_up[0],-Lk/2-Su*h_b,z_b[t]]
    ptsDS[6,:]=[ptsDS[5,0]+m_down*h_b,-Lk/2,h_d]
    ptsUS[6,:]=[ptsUS[5,0]-m_up*h_b,-Lk/2,h_d]
    ptsDS[12,:]=[ptsDS[6,0],-ptsDS[6,1],ptsDS[6,2]]
    ptsUS[12,:]=[ptsUS[6,0],-ptsUS[6,1],ptsUS[6,2]]
    ptsDS[7,:]=ptsDS[12,:]
    ptsUS[7,:]=ptsUS[12,:]
    ptsDS[8,:]=[ptsDS[5,0],-Lk/2-Su*h_b+dx[t],z_b[t]]
    ptsUS[8,:]=[ptsUS[5,0],-Lk/2-Su*h_b+dx[t],z_b[t]]
    ptsDS[9,:]=[ptsDS[0,0],ptsDS[8,1],z_b[t]]
    ptsUS[9,:]=[ptsUS[0,0],ptsUS[8,1],z_b[t]]
    ptsDS[10,:]=ptsDS[9,:]
    ptsUS[10,:]=ptsUS[9,:]
    ptsDS[11,:]=ptsDS[10,:]
    ptsUS[11,:]=ptsUS[10,:]
    ptsDS[13,:]=[ptsDS[11,0],ptsDS[11,1]-Lk,ptsDS[11,2]]
    ptsUS[13,:]=[ptsUS[11,0],ptsUS[11,1]-Lk,ptsUS[11,2]]

    # Triangulation
    coord_tri, idx_tri = triangulateDike(ptsUS, ptsDS,0)

    return ptsUS, ptsDS, coord_tri, idx_tri

def update(end_up, end_down, b_down, b_down_down, b_down_up, b_top, b_top_down, b_top_up, Lk, Sd, Su, h_d, h_b, z_b, m_down, m_up, dx, t):

    # 4 geometry "types" may be encountered
    if Sd[t+1] == Sd[0]: # Erosion has not started yet
        ptsUS, ptsDS, coord_tri, idx_tri = initialize(end_up, end_down, b_down, b_down_down, b_down_up, b_top, b_top_down, b_top_up, Lk, Sd[0], Su, h_d, h_b, z_b, m_down, m_up, dx, t)
        return ptsUS, ptsDS, coord_tri, idx_tri
    elif z_b[t+1]==0 or Sd[t+1]==math.inf:
        tri_type = 4
    elif -Lk/2-Su*h_b+dx[t+1]>Lk/2:
        tri_type = 1
    elif -Lk/2-Su*h_b+dx[t+1]>-Lk/2:
        tri_type = 2
    else:
        tri_type = 3

    ptsUS = np.zeros((14,3))
    ptsDS = np.zeros((14,3))

    ptsDS[0,:]=[b_down/2+b_down_down[t+1]-b_down_down[0],Lk/2+Sd[0]*h_d,0]
    ptsUS[0,:]=[-b_down/2+b_down_up[t+1]-b_down_up[0],Lk/2+Sd[0]*h_d,0]
    ptsDS[1,:]=[end_down,ptsDS[0,1],0]
    ptsUS[1,:]=[end_up,ptsUS[0,1],0]
    ptsDS[2,:]=[end_down,Lk/2,h_d]
    ptsUS[2,:]=[end_up,Lk/2,h_d]
    ptsDS[3,:]=[end_down,-Lk/2,h_d]
    ptsUS[3,:]=[end_up,-Lk/2,h_d]
    ptsDS[4,:]=[end_down,-Lk/2-Su*h_d,0]
    ptsUS[4,:]=[end_up,-Lk/2-Su*h_d,0]
    ptsDS[5,:]=[b_top/2+b_top_down[t+1]-b_top_down[0],-Lk/2-Su*h_b,z_b[t+1]]
    ptsUS[5,:]=[-b_top/2+b_top_up[t+1]-b_top_up[0],-Lk/2-Su*h_b,z_b[t+1]]
    ptsDS[6,:]=[ptsDS[5,0]+m_down*h_b,-Lk/2,h_d]
    ptsUS[6,:]=[ptsUS[5,0]-m_up*h_b,-Lk/2,h_d]
    ptsDS[7,:]=[ptsDS[6,0],-Lk/2-Su*h_b+dx[t+1]+h_b/Sd[t+1],h_d]
    ptsUS[7,:]=[ptsUS[6,0],-Lk/2-Su*h_b+dx[t+1]+h_b/Sd[t+1],h_d]
    ptsDS[8,:]=[ptsDS[5,0],-Lk/2-Su*h_b+dx[t+1],z_b[t+1]]
    ptsUS[8,:]=[ptsUS[5,0],-Lk/2-Su*h_b+dx[t+1],z_b[t+1]]
    ptsDS[9,:]=[ptsDS[0,0],ptsDS[8,1],ptsDS[8,2]]
    ptsUS[9,:]=[ptsUS[0,0],ptsUS[8,1],ptsUS[8,2]]
    ptsDS[10,:]=[ptsDS[9,0]+m_down*(h_d-(ptsDS[0,1]-ptsDS[7,1])/Sd[t+1]),ptsDS[8,1],h_d]
    ptsUS[10,:]=[ptsUS[9,0]-m_up*(h_d-(ptsUS[0,1]-ptsUS[7,1])/Sd[t+1]),ptsUS[8,1],h_d]
    ptsDS[11,:]=[ptsDS[0,0]+(h_d-Sd[0]*h_d/Sd[t+1])*m_down,Lk/2,h_d]
    ptsUS[11,:]=[ptsUS[0,0]-(h_d-Sd[0]*h_d/Sd[t+1])*m_up,Lk/2,h_d]
    ptsDS[12,:]=[ptsDS[6,0],ptsDS[6,1]+Lk,ptsDS[6,2]]
    ptsUS[12,:]=[ptsUS[6,0],ptsUS[6,1]+Lk,ptsUS[6,2]]
    ptsDS[13,:]=[ptsDS[11,0],ptsDS[11,1]-Lk,ptsDS[11,2]]
    ptsUS[13,:]=[ptsUS[11,0],ptsUS[11,1]-Lk,ptsUS[11,2]]
    if -Lk/2-Su*h_b+dx[t+1]+h_b/Sd[t+1]>Lk/2:
        if z_b[t+1]==0 or Sd[t+1]==math.inf:
            ptsDS[7,2]=(ptsDS[0,1]-ptsDS[8,1])/Sd[0]
            ptsUS[7,2]=(ptsUS[0,1]-ptsUS[8,1])/Sd[0]
            ptsDS[7,0]=ptsDS[8,0]+ptsDS[7,2]*m_down
            ptsUS[7,0]=ptsUS[8,0]-ptsUS[7,2]*m_up
            ptsDS[7,1]=ptsDS[8,1]
            ptsUS[7,1]=ptsUS[8,1]
        else:
            h8d=(ptsDS[8,2]+(ptsDS[0,1]-ptsDS[8,1])*Sd[t+1])/(1+Sd[0]*Sd[t+1]) # OK
            h8u=(ptsUS[8,2]+(ptsUS[0,1]-ptsUS[8,1])*Sd[t+1])/(1+Sd[0]*Sd[t+1]) # OK
            ptsDS[7,:]=[ptsDS[8,0]+(h8d-ptsDS[8,2])*m_down,ptsDS[0,1]-Sd[0]*h8d,h8d]  # OK
            ptsUS[7,:]=[ptsUS[8,0]-(h8u-ptsUS[8,2])*m_up,ptsUS[0,1]-Sd[0]*h8u,h8u]    # OK
        ptsDS[10,:]=[ptsDS[0,0]+m_down*(ptsDS[7,2]-(ptsDS[0,1]-ptsDS[7,1])/Sd[t+1]),ptsDS[7,1],ptsDS[7,2]] # OK
        ptsUS[10,:]=[ptsUS[0,0]-m_up*(ptsUS[7,2]-(ptsUS[0,1]-ptsUS[7,1])/Sd[t+1]),ptsUS[7,1],ptsUS[7,2]]   # OK
        ptsDS[11,:]=ptsDS[10,:]
        ptsUS[11,:]=ptsUS[10,:]
    elif -Lk/2-Su*h_b+dx[t+1]+h_b/Sd[t+1]<-Lk/2:
        if z_b[t+1]==0 or Sd[t+1]==math.inf:
            ptsDS[7,:]=[ptsDS[5,0]+m_down*dx[t+1]/Su,ptsDS[5,1]+dx[t+1],dx[t+1]/Su] # OK
            ptsUS[7,:]=[ptsUS[5,0]-m_up*dx[t+1]/Su,ptsUS[5,1]+dx[t+1],dx[t+1]/Su] # OK
        else:
            y8d=ptsDS[8,1]+(ptsDS[8,2]-ptsDS[8,1]/Su-Lk/(2*Su)-h_d)/(1/Su-Sd[t+1]) # OK
            y8u=ptsUS[8,1]+(ptsUS[8,2]-ptsUS[8,1]/Su-Lk/(2*Su)-h_d)/(1/Su-Sd[t+1]) # OK
            z8d=(Lk/2+Su*h_d+y8d)/Su # OK
            z8u=(Lk/2+Su*h_d+y8u)/Su # OK
            ptsDS[7,:]=[ptsDS[8,0]+(z8d-ptsDS[8,2])*m_down,y8d,z8d] # OK
            ptsUS[7,:]=[ptsUS[8,0]-(z8u-ptsUS[8,2])*m_up,y8u,z8u] # OK
        ptsDS[6,:]=ptsDS[7,:]
        ptsUS[6,:]=ptsUS[7,:]
        #ptsDS[10,:]=[ptsDS[0,0]+m_down*(ptsDS[8,2]-(ptsDS[0,1]-ptsDS[7,1])/Sd[t+1]),ptsDS[7,1],ptsDS[7,2]] !! WRONG
        #ptsUS[10,:]=[ptsUS[0,0]-m_up*(ptsUS[8,2]-(ptsUS[0,1]-ptsUS[7,1])/Sd[t+1]),ptsUS[7,1],ptsUS[7,2]]   !! WRONG
        ptsDS[10,:]=[ptsDS[0,0]+m_down*(ptsDS[7,2]-ptsDS[9,2])*math.cos(math.atan(1/Sd[t+1])),ptsDS[7,1],ptsDS[7,2]]
        ptsUS[10,:]=[ptsUS[0,0]-m_up*(ptsUS[7,2]-ptsUS[9,2])*math.cos(math.atan(1/Sd[t+1])),ptsUS[7,1],ptsUS[7,2]]
        ptsDS[13,:]=[ptsDS[0,0]+(h_d-(Lk+Sd[0]*h_d)/Sd[t+1])*m_down,-Lk/2,h_d]
        ptsUS[13,:]=[ptsUS[0,0]-(h_d-(Lk+Sd[0]*h_d)/Sd[t+1])*m_up,-Lk/2,h_d]

    # Triangulation
    coord_tri, idx_tri = triangulateDike(ptsUS, ptsDS,tri_type)

    return ptsUS, ptsDS, coord_tri, idx_tri



def adaptTriangulation(coord_tri, slope, flip, horiz_rotation, elevation_shift):
    """
    Rotate and flip the coordinates of the triangulation based on the longitudinal slope, the horizontal rotation, and the river bank side to fit the MNT.
    """
    if slope != 0: # Rotate coordinates -> rough approximation for small slopes and short dikes / X and Y coordinates should be modified to be accurate
        coord_tri[:,2] -= coord_tri[:,0] * slope

    coord_tri[:,2] += elevation_shift # Where elevation data are stored

    if flip: # Flip dike to match the river/reservoir side
        coord_tri[:,1] = -coord_tri[:,1]

    if horiz_rotation != 0:
        angle = horiz_rotation/180 * math.pi
        x_temp = coord_tri[:,0] * math.cos(angle) - coord_tri[:,1] * math.sin(angle)
        y_temp = coord_tri[:,0] * math.sin(angle) + coord_tri[:,1] * math.cos(angle)
        coord_tri[:,0], coord_tri[:,1] = x_temp, y_temp

    return coord_tri



def triangulateDike(ptsUS, ptsDS,tri_type):
    # !!! The D/S reach must be wider than the flat top reach !!! -> always the case normally
    if np.abs(ptsUS[0,1]-ptsDS[0,1]) < np.abs(ptsUS[5,1]-ptsDS[5,1]):
        raise Exception("Geometry not supported for triangulation. The D/S reach must be larger than the flat top reach!")

    # Some coordinates are altered to avoid superposition of triangles or points
    coord_tri = np.concatenate((ptsUS,ptsDS))
    coord_tri[7,1] = coord_tri[8,1].copy()
    coord_tri[10,1] = coord_tri[9,1].copy()
    coord_tri[21,1] = coord_tri[22,1].copy()
    coord_tri[24,1] = coord_tri[23,1].copy()
    if tri_type == 1 or tri_type == 2 or tri_type == 3:
        coord_tri[7,1] = coord_tri[7,1] - 10**-7
        coord_tri[10,1] = coord_tri[10,1] - 10**-7
        coord_tri[21,1] = coord_tri[21,1] - 10**-7
        coord_tri[24,1] = coord_tri[24,1] - 10**-7
        if tri_type == 1 or tri_type == 3:
            if tri_type == 1:
                z = (coord_tri[2,2]-coord_tri[1,2])/np.abs(coord_tri[2,1]-coord_tri[1,1]) * np.abs(coord_tri[9,1]-coord_tri[1,1])
            elif tri_type == 3:
                z = (coord_tri[3,2]-coord_tri[4,2])/np.abs(coord_tri[3,1]-coord_tri[4,1]) * np.abs(coord_tri[9,1]-coord_tri[4,1])
                if abs(coord_tri[8,0]-coord_tri[9,0]) < 10**-3: # Prevent small triangles from degenerating
                    coord_tri[9,0] -= 10**-3
                    coord_tri[10,0] -= 10**-3
                    coord_tri[23,0] += 10**-3
                    coord_tri[24,0] += 10**-3
            coord_tri[7,2] = z.copy()
            coord_tri[10,2] = z.copy()
            coord_tri[21,2] = z.copy()
            coord_tri[24,2] = z.copy()
    elif tri_type == 4:
        coord_tri[6,:] = coord_tri[11,:] # Made to simplify triangulation
        coord_tri[6,1] = coord_tri[3,1]
        coord_tri[20,:] = coord_tri[25,:]
        coord_tri[20,1] = coord_tri[17,1]

    # Points indices correpond to the 14 U/S points followed by the 14 D/S points
    if tri_type == 0: # Erosion has not started yet
        idx_tri = np.zeros((22,3), dtype=int)
        # U/S side slope of the dike
        idx_tri[0,:] = [3,4,6]
        idx_tri[1,:] = [4,5,6]
        idx_tri[2,:] = idx_tri[0,:] + 14 # By symmetry
        idx_tri[3,:] = idx_tri[1,:] + 14 # By symmetry
        idx_tri[4,:] = [4,5,18]
        idx_tri[5,:] = [5,18,19]
        # D/S side slope of the dike
        idx_tri[6,:] = [1,2,12]
        idx_tri[7,:] = [1,12,8]
        idx_tri[8,:] = idx_tri[6,:] + 14 # By symmetry
        idx_tri[9,:] = idx_tri[7,:] + 14 # By symmetry
        idx_tri[10,:] = [1,8,22]
        idx_tri[11,:] = [1,15,22]
        # Dike crest
        idx_tri[12,:] = [2,3,6]
        idx_tri[13,:] = [2,6,12]
        idx_tri[14,:] = idx_tri[12,:] + 14 # By symmetry
        idx_tri[15,:] = idx_tri[13,:] + 14 # By symmetry
        # Flat top reach
        idx_tri[16,:] = [5,8,22]
        idx_tri[17,:] = [5,19,22]
        # Side slopes of the flat top reach
        idx_tri[18,:] = [5,6,12]
        idx_tri[19,:] = [5,8,12]
        idx_tri[20,:] = idx_tri[18,:] + 14 # By symmetry
        idx_tri[21,:] = idx_tri[19,:] + 14 # By symmetry
    elif tri_type == 1: # Point 8 is on the D/S face of the dike
        idx_tri = np.zeros((36,3), dtype=int)
        # U/S side slope of the dike
        idx_tri[0,:] = [3,4,6]
        idx_tri[1,:] = [4,5,6]
        idx_tri[2,:] = idx_tri[0,:] + 14 # By symmetry
        idx_tri[3,:] = idx_tri[1,:] + 14 # By symmetry
        idx_tri[4,:] = [4,5,18]
        idx_tri[5,:] = [5,18,19]
        # D/S side slope of the dike
        idx_tri[6,:] = [0,1,2]
        idx_tri[7,:] = [0,2,10]
        idx_tri[8,:] = [2,10,12]
        idx_tri[9,:] = [7,10,12]
        idx_tri[10,:] = idx_tri[6,:] + 14 # By symmetry
        idx_tri[11,:] = idx_tri[7,:] + 14 # By symmetry
        idx_tri[12,:] = idx_tri[8,:] + 14 # By symmetry
        idx_tri[13,:] = idx_tri[9,:] + 14 # By symmetry
        # Dike crest
        idx_tri[14,:] = [2,3,6]
        idx_tri[15,:] = [2,6,12]
        idx_tri[16,:] = idx_tri[14,:] + 14 # By symmetry
        idx_tri[17,:] = idx_tri[15,:] + 14 # By symmetry
        # Flat top reach
        idx_tri[18,:] = [5,8,22]
        idx_tri[19,:] = [5,19,22]
        # Side slopes of the flat top reach
        idx_tri[20,:] = [5,6,12]
        idx_tri[21,:] = [5,7,12]
        idx_tri[22,:] = [5,7,8]
        idx_tri[23,:] = idx_tri[20,:] + 14 # By symmetry
        idx_tri[24,:] = idx_tri[21,:] + 14 # By symmetry
        idx_tri[25,:] = idx_tri[22,:] + 14 # By symmetry
        # D/S reach
        idx_tri[26,:] = [0,8,9]
        idx_tri[27,:] = [0,8,22]
        idx_tri[28,:] = [0,14,22]
        idx_tri[29,:] = [14,22,23]
        # Side slopes of the D/S reach
        idx_tri[30,:] = [0,9,10]
        idx_tri[31,:] = idx_tri[30,:] + 14 # By symmetry
        # Small trapezoids at the interface between flat top reach and D/S reach
        idx_tri[32,:] = [7,8,9]
        idx_tri[33,:] = [7,9,10]
        idx_tri[34,:] = idx_tri[32,:] + 14 # By symmetry
        idx_tri[35,:] = idx_tri[33,:] + 14 # By symmetry
    elif tri_type == 2: # Point 8 is on the crest of the dike
        idx_tri = np.zeros((36,3), dtype=int) # 13 faces
        # U/S side slope of the dike
        idx_tri[0,:] = [3,4,6]
        idx_tri[1,:] = [4,5,6]
        idx_tri[2,:] = idx_tri[0,:] + 14 # By symmetry
        idx_tri[3,:] = idx_tri[1,:] + 14 # By symmetry
        idx_tri[4,:] = [4,5,18]
        idx_tri[5,:] = [5,18,19]
        # D/S side slope of the dike
        idx_tri[6,:] = [0,1,2]
        idx_tri[7,:] = [0,2,11]
        idx_tri[8,:] = idx_tri[6,:] + 14 # By symmetry
        idx_tri[9,:] = idx_tri[7,:] + 14 # By symmetry
        # Dike crest
        idx_tri[10,:] = [2,3,11]
        idx_tri[11,:] = [3,10,11]
        idx_tri[12,:] = [3,6,10]
        idx_tri[13,:] = [6,7,10]
        idx_tri[14,:] = idx_tri[10,:] + 14 # By symmetry
        idx_tri[15,:] = idx_tri[11,:] + 14 # By symmetry
        idx_tri[16,:] = idx_tri[12,:] + 14 # By symmetry
        idx_tri[17,:] = idx_tri[13,:] + 14 # By symmetry
        # Flat top reach
        idx_tri[18,:] = [5,8,22]
        idx_tri[19,:] = [5,19,22]
        # Side slopes of the flat top reach
        idx_tri[20,:] = [5,6,7]
        idx_tri[21,:] = [5,7,8]
        idx_tri[22,:] = idx_tri[20,:] + 14 # By symmetry
        idx_tri[23,:] = idx_tri[21,:] + 14 # By symmetry
        # D/S reach
        idx_tri[24,:] = [0,8,9]
        idx_tri[25,:] = [0,8,22]
        idx_tri[26,:] = [0,14,22]
        idx_tri[27,:] = [14,22,23]
        # Side slopes of the D/S reach
        idx_tri[28,:] = [0,9,10]
        idx_tri[29,:] = [0,10,11]
        idx_tri[30,:] = idx_tri[28,:] + 14 # By symmetry
        idx_tri[31,:] = idx_tri[29,:] + 14 # By symmetry
        # Small trapezoids at the interface between flat top reach and D/S reach -> delete to avoid superposition of triangles
        idx_tri[32,:] = [7,8,9]
        idx_tri[33,:] = [7,9,10]
        idx_tri[34,:] = idx_tri[32,:] + 14 # By symmetry
        idx_tri[35,:] = idx_tri[33,:] + 14 # By symmetry
    elif tri_type == 3: # Point 8 is on the U/S face of the dike
        idx_tri = np.zeros((36,3), dtype=int)
        # U/S side slope of the dike
        idx_tri[0,:] = [3,4,13]
        idx_tri[1,:] = [4,10,13]
        idx_tri[2,:] = [4,7,10]
        idx_tri[3,:] = [4,5,7]
        idx_tri[4,:] = idx_tri[0,:] + 14 # By symmetry
        idx_tri[5,:] = idx_tri[1,:] + 14 # By symmetry
        idx_tri[6,:] = idx_tri[2,:] + 14 # By symmetry
        idx_tri[7,:] = idx_tri[3,:] + 14 # By symmetry
        idx_tri[8,:] = [4,5,18]
        idx_tri[9,:] = [5,18,19]
        # D/S side slope of the dike
        idx_tri[10,:] = [0,1,2]
        idx_tri[11,:] = [0,2,11]
        idx_tri[12,:] = idx_tri[10,:] + 14 # By symmetry
        idx_tri[13,:] = idx_tri[11,:] + 14 # By symmetry
        # Dike crest
        idx_tri[14,:] = [2,3,11]
        idx_tri[15,:] = [3,11,13]
        idx_tri[16,:] = idx_tri[14,:] + 14 # By symmetry
        idx_tri[17,:] = idx_tri[15,:] + 14 # By symmetry
        # Flat top reach
        idx_tri[18,:] = [5,8,22]
        idx_tri[19,:] = [5,19,22]
        # Side slopes of the flat top reach
        idx_tri[20,:] = [5,7,8]
        idx_tri[21,:] = idx_tri[20,:] + 14 # By symmetry
        # D/S reach !!!!!!
        idx_tri[22,:] = [0,8,9]
        idx_tri[23,:] = [0,8,22]
        idx_tri[24,:] = [0,14,22]
        idx_tri[25,:] = [14,22,23]
        # Side slopes of the D/S reach
        idx_tri[26,:] = [0,9,10]
        idx_tri[27,:] = [0,10,13]
        idx_tri[28,:] = [0,11,13]
        idx_tri[29,:] = idx_tri[26,:] + 14 # By symmetry
        idx_tri[30,:] = idx_tri[27,:] + 14 # By symmetry
        idx_tri[31,:] = idx_tri[28,:] + 14 # By symmetry
        # Small trapezoids at the interface between flat top reach and D/S reach  -> delete to avoid superposition of triangles
        idx_tri[32,:] = [7,8,9]
        idx_tri[33,:] = [7,9,10]
        idx_tri[34,:] = idx_tri[32,:] + 14 # By symmetry
        idx_tri[35,:] = idx_tri[33,:] + 14 # By symmetry
    elif tri_type == 4: # Point 8 is on the ground -> flat top reach + D/S reach merged (single breach width = D/S breach width)
        if coord_tri[25,0] > coord_tri[18,0]: # Out of the interpolated breach topography
            idx_tri = np.zeros((2,3), dtype=int) # 1 face
            idx_tri[0,:] = [1,4,18]
            idx_tri[1,:] = [1,15,18]
            warnings.warn('The breach is larger than the interpolated area.')
        else:
            idx_tri = np.zeros((18,3), dtype=int) # 9 faces
            # U/S side slope of the dike
            idx_tri[0,:] = [3,4,5]
            idx_tri[1,:] = [3,5,6]
            idx_tri[2,:] = idx_tri[0,:] + 14 # By symmetry
            idx_tri[3,:] = idx_tri[1,:] + 14 # By symmetry
            # D/S side slope of the dike
            idx_tri[4,:] = [0,1,2]
            idx_tri[5,:] = [0,2,12]
            idx_tri[6,:] = idx_tri[4,:] + 14 # By symmetry
            idx_tri[7,:] = idx_tri[5,:] + 14 # By symmetry
            # Dike crest
            idx_tri[8,:] = [2,3,12]
            idx_tri[9,:] = [3,6,12]
            idx_tri[10,:] = idx_tri[8,:] + 14 # By symmetry
            idx_tri[11,:] = idx_tri[9,:] + 14 # By symmetry
            # Flat top reach (D/S reach and small trapezoids cleared)
            idx_tri[12,:] = [0,5,14]
            idx_tri[13,:] = [5,14,19]
            # Side slopes of the flat top reach
            idx_tri[14,:] = [0,5,6]
            idx_tri[15,:] = [0,6,12]
            idx_tri[16,:] = idx_tri[14,:] + 14 # By symmetry
            idx_tri[17,:] = idx_tri[15,:] + 14 # By symmetry

    return coord_tri, idx_tri

# %%
