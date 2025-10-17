
#include "hipo/mat/ParCSRMatrix.hpp"
#include "hipo/operators/ParOperator.hpp"
#include "hipo/utils/TestCase.hpp"

using namespace hipo;


int getDeviceIdOnHost(MPI_Comm comm = MPI_COMM_WORLD) {
    int nprocs, myrank;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);
    int root = 0;


    char processor_name[MPI_MAX_PROCESSOR_NAME];
    int name_len;

    MPI_Get_processor_name(processor_name, &name_len);
    
    std::string name(processor_name, 0, name_len);


    std::vector<std::string> all_names(nprocs);
    comu::stlmpi_gather_stream(comm, name, all_names, root);
    std::vector<int> devIds(nprocs, -1);

    if (myrank == root) {
        std::map<std::string, int> counter;
        for (int i=0; i<all_names.size(); i++) {
            auto& cnt = counter[all_names[i]];
            devIds[i] = cnt;
            cnt++;
        }
    }
    int devId;
    comu::stlmpi_scatter_stream(comm, devIds, devId, root);
    return devId;
}


int main(int argc, char *argv[])
{
    typedef double _ValT;
    typedef HIPO_INT _IdxT;

    Device::initialize();
    {
    Device device = Device("cpu");

    if (argv[1] == std::string("-dev")) {
        device = Device(argv[2]);
        argv++;
        argv++;
    }

    auto comm = MPI_COMM_WORLD;
    int nprocs, myrank;
    MPI_Comm_size(comm, &nprocs);
    MPI_Comm_rank(comm, &myrank);
    
    
    auto devId = getDeviceIdOnHost(comm);

    HIPO_LOG(HIPO_INFO) << "myrank " << myrank << " devid " << devId;

        //Utils::loadPlugin();
    auto devices = Device::getAllDevices();

    

    HIPO_LOG(HIPO_INFO) << OperatorGallery<_ValT, _IdxT>::getAllInstances();

    typedef ParCSRMatrixT<_ValT, _IdxT> Matrix;
    Matrix A;

    typedef ParMatrixT<_ValT, _IdxT> Vector;
    Vector b;

    std::string fn1 = argv[1];
    std::string fn2 = argv[2];
    std::string json_fn = argv[3];
    
    std::ifstream ifs(json_fn);
    JsonValue json;
    ifs >> json;


    if (fn1 == "testcase" && fn2 == "testcase") {
        auto testcase = TestCaseT<_ValT, _IdxT>::getFactory()->createInstance(json["testcase"]);
        Vector x_gt;
        testcase->setDeviceAndComm(device, comm);
        testcase->generate(A, x_gt, b);

    } else {

        A.loadFromFile(argv[1], device, comm);

        b.loadFromFile(argv[2], device, comm);
    }
    if (b.getSize() == 0) {
        b.create(A.getRows(), A.getDevice(), A.getComm());
        b.fill(1);
    }



    auto solver = ParSolverT<_ValT, _IdxT>::getFactory()->createInstance(json["solver"]);
    auto precond = ParPreconditionerT<_ValT, _IdxT>::getFactory()->createInstance(json["preconditioner"]);

    solver->setup(A);
    precond->setup(A);

    HIPO_LOG(HIPO_INFO) << "solver\n" << solver->describe();
    HIPO_LOG(HIPO_INFO) << "precond\n" << precond->describe();

    int iter;
    double relres;

    Vector x;
    x.create(A.getRows(), A.getDevice(), A.getComm());
    x.fill(0);

    solver->solve(*precond, A, b, x, iter, relres);

    }
    Device::finalize();
    return 0;
}

