#pragma once

namespace hipo {
    // 跨设备的类型，用于直接在device和host之间传递数据。


    template <class _ValT, class _IdxT>
	struct COT_CSRRawMat
	{
		_IdxT rows = 0;
		_IdxT cols = 0;
		_IdxT nnzs = 0;
        _IdxT* row_ptr = 0;
		_IdxT* row_ptr_end = 0;
		_IdxT* col_idx = 0;
        _ValT* values = 0;
	};

    template <class _ValT, class _IdxT>
    struct COT_MergeCSRRawMat : public COT_CSRRawMat<_ValT, _IdxT> {
        _IdxT row_start = 0;
        _IdxT col_start = 0;
    };

    template <class _ValT, class _IdxT>
    struct COT_SpMVCSRRawMat : public COT_MergeCSRRawMat<_ValT, _IdxT> {
        int procId = -1;
        _ValT* recv_x = 0;
        _ValT* local_y = 0;
    };

    template <class _IdxT>
    struct AggregateData {
        _IdxT procId = -1;
        _IdxT localId = -1;
        _IdxT clusterId = -1;
    };
    enum AggregateStep {
        AGGR_INIT = 0,
        AGGR_COMPUTE_LOC_REM = 1,
        AGGR_WRITE_BACK=2
    };
    enum CoarsenPMISStep {
        PMIS_INIT = 0,
        PMIS_INIT_2 = 10,

        PMIS_PICK_INDEP_SET = 1,
        PMIS_SET_COARSE_FINE = 2,
        PMIS_UPDATE_SUBGRAPH=3
    };

    template <class _KeyT, class _ValT>
    struct HashTableSlot {
        _KeyT key;
        _ValT value;
        char status = 0;
    };


    template <class _ValT, class _IdxT>
	struct COT_RawMat
	{
		_IdxT rows = 0;
		_IdxT cols = 0;
        _ValT* data = 0;
	};

    template <class _ValT, class _IdxT>
	struct COT_RawCommPattern {
        _IdxT procId = -1;
        _IdxT size = 0;
        _IdxT nzc_size = 0;
        _ValT* recv_x = 0;
        _IdxT col_start = 0;
        _IdxT* nzc_recv_indices = 0;
        _IdxT* recv_write_flag = 0;
    };

    enum CSRMatStep {
        CSRMAT_CALC_NNZ,
        CSRMAT_FILL_NNZ
    };
    enum LUDecompStep {
        LU_NUMERICAL_DECOMP = 1,
        LU_BACK_SOLVE = 2,
    };
    enum CholeskyDecompStep {
        CHOL_NUMERICAL_DECOMP = 1,
        CHOL_BACK_SOLVE = 2,
    };
}

