#pragma once
#include <vector>
#include <map>
#include <set>
#include "smpi.hpp"

namespace comu {

/**
 * 将一个矩阵can的某一行进行转置，存到fun_nac中。
 * 行号由cell_global_id指定。每一行对应的列号由
 * ext和idx表示。
 */
void transpose_matrix(
        MPI_Comm comm,
        const std::vector<int>& cell_global_id,
        const std::vector<int>& can_ext,
        const std::vector<int>& can_idx,
        std::map<int, std::set<int> >& full_nac
        );


void merge_graph(
        MPI_Comm comm,
        const std::map<int, std::set<int> >& graph_in,
        std::map<int, std::set<int> >& graph_out
        );

void change_format(
        const std::map<int, std::set<int> >& full_nac,
        std::vector<int>& node_global_id,
        std::vector<int>& nac_ext,
        std::vector<int>& nac_idx
        );

void change_format2(
        const std::map<int, std::set<int> >& cac_map,
        const std::vector<int>& cell_global_id,
        std::vector<int>& cac_ext,
        std::vector<int>& cac_idx);

}
