import jax
import jax.numpy as jnp
from functools import partial
from math import log2, ceil, sqrt

__all__ = ["gen_hierarchy", "eval_potential", "eval_potential_direct"]

def get_max_l(N_tot, N_max, n_split = 3): # need to get this outside of the jit compiled function - if the particle number changes too much, we must recompile...
    r"""
    Compute number of levels in the hierarchy.
    """
    max_l = int(ceil(log2(N_tot/N_max)/n_split))
    return 0 if max_l < 0 else max_l

@partial(jax.jit, static_argnames = ["max_l", "n_split"])
def balanced_tree(pts, max_l, n_split = 3):
    r"""
    Generate a balanced 2^n-tree hierarchy.
    """
    n_chi = 2**n_split
    idcs = jnp.arange(pts.shape[0], dtype = jnp.int32)[None,:]

    for l in range(max_l*n_split):    # carry out n_split splits on max_l levels in total (we cannot make this a for_i loop as the shape constantly changes)
        splitpos = idcs.shape[1]//2   # split position in the middle
        needpad = idcs.shape[1]%2     # modulo tells us if padding must be inserted

        pts_sorted = pts.at[idcs].get(mode="fill",fill_value=-jnp.nan**2)  # padded values get converted to NaNs - NOTE: due to the argpartition implementation, we need to make sure that all the NaNs have the same sign
        axis_to_split = jnp.argmax(jnp.nanmax(pts_sorted,axis=1) - jnp.nanmin(pts_sorted,axis=1),axis=1)    # nanmax and -min to ignore NaNs
        idcs = idcs[jnp.arange(idcs.shape[0], dtype = jnp.int32)[:,None],jnp.argpartition(pts_sorted[jnp.arange(axis_to_split.shape[0], dtype = jnp.int32),:,axis_to_split],splitpos,axis=1)] # splitting - the NaNs introduced below get transported to the beginning

        # padding so the next array has the correct shape - this does not break JIT compiling because it can be computed from only the input shape
        idcs = jax.lax.pad(idcs,jnp.int32(pts.shape[0]),[(0,0,0),(0,needpad,0)])   # pad at the end with out of range values
        idcs = idcs.reshape((-1,idcs.shape[1]//2))                      # now that we padded, we can safely reshape this
    
    idcs = jnp.sort(idcs,axis=1)    # sorting is good for locality but might be overkill TODO: swap only first and last positions instead of full sort?
    rev_idcs = jnp.argsort(idcs.flatten())[:pts.shape[0]]     # reverse sorting indices, to undo the sorting
    pts_sorted = pts.at[idcs].get(mode="fill",fill_value=jnp.nan)  
    boxcenters, boxlens = [jnp.zeros((n_chi**l,3)) for l in range(max_l+1)], [jnp.zeros((n_chi**l,3)) for l in range(max_l+1)]

    for l in range(max_l,-1,-1):
        minc, maxc = jnp.nanmin(pts_sorted,axis=1), jnp.nanmax(pts_sorted,axis=1)    # nanmax and -min to ignore NaNs
        boxlens[l] = maxc - minc    # TODO: in principle we only need to save the norm of this, but it is nice to have for visualizations
        boxcenters[l] = minc + boxlens[l]/2
        if(l > 0):
            pts_sorted = pts_sorted.reshape((-1,pts_sorted.shape[1]*n_chi,3))
    return idcs, rev_idcs, boxcenters, boxlens

def reduce_max_lvl(pts, idcs, n_split, old_max_l, new_max_l):
    r"""
    Reduce max level of a balanced tree after it has already been created.
    """
    ldiff = old_max_l - new_max_l
    idcs = idcs.reshape((idcs.shape[0]//(2**(n_split*ldiff)),-1))
    trim = idcs.shape[1] - (idcs.size - pts.shape[0])//idcs.shape[0]
    idcs = jnp.sort(idcs,axis=-1)[:,:trim] # we know exactly how much padding is accumulated!
    rev_idcs = jnp.argsort(idcs.flatten())[:pts.shape[0]] # also fix the reverse sorting
    return idcs, rev_idcs

def gen_img_connectivity(L0_boxlen, theta, periodic_axes):
    r"""
    Similar to gen_connectivity, but computes connectivity information for periodic images.
    The generated patterns are rectangular cuboids, which helps mitigate numerical inaccuracies for the resulting PBC operator.
    """
    R = jnp.linalg.norm(L0_boxlen/2)                           # r = R in this case, all boxes are the same
    num_images = jnp.int32((1+theta)/(theta*L0_boxlen) * R)[0] # lower bound of non-ws images in axis directions
    non_per = jnp.array([False if i in periodic_axes else True for i in range(3)])
    num_images = num_images.at[non_per].set(0)
    mul_facs = 2*num_images + 1                                # total number of boxes in axis directions
    ids = [slice(-num_images[i],num_images[i]+1) if i in periodic_axes else slice(0,1) for i in range(3)]
    img_ids = jnp.reshape(jnp.mgrid[ids].T,(-1,3))  # spawn all the images

    L0_boxlen_up = L0_boxlen * mul_facs   # boxlength on the parent level
    R_up = jnp.linalg.norm(L0_boxlen_up/2)
    num_images_up = jnp.int32((1+theta)/(theta*L0_boxlen_up) * R_up)[0] # upper bound of ws images in axis directions
    ids_up = [slice(-num_images_up[i],num_images_up[i]+1) if i in periodic_axes else slice(0,1) for i in range(3)]
    img_ids_up = jnp.reshape(jnp.mgrid[ids_up].T,(-1,3))                                # spawn parent images
    img_ids_up = img_ids_up[jnp.any(img_ids_up!=0,axis=-1)]                             # we take out the non-ws area
    img_ids_up = ((mul_facs*img_ids_up)[:,None,:] + img_ids[None,:,:]).reshape((-1,3))  # spawn children for each remaining parent

    return img_ids*L0_boxlen, img_ids_up*L0_boxlen, mul_facs

@partial(jax.jit, static_argnames = ["p"])
def gen_M2Mop(p, dists, reg_zeros = []):
    r"""
    Generate M2M operator matrix for PBC.
    """
    reg = eval_regular_basis(dists,p).sum(axis=0)   # sign of dists does not matter here (symmetry)
    reg = reg.at[reg_zeros].set(0)  # manually set terms to zero that should be zero (symmetry)
    M2Mop = jnp.zeros(((p+1)**2,(p+1)**2))

    for j in range(p+1):
        for k in range(0,j+1):  # Real coeffs
            for n in range(j+1):
                for m in range(max(k+n-j,-n),min(k+j-n,n)+1):
                    M2Mop = M2Mop.at[mpl_idx(k,j),mpl_idx(abs(k-m),j-n)].add((-1)**((abs(k)-abs(m)-abs(k-m))//2) * reg[...,mpl_idx(abs(m),n)])
                    M2Mop = M2Mop.at[mpl_idx(k,j),mpl_idx(-abs(k-m),j-n)].add(-(-1)**((abs(k)-abs(m)-abs(k-m))//2) * jnp.sign(m)*jnp.sign(k-m)*reg[mpl_idx(-abs(m),n)])
        for k in range(-j,0):   # Imag coeffs
            for n in range(j+1):
                for m in range(max(k+n-j,-n),min(k+j-n,n)+1):
                    M2Mop = M2Mop.at[mpl_idx(k,j),mpl_idx(-abs(k-m),j-n)].add(-(-1)**((abs(k)-abs(m)-abs(k-m))//2) * jnp.sign(k-m)*reg[...,mpl_idx(abs(m),n)])
                    M2Mop = M2Mop.at[mpl_idx(k,j),mpl_idx(abs(k-m),j-n)].add(-(-1)**((abs(k)-abs(m)-abs(k-m))//2) * jnp.sign(m)*reg[...,mpl_idx(-abs(m),n)])
    return M2Mop

@partial(jax.jit, static_argnames = ["p"])
def gen_M2Lop(p, dists, sing_zeros = []):
    r"""
    Generate M2L operator matrix for PBC.
    """
    sing = eval_singular_basis(dists,2*p).sum(axis=0)   # sign of dists does not matter here (symmetry)
    sing = sing.at[sing_zeros].set(0) # manually set terms to zero that should be zero (symmetry)
    M2Lop = jnp.zeros(((p+1)**2,(p+1)**2))

    for j in range(p+1):
        for k in range(1,j+1):  # -Imag coeffs!
            for n in range(p+1):
                for m in range(max(k-j-n,-n),min(j+n+k,n)+1):
                    M2Lop = M2Lop.at[mpl_idx(k,j),mpl_idx(abs(m),n)].add((-1)**((abs(k-m)-abs(k)-abs(m))//2) * (-jnp.sign(m-k)*sing[mpl_idx(abs(m-k),j+n)]))
                    M2Lop = M2Lop.at[mpl_idx(k,j),mpl_idx(-abs(m),n)].add((-1)**((abs(k-m)-abs(k)-abs(m))//2) * jnp.sign(m)*sing[mpl_idx(-abs(m-k),j+n)])
        for k in range(-j,1):   # Real coeffs!
            for n in range(p+1):
                for m in range(max(k-j-n,-n),min(j+n+k,n)+1):
                    M2Lop = M2Lop.at[mpl_idx(k,j),mpl_idx(abs(m),n)].add((-1)**((abs(k-m)-abs(k)-abs(m))//2) * sing[mpl_idx(-abs(m-k),j+n)])
                    M2Lop = M2Lop.at[mpl_idx(k,j),mpl_idx(-abs(m),n)].add((-1)**((abs(k-m)-abs(k)-abs(m))//2) * jnp.sign(m)* jnp.sign(m-k) * sing[mpl_idx(abs(m-k),j+n)])
    return M2Lop

def gen_pbc_op(L, theta, periodic_axes, p, pbc_lvls, pbc_no_monopole):
    r"""
    Generate full PBC operator matrix.
    """
    par_zero = [jnp.zeros(((i+1)*p+1)**2,dtype=jnp.uint8) for i in range(2)]
    for i, func in enumerate((eval_regular_basis,eval_singular_basis)):
        par = func(jnp.array([1,2,3]),(i+1)*p)
        uneven = jnp.any(jnp.stack((func(jnp.array([-1,2,3]),(i+1)*p)/par < 0,
                                    func(jnp.array([1,-2,3]),(i+1)*p)/par < 0,
                                    func(jnp.array([1,2,-3]),(i+1)*p)/par < 0),axis=-1),axis=-1)  # as long as the pattern is symmetric, these cancel
        #cubic = jnp.abs(func(jnp.array([1,1,1]),p))<1e-6   # these components only cancel for patterns that are both symmetric and cubic
        par_zero[i] = jnp.where(par_zero[i].at[uneven].set(1))[0]
    reg_zeros, sing_zeros = par_zero

    img_non_ws, img_ws, mul_facs = gen_img_connectivity(L,theta,periodic_axes)
    M2Mop = jnp.eye((p+1)**2)
    res = gen_M2Lop(p,img_ws,sing_zeros)
    img_cnct_list = [[img_non_ws, img_ws]]
    for i in range(1,pbc_lvls+1):
        L *= mul_facs
        img_non_ws, img_ws, mul_facs = gen_img_connectivity(L,theta,periodic_axes)
        M2Mop = gen_M2Mop(p, img_non_ws,reg_zeros)@M2Mop
        M2Lop = gen_M2Lop(p, img_ws,sing_zeros)
        res += M2Lop@M2Mop
        img_cnct_list.append([img_non_ws, img_ws])
    if(pbc_no_monopole):    # set monopole contribution to zero
        res = res.at[0,0].set(0)
    return res, img_cnct_list

#@partial(jax.jit, static_argnames = ["theta", "n_split"])
def gen_connectivity(boxcenters, boxlens, eval_boxcenters, eval_boxlens, theta = 0.75, n_split = 3, no_cross_level = False, periodic_axes = ()): # TODO: is there a way to make this JIT compilable?
    r"""
    Compute connectivity information for a given hierarchy.
    """
    n_l, eval_n_l = len(boxcenters), len(eval_boxcenters)  # number of levels of the source and eval hierarchy
    n_chi = 2**n_split     # number of child boxes per split
    periodic = len(periodic_axes) > 0
    if(periodic):
        img_cnct = gen_img_connectivity(boxlens[0], theta, periodic_axes)[0]
    else:
        img_cnct = jnp.array([[]])

    n_img = img_cnct.shape[0]
    l_src, l_eval = 0, 0
    mpl_cnct, lvl_info = [], []
    non_wellseps = jnp.arange(n_img,dtype = jnp.int32)[None,:]
    keepgoing = True
    while(keepgoing):
        evalend, srcend = (l_eval >= (eval_n_l-1)), (l_src >= (n_l-1))
        keepgoing = not (evalend and srcend)    # we keep going until we reach the final level in both hierarchies
        nbox, nbox_eval = boxcenters[l_src].shape[0], eval_boxcenters[l_eval].shape[0]

        if(periodic):
            rhs = boxcenters[l_src][non_wellseps%nbox] + img_cnct.at[non_wellseps//nbox].get(mode="fill",fill_value=jnp.nan)
        else:
            rhs = boxcenters[l_src].at[non_wellseps].get(mode="fill",fill_value=jnp.nan)
        d = jnp.linalg.norm(eval_boxcenters[l_eval][:,None,:] - rhs,axis=-1)  # distances between boxcenters

        r1 = jnp.linalg.norm(eval_boxlens[l_eval][:,None,:],axis=-1)/2  # eval box radii
        r2 = jnp.linalg.norm(boxlens[l_src][non_wellseps%nbox if periodic else non_wellseps],axis=-1)/2 # source box radii
        tmp = r1 > r2
        R = jnp.where(tmp,r1,r2)     # R = max(r1,r2)
        r = jnp.where(tmp,r2,r1)     # r = min(r1,r2)

        ws = (R + theta*r <= theta*d)     # well-separatedness criterion, NaNs always return False
        non_ws = (R + theta*r > theta*d)  # need to check again to exclude NaNs
        ws_nums = ws.sum(axis=1)          # number of well-separated boxes for each box
        non_ws_nums = non_ws.sum(axis=1)  # number of non-well-separated boxes for each box

        to_pad_ws = jnp.max(ws_nums) - ws_nums    # how much padding per box must be inserted
        ws_padding = jnp.repeat(jnp.cumsum(ws_nums),to_pad_ws)   # the correct indices for the insert below NOTE: this has a dynamic size and therefore breaks JIT compilation
        cnct_info = jnp.insert(non_wellseps[ws],ws_padding,n_img*nbox).reshape(nbox_eval,-1) # padded ws information
        if(cnct_info.shape[1] > 0):       # do not save empty cnct information
            mpl_cnct.append(cnct_info)
            lvl_info.append((l_eval, l_src))

        to_pad_non_ws = jnp.max(non_ws_nums) - non_ws_nums    # how much padding per box must be inserted for non-well-separated boxes
        non_wellsep_padding = jnp.repeat(jnp.cumsum(non_ws_nums),to_pad_non_ws)   # the correct indices for the insert below
        non_wellseps = jnp.insert(non_wellseps[non_ws],non_wellsep_padding,n_img*nbox).reshape((nbox_eval,-1))    # we overwrite the old values here
        if(non_wellseps.shape[1] == 0):   # we are already done, quit out
            break

        r1mean, r2mean = jnp.mean(r1), jnp.mean(r2)
        if((not srcend) and ((r1mean < 1.05 * r2mean) or evalend or no_cross_level)): # TODO: play around with the first condition and factors therein
            l_src += 1          # src_boxes >= eval_boxes -> increase src lvl
            non_wellseps = jnp.repeat(non_wellseps,n_chi,axis=1)*n_chi + jnp.tile(jnp.arange(n_chi, dtype = jnp.int32),non_wellseps.shape[1])   # indices change
        if((not evalend) and ((r1mean >= 1.05 * r2mean) or srcend or no_cross_level)):
            l_eval += 1             # eval boxes > src boxes -> increase eval lvl
            non_wellseps = jnp.repeat(non_wellseps,n_chi,axis=0)    # size of non-wellseps grows

    lvl_info.append((l_eval, l_src))
    return mpl_cnct, non_wellseps, tuple(lvl_info), img_cnct

def mpl_idx(m,n):
    r"""
    Compute "flattened" array position of multipole coefficient C^m_n with order m and degree n.
    """
    return n**2 + (m+n)

def inv_mpl_idx(idx):
    r"""
    Compute order m and degree n of "flattened" array position idx.
    """
    n = int(sqrt(idx))
    m = idx - n*(n+1)
    return m, n

@partial(jax.jit, static_argnames=['p'])
def eval_regular_basis(rvec, p):
    r"""
    Evaluate real regular basis functions (Laplace kernel) with a recursion relation [Gumerov, N. A. et al. Fast multipole methods on graphics processors. J. Comp. Phys., B 227, 8290 (2008)].
    """
    x, y, z = rvec[..., 0], rvec[...,1], rvec[...,2]
    r2 = jnp.linalg.norm(rvec,axis=-1)**2   # NOTE: somehow way faster than (x**2+y**2+z**2)
    coeff = jnp.zeros((*rvec.shape[:-1], (p+1)**2))
    coeff = coeff.at[...,mpl_idx(0,0)].set(1)

    if(p>0):
        coeff = coeff.at[...,mpl_idx(-1,1)].set(0.5*y)
        coeff = coeff.at[...,mpl_idx(0,1)].set(-z)
        coeff = coeff.at[...,mpl_idx(1,1)].set(-0.5*x)
    for n in range(2,p+1):    # first/second recursion: extreme values and their neighbors
        coeff = coeff.at[...,mpl_idx(-n,n)].set((y*coeff[...,mpl_idx(n-1,n-1)] - x*coeff[...,mpl_idx(1-n,n-1)])/(2*n))
        coeff = coeff.at[...,mpl_idx(-n+1,n)].set(-z*coeff[...,mpl_idx(-n+1,n-1)])
        for m in range(-n+2,n-1):   # third recursion: all values inbetween
            coeff = coeff.at[...,mpl_idx(m,n)].set(-((2*n-1)*z*coeff[...,mpl_idx(m,n-1)] + r2*coeff[...,mpl_idx(m,n-2)])/((n-abs(m))*(n+abs(m))))
        coeff = coeff.at[...,mpl_idx(n-1,n)].set(-z*coeff[...,mpl_idx(n-1,n-1)])
        coeff = coeff.at[...,mpl_idx(n,n)].set(-(x*coeff[...,mpl_idx(n-1,n-1)] + y*coeff[...,mpl_idx(1-n,n-1)])/(2*n))
    return coeff

@partial(jax.jit, static_argnames=['p'])
def eval_regular_basis_grad(rvec, p):
    r"""
    Evaluate the gradient of real regular basis functions (Laplace kernel) with a recursion relation.
    """
    scal_coeff = eval_regular_basis(rvec, p)

    x, y, z = rvec[..., 0], rvec[...,1], rvec[...,2]
    coeff = jnp.zeros((*rvec.shape[:-1], (p+1)**2, 3))

    if(p>0):
        coeff = coeff.at[...,mpl_idx(1,1),0].set(-0.5)
        coeff = coeff.at[...,mpl_idx(-1,1),1].set(0.5)

    for n in range(2,p+1):    # first recursion: extreme values
        coeff = coeff.at[...,mpl_idx(n,n),:].set(x[...,None]*coeff[...,mpl_idx(n-1,n-1),:] + y[...,None]*coeff[...,mpl_idx(1-n,n-1),:])
        coeff = coeff.at[...,mpl_idx(n,n),0].add(scal_coeff[...,mpl_idx(n-1,n-1)])
        coeff = coeff.at[...,mpl_idx(n,n),1].add(scal_coeff[...,mpl_idx(1-n,n-1)])
        coeff = coeff.at[...,mpl_idx(n,n),:].divide(-2*n)

        coeff = coeff.at[...,mpl_idx(-n,n),:].set(y[...,None]*coeff[...,mpl_idx(n-1,n-1),:] - x[...,None]*coeff[...,mpl_idx(1-n,n-1),:])
        coeff = coeff.at[...,mpl_idx(-n,n),0].subtract(scal_coeff[...,mpl_idx(1-n,n-1)])
        coeff = coeff.at[...,mpl_idx(-n,n),1].add(scal_coeff[...,mpl_idx(n-1,n-1)])
        coeff = coeff.at[...,mpl_idx(-n,n),:].divide(2*n)

    for n in range(0,p):      # second recursion: neighbors of extreme values
        coeff = coeff.at[...,mpl_idx(n,n+1),:].set(-z[...,None]*coeff[...,mpl_idx(n,n),:])
        coeff = coeff.at[...,mpl_idx(n,n+1),2].subtract(scal_coeff[...,mpl_idx(n,n)])

        coeff = coeff.at[...,mpl_idx(-n,n+1),:].set(-z[...,None]*coeff[...,mpl_idx(-n,n),:])
        coeff = coeff.at[...,mpl_idx(-n,n+1),2].subtract(scal_coeff[...,mpl_idx(-n,n)])

    for n in range(2,p+1):    # third recursion: all values inbetween
        for m in range(-n+2,n-1):
            coeff = coeff.at[...,mpl_idx(m,n),:].set((2*n-1)*z[...,None]*coeff[...,mpl_idx(m,n-1),:] + (x**2+y**2+z**2)[...,None]*coeff[...,mpl_idx(m,n-2),:] + 2*scal_coeff[...,mpl_idx(m,n-1),None]*rvec)
            coeff = coeff.at[...,mpl_idx(m,n),2].add((2*n - 1) * scal_coeff[...,mpl_idx(m,n-1)])
            coeff = coeff.at[...,mpl_idx(m,n),:].divide((abs(m) - n) * (n + abs(m)))

    return coeff

@partial(jax.jit, static_argnames=['p'])
def eval_singular_basis(rvec, p):   # NOTE: might have to include a factor (-1)^n, also use S_n^-m for evaluating
    r"""
    Evaluate real singular basis functions (Laplace kernel) with a recursion relation.
    """
    x, y, z = rvec[..., 0], rvec[...,1], rvec[...,2]
    r2 = jnp.linalg.norm(rvec,axis=-1)**2   # NOTE: somehow way faster than (x**2+y**2+z**2)
    coeff = jnp.zeros((*rvec.shape[:-1], (p+1)**2))
    coeff = coeff.at[...,mpl_idx(0,0)].set(1/jnp.sqrt(r2))

    if(p>0):
        coeff = coeff.at[...,mpl_idx(-1,1)].set(coeff[...,mpl_idx(0,0)]*x/r2)
        coeff = coeff.at[...,mpl_idx(0,1)].set(coeff[...,mpl_idx(0,0)]*z/r2)
        coeff = coeff.at[...,mpl_idx(1,1)].set(-coeff[...,mpl_idx(0,0)]*y/r2)
    for n in range(2,p+1): # first/second recursion: extreme values and their neighbors
        coeff = coeff.at[...,mpl_idx(-n,n)].set((2*n-1)*(y*coeff[...,mpl_idx(n-1,n-1)] + x*coeff[...,mpl_idx(1-n,n-1)])/r2)
        coeff = coeff.at[...,mpl_idx(-n+1,n)].set((2*n-1)*z*coeff[...,mpl_idx(-n+1,n-1)]/r2)
        for m in range(-n+2,n-1): # third recursion: all values inbetween
            coeff = coeff.at[...,mpl_idx(m,n)].set(((2*n-1)*z*coeff[...,mpl_idx(m,n-1)] - (n-1-m)*(n-1+m)*coeff[...,mpl_idx(m,n-2)])/r2)
        coeff = coeff.at[...,mpl_idx(n-1,n)].set((2*n-1)*z*coeff[...,mpl_idx(n-1,n-1)]/r2)
        coeff = coeff.at[...,mpl_idx(n,n)].set((2*n-1)*(x*coeff[...,mpl_idx(n-1,n-1)] - y*coeff[...,mpl_idx(1-n,n-1)])/r2)
    return coeff

@partial(jax.jit, static_argnames=['p'])
def get_initial_mpls(padded_pts, padded_chrgs, boxcenters, p):
    r"""
    Get initial multipole expansions for each box on the highest level.
    """
    dist = padded_pts - boxcenters[:,None]
    return (eval_regular_basis(dist,p) * padded_chrgs[...,None]).sum(axis=1)

@partial(jax.jit, static_argnames=['p', 'n_split'])
def M2M(coeff, oldboxdims, newboxdims, p, n_split):
    r"""
    Multipole-to-multipole transformation, merging "small" multipole expansions on higher levels into "large" multipole expansions on lower levels. This is the O(p^4) algorithm proposed in the original 3D FMM paper.
    """
    n_chi = 2**n_split
    mpls = coeff.reshape((coeff.shape[0]//n_chi,n_chi,coeff.shape[1]))
    new_mpls = jnp.zeros((mpls.shape[0],mpls.shape[2]))
    oldboxdims = oldboxdims.reshape((-1,n_chi,3))
    reg = eval_regular_basis(oldboxdims - newboxdims[:,None,:],p)   # shift direction points from target to source

    for j in range(p+1):
        for n in range(j+1):
            for k in range(0,j+1):  # Real coeffs
                for m in range(max(k+n-j,-n),min(k+j-n,n)+1):
                    new_mpls = new_mpls.at[...,mpl_idx(k,j)].set(new_mpls[...,mpl_idx(k,j)] + (-1)**((abs(k)-abs(m)-abs(k-m))//2) * (
                                                  reg[...,mpl_idx(abs(m),n)]*mpls[...,mpl_idx(abs(k-m),j-n)] - 
                                                  jnp.sign(m)*jnp.sign(k-m)*reg[...,mpl_idx(-abs(m),n)]*mpls[...,mpl_idx(-abs(k-m),j-n)]).sum(axis=-1))
            for k in range(-j,0):   # Imag coeffs
                for m in range(max(k+n-j,-n),min(k+j-n,n)+1):
                    new_mpls = new_mpls.at[...,mpl_idx(k,j)].set( new_mpls[...,mpl_idx(k,j)] - (-1)**((abs(k)-abs(m)-abs(k-m))//2) * (
                                                  jnp.sign(k-m)*reg[...,mpl_idx(abs(m),n)]*mpls[...,mpl_idx(-abs(k-m),j-n)] + 
                                                  jnp.sign(m)*reg[...,mpl_idx(-abs(m),n)]*mpls[...,mpl_idx(abs(k-m),j-n)]).sum(axis=-1))
    return new_mpls

@partial(jax.jit, static_argnames=['p', 'n_split'])
def L2L(locs, oldboxdims, newboxdims, p, n_split):
    r"""
    Local-to-local transformation, distributing "large" local expansions on lower levels to "small" local expansions on higher levels. This is the O(p^4) algorithm proposed in the original 3D FMM paper.
    """
    n_chi = 2**n_split
    new_locs = jnp.zeros((locs.shape[0], n_chi, locs.shape[1]))
    newboxdims = newboxdims.reshape((-1,n_chi,3))
    reg = eval_regular_basis(oldboxdims[:,None,:]-newboxdims,p)   # shift direction points from target to source

    for j in range(p+1):
        for k in range(1,j+1):  # -Imag coeffs!
            for n in range(j,p+1):
                for m in range(k+j-n,k+n-j+1):
                    new_locs = new_locs.at[...,mpl_idx(k,j)].set(new_locs[...,mpl_idx(k,j)] - (-1)**((abs(m)-abs(m-k)-abs(k))//2) * (
                                                  -jnp.sign(m)*reg[...,mpl_idx(abs(m-k),n-j)]*locs[...,None,mpl_idx(abs(m),n)] + 
                                                  jnp.sign(m-k)*reg[...,mpl_idx(-abs(m-k),n-j)]*locs[...,None,mpl_idx(-abs(m),n)]))
        for k in range(-j,1):   # Real coeffs!
            for n in range(j,p+1):
                for m in range(k+j-n,k+n-j+1):
                    new_locs = new_locs.at[...,mpl_idx(k,j)].set(new_locs[...,mpl_idx(k,j)] + (-1)**((abs(m)-abs(m-k)-abs(k))//2) * (
                                                  reg[...,mpl_idx(abs(m-k),n-j)]*locs[...,None,mpl_idx(-abs(m),n)] + 
                                                  jnp.sign(m-k)*jnp.sign(m)*reg[...,mpl_idx(-abs(m-k),n-j)]*locs[...,None,mpl_idx(abs(m),n)]))
    return new_locs.reshape((-1,new_locs.shape[-1]))

def gen_M2L_idcs(p):
    r"""
    Generate M2L shift indices and signs for a given expansion order p.
    """
    idcs = -2*jnp.ones(((p+1)**2, (p+1)**2, 2),dtype=jnp.int32)
    signs = jnp.zeros(idcs.shape)
    for j in range(p+1):
        for k in range(-j,1):  # real coeffs
            id2 = mpl_idx(k,j)
            for n in range(p+1):
                for m in range(max(k-j-n,-n),min(j+n+k,n)+1):
                    id1 = mpl_idx(abs(m),n)
                    pos = jnp.int32(idcs[id1,id2,0] != -2)
                    idcs = idcs.at[id1, id2, pos].set(mpl_idx(-abs(m-k),j+n))
                    signs = signs.at[id1, id2, pos].set((-1)**((abs(k-m)-abs(k)-abs(m))//2))

                    id1 = mpl_idx(-abs(m),n)
                    pos = jnp.int32(idcs[id1,id2,0] != -2)
                    idcs = idcs.at[id1, id2, pos].set(mpl_idx(abs(m-k),j+n))
                    signs = signs.at[id1, id2, pos].set(jnp.sign(m)* jnp.sign(m-k) * (-1)**((abs(k-m)-abs(k)-abs(m))//2))
        for k in range(1,j+1):  # negative imag coeffs
            id2 = mpl_idx(k,j)
            for n in range(p+1):
                for m in range(max(k-j-n,-n),min(j+n+k,n)+1):
                    id1 = mpl_idx(abs(m),n)
                    pos = jnp.int32(idcs[id1,id2,0] != -2)
                    idcs = idcs.at[id1, id2, pos].set(mpl_idx(abs(m-k),j+n))
                    signs = signs.at[id1, id2, pos].set(-jnp.sign(m-k) * (-1)**((abs(k-m)-abs(k)-abs(m))//2))

                    id1 = mpl_idx(-abs(m),n)
                    pos = jnp.int32(idcs[id1,id2,0] != -2)
                    idcs = idcs.at[id1, id2, pos].set(mpl_idx(-abs(m-k),j+n))
                    signs = signs.at[id1, id2, pos].set(jnp.sign(m) * (-1)**((abs(k-m)-abs(k)-abs(m))//2))
    return idcs, signs

@partial(jax.jit, static_argnames=['p'])
def M2L(mpls, locs, boxcenters, eval_boxcenters, mpl_cnct, M2L_idcs, M2L_sgns, p, img_cnct = jnp.array([[]])):
    r"""
    Multipole-to-local transformation, turning multipole expansions into local expansions on the same level. This is the O(p^4) algorithm proposed in the original 3D FMM paper.
    """
    if(img_cnct.shape[1] > 0): # both pbc images and real boxes, shift appropriately
        n_boxs = boxcenters.shape[0]
        ids = mpl_cnct%n_boxs
        sing = jnp.nan_to_num(eval_singular_basis(boxcenters[ids] + img_cnct.at[mpl_cnct//n_boxs].get(mode="fill",fill_value=jnp.nan) - eval_boxcenters[:,None,:],2*p))
    else:               # open boundary conditions
        ids = mpl_cnct
        sing = jnp.nan_to_num(eval_singular_basis(boxcenters.at[ids].get(mode="fill",fill_value=jnp.nan)-eval_boxcenters[:,None,:],2*p))    # shift direction points from target to source

    locs += jnp.einsum('ijklm,ijk,klm->il',sing[...,M2L_idcs],mpls.at[ids].get(mode="fill",fill_value=0),M2L_sgns,optimize='optimal')

    return locs

@partial(jax.jit, static_argnames=['p', 'n_split', 'n_l'])
def go_up(coeff, boxcenters, p, n_split, n_l):
    r"""
    Using multipole-to-multipole transformation, descend the hierarchy.
    """
    mpls = [coeff]
    for i in range(n_l,0,-1):
        mpls.append(M2M(mpls[-1],boxcenters[i],boxcenters[i-1], p, n_split))
    return mpls

@partial(jax.jit, static_argnames=['p', 'n_split','lvl_info'])
def go_down(mpls, locs, boxcenters, eval_boxcenters, mpl_cnct, M2L_idcs, M2L_sgns, lvl_info, img_cnct, p, n_split):
    r"""
    Using multipole-to-local and local-to-local transformation, ascend the hierarchy.
    """
    l_eval, _ = lvl_info[0]
    for j in range(0, l_eval):   # shift the PBC local expansion to the bottom level in the connectivity
        locs = L2L(locs, eval_boxcenters[j], eval_boxcenters[j+1], p, n_split)

    l_src_max = len(mpls) - 1
    for i in range(len(lvl_info) - 1):  # for every level pair in the connectivity
        l_eval, l_src = lvl_info[i]
        locs = M2L(mpls[l_src_max-l_src], locs, boxcenters[l_src], eval_boxcenters[l_eval], mpl_cnct[i], M2L_idcs, M2L_sgns, p, img_cnct)
        if(i < (len(lvl_info) - 2)):    # skip direct connectivity at the end
            for j in range(l_eval, lvl_info[i+1][0]):   # move on to the next eval level, shift multiple times if necessary
               locs = L2L(locs,eval_boxcenters[j],eval_boxcenters[j+1], p, n_split)
    return locs

@partial(jax.jit, static_argnames=['p', 'field'])
def eval_local(locs, padded_eval_pts, rev_idcs, boxcenters, p, field = False):
    r"""
    Evaluate local expansions on the highest level.
    """
    padded_res = jnp.zeros(padded_eval_pts.shape[:2+field])
    if(field):
        reg = eval_regular_basis_grad(padded_eval_pts - boxcenters[:,None], p)
        locs = locs[:,None,:,None]  # need additional newaxis for vector components
    else:
        reg = eval_regular_basis(padded_eval_pts - boxcenters[:,None],p)   # this evaluation needs to be relative to the boxcenter
        locs = locs[:,None,:]

    for n in range(p+1):
        for m in range(-n,n+1):
            if(m!=0):
                padded_res += (-1)**n * 2*locs[:,:,mpl_idx(-m,n)] * reg[:,:,mpl_idx(m,n)]
            else:
                padded_res += (-1)**n * locs[:,:,mpl_idx(-m,n)] * reg[:,:,mpl_idx(m,n)]

    if(field):
        return -padded_res.reshape((-1,3))[rev_idcs] / (4*jnp.pi)
    else:
        return padded_res.flatten()[rev_idcs] / (4*jnp.pi)

@partial(jax.jit, static_argnames=['field'])
def eval_direct(padded_pts, padded_chrgs, padded_eval_pts, rev_idcs, dir_cnct, img_cnct = jnp.array([[]]), field = False): # TODO: replace some of these evaluations with multipole evaluations for better performance
    r"""
    Evaluate the near-field potential directly (P2P).
    """
    if(dir_cnct.shape[1] == 0):   # nothing to compute
        return 0
    npts_eval = padded_eval_pts.shape[1]
    nboxs_eval = padded_eval_pts.shape[0]
    nboxs_src = padded_pts.shape[0]

    def i_body(i):
        acc = jnp.zeros((npts_eval,3) if field else (npts_eval,))
        xblk = padded_eval_pts[i]
        def k_body(k, acc):
            if(img_cnct.shape[1] == 0): # no PBC
                partner = dir_cnct[i,k]
                distsvec = xblk[:,None] - padded_pts[partner]
            else:   # PBC, shift image positions
                partner = dir_cnct[i,k]%nboxs_src
                distsvec = xblk[:,None] - padded_pts[partner] - img_cnct.at[dir_cnct[i,k]//nboxs_src].get(mode="fill",fill_value=jnp.inf)
            distsnorm = jnp.linalg.norm(distsvec,axis=-1)
            distsnorm = 1/jnp.where(distsnorm==0,jnp.inf,distsnorm)
            chunk = padded_chrgs.at[partner].get(mode="fill",fill_value=0.0)
            if(field):
                return acc + ((chunk[None,:]*(distsnorm**3))[...,None] * distsvec).sum(axis=1)
            else:
                return acc + distsnorm.dot(chunk)
        acc = jax.lax.fori_loop(0,dir_cnct.shape[1], k_body, acc)
        return acc

    accs = jax.vmap(i_body)(jnp.arange(nboxs_eval))
    if(field):
        return accs.reshape((-1,3))[rev_idcs]/(4*jnp.pi)
    else:
        return accs.flatten()[rev_idcs]/(4*jnp.pi)

def gen_hierarchy(pts, eval_pts = None, N_max = 128, theta = 0.77, n_split = 3, p = 3, periodic_axes = (), pbc_lvls = 5, pbc_no_monopole = True, L0_boxcen = None, L0_boxlen = None, no_cross_level = False, debug_info = False):
    r"""
    Generate the balanced tree and connectivity for the FMM.

    :param pts: Array of shape (N,3) containing the positions of N point charges.
    :type pts: jnp.array
    :param eval_pts, optional: Array of shape (N_eval,3) containing the positions of N evaluation points. Defaults to None, where eval_pts = pts.
    :type eval_pts: jnp.array
    :param N_max: Maximum allowed number of point charges per box.
    :type N_max: int, optional
    :param theta: Well-separatedness parameter, determines accuracy.
    :type theta: float, optional
    :param n_split: How many splits per level and box are been performed. Each box has 2^n_split children.
    :type n_split: int, optional
    :param p: Maximum expansion order.
    :type p: int, optional
    :param periodic_axes: Tuple indicating which dimensions (0, 1 and/or 2) are periodic.
    :type periodic_axes: tuple
    :param pbc_lvls: How many virtual levels are introduced in the hierarchy. If pbc_lvls < 0, only the non-well-separated boxes on level zero will be added.
    :type pbc_lvls: int
    :param pbc_no_monopole: Disable the contribution from distant monopoles for PBC. True by default, to negate possible errors introduced by almost zero total charge.
    :type pbc_no_monopole: bool
    :param L0_boxcen: Center of the source box at level zero, useful for periodic boundary conditions. The default (None) will generate the smallest possible axis-aligned box.
    :type L0_boxcen: jnp.array, optional
    :param L0_boxlen: Sidelengths of the source box at level zero, useful for periodic boundary conditions. The default (None) will generate the smallest possible axis-aligned box.
    :type L0_boxlen: jnp.array, optional
    :param no_cross_level: For pts = eval_pts, disable cross-level comparisons.
    :type no_cross_level: bool, optional
    :param debug_info: Whether to include further information in the hierarchy (boxlengths, PBC shifts).
    :type debug_info: bool, optional

    :return: Dictionary containing full hierarchy information.
    :rtype: dict
    """
    if(eval_pts is None):
        eval_pts = pts
    periodic = len(periodic_axes) > 0
    sz_eps = 1.01   # safety factor for checking if coordinates are inside level zero boxes
    
    max_l = get_max_l(pts.shape[0], N_max, n_split)
    eval_max_l = get_max_l(eval_pts.shape[0], N_max, n_split)
    idcs, rev_idcs, boxcenters, boxlens = balanced_tree(pts, max_l, n_split)

    old_boxcen, old_boxlen = boxcenters[0].copy(), boxlens[0].copy()
    if(L0_boxcen is not None):  # overwrite with specified value
        boxcenters[0] = L0_boxcen[None,:]
    if(L0_boxlen is not None):  # overwrite with specified value
        boxlens[0] = L0_boxlen[None,:]
    if(jnp.any((old_boxcen[0] - old_boxlen[0]/2 - boxcenters[0]) < -sz_eps*boxlens[0]/2) or jnp.any((old_boxcen[0] + old_boxlen[0]/2 - boxcenters[0]) > sz_eps*boxlens[0]/2)):
        raise ValueError("Level zero box does not contain all source points.")

    if(pts is eval_pts):
        eval_idcs, eval_boxcenters, eval_boxlens = idcs, boxcenters, boxlens
    else:
        no_cross_level = False  # we must deal with cross-level contributions
        eval_idcs, _, eval_boxcenters, eval_boxlens = balanced_tree(eval_pts, eval_max_l, n_split)

        if(periodic):
            if(jnp.any((eval_boxcenters[0] - eval_boxlens[0]/2 - boxcenters[0]) < -sz_eps*boxlens[0]/2) or jnp.any((eval_boxcenters[0] + eval_boxlens[0]/2 - boxcenters[0]) > sz_eps*boxlens[0]/2)):
                raise ValueError("All evaluation points must be contained in the level zero source box for PBC.")
            eval_boxcenters[0], eval_boxlens[0] = boxcenters[0], boxlens[0]  # for PBC, we need identical level zero boxes

    mpl_cnct, dir_cnct, lvl_info, img_cnct = gen_connectivity(boxcenters, boxlens, eval_boxcenters, eval_boxlens, theta, n_split, no_cross_level, periodic_axes)

    ### we adapt the sorting idcs to the "true" max levels - the if statements prevent unnecessary work
    only_dir = (len(lvl_info) == 1)
    idcs_list = [(idcs, rev_idcs) if only_dir else reduce_max_lvl(pts,idcs,n_split,max_l,lvl_info[-2][1])] # src padding at max mpl level

    if(only_dir or (pts is eval_pts and lvl_info[-2][0]==lvl_info[-2][1])):   # eval padding at max mpl level
        idcs_list.append(idcs_list[0])
    else:
        idcs_list.append(reduce_max_lvl(eval_pts,eval_idcs,n_split,eval_max_l,lvl_info[-2][0]))

    if(only_dir or (lvl_info[-2][1]==lvl_info[-1][1])):                       # src padding at max dir level
        idcs_list.append(idcs_list[0])
    else:
        idcs_list.append(reduce_max_lvl(pts,idcs,n_split,max_l,lvl_info[-1][1]))

    if(only_dir or (lvl_info[-2][0]==lvl_info[-1][0])):                       # eval padding at max dir level
        idcs_list.append(idcs_list[1])
    elif(pts is eval_pts and lvl_info[-1][0]==lvl_info[-1][1]):
        idcs_list.append(idcs_list[2])
    else:
        idcs_list.append(reduce_max_lvl(eval_pts,eval_idcs,n_split,eval_max_l,lvl_info[-1][0]))
    # idcs_list[0][1], idcs_list[2][1] = None, None   # TODO: we do not need these rev idcs, remove them!

    if(periodic):
        PBC_op, pbc_ws = gen_pbc_op(boxlens[0], theta, periodic_axes, p, pbc_lvls, pbc_no_monopole)
        if(pbc_lvls < 0): # optionally, only add non-ws boxes on level 0
            PBC_op = jnp.zeros(((p+1)**2,(p+1)**2))
        if(len(periodic_axes)==3 and not jnp.all(jnp.isclose(boxlens[0],boxlens[0][0,0]))):
            raise ValueError("3D PBC are currently only supported for cubic level zero boxes. You can manually set the dimensions of the level zero box by specifying L0_boxcen and L0_boxlen.")
    else:   # for open boundary conditions, we get no local expansion on level 0
        PBC_op = jnp.zeros(((p+1)**2,(p+1)**2))
        pbc_ws = []

    M2L_idcs, M2L_sgns = gen_M2L_idcs(p)

    hierarchy = {"pts": pts,
                 "eval_pts": eval_pts,
                 "idcs": idcs_list,
                 "boxcenters": boxcenters,
                 "eval_boxcenters": eval_boxcenters,
                 "mpl_cnct": mpl_cnct,
                 "dir_cnct": dir_cnct,
                 "M2L_idcs": M2L_idcs, "M2L_sgns": M2L_sgns,
                 "lvl_info": lvl_info,
                 "img_cnct": img_cnct,
                 "n_split": n_split,
                 "p": p,
                 "theta": theta,
                 "periodic_axes": periodic_axes,
                 "pbc_lvls": pbc_lvls if periodic else 0,
                 "pbc_no_monopole": pbc_no_monopole,
                 "PBC_op": PBC_op
                }
    if(debug_info):
        hierarchy["boxlens"] = boxlens
        hierarchy["eval_boxlens"] = eval_boxlens
        hierarchy["pbc_ws"] = pbc_ws
    return hierarchy

@jax.jit
def handle_padding(pts, chrgs, eval_pts, idcs):
    r"""
    Generate the padded arrays required for computing the potential.
    """
    padded_pts = pts.at[idcs[0][0]].get(mode="fill",fill_value=0.0)   # TODO: we could buffer these arrays if desired...
    padded_chrgs = chrgs.at[idcs[0][0]].get(mode="fill",fill_value=0.0)  
    loc_padded_eval_pts = padded_pts if idcs[1] is idcs[0] else eval_pts.at[idcs[1][0]].get(mode="fill",fill_value=0.0)
    dir_padded_pts = padded_pts if idcs[2] is idcs[0] else pts.at[idcs[2][0]].get(mode="fill",fill_value=0.0)
    dir_padded_chrgs = padded_chrgs if idcs[2] is idcs[0] else chrgs.at[idcs[2][0]].get(mode="fill",fill_value=0.0)
    if(idcs[3] is idcs[2]):
        dir_padded_eval_pts = dir_padded_pts
    elif(idcs[3] is idcs[1]): 
        dir_padded_eval_pts = loc_padded_eval_pts
    else:
        dir_padded_eval_pts = eval_pts.at[idcs[3][0]].get(mode="fill",fill_value=0.0)
    return padded_pts, padded_chrgs, loc_padded_eval_pts, dir_padded_pts, dir_padded_chrgs, dir_padded_eval_pts

@partial(jax.jit, static_argnames=['p', 'n_split', 'field', 'lvl_info'])
def eval_potential(chrgs, pts, eval_pts, idcs, boxcenters, eval_boxcenters, mpl_cnct, dir_cnct, M2L_idcs, M2L_sgns, lvl_info, img_cnct, n_split, PBC_op, p, field = False, **kwargs):
    r"""
    Full FMM potential evaluation, does not include creation of the hierarchy (see gen_hierarchy, which generates a dict containing all parameters apart from chrgs and field). Only chrgs, field (and p for open boundaries) can be changed without recomputing the hierarchy.

    :param chrgs: Array containing point charges.
    :type chrgs: jnp.array
    :param pts: Array containing point positions.
    :type pts: jnp.array
    :param eval_pts, optional: Array of shape (N_eval,3) containing the positions of N evaluation points. Defaults to None, where eval_pts = pts.
    :type eval_pts: jnp.array
    :param idcs: Index array to sort points/charges into highest level of the hierarchy.
    :type idcs: jnp.array
    :param boxcenters: List containing source box center arrays for every level.
    :type boxcenters: list(jnp.array)
    :param eval_boxcenters: List containing evaluation box center arrays for every level.
    :type eval_boxcenters: list(jnp.array)
    :param mpl_cnct: List of interaction partner index arrays on every level.
    :type mpl_cnct: list(jnp.array)
    :param dir_cnct: Index array of interaction partners for each box on the highest level.
    :type dir_cnct: jnp.array
    :param M2L_idcs: Array of M2L shift indices.
    :type M2L_idcs: jnp.array
    :param M2L_sgns: Array of M2L shift signs.
    :type M2L_sgns: jnp.array
    :param lvl_info: Tuple containing source and eval level pairs for the connectivity.
    :type lvl_info: tuple(tuple(int,int))
    :param img_cnct: PBC image connectivity information.
    :type img_cnct: jnp.array
    :param n_split: How many splits per level and box have been performed. Each box has 2^n_split children.
    :type n_split: int
    :param PBC_op: PBC operator matrix applied to the multipoles at level zero to obtain the local expansion on level zero.
    :type PBC_op: jnp.array
    :param p: Multipole expansion order.
    :type p: int, optional
    :param field: Optionally evaluate the field instead of the potential.
    :type field: bool, optional

    :return: Electrostatic potential (or field) of the points and corresponding charges.
    :rtype: jnp.array
    """
    if(len(lvl_info) == 1): # only direct interactions - compute potential directly
        return eval_potential_direct(pts,chrgs,eval_pts,field)

    pad_arr = handle_padding(pts, chrgs, eval_pts, idcs)
    coeff = get_initial_mpls(pad_arr[0], pad_arr[1], boxcenters[lvl_info[-2][1]], p)
    mpls = go_up(coeff, boxcenters, p, n_split, lvl_info[-2][1])
    locs = (PBC_op@mpls[-1][0])[None,:]    # PBC_op is 0 for open boundary conditions
    locs = go_down(mpls, locs, boxcenters, eval_boxcenters, mpl_cnct, M2L_idcs, M2L_sgns,lvl_info, img_cnct, p, n_split)

    return eval_local(locs, pad_arr[2], idcs[1][1], eval_boxcenters[lvl_info[-2][0]], p, field = field) + eval_direct(pad_arr[3], pad_arr[4], pad_arr[5], idcs[3][1], dir_cnct, img_cnct, field = field)

@partial(jax.jit, static_argnames=['field'])
def eval_potential_direct(pts, chrgs, eval_pts = None, field = False):
    r"""
    Evaluate the potential directly via pairwise sums.

    :param pts: Array containing point positions.
    :type padded_pts: jnp.array
    :param chrgs: Array containing point charges.
    :type chrgs: jnp.array
    :param eval_pts: Array containing points to evaluate the potential at. Defaults to pts.
    :type eval_pts: jnp.array, optional
    :param field: Optionally evaluate the field (negative gradient) instead of the potential.
    :type field: bool, optional

    :return: Electrostatic potential (or field) of the points and corresponding charges.
    :rtype: jnp.array
    """
    if(eval_pts is None):
        eval_pts = pts
    res = jnp.zeros(eval_pts.shape[:field+1])
    def eval_direct_body(i, val):
        distsvec = pts[:,:] - eval_pts[i,None,:]
        inv_dists = jnp.linalg.norm(distsvec,axis=-1)
        inv_dists = 1/jnp.where(inv_dists==0,jnp.inf,inv_dists) # take out self-interaction
        if(field):
            val = val.at[i].set(-((chrgs * inv_dists**3)[:,None] * distsvec).sum(axis=0))
        else:
            val = val.at[i].set((chrgs * inv_dists).sum())
        return val
    return jax.lax.fori_loop(0,eval_pts.shape[0],eval_direct_body,res)/(4*jnp.pi)