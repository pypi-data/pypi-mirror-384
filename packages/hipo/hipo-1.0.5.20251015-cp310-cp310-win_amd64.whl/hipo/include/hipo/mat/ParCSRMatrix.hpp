#pragma once


#include "ParMatrix.hpp"
#include "CSRMatrix.hpp"
#include "Partitioner.hpp"
#include "hipo/ops/CrossOpTypes.hpp"
#include "hipo/operators/ParOperator.hpp"
#include "SpMVCommPattern.hpp"

namespace hipo {

template<typename _ValT, typename _GlobalIdxT, typename _LocalIdxT>
class HIPO_WIN_API ParCSRMatrixT  : public ParMatrixFreeT< _ValT, _GlobalIdxT, _LocalIdxT> {
public:
    typedef CSRMatrixT<_ValT, _LocalIdxT> LocalType;

    struct ColumnBlock;
    ParCSRMatrixT();
    void create(_GlobalIdxT rows, _GlobalIdxT cols, const Device& device, MPI_Comm comm);
    void create(const PartitionerT<_GlobalIdxT, _LocalIdxT>& rowPartitioner, const PartitionerT<_GlobalIdxT, _LocalIdxT>& colPartitioner,
     const std::vector<CSRMatrixT<_ValT, _LocalIdxT>>& col_blocks, const Device& device, MPI_Comm comm);
     void createSeq(const CSRMatrixT<_ValT, _LocalIdxT>& oneBlock, MPI_Comm comm);

    template <class _NewValT>
	void copyStructure(ParCSRMatrixT<_NewValT, _GlobalIdxT, _LocalIdxT>& copy) const {
        auto&A = *this;
        std::vector<CSRMatrixT<_NewValT, _LocalIdxT>> col_blocks(getColPartitioner().getNumParts());
        for (int i=0; i<col_blocks.size(); i++) {
            auto lA = getLocalMatrix(i);
            if (lA.getNnzs() > 0) {
                lA.copyStructure(col_blocks[i]);
            }
        }
		copy.create(A.getRowPartitioner(), A.getColPartitioner(), col_blocks, A.getDevice(), A.getComm());
	}

    _GlobalIdxT getRows() const;
    _GlobalIdxT getCols() const;
    _GlobalIdxT getNnzs() const;
    Device getDevice() const;
    void setDevice(const Device& dev);

    MPI_Comm getComm() const;

    void setComm(MPI_Comm comm);

    ParCSRMatrixT deepCopy() const;
    void deepCopy(ParCSRMatrixT& ret) const;
    
    template <class _NewValT>
    void toType(ParCSRMatrixT<_NewValT, _GlobalIdxT, _LocalIdxT>& ret) const {
        auto&A = *this;
        std::vector<CSRMatrixT<_NewValT, _LocalIdxT>> col_blocks(getColPartitioner().getNumParts());
        for (int i=0; i<col_blocks.size(); i++) {
            auto lA = getLocalMatrix(i);
            if (lA.getNnzs() > 0) {
                lA.toType(col_blocks[i]);
            }
        }
		ret.create(A.getRowPartitioner(), A.getColPartitioner(), col_blocks, A.getDevice(), A.getComm());
    }

    _LocalIdxT getLocalRows() const;

    SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT> getSpMVCommPattern() const;


    void beginAssemble();
    void setValue(_GlobalIdxT i, _GlobalIdxT j, const _ValT& value, SetValueMode mode = ADD_VALUE);
    template <class _IdxT>
    void setValues(_LocalIdxT nrows, const _IdxT* I, _LocalIdxT ncols, const _IdxT* J, const _ValT* values, SetValueMode mode = ADD_VALUE) {
        for (_LocalIdxT i=0; i<nrows; i++) {
            for (_LocalIdxT j=0; j<ncols; j++) {
                setValue(I[i], J[j], values[i*ncols+j], mode);
            }
        }
    }
    void traversal(std::function<bool(_GlobalIdxT i, _GlobalIdxT ncols)> row_iter, 
    std::function<bool(_GlobalIdxT i, _GlobalIdxT j, _ValT& val)> col_iter = nullptr);

    void endAssemble();

    void getOwnerShipRange(_GlobalIdxT* start_row, _GlobalIdxT* end_row) const;
    _ValT getElementValue(_GlobalIdxT i, _GlobalIdxT j, bool* exists) const;
    bool setElementValue(_GlobalIdxT i, _GlobalIdxT j, const _ValT& value);

    void loadFromFile(const std::string& filename, const Device& device = Device(), MPI_Comm comm = MPI_COMM_WORLD);
	void loadFromStream(std::istream& ifs, const Device& device = Device(), MPI_Comm comm = MPI_COMM_WORLD);
	void saveToFile(const std::string& filename, int prec = -1);
	void saveToStream(std::ostream& ofs, int prec = -1);

    CSRMatrixT<_ValT, _LocalIdxT> getLocalMatrix(int i = -1) const;
    void getLocalMatrix(std::vector<CSRMatrixT<_ValT, _LocalIdxT>>& col_blocks) const;
    void setLocalMatrix(const std::vector<CSRMatrixT<_ValT, _LocalIdxT>>& col_blocks);
    PartitionerT<_GlobalIdxT, _LocalIdxT> getRowPartitioner() const;
    PartitionerT<_GlobalIdxT, _LocalIdxT> getColPartitioner() const;

    void getDiag(ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& diag, int dim = 0) const;
    ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> getDiag(int dim = 0) const;

    ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT> rowNorm(typename TypeInfo<_ValT>::scalar_type order) const {
        ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT> norm;
        rowNorm(norm, order);
        return norm;
    }
    void rowNorm(ParMatrixT<typename TypeInfo<_ValT>::scalar_type, _GlobalIdxT, _LocalIdxT>& norm, typename TypeInfo<_ValT>::scalar_type p) const;

    ParCSRMatrixT<_ValT,  _GlobalIdxT, _LocalIdxT> rowTopK(_LocalIdxT k) const;

    void sortRows();

    using typename ParMatrixFreeT< _ValT, _GlobalIdxT, _LocalIdxT>::AsyncMatVecObject;

    void prepareMatVec(bool force = false) const;

    void exchangeMatVec(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x,
    std::function<void(int, typename SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT>::SpmvColBlock*)> on_comm_begin_fn = nullptr, 
    std::function<void(int, typename SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT>::SpmvColBlock*)> on_comm_recv_fn = nullptr, 
    std::function<void()> on_comm_end_fn = nullptr, 
    AsyncMatVecObject* asyncObj = 0) const;


    void aAxpby(_ValT a, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, _ValT b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& y, AsyncMatVecObject* asyncObj = 0);
    void matVec(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& y, AsyncMatVecObject* asyncObj = 0) const;
    ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> matVec(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x) const;

	// A = a*A
	static void scale(ParCSRMatrixT& A, _ValT a);

	// A = a*D*A
	static void matmul_aDA(_ValT a, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& D, ParCSRMatrixT& A);

	// A = a*A*D
	static void matmul_aAD(_ValT a, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& D, ParCSRMatrixT& A);

	// diag(B) = a*x + b*diag(A), B = A for non diag elements
	static void axpbyDiag(_ValT a, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, _ValT b, const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& y, const ParCSRMatrixT& A, ParCSRMatrixT& B);

	// Z = a*X+b*Y
	static void matadd(_ValT a, const ParCSRMatrixT& X, _ValT b, const ParCSRMatrixT& Y, ParCSRMatrixT& Z);


    void jacobi(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, double omega);

    
    void getRawMat(MatrixT<COT_SpMVCSRRawMat<_ValT, _LocalIdxT>, _LocalIdxT>& raw) const;

    MatrixT<COT_SpMVCSRRawMat<_ValT, _LocalIdxT>, _LocalIdxT> getRawMatOnDev() const;

    void sor(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& b, ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT>& x, double omega, bool forward);

    void transpose(ParCSRMatrixT& ret) const;
    ParCSRMatrixT transpose() const {
        ParCSRMatrixT ret;
        transpose(ret);
        return ret;
    }

    void multiply(const ParCSRMatrixT& B, ParCSRMatrixT& ret) const;
    ParCSRMatrixT multiply(const ParCSRMatrixT& B) const {
        ParCSRMatrixT ret;
        multiply(B, ret);
        return ret;
    }

    void toDevice(const Device& device, ParCSRMatrixT& ret) const;

    ParCSRMatrixT toDevice(const Device& device) const;


    ParCSRMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> sparsify(typename TypeInfo<_ValT>::scalar_type threshold) const;

    void createByAssemble(const CSRMatrixT<_ValT, _GlobalIdxT>& localMat, MPI_Comm comm);

    void scatter(MPI_Comm comm, int root, const CSRMatrixT<_ValT, _LocalIdxT>& localMat);
    CSRMatrixT<_ValT, _LocalIdxT> gather(int root) const;

    struct Meta {
        typedef typename TypeInfo<_ValT>::scalar_type Scalar;
        _GlobalIdxT rows;
        _GlobalIdxT cols;
        _GlobalIdxT entries;
        Scalar sparse;
        Scalar row_entries_min;
        Scalar row_entries_max;
        Scalar row_entries_sum;
        Scalar row_entries_avg;
        _ValT row_sum_min;
        _ValT row_sum_max;
        _ValT row_sum_sum;
        _ValT row_sum_avg;
        std::string getString() const;
        static std::string getTableHead();
    };
    void computeMeta(Meta& meta) const;
    Meta computeMeta() const {
        Meta meta;
        computeMeta(meta);
        return meta;
    }

    bool operator==(const ParCSRMatrixT& mat) const;

    void fill(_ValT val);

protected:
    class ParCSRMatrixImpl;
    std::shared_ptr<ParCSRMatrixImpl> m_impl;
};



} // namespace hipo
