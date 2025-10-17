import jax.numpy as jnp
import jaxfmm.fmm as fmm
import jaxfmm.debug_helpers as debug
from jax import random

### TODO:
#   - find similar tests for local coeffs and expansions

def test_mpl_coeffs():  # TODO: also check for correct normalization
    for n in range(9):
        for m in range(-n,n+1):
            pts, chrgs = debug.gen_multipole_dist(m,n,eps=10.0)    # special point charge distribution corresponding to multipole moments - set eps large to minimize error
            tree_info = fmm.gen_hierarchy(pts)
            coeff = fmm.get_initial_mpls(pts,chrgs,tree_info["boxcenters"][0],n)[0,:]
            test = jnp.where(jnp.abs(coeff)>1e-5)[0]   # only the (m,n) coefficient should be nonzero
            assert test.shape[0] == 1
            assert test[0] == fmm.mpl_idx(m,n)

def test_mpl_eval():  # TODO: do a better test, maybe independent from computing coeffs (related to the above todo)
    key = random.key(743)
    pts = random.uniform(key,(128,3),minval=-1,maxval=1)
    chrgs = random.uniform(key,128,minval=-1,maxval=1)

    tree_info = fmm.gen_hierarchy(pts)
    coeff = fmm.get_initial_mpls(pts,chrgs,tree_info["boxcenters"][0],10)[0,:]

    nside, sidelen = 100, 10
    eval_pts = (jnp.mgrid[:nside+1,:nside+1,:nside+1].T/nside * sidelen - sidelen/2).reshape((-1,3))
    eval_pts = eval_pts[jnp.linalg.norm(eval_pts,axis=-1)>2*jnp.sqrt(3)]

    pot_fmm = debug.eval_multipole(coeff, tree_info["boxcenters"][0], eval_pts)
    pot_dir = fmm.eval_potential_direct(pts,chrgs,eval_pts)
    max_err = jnp.max(jnp.abs(pot_fmm-pot_dir))
    assert max_err < 5.75e-6