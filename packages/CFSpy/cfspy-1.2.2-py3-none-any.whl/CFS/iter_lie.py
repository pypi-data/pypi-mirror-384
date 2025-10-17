# Function that provides the iterative Lie derivatives
def iter_lie(h,vector_field,z,Ntrunc):
    import numpy as np
    import sympy as sp

    """
    Returns the list of all the Lie derivatives indexed by the words of length from 1 to Ntrunc
    Given the system 
        dot{z} = g_0(z) + sum_{i=1}^m g_i(z) u_i(t), 
        y = h(z)
    with g_i: S -> IR^n and h: S -> IR, S is a subset of IR^n for all i in {0, ..., n}
    The Lie derivative L_eta h of the output function h(z) indexed by the word 
    eta = x_{i_1}x_{i_2}...x_{i_k} is defined recursively as
        L_eta h = L_(x_{i_2}...x_{i_k}) (partial/partial z h) cdot g_{i_1} 
    
    
    
    Parameters:
    -----------
    h: symbolic
        The symbolic function that represents the output of the system.
    
    vector_field: symbolic array
        The array that contains the vector fields of the system.
        vector_field = 
            sp.transpose(sp.Matrix([[(g_0)_1, ..., (g_0)_n],[(g_1)_1, ..., (g_1)_n], ..., [(g_m)_1, ..., (g_m)_n]]))
    
    z: symbolic array
        The domain of the vector fields.
        z = sp.Matrix([z1, z2, ...., zn])
    
    Ntrunc: int
        The truncation length of the words index of the Lie derivatives
    
    
    
    Returns:
    --------
    list: symbolic array
    
    [
    L_{x_0} h
     .
     .
     .
    L_{x_m} h
    ---------------
    L_{x_0x_0} h
     .
     .
     .
    L_{x_mx_m} h
    ---------------
     .
     .
     .
    ---------------
    L_{x_0...x_0} h
     .
     .
     .
    L_{x_m...x_m} h
    ]
    
    
    
    Examples:
    ---------
    
    # Consider the system:
    # dx1 = -x1*x2 +  x1 * u1
    # dx2 = x1*x2 - x2* u2
    
    # Define the state of the system:
    x1, x2 = sp.symbols('x1 x2')
    x = sp.Matrix([x1, x2])

    # h is a real value function representing the output.
    h = x1

    # each column of g = [[g10, g11, g12, ..., g1m], [g20, g21, g22, ..., g2m], ..., [gn1, gn2, gn3, ..., gnm]]
    # is a vector field where xdot = g0 + g_1*u_1 + g_2*u_2 +...+ g_m*u_m
    # g0 = transpose([g10, g20, ...., gn0])
    # g_1 = transpose([g11, g21, ...., gn1])
    # g_2 = transpose([g12, g22, ...., gn2])
    #                .
    #                .
    #                .
    # g_m = transpose([g0m, g1m, ...., gnm])

    # Define the vector field
    g = sp.transpose(sp.Matrix([[-x1*x2, x1*x2], [x1, 0], [0, - x2]]))

    # Ntrunc is the maximum length of words
    Ntrunc = 4

    Ceta = np.array(iter_lie(h,g,x,Ntrunc).subs([(x[0], 1/6),(x[1], 1/6)]))
    Ceta
    
    
    """
    
    if h is None:
        raise ValueError("The output function, %s , cannot be null" %h)
        
    if vector_field is None:
        raise ValueError("The vector_field, %s, cannot be null" %vector_field)
        
    if z is None:
        raise ValueError("The argument of output function and the vector field, %s, cannot be null" %z)
    
    if Ntrunc < 1:
        raise ValueError("The truncation length, %s, must be non-negative." %Ntrunc)
    
    if not isinstance(Ntrunc, int):
        raise ValueError("The truncation length, %s, must be an integer." %Ntrunc)
    
    
    # The number of vector fields is obtained.
    # num_vfield = m
    num_vfield = np.size(vector_field,1)
    
    
    # The total number of Lie derivatives of word length less than or equal to the truncation length is computed.
    # total_lderiv = num_input + num_input**2 + ... + num_input**Ntrunc
    total_lderiv = num_vfield*(1-pow(num_vfield, Ntrunc))/(1-num_vfield)
    total_lderiv = int(total_lderiv)
    
    
    # The list that will contain all the Lie derivatives is initiated. 
    Ltemp = sp.Matrix(np.zeros((total_lderiv, 1), dtype='object'))
    ctrLtemp = np.zeros((Ntrunc+1,1), dtype = 'int')
    
    
    # ctrLtemp[k] = num_input + num_input**2 + ... + num_input**k,  1<=k<=Ntrunc
    for i in range(Ntrunc):
        ctrLtemp[i+1] = ctrLtemp[i] + num_vfield**(i+1)
    
    
    # The Lie derivative L_eta h(z) of words eta of length 1 are computed 
    LT = sp.Matrix([h]).jacobian(z)*vector_field

    # Transforms the lie derivative from a row vector to a column vector
    LT = LT.reshape(LT.shape[0]*LT.shape[1], 1)
    
    # Adds the computed Lie derivatives to a repository
    Ltemp[:num_vfield, 0] = LT

    
    # The Lie derivatives of the words of length k => 1, L_{x_{i_1}...x_{i_k}}h(z) for all i_j in {0, ..., m}, 
    # are computed at each iteration.
    
    for i in range(1, Ntrunc):
        # start_prev_block = num_input + num_input**2 + ... + num_input**(i-1)
        start_prev_block = int(ctrLtemp[i-1])
        # end_prev_block = num_input + num_input**2 + ... + num_input**i
        end_prev_block = int(ctrLtemp[i])
        # end_current_block = num_input + num_input**2 + ... + num_input**(i+1)
        end_current_block = int(ctrLtemp[i+1])
        # num_prev_block = num_input**i
        num_prev_block = end_prev_block - start_prev_block
        # num_current_block = num_input**(i+1)
        num_current_block = end_current_block - end_prev_block
    
        """
        LT = 
        [
         [L_{x_0...x_0x_0}h(z)],
         [L_{x_0...x_1x_0}h(z)],
                .
                .
                .
         [L_{x_m...x_m}h(z)],
        ]
        these are the Lie derivatives indexed by words of length i
        """
        LT = Ltemp[start_prev_block:end_prev_block,0]
        
        """
        LT = 
        [
         [partial/ partial z L_{x_0...x_0x_0}h(z)],
         [partial/ partial z L_{x_0...x_1x_0}h(z)],
                .
                .
                .
         [partial/ partial z L_{x_m...x_m}h(z)],
        ]
        * 
        [g_0, g_1, ..., g_m]
        
        =
        
        [
            L_{x_0x_0...x_0}h(z)    |   L_{x_0x_0..x_0x_1x_0}h(z)   |          |  L_{x_0x_m..x_mx_m}h(z)
            L_{x_1x_0...x_0}h(z)    |   L_{x_1x_0..x_0x_1x_0}h(z)   |          |  L_{x_1x_m..x_mx_m}h(z)
            L_{x_2x_0...x_0}h(z)    |   L_{x_2x_0..x_0x_1x_0}h(z)   |          |  L_{x_2x_m..x_mx_m}h(z)
                .                   |        .                      |    ...   |       .
                .                   |        .                      |    ...   |       .
                .                   |        .                      |    ...   |       .
            L_{x_mx_0...x_0}h(z)    |   L_{x_mx_0..x_0x_1x_0}h(z)   |          |  L_{x_mx_m..x_mx_m}h(z)
        ]
        
        """
        LT = LT.jacobian(z)*vector_field
        # Transforms the lie derivative from a row vector to a column vector
        
        """
        LT =
        [
            L_{x_0x_0...x_0}h(z) 
            L_{x_1x_0...x_0}h(z) 
            L_{x_2x_0...x_0}h(z) 
                .                
                .                
                .                
            L_{x_mx_0...x_0}h(z) 
            ------------------------
            L_{x_0x_0...x_1x_0}h(z) 
            L_{x_1x_0...x_1x_0}h(z) 
            L_{x_2x_0...x_1x_0}h(z) 
                .                
                .                
                .                
            L_{x_mx_0...x_1x_0}h(z)
            ------------------------
                .
                .
                .
            ------------------------
            L_{x_0x_m...x_m}h(z) 
            L_{x_1x_m...x_m}h(z) 
            L_{x_2x_m...x_m}h(z) 
                .                
                .                
                .                
            L_{x_mx_m...x_m}h(z) 
        ]
        these are the Lie derivatives indexed by words of length i+1
        """
        LT = LT.reshape(LT.shape[0]*LT.shape[1], 1)
        # Adds the computed Lie derivatives to the repository
        Ltemp[end_prev_block:end_current_block,:]=LT

    return Ltemp


