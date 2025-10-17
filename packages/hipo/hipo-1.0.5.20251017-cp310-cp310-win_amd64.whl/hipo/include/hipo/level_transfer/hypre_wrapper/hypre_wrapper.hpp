#pragma once

#include "hipo/mat/ParCSRMatrix.hpp"
#include "HYPRE.h"
#include "_hypre_parcsr_mv.h"
#include "_hypre_parcsr_ls.h"

namespace hipo {

typedef ParCSRMatrixT<HYPRE_Real, HIPO_BIGINT, HIPO_INT> ParCSRMatrix;
typedef ParVectorT<HYPRE_Real, HIPO_BIGINT, HIPO_INT> ParVector;


HYPRE_IJVector HIPO_WIN_API convert(const ParVector& x_rap);

typedef hypre_ParVector* hypre_ParVector_PTR;
hypre_ParVector_PTR HIPO_WIN_API convertEx(const ParVector& x_rap);


HYPRE_IJMatrix HIPO_WIN_API convert(const ParCSRMatrix& A_rap);

typedef hypre_ParCSRMatrix* hypre_ParCSRMatrix_PTR;
hypre_ParCSRMatrix_PTR HIPO_WIN_API convertEx(const ParCSRMatrix& A_rap);


ParCSRMatrix HIPO_WIN_API convert(hypre_ParCSRMatrix* A_hypre);


HYPRE_Solver HIPO_WIN_API hypre_create_hierarchy(hypre_ParCSRMatrix* A,
                                hypre_ParVector* x,
                                hypre_ParVector* b,
                                HYPRE_Int print_level = 0,
                                HYPRE_Real max_row_sum = 0.9,
                                int coarsen_type = 3,
                                int interp_type = 0,
                                int p_max_elmts = 0,
                                int agg_num_levels = 0,
                                double strong_threshold = 0.5,
                                double filter_threshold =  0.3,
                                int num_functions = 1);
HYPRE_Solver HIPO_WIN_API hypre_create_GMRES(hypre_ParCSRMatrix* A,
                                hypre_ParVector* x,
                                hypre_ParVector* b, HYPRE_Solver* precond_data,
                                int coarsen_type = 6,
                                int interp_type = 0,
                                int p_max_elmts = 0,
                                int agg_num_levels = 0,
                                double strong_threshold = 0.25,
                                int num_functions = 1);
HYPRE_Solver HIPO_WIN_API hypre_create_BiCGSTAB(hypre_ParCSRMatrix* A,
                                hypre_ParVector* x,
                                hypre_ParVector* b, HYPRE_Solver* precond_data,
                                int coarsen_type = 6,
                                int interp_type = 0,
                                int p_max_elmts = 0,
                                int agg_num_levels = 0,
                                double strong_threshold = 0.25,
                                int num_functions = 1);


}
