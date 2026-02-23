from mastereq.tests.test_gksl_basic import *

if __name__ == '__main__':
    test_trace_and_hermitian()
    test_positive_semidef()
    test_agrees_with_analytic_sm()
    print('RUN_TESTS: ALL OK')
