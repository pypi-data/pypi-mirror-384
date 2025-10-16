#pragma once


namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParMatrixFreeT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParCSRMatrixT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParPreconditionerT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSolverT;


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParSmootherT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParOpBaseT;


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParRestrictionerT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParProlongationerT;


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParLevelTransferT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParCoarsenerT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParInterpolatorT;


template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParAggretatorT;


}