############################
# define spin Hamiltonians
############################

import numpy as np
from qiskit.quantum_info import SparsePauliOp
import random
import itertools

class IQP:
    def __init__(self, n: int, theta=0, verbose=False):
        ## todo degree-k
        self.n = n
        if theta == 0:
            self.pstr = [(''.join(random.choices(['I','Z'], k=n)), 2*np.pi*random.random()) for _ in range(1*n)]
        else:
            self.pstr = [(''.join(random.choices(['I','Z'], k=n)), theta) for _ in range(1*n)]

        if verbose: print('pstr: ', self.pstr)
        self.ham = SparsePauliOp.from_list(self.pstr)
        # return SparsePauliOp.from_list(pstr)

    # if H_type == 0:
    #     J = 2
    #     ising_str = 'ZZ' + 'I' * (n-2)
    #     uni_ising = [(ising_str[i:]+ising_str[:i], J) for i in range(n)]
    #     del uni_ising[1]
    #     print(uni_ising)
    #     H =  SparsePauliOp.from_list(uni_ising)
    # else:
    #     # H = get_hamiltonian(L=n, J=1.0, h=0.2, g=0.0, verbose=True)
    #     H = IQP_H(n, theta, verbose=True)

class Cluster_Ising:
    ## often used in machine learning for quantum phase transition
    def __init__(self, n: int, h1, h2, verbose=False):
        self.n = n  # n is supposed to be even
        self.h1 = h1
        self.h2 = h2
        self.verbose = verbose

        self.ham = SparsePauliOp.from_list([['I'*n, 0]])

        for i in range(n-2):
            self.ham += SparsePauliOp.from_list([['I'*i + 'ZXZ' + 'I'*(n-i-3), -1]])
            self.ham += SparsePauliOp.from_list([['I'*i + 'X' + 'I'*(n-i-1), -h1]])
            self.ham += SparsePauliOp.from_list([['I'*i + 'XX' + 'I'*(n-i-2), -h2]])

        self.ham += SparsePauliOp.from_list([['I'*(n-2)+'XI', -h1], ['I'*(n-1)+'X', -h1]])
        self.ham += SparsePauliOp.from_list([['I'*(n-2)+'XX', -h2]])

        self.ham.simplify()
        self.H = self.ham  # alternative name for compatibility with other classes
        order_string = ''
        for i in range(1, n+1):
            if i == 1:
                order_string += 'Z'
            elif i % 2 == 0:
                order_string += 'X'
            elif i == n:
                order_string += 'Z'
            else:
                order_string += 'I'
        if verbose: print('order string: ', order_string)
        self.string_order = SparsePauliOp.from_list([[order_string, 1]])

class Nearest_Neighbour_2d:
    def __init__(self, nd: int, Jx=0, Jy=0, Jz=0, hx=0, hy=0, hz=0, pbc=False, verbose=False, rand_field=[]):
        ## 2D square (todo rectangular) lattice
        ##     n is the number of qubits in each direction
        self.nd = nd
        self.Jx, self.Jy, self.Jz = Jx, Jy, Jz
        self.hx, self.hy, self.hz = hx, hy, hz

        def neighbor_list(n):
            nq = n**2
            return nq, [(i,j) for i,j in itertools.combinations(range(nq), 2) if abs(i-j)%n + abs(i//n-j//n)==1]

        self.n, self.loc_pairs = neighbor_list(nd)
        self.xx_tuples = [('XX', pair, Jx) for pair in self.loc_pairs]
        self.yy_tuples = [('YY', pair, Jy) for pair in self.loc_pairs]
        self.zz_tuples = [('ZZ', pair, Jz) for pair in self.loc_pairs]

        if len(rand_field) == 0:
            self.rand_field = [0]*self.n
        elif len(rand_field) >= self.n:
            self.rand_field = rand_field[:self.n]
        else:
            raise ValueError(f'Length of random field should be at least {self.n}!')

        self.x_tuples = [('X', [i], (self.rand_field[i]+1)*hx) for i in range(0, self.n)] 
        self.y_tuples = [('Y', [i], (self.rand_field[i]+1)*hy) for i in range(0, self.n)] 
        self.z_tuples = [('Z', [i], (self.rand_field[i]+1)*hz) for i in range(0, self.n)] 

        if pbc: 
            for i in range(self.nd):
                ## add periodic boundary conditions in horizontal direction
                self.xx_tuples.append(('XX', [i*nd, (i+1)*nd-1], Jx))
                self.yy_tuples.append(('YY', [i*nd, (i+1)*nd-1], Jy))
                self.zz_tuples.append(('ZZ', [i*nd, (i+1)*nd-1], Jz))
                ## add periodic boundary conditions in vertical direction
                self.xx_tuples.append(('XX', [i, i+nd*(nd-1)], Jx))
                self.yy_tuples.append(('YY', [i, i+nd*(nd-1)], Jy))
                self.zz_tuples.append(('ZZ', [i, i+nd*(nd-1)], Jz))

        self.ham = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.yy_tuples, *self.zz_tuples, *self.x_tuples, *self.y_tuples, *self.z_tuples], num_qubits=self.n).simplify() 

        self.xyz_group()
        # self.par_group()
        if verbose: 
            print('The Hamiltonian: \n', self.ham)
            print('The xyz grouping: \n', self.ham_xyz)
            # print('The parity grouping: \n', self.ham_par)

    def xyz_group(self):
        self.x_terms = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.x_tuples], num_qubits=self.n).simplify()
        self.y_terms = SparsePauliOp.from_sparse_list([*self.yy_tuples, *self.y_tuples], num_qubits=self.n).simplify()
        self.z_terms = SparsePauliOp.from_sparse_list([*self.zz_tuples, *self.z_tuples], num_qubits=self.n).simplify()
        self.ham_xyz = [self.x_terms, self.y_terms, self.z_terms]
        ## remove empty terms e.g. No Y terms
        self.ham_xyz = [item for item in self.ham_xyz if not np.all(abs(item.coeffs) == 0)]

class Nearest_Neighbour_1d:
    def __init__(self, n: int, Jx=0, Jy=0, Jz=0, hx=0, hy=0, hz=0, pbc=False, verbose=False, rand_field=[]):
        self.n = n
        self.Jx, self.Jy, self.Jz = Jx, Jy, Jz
        self.hx, self.hy, self.hz = hx, hy, hz

        self.xx_tuples = [('XX', [i, i + 1], Jx) for i in range(0, n-1)]
        self.yy_tuples = [('YY', [i, i + 1], Jy) for i in range(0, n-1)]
        self.zz_tuples = [('ZZ', [i, i + 1], Jz) for i in range(0, n-1)]

        if len(rand_field) == 0:
            self.rand_field = [0]*n
        elif len(rand_field) >= n:
            self.rand_field = rand_field[:n]
        else:
            raise ValueError(f'Length of random field should be at least {n}!')

        self.x_tuples = [('X', [i], (self.rand_field[i]+1)*hx) for i in range(0, n)] 
        self.y_tuples = [('Y', [i], (self.rand_field[i]+1)*hy) for i in range(0, n)] 
        self.z_tuples = [('Z', [i], (self.rand_field[i]+1)*hz) for i in range(0, n)] 

        if pbc: 
            self.xx_tuples.append(('XX', [n-1, 0], Jx))
            self.yy_tuples.append(('YY', [n-1, 0], Jy))
            self.zz_tuples.append(('ZZ', [n-1, 0], Jz))

        self.ham = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.yy_tuples, *self.zz_tuples, *self.x_tuples, *self.y_tuples, *self.z_tuples], num_qubits=n).simplify() 
        self.xyz_group()
        self.par_group()
        if verbose: 
            print('The Hamiltonian: \n', self.ham)
            print('The xyz grouping: \n', self.ham_xyz)
            print('The parity grouping: \n', self.ham_par)

    def xyz_group(self):
        self.x_terms = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.x_tuples], num_qubits=self.n).simplify()
        self.y_terms = SparsePauliOp.from_sparse_list([*self.yy_tuples, *self.y_tuples], num_qubits=self.n).simplify()
        self.z_terms = SparsePauliOp.from_sparse_list([*self.zz_tuples, *self.z_tuples], num_qubits=self.n).simplify()
        self.ham_xyz = [self.x_terms, self.y_terms, self.z_terms]
        self.ham_xyz = [item for item in self.ham_xyz if not np.all(abs(item.coeffs) == 0)]

    def par_group(self):
        self.even_terms = SparsePauliOp.from_sparse_list([*self.xx_tuples[::2], *self.yy_tuples[::2], *self.zz_tuples[::2], *self.x_tuples[::2], *self.y_tuples[::2], *self.z_tuples[::2]], num_qubits=self.n).simplify()
        self.odd_terms = SparsePauliOp.from_sparse_list([*self.xx_tuples[1::2], *self.yy_tuples[1::2], *self.zz_tuples[1::2], *self.x_tuples[1::2], *self.y_tuples[1::2], *self.z_tuples[1::2]], num_qubits=self.n).simplify()
        self.ham_par = [self.even_terms, self.odd_terms]

    # def lc_group(self, right, left, step):
    #     self.ham_lc = []


class Power_Law:
    def __init__(self, n: int, alpha: int, Jx=0, Jy=0, Jz=0, hx=0.0, hy=0.0, hz=0, pbc=False, verbose=False):
        self.n, self.alpha = n, alpha
        self.Jx, self.Jy, self.Jz = Jx, Jy, Jz
        self.hx, self.hy, self.hz = hx, hy, hz
        self.xx_tuples = [('XX', [i, j], Jx*abs(i-j)**(-alpha)) for i in range(0, n-1) for j in range(i+1, n)]
        self.yy_tuples = [('YY', [i, j], Jy*abs(i-j)**(-alpha)) for i in range(0, n-1) for j in range(i+1, n)]
        self.zz_tuples = [('ZZ', [i, j], Jz*abs(i-j)**(-alpha)) for i in range(0, n-1) for j in range(i+1, n)]
        self.x_tuples = [('X', [i], hx) for i in range(0, n)] 
        self.y_tuples = [('Y', [i], hy) for i in range(0, n)] 
        self.z_tuples = [('Z', [i], hz) for i in range(0, n)] 
        if pbc: 
            # self.xx_tuples.append(('XX', [n-1, 0], Jx))
            # self.yy_tuples.append(('YY', [n-1, 0], Jy))
            # self.zz_tuples.append(('ZZ', [n-1, 0], Jz))
            raise ValueError(f'PBC is not defined!')

        self.ham = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.yy_tuples, *self.zz_tuples, *self.x_tuples, *self.y_tuples, *self.z_tuples], num_qubits=n).simplify()
        if verbose: print('The Hamiltonian: \n', self.ham)
        self.xyz_group()

    def xyz_group(self):
        self.x_terms = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.x_tuples], self.n).simplify()
        self.y_terms = SparsePauliOp.from_sparse_list([*self.yy_tuples, *self.y_tuples], self.n).simplify()
        self.z_terms = SparsePauliOp.from_sparse_list([*self.zz_tuples, *self.z_tuples], self.n).simplify()
        self.ham_xyz = [self.x_terms, self.y_terms, self.z_terms]
        self.ham_xyz = [item for item in self.ham_xyz if not np.all(abs(item.coeffs) == 0)]

    # def parity_group(self):
    #     print('todo')
    #     return self.ham.to_matrix().todense()










# class TF_Ising_1d:
#     def __init__(self, n: int, J=1, h=0.2, g=0.0, pbc=False, verbose=False):
#         self.n = n
#         self.zz_tuples = [('ZZ', [i, i + 1], -J) for i in range(0, n-1)]
#         self.x_tuples = [('X', [i], -h) for i in range(0, n)] 
#         self.z_tuples = [('Z', [i], -g) for i in range(0, n)] 
#         if pbc: self.zz_tuples.append(('ZZ', [n-1, 0], -J))

#         self.ham = SparsePauliOp.from_sparse_list([*self.zz_tuples, *self.x_tuples, *self.z_tuples], num_qubits=n).simplify()
#         if verbose: print('The Hamiltonian: \n', self.ham)
#         self.parity_group()
#         self.xyz_group()

#     def parity_group(self):
#         # return self.ham.to_matrix().todense()
#         self.ham_parity = [SparsePauliOp.from_sparse_list([*self.zz_tuples[::2], *self.x_tuples[::2], *self.z_tuples[::2]], num_qubits=self.n).simplify(), SparsePauliOp.from_sparse_list([*self.zz_tuples[1::2], *self.x_tuples[1::2], *self.z_tuples[1::2]], num_qubits=self.n).simplify()]

#     def xyz_group(self):
#         self.ham_xyz = [SparsePauliOp.from_sparse_list([*self.zz_tuples, *self.z_tuples], num_qubits=self.n).simplify(), SparsePauliOp.from_sparse_list([*self.x_tuples], num_qubits=self.n)]

# class Heisenberg_1d:
#     def __init__(self, n: int, Jx=1, Jy=1, Jz=1, h=0.2, pbc=False, verbose=False):
#         self.xx_tuples = [('XX', [i, i + 1], -Jx) for i in range(0, n-1)]
#         self.yy_tuples = [('YY', [i, i + 1], -Jy) for i in range(0, n-1)]
#         self.zz_tuples = [('ZZ', [i, i + 1], -Jz) for i in range(0, n-1)]
#         self.x_tuples = [('X', [i], -h) for i in range(0, n)] 
#         if pbc: 
#             self.xx_tuples.append(('XX', [n-1, 0], -Jx))
#             self.yy_tuples.append(('YY', [n-1, 0], -Jy))
#             self.zz_tuples.append(('ZZ', [n-1, 0], -Jz))

#         self.ham = SparsePauliOp.from_sparse_list([*self.xx_tuples, *self.yy_tuples, *self.zz_tuples, *self.x_tuples], num_qubits=n)
#         if verbose: print('The Hamiltonian: \n', self.ham)

#     def parity_group(self):
#         print('todo')
#         return self.ham.to_matrix().todense()
