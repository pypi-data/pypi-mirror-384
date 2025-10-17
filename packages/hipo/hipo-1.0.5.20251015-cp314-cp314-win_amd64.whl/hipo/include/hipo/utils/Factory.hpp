#pragma once
#include "json.hpp"
#include "hipo/utils/logging.hpp"
#include <iostream>
#include "hipo/utils/Utils.hpp"
#include "hipo/operators/ParOperatorBase.hpp"

namespace hipo {
#define LOGD(...) HIPO_LOG(HIPO_INFO) << string_printf(__VA_ARGS__)
#define LOGE(...) HIPO_LOG(HIPO_ERROR) << string_printf(__VA_ARGS__)

using JsonValue = nlohmann::json;

//#define REGISTER_APP(name, cls) \
//static int name ## _app_init = insertToMap<cls>(#name);

template <class _BaseT>
class HIPO_WIN_API Factory {
public:
    typedef std::function<std::shared_ptr<_BaseT>(const JsonValue& json, const ParOperator* root)> CreatorType;

    struct AppInfo {
        std::string type;
        std::string name;
        CreatorType creator;
        std::shared_ptr<_BaseT> inst;
    };

    std::map<std::string, AppInfo> s_creator_map;

    std::map<std::string, AppInfo>* getCreatorMap() {
        return &s_creator_map;
    }
    std::string key;

    Factory(const std::string& key) {
        this->key = key;
    }
    int insertToMap(const std::string& type, const std::string& name, CreatorType creator) {
        AppInfo info;
        info.creator = creator;
        info.type = type;
        info.name = name;
        auto map = getCreatorMap();
        //LOGD("insertToMap type %s, name %s\n", type.c_str(), name.c_str());
        map->insert({name, info});
        return (int)map->size();
    }
    
    AppInfo* getCreator(const std::string& name) {
        auto map = getCreatorMap();
        auto it = map->find(name);
        if (it == map->end()) {
            LOGE("getCreator %s failed\n", name.c_str());
            return nullptr;
        }
        return &it->second;
    }

    //static Factory* getRegistry();

    std::shared_ptr<_BaseT> createInstance(const JsonValue& json, const ParOperator* root=0) {

        CHECK(json.contains(key)) << "json " << json << " not contains key " << key;
        std::string tagName;
        if (json.contains("tagName")) {
            tagName = json["tagName"].get<std::string>();
        }

        std::string name = json[key].get<std::string>();

        AppInfo* info = getCreator(name);
        if (info == nullptr) {
            LOGE("createInstance %s failed\n", name.c_str());
            return nullptr;
        }
        JsonValue params;
        std::string param_key = name + "_params";
        if (json.contains(param_key)) {
            params = json[param_key];
        }
        HIPO_LOG(HIPO_INFO) << info->type <<  "::createInstance: name " << name << ", tagName '" << tagName << "', root " << root << ", params " << params << std::endl;

        if (root && tagName.size() > 0) {
            auto cb = root->getCallBack(tagName, ParOperator::BEFORE_CREATE);
            HIPO_LOG(HIPO_INFO) << "BEFORE_CREATE name " << name << " tagName " << tagName  << " callback " << (cb ? &cb : 0);
            if (cb) {
                cb(nullptr);
            }
        }

        auto inst = info->creator(params, root);
        if (tagName.size() > 0) {
            inst->setTagName(tagName);
        }
        if (root && tagName.size() > 0) {
            auto cb = root->getCallBack(tagName, ParOperator::AFTER_CREATE);
            HIPO_LOG(HIPO_INFO) << "AFTER_CREATE name " << name << " tagName " << tagName  << " callback " << (cb ? &cb : 0);
            if (cb) {
                cb(inst);
            }
        }
        return inst;
    }
};



template <class BaseT, class DerivedT>
class FactoryRegisterer {
public:
    FactoryRegisterer(const std::string& type, const std::string& name) {
        std::string baseType = type;
        std::string deriveType = name;
        auto creator = [baseType, deriveType](const JsonValue& json, const ParOperator* root) {
            auto app = std::make_shared<DerivedT>();
            app->setRoot(root);
            app->create(json);
            app->setBaseType(baseType);
            app->setType(deriveType);
            return std::shared_ptr<BaseT>(app);
        };
        BaseT::getFactory()->insertToMap(type, name, creator);
    }
};

}
