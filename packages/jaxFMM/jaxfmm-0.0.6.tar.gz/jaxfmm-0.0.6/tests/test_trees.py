import jax.numpy as jnp
import jaxfmm.fmm as fmm

### TODO:
#   - find better tests

def test_tree_connectivity_unitcube():
    nside, sidelen = 64, 10.0
    pts = (jnp.mgrid[:nside,:nside,:nside].T/(nside-1) * sidelen - sidelen/2).reshape((-1,3))

    max_l = fmm.get_max_l(pts.shape[0], 128)
    assert max_l==4

    idcs, rev_idcs, boxcenters, boxlens = fmm.balanced_tree(pts,max_l)
    assert idcs.shape[1]==64
    assert jnp.all(idcs < pts.shape[0])
    assert jnp.allclose(pts, pts[idcs].reshape((-1,3))[rev_idcs])
    for i in range(len(boxlens)):
        assert jnp.allclose(boxlens[i], pts[nside//(2**i)-1,0] - pts[0,0])

    mpl_cnct, dir_cnct, _, _ = fmm.gen_connectivity(boxcenters, boxlens,boxcenters,boxlens,no_cross_level=True)

    assert (mpl_cnct[-1]<mpl_cnct[-1].shape[0]).sum() == 611136
    assert (dir_cnct<dir_cnct.shape[0]).sum() == 70336