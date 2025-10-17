from functools import reduce
import itertools as it

import numpy as np
from qiskit.quantum_info import SparsePauliOp, DensityMatrix, shannon_entropy, Statevector, partial_trace, pauli_basis, PTM, Operator
from qiskit_aer.noise import pauli_error

### channel ### 
def depolarize_error(rate):
    return pauli_error([('X', rate/3), ('Y', rate/3), ('Z', rate/3), ('I', 1 - rate)])

def dm2pauli(dm, verbose=False):
    n = int(np.log2(dm.dim))
    if verbose: print('num_qubits=', pauli_basis(n))
    pauli_coeffs = [dm.expectation_value(SparsePauliOp(op)) for op in pauli_basis(n)]
    return pauli_coeffs

def pauli2dm(pauli_coeffs):
    n = int(np.log2(len(pauli_coeffs)))
    return sum([SparsePauliOp(op, coeff/2**n).to_matrix()  for op, coeff in zip(pauli_basis(n), pauli_coeffs)])

def tensor_channel(channel, n, all=True): 
    id_c = PTM(np.eye(4))
    if all:
        global_channel = reduce(lambda x, y: x.tensor(y), [PTM(channel)] * n)
    else:
        global_channel = reduce(lambda x, y: x.tensor(y), [id_c] * (n-1) + [PTM(channel)])
        
    return global_channel 

def unitary2ptm(U, verbose=False):
    """Convert a unitary matrix to its PTM representation."""
    n = int(np.log2(U.shape[0]))
    if verbose: print('num_qubits=', n)
    if not Operator(U).is_unitary:
        raise ValueError("The input matrix is not unitary.")
    
    paulis = [label.to_matrix() for label in pauli_basis(n)]
    if verbose: print('paulis=',  pauli_basis(n))
    dim = len(paulis)
    ptm = np.zeros((dim, dim), dtype=complex)
    
    for i, P_i in enumerate(paulis):
        for j, P_j in enumerate(paulis):
            ptm[i, j] = np.trace(P_i @ U @ P_j @ U.conj().T)/2**n
    
    return PTM(ptm)

def mat2pauli(mat, return_dict=True, verbose=False):
    n = int(np.log2(mat.shape[0]))
    if verbose: 
        print('num_qubits=', n)
        print('pauli_basis=', pauli_basis(n))
    pauli_coeffs = [np.trace(mat @ SparsePauliOp(op).to_matrix()) for op in pauli_basis(n)]
    if return_dict:
        return dict(zip(pauli_basis(n), pauli_coeffs))
    else:
        return pauli_coeffs
