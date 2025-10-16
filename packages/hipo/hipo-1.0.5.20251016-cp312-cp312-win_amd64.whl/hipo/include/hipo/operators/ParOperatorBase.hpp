#pragma once
#include <functional>
#include <memory>
#include <string>
#include <map>
#include <list>
#include <sstream>

namespace hipo {



class HIPO_WIN_API ParOperator {
public:
    enum CallBackPlace {
        BEFORE_CREATE = 0,
        AFTER_CREATE = 1,
        BEFORE_SETUP = 2,
        AFTER_SETUP = 3
    };
    typedef std::function<void(std::shared_ptr<ParOperator> par_op)> CallBackFunc;
        ParOperator();
    virtual ~ParOperator();
    void appendChild(std::shared_ptr<ParOperator> child, const std::string& name);
    static void recusiveFindAllOpsByTagName(const ParOperator* root, const std::string& tagName, std::vector<const ParOperator*>& ops);
    const ParOperator* findOpByTagName(const std::string& name);
    std::vector<const ParOperator*> findAllOpsByTagName(const std::string& name);
    void registerCallBack(const std::string& tagName, CallBackPlace place, CallBackFunc par_op);
    CallBackFunc getCallBack(const std::string& tagName, CallBackPlace place) const;
    void setName(const std::string& name) {
        this->name = name;
    }
    void setType(const std::string& type) {
        this->type = type;
    }
    void setBaseType(const std::string& baseType) {
        this->baseType = baseType;
    }
    void setTagName(const std::string& tagName) {
        this->tagName = tagName;
    }
    const ParOperator* getRoot() const {
        return this->root;
    }
    void setRoot(const ParOperator* op) {
        this->root = op;
    }
    void describe(std::ostringstream& oss, int level) const;
    std::string describe() const {
        std::ostringstream oss;
        describe(oss, 0);
        return oss.str();
    }
protected:
    std::string type;
    std::string baseType;
    std::string name;
    std::string tagName;
    const ParOperator* parent = 0;
    const ParOperator* root = 0;
    std::map<std::string, std::map<int,CallBackFunc >> callback;
    std::list<std::shared_ptr<ParOperator>> children;
};

}
