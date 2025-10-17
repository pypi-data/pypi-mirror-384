
#pragma once

#include <cmath>
#include "hipo/spm/MultiArch.hpp"
#include "Utils.hpp"

namespace hipo
{

#define ATTRIBUTE SPM_ATTRIBUTE


template <class _ValT>
struct Complex
{
	_ValT real;
	_ValT imag;

	ATTRIBUTE Complex(_ValT re = _ValT(0), _ValT im = _ValT(0))
		: real(re),
		imag(im)
	{
	}

	ATTRIBUTE Complex(const Complex &a)
		: real(a.real),
		imag(a.imag)
	{
	}

	template <class _NewValT>
	ATTRIBUTE Complex(const Complex<_NewValT> &a)
		: real(_ValT(a.real)),
		imag(_ValT(a.imag))
	{
	}

	ATTRIBUTE Complex operator+() const
	{
		return *this;
	}

	ATTRIBUTE Complex operator-() const
	{
		return Complex(-real, -imag);
	}

	ATTRIBUTE Complex operator+(const _ValT& a) const
	{
		return Complex(real + a, imag);
	}

	ATTRIBUTE Complex operator-(const _ValT& a) const
	{
		return Complex(real - a, imag);
	}

	ATTRIBUTE Complex operator*(const _ValT& a) const
	{
		return Complex(real * a, imag * a);
	}

	ATTRIBUTE Complex operator/(const _ValT& a) const
	{
		return Complex(real / a, imag / a);
	}

	ATTRIBUTE Complex operator+(const Complex& a) const
	{
		return Complex(real + a.real, imag + a.imag);
	}

	ATTRIBUTE Complex operator-(const Complex& a) const
	{
		return Complex(real - a.real, imag - a.imag);
	}

	ATTRIBUTE Complex operator*(const Complex& a) const
	{
		return Complex(real * a.real - imag * a.imag, real * a.imag + imag * a.real);
	}

	ATTRIBUTE Complex operator/(const Complex& a) const
	{
		_ValT denom = _ValT(1.0) / (a.real * a.real + a.imag * a.imag);
		return Complex((real * a.real + imag * a.imag) * denom, (-real * a.imag + imag * a.real) * denom);
	}

	ATTRIBUTE Complex& operator+=(const _ValT& a)
	{
		real += a;
		return *this;
	}

	ATTRIBUTE Complex& operator-=(const _ValT& a)
	{
		real -= a;
		return *this;
	}

	ATTRIBUTE Complex& operator*=(const _ValT& a)
	{
		real *= a;
		imag *= a;
		return *this;
	}

	ATTRIBUTE Complex& operator/=(const _ValT& a)
	{
		real /= a;
		imag /= a;
		return *this;
	}
	
	ATTRIBUTE Complex& operator+=(const Complex& a)
	{
		real += a.real;
		imag += a.imag;
		return *this;
	}

	ATTRIBUTE Complex& operator-=(const Complex& a)
	{
		real -= a.real;
		imag -= a.imag;
		return *this;
	}

	ATTRIBUTE Complex& operator*=(const Complex& a)
	{
		_ValT temp = real * a.real - imag * a.imag;
		imag = real * a.imag + imag * a.real;
		real = temp;
		return *this;
	}

	ATTRIBUTE Complex& operator/=(const Complex& a)
	{
		_ValT denom = _ValT(1.0) / (a.real * a.real + a.imag * a.imag);
		_ValT temp = (real * a.real + imag * a.imag) * denom;
		imag = (-real * a.imag + imag * a.real) * denom;
		real = temp;
		return *this;
	}

	ATTRIBUTE bool operator==(const _ValT& a) const
	{
		return real == a && imag == 0;
	}

	ATTRIBUTE bool operator!=(const _ValT& a) const
	{
		return real != a || imag != 0;
	}

	ATTRIBUTE bool operator==(const Complex& a) const
	{
		return real == a.real && imag == a.imag;
	}

	ATTRIBUTE bool operator!=(const Complex& a) const
	{
		return real != a.real || imag != a.imag;
	}

	ATTRIBUTE Complex& operator=(const _ValT& a)
	{
		real = a;
		imag = 0.0;
		return *this;
	}

	ATTRIBUTE Complex& operator=(const Complex& a)
	{
		real = a.real;
		imag = a.imag;
		return *this;
	}

	template <class _NewValT>
	ATTRIBUTE Complex& operator=(const Complex<_NewValT>& a)
	{
		real = _ValT(a.real);
		imag = _ValT(a.imag);
		return *this;
	}
};


template <class _ValT>
inline ATTRIBUTE _ValT real(const _ValT& a)
{
	return a;
}
template <class _ValT>
inline ATTRIBUTE _ValT real(const Complex<_ValT>& a)
{
	return a.real;
}
template <class _ValT>
inline ATTRIBUTE _ValT imag(const _ValT& a)
{
	return 0;
}
template <class _ValT>
inline ATTRIBUTE _ValT imag(const Complex<_ValT>& a)
{
	return a.imag;
}


template <class _ValT>
inline ATTRIBUTE _ValT abs(const _ValT& a)
{
	return std::abs(a);
}

template <class _ValT>
inline ATTRIBUTE _ValT abs(const Complex<_ValT>& a)
{
	return std::sqrt(a.real * a.real + a.imag * a.imag);
}

template <class _ValT>
inline ATTRIBUTE _ValT abs2(const _ValT& a)
{
	return a*a;
}

template <class _ValT>
inline ATTRIBUTE _ValT abs2(const Complex<_ValT>& a)
{
	return a.real * a.real + a.imag * a.imag;
}

template <class _ValT>
inline ATTRIBUTE _ValT pow(const _ValT& a, _ValT e)
{
	return std::pow(a, e);
}

#if 0
template <class _ValT>
inline ATTRIBUTE Complex<_ValT> pow(const Complex<_ValT>& a, Complex<_ValT> e)
{
	// FIXME: error
	return a;
}
#endif

template <typename _Tp>
inline ATTRIBUTE _Tp arg(const Complex<_Tp> &__z) {
    return std::atan2(__z.imag, __z.real);
}

template <typename _Tp>
inline ATTRIBUTE _Tp arg(const _Tp &__z) {
    return 0;
}

template <typename _Tp>
inline ATTRIBUTE Complex<_Tp> polar(const _Tp &__rho, const _Tp &__theta) {
    //assert(__rho >= 0);
    return Complex<_Tp>(__rho * std::cos(__theta), __rho * std::sin(__theta));
}

template <typename _Tp>
inline ATTRIBUTE Complex<_Tp> log(const Complex<_Tp> &__z) {
    return Complex<_Tp>(std::log(abs(__z)), arg(__z));
}

template <typename _Tp>
inline ATTRIBUTE Complex<_Tp> exp(const Complex<_Tp> &__z) {
    return polar<_Tp>(std::exp(__z.real), __z.imag);
}

template <typename _Tp>
inline ATTRIBUTE Complex<_Tp> pow(const Complex<_Tp> &__x, const _Tp &__y) {
    if (__x == _Tp()) {
        return _Tp();
    }

    if (__x.imag == _Tp() && __x.real > _Tp())
        return pow(__x.real, __y);

    Complex<_Tp> __t = log(__x);
    return polar<_Tp>(exp(__y * __t.real), __y * __t.imag);
}

template <typename _Tp>
inline ATTRIBUTE Complex<_Tp> pow(const Complex<_Tp> &__x, const Complex<_Tp> &__y) {
    return __x == _Tp() ? _Tp() : exp(__y * log(__x));
}


template <class _ValT>
inline ATTRIBUTE _ValT conj(const _ValT& a)
{
	return a;
}

template <class _ValT>
inline ATTRIBUTE Complex<_ValT> conj(const Complex<_ValT>& a)
{
	return Complex<_ValT>(a.real, -a.imag);
}

template <class _ValT>
inline ATTRIBUTE _ValT sqrt(const _ValT& a) {
	return std::sqrt(a);
}

template <class _ValT>
inline ATTRIBUTE Complex<_ValT> sqrt(const Complex<_ValT>& a)
{
	if (a.real > 0)
	{
		_ValT temp = std::sqrt(_ValT(0.5) * (abs(a) + a.real));
		return Complex(temp, _ValT(0.5) * a.imag / temp);
	}
	else
	{
		_ValT temp = std::sqrt(_ValT(0.5) * (abs(a) - a.real));
		if (a.imag >= 0)
			return Complex(_ValT(0.5) * a.imag / temp, temp);
		else
			return Complex(_ValT(-0.5) * a.imag / temp, -temp);
	}
}


template <class ValT>
struct TypeInfo {
    using scalar_type = ValT;
    enum { is_complex = false };
};


template <class ValT>
struct TypeInfo<Complex<ValT>> {
    using scalar_type = ValT;
    enum { is_complex = true };
};


template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator * (const Complex<_ValT>& a, const _ValT& b) {
    Complex<_ValT> ret = a;
	ret.real *= b;
	ret.imag *= b;
	return ret;
}

template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator * (const _ValT& a, const Complex<_ValT>& b) {
	return b*a;
}

template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator + (const Complex<_ValT>& a, const _ValT& b) {
    Complex<_ValT> ret = a;
	ret.real += b;
	return ret;
}

template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator + (const _ValT& a, const Complex<_ValT>& b) {
    Complex<_ValT> ret = b;
	ret.real += a;
	return ret;
}

template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator - (const Complex<_ValT>& a, const _ValT& b) {
    Complex<_ValT> ret = a;
	ret.real -= b;
	return ret;
}

template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator - (const _ValT& a, const Complex<_ValT>& b) {
    Complex<_ValT> ret;
	ret.real = a - b.real;
	ret.imag = -b.imag;
	return ret;
}

template <class _ValT>
SPM_ATTRIBUTE bool operator < (const Complex<_ValT>& a, const Complex<_ValT>& b) {
    return ((a.real) < (b.real));
}
template <class _ValT>
SPM_ATTRIBUTE bool operator <= (const Complex<_ValT>& a, const Complex<_ValT>& b) {
    return a.real <= b.real;
}

template <class _ValT>
SPM_ATTRIBUTE bool operator > (const Complex<_ValT>& a, const Complex<_ValT>& b) {
    return a.real > b.real;
}
template <class _ValT>
SPM_ATTRIBUTE bool operator >= (const Complex<_ValT>& a, const Complex<_ValT>& b) {
    return a.real >= b.real;
}

template <class _ValT>
SPM_ATTRIBUTE Complex<_ValT> operator / (double a, const Complex<_ValT>& b) {
    return Complex<_ValT>((_ValT)a) / b;
}

}


#include <iostream>
namespace std {
template <class _ValT>
std::basic_istream<char> &operator>>(std::basic_istream<char>& is, hipo::Complex<_ValT>& a) {
    if (hipo::Utils::isStrictMatrixMarket()) {
        is >> a.real >> a.imag;
    } else {
        is >> a.real;
        char sign = ' ';
        is >> sign;
        if (sign == '+' || sign == '-') {
            char j;
            _ValT imag;
            is >> j >> imag;
            a.imag = sign == '+' ? imag : -imag;
        } else {
            is.putback(sign);
            a.imag = 0;
        }
    }
    return is;
}

template <class _ValT>
std::basic_ostream<char> & operator<<(std::basic_ostream<char> & os, const hipo::Complex<_ValT>& a)
{
    if (hipo::Utils::isStrictMatrixMarket()) {
        os << a.real << " " << a.imag;
    } else {
        char sign = '+';
		auto imag = a.imag;
		if (a.imag < 0) {
			sign = '-';
			imag = -imag;
		}
        os << a.real << sign << "j" << imag;
    }
    return os;
}
}

