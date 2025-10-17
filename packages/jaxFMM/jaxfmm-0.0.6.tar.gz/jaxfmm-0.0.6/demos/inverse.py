import jax.numpy as jnp
from jax.scipy.optimize import minimize
from jaxfmm import *

print("Assembling grid of charges.")
nside, sidelen = 15, 4*jnp.pi
pts = (jnp.mgrid[:nside,:nside,:nside].T/(nside-1) * sidelen - sidelen/2).reshape((-1,3))
chrgs = 0.01*jnp.ones(pts.shape[0])

print("Generating hierarchy.")
tree_info = gen_hierarchy(pts)

print("Computing desired potential.")
desired_pot = jnp.sin(jnp.linalg.norm(pts,axis=-1))
norm = jnp.linalg.norm(desired_pot)

def loss(chrgs):
    return jnp.linalg.norm(desired_pot-eval_potential(chrgs, **tree_info))/norm

print("Initial loss: %.2e"%loss(chrgs))
print("Compiling + running minimizer.")
res = minimize(loss,chrgs,method="BFGS",options={"maxiter": 1000})
print("Final loss (%i iterations): %.2e"%(res.nit,res.fun))