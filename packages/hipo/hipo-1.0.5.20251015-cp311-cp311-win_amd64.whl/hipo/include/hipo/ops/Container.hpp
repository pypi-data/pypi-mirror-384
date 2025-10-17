#pragma once
#include "hipo/spm/Parallel.hpp"
#include "hipo/ops/CrossOpTypes.hpp"

namespace hipo {

template <class ValT>
class Vector {
    ValT *m_data = 0;
    size_t m_n = 0;
    size_t m_capacity = 0;
public:
    SPM_INLINE_FUNCTION Vector(size_t ncap, ValT *data) : m_capacity(ncap), m_data(data) {}
    SPM_INLINE_FUNCTION ValT &operator[](size_t i) {
        SPM_ASSERT(i < m_n);
        return m_data[i];
    }
    SPM_INLINE_FUNCTION const ValT &operator[](size_t i) const {
        SPM_ASSERT(i < m_n);
        return m_data[i];
    }
    SPM_INLINE_FUNCTION ValT *data() const { return m_data; }
    SPM_INLINE_FUNCTION size_t size() const { return m_n; }
    SPM_INLINE_FUNCTION void resize(size_t newsz) {
        SPM_ASSERT(newsz <= m_capacity);
        m_n = newsz;
    }
};

template <class _ValT>
class Stack {
public:
    int n = 0;
    _ValT *data = 0;
    int end = 0;
    SPM_INLINE_FUNCTION Stack(int n, _ValT *data) {
        this->n = n;
        this->data = data;
    }
    SPM_INLINE_FUNCTION void clear() {
        end = 0;
    }
    SPM_INLINE_FUNCTION void push(const _ValT &e) {
        data[end] = e;
        end++;
    }
    SPM_INLINE_FUNCTION _ValT pop() {
        end--;
        return data[end];
    }
    SPM_INLINE_FUNCTION int size() const { return end; }
};

template <class _IdxT>
class UnionFind {
public:
    _IdxT size = 0;
    _IdxT *m_parents = 0;
    SPM_INLINE_FUNCTION UnionFind(_IdxT n, _IdxT *p) {
        size = n;
        m_parents = p;
        for (_IdxT i = 0; i < n; i++) {
            m_parents[i] = -1;
        }
    }
    SPM_INLINE_FUNCTION _IdxT remove(_IdxT x) {
        _IdxT px = m_parents[x];
        // // 处理所有的子节点
        // if (px == x) {
        // 	for (int i=0; i<size; i++) {
        // 		if (m_parents[i] == x) {
        // 			m_parents[i] = i;
        // 		}
        // 	}
        // } else {
        // 	for (int i=0; i<size; i++) {
        // 		if (m_parents[i] == x) {
        // 			m_parents[i] = px;
        // 		}
        // 	}
        // }
        m_parents[x] = -1;
        return px;
    }
    SPM_INLINE_FUNCTION _IdxT union2(_IdxT x, _IdxT y) {
        _IdxT root1 = x;
        _IdxT root2 = y;
        _IdxT root = -1;
        // REMS algorithm to merge the trees
        auto &dbs = *this;
        if (dbs.m_parents[x] < 0) {
            dbs.m_parents[x] = x;
        }
        if (dbs.m_parents[x] == x) {
            dbs.m_parents[y] = x;
            return x;
        }
        while (dbs.m_parents[root1] != dbs.m_parents[root2]) {
            if (dbs.m_parents[root1] < dbs.m_parents[root2]) {
                if (dbs.m_parents[root1] == root1) {
                    dbs.m_parents[root1] = dbs.m_parents[root2];
                    root = dbs.m_parents[root2];
                    break;
                }

                // splicing
                _IdxT z = dbs.m_parents[root1];
                dbs.m_parents[root1] = dbs.m_parents[root2];
                root1 = z;
            } else {
                if (dbs.m_parents[root2] == root2) {
                    dbs.m_parents[root2] = dbs.m_parents[root1];
                    root = dbs.m_parents[root1];
                    break;
                }

                // splicing
                _IdxT z = dbs.m_parents[root2];
                dbs.m_parents[root2] = dbs.m_parents[root1];
                root2 = z;
            }
        }
        return root;
    }

    SPM_INLINE_FUNCTION _IdxT find(_IdxT x) {
        if (m_parents[x] < 0) {
            return -1;
        }
        if (m_parents[x] != x) {
            m_parents[x] = find(m_parents[x]); // 递归查找根节点，并进行路径压缩
        }
        return m_parents[x];
    }
};

template <class KeyT>
class IntHash {
public:
    SPM_INLINE_FUNCTION KeyT operator()(KeyT k) const {
        k ^= k >> 16;
        k *= 0x85ebca6b;
        k ^= k >> 13;
        k *= 0xc2b2ae35;
        k ^= k >> 16;
        return k;
    }
};

template <typename KeyT, typename ValueT, typename Hash = IntHash<KeyT>>
class HashTable {
public:
    enum SlotStatus { EMPTY = 0, OCCUPIED, DELETED };

    typedef HashTableSlot<KeyT, ValueT> Slot;

    Vector<Slot> table;
    size_t occupied_count = 0;
    Hash hasher;

    struct InsertStatus {
        bool success = false;
        Slot *ptr = 0;
        bool full = true;
    };
    // static constexpr double LOAD_FACTOR = 0.7;

public:
    SPM_INLINE_FUNCTION HashTable(int n, Slot *data) : table(n, data) { table.resize(n); }

    SPM_INLINE_FUNCTION InsertStatus insert(KeyT key, const ValueT& value) {
        // if (need_expand()) rehash();
        InsertStatus stat;

        size_t index = find_slot(key);
        if (index == table.size()) {
            stat.full = true;
            return stat; // 仅在哈希表满时发生
        }

        if (table[index].status != OCCUPIED) {
            ++occupied_count;
            table[index].key = key;
            table[index].value = value;
            table[index].status = OCCUPIED;
            stat.success = true;
        } else {
            // table[index].value = value; // 更新现有键
            stat.success = false;
        }

        stat.ptr = &table[index];
        stat.full = (size() == capacity());

        return stat;
    }

    SPM_INLINE_FUNCTION ValueT *find(const KeyT &key) {
        size_t index = probe(key);
        return (index != table.size() && table[index].status == OCCUPIED) ? &table[index].value : nullptr;
    }

    SPM_INLINE_FUNCTION bool erase(const KeyT &key) {
        size_t index = probe(key);
        if (index == table.size() || table[index].status != OCCUPIED)
            return false;

        table[index].status = DELETED;
        --occupied_count;
        return true;
    }

    SPM_INLINE_FUNCTION size_t size() const { return occupied_count; }

    SPM_INLINE_FUNCTION size_t capacity() const { return table.size(); }


    SPM_INLINE_FUNCTION void clear() {
        for (size_t i = 0; i < table.size(); i++) {
            table[i].status = EMPTY;
        }
    }

private:
    SPM_INLINE_FUNCTION size_t probe(const KeyT &key) const {
        size_t start = hasher(key) % table.size();
        size_t index = start;
        do {
            if (table[index].status == EMPTY) {
                break;
            }
            if (table[index].status == OCCUPIED && table[index].key == key) {
                return index;
            }
            index = (index + 1) % table.size();
        } while (index != start);
        return table.size(); // 未找到
    }

    SPM_INLINE_FUNCTION size_t find_slot(const KeyT &key) {
        size_t first_tombstone = table.size();
        size_t start = hasher(key) % table.size();
        size_t index = start;

        do {
            if (table[index].status == EMPTY) {
                return (first_tombstone != table.size()) ? first_tombstone : index;
            }
            if (table[index].status == DELETED && first_tombstone == table.size()) {
                first_tombstone = index;
            }
            if (table[index].status == OCCUPIED && table[index].key == key) {
                return index;
            }
            index = (index + 1) % table.size();
        } while (index != start);

        return table.size(); // 表已满
    }
#if 0
    bool need_expand() const {
        return static_cast<double>(occupied_count) / table.size() >= LOAD_FACTOR;
    }

    void rehash() {
        std::vector<Slot> old_table(table.size() * 2);
        std::swap(table, old_table);
        occupied_count = 0;
        
        for (auto& slot : old_table) {
            if (slot.status == OCCUPIED) {
                insert(std::move(slot.key), std::move(slot.value));
            }
        }
    }
#endif
};

template <class _ValT>
SPM_INLINE_FUNCTION _ValT max(const _ValT& a, const _ValT& b) {
    return a < b ? b : a;
}

template <class _ValT>
SPM_INLINE_FUNCTION _ValT min(const _ValT& a, const _ValT& b) {
    return a < b ? a : b;
}

template <class _ValT>
SPM_INLINE_FUNCTION void swap(_ValT& a, _ValT& b) {
    _ValT tmp = a;
    a = b;
    b = tmp;
}

} // namespace hipo
