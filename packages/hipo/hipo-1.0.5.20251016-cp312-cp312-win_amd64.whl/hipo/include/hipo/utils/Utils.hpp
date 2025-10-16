#pragma once
#include <vector>
#include <regex>
#include <string>
#include <cstdarg>
#include <cstdio>
#include "Config.hpp"

namespace hipo {


class HIPO_WIN_API Utils {
public:
    static void loadPlugin(const std::string& so_fn);

    static bool isStrictMatrixMarket();

    static int getVerboseLevel();

    static bool isWaitSome();

    static std::string getLogDir();

};

#define HIPO_FATAL 0
#define HIPO_ERROR 1
#define HIPO_WARNING 2
#define HIPO_INFO 3

#define HIPO_LOG(x) LOG_IF(INFO, (x)<=Utils::getVerboseLevel())


inline std::vector<std::string> HIPO_WIN_API stringSplit(const std::string& str, const std::string&  delim) {
    std::regex reg(delim);
    std::vector<std::string> elems(std::sregex_token_iterator(str.begin(), str.end(), reg, -1),
                                   std::sregex_token_iterator());
    return elems;
}

inline std::vector<std::string> HIPO_WIN_API stringSplitExt(const std::string& str) {
    std::vector<std::string> ret(2);
    auto pos = str.find_last_of('.');
    if (pos != std::string::npos) {
        ret[0] = str.substr(0, pos);
        ret[1] = str.substr(pos+1);
    } else {
        ret[0] = str;
        ret[1] = "";
    }
    return ret;
}

template <typename T>
inline void HIPO_WIN_API hash_combine(std::size_t &seed, const T &val) {
    seed ^= std::hash<T>()(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}

// auxiliary generic functions to create a hash value using a seed
template <typename T, typename... Types>
void hash_combine(std::size_t &seed, const T &val, const Types &...args) {
    hash_combine(seed, val);
    hash_combine(seed, args...);
}

// optional auxiliary generic functions to support hash_val() without arguments
//inline void hash_combine(std::size_t &seed) {}
//  generic function to create a hash value out of a heterogeneous list of arguments
template <typename... Types>
std::size_t hash_val(const Types &...args) {
    std::size_t seed = 0;
    hash_combine(seed, args...);
    return seed;
}


std::string HIPO_WIN_API string_printf(const char* format, ...);


#  ifndef HIPO_TIC
#    define HIPO_TIC(name)
#  endif
#  ifndef HIPO_TOC
#    define HIPO_TOC(name)
#  endif

}
