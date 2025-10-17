import jax.numpy as jnp
from jaxfmm import *
from jax import random
import pytest

### TODO:
# - check if the FMM error scaling roughly works out

@pytest.mark.parametrize("eval_pts", [None, random.uniform(random.key(156),(2**12,3),minval=0.66,maxval=1.33)])
def test_potential_unitcube(eval_pts):
    N = 2**15
    key = random.key(856)
    pts = random.uniform(key,(N,3))
    chrgs = random.uniform(key,N,minval=-1,maxval=1)

    tree_info = gen_hierarchy(pts,eval_pts)
    pot_FMM = eval_potential(chrgs, **tree_info)

    pot_dir = eval_potential_direct(pts,chrgs,eval_pts)

    err = jnp.linalg.norm(pot_dir-pot_FMM)/jnp.linalg.norm(pot_dir)
    assert err < 4e-3

@pytest.mark.parametrize("eval_pts", [None, random.uniform(random.key(156),(2**12,3),minval=0.66,maxval=1.33)])
def test_field_unitcube(eval_pts):
    N = 2**15
    key = random.key(856)
    pts = random.uniform(key,(N,3))
    chrgs = random.uniform(key,N,minval=-1,maxval=1)

    tree_info = gen_hierarchy(pts, eval_pts)
    field_FMM = eval_potential(chrgs, field=True, **tree_info)

    field_dir = eval_potential_direct(pts,chrgs,eval_pts, field=True)

    err = jnp.linalg.norm(field_dir-field_FMM)/jnp.linalg.norm(field_dir)
    assert err < 6e-3