#pragma once

#include "hipo/operators/ParOperator.hpp"
#include "hipo/mat/ParCSRMatrix.hpp"

namespace hipo {

template <typename _ValT, typename _GlobalIdxT, typename _LocalIdxT=_GlobalIdxT>
class HIPO_WIN_API TestCaseT : public virtual ParOperator {
protected:
    Device device;
    int myrank = 0;
    int nprocs = 1;
    MPI_Comm comm = MPI_COMM_WORLD;
public:
    void setDeviceAndComm(const Device& device, MPI_Comm comm) {
        this->comm = comm;
        this->device = device;
        MPI_Comm_size(comm, &nprocs);
        MPI_Comm_rank(comm, &myrank);
    }
    int create(const JsonValue& params) {
        std::string device_str;
        FACTORY_GET_JSON_VAL(device_str, "device", std::string);
        if (device_str.size() > 0) {
            this->device = Device(device_str);
        }
        return 0;
    }

    static Factory<TestCaseT> *getFactory();
    virtual void generate(ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& A,
                ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>& x,
                ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>& b) =  0;
};



template <class ValT, class IdxT>
struct DofMapND {
    typedef IdxT IntType;
    typedef std::vector<IdxT> IntVector;
    typedef std::vector<ValT> ValVector;

    IntVector ndofs;
    IntVector ndofs_acc;
    IdxT dim_;
    DofMapND(const IntVector& dofs) {
        ndofs = dofs;
        dim_ = dofs.size();
        ndofs_acc.resize(dim_+1);
        IdxT prod = 1;
        ndofs_acc[0] = prod;
        for (IdxT i=0; i<dim_; i++) {
            assert(dofs[i] >= 2);
            prod *= dofs[i];
            ndofs_acc[i+1] = prod;
        }
    }
    void idx2grid(IdxT idx, IntVector& dofs) {
        dofs.resize(dim_);
        for (IdxT i=dim_-1; i>=0; i--) {
            dofs[i] = idx / ndofs_acc[i];
            idx -= dofs[i] * ndofs_acc[i];
        }
    }
    IdxT grid2idx(const IntVector& dofs) {
        IdxT sum = 0;
        for (IdxT i=0; i<dim_; i++) {
            sum += dofs[i] * ndofs_acc[i];
        }
        return sum;
    }
    IdxT operator()(const IntVector& dofs) {
        return grid2idx(dofs);
    }
    IdxT size() {
        return ndofs_acc[dim_];
    }
    IdxT dim() {
        return dim_;
    }
    IdxT dof(int dim) {
        return ndofs[dim];
    }

    ValVector getDelta() {
        ValVector delta(dim_);
        for (int i=0; i<dim_; i++) {
            double span = ndofs[i]-1;
            delta[i] = 1. / span;
        }
        return delta;
    }
    bool isBoundary(const IntVector& dofs) {
        bool is_boundary = false;
        for (int i=0; i<dim_; i++) {
            if (dofs[i] == 0 || dofs[i] == ndofs[i]-1) {
                is_boundary = true;
                break;
            }
        }
        return is_boundary;
    }
};

template <typename _ValT, typename _GlobalIdxT, typename _LocalIdxT>
class PoissonFDM_T : public TestCaseT<_ValT, _GlobalIdxT, _LocalIdxT> {

public:

    int dim = 2;
    int N = 100;
    std::string rhs = "sin(pi*x)";
    std::vector<int> size;
    std::vector<double> low, high;
    int create(const JsonValue& params) {
        TestCaseT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params);
        FACTORY_GET_JSON_VAL(dim, "dim", int);
        FACTORY_GET_JSON_VAL(N, "N", int);
        FACTORY_GET_JSON_VAL(rhs, "rhs", std::string);
        return 0;
    }
    
    virtual void generate(ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& A,
                ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>& x,
                ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>& b);
};


template <typename _ValT, typename _GlobalIdxT, typename _LocalIdxT>
class MatrixMarket_T : public TestCaseT<_ValT, _GlobalIdxT, _LocalIdxT> {

public:

    std::string filename_A;
    std::string filename_b;
    std::string filename_x;


    int create(const JsonValue& params) {
        TestCaseT<_ValT, _GlobalIdxT, _LocalIdxT>::create(params);
        FACTORY_GET_JSON_VAL(filename_A, "filename_A", std::string);
        FACTORY_GET_JSON_VAL(filename_b, "filename_b", std::string);
        FACTORY_GET_JSON_VAL(filename_x, "filename_x", std::string);
        return 0;
    }
    virtual void generate(ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& A,
                ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>& x,
                ParVectorT<_ValT, _GlobalIdxT, _LocalIdxT>& b);
};

}
