
def binary_search_r(r_start, r_end, epsilon, error_measure, step=1, comment='', verbose=False):
    # print(f'----binary search r ({error_measure.__name__})----')
    print(f'----[{comment}] binary search r (r_start={r_start}, r_end={r_end})----')
    while error_measure(r_end) > epsilon:
        print("the initial r_end is too small, increase it by 10 times.")
        r_end *= 10

    if error_measure(r_start) <= epsilon:
        r = r_start
    else: 
        while r_start < r_end - step: 
            r_mid = int((r_start + r_end) / 2)
            if error_measure(r_mid) > epsilon:
                r_start = r_mid
            else:
                r_end = r_mid
            if verbose: print('r_start:', r_start, '; r_end:', r_end)
        r = r_end
    if verbose: print('r:', r, '; err: ', error_measure(r))
    return r


# def search_r_for_error(r_start, r_end, epsilon, t, list_herm, k, norm='spectral', verbose=False):
#     tol = r_end - r_start
#     exact_U = expm(-1j * t * sum(list_herm))
#     # binary search from r_start to r_end
#     while tol > 2:
#         r = int((r_start + r_end) / 2)
#         err = op_error(matrix_power(pf(list_herm, k, t=t/r), r), exact_U, norm)
#         # if k == 1:
#         #     err = op_error(matrix_power(unitary_matrix_product(list_herm, t=t/r), r), exact_U, norm)
#         # elif k == 2:
#         #     err = op_error(matrix_power(second_order_trotter(list_herm, t=t/r), r), exact_U, norm)
#         # elif k != 2 and k > 1 and k % 2 == 0:
#         #     err = op_error(matrix_power(high_order_trotter(list_herm, k, t=t/r), r), exact_U, norm)
#         # else:
#         #     raise ValueError('k is not defined')

#         if err > epsilon:
#             r_start = r
#         else:
#             r_end = r
#         tol = abs(r_end - r_start)
#     if verbose: print('err: ', err)
#     return r


def normalize(data):
    s = sum(a**2 for a in data)
    return [a**2/s for a in data]



def ob_dt(ob_list, t_list, ord=1):
    """time derivative of observable expectation 

    Args:
        ob_list (_type_): _description_
        t_list (_type_): _description_

    Returns:
        ob_dt_list: _description_
    """
    if ord == 1:
        ob_dt_list = [(ob_list[i + 1] - ob_list[i]) / (t_list[-1]/len(t_list))  for i in range(len(ob_list) - 1)]
    elif ord == 2:
        ob_dt_list = [(ob_list[i + 2] - 2*ob_list[i + 1] + ob_list[i]) / (0.5*t_list[-1]/len(t_list))  for i in range(len(ob_list) - 2)]
    return ob_dt_list
