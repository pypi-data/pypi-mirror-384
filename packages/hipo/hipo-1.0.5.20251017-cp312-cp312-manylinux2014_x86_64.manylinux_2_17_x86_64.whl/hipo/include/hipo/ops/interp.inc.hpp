template <class _ValT, class _GlobalIdxT, class _IdxT, class _Space>
void SpLevelTransferOpsImpl<_ValT, _GlobalIdxT, _IdxT, _Space>::par_boomeramg_interpolation_extended_pi(
    _Space &space, _IdxT nprocs, _IdxT myrank, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> *A_blks,
    COT_SpMVCSRRawMat<_IdxT, _IdxT> *S_blks, const _ValT *A_diag, const _IdxT *CF_marker, COT_RawCommPattern<_IdxT, _IdxT> *CF_marker_exter,
    COT_CSRRawMat<_ValT, _IdxT> P, _IdxT *naggr, typename TypeInfo<_ValT>::scalar_type trunc_factor, _IdxT *P_marker,
    COT_RawCommPattern<_IdxT, _IdxT> *P_marker_exter, _IdxT *fine_to_coarse, _IdxT num_functions, _IdxT *dof_func) {
    typedef typename TypeInfo<_ValT>::scalar_type Scalar;
    _IdxT jj_counter_data = 0;
    _IdxT coarse_counter_data = 0;
    _IdxT strong_f_marker_data = -2;

    _IdxT n_fine = rows;
    _IdxT num_procs = nprocs;
    _IdxT *p_jj_counter = &jj_counter_data;
    _IdxT *p_coarse_counter = naggr;
    _IdxT *p_strong_f_marker = &strong_f_marker_data;
    _ValT one = 1;
    _ValT zero = 0;

    if (P.col_idx == 0 || P.values == 0) {
        spm::parallel_for(
            Range(space, 0, n_fine), SPM_LAMBDA(_IdxT i) {
                *p_coarse_counter = 0;
                P_marker[i] = -1;
                fine_to_coarse[i] = -1;
            });
        // 计算非零元的个数
        spm::parallel_for(
            Range(space, 0, n_fine), SPM_LAMBDA(_IdxT i) {
        auto &jj_counter = *p_jj_counter;
        auto &coarse_counter = *p_coarse_counter;

        P.row_ptr[i] = jj_counter;
        if (num_procs > 1) {
            /// TBD
        }
        if (CF_marker[i] >= 0) {
            jj_counter++;
            fine_to_coarse[i] = coarse_counter;
            coarse_counter++;
        } else if (CF_marker[i] != -3) {
            for (_IdxT jj = S.row_ptr[i]; jj < S.row_ptr[i + 1]; jj++) {
                _IdxT i1 = S.col_idx[jj];
                if (!S.values[jj]) {
                    continue;
                }
                if (CF_marker[i1] >= 0) {
                    // i1 is a C point
                    if (P_marker[i1] < P.row_ptr[i]) {
                        P_marker[i1] = jj_counter;
                        jj_counter++;
                    }
                } else if (CF_marker[i1] != -3) {
                    // i1 is a F point, loop through it's strong neighors
                    for (_IdxT kk = S.row_ptr[i1]; kk < S.row_ptr[i1 + 1]; kk++) {
                        _IdxT k1 = S.col_idx[kk];
                        if (!S.values[kk]) {
                            continue;
                        }
                        if (CF_marker[k1] >= 0) {
                            if (P_marker[k1] < P.row_ptr[i]) {
                                P_marker[k1] = jj_counter;
                                jj_counter++;
                            }
                        }
                    }
                    if (num_procs > 1) {
                        // TBD
                    }
                }
            }

            // Look at off diag strong connections of i
            if (num_procs > 1) {
                // TBD
            }
        }
            });

        spm::parallel_for(
            Range(space, 0, 1), SPM_LAMBDA(_IdxT _ii) {
                auto &jj_counter = *p_jj_counter;
                P.row_ptr[n_fine] = jj_counter;
            });
    } else {
        spm::parallel_for(Range(space, 0, n_fine), SPM_LAMBDA(_IdxT i) { P_marker[i] = -1; });

        // 先填充非零元的位置
        spm::parallel_for(Range(space, 0, n_fine), SPM_LAMBDA(_IdxT i) {
        _IdxT &strong_f_marker = *p_strong_f_marker;
        _IdxT jj_begin_row = P.row_ptr[i];
        _IdxT jj_counter = jj_begin_row;

        /*--------------------------------------------------------------------
            *  If i is a c-point, interpolation is the identity.
            *--------------------------------------------------------------------*/

        if (CF_marker[i] >= 0) {
            P.col_idx[jj_counter] = fine_to_coarse[i];
            P.values[jj_counter] = one;
            jj_counter++;
        }
        /*--------------------------------------------------------------------
            *  If i is an F-point, build interpolation.
            *--------------------------------------------------------------------*/

        else if (CF_marker[i] != -3) {
            strong_f_marker--;
            for (int jj = S.row_ptr[i]; jj < S.row_ptr[i + 1]; jj++) {
                _IdxT i1 = S.col_idx[jj];
                if (!S.values[jj]) {
                    return;
                }
                /*--------------------------------------------------------------
                    * If neighbor i1 is a C-point, set column number in P_diag_j
                    * and initialize interpolation weight to zero.
                    *--------------------------------------------------------------*/
                if (CF_marker[i1] >= 0) {
                    if (P_marker[i1] < jj_begin_row) {
                        P_marker[i1] = jj_counter;
                        P.col_idx[jj_counter] = fine_to_coarse[i1];
                        P.values[jj_counter] = zero;
                        jj_counter++;
                    }
                } else if (CF_marker[i1] != -3) {
                    P_marker[i1] = strong_f_marker;
                    for (_IdxT kk = S.row_ptr[i1]; kk < S.row_ptr[i1 + 1]; kk++) {
                        _IdxT k1 = S.col_idx[kk];
                        if (!S.values[kk]) {
                            return;
                        }
                        if (CF_marker[k1] >= 0) {
                            if (P_marker[k1] < jj_begin_row) {
                                P_marker[k1] = jj_counter;
                                P.col_idx[jj_counter] = fine_to_coarse[k1];
                                P.values[jj_counter] = zero;
                                jj_counter++;
                            }
                        }
                    }
                    if (num_procs > 1) {
                        // TBD
                    }
                }
            }
            if (num_procs > 1) {
                // TBD
            }

            //  再填充非零元的值
            _IdxT jj_end_row = jj_counter;
            SPM_ASSERT(jj_end_row == P.row_ptr[i + 1]);
            _ValT diagonal = A_diag[i];

            printf("HIPO row %d\n", i);
            for (_IdxT jj = A.row_ptr[i]; jj < A.row_ptr[i + 1]; jj++) {
                /* i1 is a c-point and strongly influences i, accumulate
                    * a_(i,i1) into interpolation weight */
                auto &S = S_blks[k];
                printf("  L1 HIPO row %d, col %d Aval %f, Sval %d\n", i, col, A.values[jj], S.values[jj]);
                if (i == col) {
                    return;
                }
                SPM_ASSERT(S.procId == A.procId);
                // if (!S.values[jj]) {
                //     return;
                // }
                _IdxT i1 = A.col_idx[jj];
                if (P_marker[i1] >= jj_begin_row) {
                    P.values[P_marker[i1]] += A.values[jj];
                } else if (P_marker[i1] == strong_f_marker) {
                    _ValT sum = zero;
                    _ValT sgn = 1;
                    if (A.values[A.row_ptr[i1]] < _ValT(0)) {
                        sgn = -1;
                    }
                    // Loop over row of A for point i1 and calculate the sum
                    // of the connections to c-points that strongly influence i.
                    for (_IdxT jj1 = A.row_ptr[i1]; jj1 < A.row_ptr_end[i1]; jj1++) {
                        _IdxT i2 = A.col_idx[jj1];
                        printf("    L2 HIPO row %d, col %d col2 %d, Aval %f, Sval %d sgn %f P_marker %d\n", i, col, i2,
                                A.values[jj1], S.values[jj1], sgn, P_marker[i2]);

                        if (i1 == i2) {
                            continue;
                        }
                        // if (!S.values[jj1]) {
                        //     return;
                        // }
                        if ((P_marker[i2] >= jj_begin_row || i2 == i) && (sgn * A.values[jj1]) < _ValT(0)) {
                            sum += A.values[jj1];
                            if (1) {
                                printf("    SUMACC HIPO row %d, i1 %d i2 %d val %f acc sum %f\n", i, i1, i2, A.values[jj1], sum);
                            }
                        }
                    }
                    if (num_procs > 1) {
                        // TBD
                    }
                    if (sum != 0) {
                        _ValT distribute = A.values[jj] / sum;
                        // Loop over row of A for point i1 and do the distribution
                        for (_IdxT jj1 = A.row_ptr[i1]; jj1 < A.row_ptr_end[i1]; jj1++) {
                            _IdxT i2 = A.col_idx[jj1];
                            if (i1 == i2) {
                                continue;
                            }

                            if ((P_marker[i2] >= jj_begin_row) && (sgn * A.values[jj1]) < _ValT(0)) {
                                P.values[P_marker[i2]] += distribute * A.values[jj1];
                            }
                            if (i2 == i && (sgn * A.values[jj1]) < _ValT(0)) {
                                diagonal += distribute * A.values[jj1];
                            }
                        }
                        if (num_procs > 1) {
                            // TBD
                        }
                    } else {
                        diagonal += A.values[jj];
                    }
                } else if (CF_marker[i1] != -3) {
                    if (num_functions == 1 || dof_func[i] == dof_func[i1]) {
                        diagonal += A.values[jj];
                    }
                }
            }
            // printf("HIPO row %d sum %f diagonal %f\n", (int)i, sum, diagonal);

            if (num_procs > 1) {
                // TBD
            }
            if (hipo::abs(diagonal)) {
                for (_IdxT jj = jj_begin_row; jj < jj_end_row; jj++) {
                    P.values[jj] /= -diagonal;
                }
            }
        }
        strong_f_marker--;
    });
        // End large for loop over nfine
    }
}
