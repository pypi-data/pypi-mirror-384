
#pragma once


#include "hipo/utils/Complex.hpp"
#include "hipo/utils/Device.hpp"



namespace hipo {
template <class _ValT, class _IdxT>
class HIPO_WIN_API BlasOps {
public:
    static void fill(const Device& dev, _IdxT n, _ValT a, _ValT * x);
    static void scal(const Device& dev, _IdxT n, _ValT a, _ValT * x);
    static void copy(const Device& dev, _IdxT n, const _ValT * x, _ValT * y);
    static void axpy(const Device& dev, _IdxT n, _ValT a, const _ValT * x, _ValT * y);
    static void axpby(const Device& dev, _IdxT n, _ValT a, const _ValT * x, _ValT b, _ValT * y);
    static void axpbypz(const Device& dev, _IdxT n, _ValT a, const _ValT * x, _ValT b, const _ValT * y, _ValT * z);
    static void axypbz(const Device& dev, _IdxT n, _ValT a, const _ValT * x, const _ValT * y, _ValT b, _ValT * z);
    static void axpbypcz(const Device& dev, _IdxT n, _ValT a, const _ValT * x, _ValT b, const _ValT * y, _ValT c, _ValT * z);
    static _ValT dot(const Device& dev, _IdxT n, const _ValT * x, const _ValT * y);
    static _ValT dotu(const Device& dev, _IdxT n, const _ValT * x, const _ValT * y);
    static void reciprocal(const Device& dev, _IdxT n, _ValT a, _ValT * x);
    static void pow(const Device& dev, _IdxT n, _ValT a, _ValT * x);
    static typename TypeInfo<_ValT>::scalar_type abs_max(const Device& dev, _IdxT n, const _ValT * x);
    static typename TypeInfo<_ValT>::scalar_type abs_sum(const Device& dev, _IdxT n, const _ValT * x, typename TypeInfo<_ValT>::scalar_type order);
    static void get_nonzero_indices(const Device& dev, _IdxT n, const _ValT * x, _IdxT * idxLen, _IdxT * indices);
    static void get_real(const Device& dev, _IdxT n, const _ValT * x, typename TypeInfo<_ValT>::scalar_type * real);
    static void get_imag(const Device& dev, _IdxT n, const _ValT * x, typename TypeInfo<_ValT>::scalar_type * imag);
    static void create_complex(const Device& dev, _IdxT n, const _ValT * real, const _ValT * imag, Complex<_ValT> * complex);
    static void min_max_sum(const Device& dev, _IdxT n, const _ValT * x, _ValT * min, _ValT * max, _ValT * sum);
    static void adamw_step(const Device& dev, _IdxT n, const _ValT * g, _ValT * theta, _ValT * m, typename TypeInfo<_ValT>::scalar_type * v, typename TypeInfo<_ValT>::scalar_type * vmax, _ValT gamma, typename TypeInfo<_ValT>::scalar_type beta1, typename TypeInfo<_ValT>::scalar_type beta2, typename TypeInfo<_ValT>::scalar_type epsilon, _ValT lambda, _IdxT amsgrad, _IdxT step);
    static void remove_empty_rows(const Device& dev, _IdxT orig_rows, _IdxT * row_ptr, _IdxT * rows, _IdxT * global2local);
}; // end of class BlasOps
} // end of namespace hipo
