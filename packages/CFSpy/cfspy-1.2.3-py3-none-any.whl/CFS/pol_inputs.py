# Function that provides the list of symbolic monomials equal to the interated integrals with constant input
def pol_inputs(u, Ntrunc):
    import numpy as np
    import sympy as sp

    """
    Returns the list of all the symbolic monomials equal to the iterated integrals indexed by the words of length 
    from 1 to Ntrunc given constant inputs.
    
    
    Parameters:
    -----------
    u: symbolic array
        The domain of the vector fields.
        u = sp.Matrix([u0, u2, ...., um]), or
        u = sp.symbols('u0:m') which generates the symbols u0, u1, ..., um
    
    Ntrunc: int
        The truncation length of the words index of the iterated integrals
    
    
    
    Returns:
    --------
    list: symbolic array
    
    [
    u0
     .
     .
     .
    um
    ---------------
    u0*u0
    u0*u1
     .
     .
     .
    um*um
    ---------------
     .
     .
     .
    ---------------
    u0...u0
     .
     .
     .
    um...um
    ]
    
    
    
    """
        
    if u is None:
        raise ValueError("The argument of the input of the system, %s, cannot be null" %u)
    
    if Ntrunc < 1:
        raise ValueError("The truncation length, %s, must be non-negative." %Ntrunc)
    
    if not isinstance(Ntrunc, int):
        raise ValueError("The truncation length, %s, must be an integer." %Ntrunc)
    
    
    # The number of inputs is obtained.
    # num_inputs = m
    num_inputs = np.size(u,0)
    
    
    # The total number of monomials indexed by words of length less than or equal to the truncation length is computed.
    # total_monomials = num_input + num_input**2 + ... + num_input**Ntrunc
    total_monomials = num_inputs*(1-pow(num_inputs, Ntrunc))/(1-num_inputs)
    total_monomials = int(total_monomials)
    
    
    # The list that will contain all the monomials is initiated. 
    Ltemp = sp.Matrix(np.zeros((total_monomials, 1), dtype='object'))
    ctrLtemp = np.zeros((Ntrunc+1,1), dtype = 'int')
    
    
    # ctrLtemp[k] = num_input + num_input**2 + ... + num_input**k,  1<=k<=Ntrunc
    for i in range(Ntrunc):
        ctrLtemp[i+1] = ctrLtemp[i] + num_inputs**(i+1)
    
    
    # The Lie derivative L_eta h(z) of words eta of length 1 are computed 
    LT = u

    # Transforms the input vector from a row vector to a column vector
    LT = LT.reshape(LT.shape[0]*LT.shape[1], 1)
    
    # Starts the list of inputs and stores them in a repository
    Ltemp[:num_inputs, 0] = LT

    
    # The monomials of the words of length k => 1, ui_0...ui_k for all i_j in {0, ..., m}, 
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
         [u0...u0u0],
         [u0...u1u0],
                .
                .
                .
         [um...um],
        ]
        these are the monomials indexed by words of length i
        """
        
        # Generates the sequence of index where each element repeats num_prev_block times
        # np.repeat(range(3), 2) = [0 0 1 1 2 2]
        pattern = np.repeat(range(num_inputs), num_prev_block)

        # Generate the vector of inputs by selecting the inputs according to the index sequence pattern 
        U_vector = sp.Matrix([u[i] for i in pattern])
        
        
        """
        U_vector = 
        [
         u0
         u0
         .
         .        num_prev_block
         .
         u0
         --
         u1
         u1
         .
         .        num_prev_block
         .
         u1
         --
         .
         .
         .
         --
         um
         um
         .
         .        num_prev_block
         .
         um
        ]
        
        """
        
        # Generates a vector by stacking the LT block num_inputs times
        stacked_block = sp.Matrix.vstack(*[LT for _ in range(num_inputs)])

        
        
        """
        stacked_block =
        [
            u0u0...u0 
            u1u0...u0 
            u2u0...u0 
                .                
                .                
                .                
            umu0...u0 
            ------------------------
            u0u0...u1u0 
            u1u0...u1u0 
            u2u0...u1u0 
                .                
                .                
                .                
            umu0...u1u0
            ------------------------
                .
                .
                .
            ------------------------
            u0um...um 
            u1um...um 
            u2um...um 
                .                
                .                
                .                
            umum...um 
        ]
        these are the monomials indexed by words of length i+1
        """
        LT = sp.Matrix([stacked_block[i] * U_vector[i] for i in range(stacked_block.rows)])
        # Adds the computed monomials to the repository
        Ltemp[end_prev_block:end_current_block,:]=LT

    return Ltemp
