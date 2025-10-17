#pragma once

#include "smpi.hpp"
#include <vector>
#include <functional>
#include <map>



/// 用于计算属主，全局编号，词频等问题

namespace comu {


template <class _MapType, class _RedType>
void map_reduce(MPI_Comm comm,
                size_t num,
                const _MapType* inVecs,
                std::function<int(size_t, const _MapType&)> mapper,
                std::function<void(int nprocs, int myrank, const std::vector<std::vector<_MapType>>&, std::vector<std::vector<_RedType>>&)> reducer,
                _RedType* outVecs
                ) {
    // 将(inObj)发送到hash(inObj)进程；
    // 在hash(id)号进程上，对所有发送到这个进程的数据进行reduce。
    int size;
    int rank;
    MPI_Comm_size(comm, &size);
    MPI_Comm_rank(comm, &rank);

    // prepare send_data
    std::vector<std::vector<_MapType> > send_data(size);
    std::vector<std::vector<size_t> > reverse_idx(size);
    for (size_t i=0; i<num; i++) {
        int to_rank = mapper(i, inVecs[i]);
        send_data[to_rank].push_back(inVecs[i]);
        reverse_idx[to_rank].push_back(i);
    }

    // send send_data
    std::vector<std::vector<_MapType>> recv_data(size);
    sparse_send_recv(comm, send_data, recv_data, false);

    std::vector<std::vector<_RedType>> send_red_data(size), recv_red_data(size);
    reducer(size, rank, recv_data, send_red_data);

    if (0 == outVecs) {
        return;
    }

    for (int i=0; i<size; i++) {
        recv_red_data[i].resize(send_data[i].size());
    }

    // send the reduce data back to the original processor
    sparse_send_recv(comm, send_red_data, recv_red_data, true);

    // recover the vector
    for (int i=0; i<recv_red_data.size(); i++) {
        for (int j=0; j<recv_red_data[i].size(); j++) {
            size_t idx = reverse_idx[i][j];
            outVecs[idx] = recv_red_data[i][j];
        }
    }
}

}
