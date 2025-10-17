#pragma once

#include <boost/rational.hpp>
#include <boost/multiprecision/cpp_bin_float.hpp>



namespace hipo {

using cpp_rational_t = boost::rational<int64_t>;
using cpp_bin_float_t = boost::multiprecision::cpp_bin_float_100;

}


namespace std {
    using namespace hipo;
    inline cpp_bin_float_t abs(const cpp_bin_float_t& x) {
        return boost::multiprecision::abs(x);
    }

    inline cpp_rational_t abs(const cpp_rational_t& x) {
        return boost::abs(x);
    }

    inline cpp_bin_float_t sqrt(const cpp_bin_float_t& x) {
        return boost::multiprecision::sqrt(x);
    }
}
