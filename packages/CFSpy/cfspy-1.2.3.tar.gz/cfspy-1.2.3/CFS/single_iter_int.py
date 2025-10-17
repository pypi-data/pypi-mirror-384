# Individual iterative integral
def single_iter_int(eta, u, t0, tf, dt):
    import numpy as np
    
    # The length of the partition of time is computed
    length_t = int((tf-t0)//dt+1)
    # The sequence of numbers that represent the partition of the time domain of the input is generated.
    # This is used to discretize the integrals.
    t = np.linspace(t0, tf, length_t)
    # The input u_0 associated with the letter x_0 is generated.
    u0 = np.ones(length_t)
    # The inputs of the system associated with x_1, ..., x_m with the input associated to x_0 vertically are stacked.
    # [
    #  [u_0(t0), u_0(t0+dt), ..., u_0(tf)],
    #  [u_1(t0), u_1(t0+dt), ..., u_1(tf)],
    #    .
    #    .
    #    .
    #  [u_m(t0), u_m(t0+dt), ..., u_m(tf)]
    # ]
    u = np.vstack([u0, u])
    temp = 1
    for i in np.flip(eta):
        temp = temp * u[i]
        temp = np.append(0,np.cumsum(temp)*delta)
        temp = temp[:-1]

    return temp
