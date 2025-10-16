
#pragma once


#include "hipo/utils/Complex.hpp"
#include "hipo/utils/Device.hpp"



namespace hipo {
template <class _ValT, class _IdxT, class _Layout>
class HIPO_WIN_API MatOps {
public:
    static void aAxpby(const Device& dev, _ValT a, _IdxT rows, _IdxT cols, const _ValT * data, const _ValT * x, _ValT b, _ValT * y);
    static void transpose(const Device& dev, _IdxT rows, _IdxT cols, const _ValT * data, _ValT * transposed);
    static void matmat(const Device& dev, _IdxT rows, _IdxT cols, _IdxT cols_B, const _ValT * A, const _ValT * B, _ValT * C);
    static void matmat2(const Device& dev, _IdxT rows, _IdxT cols, _IdxT cols_B, const _ValT * A, const _ValT * B, _ValT * C);
    static void xgetrf(const Device& dev, _IdxT m, _IdxT n, _ValT * a, _IdxT * ipiv, _IdxT * info);
    static void xgetrf_det(const Device& dev, _IdxT n, const _ValT * a, const _IdxT * ipiv, _ValT * pdet);
    static void xgetri(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _IdxT * info);
    static void xgetrs(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _ValT * b, _IdxT nrhs, _IdxT * info);
    static void xgesv(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _ValT * b, _IdxT nrhs, _IdxT * info);
    static void xpotrf(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _IdxT * info);
    static void xpotrs(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _ValT * b, _IdxT nrhs, _IdxT * info);
    static void xsytrf(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _IdxT * info);
    static void xsytf2(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _IdxT * info);
    static void xsytrs(const Device& dev, _IdxT n, _ValT * a, _IdxT * ipiv, _IdxT * info);
    static void get_element_value(const Device& dev, _IdxT rows, _IdxT cols, const _ValT * values, _IdxT i, _IdxT j, _ValT * getval);
    static void set_element_value(const Device& dev, _IdxT rows, _IdxT cols, _ValT * values, _IdxT i, _IdxT j, _ValT setval);
    static void get_diag(const Device& dev, _IdxT rows, _IdxT cols, const _ValT * values, _IdxT diagLen, _ValT * diag);
    static void set_diag(const Device& dev, _IdxT rows, _IdxT cols, _ValT * values, _IdxT diagLen, const _ValT * diag);
    static void select_rows(const Device& dev, _IdxT rows, _IdxT cols, const _ValT * data, _IdxT idxLen, _IdxT * indices, _ValT * sub_array);
    static void unselect_rows(const Device& dev, _IdxT rows, _IdxT cols, _ValT * data, _IdxT idxLen, _IdxT * indices, const _ValT * sub_array);
    static void mat_row_norm(const Device& dev, COT_RawMat<_ValT, _IdxT> rawMat, int dim, typename TypeInfo<_ValT>::scalar_type order, typename TypeInfo<_ValT>::scalar_type * norm);
    static void mat_gauss_elim(const Device& dev, _ValT * A, _ValT * x, _IdxT n, _IdxT * error);
    static void spd_mat_cholesky_decomp(const Device& dev, CholeskyDecompStep step, _ValT * A, _ValT * x, _IdxT n, _IdxT * error);
    static void mat_lu_decomp(const Device& dev, LUDecompStep step, _ValT * A, _ValT * x, _IdxT n, _IdxT * error);
    static void sym_mat_lu_decomp(const Device& dev, LUDecompStep step, _ValT * A, _ValT * x, _IdxT n, _ValT * work, _IdxT * error);
}; // end of class MatOps
} // end of namespace hipo
