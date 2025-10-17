#pragma once

#include "Matrix.hpp"
#include <vector>
#include <algorithm>
#include <cmath>
#include <cassert>
#include <cstdlib>
#include <map>
#include <unordered_map>
#include <functional>
#include <memory>
#include <fstream>
#include <sstream>
#include "hipo/ops/CrossOpTypes.hpp"
#include "hipo/ops/SpBlasOps.hpp"
#include "hipo/comm/Stream.h"

namespace hipo {

template <typename _ValT, typename _RowIdxT, typename _ColIdxT>
class HIPO_WIN_API COOMatrixT;

template<class _ValT, class _IdxT>
class CSRMatrixT
{
public:
	// 类型定义
	typedef _IdxT index_type;
	typedef _ValT value_type;
	typedef _ValT* pointer;
	typedef const _ValT* const_pointer;
	typedef _ValT& reference;
	typedef const _ValT& const_reference;

public:
	void create(_IdxT rows = 0, _IdxT cols = 0, _IdxT nnzs = 0, const Device& device = Device())
	{
		m_impl = std::make_shared<CSRMatrixImpl>();
		m_impl->device = device;
		m_impl->rows = rows;
		m_impl->cols = cols;
		m_impl->nnzs = nnzs;

		if (rows > 0) {
			m_impl->row_ptr = device.template malloc<_IdxT>((rows+1));
		}
		if (nnzs > 0) {
			m_impl->col_idx = device.template malloc<_IdxT>(nnzs);
			m_impl->values = device.template malloc<_ValT>(nnzs);
		}
	}

	CSRMatrixT()
	{
		create();
	}
	CSRMatrixT(_IdxT row, _IdxT col, const Device& device)
	{
		create(row, col, 0, device);
	}
	CSRMatrixT(_IdxT row, _IdxT col, _IdxT nnz, const Device& device)
	{
		create(row, col, nnz, device);
	}
	~CSRMatrixT()
	{
		m_impl.reset();
	}

	// info retrieval
	Device getDevice() const {
		return m_impl->device;
	}

	_IdxT getRows() const
	{
		return m_impl->rows;
	}
	_IdxT getCols() const
	{
		return m_impl->cols;
	}
	_IdxT getNnzs() const
	{
		return m_impl->getNnzs();
	}

	_IdxT* getRowPtr() const {
		return m_impl->row_ptr;
	}
	_IdxT* getColIdx() const {
		return m_impl->col_idx;
	}
	_ValT* getValues() const {
		return m_impl->values;
	}

	// row == 0 或者 col == 0 就称为空矩阵
	bool isEmpty() const
	{
		return getRows() == 0 || getCols() == 0;
	}

	CSRMatrixT deepCopy() const {
		CSRMatrixT ret;
		deepCopy(ret);
		return ret;
	}


	MatrixT<_IdxT, _IdxT> getRowPtrArray() const {
		auto srcDev = getDevice();
		if (getRows() == 0) {
			return MatrixT<_IdxT, _IdxT>();
		}
		MatrixT<_IdxT, _IdxT> ret(getRows()+1, 1, srcDev);
		srcDev.copyTo(ret.getSize(), getRowPtr(), srcDev, ret.getData());
		return ret;
	}
	MatrixT<_IdxT, _IdxT> getColIdxArray() const {
		auto srcDev = getDevice();
		MatrixT<_IdxT, _IdxT> ret(getNnzs(), 1, srcDev);
		srcDev.copyTo(getNnzs(), getColIdx(), srcDev, ret.getData());
		return ret;
	}
	MatrixT<_ValT, _IdxT> getValuesArray() const {
		auto srcDev = getDevice();
		MatrixT<_ValT, _IdxT> ret(getNnzs(), 1, srcDev);
		srcDev.copyTo(getNnzs(), getValues(), srcDev, ret.getData());
		return ret;
	}

	void removeEmptyRows(MatrixT<_IdxT, _IdxT>& out) {
		Device dev = getDevice();
		CrossData<_IdxT> newRows(dev, 0);
		out.resize(getRows(), dev);
		BlasOps<_IdxT, _IdxT>::remove_empty_rows(dev, getRows(), getRowPtr(), newRows.device(), out.getData());
		newRows.toHost();
		m_impl->rows = newRows.host();
	}

	MatrixT<_IdxT, _IdxT> removeEmptyRows() {
		MatrixT<_IdxT, _IdxT> ret;
		removeEmptyRows(ret);
		return ret;
	}

	void deepCopy(CSRMatrixT& ret) const {
		if (ret.getRows() != getRows() || ret.getCols() != getCols() || ret.getNnzs() != getNnzs() || ret.getDevice()!= getDevice()) {
			ret.create(getRows(), getCols(), getNnzs(), getDevice());
		}
		if (getNnzs() == 0) {
			ret = CSRMatrixT();
			return;
		}
		auto srcDev = getDevice();
		srcDev.copyTo(getRows()+1, getRowPtr(), srcDev, ret.getRowPtr());
		srcDev.copyTo(getNnzs(), getColIdx(), srcDev, ret.getColIdx());
		srcDev.copyTo(getNnzs(), getValues(), srcDev, ret.getValues());
	}

	CSRMatrixT toDevice(const Device& device) const {
		CSRMatrixT ret;
		toDevice(device, ret);
		return ret;
	}
	void toDevice(const Device& device, CSRMatrixT& ret) const {
		auto srcDev = getDevice();
		if (ret.getRows() != getRows() || ret.getCols() != getCols() || ret.getNnzs() != getNnzs() || ret.getDevice()!= device) {
			ret.create(getRows(), getCols(), getNnzs(), device);
		}
		if (getNnzs() == 0) {
			ret = CSRMatrixT();
			return;
		}
		srcDev.copyTo(getRows()+1, getRowPtr(), device, ret.getRowPtr());
		srcDev.copyTo(getNnzs(), getColIdx(), device, ret.getColIdx());
		srcDev.copyTo(getNnzs(), getValues(), device, ret.getValues());
	}

	template <class _NewValT>
	void toType(CSRMatrixT<_NewValT, _IdxT>& ret) const {
		if (ret.getRows() != getRows() || ret.getCols() != getCols() || ret.getNnzs() != getNnzs() || ret.getDevice()!= getDevice()) {
			ret.create(getRows(), getCols(), getNnzs(), getDevice());
		}
		if (getNnzs() == 0) {
			ret = CSRMatrixT<_NewValT, _IdxT>();
			return;
		}
		BlasOps<_IdxT, _IdxT>::copy(getDevice(), getRows()+1, getRowPtr(), ret.getRowPtr());
		BlasOps<_IdxT, _IdxT>::copy(getDevice(), getNnzs(), getColIdx(), ret.getColIdx());
		MixedBlasOps<_NewValT, _ValT, _IdxT>::copy(getDevice(), getNnzs(), getValues(), ret.getValues());
	}

	void resize(_IdxT rows, _IdxT cols, const Device& device) {
		if (rows == getRows() && device == getDevice()) {
			m_impl->cols = cols;
			return;
		}
		
		getDevice().free(m_impl->row_ptr);
		getDevice().free(m_impl->col_idx);
		getDevice().free(m_impl->values);
		m_impl->rows = rows;
		m_impl->cols = cols;
		m_impl->nnzs = 0;
		m_impl->device = device;
		if (rows > 0) {
			m_impl->row_ptr = device.template malloc<_IdxT>(rows+1);
		}
		// copy existing data
		// TBD
	}

	void resize(_IdxT rows, _IdxT cols) {
		resize(rows, cols, getDevice());
	}
	void resizeNnz(_IdxT nnzs, _IdxT cols = 0) {
		CHECK(m_impl->col_idx == 0 && m_impl->values == 0);
		if (cols > 0) {
			m_impl->cols = cols;
		}
		if (getNnzs() == nnzs) {
			return;
		}
		auto device = getDevice();
		
		m_impl->nnzs = nnzs;
		if (nnzs > 0) {
			m_impl->col_idx = device.template malloc<_IdxT>(nnzs);
			m_impl->values = device.template malloc<_ValT>(nnzs);
		}
		// copy existing data
		// TBD
	}


	static CSRMatrixT rand(_IdxT m, _IdxT n, float sparsity = 0.3);

	template <class _GlobalIdxT, class LocalIdxT>
	static CSRMatrixT<_ValT, _IdxT> mergeRows(const PartitionerT<_GlobalIdxT, LocalIdxT>& partitioner, const std::vector<CSRMatrixT<_ValT, _IdxT>>& blks)
	{
		_IdxT M = blks.size();
		if (M == 0) {
			return CSRMatrixT<_ValT, _IdxT>();
		}

		_IdxT rows = 0;
		_IdxT nnzs = 0;
		_IdxT cols = 0;
		Device device;

		_IdxT nnzBlks = 0;
		for (_IdxT i=0; i<blks.size(); i++) {
			auto& blk = blks[i];
			if (blk.getNnzs() == 0) {
				rows += partitioner.getLocalSizeForPart(i);
				continue;
			}
			if (cols == 0) {
				cols = blk.getCols();
				device = blk.getDevice();
			}
			nnzBlks+=1;
			rows += blk.getRows();
			CHECK(cols == blk.getCols()) << "merge: submat column size should be equal";
			nnzs += blk.getNnzs();
			CHECK(device == blk.getDevice()) << "merge: submat should on the same device";
		}
		CSRMatrixT<_ValT, _IdxT> mat(rows, cols, nnzs, device);

		if (rows == 0 || cols == 0) {
			return mat;
		}

#if 1
		// 第一个矩阵为空时，存在问题。
		COT_CSRRawMat<_ValT, _IdxT> matRaw, blkRaw;
		mat.getRawMat(matRaw);
		_IdxT row_start = 0;
		_IdxT nnz_start = 0;
		// 如果是一个空矩阵该怎么处理？
		for (_IdxT i=0; i<blks.size(); i++) {
			blks[i].getRawMat(blkRaw);
			if (blkRaw.row_ptr == 0) {
				blkRaw.rows = partitioner.getLocalSizeForPart(i);
			}
			SpBlasOps<_ValT, _IdxT>::csr_append_rows(mat.getDevice(), matRaw, row_start, nnz_start, blkRaw);
			row_start += blkRaw.rows;
			nnz_start += blkRaw.nnzs;
		}
#else
		MatrixT<COT_MergeCSRRawMat<_ValT, _IdxT>, _IdxT> blkVecs(nnzBlks, Device());
		auto blkData = blkVecs.getData();
		_IdxT cnt = 0;
		for (_IdxT i=0; i<blks.size(); i++) {
			auto& blk = blks[i];
			if (blk.getNnzs() == 0) {
				continue;
			}
			blk.getRawMat(blkData[cnt]);
			_GlobalIdxT begin, end;
			partitioner.getOwnerShipRangeForPart(i, &begin, &end);
			blkData[cnt].shift = begin;
			cnt++;
		}
		auto blkVecsDev = blkVecs.toDevice(device);
		COT_MergeCSRRawMat<_ValT, _IdxT> matRaw;
		mat.getRawMat(matRaw);
		SpBlasOps<_ValT, _IdxT>::csr_merge_rows(mat.getDevice(), blkVecsDev.getSize(), blkVecsDev.getData(), matRaw);

		_IdxT nnzsAcc = mat.evaluateNnzs();

		CHECK(nnzs == nnzsAcc) << "nnz not equal";
		mat.resizeNnz(nnzsAcc);
		mat.getRawMat(matRaw);
		SpBlasOps<_ValT, _IdxT>::csr_merge_rows(mat.getDevice(), blkVecsDev.getSize(), blkVecsDev.getData(), matRaw);
#endif
		return mat;
	}

	template <class _GlobalIdxT, class LocalIdxT>
	void splitRows(const PartitionerT<_GlobalIdxT, LocalIdxT>& partitioner, std::vector<CSRMatrixT<_ValT, _IdxT>>& blks) const
	{
		if (getNnzs() == 0) {
			blks.clear();
			return;
		}
		CHECK(this->getRows() == partitioner.getGlobalSize()) << "splitRows: rows.size() != partitioner.getGlobalSize()";
		blks.resize(partitioner.getNumParts());
		for (_IdxT k=0; k<partitioner.getNumParts(); k++) {
			auto& blk = blks[k];
			_GlobalIdxT begin, end;
			partitioner.getOwnerShipRangeForPart(k, &begin, &end);
			MatrixT<_IdxT, _IdxT> rowIds = MatrixT<_IdxT, _IdxT>::range(begin, end).toDevice(getDevice());
			getSelectedRows(rowIds, blk);
		}
	}

	template <class _GlobalIdxT, class LocalIdxT>
	static CSRMatrixT<_ValT, _IdxT> mergeCols(const PartitionerT<_GlobalIdxT, LocalIdxT>& partitioner, const std::vector<CSRMatrixT<_ValT, _IdxT>>& blks)
	{
		_IdxT M = blks.size();
		if (M == 0) {
			return CSRMatrixT<_ValT, _IdxT>();
		}

		_IdxT rows = 0;
		_IdxT nnzs = 0;
		_IdxT cols = 0;
		Device device;

		_IdxT nnzBlks = 0;
		for (_IdxT i=0; i<blks.size(); i++) {
			auto& blk = blks[i];
			if (blk.getNnzs() == 0) {
				cols += partitioner.getLocalSizeForPart(i);
				continue;
			}
			if (rows == 0) {
				rows = blk.getRows();
				device = blk.getDevice();
			}
			nnzBlks+=1;
			cols += blk.getCols();
			CHECK(rows == blk.getRows()) << "merge: submat row size should be equal";
			nnzs += blk.getNnzs();
			CHECK(device == blk.getDevice()) << "merge: submat should on the same device";
		}
		CSRMatrixT<_ValT, _IdxT> mat(rows, cols, 0, device);

		if (rows == 0 || cols == 0) {
			return mat;
		}

		MatrixT<COT_MergeCSRRawMat<_ValT, _IdxT>, _IdxT> blkVecs(nnzBlks, Device());
		auto blkData = blkVecs.getData();
		_IdxT cnt = 0;
		for (_IdxT i=0; i<blks.size(); i++) {
			auto& blk = blks[i];
			if (blk.getNnzs() == 0) {
				continue;
			}
			blk.getRawMat(blkData[cnt]);
			_GlobalIdxT col_begin;
			partitioner.getOwnerShipRangeForPart(i, &col_begin, 0);
			blkData[cnt].col_start = col_begin;
			cnt++;
		}
		auto blkVecsDev = blkVecs.toDevice(device);
		COT_MergeCSRRawMat<_ValT, _IdxT> matRaw;
		mat.getRawMat(matRaw);
		SpBlasOps<_ValT, _IdxT>::csr_merge_cols(mat.getDevice(), blkVecsDev.getSize(), blkVecsDev.getData(), matRaw);

		_IdxT nnzsAcc = mat.evaluateNnzs();

		CHECK(nnzs == nnzsAcc) << "nnz not equal";
		mat.resizeNnz(nnzsAcc);
		mat.getRawMat(matRaw);
		SpBlasOps<_ValT, _IdxT>::csr_merge_cols(mat.getDevice(), blkVecsDev.getSize(), blkVecsDev.getData(), matRaw);
		return mat;
	}

	template <class _GlobalIdxT, class LocalIdxT>
	void splitCols(const PartitionerT<_GlobalIdxT, LocalIdxT>& partitioner, std::vector<CSRMatrixT<_ValT, _IdxT>>& blks) const
	{
		if (getNnzs() == 0) {
			blks.clear();
			return;
		}
		CHECK(this->getCols() == partitioner.getGlobalSize()) << "splitRows: rows.size() != partitioner.getGlobalSize()";
		blks.resize(partitioner.getNumParts());
		if (blks.size() == 1) {
			blks[0] = *this;
			return;
		}
		#if 1
		for (_IdxT k=0; k<partitioner.getNumParts(); k++) {
			auto& blk = blks[k];
			_GlobalIdxT begin, end;
			partitioner.getOwnerShipRangeForPart(k, &begin, &end);
			getSelectedCols(begin, end, blk, -begin);
		}
		#else
		for (_IdxT k=0; k<partitioner.getNumParts(); k++) {
			auto& blk = blks[k];
			_GlobalIdxT begin, end;
			partitioner.getOwnerShipRangeForPart(k, &begin, &end);
			blk.resize(getRows(), end-begin);
		}
		auto dev = getDevice();
		auto cpu = Device();
		_IdxT n = partitioner.getNumParts();

		auto part = partitioner.getPartition();
		auto part_dev = part.toDevice(dev);

		COT_CSRRawMat<_ValT, _IdxT> origMatRaw;
		this->getRawMat(origMatRaw);
		MatrixT<COT_CSRRawMat<_ValT, _IdxT>, _IdxT> colmat_arr(n, cpu);
		auto colmat_arr_data = colmat_arr.getData();
		for (_IdxT i=0; i<n; i++) {
			blks[i].getRawMat(colmat_arr_data[i]);
		}
		auto colmat_arr_dev = colmat_arr.toDevice(dev);
		
		SpBlasOps<_ValT, _IdxT>::csr_split_cols(dev, CSRMAT_CALC_NNZ, origMatRaw, n, part_dev.getData(), colmat_arr_dev.getData(),  true);

		for (_IdxT i=0; i<n; i++) {
			_IdxT nnzs = blks[i].evaluateNnzs();
			blks[i].resizeNnz(nnzs);
			blks[i].getRawMat(colmat_arr_data[i]);
		}

		colmat_arr_dev = colmat_arr.toDevice(dev);
		SpBlasOps<_ValT, _IdxT>::csr_split_cols(dev, CSRMAT_FILL_NNZ, origMatRaw, n, part_dev.getData(), colmat_arr_dev.getData(),  true);

		#endif
	}

	void getSelectedRows(const MatrixT<_IdxT, _IdxT>& rowIds, CSRMatrixT<_ValT, _IdxT>& rowMat, bool sameRows = false) const {
		_IdxT nrows = sameRows ? getRows() : rowIds.getSize();
		if (nrows <= 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.create(nrows, getCols(), 0, getDevice());
		COT_CSRRawMat<_ValT, _IdxT> thisRaw, rowMatRaw;
		this->getRawMat(thisRaw);
		rowMat.getRawMat(rowMatRaw);

		SpBlasOps<_ValT, _IdxT>::get_selected_rows(getDevice(), thisRaw, rowIds.getSize(), rowIds.getData(), rowMatRaw, sameRows);

		_IdxT nnzs = rowMat.evaluateNnzs();
		if (nnzs == 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.resizeNnz(nnzs);
		rowMat.getRawMat(rowMatRaw);
		SpBlasOps<_ValT, _IdxT>::get_selected_rows(getDevice(), thisRaw, rowIds.getSize(), rowIds.getData(), rowMatRaw, sameRows);
	}

	void getSelectedCols(const MatrixT<_IdxT, _IdxT>& rowIds, CSRMatrixT<_ValT, _IdxT>& rowMat, _IdxT col_shift) const {
		_IdxT ncols = rowIds.getSize();
		if (ncols <= 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.create(getRows(), ncols, 0, getDevice());
		COT_CSRRawMat<_ValT, _IdxT> thisRaw, rowMatRaw;
		this->getRawMat(thisRaw);
		rowMat.getRawMat(rowMatRaw);

		SpBlasOps<_ValT, _IdxT>::get_selected_cols(getDevice(), thisRaw, rowIds.getSize(), rowIds.getData(), rowMatRaw, col_shift);

		_IdxT nnzs = rowMat.evaluateNnzs();
		if (nnzs == 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.resizeNnz(nnzs);
		rowMat.getRawMat(rowMatRaw);
		SpBlasOps<_ValT, _IdxT>::get_selected_cols(getDevice(), thisRaw, rowIds.getSize(), rowIds.getData(), rowMatRaw, col_shift);
	}

	void getSelectedCols(_IdxT col_start, _IdxT col_end, CSRMatrixT<_ValT, _IdxT>& rowMat, _IdxT col_shift) const {
		_IdxT ncols = col_end - col_start;
		if (ncols <= 0 || this->getNnzs() <= 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.create(getRows(), ncols, 0, getDevice());
		COT_CSRRawMat<_ValT, _IdxT> thisRaw, rowMatRaw;
		this->getRawMat(thisRaw);
		rowMat.getRawMat(rowMatRaw);

		SpBlasOps<_ValT, _IdxT>::get_selected_cols_v3(getDevice(), thisRaw, col_start, col_end, rowMatRaw, col_shift);

		_IdxT nnzs = rowMat.evaluateNnzs();
		if (nnzs == 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}

		rowMat.resizeNnz(nnzs);
		rowMat.getRawMat(rowMatRaw);
		SpBlasOps<_ValT, _IdxT>::get_selected_cols_v3(getDevice(), thisRaw, col_start, col_end, rowMatRaw, col_shift);
	}

	void getSelectedCols(const MatrixT<_IdxT, _IdxT>& start, const MatrixT<_IdxT, _IdxT>& end, CSRMatrixT<_ValT, _IdxT>& rowMat, _IdxT col_shift = 0) const {
		_IdxT ncols = getCols();
		if (ncols <= 0 || this->getNnzs() <= 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.create(getRows(), ncols, 0, getDevice());
		COT_CSRRawMat<_ValT, _IdxT> thisRaw, rowMatRaw;
		this->getRawMat(thisRaw);
		rowMat.getRawMat(rowMatRaw);

		SpBlasOps<_ValT, _IdxT>::get_selected_cols_v2(getDevice(), thisRaw, start.getData(), end.getData(), rowMatRaw, col_shift);

		_IdxT nnzs = rowMat.evaluateNnzs();
		if (nnzs == 0) {
			rowMat = CSRMatrixT<_ValT, _IdxT>();
			return;
		}
		rowMat.resizeNnz(nnzs);
		rowMat.getRawMat(rowMatRaw);
		SpBlasOps<_ValT, _IdxT>::get_selected_cols_v2(getDevice(), thisRaw, start.getData(), end.getData(), rowMatRaw, col_shift);
	}

	void getRowElementCount(MatrixT<_IdxT, _IdxT>& count) const {
		if (count.getSize() != getRows() || count.getDevice() != getDevice()) {
			count.create(getRows(), getDevice());
		}
		count.fill(0);
		if (getRows() == 0) {
			return;
		}
		COT_CSRRawMat<_ValT, _IdxT> thisRaw;
		this->getRawMat(thisRaw);
		SpBlasOps<_ValT, _IdxT>::get_row_element_count(getDevice(), thisRaw, count.getSize(), count.getData());
	}
	void getColElementCount(MatrixT<_IdxT, _IdxT>& count) const {
		if (count.getSize() != getCols() || count.getDevice() != getDevice()) {
			count.create(getCols(), getDevice());
		}
		count.fill(0);
		if (getRows() == 0) {
			return;
		}
		COT_CSRRawMat<_ValT, _IdxT> thisRaw;
		this->getRawMat(thisRaw);
		SpBlasOps<_ValT, _IdxT>::get_col_element_count(getDevice(), thisRaw, count.getSize(), count.getData());
	}

	CSRMatrixT& operator += (const CSRMatrixT& B) {
		CSRMatrixT ret;
		this->add(B, ret);
		*this = ret;
		return *this;
	}

	CSRMatrixT add(const CSRMatrixT& B) const {
		CSRMatrixT C;
		add(B, C);
		return C;
	}

	void add(const CSRMatrixT& B, CSRMatrixT& C) const {
		const CSRMatrixT& A = *this;

		if (A.getNnzs() == 0) {
			C = B;
			return;
		}
		if (B.getNnzs() == 0) {
			C = A;
			return;
		}

		matadd(1, A, 1, B, C);
	}

	_ValT getElementValue(_IdxT i, _IdxT j, bool* exists) const {

		struct Ret {
			_ValT value;
			int exists;
		};
		MatrixT<Ret, _IdxT> retdata(1, 1, getDevice());

		SpBlasOps<_ValT, _IdxT>::get_element_value(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), 
		 	i, j, &retdata.getData()[0].value, &retdata.getData()[0].exists);
		
		auto ret = retdata.toDevice(Device());
		if (exists) {
			*exists = ret.getData()[0].exists != 0;
		}
		return ret.getData()[0].value;
	}
    bool setElementValue(_IdxT i, _IdxT j, const _ValT& value) {
		
		MatrixT<int, _IdxT> retdata(1, 1, getDevice());

		SpBlasOps<_ValT, _IdxT>::set_element_value(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), 
		 	i, j, value, retdata.getData());
		
		auto ret = retdata.toDevice(Device());
		return ret.getData()[0] != 0;
	}

	CSRMatrixT<_ValT, _IdxT> sparsify(typename TypeInfo<_ValT>::scalar_type threshold) const {
		auto& A = *this;
		CSRMatrixT<_ValT, _IdxT> ret(A.getRows(), A.getCols(), 0, A.getDevice());
		if (A.getNnzs() <= 0) {
			return ret;
		}
		COT_CSRRawMat<_ValT, _IdxT> A_raw, ret_raw;
		A.getRawMat(A_raw);
		ret.getRawMat(ret_raw);
		SpBlasOps<_ValT, _IdxT>::csr_sparsify(A.getDevice(), A_raw, threshold, 0, ret_raw);
		_IdxT nnzs = ret.evaluateNnzs();
		ret.resizeNnz(nnzs);
		ret.getRawMat(ret_raw);
		SpBlasOps<_ValT, _IdxT>::csr_sparsify(A.getDevice(), A_raw, threshold, 0, ret_raw);
		return ret;
	}

	CSRMatrixT<_ValT, _IdxT> sparsify(MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> threshold) const {
		auto& A = *this;
		CSRMatrixT<_ValT, _IdxT> ret(A.getRows(), A.getCols(), 0, A.getDevice());
		if (A.getNnzs() <= 0) {
			return ret;
		}
		COT_CSRRawMat<_ValT, _IdxT> A_raw, ret_raw;
		A.getRawMat(A_raw);
		ret.getRawMat(ret_raw);
		SpBlasOps<_ValT, _IdxT>::csr_sparsify(A.getDevice(), A_raw, 0, threshold.getData(), ret_raw);
		_IdxT nnzs = ret.evaluateNnzs();
		ret.resizeNnz(nnzs);
		ret.getRawMat(ret_raw);
		SpBlasOps<_ValT, _IdxT>::csr_sparsify(A.getDevice(), A_raw, 0, threshold.getData(), ret_raw);
		return ret;
	}

	void rowNorm(MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> &norm, typename TypeInfo<_ValT>::scalar_type p) const {
		norm.create(getRows(), getDevice());
		MatrixT<COT_SpMVCSRRawMat<_ValT, _IdxT>, _IdxT> blks;
		blks.resize(1, 1, Device());
		this->getRawMat(blks.getData()[0]);
		if (blks.getSize() <= 0) {
			return;
		}
		_IdxT rows = this->getRows();
		auto devBlks = blks.toDevice(getDevice());
		SpBlasOps<_ValT, _IdxT>::par_csr_row_norm_lp(getDevice(), rows, devBlks.getSize(), devBlks.getData(), p, norm.getData());
	}

	MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> rowNorm(typename TypeInfo<_ValT>::scalar_type p) const {
		MatrixT<typename TypeInfo<_ValT>::scalar_type, _IdxT> ret;
		rowNorm(ret, p);
		return ret;
	}

	int getStreamSize() const {
		using namespace comu;
		int nbytes = 0;
		nbytes += comu::getStreamSize(getRows());
		nbytes += comu::getStreamSize(getCols());
		nbytes += comu::getStreamSize(getNnzs());
		nbytes += comu::getStreamSize(getRowPtr(), getRows()+1);
		nbytes += comu::getStreamSize(getColIdx(), getNnzs());
		nbytes += comu::getStreamSize(getValues(), getNnzs());
		return nbytes;
	}

	void packStream(comu::Stream& stream) const {
		using namespace comu;
		comu::packStream(stream, getRows());
		comu::packStream(stream, getCols());
		comu::packStream(stream, getNnzs());
		comu::packStream(stream, getRowPtr(), getRows()+1);
		comu::packStream(stream, getColIdx(), getNnzs());
		comu::packStream(stream, getValues(), getNnzs());
	}

	void unpackStream(comu::Stream& stream) {
		using namespace comu;
		_IdxT rows, cols, nnzs;
		comu::unpackStream(stream, rows);
		comu::unpackStream(stream, cols);
		comu::unpackStream(stream, nnzs);
		create(rows, cols, nnzs, getDevice());
		comu::unpackStream(stream, getRowPtr(), getRows()+1);
		comu::unpackStream(stream, getColIdx(), getNnzs());
		comu::unpackStream(stream, getValues(), getNnzs());
	}


	std::string getString() const
    {
        std::ostringstream oss;
        return oss.str();
    }

	//// 稀疏矩阵数乘
	CSRMatrixT operator*(const_reference a) const
	{
		CSRMatrixT ret = deepCopy();
		BlasOps<_ValT, _IdxT>::scal(getDevice(), ret.getNnzs(), a, ret.getValues());
		return ret;
	}
	//// 稀疏矩阵负
	CSRMatrixT operator-() const
	{
		CSRMatrixT ret = deepCopy();
		BlasOps<_ValT, _IdxT>::scal(getDevice(), ret.getNnzs(), _ValT(-1), ret.getValues());
		return ret;
	}

	//// 矩阵填充
	void fill(_ValT a) const
	{
		BlasOps<_ValT, _IdxT>::fill(getDevice(), getNnzs(), a, getValues());
	}

	void toDense(MatrixT<_ValT, _IdxT>& ret) const {
		ret.resize(getRows(), getCols(), getDevice());
		SpBlasOps<_ValT, _IdxT>::csr2dense(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), ret.getData());
	}

	MatrixT<_ValT, _IdxT> toDense() const {
		MatrixT<_ValT, _IdxT> ret;
		toDense(ret);
		return ret;
	}


	//// 稀疏矩阵的转置, 为测试提供某些方便
	void transpose(CSRMatrixT& trans) const
	{
		if (getNnzs() == 0) {
			trans = CSRMatrixT();
			return;
		}
		if (trans.getRows() != getCols() || trans.getCols() != getRows() || trans.getNnzs() != getNnzs() || trans.getDevice()!= getDevice()) {
			trans.create(getCols(), getRows(), getNnzs(), getDevice());
		}
		SpBlasOps<_ValT, _IdxT>::csr_transpose(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(),
			trans.getRowPtr(), trans.getColIdx(), trans.getValues());
	}
	CSRMatrixT transpose() const
	{
		CSRMatrixT trans;
		transpose(trans);
		return trans;
	}

	void multiply(const CSRMatrixT& mat2, CSRMatrixT& prod) const
	{
		const auto& mat1 = *this;
		_IdxT row1 = mat1.getRows();
		_IdxT col1 = mat1.getCols();
		_IdxT row2 = mat2.getRows();
		_IdxT col2 = mat2.getCols();

		if (mat1.getNnzs() == 0 || mat2.getNnzs() == 0) {
			prod = CSRMatrixT();
			return;
		}
		
		CHECK(mat1.getDevice() == mat2.getDevice()) << "multiply: mat1.device!= mat2.device";
		CHECK(col1 == row2) << "multiply: mat1.col1 != mat2.row2";
		prod.resize(row1, col2, mat1.getDevice());


		MatrixT<_IdxT, _IdxT> work(col2, 1, mat1.getDevice());

		
		SpBlasOps<_ValT, _IdxT>::csr_matmul(mat1.getDevice(), mat1.getRawMat(), mat2.getRawMat(), prod.getRawMat(), work.getData());


		// 获取非零元素个数
		_IdxT nnzs;
		prod.getDevice().copyTo(1, prod.getRowPtr()+row1, Device(Device::CPU), &nnzs);
		prod.resizeNnz(nnzs);

		SpBlasOps<_ValT, _IdxT>::csr_matmul(mat1.getDevice(), mat1.getRawMat(), mat2.getRawMat(), prod.getRawMat(), work.getData());
	}

	template <class _NewValT>
	void copyStructure(CSRMatrixT<_NewValT, _IdxT>& strength) const {
		auto&A = *this;
		strength.create(A.getRows(), A.getCols(), A.getNnzs(), A.getDevice());
		if (getNnzs() == 0) {
			strength = CSRMatrixT<_NewValT, _IdxT>();
			return;
		}
    	A.getDevice().copyTo(A.getRows()+1, A.getRowPtr(), strength.getDevice(), strength.getRowPtr());
    	A.getDevice().copyTo(A.getNnzs(), A.getColIdx(), strength.getDevice(), strength.getColIdx());
	}

	void getDiag(MatrixT<_ValT, _IdxT>& diag) const {
		if (getNnzs() == 0) {
			diag = MatrixT<_ValT, _IdxT>();
			return;
		}
		diag.resize(getRows(), 1, getDevice());
		diag.fill(0);
		SpBlasOps<_ValT, _IdxT>::csr_diag(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), diag.getData(), 0, 0);
	}
	MatrixT<_ValT, _IdxT> getDiag() const {
		MatrixT<_ValT, _IdxT> diag;
		getDiag(diag);
		return diag;
	}

	void sortRows() {
		if (getNnzs() == 0) {
			return;
		}
		SpBlasOps<_ValT, _IdxT>::csr_sort_rows(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues());
	}
	CSRMatrixT multiply(const CSRMatrixT& mat2) const
	{
		CSRMatrixT prod;
		multiply(mat2, prod);
		return prod;
	}


	bool operator==(const CSRMatrixT& mat) const
	{
		CHECK(getDevice() == mat.getDevice());
		if (getRows() != mat.getRows() || getCols() != mat.getCols()) {
			return false;
		}
		CSRMatrixT diff;
		matadd(1, *this, -1, mat, diff);
		auto sum2 = BlasOps<_ValT, _IdxT>::abs_sum(diff.getDevice(), diff.getNnzs(), diff.getValues(), 2);
		return sum2 == 0;
	}
	bool operator!=(const CSRMatrixT& mat) const
	{
		return !((*this) == mat);
	}
	bool numericalEqual(const CSRMatrixT& mat, double factor = 100.0) const
	{
		CHECK(getDevice() == mat.getDevice());
		if (getRows() != mat.getRows() || getCols() != mat.getCols()) {
			return false;
		}
		CSRMatrixT diff;
		matadd(1, *this, -1, mat, diff);
		auto sum2 = BlasOps<_ValT, _IdxT>::abs_sum(diff.getDevice(), diff.getNnzs(), diff.getValues(), 2);
		typedef decltype(sum2) RetType;
		auto dist = std::sqrt(sum2);
		LOG(INFO) << "CSRMatrixT dist = " << dist;
		return Math::numericalEqual(RetType(0), dist, RetType(factor));
	}

	void aAxpby(_ValT a, const MatrixT<_ValT, _IdxT>& x, _ValT b, MatrixT<_ValT, _IdxT>& y) const {
		auto& A = *this;
		if (A.getNnzs() == 0 || x.getSize() == 0) {
			y = MatrixT<_ValT, _IdxT>();
			return;
		}
		if (b == 0) {
			y.resize(A.getRows(), x.getCols(), getDevice());
		}
		CHECK(x.getCols() == 1) << "aAxpby: x.cols!= 1";
		CHECK(A.getCols() == x.getRows()) << "aAxpby: A.cols != x.rows";
		CHECK(A.getDevice() == x.getDevice()) << "aAxpby: A and x must on the same device";
		CHECK(A.getRows() == y.getRows() && x.getCols() == y.getCols()) << "aAxpby: A.rows!= y.rows";
		CHECK(A.getDevice() == y.getDevice()) << "aAxpby: A and y must on the same device";

		SpBlasOps<_ValT, _IdxT>::aAxpby(A.getDevice(), a, A.getRows(), A.getCols(), A.getRowPtr(), A.getRowPtr()+1, A.getColIdx(), A.getValues(), x.getData(), b, y.getData());
	}

	void matVec(const MatrixT<_ValT, _IdxT>& x, MatrixT<_ValT, _IdxT>& y) const {
		auto& A = *this;
		y.resize(A.getRows(), x.getCols(), A.getDevice());
		aAxpby(_ValT(1), x, _ValT(0), y);
	}
	MatrixT<_ValT, _IdxT> matVec(const MatrixT<_ValT, _IdxT>& x) const {
		MatrixT<_ValT, _IdxT> ret;
		matVec(x, ret);
		return ret;
	}

	MatrixT<_ValT, _IdxT> operator*(const MatrixT<_ValT, _IdxT>& x) {
		return this->matVec(x);
	}
	// A = a*A
	static void scale(CSRMatrixT& A, _ValT a) {
		if (A.getNnzs() == 0) {
			return;
		}
		BlasOps<_ValT, _IdxT>::scal(A.getDevice(), A.getNnzs(), a, A.getValues());
	}

	// A = aDA
	static void matmul_aDA(_ValT a, const MatrixT<_ValT, _IdxT>& D, CSRMatrixT& A) {
		if (A.getNnzs() == 0) {
			return;
		}
		COT_MergeCSRRawMat<_ValT, _IdxT> Araw;
		A.getRawMat(Araw);
		SpBlasOps<_ValT, _IdxT>::csr_matmul_aDA(A.getDevice(), a, D.getData(), Araw);
	}

	// A = A*diag(a)
	static void matmul_aAD(_ValT a, const MatrixT<_ValT, _IdxT>& D, CSRMatrixT& A) {
		if (A.getNnzs() == 0) {
			return;
		}
		COT_SpMVCSRRawMat<_ValT, _IdxT> Araw;
		A.getRawMat(Araw);
		Araw.recv_x = D.getData();
		SpBlasOps<_ValT, _IdxT>::csr_matmul_aAD(A.getDevice(), a, Araw);
	}

	// diag(B) = a*x + b*diag(A), B = A for non diag elements
	static void axpbyDiag(_ValT a, const MatrixT<_ValT, _IdxT>& x, _ValT b, const MatrixT<_ValT, _IdxT>& y, const CSRMatrixT& A, CSRMatrixT& B, _IdxT row_start = 0, _IdxT col_start = 0) {
		if (A.getNnzs() == 0) {
			B = CSRMatrixT();
			return;
		}
		if (B.getRows() != A.getRows() || B.getCols() != A.getCols() || B.getDevice()!=A.getDevice()) {
			B.create(A.getRows(), A.getCols(), 0, A.getDevice());
		}
		COT_MergeCSRRawMat<_ValT, _IdxT> Araw, Braw;
		A.getRawMat(Araw);
		Araw.row_start = row_start;
		Araw.col_start = col_start;
		B.getRawMat(Braw);
		Braw.col_idx = 0;
		SpBlasOps<_ValT, _IdxT>::csr_axpby_diag(A.getDevice(), a, x.getData(), b, y.getData(), Araw, Braw);
		_IdxT nnzs = B.evaluateNnzs();
		B.resizeNnz(nnzs);
		B.getRawMat(Braw);
		SpBlasOps<_ValT, _IdxT>::csr_axpby_diag(A.getDevice(), a, x.getData(), b, y.getData(), Araw, Braw);
	}

	// Z = a*X+b*Y
	static void matadd(_ValT a, const CSRMatrixT<_ValT, _IdxT>& A, _ValT b, const CSRMatrixT<_ValT, _IdxT>& B, CSRMatrixT<_ValT, _IdxT>& C) {

		if (A.getNnzs() == 0) {
			C = B.deepCopy();
			scale(C, b);
			return;
		}
		if (B.getNnzs() == 0) {
			C = A.deepCopy();
			scale(C, a);
			return;
		}

		CHECK(A.getRows() == B.getRows() && A.getCols() == B.getCols()) << "add: A and B must has same dim";
		CHECK(A.getDevice() == B.getDevice()) << "add: A and B must on the same device";
		if (C.getRows() != A.getRows() || C.getCols() != A.getCols() || C.getDevice()!=A.getDevice()) {
			C.create(A.getRows(), A.getCols(), 0, A.getDevice());
		}
		COT_CSRRawMat<_ValT, _IdxT> rawA, rawB, rawC, raw_tmp;
		A.getRawMat(rawA);
		B.getRawMat(rawB);
		C.getRawMat(rawC);
		rawC.col_idx = 0;
		//MatrixT<HashTableSlot<_IdxT, _IdxT>,_IdxT> work(A.getNnzs()+B.getNnzs(), A.getDevice());
		CSRMatrixT<_ValT,_IdxT> tmp(A.getRows(), A.getCols(), A.getNnzs()+B.getNnzs(), A.getDevice());
		tmp.getRawMat(raw_tmp);
		SpBlasOps<_ValT, _IdxT>::csr_matadd(A.getDevice(), a, rawA, b, rawB, rawC, raw_tmp);
		_IdxT nnzs = C.evaluateNnzs();
		C.resizeNnz(nnzs);
		C.getRawMat(rawC);
		SpBlasOps<_ValT, _IdxT>::csr_matadd(A.getDevice(), a, rawA, b, rawB, rawC, raw_tmp);
	}

	static void matAddVec(const std::vector<CSRMatrixT<_ValT, _IdxT>>& Avec, CSRMatrixT<_ValT, _IdxT>& C) {

		if (Avec.size() == 0) {
			C = CSRMatrixT();
			return;
		}
		auto A = Avec[0];

		if (C.getRows() != A.getRows() || C.getCols() != A.getCols() || C.getDevice()!=A.getDevice()) {
			C.create(A.getRows(), A.getCols(), 0, A.getDevice());
		}
		MatrixT<COT_CSRRawMat<_ValT, _IdxT>, _IdxT> rawA(Avec.size(), Device());
		for (_IdxT i=0; i<Avec.size(); i++) {
			auto B = Avec[i];
			CHECK(A.getRows() == B.getRows() && A.getCols() == B.getCols()) << "add: A and B must has same dim";
			CHECK(A.getDevice() == B.getDevice()) << "add: A and B must on the same device";
			B.getRawMat(rawA.getData()[i]);
		}


		COT_CSRRawMat<_ValT, _IdxT> rawC;
		C.getRawMat(rawC);
		rawC.col_idx = 0;
		MatrixT<_IdxT,_IdxT> work(C.getCols(), A.getDevice());

		auto rawAdev = rawA.toDevice(A.getDevice());
		SpBlasOps<_ValT, _IdxT>::csr_matadd_vec(A.getDevice(), A.getRows(), rawAdev.getSize(), rawAdev.getData(), rawC, work.getData());
		_IdxT nnzs = C.evaluateNnzs();
		C.resizeNnz(nnzs);
		C.getRawMat(rawC);
		SpBlasOps<_ValT, _IdxT>::csr_matadd_vec(A.getDevice(), A.getRows(), rawAdev.getSize(), rawAdev.getData(), rawC, work.getData());
	}


	static void matFMAVec(const std::vector<CSRMatrixT<_ValT, _IdxT>>& Avec, const std::vector<CSRMatrixT<_ValT, _IdxT>>& Bvec, CSRMatrixT<_ValT, _IdxT>& C) {

		if (Avec.size() == 0) {
			C = CSRMatrixT();
			return;
		}
		CHECK(Avec.size() == Bvec.size()) << "matFMAVec size should equal";
		auto& A = Avec[0];
		auto& B = Bvec[0];

		auto device = A.getDevice();

		if (C.getRows() != A.getRows() || C.getCols() != B.getCols() || C.getDevice()!=device) {
			C.create(A.getRows(), B.getCols(), 0, device);
		}
		MatrixT<COT_CSRRawMat<_ValT, _IdxT>, _IdxT> rawA(Avec.size(), Device());
		MatrixT<COT_CSRRawMat<_ValT, _IdxT>, _IdxT> rawB(Bvec.size(), Device());
		for (_IdxT i=0; i<Avec.size(); i++) {
			auto& Ai = Avec[i];
			auto& Bi = Bvec[i];
			CHECK(A.getRows() == Ai.getRows() && B.getCols() == Bi.getCols()) << "add: A and Ai must has same dim";
			CHECK(Ai.getDevice() == Bi.getDevice()) << "add: A and B must on the same device";
			Ai.getRawMat(rawA.getData()[i]);
			Bi.getRawMat(rawB.getData()[i]);
		}


		COT_CSRRawMat<_ValT, _IdxT> rawC;
		C.getRawMat(rawC);
		rawC.col_idx = 0;
		MatrixT<_IdxT,_IdxT> work(C.getCols(), device);

		auto rawAdev = rawA.toDevice(device);
		auto rawBdev = rawB.toDevice(device);
		SpBlasOps<_ValT, _IdxT>::csr_mat_fma_vec(device, A.getRows(), rawAdev.getSize(), rawAdev.getData(), rawBdev.getData(), rawC, work.getData());
		_IdxT nnzs = C.evaluateNnzs();
		C.resizeNnz(nnzs);
		C.getRawMat(rawC);
		SpBlasOps<_ValT, _IdxT>::csr_mat_fma_vec(device, A.getRows(), rawAdev.getSize(), rawAdev.getData(), rawBdev.getData(),rawC, work.getData());
	
		if (0) {
		for (_IdxT i=0; i<Avec.size(); i++) {
			LOG(INFO) << "A is " << i << std::endl;
			Avec[i].saveToStreamRaw2(LOG(INFO));
			LOG(INFO) << "B is " << i << std::endl;
			Bvec[i].saveToStreamRaw2(LOG(INFO));

		}
		LOG(INFO) << "result C is " << std::endl;
		C.saveToStreamRaw2(LOG(INFO));
		}
	}




	// 稀疏矩阵的sor
	void sor(const MatrixT<_ValT, _IdxT>& b, MatrixT<_ValT, _IdxT>& x, double omega, bool forward) const {
	    SpBlasOps<_ValT, _IdxT>::sor(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), b.getData(), x.getData(), omega, forward, 0);
	}

	void jacobi(const MatrixT<_ValT, _IdxT>& b, MatrixT<_ValT, _IdxT>& x, double omega) const {
		MatrixT<_ValT, _IdxT> x_old = x.deepCopy();
	    SpBlasOps<_ValT, _IdxT>::jacobi(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), x_old.getData(), b.getData(), x.getData(), omega);
	}

	void jacobiDiagLp(const MatrixT<_ValT, _IdxT>& b, MatrixT<_ValT, _IdxT>& x, double omega, double order) const {
		MatrixT<_ValT, _IdxT> x_old = x.deepCopy();
	    SpBlasOps<_ValT, _IdxT>::jacobi_diagLp(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), x_old.getData(), b.getData(), x.getData(), omega, order, 0);
	}

	void richardson(const MatrixT<_ValT, _IdxT>& b, MatrixT<_ValT, _IdxT>& x, double omega) const {
	    MatrixT<_ValT, _IdxT>& x_old = x.deepCopy();
		SpBlasOps<_ValT, _IdxT>::jacobi(getDevice(), getRows(), getCols(), getRowPtr(), getColIdx(), getValues(), x_old.getData(), b.getData(), x.getData(), omega);
	}


	void loadFromFile(const std::string& filename) {
		std::ifstream ifs(filename);
		loadFromStream(ifs);
	}
	
	void loadFromStream(std::istream& ifs);

	void loadFromStreamRaw(std::istream& ifs) {
		if (!ifs) {
			return;
		}
		auto& csrMat = *this;

		int64_t nrows, ncols, nnzs;

		ifs >> nrows;
		ncols = nrows;
		csrMat.resize(nrows, ncols);
		auto row_ptr = csrMat.getRowPtr();
		for (_IdxT i=0; i<nrows + 1; i++) {
			ifs >> row_ptr[i];
			row_ptr[i]-=1;
		}
		nnzs = row_ptr[nrows];
		csrMat.resizeNnz(nnzs);
		auto col_idx = csrMat.getColIdx();
		for (_IdxT i=0; i<nnzs; i++) {
			ifs >> col_idx[i];
			col_idx[i]-=1;
		}
		auto values = csrMat.getValues();
		for (_IdxT i=0; i<nnzs; i++) {
			ifs >> values[i];
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
		auto m = A.getRows();
		auto n = A.getCols();
		auto nz = A.getNnzs();

		auto row_ptr = A.getRowPtr();
		auto col_idx = A.getColIdx();
		auto values = A.getValues();

		ofs << "%%MatrixMarket matrix coordinate " << (IS_COMPLEX_TYPE(_ValT) ? "complex" : "real") << " general" << std::endl;

		ofs << m << " " << n << " " << nz << std::endl;

		for (_IdxT i = 0; i < m; ++i) {
			for (_IdxT jj = row_ptr[i]; jj < row_ptr[i + 1]; jj++) {
				ofs << i + 1 << " " << col_idx[jj] + 1 << " " << std::setiosflags(std::ios::scientific)  << std::setprecision(prec) << values[jj] << std::endl;
			}
		}
	}

	void saveToStreamRaw2(std::ostream& ofs, int prec = -1) const {
		auto& csrMat = *this;

		if (prec <= 0) {
			prec = Math::precision<_ValT>();
		}

		ofs << csrMat.getRows() << " " << csrMat.getCols() << " " << csrMat.getNnzs() << "\n";
		
		_IdxT nrows = csrMat.getRows();

		if (nrows == 0) {
			return;
		}

		ofs << "csr row_ptr ";
		auto row_ptr = csrMat.getRowPtr();
		for (_IdxT i=0; i<nrows + 1; i++) {
			ofs << row_ptr[i] << " ";
		}
		ofs << std::endl;
		_IdxT nnzs = row_ptr[nrows];

		if (1) {
			ofs << "csr idx\tcol_idx\tvalues\n";
			auto col_idx = csrMat.getColIdx();
			auto values = csrMat.getValues();
			for (_IdxT i=0; i<nnzs; i++) {
				ofs << "csr " << i << "\t" << col_idx[i] << "\t" << values[i] <<  "\n";
			}
			return;
		}
		ofs << "col_idx ";
		auto col_idx = csrMat.getColIdx();
		for (_IdxT i=0; i<nnzs; i++) {
			ofs << col_idx[i] << " ";
		}
		ofs << std::endl;
		ofs << "values ";
		auto values = csrMat.getValues();
		for (_IdxT i=0; i<nnzs; i++) {
			ofs << values[i] << " ";
		}
		ofs << std::endl;
	}
	void saveToStreamRaw(std::ostream& ofs, int prec = -1) const {
		auto& csrMat = *this;
		if (prec <= 0) {
			prec = Math::precision<_ValT>();
		}

		_IdxT nrows = csrMat.getRows();

		ofs << nrows << std::endl;
		

		if (nrows == 0) {
			return;
		}

		auto row_ptr = csrMat.getRowPtr();
		for (_IdxT i=0; i<nrows + 1; i++) {
			ofs << row_ptr[i] << std::endl;
		}

		_IdxT nnzs = row_ptr[nrows];


		auto col_idx = csrMat.getColIdx();
		for (_IdxT i=0; i<nnzs; i++) {
			ofs << col_idx[i] << std::endl;
		}

		auto values = csrMat.getValues();
		for (_IdxT i=0; i<nnzs; i++) {
			ofs << std::setiosflags(std::ios::scientific)  << std::setprecision(prec) << values[i] << std::endl;
		}
	}

	void check(bool row_sorted = true) {
		auto rows = getRows();
		if (rows == 0) {return;}
		auto cols = getCols();
		auto nnzs = getNnzs();
		auto row_ptr = getRowPtr();
		auto col_idx = getColIdx();
		auto values = getValues();
		for (_IdxT i=0; i<rows; i++) {
			CHECK_LE(row_ptr[i], row_ptr[i+1]);
			CHECK_GE(row_ptr[i], 0);
		}
		CHECK_EQ(row_ptr[rows], nnzs);
		for (_IdxT i=0; i<nnzs; i++) {
			CHECK_LT(col_idx[i], cols);
			CHECK_GE(col_idx[i], 0);
		}
		if (row_sorted) {
			for (_IdxT i=0; i<rows; i++) {
				for (_IdxT jj=row_ptr[i]; jj<row_ptr[i+1]-1; jj++) {
					CHECK_LT(col_idx[jj], col_idx[jj+1]);
				}
			}
		}
	}
	_IdxT evaluateNnzs() const {
		_IdxT nnzs;
		auto& A = *this;
		A.getDevice().copyTo(1, A.getRowPtr()+A.getRows(), Device(Device::CPU), &nnzs);
		return nnzs;
	}
	_IdxT evaluateCols() const {
		CHECK(false);
		return 0;
	}

	COT_CSRRawMat<_ValT, _IdxT> getRawMat() const {
		COT_CSRRawMat<_ValT, _IdxT> ret;
		getRawMat(ret);
		return ret;
	}

	void getRawMat(COT_CSRRawMat<_ValT, _IdxT>& raw) const {
		raw.rows = m_impl->rows;
		raw.cols = m_impl->cols;
		raw.nnzs = m_impl->nnzs;
		raw.row_ptr = m_impl->row_ptr;
		raw.row_ptr_end = m_impl->row_ptr + 1;
		raw.col_idx = m_impl->col_idx;
		raw.values = m_impl->values;
	}

protected:
	// 矩阵数据
	struct CSRMatrixImpl
	{
        Device device;
		_IdxT rows = 0;
		_IdxT cols = 0;
		_IdxT nnzs = 0;
        _IdxT* row_ptr = 0;
		_IdxT* col_idx = 0;
        _ValT* values = 0;
        ~CSRMatrixImpl() {
            if (row_ptr) {
                device.free(row_ptr);
				row_ptr = 0;
            }
            if (col_idx) {
                device.free(col_idx);
				col_idx = 0;
            }
            if (values) {
                device.free(values);
				values = 0;
            }
        }
		_IdxT getNnzs() {
			// row_ptr might be on device, can not access
			return nnzs;
		}
	};
	std::shared_ptr<CSRMatrixImpl> m_impl;

};

template<class _ValT, class _IdxT>
std::ostream& operator<<(std::ostream& os, const CSRMatrixT<_ValT, _IdxT>& mat) {
	auto cpu = Device(Device::CPU);
	mat.toDevice(cpu).saveToStream(os);
	return os;
}
template<class _ValT, class _IdxT>
std::ostream& operator>>(std::ostream& os, CSRMatrixT<_ValT, _IdxT>& mat) {
	mat.loadFromStream(os);
	return os;
}

}

#include "COOMatrix.hpp"


namespace hipo {

template <class _ValT, class _IdxT>
inline CSRMatrixT<_ValT, _IdxT> CSRMatrixT<_ValT, _IdxT>::rand(_IdxT m, _IdxT n, float sparsity)
{
	auto coo = COOMatrixT<_ValT, _IdxT, _IdxT>::rand(m, n, sparsity);
	CSRMatrixT csr;
	coo.toCSR(csr);
	return csr;
}

template <class _ValT, class _IdxT>
inline void CSRMatrixT<_ValT, _IdxT>::loadFromStream(std::istream &ifs) {
	if (!ifs) {
        return;
    }
	COOMatrixT<_ValT, _IdxT, _IdxT> coo;
	coo.loadFromStream(ifs);
	create(coo.getRows(), coo.getCols());
	coo.toCSR(*this);
}
}
