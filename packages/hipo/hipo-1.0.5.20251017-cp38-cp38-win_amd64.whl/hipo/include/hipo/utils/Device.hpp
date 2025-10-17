#pragma once
#include <string>
#include <map>
#include <vector>
#include <iostream>
#include <memory>
#include "hipo/utils/Config.hpp"

namespace hipo {



class HIPO_WIN_API Device {
private:
    int m_type = 0;
    int m_id = 0;
    std::string m_type_name = "cpu";

    static std::map<std::string, int> type_map;
public:
    struct DeviceInfo {
        std::shared_ptr<void> space = nullptr;
        void* stream = nullptr;
    };
    static std::map<Device, DeviceInfo>* getDeviceInfoMap();

    enum Type {
        CPU = 0,
        CUDA = 1,
        HIP = 2,
        MUXI = 3,
    };
    explicit Device(int type = 0, int id = 0);
    Device(const std::string& dev);
    int getId() const {
        return m_id;
    }
    int getType() const {
        return m_type;
    }

    std::string getString() const {
        return m_type_name + ":" + std::to_string(m_id);
    }

    DeviceInfo getDeviceInfo() const;

    void setDeviceContext() const;

    int getDeviceContext() const;

    static void initialize();
    static void finalize();

    static std::vector<Device> getAllDevices();
    
    bool operator==(const Device& dev) const {
        return m_type == dev.m_type && m_id == dev.m_id;
    }

    bool operator<(const Device& dev) const {
        return m_type < dev.m_type || (m_type == dev.m_type && m_id < dev.m_id);
    }
    bool operator!=(const Device& dev) const {
        return !(*this == dev);
    }

    template <typename _T>
    _T* malloc(size_t size) const {
        return reinterpret_cast<_T*>(this->rawMalloc(sizeof(_T)*size));
    }
    template <typename _T>
    void free(_T& ptr) const {
        if (ptr != 0) {
            this->rawFree(ptr);
        }
        ptr = 0;
    }
    void* rawMalloc(size_t size) const;
    void* rawRealloc(void* ptr, size_t size) const;
    void rawFree(void* ptr) const;


    template <typename _T>
    void copyTo(size_t size, const _T* src, const Device& destDevice, _T* dest) {
        this->rawCopyTo(sizeof(_T)*size, reinterpret_cast<const void*>(src), destDevice, dest);
    }

    void rawCopyTo(size_t size, const void* src, const Device& destDevice, void* dest);
};

}
