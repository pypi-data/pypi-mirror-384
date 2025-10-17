import jax.numpy as jnp
import jaxfmm.fmm as fmm
from jax import random

### TODO:
#   - find similar tests for L2L, M2L
 
def test_M2M():
    key = random.key(825)
    pts = random.uniform(key,(8*128,3),minval=-1,maxval=1)
    chrgs = random.uniform(key,8*128,minval=-1,maxval=1)

    tree_info = fmm.gen_hierarchy(pts)
    padded_pts = pts.at[tree_info["idcs"][0][0]].get(mode="fill",fill_value=0.0)
    padded_chrgs = chrgs.at[tree_info["idcs"][0][0]].get(mode="fill",fill_value=0.0)

    coeff = fmm.get_initial_mpls(padded_pts,padded_chrgs,tree_info["boxcenters"][1],10)
    coeff_merged = fmm.M2M(coeff,tree_info["boxcenters"][1], tree_info["boxcenters"][0], 10, 3)[0,:]
    coeff_dir = fmm.get_initial_mpls(pts,chrgs,tree_info["boxcenters"][0],10)[0,:]

    assert jnp.allclose(coeff_merged, coeff_dir, rtol=1e-3, atol=1e-6)