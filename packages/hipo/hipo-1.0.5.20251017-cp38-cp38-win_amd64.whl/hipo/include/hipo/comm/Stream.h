#pragma once
#include <vector>
#include <set>
#include <string>
#include <list>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include <assert.h>
#include <iostream>
#include "hipo/utils/Complex.hpp"

namespace comu {


/**
 * Stream 由一个circular buffer构成。
 * 也就是说，Stream是一个先进先出的队列！
 *
 * Stream 要能够封装如下类型：
 * POD类型，POD类型数组，POD类型vector。
 * 对这几种类型，不能使用通常的pack和unpack。
 */
class HIPO_WIN_API Stream {
public:
    Stream();
    ~Stream();

    void setAllocactedBuffer(int capacity, void* buffer);
    void setCapacity(int capacity);
    int capacity() const {
        return m_capacity;
    }
    int head() const {
        return m_head;
    }
    int tail() const {
        return m_tail;
    }
    int size() const {
        return (m_tail - m_head);
    }
    void* buffer() const {
        return m_buffer;
    }
    void pushBack(const void* data, int size);
    void popFront(void* data, int size);
    /// for primitive types
    template <class Type>
    static int getSizeOf() {
        return sizeof(Type);
    }
private:
    char* m_buffer;
    int m_capacity;
    int m_head;
    int m_tail;
    bool m_is_external;
};


template <class Type>
int getStreamSize(const Type& data);
template <class Type>
void packStream(Stream& stream, const Type& data);
template <class Type>
void unpackStream(Stream& stream, Type& data);

#define TEMP_PREFIX 

template <class Type>
int getStreamSizeT(const Type& data) {
    return Stream::getSizeOf<Type>();
}
template <class Type>
void packStreamT(Stream& stream, const Type& data) {
    stream.pushBack(&(data), stream.getSizeOf<Type>());
}
template <class Type>
void unpackStreamT(Stream& stream, Type& data) {
    stream.popFront((void*)&(data), stream.getSizeOf<Type>());
}




/// pack and unpack primitive types
// int
TEMP_PREFIX inline int getStreamSize(const int& data) {
    return getStreamSizeT(data);
}
TEMP_PREFIX inline void packStream(Stream& stream, const int& data) {
    packStreamT(stream, data);
}
TEMP_PREFIX inline void unpackStream(Stream& stream, int& data) {
    unpackStreamT(stream, data);
}
// long
TEMP_PREFIX inline int getStreamSize(const int64_t& data) {
    return getStreamSizeT(data);
}
TEMP_PREFIX inline void packStream(Stream& stream, const int64_t& data) {
    packStreamT(stream, data);
}
TEMP_PREFIX inline void unpackStream(Stream& stream, int64_t& data) {
    unpackStreamT(stream, data);
}

// float
TEMP_PREFIX inline int getStreamSize(const float& data) {
    return getStreamSizeT(data);
}
TEMP_PREFIX inline void packStream(Stream& stream, const float& data) {
    packStreamT(stream, data);
}
TEMP_PREFIX inline void unpackStream(Stream& stream, float& data) {
    unpackStreamT(stream, data);
}

// double
TEMP_PREFIX inline int getStreamSize(const double& data) {
    return getStreamSizeT(data);
}
TEMP_PREFIX inline void packStream(Stream& stream, const double& data) {
    packStreamT(stream, data);
}
TEMP_PREFIX inline void unpackStream(Stream& stream, double& data) {
    unpackStreamT(stream, data);
}


// Complex<float>
TEMP_PREFIX inline int getStreamSize(const hipo::Complex<float>& data) {
    return getStreamSizeT(data);
}
TEMP_PREFIX inline void packStream(Stream& stream, const hipo::Complex<float>& data) {
    packStreamT(stream, data);
}
TEMP_PREFIX inline void unpackStream(Stream& stream, hipo::Complex<float>& data) {
    unpackStreamT(stream, data);
}

// Complex<double>
TEMP_PREFIX inline int getStreamSize(const hipo::Complex<double>& data) {
    return getStreamSizeT(data);
}
TEMP_PREFIX inline void packStream(Stream& stream, const hipo::Complex<double>& data) {
    packStreamT(stream, data);
}
TEMP_PREFIX inline void unpackStream(Stream& stream, hipo::Complex<double>& data) {
    unpackStreamT(stream, data);
}


/// pack and unpack std::string
TEMP_PREFIX inline int getStreamSize(const std::string& data) {
    int nbytes = Stream::getSizeOf<int>();
    nbytes += (int)data.size();
    return nbytes;
}

TEMP_PREFIX inline void packStream(Stream& stream, const std::string& data) {
    int size = (int)data.size();
    packStream(stream, size);
    stream.pushBack((void*)data.data(), size);
}

TEMP_PREFIX inline void unpackStream(Stream& stream, std::string& data) {
    int size;
    unpackStream(stream, size);
    data.resize(size);
    stream.popFront((void*)data.data(), size);
}


/// pack and unpack primitive types array, without the length
template <class Type>
int getStreamSize(const Type* data, int size) {
    int nbytes = 0;
    for (int i=0; i<size; i++) {
        nbytes += getStreamSize(data[i]);
    }
    return nbytes;
}
template <class Type>
void packStream(Stream& stream, const Type* data, int size) {
    for (int i=0; i<size; i++) {
        packStream(stream, data[i]);
    }
}
template <class Type>
void unpackStream(Stream& stream, Type* data, int size) {
    for (int i=0; i<size; i++) {
        unpackStream(stream, data[i]);
    }
}


/// pack and unpack std::vector
template <class Type>
int getStreamSize(const std::vector<Type>& data) {
    int size = (int)data.size();
    int nbytes = getStreamSize(size);
    for (int i=0; i<size; i++) {
        nbytes += getStreamSize(data[i]);
    }
    return nbytes;
}
template <class Type>
void packStream(Stream& stream, const std::vector<Type>& data) {
    int size = (int)data.size();
    packStream(stream, size);
    for (int i=0; i<size; i++) {
        packStream(stream, data[i]);
    }
}
template <class Type>
void unpackStream(Stream& stream, std::vector<Type>& data) {
    int size;
    unpackStream(stream, size);
    data.resize(size);
    for (int i=0; i<size; i++) {
        unpackStream(stream, data[i]);
    }
}

/// pack and unpack std::set
template <class Type>
int getStreamSize(const std::set<Type>& data) {
    int size = (int)data.size();
    int nbytes = getStreamSize(size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        nbytes += getStreamSize(*it);
    }
    return nbytes;
}
template <class Type>
void packStream(Stream& stream, const std::set<Type>& data) {
    int size = (int)data.size();
    packStream(stream, size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        packStream(stream, *it);
    }
}
template <class Type>
void unpackStream(Stream& stream, std::set<Type>& data) {
    int size;
    unpackStream(stream, size);
    for (int i=0; i<size; i++) {
        Type item;
        unpackStream(stream, item);
        data.insert(item);
    }
}

/// pack and unpack std::unordered_set
template <class Type>
int getStreamSize(const std::unordered_set<Type>& data) {
    int size = (int)data.size();
    int nbytes = getStreamSize(size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        nbytes += getStreamSize(*it);
    }
    return nbytes;
}
template <class Type>
void packStream(Stream& stream, const std::unordered_set<Type>& data) {
    int size = (int)data.size();
    packStream(stream, size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        packStream(stream, *it);
    }
}
template <class Type>
void unpackStream(Stream& stream, std::unordered_set<Type>& data) {
    int size;
    unpackStream(stream, size);
    for (int i=0; i<size; i++) {
        Type item;
        unpackStream(stream, item);
        data.insert(item);
    }
}

/// pack and unpack std::map
template <class Key, class Type>
int getStreamSize(const std::map<Key, Type>& data) {
    int size = (int)data.size();
    int nbytes = getStreamSize(size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        nbytes += getStreamSize(it->first);
        nbytes += getStreamSize(it->second);
    }
    return nbytes;
}
template <class Key, class Type>
void packStream(Stream& stream, const std::map<Key, Type>& data) {
    int size = (int)data.size();
    packStream(stream, size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        packStream(stream, it->first);
        packStream(stream, it->second);
    }
}
template <class Key, class Type>
void unpackStream(Stream& stream, std::map<Key, Type>& data) {
    int size;
    unpackStream(stream, size);
    for (int i=0; i<size; i++) {
        std::pair<Key, Type> item;
        unpackStream(stream, item.first);
        unpackStream(stream, item.second);
        data.insert(item);
    }
}


/// pack and unpack std::map
template <class Key, class Type>
int getStreamSize(const std::unordered_map<Key, Type>& data) {
    int size = (int)data.size();
    int nbytes = getStreamSize(size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        nbytes += getStreamSize(it->first);
        nbytes += getStreamSize(it->second);
    }
    return nbytes;
}
template <class Key, class Type>
void packStream(Stream& stream, const std::unordered_map<Key, Type>& data) {
    int size = (int)data.size();
    packStream(stream, size);
    for (auto it = data.begin(); it != data.end(); ++it) {
        packStream(stream, it->first);
        packStream(stream, it->second);
    }
}
template <class Key, class Type>
void unpackStream(Stream& stream, std::unordered_map<Key, Type>& data) {
    int size;
    unpackStream(stream, size);
    for (int i=0; i<size; i++) {
        std::pair<Key, Type> item;
        unpackStream(stream, item.first);
        unpackStream(stream, item.second);
        data.insert(item);
    }
}

template <class Type>
int getStreamSize(const Type& data) {
    return data.getStreamSize();
}
template <class Type>
void packStream(Stream& stream, const Type& data) {
    data.packStream(stream);
}
template <class Type>
void unpackStream(Stream& stream, Type& data) {
    data.unpackStream(stream);
}

}


