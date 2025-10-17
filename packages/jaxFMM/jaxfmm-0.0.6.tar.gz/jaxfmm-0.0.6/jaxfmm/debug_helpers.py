import jax.numpy as jnp
import jax.scipy as jsp
import jaxfmm.fmm as fmm
from math import isqrt
import numpy as np
import pyvista as pv
import os

__all__ = ["gen_stats","gen_hierarchy_vtk","gen_wellsep_vtk","gen_pts_vtk"]

def gen_stats(pts, eval_pts, idcs, boxcenters, eval_boxcenters, mpl_cnct, dir_cnct, img_cnct, lvl_info, n_split, periodic_axes, p, theta, print_stats = False, **kwargs):
    """Generate hierarchy stats. Use the hierarchy information from gen_hierarchy as input."""
    stats = {"p": p,
             "theta": theta,
             "max_l": len(boxcenters)-1,
             "eval_max_l": len(eval_boxcenters)-1,
             "num_pts": pts.shape[0],
             "num_eval_pts": eval_pts.shape[0],
             "num_child": 2**n_split,
             "pts_per_box": idcs[2][0].shape[1],
             "eval_pts_per_box": idcs[3][0].shape[1]}
    periodic = len(periodic_axes)>0
    mem_hierarch = idcs[0][0].nbytes + idcs[0][1].nbytes
    if(idcs[1] is not idcs[0]):
        mem_hierarch += idcs[1][0].nbytes + idcs[1][1].nbytes
    if(idcs[2] is not idcs[0]):
        mem_hierarch += idcs[2][0].nbytes + idcs[2][1].nbytes
    if((idcs[3] is not idcs[1]) and (idcs[3] is not idcs[2])):
        mem_hierarch += idcs[3][0].nbytes + idcs[3][1].nbytes
    mem_hierarch = dir_cnct.nbytes + img_cnct.nbytes
    M2L_nums = []
    M2L_pad_fracs = []
    n_img = img_cnct.shape[0]

    for i in range(len(lvl_info)-1):
        _, l_src = lvl_info[i]
        num_nopad = (mpl_cnct[i] < boxcenters[l_src].shape[0]*n_img).sum().tolist()
        M2L_nums.append(mpl_cnct[i].size)
        mem_hierarch += mpl_cnct[i].nbytes
        M2L_pad_fracs.append(1 if num_nopad==0 else M2L_nums[-1] / num_nopad)

    for i in range(stats["max_l"]):
        mem_hierarch += boxcenters[i].nbytes
        if 'boxlens' in kwargs:
            mem_hierarch += kwargs.get("boxlens")[i].nbytes

    if(eval_pts is not pts):
        for i in range(stats["eval_max_l"]):
            mem_hierarch += eval_boxcenters[i].nbytes
            if 'eval_boxlens' in kwargs:
                mem_hierarch += kwargs.get("eval_boxlens")[i].nbytes

    stats["M2L_nums"] = M2L_nums
    stats["lvl_info"] = lvl_info
    stats["M2L_pad_fracs"] = M2L_pad_fracs
    stats["direct_num"] = dir_cnct.size
    dir_no_pad = (dir_cnct < boxcenters[lvl_info[-1][1]].shape[0]*n_img).sum().tolist()
    stats["direct_pad_frac"] = (dir_cnct.size / dir_no_pad) if dir_no_pad != 0 else 1
    stats["compression_ratio"] = dir_no_pad * idcs[3][0].shape[1] * idcs[2][0].shape[1] / (pts.shape[0]*eval_pts.shape[0])
    stats["mem_hierarch"] = mem_hierarch
    stats["mem_coeffs"] = 4*2*((p+1)**2)*(8**(stats["max_l"]+1)-1)/7 # 4 bytes, 2 arrays, (p+1)**2 coeffs and nboxes
    stats["mem_pts_chrgs"] = (pts.nbytes*4)/3
    if(eval_pts is not pts):
        stats["mem_pts_chrgs"] += eval_pts.nbytes
    if(print_stats):
        print("---------------------FMM Hierarchy Stats---------------------")
        print("p = %i, theta = %.2f, %i children per box"%(p,theta,stats["num_child"]))
        if(periodic): 
            print("Periodic boundary on axes: ", periodic_axes)
        print("%i points, %i levels, %i particles per box"%(stats["num_pts"],stats["max_l"], stats["pts_per_box"]))
        if(eval_pts is not pts):
            print("%i eval points, %i eval levels, %i eval points per box"%(stats["num_eval_pts"],stats["eval_max_l"],stats["eval_pts_per_box"]))
        print("")
        print(" (l_eval, l_src) | padding frac. | interactions")
        print("-----------------------------------------------")
        for i in range(len(lvl_info)-1):
            l_eval, l_src = lvl_info[i]
            print(" M2L (%2i,%2i)     |     %5.2f     | %11i"%(l_eval, l_src, stats["M2L_pad_fracs"][i], stats["M2L_nums"][i]))
        totsum = jnp.array(stats["M2L_nums"]).sum()
        print("-----------------------------------------------")
        print(" M2L Total:            %5.2f       %11i"%(totsum/jnp.array(stats["M2L_nums"]).dot(1/jnp.array(stats["M2L_pad_fracs"])),totsum))
        print("-----------------------------------------------")
        print(" dir (%2i,%2i)     |     %5.2f     | %11i"%(lvl_info[-1][0], lvl_info[-1][1], stats["direct_pad_frac"], stats["direct_num"]))
        print("-----------------------------------------------")
        print("\nDirect interaction compression (without padding): %.2e"%(stats["compression_ratio"]))
        print("\nMemory used by the hierarchy:            %.2e Bytes"%stats["mem_hierarch"])
        print("Memory used by mpl + local coeffs (p=%i): %.2e Bytes"%(p, stats["mem_coeffs"])) 
        print("Memory used by the points + charges:     %.2e Bytes"%stats["mem_pts_chrgs"])
        print("-------------------------------------------------------------")
    return stats

def make_pyvista_mesh(boxcenters, boxlens):
    pv_shifts = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
    pts = np.zeros((boxcenters.shape[0],8,3))
    for i in range(pv_shifts.shape[0]):
        pts[:,i,:] = boxcenters + boxlens/2 * pv_shifts[i,None,:]
    pts = pts.reshape((-1,3))
    cells = np.arange(pts.shape[0],dtype=np.int32).reshape((-1,8))
    return pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells}, pts)

def gen_hierarchy_vtk(boxcenters, boxlens, eval_boxcenters, eval_boxlens, dir="hierarchy", **kwargs):
    r"""
    Output a series of vtk files showing the FMM hierarchy on every level. Does not show virtual PBC images.
    """
    eval_max_l = len(eval_boxcenters)
    max_l = len(boxcenters)
    if not os.path.exists(dir):
        os.makedirs(dir)
    for l in range(max_l):
        mesh = make_pyvista_mesh(boxcenters[l],boxlens[l])
        mesh.cell_data["src_level"] = np.ones(mesh.points.shape[0]//8)*l
        mesh.save("%s/src_level_%i.vtk"%(dir,l))
    
    if(eval_boxcenters is not boxcenters or eval_boxlens is not boxlens):
        for l in range(eval_max_l):
            mesh = make_pyvista_mesh(eval_boxcenters[l],eval_boxlens[l])
            mesh.cell_data["eval_level"] = np.ones(mesh.points.shape[0]//8)*l
            mesh.save("%s/eval_level_%i.vtk"%(dir,l))

def gen_pts_vtk(pts, eval_pts, dir="hierarchy", **kwargs):
    r"""
    Output the hierarchy points as vtk.
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    point_cloud = pv.PolyData(np.array(pts))
    point_cloud.save("%s/src_pts.vtk"%(dir))
    point_cloud = pv.PolyData(np.array(eval_pts))
    point_cloud.save("%s/eval_pts.vtk"%(dir))

def gen_wellsep_vtk(id, boxcenters, boxlens, eval_boxcenters, eval_boxlens, mpl_cnct, dir_cnct, img_cnct, lvl_info, n_split, pbc_ws, dir="hierarchy", **kwargs):
    r"""
    Output a vtk file showing all the boxes that are considered for potential calculation, given an id of a box on the highest level. Includes virtual PBC images.
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    max_l_eval = lvl_info[-1][0]
    n_chi = 2**n_split
    periodic = len(pbc_ws)>0
    meshlist = []

    L = boxlens[0][0]
    for l, img_cnct_ws in enumerate(pbc_ws):
        mesh = make_pyvista_mesh(boxcenters[0] - img_cnct_ws[1],jnp.tile(L,(img_cnct_ws[1].shape[0],1)))
        mesh.cell_data["eval_level"] = np.ones(mesh.points.shape[0]//8)*(-l)
        mesh.cell_data["src_level"] = np.ones(mesh.points.shape[0]//8)*(-l)
        meshlist.append(mesh)
        L += jnp.ptp(img_cnct_ws[0],axis=0)

    for i in range(len(lvl_info)-1):
        l_eval, l_src = lvl_info[i]
        extract = mpl_cnct[i][id//(n_chi**(max_l_eval-l_eval))]
        n_src = n_chi**l_src
        if(periodic):
            extract = extract[extract < (n_src*img_cnct.shape[0])]
            mesh = make_pyvista_mesh(boxcenters[l_src][extract%n_src] + img_cnct[extract//n_src],boxlens[l_src][extract%n_src])
        else:
            extract = extract[extract < n_src]
            mesh = make_pyvista_mesh(boxcenters[l_src][extract],boxlens[l_src][extract])
        mesh.cell_data["eval_level"] = np.ones(mesh.points.shape[0]//8)*(l_eval)
        mesh.cell_data["src_level"] = np.ones(mesh.points.shape[0]//8)*(l_src)
        meshlist.append(mesh)

    l_eval, l_src = lvl_info[-1]
    extract = dir_cnct[id]
    n_src = n_chi**l_src
    if(periodic):
        extract = extract[extract<n_src*img_cnct.shape[0]]
        mesh = make_pyvista_mesh(boxcenters[-1][extract%n_src] + img_cnct[extract//n_src],boxlens[-1][extract%n_src])
    else:
        extract = extract[extract < n_src]
        mesh = make_pyvista_mesh(boxcenters[l_src][extract],boxlens[l_src][extract])

    mesh.cell_data["eval_level"] = np.ones(mesh.points.shape[0]//8)*(l_eval + 1)
    mesh.cell_data["src_level"] = np.ones(mesh.points.shape[0]//8)*(l_src + 1)
    meshlist.append(mesh)

    mesh = make_pyvista_mesh(eval_boxcenters[l_eval][id][None,:],eval_boxlens[l_eval][id][None,:]*1.001)   # the multiplication fixes pyvista getting confused for eval_pts = pts
    mesh.cell_data["eval_level"] = np.ones(1)*(l_eval + 2)
    mesh.cell_data["src_level"] = np.ones(1)*(l_src + 2)
    meshlist.append(mesh)

    mergedmesh = pv.merge(meshlist)
    mergedmesh.save("%s/wellsep_%i.vtk"%(dir,id))

def eval_multipole(coeff, boxcenter, eval_pts):
    r"""
    Evaluate a single multipole expansion.
    """
    p = get_deg(coeff.shape[-1])
    sing = fmm.eval_singular_basis(eval_pts - boxcenter,p)
    res = jnp.zeros(eval_pts.shape[0])
    for n in range(p+1):
        for m in range(-n,n+1):
            if(m!=0):
                res += (-1)**n * 2 * coeff[...,fmm.mpl_idx(m,n)] * sing[...,fmm.mpl_idx(-m,n)]
            else:
                res += (-1)**n * coeff[...,fmm.mpl_idx(m,n)] * sing[...,fmm.mpl_idx(-m,n)] 
    res /= (4*jnp.pi)
    return res

def get_local_expansions(pts, chrgs, exp_centers, p):
    r"""
    Generate local expansions.
    """
    dist = pts[None,...] - exp_centers[:,None,:]
    coeff = (fmm.eval_singular_basis(dist,p) * chrgs[None,:,None]).sum(axis=1)
    return coeff

def binom(x, y):
  return jnp.exp(jsp.special.gammaln(x + 1) - jsp.special.gammaln(y + 1) - jsp.special.gammaln(x - y + 1))

def gen_multipole_dist(m, n, eps = 0.5):
    r"""
    Generate a point charge distribution corresponding to a specific multipole moment (Majic, Matt. (2022). Point charge representations of multipoles. European Journal of Physics. 43. 10.1088/1361-6404/ac578b.)
    """
    if(m == 0):   # axial
        k = jnp.arange(-n, n+1, 2)
        chrgs = (-1)**((n-k)/2) * binom(n, (n-k)/2.0) / (jsp.special.factorial(n) * (2*eps)**n)
        pts = jnp.zeros((k.shape[0],3))
        pts = pts.at[:,2].set(k*eps)
    else:         # (stacked) bracelet
        rotate = m < 0
        m = abs(m)      # we work with the real basis and rotate later
        knum = n-m+1
        jnum = 2*m
        j = jnp.tile(jnp.arange(jnum),knum)
        k = jnp.repeat(jnp.arange(-n+m,n-m+1,2),jnum)
        phi = (j-0.5) * jnp.pi/m if rotate else j * jnp.pi/m
        pts = jnp.array([eps*jnp.cos(phi), eps*jnp.sin(phi), k*eps]).T
        chrgs = 4**(m-1) * jsp.special.factorial(m-1) / ((2*eps)**n * jsp.special.factorial(n-m)) * (-1)**((n-m-k)/2 + j) * binom(n-m,(n-m-k)/2)
    return pts, chrgs

def get_deg(N_coeff):
    r"""
    Get the degree p of a multipole expansion from the number of coefficients.
    """
    return isqrt(N_coeff) - 1