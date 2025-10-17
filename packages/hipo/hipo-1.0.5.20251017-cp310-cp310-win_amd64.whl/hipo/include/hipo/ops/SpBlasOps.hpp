
#pragma once


#include "hipo/utils/Complex.hpp"
#include "hipo/utils/Device.hpp"



namespace hipo {
template <class _ValT, class _IdxT>
class HIPO_WIN_API SpBlasOps {
public:
    static void aAxpby(const Device& dev, _ValT a, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * row_end_ptr, const _IdxT * col_idx, const _ValT * values, const _ValT * x, _ValT b, _ValT * y);
    static void aAxpby_multi(const Device& dev, _ValT a, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, _IdxT n, _IdxT ldx, const _ValT * x, _ValT b, _IdxT ldy, _ValT * y);
    static void jacobi(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, const _ValT * x_old, const _ValT * b, _ValT * x, _ValT omega);
    static void jacobi_diagLp(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, const _ValT * x_old, const _ValT * b, _ValT * x, _ValT omega, typename TypeInfo<_ValT>::scalar_type p, const _IdxT * sweep_ordering);
    static void richardson(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, const _ValT * x_old, const _ValT * b, _ValT * x, _ValT omega);
    static void sor(const Device& dev, _IdxT rows, _IdxT cols, _IdxT * row_ptr, _IdxT * col_idx, _ValT * values, const _ValT * b, _ValT * x, _ValT omega, int forward, const _IdxT * sweep_ordering);
    static void csr2dense(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, _ValT * dense);
    static void get_selected_rows(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> origmat, _IdxT n, const _IdxT * rowIds, COT_CSRRawMat<_ValT, _IdxT> rowmat, int sameRows);
    static void get_selected_cols(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> origmat, _IdxT n, const _IdxT * colIds, COT_CSRRawMat<_ValT, _IdxT> colmat, _IdxT col_shift);
    static void get_selected_cols_v2(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> origmat, const _IdxT * row_start, const _IdxT * row_end, COT_CSRRawMat<_ValT, _IdxT> colmat, _IdxT col_shift);
    static void get_selected_cols_v3(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> origmat, _IdxT col_start, _IdxT col_end, COT_CSRRawMat<_ValT, _IdxT> colmat, _IdxT col_shift);
    static void csr_split_cols(const Device& dev, CSRMatStep step, const COT_CSRRawMat<_ValT, _IdxT> origmat, const _IdxT n, const _IdxT * part, COT_CSRRawMat<_ValT, _IdxT> * colmat_arr, _IdxT col_shift);
    static void get_col_element_count(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> mat, _IdxT n, _IdxT * counts);
    static void get_row_element_count(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> mat, _IdxT n, _IdxT * counts);
    static void csr_matadd_vec(const Device& dev, _IdxT rows, _IdxT nblks, const COT_CSRRawMat<_ValT, _IdxT> * A, COT_CSRRawMat<_ValT, _IdxT> C, _IdxT * w);
    static void csr_mat_fma_vec(const Device& dev, _IdxT rows, _IdxT nblks, const COT_CSRRawMat<_ValT, _IdxT> * A, const COT_CSRRawMat<_ValT, _IdxT> * B, COT_CSRRawMat<_ValT, _IdxT> C, _IdxT * w);
    static void csr_matadd_hash(const Device& dev, _ValT a, const COT_CSRRawMat<_ValT, _IdxT> A, _ValT b, const COT_CSRRawMat<_ValT, _IdxT> B, COT_CSRRawMat<_ValT, _IdxT> C, HashTableSlot<_IdxT, _IdxT> * tmp);
    static void csr_matadd(const Device& dev, _ValT a, const COT_CSRRawMat<_ValT, _IdxT> A, _ValT b, const COT_CSRRawMat<_ValT, _IdxT> B, COT_CSRRawMat<_ValT, _IdxT> C, COT_CSRRawMat<_ValT, _IdxT> tmp);
    static void csr_matmul_aDA(const Device& dev, _ValT a, const _ValT * D, COT_MergeCSRRawMat<_ValT, _IdxT> A);
    static void csr_matmul_aAD(const Device& dev, _ValT a, COT_SpMVCSRRawMat<_ValT, _IdxT> A);
    static void csr_axpby_diag(const Device& dev, _ValT a, const _ValT * x, _ValT b, const _ValT * y, const COT_MergeCSRRawMat<_ValT, _IdxT> A, COT_MergeCSRRawMat<_ValT, _IdxT> B);
    static void csr_append_rows(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, _IdxT row_start, _IdxT nnz_start, const COT_CSRRawMat<_ValT, _IdxT> B);
    static void csr_merge_rows(const Device& dev, _IdxT nblks, COT_MergeCSRRawMat<_ValT, _IdxT> * blks, COT_CSRRawMat<_ValT, _IdxT> dst);
    static void csr_merge_cols(const Device& dev, _IdxT nblks, COT_MergeCSRRawMat<_ValT, _IdxT> * blk, COT_CSRRawMat<_ValT, _IdxT> dst);
    static void get_element_value(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, _IdxT i, _IdxT j, _ValT * getval, int * success);
    static void set_element_value(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, _ValT * values, _IdxT i, _IdxT j, _ValT getval, int * success);
    static void csr_transpose(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, _IdxT * trans_row_ptr, _IdxT * trans_col_idx, _ValT * trans_values);
    static void csr_matmul(const Device& dev, const COT_CSRRawMat<_ValT, _IdxT> A, const COT_CSRRawMat<_ValT, _IdxT> B, COT_CSRRawMat<_ValT, _IdxT> C, _IdxT * work);
    static void csr_diag(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, const _IdxT * col_idx, const _ValT * values, _ValT * diag, _IdxT row_start, _IdxT col_start);
    static void csr_sort_rows(const Device& dev, _IdxT rows, _IdxT cols, const _IdxT * row_ptr, _IdxT * col_idx, _ValT * values);
    static void csr_sparsify(const Device& dev, COT_CSRRawMat<_ValT, _IdxT> A, typename TypeInfo<_ValT>::scalar_type threshold, const typename TypeInfo<_ValT>::scalar_type * thresh_array, COT_CSRRawMat<_ValT, _IdxT> ret);
    static void par_sor(const Device& dev, _IdxT rows, _IdxT myrank, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * blks, const _ValT * b, const _ValT * diag, _ValT * x, _ValT omega, int forward, const _IdxT * sweep_ordering);
    static void par_csr_diag(const Device& dev, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * blks, _ValT * diag);
    static void par_csr_row_norm_lp(const Device& dev, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * blks, typename TypeInfo<_ValT>::scalar_type p, typename TypeInfo<_ValT>::scalar_type * norm);
    static void par_csr_row_norm_topk(const Device& dev, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * blks, _IdxT k, COT_CSRRawMat<_ValT, _IdxT> mat);
    static void par_csr_row_meta(const Device& dev, _IdxT rows, _IdxT nblks, COT_SpMVCSRRawMat<_ValT, _IdxT> * blks, _IdxT * row_entries, _ValT * row_sum, int strict);
}; // end of class SpBlasOps
} // end of namespace hipo
