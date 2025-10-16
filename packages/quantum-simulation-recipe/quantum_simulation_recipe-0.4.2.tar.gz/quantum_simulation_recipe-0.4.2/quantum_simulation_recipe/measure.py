import numpy as np
from jax.scipy.linalg import expm
import jax.numpy as jnp
from scipy.sparse import csr_matrix, csc_matrix

# from quantum_simulation_recipe.bounds import *
# from quantum_simulation_recipe.trotter import pf
# pf_r = pf

def commutator(A, B):
    return A @ B - B @ A

# def anticommutator(A, B, to_sparse=False):
def anticommutator(A, B):
    return A @ B + B @ A

def norm(A, ord='spectral'):
    if ord == 'fro':
        return np.linalg.norm(A)
    elif ord == 'spectral':
        return np.linalg.norm(A, ord=2)
    elif ord == '4':
        return np.trace(A @ A.conj().T @ A @ A.conj().T)**(1/4)
    else:
        # raise ValueError('norm is not defined')
        return np.linalg.norm(A, ord=ord)

# def measure_error(r, h_list, t, exact_U, type, rand_states=[], ob=None, pf_ord=2, coeffs=[], use_jax=False, verbose=False, return_error_list=False): 
#     # print(type)
#     if type == 'worst_empirical':
#         return 2 * np.linalg.norm(exact_U - pf_r(h_list, t, r, order=pf_ord, use_jax=use_jax), ord=2)
#     elif type == 'worst_bound':
#         if coeffs != []:
#             return 2 * tight_bound(h_list, 2, t, r) * coeffs[0]
#         else:
#             return 2 * tight_bound(h_list, 2, t, r)
#     elif type == 'worst_ob_empirical':
#         appro_U = pf_r(h_list, t, r, order=pf_ord, use_jax=use_jax)
#         # appro_U = pf_r(h_list, t, r, order=pf_ord)
#         exact_ob = exact_U.conj().T @ ob @ exact_U 
#         appro_ob = appro_U.conj().T @ ob @ appro_U
#         # ob_error = np.linalg.norm(exact_ob - appro_ob, ord=2)
#         ob_error = np.sort(abs(np.linalg.eigvalsh(exact_ob - appro_ob)))[-1]
#         print('ob error (operator norm, largest eigen): ', ob_error, '; r:', r, '; t:', t)
#         return ob_error
#     elif type == 'worst_loose_bound':
#         return relaxed_st_bound(r, coeffs[1], coeffs[2], t, ob_type=coeffs[0])
#     elif type == 'lightcone_bound':
#         return lc_tail_bound(r, coeffs[1], coeffs[2], t, ob_type=coeffs[0], verbose=False)
#         # return relaxed_lc_bound(r, coeffs[1], coeffs[2], t, ob_type=coeffs[0], verbose=False)
#     elif type == 'average_bound':
#         # return tight_bound(h_list, 2, t, r, type='4')
#         if coeffs != []:
#             return 2 * tight_bound(h_list, 2, t, r, type='fro') * coeffs[0]
#         else:
#             return 2 * tight_bound(h_list, 2, t, r, type='fro')
#     elif type == 'average_empirical':
#         appro_U = pf_r(h_list, t, r, order=pf_ord, use_jax=use_jax)
#         err_list = [np.linalg.norm(np.outer(exact_U @ state.data.conj().T , (exact_U @ state.data.conj().T).conj().T) - np.outer(appro_U @ state.data.conj().T, (appro_U @ state.data.conj().T).conj().T), ord='nuc') for state in rand_states]
#         # err_list = [np.linalg.norm((exact_U - pf_r(h_list, t, r, order=pf_ord, use_jax=use_jax)) @ state.data) for state in rand_states]
#         if type(ob) == list:
#             ob_norm = sum([np.linalg.norm(o, ord=2) for o in ob])
#         else:
#             ob_norm = np.linalg.norm(ob, ord=2)
#         if return_error_list:
#             return np.array(err_list) * ob_norm
#             # return np.array(err_list) * np.linalg.norm(ob, ord=2)
#         else:
#             # return np.mean(err_list) * np.linalg.norm(ob, ord=2)
#             return np.mean(err_list) * ob_norm
#     elif type == 'average_ob_bound_legacy':
#     # elif type == 'average_ob_bound':
#         if isinstance(h_list[0], csr_matrix):
#             onestep_exactU = scipy.linalg.expm(-1j * t/r * sum([herm.toarray() for herm in h_list]))
#             d = len(h_list[0].toarray())
#         elif isinstance(h_list[0], np.ndarray):
#             onestep_exactU = scipy.linalg.expm(-1j * t/r * sum([herm for herm in h_list]))
#             d = len(h_list[0])
#         E_op = onestep_exactU - pf_r(h_list, t/r, 1, order=pf_ord, use_jax=use_jax)
#         # print((np.trace(E_op @ E_op.conj().T @ E_op @ E_op.conj().T)/d)**(1/4))
#         bound = 2 * r * (np.trace(E_op @ E_op.conj().T @ E_op @ E_op.conj().T)/d)**(1/4) * (np.trace(ob @ ob @ ob @ ob)/d)**(1/4)
#         # print(f'bound_e={bound_e}, bound={bound}')
#         return bound
#     elif type == 'average_ob_bound':
#     # elif type == 'average_ob_bound_nc':
#         if isinstance(h_list[0], csr_matrix):
#             d = len(h_list[0].toarray())
#         elif isinstance(h_list[0], np.ndarray):
#             d = len(h_list[0])
#         # if coeffs == []:
#         #     bound = 2 * tight_bound(h_list, 2, t, r, type='4') * (np.trace(ob @ ob @ ob @ ob)/d)**(1/4)
#         # else:
#         #     bound = np.sqrt(2) * tight_bound(h_list, 2, t, r, type='fro') * (sum([np.linalg.norm(ob, ord='fro') for ob in coeffs[0]])/(d+1)**(1/2)) 
#         if type(ob) == list:
#             bound = np.sqrt(2) * tight_bound(h_list, 2, t, r, type='fro') * sum([np.linalg.norm(o, ord='fro') for o in ob])/(d+1)**(1/2) 
#         else:
#             bound = np.sqrt(2) * tight_bound(h_list, 2, t, r, type='fro') * np.linalg.norm(ob, ord='fro')/(d+1)**(1/2) 
#         return bound
#     # elif type == 'observable_empirical':
#     elif type == 'average_ob_empirical':
#         approx_U = pf_r(h_list, t, r, order=pf_ord, use_jax=use_jax)
#         exact_final_states = [exact_U @ state.data.T for state in rand_states]
#         appro_final_states = [approx_U @ state.data.T for state in rand_states]
#         if type(ob) == list:
#             err_list = [sum([abs(appro_final_states[i].conj().T @ o @ appro_final_states[i] - exact_final_states[i].conj().T @ o @ exact_final_states[i]) for o in ob]) for i in range(len(rand_states))]
#         else:
#             err_list = [abs(appro_final_states[i].conj().T @ ob @ appro_final_states[i] - exact_final_states[i].conj().T @ ob @ exact_final_states[i]) for i in range(len(rand_states))]
#         if return_error_list:
#             return np.array(err_list)
#         else:
#             return np.mean(err_list)
#     # elif type == 'observable_bound':
#     #     return None
#     else: 
#         raise ValueError(f'type={type} is not defined!')

# def op_error(exact, approx, norm='spectral'):
#     ''' 
#     Frobenius norm of the difference between the exact and approximated operator
#     input:
#         exact: exact operator
#         approx: approximated operator
#     return: error of the operator
#     '''
#     if norm == 'fro':
#         return jnp.linalg.norm(exact - approx)
#     elif norm == 'spectral':
#         # if the input is in csr_matrix format
#         if isinstance(exact, csc_matrix) and isinstance(approx, csc_matrix):
#             return jnp.linalg.norm(jnp.array(exact.toarray() - approx.toarray()), ord=2)
#         else:
#             return jnp.linalg.norm(exact - approx, ord=2)
#     else:
#         raise ValueError('norm is not defined')
#     # return np.linalg.norm(exact - approx)/len(exact)


# # evaluate trotter error for different number of trotter steps
# def trotter_error(list_herm, r_list, t, norm='spectral', n_perm=50, verbose=False):
#     ''' 
#     evaluate trotter error for different number of trotter steps
#     input: 
#         list_herm: a list of Hermitian matrices
#         r_list: number of trotter steps
#     return: trotter error
#     '''
#     exact_U = expm(-1j * t * sum(list_herm))
#     list_U = [expm(-1j * t / (2*r_list[-1]) * herm) for herm in list_herm]
#     if len(list_U) >= 5:
#         print('number of terms: ', len(list_U))
#         perm_list = [list_U] 
#         seed_value = random.randrange(sys.maxsize)
#         random.seed(seed_value)  
#         # randomly select 5 permutations from perm_list
#         for _ in range(n_perm-1):
#             # random.shuffle(list_U) 
#             # perm_list.append(list_U[:])
#             perm_list.append(random.sample(list_U, len(list_U)))
#         # perm_list = random.sample(perm_list, 50) 
#         print('# randomly selected perm: ', len(perm_list))
#     else:
#         # generate a list of permutation of the order of the matrices
#         perm_list = list(itertools.permutations(list_U))
#         # print('perm_list', perm_list)
#         print('# all perm: ', len(perm_list))
#     # perm_list = list(itertools.permutations(list_herm))[:5]
#     # for r in r_list:
#     # first-order trotter
#     trotter_error_list = [op_error(matrix_power(matrix_product(perm, int(2*r_list[-1]/r)), r), exact_U, norm) for r in r_list for perm in perm_list]
#     # trotter_error_list = [op_error(matrix_power(unitary_matrix_product(perm, t=t/r), r), exact_U, norm) for r in r_list for perm in perm_list]
#     # second-order trotter
#     trotter_error_list_2nd = [op_error(matrix_power(matrix_product(perm, int(r_list[-1]/r)) @ matrix_product(perm[::-1], int(r_list[-1]/r)), r), exact_U, norm) for r in r_list for perm in perm_list]
#     err_1st_reshaped = np.array(trotter_error_list).reshape(len(r_list), len(perm_list))
#     err_2nd_reshaped = np.array(trotter_error_list_2nd).reshape(len(r_list), len(perm_list))

#     return err_1st_reshaped , err_2nd_reshaped



