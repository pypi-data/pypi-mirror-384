#pragma once
#include "Range.hpp"
#include "hipo/utils/Math.hpp"

namespace hipo {
namespace spm {

template <class ValT, class Space>
class Sum {
public:
    typedef ValT value_type;
    ValT& value;
    ValT init = 0;
    SPM_ATTRIBUTE Sum(ValT& v): value(v) {}
    SPM_ATTRIBUTE void reduce(const ValT& v1, const ValT& v2, ValT& ret) const {
        ret = v1 + v2;
    }
};

template <class ValT, class Space>
class Min {
public:
    typedef ValT value_type;
    ValT& value;
    ValT init = Math::max<ValT>();
    SPM_ATTRIBUTE Min(ValT& v): value(v) {}
    SPM_ATTRIBUTE void reduce(const ValT& v1, const ValT& v2, ValT& ret) const {
        ret = v1 < v2 ? v1 : v2;
    }
};

template <class ValT, class Space>
class Max {
    public:
    typedef ValT value_type;
    ValT& value;
    ValT init = Math::min<ValT>();
    SPM_ATTRIBUTE Max(ValT& v): value(v) {}
    SPM_ATTRIBUTE void reduce(const ValT& v1, const ValT& v2, ValT& ret) const {
        ret = v1 > v2 ? v1 : v2;
    }
};


template <class Space, class Functor, class ValT>
void parallel_reduce(const RangePolicy<Space>& policy, const Functor& functor, ValT& val) {
    parallel_reduce(policy, functor, Sum<ValT, Space>(val));
}

}
}
