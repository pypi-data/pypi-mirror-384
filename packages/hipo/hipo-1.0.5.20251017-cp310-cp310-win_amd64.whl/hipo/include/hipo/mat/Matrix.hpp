#pragma once

#include <cassert>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <cmath>
#include <algorithm>
#include <memory>
#include <fstream>
#include <sstream>
#include <iomanip>

#include "hipo/utils/logging.hpp"
#include "Matrix_fwd.hpp"
#include "hipo/utils/Complex.hpp"
#include "hipo/utils/Device.hpp"
#include "hipo/utils/Math.hpp"
#include "hipo/utils/Utils.hpp"
#include "hipo/ops/BlasOps.hpp"
#include "hipo/ops/MixedBlasOps.hpp"
#include "hipo/ops/CrossOpTypes.hpp"
#include "hipo/ops/MatOps.hpp"
#include "hipo/comm/Stream.h"
#include "Partitioner.hpp"
#include "hipo/utils/CrossData.hpp"


namespace hipo {



template <class _ValT, class _IdxT>
static void mat_lu_decomp(LUDecompStep step, _ValT *pA, _ValT *x, _IdxT n, _IdxT *error) {


    auto A = [pA, n](_IdxT i, _IdxT j)-> _ValT& {
      return pA[i*n+j];
    };

    if (step == LU_NUMERICAL_DECOMP) {

    
    {

        *error = 0;
        
        for (_IdxT k=0; k<n; k++) {
            auto& A_kk = A(k, k);
            if (A_kk == 0) {
                *error = k+1;
                return;
            }

            for (_IdxT i=k+1; i<n; i++) {
                _ValT& A_ik = A(i,k);
                if (A_ik != 0) {
                    A_ik /= A_kk;
                    for (_IdxT j=k+1; j<n; j++) {
                        A(i,j) -= A_ik * A(k,j);
                    }
                }
            }
        }
        
    
    }

    }

    if (step == LU_BACK_SOLVE) {
    {


        
        for (_IdxT i=0; i<n; i++) {
            for (_IdxT j=0; j<i; j++) {
                x[i] -= A(i, j) * x[j];
            }
        }


        for (_IdxT i=n-1; i>=0; i--) {
            for (_IdxT j=n-1; j>i; j--) {
                x[i] -= A(i, j) * x[j];
            }
            x[i] /= A(i,i);
        }
    };   
    }
}

enum SetValueMode {
	INSERT_VALUE = 0,
	ADD_VALUE = 1,
};

/**
 * @brief 矩阵类
 * @tparam _ValT 矩阵元素类型
 * @tparam _IdxT 矩阵元素索引类型
 */
template<class _ValT, class _IdxT, class _Layout>
class HIPO_WIN_API MatrixT
{
public:
	typedef _ValT value_type;
	typedef _ValT* pointer;
	typedef const _ValT* const_pointer;
	typedef _ValT& reference;
	typedef const _ValT& const_reference;
public:
	// 初始化函数
	void create(_IdxT rows = 0, _IdxT cols = 0, const Device& device = Device())
	{
		CHECK(rows>=0 && cols>=0);
		_IdxT n = rows * cols;
		m_impl = std::make_shared<MatrixImpl>();
		m_impl->device = device;
		m_impl->rows = rows;
		m_impl->cols = cols;
		if (n > 0) {
			m_impl->data = device.template malloc<_ValT>(n);
		}
		m_impl->capacity = n;
	}
	void create(_IdxT rows, const Device& device = Device())
	{
		create(rows, 1, device);
	}
	/**
	 * @brief 构造一个空的矩阵
	 */
	MatrixT()
	{
		create();
	}
	/**
	 * @brief 构造一个长度为size*1的矩阵（列向量），并设置初始值
	 * @param size [in] 列向量的长度
	 * @param value [in] 列向量的初始值，如果value=0，则初始值为零向量
	 */
	MatrixT(_IdxT size, const Device& device)
	{
		assert(size >= 0);
		create(size, 1, device);
	}
	/**
	 * @brief 构造一个row*col的矩阵，并设置初始值
	 * @param row [in] 矩阵的行数
	 * @param col [in] 矩阵的列数
	 * @param value [in] 矩阵的初始值，列优先存储，如果value=0，则初始值为零矩阵
	 */
	MatrixT(_IdxT rows, _IdxT cols, const Device& device)
	{
		assert(rows>=0 && cols>=0);
		create(rows, cols, device);
	}
	
	~MatrixT()
	{
		m_impl.reset();
	}
	
	pointer getData() const
	{
		return m_impl->data;
	}
	
	Device getDevice() const {
		return m_impl->device;
	}

    // std compliance
    
	_IdxT getSize() const
	{
		return getRows() * getCols();
	}
	_IdxT getRows() const
	{
		return m_impl->rows;
	}
	_IdxT getCols() const
	{
		return m_impl->cols;
	}

	_IdxT getCapacity() const {
		return m_impl->capacity;
	}
	
	bool isEmpty() const
	{
		return getRows() == 0 || getCols() == 0;
	}

 	// deep copy.
    MatrixT deepCopy() const
	{
		MatrixT ret;
		deepCopy(ret);
		return ret;
	}

	// deep copy.
    void deepCopy(MatrixT& ret) const
	{
		ret.resize(getRows(), getCols(), getDevice());
		Device dev = getDevice();
		dev.copyTo(getSize(), getData(), dev, ret.getData());
	}

	void resize(_IdxT rows, _IdxT cols, const Device& device) {
		_IdxT n = rows * cols;
		if (n <= getCapacity() && device == getDevice()) {
			m_impl->rows = rows;
			m_impl->cols = cols;
			return;
		}
		create(rows, cols, device);
	}
	void resize(_IdxT rows, _IdxT cols) {
		resize(rows, cols, getDevice());
	}

	void resize(_IdxT n, const Device& device) {
		resize(n, 1, device);
	}

	void toDevice(const Device& device, MatrixT& ret) const {
		auto srcDev = getDevice();
		if (srcDev == device) {
			ret = *this;
			return;
		}
		ret.resize(getRows(), getCols(), device);
		srcDev.copyTo(getSize(), getData(), device, ret.getData());
	}

	MatrixT toDevice(const Device& device) const {
		MatrixT ret;
		toDevice(device, ret);
		return ret;
	}

	template <class _NewValT>
	void toType(MatrixT<_NewValT, _IdxT>& ret) const {
		ret.resize(getRows(), getCols(), getDevice());
		MixedBlasOps<_NewValT, _ValT, _IdxT>::copy(getDevice(), getSize(), getData(), ret.getData());
	}

	void copyTo(_ValT* dst) const {
		auto device = getDevice();
		device.copyTo(getSize(), getData(), device, dst);
	}
	
	/**
	 * @brief 给矩阵赋值
	 */
	void fill(const_reference a)
	{
		// 避免出现没有初始化就赋值的情况
		BlasOps<_ValT, _IdxT>::fill(getDevice(), getSize(), a, getData());
	}

	static void scale(const_reference a, MatrixT& x) {
		BlasOps<_ValT, _IdxT>::scal(x.getDevice(), x.getSize(), a, x.getData());
	}

	static void axpy(const_reference a, const MatrixT& x, MatrixT& y) {
		CHECK(x.getSize() == y.getSize()) << "axpy: x and y must have the same size";
		CHECK(x.getDevice() == y.getDevice()) << "axpy: x and y must be on the same device";
		BlasOps<_ValT, _IdxT>::axpy(x.getDevice(), x.getSize(), a, x.getData(), y.getData());
	}
	static void axpby(const_reference a, const MatrixT& x, const_reference b, MatrixT& y) {
		CHECK(x.getSize() == y.getSize()) << "axpby: x and y must have the same size";
		CHECK(x.getDevice() == y.getDevice()) << "axpby: x and y must be on the same device";
		BlasOps<_ValT, _IdxT>::axpby(x.getDevice(), x.getSize(), a, x.getData(), b, y.getData());
	}
	static void axpbypz(const_reference a, const MatrixT& x, const_reference b, const MatrixT& y, MatrixT& z) {
		CHECK(x.getSize() == y.getSize()) << "axpbypz: x and y must have the same size";
		CHECK(x.getDevice() == y.getDevice()) << "axpbypz: x and y must be on the same device";
		CHECK(x.getSize() == z.getSize()) << "axpbypz: x and z must have the same size";
		CHECK(x.getDevice() == z.getDevice()) << "axpbypz: x and z must be on the same device";
		BlasOps<_ValT, _IdxT>::axpbypz(x.getDevice(), x.getSize(), a, x.getData(), b, y.getData(), z.getData());
	}
	static void axpbypcz(const_reference a, const MatrixT& x, const_reference b, const MatrixT& y, const_reference c, MatrixT& z) {
		CHECK(x.getSize() == y.getSize()) << "axpbypz: x and y must have the same size";
		CHECK(x.getDevice() == y.getDevice()) << "axpbypz: x and y must be on the same device";
		CHECK(x.getSize() == z.getSize()) << "axpbypz: x and z must have the same size";
		CHECK(x.getDevice() == z.getDevice()) << "axpbypz: x and z must be on the same device";
		BlasOps<_ValT, _IdxT>::axpbypcz(x.getDevice(), x.getSize(), a, x.getData(), b, y.getData(), c, z.getData());
	}
	
    static void axypbz(_ValT a, const MatrixT& x, const MatrixT& y, _ValT b, MatrixT& z) {
		CHECK(x.getSize() == y.getSize()) << "axpbypz: x and y must have the same size";
		CHECK(x.getDevice() == y.getDevice()) << "axpbypz: x and y must be on the same device";
		CHECK(x.getSize() == z.getSize()) << "axpbypz: x and z must have the same size";
		CHECK(x.getDevice() == z.getDevice()) << "axpbypz: x and z must be on the same device";
		BlasOps<_ValT, _IdxT>::axypbz(x.getDevice(), x.getSize(), a, x.getData(), y.getData(), b, z.getData());
    }

	static _ValT dot(const MatrixT& x, const MatrixT& y) {
		CHECK(x.getDevice() == y.getDevice()) << "dot: x and y must be on the same device";
		CHECK(x.getSize() == y.getSize()) << "dot: x and y must have the same size";
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
			_ValT sum = 0;
			for (_IdxT i = 0; i < x.getSize(); i++) {
				_ValT& v = x.getData()[i];
				sum += v * v;
			}
			return sum;
		} else {
		return BlasOps<_ValT, _IdxT>::dot(x.getDevice(), x.getSize(), x.getData(), y.getData());
		}
	}

	static _ValT dotu(const MatrixT& x, const MatrixT& y) {
		CHECK(x.getDevice() == y.getDevice()) << "dot: x and y must be on the same device";
		CHECK(x.getSize() == y.getSize()) << "dot: x and y must have the same size";
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
			_ValT sum = 0;
			for (_IdxT i = 0; i < x.getSize(); i++) {
				_ValT& v = x.getData()[i];
				sum += v * v;
			}
			return sum;
		} else {
		return BlasOps<_ValT, _IdxT>::dotu(x.getDevice(), x.getSize(), x.getData(), y.getData());
		}
	}

	static typename TypeInfo<_ValT>::scalar_type absMax(const MatrixT& x) {
		return BlasOps<_ValT, _IdxT>::abs_max(x.getDevice(), x.getSize(), x.getData());
	}
	
	static typename TypeInfo<_ValT>::scalar_type absSum(const MatrixT& x, typename TypeInfo<_ValT>::scalar_type order) {
		return BlasOps<_ValT, _IdxT>::abs_sum(x.getDevice(), x.getSize(), x.getData(), order);
	}

	static typename TypeInfo<_ValT>::scalar_type normL2(const MatrixT& x) {
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
			_ValT sum = 0;
			for (_IdxT i = 0; i < x.getSize(); i++) {
				_ValT& v = x.getData()[i];
				sum += v * v;
			}
			return std::sqrt(sum);
		} else {
		auto sum = absSum(x, 2);
		return std::sqrt(sum);
		}
	}
	static typename TypeInfo<_ValT>::scalar_type distanceL2(const MatrixT& x, const MatrixT& y) {
		CHECK(x.getDevice() == y.getDevice()) << "distanceL2: x and y must be on the same device";
		CHECK(x.getSize() == y.getSize()) << "distanceL2: x and y must have the same size";
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
			_ValT sum = 0;
			for (_IdxT i = 0; i < x.getSize(); i++) {
				_ValT v = x.getData()[i] - y.getData()[i];
				sum += v * v;
			}
			return std::sqrt(sum);
		} else {
			MatrixT diff = y.deepCopy();
			axpby(_ValT(1), x, _ValT(-1), diff);
			return normL2(diff);
		}
	}
	static void reciprocal(_ValT a, MatrixT &x) {
		BlasOps<_ValT, _IdxT>::reciprocal(x.getDevice(), x.getSize(), a, x.getData());
	}
	static void pow(_ValT a, MatrixT &x) {
		BlasOps<_ValT, _IdxT>::pow(x.getDevice(), x.getSize(), a, x.getData());
	}
	void getRawMat(COT_RawMat<_ValT, _IdxT>& raw) const {
		raw.rows = m_impl->rows;
		raw.cols = m_impl->cols;
		raw.data = m_impl->data;
	}

	MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> rowNorm(double order) const {
		MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> ret;
		rowNorm(ret, order);
		return ret;
	}
	void rowNorm(MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT>& norm, double order) const {
		norm.resize(getRows(), getDevice());
		COT_RawMat<_ValT, _IdxT> rawMat;
		getRawMat(rawMat);
		MatOps<_ValT, _IdxT, _Layout>::mat_row_norm(getDevice(), rawMat, 1, order, norm.getData());		
	}

	MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> getReal() const {
        MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> ret;
        getReal(ret);
        return ret;
    }

	void getReal(MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT>& ret) const {
		ret.resize(getRows(), getCols(), getDevice());
		BlasOps<_ValT, _IdxT>::get_real(getDevice(), getSize(), getData(), ret.getData());
	}
	MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> getImag() const {
        MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> ret;
        getImag(ret);
        return ret;
    }
    void getImag(MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT>& ret) const {
		ret.resize(getRows(), getCols(), getDevice());
		BlasOps<_ValT, _IdxT>::get_imag(getDevice(), getSize(), getData(), ret.getData());
	}

	void createComplex(const MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT>& real, const MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT>& imag) {
		if constexpr (TypeInfo<_ValT>::is_complex) {
			auto& ret = *this;
			if (real.getSize() > 0) {
				ret.resize(real.getRows(), real.getCols(), real.getDevice());
			} else if (imag.getSize() > 0) {
				ret.resize(imag.getRows(), imag.getCols(), imag.getDevice());
			} else {
				ret = MatrixT<_ValT, _IdxT>();
				return;
			}
			typedef typename TypeInfo<_ValT>::scalar_type ScalarT;
			BlasOps<ScalarT, _IdxT>::create_complex(ret.getDevice(), ret.getSize(), real.getData(), imag.getData(), ret.getData());
		} else {
			real.deepCopy(*this);
		}
	}

	// 从x中抽取索引为indices到sub_array
    void selectRows(const MatrixT<_IdxT, _IdxT>& indices, MatrixT<_ValT, _IdxT>& sub_array) const {
        CHECK(getDevice() == indices.getDevice()) << "selectRows: indices should on the same device";
        sub_array.resize(indices.getSize(), this->getCols(), this->getDevice());
        MatOps<_ValT, _IdxT, _Layout>::select_rows(getDevice(), getRows(), getCols(), getData(), indices.getSize(), indices.getData(), sub_array.getData());
    }
    void unselectRows(const MatrixT<_IdxT, _IdxT>& indices, const MatrixT<_ValT, _IdxT>& sub_array) {
        CHECK(getDevice() == indices.getDevice() && getDevice() == sub_array.getDevice()) << "selectRows: indices and sub_array should on the same device";
        MatOps<_ValT, _IdxT, _Layout>::unselect_rows(getDevice(), getRows(), getCols(), getData(), indices.getSize(), indices.getData(), sub_array.getData());
    }

    void getNonZeroIndices(MatrixT<_IdxT, _IdxT>& indices) const {
        MatrixT<_IdxT, _IdxT> len(1, getDevice());
        BlasOps<_ValT, _IdxT>::get_nonzero_indices(getDevice(), getSize(), getData(), len.getData(), 0);
        auto cpuLen = len.toDevice(Device(Device::CPU));
        indices.resize(cpuLen.getData()[0], getDevice());
        BlasOps<_ValT, _IdxT>::get_nonzero_indices(getDevice(), getSize(), getData(), len.getData(), indices.getData());
    }

	void aAxpby(_ValT a, const MatrixT& x, _ValT b, MatrixT& y) {
		auto& A = *this;
		CHECK(A.getCols() == x.getRows()) << "aAxpby: A.cols != x.rows";
		CHECK(A.getDevice() == x.getDevice()) << "aAxpby: A and x must on the same device";

		CHECK(A.getRows() == y.getRows() && x.getCols() == y.getCols()) << "aAxpby: A.rows!= y.rows || x.cols!= y.cols";
		CHECK(A.getDevice() == y.getDevice()) << "aAxpby: A and y must on the same device";
		MatOps<_ValT, _IdxT, _Layout>::aAxpby(A.getDevice(), a, A.getRows(), A.getCols(), A.getData(), x.getData(), b, y.getData());
	}

	void matVec(const MatrixT& x, MatrixT& y) {
		auto& A = *this;
		if (y.getRows() != A.getRows() || y.getCols() != x.getCols() || y.getDevice() != A.getDevice()) {
			y.resize(A.getRows(), x.getCols(), A.getDevice());
		}
		aAxpby(_ValT(1), x, _ValT(0), y);
	}

	MatrixT& operator+=(const MatrixT& x) {
		CHECK(getDevice() == x.getDevice()) << "operator+=: x and y must be on the same device";
		CHECK(getRows() == x.getRows() && getCols() == x.getCols()) << "operator+=: x and y must have same size";
		BlasOps<_ValT, _IdxT>::axpy(getDevice(), getSize(), _ValT(1), x.getData(), getData());
		return *this;
	}

	MatrixT operator+(const MatrixT& x) const {
		CHECK(getDevice() == x.getDevice()) << "operator+=: x and y must be on the same device";
		CHECK(getRows() == x.getRows() && getCols() == x.getCols()) << "operator+=: x and y must have same size";
		MatrixT ret(getRows(), getCols(), getDevice());
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
		for (_IdxT i = 0; i < getSize(); i++) {
			ret.getData()[i] = getData()[i] + x.getData()[i];
		}
		} else {
			this->deepCopy(ret);
			BlasOps<_ValT, _IdxT>::axpy(getDevice(), getSize(), _ValT(1), x.getData(), ret.getData());

		}
		return ret;
	}
	MatrixT operator-(const MatrixT& x) const {
		CHECK(getDevice() == x.getDevice()) << "operator+=: x and y must be on the same device";
		CHECK(getRows() == x.getRows() && getCols() == x.getCols()) << "operator+=: x and y must have same size";
		MatrixT ret(getRows(), getCols(), getDevice());
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
		for (_IdxT i = 0; i < getSize(); i++) {
			ret.getData()[i] = getData()[i] - x.getData()[i];
		}
		} else {
			this->deepCopy(ret);
			BlasOps<_ValT, _IdxT>::axpy(getDevice(), getSize(), _ValT(-1), x.getData(), ret.getData());

		}
		return ret;
	}

	MatrixT operator*(const MatrixT& x) {
		return this->multiply(x);
	}

	MatrixT& operator*=(const _ValT& a) {
        auto& mat = *this;
        scale(a, mat);
        return mat;
    }

	/**
	 * 这里比较有高见, 只需定义等于就可以了
	 * 跟BS先生学的
	 * 这就是不用mat1(i, j) ！= mat2(i, j)的原因
	 */
	bool operator==(const MatrixT& mat) const
	{
		CHECK(getRows() == mat.getRows() && getCols() == mat.getCols() && getDevice() == mat.getDevice());
		auto dist = distanceL2(*this, mat);
		return dist == 0;
	}
	bool operator!=(const MatrixT& mat) const
	{
		return !((*this) == mat);
	}
	static bool numericalEqual(const MatrixT& mat1, const MatrixT& mat2, double factor = 100.0) {
		return mat1.numericalEqual(mat2, factor);
	}
	bool numericalEqual(const MatrixT& mat, double factor = 100.0) const
	{
		assert(getRows() == mat.getRows() && getCols() == mat.getCols());
		auto dist = distanceL2(*this, mat);
		typedef decltype(dist) RetType;
		//LOG(INFO) << "MatrixT dist = " << dist;
		return Math::numericalEqual(RetType(0), dist, RetType(factor));
	}

	static MatrixT<_ValT, _IdxT> rand(_IdxT m, _IdxT n) {
		MatrixT<_ValT, _IdxT> mat(m, n, Device());
		//std::srand((_IdxT) std::time(0));
		auto data = mat.getData();
		for (_IdxT i = 0; i < m * n; i++) {
			data[i] = Math::rand<_ValT>();
		}
		return mat;
	}

	static MatrixT<_ValT, _IdxT> zero(_IdxT m, _IdxT n) {
		MatrixT<_ValT, _IdxT> mat(m, n, Device());
		//std::srand((_IdxT) std::time(0));
		for (_IdxT i=0; i<m; i++) {
			for (_IdxT j=0; j<n; j++) {
				mat(i, j) = 0;
			}
		}
		return mat;
	}

	static MatrixT<_ValT, _IdxT> eye(_IdxT m, _IdxT n) {
		MatrixT<_ValT, _IdxT> mat = zero(m, n);
		_IdxT min = std::min(m, n);
		for (_IdxT i=0; i<min; i++) {
			mat(i, i) = 1;
		}
		return mat;
	}

	static MatrixT range(_IdxT begin, _IdxT end, _IdxT stride = 1) {
		MatrixT vec(end-begin, Device());
		auto data = vec.getData();
		for (_IdxT i=0; i<vec.getSize(); i++) {
			data[i] = begin + i * stride;
		}
		return vec;
	}

	/**
	 * @brief 将分块矩阵blk合成一个矩阵。
	 */
	static MatrixT<_ValT, _IdxT> block(const MatrixT<MatrixT<_ValT, _IdxT>, _IdxT>& blk)
	{
		_IdxT M = blk.getRows();
		_IdxT N = blk.getCols();
		std::vector<_IdxT> rows(M+1, 0), cols(N+1, 0);
		
		// check that the block matrix is valid
		for (_IdxT i=0; i<M; i++)
			for (_IdxT j=0; j<N; j++)
				if (!blk(i,j).isEmpty())
				{
					if (rows[i] != 0)
						assert(rows[i] == blk(i,j).getRows());
					else
						rows[i] = blk(i,j).getRows();
					if (cols[j] != 0)
						assert(cols[j] == blk(i,j).getCols());
					else
						cols[j] = blk(i,j).getCols();
				}
		for (_IdxT i=M; i>0; i--)
			rows[i] = rows[i-1];
		rows[0] = 0;
		for (_IdxT i=0; i<M; i++)
			rows[i+1] += rows[i];

		for (_IdxT j=N; j>0; j--)
			cols[j] = cols[j-1];
		cols[0] = 0;
		for (_IdxT j=0; j<N; j++)
			cols[j+1] += cols[j];

		_IdxT row = rows[M];
		_IdxT col = cols[N];
		MatrixT<_ValT, _IdxT> mat(row, col);
		mat.fill(0);

		for (_IdxT i=0; i<M; i++)
			for (_IdxT j=0; j<N; j++)
				if (!blk(i,j).isEmpty())
				{
					for (_IdxT ii = 0; ii < blk(i,j).getRows(); ii++)
						for (_IdxT jj = 0; jj < blk(i,j).getCols(); jj++)
						{
							mat(rows[i]+ii, cols[j]+jj) = blk(i,j)(ii,jj);
						}
				}
		return mat;
	}

	template <class _GlobalIdxT, class _LocalIdxT>
	static MatrixT<_ValT, _IdxT> mergeRows(const PartitionerT<_GlobalIdxT, _LocalIdxT>& partitioner, const std::vector<MatrixT<_ValT, _IdxT>>& blk)
	{
		if (blk.size() == 0) {
			return MatrixT<_ValT, _IdxT>();
		}
		CHECK(blk.size() == partitioner.getNumParts());

		_GlobalIdxT rows = 0;
		_GlobalIdxT cols = 0;
		Device device;

		for (_IdxT i=0; i<blk.size(); i++) {
			if (blk[i].getSize() > 0) {
				if (cols == 0) {
					cols = blk[i].getCols();
					device = blk[i].getDevice();
				}
				CHECK(cols == blk[i].getCols());
				CHECK(device == blk[i].getDevice());
				rows += blk[i].getRows();
			}
		}

		CHECK(rows == partitioner.getGlobalSize());

		MatrixT<_ValT, _IdxT> mat(rows, cols, device);

		for (_IdxT i=0; i<blk.size(); i++) {
			if (blk[i].getSize() > 0) {
				_GlobalIdxT begin, end;
				partitioner.getOwnerShipRangeForPart(i, &begin, &end);
				MatrixT<_LocalIdxT, _LocalIdxT> ids = MatrixT<_LocalIdxT, _LocalIdxT>::range(begin, end).toDevice(device);
				mat.unselectRows(ids, blk[i]);
			}
		}
		return mat;
	}

	template <class _GlobalIdxT, class _LocalIdxT>
	void splitRows(const PartitionerT<_GlobalIdxT, _LocalIdxT>& partitioner, std::vector<MatrixT<_ValT, _IdxT>>& blks) const
	{
		CHECK(this->getRows() == partitioner.getGlobalSize()) << "splitRows: rows.size() != partitioner.getGlobalSize()";
		blks.resize(partitioner.getNumParts());
		for (_IdxT k=0; k<partitioner.getNumParts(); k++) {
			auto& blk = blks[k];
			_GlobalIdxT begin, end;
			partitioner.getOwnerShipRangeForPart(k, &begin, &end);
			MatrixT<_LocalIdxT, _LocalIdxT> ids = MatrixT<_LocalIdxT, _LocalIdxT>::range(begin, end).toDevice(getDevice());
			selectRows(ids, blk);
		}
	}

	struct MatRef {
	private:
		_ValT* a;
		_IdxT m, n;
	public:
		MatRef(_ValT* a, _IdxT m, _IdxT n) : a(a), m(m), n(n) {}
		_ValT& operator()(_IdxT i, _IdxT j) {
			if constexpr (std::is_same<_Layout, MatrixLayoutRowMajor>::value) {
				return a[i * n + j];
			} else {
				return a[i + j * m];
			};
		}
	};

	reference operator()(_IdxT i, _IdxT j) const {
		assert(i >= 0 && i < getRows());
		assert(j >= 0 && j < getCols());
		auto& A = *this;
		auto rows = A.getRows();
		auto cols = A.getCols();
		auto data = A.getData();
		if constexpr (std::is_same<_Layout, MatrixLayoutRowMajor>::value) {
			return data[i * cols + j];
		} else {
			return data[i + j * rows];
		}
	}

	reference operator()(_IdxT i) const {
		return (*this)(i, 0);
	}



	// A = P*L*U
	static void xgetrf(_IdxT m, _IdxT n, pointer a, _IdxT* ipiv, _IdxT* info)
	{
		MatRef A(a, m, n);
		for (_IdxT k = 0; k < m; k++)
		{
			_IdxT i, j;
			// 选主元
			_ValT piv = hipo::abs(A(k, k));
			ipiv[k] = k;
			for (i = k + 1; i < m; i++)
			{
				_ValT tmp = hipo::abs(A(i, k));
				if (tmp > piv)
				{
					piv = tmp;
					ipiv[k] = i;
				}
			}
			// 如果主元为零, 矩阵奇异
			if (piv == _ValT(0))
			{
				*info = k+1;
				return;
			}
			// 交换行
			if (ipiv[k] != k) {
				for (_IdxT j=0; j<n; j++) {
					std::swap(A(k, j), A(ipiv[k], j));
				}
			}
			// 求Gauss向量
			for (i = k + 1; i < m; i++)
				A(i, k) /= A(k, k);
			// 对其他列作Gauss变换
			for (i = k + 1; i < m; i++)
				for (j = k + 1; j < n; j++)
					A(i,j) -= A(i,k) * A(k,j);
		}
		*info = 0;
	}
	static void xgetri(_IdxT n, pointer a, _IdxT* ipiv, _IdxT* info)
	{
		MatRef A(a, n, n);

		if (*info != 0)
			return;

		_IdxT i, j, k;
		value_type sum;

		// step1: 从LU分解A得到PA=LU, 求P, L, U由xgetrf完成
		// step2: 求U^-1
		for (j = 0; j < n; j++)
		{
			A(j, j) = value_type(1) / A(j, j);
			for (i = 0; i < j; i++)
			{
				sum = value_type(0);
				for (k = i; k < j; k++)
					sum += A(i, k) * A(k, j);
				A(i, j) = sum * (-A(j, j));
			}
		}

		// step3: 求L^-1
		for (i = 0; i < n; i++)
		{
			for (j = 0; j < i; j++)
			{
				sum = A(i, j);
				for (k = j + 1; k < i; k++)
					sum += A(i, k) * A(k, j);
				A(i, j) = -sum;
			}
		}

		// step4: 求U^-1 * L^-1
		for (j = 0; j < n; j++)
		{
			for (i = 0; i <= j; i++)
			{
				sum = A(i, j);
				for (k = j + 1; k < n; k++)
					sum += A(i, k) * A(k, j);
				A(i, j) = sum;
			}
			for (i = j + 1; i < n; i++)
			{
				sum = value_type(0);
				for (k = i; k < n; k++)
					sum += A(i, k) * A(k, j);
				A(i, j) = sum;
			}
		}

		// step5: 从(PA)^-1中求解A^-1
		for (k = n - 1; k >= 0; k--)
		{
			if (k != ipiv[k]) {
				for (_IdxT j = 0; j < n; j++)
					std::swap(A(j, k), A(j, ipiv[k]));
			}
		}
	}

	static void xgetrs(_IdxT n, pointer a, _IdxT* ipiv, pointer x, _IdxT* info) {
		MatRef A(a, n, n);
		
		// Solve A * X = B.

		// Apply row interchanges to the right hand sides.

		for (_IdxT i=0; i<n; i++) {
			_IdxT pi = ipiv[i];
			if (i != pi) {
				std::swap(x[i], x[pi]);
			}
		}

		// Solve L*X = B, overwriting B with X.
		for (_IdxT i=0; i<n; i++) {
            for (_IdxT j=0; j<i; j++) {
                x[i] -= A(i, j) * x[j];
            }
        }

		// Solve U*X = B, overwriting B with X.
		for (_IdxT i=n-1; i>=0; i--) {
            for (_IdxT j=n-1; j>i; j--) {
                x[i] -= A(i, j) * x[j];
            }
			if (A(i,i) != 0) {
            	x[i] /= A(i,i);
			} else {
				*info = i+1;
				break;
			}
        }
	}

	static void xgesv(_IdxT n, pointer a, _IdxT* ipiv, pointer* x, _IdxT* info) {
		xgetrf(n, n, a, ipiv, info);
		if (*info == 0) {
			xgetrs(n, a, ipiv, x, info);
		}
	}

    _IdxT pluDecomp(MatrixT<_IdxT, _IdxT>& p, MatrixT& x = 0, int steps = LU_NUMERICAL_DECOMP) {
		auto& lA = *this;
		auto dev = lA.getDevice();
		_IdxT N = lA.getRows();
		p.resize(N, dev);
		_ValT*A = lA.getData();
		_IdxT* ipiv = p.getData();
		_IdxT info;
		if (steps & LU_NUMERICAL_DECOMP) {
			
			xgetrf(N, N, A, ipiv, &info);
		}
		if (steps & LU_BACK_SOLVE) {
			if (info == 0) {
				xgetrs(N, A, ipiv, x.getData(), &info);
			}
		}
		return info;
	}
	MatrixT inverse(pointer pdet = 0) const
	{
		assert(getRows() == getCols());
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
		
		_IdxT row = getRows();
		_IdxT info;

		MatrixT inv = deepCopy();
		pointer invData = inv.getData();

		_IdxT* ipiv = new _IdxT[row];
		xgetrf(row, row, invData, ipiv, &info);
		if (pdet)
		{
			*pdet = value_type(1);
			for (_IdxT i = 0; i < row; i++)
			{
				(*pdet) *= invData[i + row * i];
				if (ipiv[i] != i)
					(*pdet) *= -value_type(1);
			}
		}
		xgetri(row, invData, ipiv, &info);
		delete[] ipiv;
		return inv;

		} else {

		_IdxT row = getRows();
		
		Device dev = getDevice();

		MatrixT inv = deepCopy();
		_ValT* invData = inv.getData();


		MatrixT<_IdxT, _IdxT> ipiv(row+1, 1, dev);
		_IdxT* pInfo = ipiv.getData()+row;
		MatOps<_ValT, _IdxT, _Layout>::xgetrf(dev, row, row, invData, ipiv.getData(), pInfo);
		if (pdet)
		{
			MatrixT<_ValT, _IdxT> det_dev(1, 1, dev);
			MatOps<_ValT, _IdxT, _Layout>::xgetrf_det(dev, row, invData, ipiv.getData(), det_dev.getData());
			MatrixT<_ValT, _IdxT> det_host = det_dev.toDevice(Device(Device::CPU));
			*pdet = det_host.getData()[0];
		}
		MatOps<_ValT, _IdxT, _Layout>::xgetri(dev, row, invData, ipiv.getData(), pInfo);
		return inv;
		}
	}

	_IdxT gaussElim(MatrixT& x) {
		auto& lA = *this;
		auto dev = lA.getDevice();
		CrossData<_IdxT> error(dev, 0);
		MatOps<_ValT, _IdxT, _Layout>::mat_gauss_elim(dev, lA.getData(), x.getData(), lA.getRows(), error.device());
		error.toHost();
		return error.host();
	}

	_IdxT luDecompV2(MatrixT* x = 0, int steps = LU_NUMERICAL_DECOMP) {
		auto& lA = *this;
		auto dev = lA.getDevice();
		CrossData<_IdxT> error(dev, 0);
		_ValT* data = x ? x->getData() : 0;
		if (steps & LU_NUMERICAL_DECOMP) {
			mat_lu_decomp(LU_NUMERICAL_DECOMP, lA.getData(), data, lA.getRows(), error.device());
		}
		if (steps & LU_BACK_SOLVE) {
			CHECK(data != 0);
			mat_lu_decomp(LU_BACK_SOLVE, lA.getData(), data, lA.getRows(), error.device());
		}
		error.toHost();
		return error.host();
	}

	_IdxT luDecomp(MatrixT* x = 0, int steps = LU_NUMERICAL_DECOMP) {
		auto& lA = *this;
		auto dev = lA.getDevice();
		CrossData<_IdxT> error(dev, 0);
		_ValT* data = x ? x->getData() : 0;
		if (steps & LU_NUMERICAL_DECOMP) {
			MatOps<_ValT, _IdxT, _Layout>::mat_lu_decomp(dev, LU_NUMERICAL_DECOMP, lA.getData(), data, lA.getRows(), error.device());
		}
		if (steps & LU_BACK_SOLVE) {
			CHECK(data != 0);
			MatOps<_ValT, _IdxT, _Layout>::mat_lu_decomp(dev, LU_BACK_SOLVE, lA.getData(), data, lA.getRows(), error.device());
		}
		error.toHost();
		return error.host();
	}
	_IdxT ldlDecomp(MatrixT* x = 0, int steps = LU_NUMERICAL_DECOMP) {
		auto& lA = *this;
		#if 1
		auto dev = lA.getDevice();
		CrossData<_IdxT> error(dev, 0);
		_ValT* data = x ? x->getData() : 0;
		MatrixT work(lA.getRows(), 1, dev);
		if (steps & LU_NUMERICAL_DECOMP) {
			MatOps<_ValT, _IdxT, _Layout>::sym_mat_lu_decomp(dev, LU_NUMERICAL_DECOMP, lA.getData(), data, lA.getRows(), work.getData(), error.device());
		}
		if (steps & LU_BACK_SOLVE) {
			CHECK(data != 0);
			MatOps<_ValT, _IdxT, _Layout>::sym_mat_lu_decomp(dev, LU_BACK_SOLVE, lA.getData(), data, lA.getRows(), work.getData(), error.device());
		}

		error.toHost();
		return error.host();

		#else
		if constexpr (std::is_same<_ValT, double>::value){

		
		_IdxT n = lA.getRows();
		auto pA = lA.getData();
		_IdxT one = 1;
		_IdxT info;

		auto cpu = Device();
		MatrixT<_IdxT, _IdxT> ipiv(n, 1, cpu);
		_IdxT lwork = n;
		MatrixT<_ValT, _IdxT> work(n, 1, cpu);


		::dsysv_("l", &n, &one, pA, &n, ipiv.getData(), x->getData(), &n, work.getData(), &lwork, &info);
		}
		return 0;
	#endif
	}


	MatrixT add(const MatrixT& B) const {
		MatrixT C;
		add(B, C);
		return C;
	}

	void add(const MatrixT& B, MatrixT& C) const {
		auto& A = *this;
		matadd(1, A, 1, B, C);
	}
	static void matadd(_ValT a, const MatrixT& A, _ValT b, const MatrixT& B, MatrixT& C) {
		CHECK(A.getRows() == B.getRows() && A.getCols() == B.getCols()) << "add: A and B must has same dim";
		CHECK(A.getDevice() == B.getDevice()) << "add: A and B must on the same device";
		if (C.getRows() != A.getRows() || C.getCols() != A.getCols() || C.getDevice()!=A.getDevice()) {
			C.create(A.getRows(), A.getCols(), A.getDevice());
		}
		
		BlasOps<_ValT, _IdxT>::axpbypcz(A.getDevice(), A.getSize(), a, A.getData(), b, B.getData(), 0, C.getData());
	}

	void getDiag(MatrixT<_ValT, _IdxT>& diag) const {
		_IdxT size = std::min(getRows(), getCols());
		if (size == 0) {
			diag = MatrixT<_ValT, _IdxT>();
			return;
		}
		diag.resize(size, 1, getDevice());
		MatOps<_ValT, _IdxT, _Layout>::get_diag(getDevice(), getRows(), getCols(), getData(), diag.getSize(), diag.getData());
	}

	MatrixT<_ValT, _IdxT> getDiag() const {
		MatrixT<_ValT, _IdxT> diag;
		getDiag(diag);
		return diag;
	}
	void setDiag(const MatrixT<_ValT, _IdxT>& diag) const {
		CHECK(diag.getSize() == getRows() || diag.getSize() == getCols());
		MatOps<_ValT, _IdxT, _Layout>::set_diag(getDevice(), getRows(), getCols(), getData(), diag.getSize(), diag.getData());
	}



	void multiply(const MatrixT& mat2, MatrixT& prod) const
	{
		const auto& mat1 = *this;
		_IdxT row1 = mat1.getRows();
		_IdxT col1 = mat1.getCols();
		_IdxT row2 = mat2.getRows();
		_IdxT col2 = mat2.getCols();
		
		CHECK(mat1.getDevice() == mat2.getDevice()) << "multiply: mat1.device!= mat2.device";
		CHECK(col1 == row2) << "multiply: mat1.col1 != mat2.row2";
		prod.resize(row1, col2, mat1.getDevice());

		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {
		
		for (_IdxT i = 0; i < row1; i++)
			for (_IdxT j = 0; j < col2; j++) {
				_ValT sum = _ValT(0);
				for (_IdxT k = 0; k < col1; k++)
				{
					sum += mat1(i,k) * mat2(k, j);
				}
				prod(i,j) = sum;
			}
		
		} else {
		
		MatOps<_ValT, _IdxT, _Layout>::matmat(mat1.getDevice(), mat1.getRows(), mat1.getCols(), mat2.getCols(), 
		mat1.getData(), mat2.getData(), prod.getData());
		
		}
	}
	MatrixT multiply(const MatrixT& mat) const {
		MatrixT prod;
		multiply(mat, prod);
		return prod;
	}

	void transpose(MatrixT& trans) const
	{
		_IdxT row = getRows();
		_IdxT col = getCols();
		trans.resize(col, row, getDevice());
	
		if constexpr (!IS_INSTANTIATION_TYPE(_ValT)) {

		for (_IdxT i = 0; i < row; i++)
			for (_IdxT j = 0; j < col; j++)
				trans(j, i) = (*this)(i, j);
		} else {
		MatOps<_ValT, _IdxT, _Layout>::transpose(getDevice(), getRows(), getCols(), getData(), trans.getData());
		}
	}

	MatrixT transpose() const {
		MatrixT trans;
		transpose(trans);
		return trans;
	}

	void min_max_sum(_ValT* min, _ValT* max, _ValT* sum) const {
		BlasOps<_ValT, _IdxT>::min_max_sum(getDevice(), getSize(), getData(), min, max, sum);
	}


	_ValT getElementValue(_IdxT i, bool *exists = 0) const {
		return getElementValue(i, 0, exists);
	}
	bool setElementValue(_IdxT i, const _ValT &value) {
		return setElementValue(i, 0, value);
	}
	_ValT getElementValue(_IdxT i, _IdxT j, bool *exists = 0) const {
		if (i < 0 || i >= getRows() || j < 0 || j >= getCols()) {
			if (exists) *exists = false;
			return _ValT(0);
		}
		else {
			if (exists) *exists = true;
			MatrixT ret(1, 1, getDevice());
			MatOps<_ValT, _IdxT, _Layout>::get_element_value(getDevice(), getRows(), getCols(), getData(), i, j, ret.getData());
			MatrixT retHost = ret.toDevice(Device(Device::CPU));
			return retHost.getData()[0];
		}
	}

	bool setElementValue(_IdxT i, _IdxT j, const _ValT &value) {
		if (i < 0 || i >= getRows() || j < 0 || j >= getCols()) {
			return false;
		} else {
			MatOps<_ValT, _IdxT, _Layout>::set_element_value(getDevice(), getRows(), getCols(), getData(), i, j, value);
			return true;
		}
	}

	int getStreamSize() const {
		using namespace comu;
		int nbytes = 0;
		nbytes += comu::getStreamSize(getRows());
		nbytes += comu::getStreamSize(getCols());
		nbytes += comu::getStreamSize(getData(), getSize());
		return nbytes;
	}

	void packStream(comu::Stream& stream) const {
		using namespace comu;
		comu::packStream(stream, getRows());
		comu::packStream(stream, getCols());
		comu::packStream(stream, getData(), getSize());
	}

	void unpackStream(comu::Stream& stream) {
		using namespace comu;
		_IdxT rows, cols;
		comu::unpackStream(stream, rows);
		comu::unpackStream(stream, cols);
		create(rows, cols, getDevice());
		comu::unpackStream(stream, getData(), getSize());
	}

	void loadFromFile(const std::string& filename) {
		std::ifstream ifs(filename);
		loadFromStream(ifs);
	}

	void loadFromStream(std::istream& ifs) {
		if (!ifs) {
			return;
		}
		auto& A = *this;
		_IdxT m, n;

		std::string line;
		while(std::getline(ifs, line)) {

			if (line.size() == 0 || line[0] == '%') {
				continue;
			} else {
				auto items = stringSplit(line, "[ \t]+");
				// for (auto& item : items) {
				// 	LOG(INFO) << "loading dense matrix " << item;
				// }
				if (items.size() == 2) {
					m = atol(items[0].c_str());
					n = atol(items[1].c_str());
				} else if (items.size() == 1) {
					m = atol(items[0].c_str());
					n = 1;
				} else {
					LOG(FATAL) << "invalid matrix format";
				}
				break;
			}
		}
		//LOG(INFO) << "loading dense matrix " << m << " " << n << std::endl;
		create(m, n, Device(Device::CPU));
		auto rows = A.getRows();
		auto cols = A.getCols();
		auto data = A.getData();

		for (_IdxT i = 0; i<rows; i++) {
			for (_IdxT j = 0; j<cols; j++) {
				_IdxT idx = i * cols + j;
				ifs >> A(i, j);
			}
		}
	}

	void saveToFile(const std::string& filename, int prec = -1) const {
		std::string format = "mtx";
		
		auto split = stringSplit(filename, "\\.");
		if (split.size() > 0 && split.back().size() > 0) {
			format = split.back();
		}
		std::ofstream ofs(filename);

		if (format == "mtx") {
			saveToStream(ofs, prec);
		} else if (format == "raw") {
			saveToStreamRaw(ofs, prec);
		}
	}
	void saveToStream(std::ostream& ofs, int prec = -1) const {
		auto& A = *this;
		if (prec <= 0) {
			prec = Math::precision<_ValT>();
		}
		auto rows = A.getRows();
		auto cols = A.getCols();
		auto data = A.getData();

		ofs << "%%MatrixMarket matrix array "<< (IS_COMPLEX_TYPE(_ValT) ? "complex" : "real")  << " general" << std::endl;
		ofs << rows << " " << cols << std::endl;

		bool elem_break = Utils::isStrictMatrixMarket();
		for (_IdxT i = 0; i<rows; i++) {
			for (_IdxT j = 0; j<cols; j++) {
				ofs << std::setiosflags(std::ios::scientific) << std::setprecision(prec) << A(i, j);
				if (elem_break) {
					ofs << "\n";
				} else {
					ofs << (j == cols-1 ? "\n" : " ");
				}
			}
		}
	}
	void saveToStreamRaw(std::ostream& ofs, int prec = -1) const {
		auto& A = *this;
		if (prec <= 0) {
			prec = Math::precision<_ValT>();
		}
		auto size = A.getSize();
		auto data = A.getData();

		ofs << size << std::endl;

		for (_IdxT i = 0; i<size; i++) {
			ofs << std::setiosflags(std::ios::scientific) << std::setprecision(prec) << data[i] << std::endl;
		}
	}
	



protected:
	struct MatrixImpl
	{
		_IdxT rows = 0;
		_IdxT cols = 0;
		_ValT* data = 0;
		_IdxT capacity = 0;
		Device device;
		~MatrixImpl() {
			if (data != 0) {
				device.free(data);
				data = 0;
			}
		}
	};
	// implementation
	std::shared_ptr<MatrixImpl> m_impl;
};

template<class _ValT, class _IdxT, class _Layout>
std::ostream& operator<<(std::ostream& os, const MatrixT<_ValT, _IdxT, _Layout>& mat) {
	auto cpu = Device(Device::CPU);
	mat.toDevice(cpu).saveToStream(os);
	return os;
}
template<class _ValT, class _IdxT, class _Layout>
std::ostream& operator>>(std::ostream& os, MatrixT<_ValT, _IdxT, _Layout>& mat) {
	mat.loadFromStream(os);
	return os;
}

template<class _ValT, class _IdxT, class _Layout>
MatrixT<_ValT, _IdxT, _Layout> operator*(const _ValT& a, MatrixT<_ValT, _IdxT, _Layout>& mat) {
	MatrixT<_ValT, _IdxT, _Layout> ret = mat.deepCopy();
	MatrixT<_ValT, _IdxT, _Layout>scale(a, ret);
	return ret;
}

template<class _ValT, class _IdxT, class _Layout>
MatrixT<_ValT, _IdxT, _Layout> operator*(MatrixT<_ValT, _IdxT, _Layout>& mat, const _ValT& a) {
	MatrixT<_ValT, _IdxT, _Layout> ret = mat.deepCopy();
	MatrixT<_ValT, _IdxT, _Layout>scale(a, ret);
	return ret;
}




template <class _ValT>
std::string vec2str(const _ValT* data, size_t N) {
    std::ostringstream oss;
    oss << "[";
    for (size_t i=0; i<N; i++) {
        oss << data[i] << (i == N-1 ? "" : ",");
    }
    oss << "]";
    return oss.str();
}


template <class _ValT, class _IdxT>
std::string vec2str(const MatrixT<_ValT, _IdxT>& vec) {
    return vec2str(vec.getData(), vec.getSize());
}

template <class _ValT>
std::string vec2str(const std::vector<_ValT>& vec) {
    return vec2str(vec.data(), vec.size());
}

}
