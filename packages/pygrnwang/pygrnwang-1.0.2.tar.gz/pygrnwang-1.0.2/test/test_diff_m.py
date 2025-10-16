import sympy as sp

# 定义符号
r, k, m = sp.symbols('r k m')
Jm = sp.besselj(m, k*r)

# 求导
dJm_dr = sp.diff(m**2 * Jm, r)
print(sp.simplify(dJm_dr))