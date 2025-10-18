#include "Privacy.hpp"
#include <cassert>

int main()
{

    uint32_t num_epochs = 200;
    uint32_t num_ex     = 200000;
    uint32_t batch_size = 1;

    std::cout << "num_epochs = " << num_epochs << std::endl;
    std::cout << "num_ex     = " << num_ex << std::endl;
    std::cout << "batch_size = " << batch_size << std::endl;

    for (double log_eps = -4.0; log_eps <= 10.0; log_eps += 1.0) {
        double eps = pow(10.0, log_eps);
        try {
            double sigma = glm::privacy::find_sigma_for_privacy(num_epochs, num_ex, batch_size, eps, 0.01);
            assert(!std::isinf(sigma));
            assert(!std::isnan(sigma));
        } catch (std::exception& e) {
            std::cout << e.what() << std::endl;
        }
    }

    return 0;
}
