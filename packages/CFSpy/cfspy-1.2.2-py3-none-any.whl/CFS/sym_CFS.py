def sym_CFS(u, t, Ntrunc, Ceta=None):
    import numpy as np
    import sympy as sp
    from CFS.pol_inputs import pol_inputs

    # Create dynamic substitution: {u[i]: t for all u's in the list}
    substitution = {ui: t for ui in u}
    
    # Call pol_inputs with `u` and `Ntrunc` (assuming it accepts arbitrary-length `u`)
    T = pol_inputs(u, Ntrunc).subs(substitution)
    
    # Compute derivatives
    T_derivative = T.diff(t)
    T_derivative_at_1 = T_derivative.subs(t, 1)
    
    # Invert derivative values (1/x where x != 0, else return oo for zero values)
    T_derivative_inverted = T_derivative_at_1.applyfunc(lambda x: 1/x if x != 0 else sp.oo)
    
    # Elementwise product of T_derivative_inverted and T
    T_elementwise_product = sp.Matrix.multiply_elementwise(T_derivative_inverted, T)
    
    # Elementwise product of the result with pol_inputs(u, Ntrunc)
    T_elementwise_productU = sp.Matrix.multiply_elementwise(T_elementwise_product, pol_inputs(u, Ntrunc))
    
    # Apply Ceta if provided (optional). If Ceta is provided, multiply elementwise with T_elementwise_productU.
    if Ceta is not None:
        num_inputs = u.shape[0]
        total_monomials = num_inputs*(1-pow(num_inputs, Ntrunc))/(1-num_inputs)
        total_monomials = int(total_monomials)
        
        if Ceta.shape[0] == total_monomials:
            # Ensure Ceta is the correct size and shape before multiplying
            Ceta_matrix = sp.Matrix(Ceta)
            T_elementwise_productU = sp.Matrix.multiply_elementwise(T_elementwise_productU, Ceta_matrix)

        else:
            raise ValueError("Ceta does not have the correct size.")

    
    return T_elementwise_productU