#include "UnitTests.hpp"
#include "Loaders.hpp"
#include "PrimalLogisticRegression.hpp"
#include "PrimalRidgeRegression.hpp"
#include "Privacy.hpp"

template <class D, class O> double sgd_test(std::shared_ptr<D> data, std::shared_ptr<D> data_t)
{

    double lambda = 1.0;
    double w_pos  = 1.0;
    double w_neg  = 1.0;
    double tol    = 0.001;

    std::shared_ptr<O> obj = std::make_shared<O>(lambda, w_pos, w_neg);

    // sgd parameters
    uint32_t num_epochs    = 10000;
    double   eta           = 0.0001;
    uint32_t batch_size    = 1;
    double   grad_clip     = 1.0;
    double   privacy_sigma = 0.0;

    auto solver_scd = std::make_shared<glm::HostSolver<D, O>>(data_t.get(), obj.get(), 1.0, tol);
    auto solver_sgd = std::make_shared<glm::SGDSolver<D, O>>(data.get(), obj.get(), 1.0, tol, eta, batch_size,
                                                             grad_clip, privacy_sigma);

    // run scd
    solver_scd->init(nullptr);
    double cost_init_scd = solver_scd->partial_cost();
    for (uint32_t i = 0; i < num_epochs; i++) {
        solver_scd->get_update(nullptr);
    }
    double cost_scd = solver_scd->partial_cost();

    // run sgd
    solver_sgd->init(nullptr);
    double cost_init_sgd = solver_sgd->partial_cost();
    for (uint32_t i = 0; i < num_epochs; i++) {
        solver_sgd->get_update(nullptr);
    }
    double cost_sgd = solver_sgd->partial_cost();

    printf("cost_scd_init: %e, cost_scd_end:%e, cost_sgd_init: %e, cost_sgd_end: %e\n", cost_init_scd, cost_scd,
           cost_init_sgd, cost_sgd);

    assert(glm::tests::are_close(cost_sgd, cost_scd, 0.07));
    assert(cost_scd < cost_sgd);
    assert(cost_init_scd == cost_init_sgd);
    assert(cost_scd < cost_init_scd);
    assert(cost_sgd < cost_init_sgd);

    return 0;
}

int main()
{
    using namespace glm;

    uint32_t seed   = 1232;
    uint32_t num_ex = 100;
    uint32_t num_ft = 20;

    // dense check
    auto data_dense   = tests::generate_small_random_dense_dataset(seed, false, num_ex, num_ft, 1.0);
    auto data_dense_t = tests::generate_small_random_dense_dataset(seed, true, num_ex, num_ft, 1.0);

    sgd_test<DenseDataset, PrimalLogisticRegression>(data_dense, data_dense_t);
    sgd_test<DenseDataset, PrimalRidgeRegression>(data_dense, data_dense_t);

    // sparse check

    auto data_sparse   = tests::generate_small_random_dataset(seed, false, num_ex, num_ft, 0.1);
    auto data_sparse_t = tests::generate_small_random_dataset(seed, true, num_ex, num_ft, 0.1);

    sgd_test<SparseDataset, PrimalLogisticRegression>(data_sparse, data_sparse_t);
    sgd_test<SparseDataset, PrimalRidgeRegression>(data_sparse, data_sparse_t);
}
