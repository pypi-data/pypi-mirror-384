#pragma once
#include "hipo/utils/Math.hpp"
#include "Matrix.hpp"
#include "CSRMatrix.hpp"
#include "Partitioner.hpp"
#include "hipo/comm/communication_tools.h"
#include <map>
#include <unordered_map>
#include <mutex>

namespace hipo {


template <typename KeyT, typename ValT>
struct MapWithLockType {
    typedef std::unordered_map<KeyT, ValT> RowType;
    RowType type;
    std::mutex col_lock;
};

template <typename _ValT, typename _RowIdxT, typename _ColIdxT>
class HIPO_WIN_API COOMatrixT {
protected:
    typedef _RowIdxT _IdxT;
    typedef MapWithLockType<_ColIdxT, _ValT> RowExType;
    typedef typename MapWithLockType<_ColIdxT, _ValT>::RowType RowType;
    typedef std::unordered_map<_RowIdxT, std::shared_ptr<RowExType>> MatType;
public:

    COOMatrixT() {
        create(0, 0);
    }

    COOMatrixT(_RowIdxT rows, _ColIdxT cols) {
        create(rows, cols);
    }

    void create(_RowIdxT rows, _ColIdxT cols) {
        m_impl = std::make_shared<COOMatrixImpl>();
        m_impl->rows = rows;
        m_impl->cols = cols;
        //m_impl->nnzs = nnzs;
    }

    static COOMatrixT rand(_RowIdxT rows, _ColIdxT cols, double sparsity = 0.3) {
        COOMatrixT mat;
        mat.create(rows, cols);


        for (_IdxT k=0; k<std::min(rows, cols); k++) {
            mat(k, k) = Math::rand<_ValT>();
        }
        //std::srand((_IdxT) std::time(0));
        _IdxT sz = (_IdxT) (rows * cols * sparsity);
        for (_IdxT k = 0; k < sz; k++)
        {
            _IdxT row = std::rand() % rows;
            _IdxT col = std::rand() % cols;
            
            mat(row, col) = Math::rand<_ValT>();
        }

        return mat;
    }


    _IdxT getRows() const {
        return m_impl->rows;
    }
    _IdxT getCols() const {
        return m_impl->cols;
    }
    // _IdxT getNnzs() const {
    //     return m_impl->nnzs;
    // }

    void resize(_RowIdxT rows, _ColIdxT cols) {
        m_impl->rows = rows;
        m_impl->cols = cols;
    }

    MatType& getData() const {
        return m_impl->data;
    }
    RowExType& getRowEx(_RowIdxT i) const {
        std::lock_guard<std::mutex> lock(m_impl->row_lock);

        auto& row = m_impl->data[i];
        if (row == nullptr) {
            row = std::make_shared<RowExType>();
        }
        return *row;
    }
    RowType& getRow(_RowIdxT i) const {
        return getRowEx(i).type;
    }

    _ValT& operator()(_RowIdxT i, _ColIdxT j) const {
        return getRow(i)[j];
    }

    _ValT getElementValue(_RowIdxT i, _ColIdxT j, bool* exists = 0) const {
        auto row = getRow(i);
        auto iter = row.find(j);
        if (iter == row.end()) {
            if (exists) {
                *exists = false;
            }
            return 0;
        } else {
            if (exists) {
                *exists = true;
            }
            return iter->second;
        }
    }

    int getStreamSize() const {
        auto& mat = *this;
        _IdxT size = mat.getData().size();
        if (size == 0) {
            return 0;
        }
        int nbytes = 0;
        nbytes += comu::getStreamSize(size);
        for (auto& item : mat.getData()) {
            nbytes += comu::getStreamSize(item.first);
            nbytes += comu::getStreamSize(item.second->type);
        }
        return nbytes;
    }

    void packStream(comu::Stream& stream) const {
        auto& mat = *this;
        _IdxT size = mat.getData().size();
        if (size == 0) {
            return;
        }
        comu::packStream(stream, size);
        for (auto& item : mat.getData()) {
            comu::packStream(stream, item.first);
            comu::packStream(stream, item.second->type);
        }
    }

    void unpackStream(comu::Stream& stream) {
        if (stream.size() == 0) {
            return;
        }
        auto& mat = *this;
        _IdxT size;
        comu::unpackStream(stream, size);
        for (_IdxT i=0; i<size; i++) {
            typename MatType::key_type item_key;
            auto item_val = std::make_shared<RowExType>();
            comu::unpackStream(stream, item_key);
            comu::unpackStream(stream, item_val->type);
            mat.getData()[item_key] = item_val;
        }
    }

    template <class _LocalIdxT>
    void splitRows(const PartitionerT<_RowIdxT, _LocalIdxT>& partition, std::vector<COOMatrixT<_ValT, _LocalIdxT, _ColIdxT>>& submats) {
        const COOMatrixT& gmat = *this;
        submats.resize(partition.getNumParts());
        for (_IdxT i=0; i<submats.size(); i++) {
            submats[i].getData().reserve(partition.getLocalSizeForPart(i));
        }
        
        for (auto & item : gmat.getData()) {
            _RowIdxT globalRow = item.first;
            _LocalIdxT procIdx, localIdx;
            partition.global2Local(globalRow, procIdx, localIdx);
            submats[procIdx].getData()[localIdx] = item.second;
        }
    }


    //// 稀疏矩阵的转置, 为测试提供某些方便
	void transpose(COOMatrixT& trans) const
	{
		trans = COOMatrixT(getCols(), getRows());
		for (_IdxT i = 0; i < getRows(); i++)
		{
			for (auto& pos : getRow(i))
			{
				_IdxT j = pos.first; // 列号
				trans(j, i) = pos.second;
			}
		}
	}

    // 矩阵乘法
	void matMult(const COOMatrixT& mat2, COOMatrixT& prod) const {
		const COOMatrixT& mat1 = *this;
		prod.create(mat1.getRows(), mat2.getCols());
		assert(mat1.getCols() == mat2.getRows());
		for (_IdxT i = 0; i < mat1.getRows(); i++) {
			for (_IdxT j=0; j<mat2.getCols(); j++) {
				for (auto& pos : mat1.getRow(i))
				{
					_IdxT k = pos.first; // 列号
					_ValT val = pos.second;
					prod(i, j) += val * mat2.getElementValue(k, j);
				}
			}
		}
	}

    void beginAssemble()
    {
        getData().clear();
    }

    void setValue(_RowIdxT i, _ColIdxT j, const _ValT &value, SetValueMode mode)
    {
        // 先用行锁获取行
        RowExType& rowEx = getRowEx(i);
        // 再用列锁写列
        std::lock_guard<std::mutex> lock(rowEx.col_lock);
        if (mode == INSERT_VALUE) {
            rowEx.type[j] = value;
        } else if (mode == ADD_VALUE) {
            rowEx.type[j] += value;
        }
    }
    void traversal(std::function<bool(_RowIdxT i, _RowIdxT ncols)> row_iter,
            std::function < bool(_RowIdxT i, _ColIdxT j, _ValT &val)> col_iter) {
        // 先用行锁获取行
        for (auto& rowIter : getData()) {
            auto& row = rowIter.second->type;
            if (row_iter) {
                row_iter(rowIter.first, row.size());
            }
            if (col_iter) {
                for (auto& colIter : row) {
                    col_iter(rowIter.first, colIter.first, colIter.second);
                }
            }
        }
    }

    template <class _LocalIdxT>
    void endAssemble(MPI_Comm comm_, const PartitionerT<_ColIdxT, _LocalIdxT>& row_partition, COOMatrixT<_ValT, _LocalIdxT, _ColIdxT>& localMat);

    void toCSR(CSRMatrixT<_ValT, _RowIdxT>& mat) const {
        //LOG(INFO) << "begin toCSR";

        if (getData().size() == 0 || getRows() == 0) {
            return;
        }
        // if (getRows() == 0 && mat.getRows() == 0) {
        //     return;
        // }
        //if (getRows() > 0 && mat.getRows() == 0) {
            mat.resize(getRows(), getCols());
        //}
        _IdxT rows = mat.getRows();
        auto row_ptr = mat.getRowPtr();
        row_ptr[0] = 0;

        for (_IdxT i=0; i<rows; i++) {
            auto& row = getRow(i);
            row_ptr[i+1] = row_ptr[i] + row.size();
        }
        mat.resizeNnz(row_ptr[rows]);
        auto col_idx = mat.getColIdx();
        auto values = mat.getValues();
        //LOG(INFO) << "begin fill col_idx and values";
        #pragma omp parallel for
        for (_IdxT i=0; i<rows; i++) {
            auto& row = getRow(i);
            auto count = row_ptr[i];
            for (auto& item : row) {
                col_idx[count] = item.first;
                values[count] = item.second;
                count++;
            }
        }
    }

    void fromCSR(const CSRMatrixT<_ValT, _ColIdxT>& mat) {
        create(mat.getRows(), mat.getCols());
        _IdxT rows = mat.getRows();
        _ColIdxT* row_ptr = mat.getRowPtr();
        _ColIdxT* col_idx = mat.getColIdx();
        _ValT* values = mat.getValues();

        for (_IdxT i=0; i<rows; i++) {
            for (_IdxT k=row_ptr[i]; k<row_ptr[i+1]; k++) {
                _IdxT j = col_idx[k];
                _ValT val = values[k];
                (*this)(i, j) = val;
            }
        }
    }

    template <class _LocalIdxT>
    void toDense(MatrixT<_ValT, _LocalIdxT>& mat) const {
        mat.resize(getRows(), getCols());
        mat.fill(0);
        _IdxT rows = mat.getRows();
        #pragma omp parallel for
        for (_IdxT i=0; i<rows; i++) {
            auto& row = getRow(i);
            for (auto& item : row) {
                mat(i, item.first) = item.second;
            }
        }
    }


    void loadFromFile(const std::string& filename) {
        std::ifstream ifs(filename);
        loadFromStream(ifs);
    }

    void loadFromStream(std::istream& ifs) {
        if (!ifs) {
            return;
        }
        auto&A = *this;
        typedef int64_t _IdxT;
		_IdxT m, n, nnz;



		std::string line;
        bool symmetric = false;
        bool has_format = false;
		while(std::getline(ifs, line)) {
			if (line.size() == 0 || line[0] == '%') {
                if (line[0] == '%') {
                    if (has_format) {
                        continue;
                    } else {
                        // MatrixMarket matrix coordinate real general
                        auto start = line.find_first_not_of("% \t");
                        auto end = line.find_last_not_of("\r\n \t");
                        if (start == std::string::npos) {
                            continue;
                        }
                        if (end == std::string::npos) {
                            continue;
                        }
                        std::string format_data(line, start, end-start+1);
                        auto items = stringSplit(format_data, " |\t");

                        //LOG(INFO) <<  "MatrixMarket read start " << start << " format " << format_data << " items " << comu::vec2str(items);
                    
                        if (items.size() == 5 && items[0] == "MatrixMarket") {
                            has_format = true;
                             if (items[4] == "symmetric") {
                                //LOG(INFO) << "format is symmetric";
                                symmetric = true;
                            }
                        }
                       
                    }
                }
				continue;
			} else {
				std::istringstream iss(line);
				iss >> m >> n >> nnz;
				break;
			}
		}

		if (symmetric) {
			LOG(INFO) << "loadFromStream read symmetric matrix";
		}

        m_impl->rows = m;
        m_impl->cols = n;
        //m_impl->nnzs = nnz;

		//LOG(INFO) << "loading coo matrix " << m << " " << n << " " << nnz << std::endl;

		for (_IdxT k = 0; k < nnz; k++) {
			_IdxT i, j;
			_ValT val;
			ifs >> i >> j >> val;
			//LOG(INFO) << "xxx " << i << " " << j << " " << val << std::endl;
			i--;
			j--;
			A(i, j) = val;
			if (symmetric && i != j) {
				A(j, i) = val;
			}
		}
    }

    struct COOMatrixImpl {
        MatType data;
        _RowIdxT rows = -1;
        _ColIdxT cols = -1;
        //int64_t nnzs = 0;
        std::mutex row_lock;
    };
    std::shared_ptr<COOMatrixImpl> m_impl;

    
};


template <typename _ValT, typename _RowIdxT, typename _ColIdxT>
template <class _LocalIdxT>
void COOMatrixT<_ValT, _RowIdxT, _ColIdxT>::endAssemble(MPI_Comm comm_, const PartitionerT<_ColIdxT, _LocalIdxT>& row_partition, COOMatrixT<_ValT, _LocalIdxT, _ColIdxT>& localMat) {
    typedef COOMatrixT<_ValT, _LocalIdxT, _ColIdxT> CooMatT;
    int myrank, nprocs;
    MPI_Comm_rank(comm_, &myrank);
    MPI_Comm_size(comm_, &nprocs);

    std::vector<CooMatT> send_data(nprocs);
    //LOG(INFO) << "begin splitRows";
    this->splitRows(row_partition, send_data);
    //LOG(INFO) << "finish splitRows";

    if (send_data.size() < nprocs) {
        return;
    }
    std::vector<CooMatT> recv_data(nprocs);
    comu::sparse_send_recv_stream(comm_, send_data, recv_data);

    localMat = send_data[myrank];
    for (_IdxT i=0; i<recv_data.size(); i++) {
        // get a submat
        if (i == myrank) {
            continue;
        }
        auto& submat = recv_data[i];
        for (auto& item : submat.getData()) {
            for (auto& col : item.second->type) {
                localMat(item.first, col.first) += col.second;
            }
        }
    }
    localMat.resize(getRows(), getCols());
}
}
