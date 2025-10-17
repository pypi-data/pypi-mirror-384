#pragma once
#include <vector>
#include "smpi.hpp"
#include <assert.h>
#include <iostream>
#include <algorithm>
#include "hipo/utils/logging.hpp"
#include "Stream.h"

namespace comu {


template<class _ValT>
inline MPI_Datatype getMPIDataType(const _ValT& x = 0);
///inline MPI_Datatype getMPIDataType(const int&) { return MPI_INT;}
///inline MPI_Datatype getMPIDataType(const long&) { return MPI_LONG;}
template <> inline MPI_Datatype getMPIDataType(const int32_t&) { return MPI_INT32_T;}
template <> inline MPI_Datatype getMPIDataType(const int64_t&) { return MPI_INT64_T;}
template <> inline MPI_Datatype getMPIDataType(const float&) { return MPI_FLOAT;}
template <> inline MPI_Datatype getMPIDataType(const double&) { return MPI_DOUBLE;}
template <> inline MPI_Datatype getMPIDataType(const hipo::Complex<float>&) { return MPI_COMPLEX;}
template <> inline MPI_Datatype getMPIDataType(const hipo::Complex<double>&) { return MPI_DOUBLE_COMPLEX;}

template <class Type>
std::string vec2str(const std::vector<Type>& vec) {
    std::ostringstream oss;
    oss << "[";
    int N = vec.size();
    for (int i=0; i<N; i++) {
        oss << vec[i] << (i == N-1 ? "" : ",");
    }
    oss << "]";
    return oss.str();
}

/**
 * @brief sparse_send_recv类似 MPI_Alltoall，
 * 完成alltoall通信。该函数要求Type是POD类型，
 * 对应的非POD的版本为sparse_send_recv_stream。
 * 主要用于peer to peer的通信，而非client server通信。
 * @param comm [in]  MPI 通信器
 * @param send_data [in] 长度为comm中进程个数，分量表示发往对应进程的数据。
 * @param recv_data [inout] 长度为comm中进程个数，分量表示从对应进程接收的数据。
 * @param has_recv_length [in] 表示recv_data中的长度为输入参数，不需要另行计算。
 */
template <class Type>
void sparse_send_recv(
        MPI_Comm comm,
        const std::vector<std::vector<Type> >& send_data,
        std::vector<std::vector<Type> >& recv_data,
        bool has_recv_length = false
        ) {
    int nprocs;
    int myrank;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);
    assert(send_data.size() == nprocs);

    // compute the recv data length if neccessary
    if (has_recv_length) {
        assert(recv_data.size() == nprocs);
    }
    else {
        // first get the send length
        std::vector<int> send_length(nprocs);
        for (int i=0; i<send_data.size(); i++) {
            send_length[i] = (int)send_data[i].size();
        }

        // use alltoall to get the recv length
        std::vector<int> recv_length(nprocs);
        MPI_Alltoall(send_length.data(), 1, MPI_INT,
                     recv_length.data(), 1, MPI_INT, comm);

        // allocate the space for recv_data
        recv_data.resize(nprocs);
        for (int i=0; i<nprocs; i++) {
            recv_data[i].resize(recv_length[i]);
        }
    }


    std::vector<MPI_Request> requests;
    for (int i=0; i<nprocs; i++) {
        if (i == myrank) {
            // for local DATA
            recv_data[i] = send_data[i];
        }
        else {
            if (send_data[i].size() > 0) {
                MPI_Request send_request;
                MPI_Isend(send_data[i].data(), int(send_data[i].size()*sizeof(Type)),
                          MPI_BYTE, i, 0, comm, &send_request);
                requests.push_back(send_request);
            }
            if (recv_data[i].size() > 0) {
                MPI_Request recv_request;
                MPI_Irecv(recv_data[i].data(), int(recv_data[i].size()*sizeof(Type)),
                          MPI_BYTE, i, 0, comm, &recv_request);
                requests.push_back(recv_request);
            }
        }
    }
    std::vector<MPI_Status> status(requests.size());
    MPI_Waitall(requests.size(), requests.data(), status.data());
    // no need to free. from yangzhang
    //    for (int i=0; i<requests.size(); i++) {
    //        MPI_Request_free(&requests[i]);
    //    }
}


template <class Type>
void sparse_send_recv_stream(
        MPI_Comm comm,
        const std::vector<Type>& send_data,
        std::vector<Type>& recv_data,
        std::vector<int>* p_recv_length = 0
        ) {
    int nprocs;
    int myrank;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);
    assert(send_data.size() == nprocs);


    /// pack send_data to stream
    std::vector<Stream> send_stream(nprocs);
    std::vector<Stream> recv_stream(nprocs);
    std::vector<int> send_length(nprocs);
    std::vector<int> recv_length(nprocs);
    for (int i=0; i<send_data.size(); i++) {
        if (i == myrank) {
            continue;
        }
        send_length[i] = getStreamSize(send_data[i]);
    }
    /// compute the recv data length if neccessary
    MPI_Alltoall(send_length.data(), 1, MPI_INT,
                 recv_length.data(), 1, MPI_INT, comm);
    //LOG(INFO) << "nprocs " << nprocs << ", myrank " << myrank <<  ", send_length: " << vec2str(send_length);
    //LOG(INFO) << "nprocs " << nprocs << ", myrank " << myrank <<  ", recv_length: " << vec2str(recv_length);

    for (int i=0; i<send_data.size(); i++) {
        if (i == myrank) {
            continue;
        }
        send_stream[i].setCapacity(send_length[i]);
        packStream(send_stream[i], send_data[i]);

        recv_stream[i].setCapacity(recv_length[i]);
        recv_stream[i].pushBack(0, recv_length[i]);
    }
    recv_data.resize(nprocs);

    /// sparse send and recv
    std::vector<MPI_Request> requests;
    for (int i=0; i<nprocs; i++) {
        if (i == myrank) {
            // for local DATA
            recv_data[i] = send_data[i];
        }
        else {
            if (send_length[i] > 0) {
                MPI_Request send_request;
                MPI_Isend(send_stream[i].buffer(), send_length[i],
                          MPI_BYTE, i, 0, comm, &send_request);
                requests.push_back(send_request);
            }
            if (recv_length[i] > 0) {
                MPI_Request recv_request;
                MPI_Irecv(recv_stream[i].buffer(), recv_length[i],
                          MPI_BYTE, i, 0, comm, &recv_request);
                requests.push_back(recv_request);
            }
        }
    }
    std::vector<MPI_Status> status(requests.size());
    MPI_Waitall(requests.size(), requests.data(), status.data());


    /// unpack
    for (int i=0; i<recv_data.size(); i++) {
        if (i == myrank) {
            continue;
        }
        else {
            if (recv_length[i] > 0) {
                unpackStream(recv_stream[i], recv_data[i]);
            }
        }
    }
}


template <class Type>
void stlmpi_alltoall(
        MPI_Comm comm,
        const std::vector<Type>& send_data,
        std::vector<Type>& recv_data
        ) {
    MPI_Alltoall(
                send_data.data(),
                sizeof(Type),
                MPI_BYTE,
                recv_data.data(),
                sizeof(Type),
                MPI_BYTE,
                comm);
}


template <class Type>
void stlmpi_alltoall_stream(
        MPI_Comm comm,
        const std::vector<Type>& send_data,
        std::vector<Type>& recv_data
        ) {
    int nprocs;
    int myrank;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);
    assert(send_data.size() == nprocs);


    /// compute the send data length
    std::vector<int> send_length(nprocs);
    std::vector<int> recv_length(nprocs);
    for (int i=0; i<send_data.size(); i++) {
        send_length[i] = getStreamSize(send_data[i]);
    }
    /// compute the recv data length via communication
    MPI_Alltoall(send_length.data(), 1, MPI_INT,
                 recv_length.data(), 1, MPI_INT, comm);

    /// compute the displacements
    std::vector<int> send_disps(nprocs+1), recv_disps(nprocs+1);
    send_disps[0] = 0;
    recv_disps[0] = 0;
    for (int i=0; i<nprocs; i++) {
        send_disps[i+1] = send_disps[i] + send_length[i];
        recv_disps[i+1] = recv_disps[i] + recv_length[i];
    }

    /// pack send data to send stream
    Stream send_stream, recv_stream;
    send_stream.setCapacity(send_disps[nprocs]);
    for (int i=0; i<nprocs; i++) {
        packStream(send_stream, send_data[i]);
    }
    recv_stream.setCapacity(recv_disps[nprocs]);
    recv_stream.pushBack(0, recv_disps[nprocs]);

    /// get recv stream
    MPI_Alltoallv(
                send_stream.buffer(),
                send_length.data(),
                send_disps.data(),
                MPI_BYTE,
                recv_stream.buffer(),
                recv_length.data(),
                recv_disps.data(),
                MPI_BYTE,
                comm
                );

    /// unpack recv stream to recv data
    recv_data.resize(nprocs);
    for (int i=0; i<nprocs; i++) {
        unpackStream(recv_stream, recv_data[i]);
    }
}


template <class Type>
void stlmpi_gather(
        MPI_Comm comm,
        const Type& send_data,
        std::vector<Type>& recv_data,
        int root
        ) {
    int myrank;
    MPI_Comm_rank(comm, &myrank);
    MPI_Gather(&send_data,
               sizeof(Type),
               MPI_BYTE,
               root == myrank ? recv_data.data() : 0,
               sizeof(Type),
               MPI_BYTE,
               root,
               comm);
}

template <class Type>
void stlmpi_gather_stream(
        MPI_Comm comm,
        const Type& send_data,
        std::vector<Type>& recv_data,
        int root
        ) {
    int myrank;
    int nprocs;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);

    int send_length = getStreamSize(send_data);

    std::vector<int> recv_length(nprocs);
    MPI_Gather(&send_length, 1, MPI_INT,
               recv_length.data(), 1, MPI_INT,
               root, comm);

    std::vector<int> recv_disps;
    if (myrank == root) {
        recv_disps.resize(nprocs+1);
        recv_disps[0] = 0;
        for (int i=0; i<nprocs; i++) {
            recv_disps[i+1] = recv_disps[i] + recv_length[i];
        }
    }

    Stream send_stream, recv_stream;
    send_stream.setCapacity(send_length);
    packStream(send_stream, send_data);

    if (myrank == root) {
        recv_stream.setCapacity(recv_disps[nprocs]);
        recv_stream.pushBack(0, recv_disps[nprocs]);
    }

    MPI_Gatherv(send_stream.buffer(),send_length,MPI_BYTE,
                recv_stream.buffer(),recv_length.data(),recv_disps.data(),MPI_BYTE,
                root, comm);

    recv_data.resize(nprocs);
    if (myrank == root) {
        for (int i=0; i<nprocs; i++) {
            unpackStream(recv_stream, recv_data[i]);
        }
    }
}


template <class Type>
void stlmpi_allgather(
        MPI_Comm comm,
        const Type& send_data,
        std::vector<Type>& recv_data
        ) {
    MPI_Allgather(&send_data,
                  sizeof(Type),
                  MPI_BYTE,
                  recv_data.data(),
                  sizeof(Type),
                  MPI_BYTE,
                  comm);
}

template <class Type>
void stlmpi_allgather_stream(
        MPI_Comm comm,
        const Type& send_data,
        std::vector<Type>& recv_data
        ) {
    int myrank;
    int nprocs;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);

    int send_length = getStreamSize(send_data);

    std::vector<int> recv_length(nprocs);
    MPI_Allgather(&send_length, 1, MPI_INT,
               recv_length.data(), 1, MPI_INT,
               comm);

    std::vector<int> recv_disps(nprocs+1);
    recv_disps[0] = 0;
    for (int i=0; i<nprocs; i++) {
        recv_disps[i+1] = recv_disps[i] + recv_length[i];
    }

    Stream send_stream, recv_stream;
    send_stream.setCapacity(send_length);
    recv_stream.setCapacity(recv_disps[nprocs]);
    recv_stream.pushBack(0, recv_disps[nprocs]);

    packStream(send_stream, send_data);

    MPI_Allgatherv(send_stream.buffer(),send_length,MPI_BYTE,
                recv_stream.buffer(),recv_length.data(),recv_disps.data(),MPI_BYTE,
                comm);

    recv_data.resize(nprocs);
    for (int i=0; i<nprocs; i++) {
        unpackStream(recv_stream, recv_data[i]);
    }
}

template <class Type>
void stlmpi_scatter(
        MPI_Comm comm,
        const std::vector<Type>& send_data,
        Type& recv_data,
        int root
        ) {
    int myrank;
    MPI_Comm_rank(comm, &myrank);
    MPI_Scatter(root == myrank ? send_data.data(): 0,
                sizeof(Type),
                MPI_BYTE,
                &recv_data,
                sizeof(Type),
                MPI_BYTE,
                root,
                comm);
}

template <class Type>
void stlmpi_scatter_stream(
        MPI_Comm comm,
        const std::vector<Type>& send_data,
        Type& recv_data,
        int root
        ) {
    int myrank;
    int nprocs;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);

    std::vector<int> send_length;

    if (myrank == root) {
        assert(send_data.size() == nprocs);
        send_length.resize(nprocs);
        for (int i=0; i<nprocs; i++) {
            send_length[i] = getStreamSize(send_data[i]);
        }
    }

    int recv_length;

    MPI_Scatter(
                send_length.data(),
                1,
                MPI_INT,
                &recv_length,
                1,
                MPI_INT,
                root ,comm);

    std::vector<int> send_disps;
    if (myrank == root) {
        send_disps.resize(nprocs+1);
        for (int i=0; i<nprocs; i++) {
            send_disps[i+1] = send_disps[i] + send_length[i];
        }
    }

    Stream send_stream, recv_stream;
    if (myrank == root) {
        send_stream.setCapacity(send_disps[nprocs]);
        for (int i=0; i<nprocs; i++) {
            packStream(send_stream, send_data[i]);
        }
    }
    recv_stream.setCapacity(recv_length);
    recv_stream.pushBack(0, recv_length);

    MPI_Scatterv(send_stream.buffer(), send_length.data(),
                 send_disps.data(), MPI_BYTE, recv_stream.buffer(),
                 recv_length, MPI_BYTE, root, comm);

    unpackStream(recv_stream, recv_data);
}


template <class Type>
void stlmpi_bcast(
        MPI_Comm comm,
        Type& send_recv_data,
        int root
        ) {
    MPI_Bcast(&send_recv_data, sizeof(Type), MPI_BYTE, root, comm);
}

template <class Type>
void stlmpi_bcast_stream(
        MPI_Comm comm,
        Type& send_recv_data,
        int root
        ) {
    int myrank;
    int nprocs;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);
    int length;
    if (myrank == root) {
        length = getStreamSize(send_recv_data);
    }
    MPI_Bcast(&length, 1, MPI_INT, root, comm);


    Stream stream;
    stream.setCapacity(length);
    if (myrank == root) {
        packStream(stream, send_recv_data);
    }
    else {
        stream.pushBack(0, length);
    }
    MPI_Bcast(stream.buffer(), length, MPI_BYTE, root, comm);

    if (myrank != root) {
        unpackStream(stream, send_recv_data);
    }
}

namespace impl {

// A helper class used to create user-defined MPI_Ops
template<typename Type, typename Op>
class user_op
{
public:
    user_op(Op& op, bool is_commutative = true) {
        MPI_Op_create(
                    &user_op<Type, Op>::perform,
                    is_commutative,
                    &mpi_op
                    );
        op_ptr = &op;
    }

    ~user_op() {
        MPI_Op_free(&mpi_op);
    }

    MPI_Op& get_mpi_op()
    {
        return mpi_op;
    }

private:
    MPI_Op mpi_op;
    static Op* op_ptr;

    static void perform(void* vinvec, void* voutvec, int* plen, MPI_Datatype*)
    {
        Type* invec = static_cast<Type*>(vinvec);
        Type* outvec = static_cast<Type*>(voutvec);
        std::transform(invec, invec + *plen, outvec, outvec, *op_ptr);
    }
};

template<typename Type, typename Op> Op* user_op<Type, Op>::op_ptr = 0;

template <class Type>
MPI_Datatype get_mpi_datatype() {
    return MPI_DATATYPE_NULL;
}
template <>
inline MPI_Datatype get_mpi_datatype<char>() {
    return MPI_CHAR;
}
template <>
inline MPI_Datatype get_mpi_datatype<int>() {
    return MPI_INT;
}
template <>
inline MPI_Datatype get_mpi_datatype<long>() {
    return MPI_LONG;
}
template <>
inline MPI_Datatype get_mpi_datatype<float>() {
    return MPI_FLOAT;
}
template <>
inline MPI_Datatype get_mpi_datatype<double>() {
    return MPI_DOUBLE;
}

//#include <boost/mpi.hpp>

}



template <class Type>
void stlmpi_reduce(
    MPI_Comm comm,
    const Type* p_send_data,
    int size,
    Type* p_recv_data,
    MPI_Op mpi_op,
    int root
    ) {
    MPI_Datatype reduce_datatype;
    MPI_Datatype input_datatype = impl::get_mpi_datatype<Type>();
    if (MPI_DATATYPE_NULL == input_datatype) {
        // define a new type
        MPI_Type_contiguous(sizeof(Type), MPI_BYTE, &reduce_datatype);
        MPI_Type_commit(&reduce_datatype);
    }
    else {
        reduce_datatype = input_datatype;
    }

    MPI_Reduce(
        p_send_data,
        p_recv_data,
        size,
        reduce_datatype,
        mpi_op,
        root,
        comm
    );

    if (MPI_DATATYPE_NULL == input_datatype) {
        // delete the new type
        MPI_Type_free(&reduce_datatype);
    }
}

template <class Type, class Op>
void stlmpi_reduce(
    MPI_Comm comm,
    const Type* p_send_data,
    int size,
    Type* p_recv_data,
    Op op,
    int root
    ) {
    int myrank;
    int nprocs;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);


    // change op to user_op
    impl::user_op<Type, Op> user_op(op);
    stlmpi_reduce(
                comm,
                p_send_data,
                size,
                p_recv_data,
                user_op.get_mpi_op(),
                root);
}

template <class Type, class Op>
void stlmpi_reduce_stream(
    MPI_Comm comm,
    const Type* p_send_data,
    int size,
    Type* p_recv_data,
    Op op,
    int root
    ) {
    int myrank;
    int nprocs;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);

    std::vector<Type> in_values;
    if (p_send_data) {
        in_values.resize(size);
        std::copy(p_send_data, p_send_data + size, in_values.data());
    }
    // first gather data to the root
    std::vector<std::vector<Type> > out_values;
    stlmpi_gather(comm, in_values, out_values, root);
    if (myrank == root) {
        assert(p_recv_data != 0);
        bool first_value = true;
        for (int p=0; p<nprocs; p++) {
            if (out_values[p].size() > 0) {
                if (first_value) {
                    for (int i=0; i<size; i++) {
                        p_recv_data[i] = out_values[p][i];
                    }
                    first_value = false;
                }
                else {
                    for (int i=0; i<size; i++) {
                        p_recv_data[i] = op(p_recv_data[i], out_values[p][i]);
                    }
                }
            }
        }
    }
}


template<class Type>
void stlmpi_all_reduce(
        MPI_Comm comm,
        const Type* p_send_data,
        int size,
        Type* p_recv_data,
        MPI_Op mpi_op
        ) {
    MPI_Datatype reduce_datatype;
    MPI_Datatype input_datatype = impl::get_mpi_datatype<Type>();
    if (MPI_DATATYPE_NULL == input_datatype) {
        // define a new type
        MPI_Type_contiguous(sizeof(Type), MPI_BYTE, &reduce_datatype);
        MPI_Type_commit(&reduce_datatype);
    }
    else {
        reduce_datatype = input_datatype;
    }

    MPI_Allreduce(
        p_send_data,
        p_recv_data,
        size,
        reduce_datatype,
        mpi_op,
        comm
    );

    if (MPI_DATATYPE_NULL == input_datatype) {
        // delete the new type
        MPI_Type_free(&reduce_datatype);
    }
}

template<class Type, class Op>
void stlmpi_all_reduce(
    MPI_Comm comm,
    const Type* p_send_data,
    int size,
    Type* p_recv_data,
    Op op) {
    // change op to user_op
    impl::user_op<Type, Op> user_op(op);

    stlmpi_all_reduce(
                comm,
                p_send_data,
                size,
                p_recv_data,
                user_op.get_mpi_op()
                );
}


template<class Type>
void stlmpi_scan(
        MPI_Comm comm,
        const Type* p_send_data,
        int size,
        Type* p_recv_data,
        MPI_Op mpi_op) {
    MPI_Datatype reduce_datatype;
    MPI_Datatype input_datatype = impl::get_mpi_datatype<Type>();
    if (MPI_DATATYPE_NULL == input_datatype) {
        // define a new type
        MPI_Type_contiguous(sizeof(Type), MPI_BYTE, &reduce_datatype);
        MPI_Type_commit(&reduce_datatype);
    }
    else {
        reduce_datatype = input_datatype;
    }

    MPI_Scan(
        p_send_data,
        p_recv_data,
        size,
        reduce_datatype,
        mpi_op,
        comm
    );

    if (MPI_DATATYPE_NULL == input_datatype) {
        // delete the new type
        MPI_Type_free(&reduce_datatype);
    }
}

template<class Type, class Op>
void stlmpi_scan(
        MPI_Comm comm,
        const Type* p_send_data,
        int size,
        Type* p_recv_data,
        Op op) {
    // change op to user_op
    impl::user_op<Type, Op> user_op(op);

    stlmpi_scan(comm, p_send_data, size,
                p_recv_data, user_op.get_mpi_op());
}


}
