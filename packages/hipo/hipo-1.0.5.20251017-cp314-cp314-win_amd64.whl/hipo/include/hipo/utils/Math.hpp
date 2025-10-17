#pragma once

#include <cmath>
#include <regex>
#include <cstdlib>
#include <type_traits>
#include <float.h>
#include <limits.h>
#include "Complex.hpp"

namespace hipo {


class MatrixLayoutRowMajor {};
class MatrixLayoutColMajor {};

#define IS_INTEGER_TYPE(V) (std::is_same<V, int>::value || std::is_same<V, int64_t>::value)
#define IS_SCALAR_TYPE(V) (std::is_same<V, float>::value || std::is_same<V, double>::value)
#define IS_STRING_TYPE(V) (std::is_same<V, std::string>::value)
#define IS_COMPLEX_TYPE(V) (std::is_same<V, hipo::Complex<float>>::value || std::is_same<V, hipo::Complex<double>>::value)
#define IS_NUMERIC_TYPE(V) (IS_SCALAR_TYPE(V) || IS_COMPLEX_TYPE(V))
#define IS_INSTANTIATION_TYPE(V) (IS_INTEGER_TYPE(V) || IS_SCALAR_TYPE(V) || IS_COMPLEX_TYPE(V))

class HIPO_WIN_API Math {
public:
	// 数值比较
	template <class _ValT>
	static typename TypeInfo<_ValT>::scalar_type realmin();
	template <class _ValT>
	static typename TypeInfo<_ValT>::scalar_type realmax();

	template <class _ValT>
	static typename TypeInfo<_ValT>::scalar_type eps(_ValT x = _ValT(1));

	template <class _ValT>
	static int precision() {
		if constexpr (IS_NUMERIC_TYPE(_ValT)) {
			return std::ceil(-std::log10(Math::eps(_ValT(1))));
		} else {
			return 7;
		}
	}
    template <class _ValT>
	static bool numericalEqual(const _ValT& x, const _ValT&  y, typename TypeInfo<_ValT>::scalar_type factor);

	template <class _ValT>
	static _ValT rand() {
		_ValT val = 0;
		if constexpr (std::is_same_v<_ValT, float> || std::is_same_v<_ValT, double>) {
			val = std::rand() * _ValT(1) / _ValT(RAND_MAX);
		}
		else if constexpr (std::is_same_v<_ValT, Complex<float>> || std::is_same_v<_ValT, Complex<double>>) {
			typedef decltype(val.real) Real;
			val.real = std::rand() * Real(1) / Real(RAND_MAX);
			val.imag = std::rand() * Real(1) / Real(RAND_MAX);
		}
		else if constexpr (std::is_same_v<_ValT, int32_t> || std::is_same_v<_ValT, int64_t>) {
			val = std::rand();
		} else {
			val = std::rand();
		}
		return val;
	}


	template <class _ValT>
	SPM_ATTRIBUTE static _ValT max() {
		if constexpr(std::is_same<_ValT, float>::value) {
			return FLT_MAX;
		}
		else if constexpr(std::is_same<_ValT, double>::value) {
			return DBL_MAX;
		}
		else if constexpr(std::is_same<_ValT, int32_t>::value) {
			return INT_MAX;
		}
		else if constexpr(std::is_same<_ValT, int64_t>::value) {
			return LONG_MAX;
		} else {
			return _ValT();
		}
	}
	template <class _ValT>
	SPM_ATTRIBUTE static _ValT min() {
		if constexpr(std::is_same<_ValT, float>::value) {
			return FLT_MIN;
		}
		else if constexpr(std::is_same<_ValT, double>::value) {
			return DBL_MIN;
		}
		else if constexpr(std::is_same<_ValT, int32_t>::value) {
			return INT_MIN;
		}
		else if constexpr(std::is_same<_ValT, int64_t>::value) {
			return LONG_MIN;
		} else {
			return _ValT();
		}
	}
	
};



inline float math_realmin(float)
{
	return std::ldexp((float)1.0, -126);
}

inline double math_realmin(double)
{
	return std::ldexp((double)1.0, -1022);
}
template <class T>
inline T math_realmin(Complex<T> x) {
	return math_realmin(x.real);
}



inline float math_realmax(float)
{
	float f = std::ldexp((float)1.0, -23);
	return std::ldexp((float)(2.0 - f), 127);
}

inline double math_realmax(double)
{
	double f = std::ldexp((double)1.0, -52);
	return std::ldexp((double)(2.0 - f), 1023);
}

template <class T>
inline T math_realmax(Complex<T> x) {
	return math_realmax(x.real);
}

inline float math_eps(float x)
{
	float abs = std::abs(x);
	if (abs <= math_realmin(x))
		return std::ldexp((float) 1.0, -149);
	else
	{
		int exp;
		std::frexp(abs, &exp);
		return std::ldexp((float) 1.0, exp - 24);
	}
}

inline double math_eps(double x)
{
	double abs = std::abs(x);
	if (abs <= math_realmin(x))
		return std::ldexp((double)1.0, -1074);
	else
	{
		int exp;
		std::frexp(abs, &exp);
		return std::ldexp((double)1.0, exp - 53);
	}
}

template <class T>
inline T math_eps(Complex<T> x) {
	return hipo::math_eps(abs(x));
}

template <class T>
inline T math_eps(T x) {
	return 0;
}

template <class _ValT>
typename TypeInfo<_ValT>::scalar_type Math::eps(_ValT x) {
	return hipo::math_eps(x);
}

template <class _ValT>
typename TypeInfo<_ValT>::scalar_type Math::realmin() {
	_ValT x = 0;
	return math_realmin(x);
}

template <class _ValT>
typename TypeInfo<_ValT>::scalar_type Math::realmax() {
	_ValT x = 0;
	return math_realmax(x);
}

template <class _ValT>
bool Math::numericalEqual(const _ValT& x, const _ValT&  y, typename TypeInfo<_ValT>::scalar_type factor)
{
	// FIXED bug here, factor = 0.0 will be included
	// Find bug here, there is problems when x and y are less than 1.0
	auto absx = hipo::abs(x);
	absx = (absx == 0) ? 1 : absx;
	if (hipo::abs(x - y) > factor * eps(absx))
		return false;
	else
		return true;
}

}
