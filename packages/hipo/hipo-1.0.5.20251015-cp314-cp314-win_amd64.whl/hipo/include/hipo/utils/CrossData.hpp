#pragma once
#include "hipo/mat/Matrix.hpp"

namespace hipo {

template <class _ValT>
class CrossData {
    MatrixT<_ValT, HIPO_INT> _host;
    MatrixT<_ValT, HIPO_INT> _dev;
public:
    CrossData(const Device& dev, const _ValT& ival = 0) {
        Device cpu;
        _host.create(1, cpu);
        _dev.create(1, dev);
        _host.fill(ival);
        _dev.fill(ival);
    }
    void toHost() {
        _dev.toDevice(_host.getDevice(), _host);
    }
    void toDevice() {
        _host.toDevice(_dev.getDevice(), _dev);
    }
    _ValT& host() {
        return *_host.getData();
    }
    _ValT* device() {
        return _dev.getData();
    }
    CrossData& operator=(const _ValT& d) {
        _host.fill(d);
        _dev.fill(d);
        return *this;
    }
};


}