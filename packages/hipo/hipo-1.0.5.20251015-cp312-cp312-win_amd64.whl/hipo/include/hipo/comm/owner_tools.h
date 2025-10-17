#pragma once

#include "smpi.hpp"
#include <vector>

namespace comu {

/**
 * @brief get_owner_ranks对global_id中的每一个整数，找一个对应的属主进程。
 * global_id中的数可以是连续的，也可以是不连续的。
 * global_id中的值可以有重复，
 * 但是为了减少通信量，global_id中的值最好是不重复的。
 * 因为本进程和其他进程的global_id是有重复的，所以
 * 需要通信才知道属主等全局信息。
 *
 * 有了属主进程，可以得到如下信息：
 * 1. 每一个id的一个新的全局编号；
 * 2. 不同的global_id的个数；
 *
 * @param comm [in] MPI通信器
 * @param num [in] 全局id的个数
 * @param global_id [in] 全局id
 * @param owner_rank [out] 每一个全局id的属主进程号
 */
void get_owner_rank(
    MPI_Comm comm,
    int num,
    const int* global_id,
    int* owner_rank
    );

/**
 * @param comm [in] MPI通信器
 * @param global_id [in] 全局id
 * @param owner_rank [out] 每一个全局id的属主进程号
 */
void get_owner_rank(
    MPI_Comm comm,
    const std::vector<int>& global_id,
    std::vector<int>& owner_rank
    );

/**
 * @brief 用于优化属主的hash函数。
 */
typedef int (*HashFunc)(int id, void* data);

/**
 * @brief get_owner_ranks_ex与get_owner_ranks类似。
 * 不过增加了两个参数，hash函数及其参数，用于优化此函数的通信算法，
 * 都可以是0。
 *
 * @param comm [in] MPI通信器
 * @param num [in] 全局id的个数
 * @param global_id [in] 全局id
 * @param hash [in] hash函数
 * @param data [in] hash函数的参数，可以是0
 * @param owner_rank [out] 每一个全局id的属主进程号
 */
void get_owner_rank_ex(
    MPI_Comm comm,
    int num,
    const int* global_id,
    HashFunc hash,
    void* data,
    int* owner_rank
    );

}
