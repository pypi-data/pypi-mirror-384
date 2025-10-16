#pragma once
#include "hipo/utils/Math.hpp"
namespace hipo {

template <class _ValT, class _IdxT, class _Layout=MatrixLayoutRowMajor>
class MatrixT;

template <class _ValT, class _IdxT>
using VectorT = MatrixT<_ValT, _IdxT>;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParMatrixT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
using ParVectorT = ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>;


template<typename _ValT, typename _GlobalIdxT, typename _LocalIdxT>
class ParCSRMatrixT;

}