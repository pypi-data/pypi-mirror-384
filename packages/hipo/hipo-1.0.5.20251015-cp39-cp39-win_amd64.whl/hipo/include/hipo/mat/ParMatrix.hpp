#pragma once
#include "Matrix.hpp"
#include "hipo/operators/ParOperator_fwd.hpp"
#include "Partitioner.hpp"
#include <map>

namespace hipo {
template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API ParMatrixT {

public:
    typedef MatrixT<_ValT, _LocalIdxT> LocalType;

    ParMatrixT();
    ParMatrixT(_GlobalIdxT rows, const Device& device, MPI_Comm comm);
    ParMatrixT(_GlobalIdxT rows, _GlobalIdxT cols, const Device& device, MPI_Comm comm);
   
    void create(_GlobalIdxT rows, _GlobalIdxT cols, const Device& device, MPI_Comm comm);
    void create(_GlobalIdxT rows, const Device& device, MPI_Comm comm);
    void create(const PartitionerT<_GlobalIdxT, _LocalIdxT>& row_partition, const PartitionerT<_GlobalIdxT, _LocalIdxT>& col_partition, const Device& device, MPI_Comm comm);
    void create(const PartitionerT<_GlobalIdxT, _LocalIdxT>& row_partition, const Device& device, MPI_Comm comm);
    void createSeq(const MatrixT<_ValT, _LocalIdxT>& localMat, MPI_Comm comm);

    void resize(_GlobalIdxT rows, _GlobalIdxT cols, const Device& device, MPI_Comm comm);


    template <class _NewValT>
	void copyStructure(ParMatrixT<_NewValT, _GlobalIdxT, _LocalIdxT>& copy) const {
        auto&A = *this;
		copy.create(A.getRowPartitioner(), A.getColPartitioner(), A.getDevice(), A.getComm());
	}

    _GlobalIdxT getRows() const;
    _GlobalIdxT getCols() const;
    _GlobalIdxT getSize() const;
    Device getDevice() const;
    MPI_Comm getComm() const;


    _ValT* getData() const;

    void beginAssemble();
    void setValue(_GlobalIdxT i, _GlobalIdxT j, const _ValT& value, SetValueMode mode);
    void setValue(_GlobalIdxT i, const _ValT& value, SetValueMode mode = ADD_VALUE);
    template <class _IdxT>
    void setValues(_LocalIdxT n, const _IdxT* I, const _ValT* values, SetValueMode mode = ADD_VALUE) {
        for (_LocalIdxT i=0; i<n; i++) {
            setValue(I[i], values[i], mode);
        }
    }
    void endAssemble();

    template <class _Func, class _OutT>
    void map(_Func fun, ParMatrixT<_OutT, _GlobalIdxT, _LocalIdxT>& ret);
    
    ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT> getReal() const {
        ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT> ret;
        getReal(ret);
        return ret;
    }
    void getReal(ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT>& ret) const;
    ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT> getImag() const {
        ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT> ret;
        getImag(ret);
        return ret;
    }
    void getImag(ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT>& ret) const;
    void createComplex(const ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT>& real,
         const ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT>& imag);

    void getOwnerShipRange(_GlobalIdxT* start_row, _GlobalIdxT* end_row) const;
    _ValT getElementValue(_GlobalIdxT i, _GlobalIdxT j, bool* exists) const;
    bool setElementValue(_GlobalIdxT i, _GlobalIdxT j, const _ValT& value);

    void loadFromFile(const std::string& filename, const Device& device = Device(), MPI_Comm comm = MPI_COMM_WORLD);
	void loadFromStream(std::istream& ifs, const Device& device = Device(), MPI_Comm comm = MPI_COMM_WORLD);
	void saveToFile(const std::string& filename) const;
	void saveToStream(std::ostream& ofs) const;

    MatrixT<_ValT, _LocalIdxT> getLocalMatrix(int id = -1) const;
    void setLocalMatrix(const std::vector<MatrixT<_ValT, _LocalIdxT>>& localMat);
    PartitionerT<_GlobalIdxT, _LocalIdxT> getRowPartitioner() const;
    PartitionerT<_GlobalIdxT, _LocalIdxT> getColPartitioner() const;

    void fill(_ValT value);

    static void axpy(_ValT a, const ParMatrixT& x, ParMatrixT& y);
    static void axpby(_ValT a, const ParMatrixT& x, _ValT b, ParMatrixT& y);
    static void axpbypz(_ValT a, const ParMatrixT& x, _ValT b, const ParMatrixT& y, ParMatrixT& z);
    static void axpbypcz(_ValT a, const ParMatrixT& x, _ValT b, const ParMatrixT& y, _ValT c, ParMatrixT& z);

    static void axypbz(_ValT a, const ParMatrixT& x, const ParMatrixT& y, _ValT b, ParMatrixT& z);

    static void scale(_ValT a, ParMatrixT& x);

    ParMatrixT& operator*=(const _ValT& a) {
        auto& mat = *this;
        scale(a, mat);
        return mat;
    }

    bool operator==(const ParMatrixT& mat) const
	{
		CHECK(getComm() == mat.getComm());
		return getLocalMatrix() == mat.getLocalMatrix();
	}

    static void reciprocal(_ValT a, ParMatrixT& x);
    static void pow(_ValT a, ParMatrixT& x);

    static void residual_vec(ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& A,
     const ParMatrixT &x, const ParMatrixT &b, ParMatrixT &r);
    static typename TypeInfo<_ValT>::scalar_type residual(ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& A,
     const ParMatrixT &x, const ParMatrixT &b, ParMatrixT &r);
    static typename TypeInfo<_ValT>::scalar_type residual(ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>& A,
     const ParMatrixT &x, const ParMatrixT &b);

    static _ValT dot(const ParMatrixT& x, const ParMatrixT& y);
    static typename TypeInfo<_ValT>::scalar_type normL2(const ParMatrixT& x);
    static typename TypeInfo<_ValT>::scalar_type normL1(const ParMatrixT& x);
    static typename TypeInfo<_ValT>::scalar_type absSum(const ParMatrixT& x, typename TypeInfo<_ValT>::scalar_type order);
    static typename TypeInfo<_ValT>::scalar_type absMax(const ParMatrixT& x);


    void min_max_sum(_ValT* min, _ValT* max, _ValT* sum) const;

    ParMatrixT deepCopy() const;

    void deepCopy(ParMatrixT& ret) const;

    template <class _NewValT>
    void toType(ParMatrixT<_NewValT, _GlobalIdxT, _LocalIdxT>& ret) const {
        auto local_mat = ret.getLocalMatrix();
        getLocalMatrix().toType(local_mat);
    }

    void toDevice(Device device, ParMatrixT& ret) const;
    ParMatrixT toDevice(Device device) const;

    void createByAssemble(const MatrixT<_ValT, _GlobalIdxT>& localMat, MPI_Comm comm);

    void scatter(MPI_Comm comm, int root, const MatrixT<_ValT, _LocalIdxT>& localMat,
     const PartitionerT<_GlobalIdxT, _LocalIdxT> *rowpart = 0,
     const PartitionerT<_GlobalIdxT, _LocalIdxT> *colpart = 0);

    MatrixT<_ValT, _LocalIdxT> gather(int root) const;

    _LocalIdxT getLocalRows() const;
protected:
    class ParMatrixImpl;
    std::shared_ptr<ParMatrixImpl> m_impl;
};



}
