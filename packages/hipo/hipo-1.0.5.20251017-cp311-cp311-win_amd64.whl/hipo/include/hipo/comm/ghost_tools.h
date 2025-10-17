#pragma once
#include <vector>
#include "smpi.hpp"


namespace comu {

template <class Type>
inline const Type& getNullReference() {
   return (*(const Type*)0);
}

/**
 * @brief get_sym_ghost_info 用于获取对称矩阵的影像区信息。
 * 对称矩阵是（主id，从id）的矩阵，其中主id和从id是同一个集合。
 * comm [in] MPI通信器。该函数要求主id的编号是连续分布的。
 *
 * @param cell_global_id [in] 主id的全局编号。
 * @param cac_ext [in] 对称矩阵的ext数组。
 * @param cac_idx [in] 对称矩阵的idx数组。
 * @param send_info [out] 长度为comm中进程数的数组，每一个
 * 分量表示要发往对应进程的全局id。
 * @param recv_info [out] 长度为comm中进程数的数组，每一个分量
 * 表示要从对应进程接收的全局id。
 * @param ghost_cell_global_id [out] 本进程上的影像全局id。
 * @param ghost_cell_owner_rank [out] 每一个影像全局id的属主。
 */
void get_sym_ghost_info(
        MPI_Comm comm,
        const std::vector<int> &cell_global_id,
        const std::vector<int>& cac_ext,
        const std::vector<int>& cac_idx,
        std::vector<std::vector<int> >& send_info,
        std::vector<std::vector<int> >& recv_info,
        std::vector<int>& ghost_cell_global_id,
        std::vector<int>& ghost_cell_owner_rank
        );

/**
 * @brief get_unsym_ghost_info与get_ghost_info类似，
 * 不过其矩阵是非对称的。
 * comm [in] MPI通信器。
 * global_id [in] 主id的全局编号。
 * @param can_ext [in] 非对称矩阵的ext数组。
 * @param can_idx [in] 非对称矩阵的idx数组。
 * @param send_info [out] 长度为comm中进程数的数组，每一个
 * 分量表示要发往对应进程的全局id。
 * @param recv_info [out] 长度为comm中进程数的数组，每一个分量
 * 表示要从对应进程接收的全局id。
 * @param ghost_cell_global_id [out] 本进程上的影像全局id。
 * @param ghost_cell_owner_rank [out] 每一个影像全局id的属主。
 */
void get_unsym_ghost_info(
        MPI_Comm comm,
        const std::vector<int>& cell_global_id,
        const std::vector<int>& can_ext,
        const std::vector<int>& can_idx,
        std::vector<std::vector<int> >& send_info,
        std::vector<std::vector<int> >& recv_info,
        std::vector<int>& ghost_cell_global_id,
        std::vector<int>& ghost_cell_owner_rank
        );

}
