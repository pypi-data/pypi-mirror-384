def single_iter_lie(eta, h,vector_field,z):
    import numpy as np
    import sympy as sp

    # The list that will contain all the Lie derivatives is initiated. 
    LT = sp.Matrix([h])
    
    for i in eta:
        
        LT = LT.jacobian(z)*vector_field[:,i]
    return LT
