#pragma once

#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"
#include "hipo/utils/TickMeter.hpp"
#include <smumps_c.h>
#include <dmumps_c.h>
#include <cmumps_c.h>
#include <zmumps_c.h>

namespace hipo {



template <class _ValT>
struct MumpsWrapper {
    typedef void value;
};

template <>
struct MumpsWrapper<float> {
    typedef SMUMPS_STRUC_C struc_c;
    typedef float val_type;
    static void mumps_c(struc_c * id ) {
        smumps_c(id);
    }
};

template <>
struct MumpsWrapper<double> {
    typedef DMUMPS_STRUC_C struc_c;
    typedef double val_type;
    static void mumps_c(struc_c * id ) {
        dmumps_c(id);
    }
};

template <>
struct MumpsWrapper<Complex<float>> {
    typedef CMUMPS_STRUC_C struc_c;
    typedef mumps_complex val_type;
    static void mumps_c(struc_c * id ) {
        cmumps_c(id);
    }
};

template <>
struct MumpsWrapper<Complex<double>> {
    typedef ZMUMPS_STRUC_C struc_c;
    typedef mumps_double_complex val_type;
    static void mumps_c(struc_c * id ) {
        zmumps_c(id);
    }
};

template <class _ValT, class _GlobalIdxT, class _LocalIdxT, class _PValT=_ValT>
class SolverMUMPS_T : public ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT> {

public:

    typename MumpsWrapper<_ValT>::struc_c id;

    ParCSRMatrixT<_PValT, _GlobalIdxT, _LocalIdxT> matA;
    CSRMatrixT<_PValT, _LocalIdxT> csrA;

    MatrixT<_LocalIdxT, _LocalIdxT> rowIdx, colIdx;
    MatrixT<_ValT, _LocalIdxT> values;

    TickMeter tm_fact, tm_solve;
    SolverMUMPS_T();
    ~SolverMUMPS_T();


    void csrArrayToCoo(_LocalIdxT nrows, _LocalIdxT nblks, COT_SpMVCSRRawMat<_ValT, _LocalIdxT> *blks,
        _LocalIdxT *rowIdx, _LocalIdxT* colIdx, _ValT* values, _LocalIdxT base = 0);

    void setup(const ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A);

    int create(const JsonValue &params) {
        ParSolverT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params, "MUMPS");
        return 0;
    }

    void solve(ParPreconditionerT<_PValT, _GlobalIdxT, _LocalIdxT> &P,
               ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT> &A,
               const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &b,
               ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, int &iter,
               double &relres);
};

} // namespace hipo
