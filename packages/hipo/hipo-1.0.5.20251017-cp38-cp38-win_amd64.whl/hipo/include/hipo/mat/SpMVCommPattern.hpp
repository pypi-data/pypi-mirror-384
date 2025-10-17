#pragma once
#include <memory>
#include <functional>
#include "hipo/operators/ParOperator.hpp"
#include "hipo/comm/smpi.hpp"
#include "hipo/mat/Partitioner.hpp"
#include "hipo/ops/CrossOpTypes.hpp"
#include "hipo/mat/CSRMatrix.hpp"

namespace hipo {

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParMatrixT;
template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class ParCSRMatrixT;

template <class _ValT, class _GlobalIdxT, class _LocalIdxT>
class HIPO_WIN_API SpMVCommPatternT {
protected:
    class SpMVCommPatternImpl;

    using AsyncMatVecObject = typename ParMatrixFreeT<_ValT, _GlobalIdxT, _LocalIdxT>::AsyncMatVecObject;
public:
    std::shared_ptr<SpMVCommPatternImpl> m_impl;

    struct SpmvColBlock {
        _GlobalIdxT col_start = 0;
        _GlobalIdxT col_end = 0;
        // x 所属的进程号
        //int src_proc = -1;
        // 本进程接收的非零列的局部索引
        // non zero column
        MatrixT<_LocalIdxT, _LocalIdxT> nzc_recv_indices;
        MatrixT<_LocalIdxT, _LocalIdxT> nzc_recv_indices_host;
        // 本进程需要收到的向量x
        MatrixT<_ValT, _LocalIdxT> recv_x;
        MatrixT<_ValT, _LocalIdxT> recv_x_host;
        MatrixT<_ValT, _LocalIdxT> recv_x_device;
        MatrixT<_LocalIdxT, _LocalIdxT> recv_write_flag;
        // 本进程计算得到的向量y
        //MatrixT<_ValT, _LocalIdxT> local_y;
        // 接收请求
        MPI_Request recv_req;
        void* user_data = 0;
        template <class _RetT>
        _RetT getUserData() const {
            return (_RetT)user_data;
        }
    };

    struct SpmvSendMeta {
        // x 所属的进程号
        //int dst_proc;
        // 本进程发送的非零列的局部索引
        MatrixT<_LocalIdxT, _LocalIdxT> nzc_send_indices;
        MatrixT<_LocalIdxT, _LocalIdxT> nzc_send_indices_host;
        // 本进程发送给dst_proc的向量x
        MatrixT<_ValT, _LocalIdxT> send_x_host;
        // 发送请求
        MPI_Request send_req;
    };
protected:
    class SpMVCommPatternImpl {
    public:
        MPI_Comm comm;
        Device device;

        bool use_recv_event = true;

        // setupHalo需要生成这两个数据结构
        std::map<int, SpmvColBlock> spmv_col_block;
        std::map<int, SpmvSendMeta> spmv_send_meta;
        MatrixT<_ValT, _LocalIdxT> spmv_local_x_host;
        static int64_t getMessageTag();
        static void incMessageTag();
    };
public:
    SpMVCommPatternT();
    
    Device getDevice() const;
    MPI_Comm getComm() const;

    template <class _MatValT>
    void create(const ParCSRMatrixT<_MatValT, _GlobalIdxT, _LocalIdxT> &par_csrmat) {

        auto col_part = par_csrmat.getColPartitioner();
    
        std::vector<MatrixT<_LocalIdxT, _LocalIdxT>> col_count(col_part.getNumParts());
        for (int i=0; i<col_count.size(); i++) {
            auto localMat = par_csrmat.getLocalMatrix(i);
            if (localMat.getNnzs() > 0) {
                localMat.getColElementCount(col_count[i]);
            }
        }
        //LOG(INFO) << "Finish counting nonzero col indices for mat " << &par_csrmat << ", rows " << col_part.getGlobalSize();

        create(par_csrmat.getComm(), par_csrmat.getDevice(), par_csrmat.getColPartitioner(), col_count);
    }

    void create(MPI_Comm comm_, Device dev, const PartitionerT<_GlobalIdxT, _LocalIdxT>& col_part, const std::vector<MatrixT<_LocalIdxT, _LocalIdxT>>& col_count);
    
    template <class _NewValT>
    void create(MPI_Comm comm, Device device, const PartitionerT<_GlobalIdxT, _LocalIdxT>& col_part, const std::vector<CSRMatrixT<_NewValT, _LocalIdxT>>& col_blocks) {

        int npart = col_part.getNumParts();
        CHECK_EQ(npart, col_blocks.size()) << "blocks doesnot match the col partition";
        
        std::vector<MatrixT<_LocalIdxT, _LocalIdxT>> col_count(npart);
        for (int i=0; i<npart; i++) {
            col_blocks[i].getColElementCount(col_count[i]);
        }

        create(comm, device, col_part, col_count);
    }
    template <class _NewValT>
    void create(MPI_Comm comm, Device device, const PartitionerT<_GlobalIdxT, _LocalIdxT>& col_part, const CSRMatrixT<_NewValT, _LocalIdxT>& localmat) {
        std::vector<CSRMatrixT<_NewValT, _LocalIdxT>> col_blocks;
        localmat.splitCols(col_part, col_blocks);
        create(comm, device, col_part, col_blocks);
    }
    template <class _NewValT>
    void copyStructure(SpMVCommPatternT<_NewValT, _GlobalIdxT, _LocalIdxT>& newpat, bool init_local_vec = false) const {
        auto cpu = Device(Device::CPU);
        auto dev = m_impl->device;
    
        newpat.m_impl->device = m_impl->device;
        newpat.m_impl->comm = m_impl->comm;
        newpat.m_impl->use_recv_event = m_impl->use_recv_event;
        for (auto& item : m_impl->spmv_col_block) {
            auto& srcblk = item.second;
            auto& dstblk = newpat.m_impl->spmv_col_block[item.first];
            dstblk.nzc_recv_indices = srcblk.nzc_recv_indices;
            dstblk.nzc_recv_indices_host = srcblk.nzc_recv_indices_host;
            dstblk.col_start = srcblk.col_start;
            dstblk.col_end   = srcblk.col_end;
            dstblk.recv_x_host.resize(srcblk.recv_x_host.getSize(), cpu);
            dstblk.recv_x.resize(srcblk.recv_x.getSize(), dev);
        }
        if (init_local_vec) {
            int myrank;
            MPI_Comm_rank(m_impl->comm, &myrank);
            auto iter = m_impl->spmv_col_block.find(myrank);
            if (iter != m_impl->spmv_col_block.end()) {
                auto& blk = iter->second;
                blk.recv_x.resize(blk.col_end-blk.col_start, m_impl->device);
            }
        }
        for (auto& item : m_impl->spmv_send_meta) {
            auto& srcblk = item.second;
            auto& dstblk = newpat.m_impl->spmv_send_meta[item.first];
            dstblk.nzc_send_indices = srcblk.nzc_send_indices;
            dstblk.nzc_send_indices_host = srcblk.nzc_send_indices_host;
        }
    }

    void exchange(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x,
                  std::function<void(int, SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT>::SpmvColBlock *)> on_comm_begin_fn = nullptr,
                  std::function<void(int, SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT>::SpmvColBlock *)> on_comm_recv_fn = nullptr,
                  std::function<void()> on_comm_end_fn = nullptr, AsyncMatVecObject *asyncObj = nullptr);

    void exchange(const MatrixT<_ValT, _LocalIdxT> &local_x,
                  std::function<void(int, SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT>::SpmvColBlock *)> on_comm_begin_fn = nullptr,
                  std::function<void(int, SpMVCommPatternT<_ValT, _GlobalIdxT, _LocalIdxT>::SpmvColBlock *)> on_comm_recv_fn = nullptr,
                  std::function<void()> on_comm_end_fn = nullptr, AsyncMatVecObject *asyncObj = nullptr);


    template <class _NewValT>
    CSRMatrixT<_NewValT, _LocalIdxT> getGhostMatrix(const ParCSRMatrixT<_NewValT, _GlobalIdxT, _LocalIdxT> &mat) const {
    
        auto comm_ = m_impl->comm;
        int nprocs, myrank;
        MPI_Comm_rank(comm_, &myrank);
        MPI_Comm_size(comm_, &nprocs);
        auto cpu = Device();
        auto device = mat.getDevice();

        CSRMatrixT<_NewValT, _LocalIdxT> localMat = mat.getLocalMatrix();

        std::vector<CSRMatrixT<_NewValT, _LocalIdxT> > send_data(nprocs), recv_data(nprocs);

        for (auto& item : m_impl->spmv_send_meta) {
            if (item.first == myrank) {
                //send_data[myrank] = localMat;
            } else {
                localMat.getSelectedRows(item.second.nzc_send_indices, send_data[item.first], true);
            }
        }

        for (auto& item : send_data) {
            item = item.toDevice(cpu);
        }
        comu::sparse_send_recv_stream(comm_, send_data, recv_data);
        for (auto& item : recv_data) {
            item = item.toDevice(device);
        }

        recv_data[myrank] = localMat;

        CSRMatrixT<_NewValT, _LocalIdxT> ghost_mat = CSRMatrixT<_NewValT, _LocalIdxT>::mergeRows(mat.getRowPartitioner(), recv_data);

        return ghost_mat;
    }

    void initReverseExchange();

    void reverseExchange(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x, const ParMatrixT<_LocalIdxT, _GlobalIdxT, _LocalIdxT> &owner,
        std::function<_ValT(const _ValT& orig, const _ValT& newval)> x_reducer= [](const _ValT& orig, const _ValT& newval) { return newval; },
        std::function<_LocalIdxT(const _LocalIdxT& orig, const _LocalIdxT& newval)> owner_reducer= [](const _LocalIdxT& orig, const _LocalIdxT& newval) { return newval; }
    );
    void reverseExchange(const ParMatrixT<_ValT, _GlobalIdxT, _LocalIdxT> &x,
        std::function<_ValT(const _ValT& orig, const _ValT& newval)> x_reducer= [](const _ValT& orig, const _ValT& newval) { return newval; }    );


    void recvTraversal(std::function<void(int rank, SpmvColBlock* recv_blk)> callback);
    void sendTraversal(std::function<void(int rank, SpmvSendMeta* send_blk)> callback);


    void saveToStream(std::ostream& os, int prec = -1) const;

    void fill(_ValT val);

    void getRawMat(MatrixT<COT_RawCommPattern<_ValT, _LocalIdxT>, _LocalIdxT>& raw) const;
    MatrixT<COT_RawCommPattern<_ValT, _LocalIdxT>, _LocalIdxT> getRawMatOnDev() const;
};

} // namespace hipo
