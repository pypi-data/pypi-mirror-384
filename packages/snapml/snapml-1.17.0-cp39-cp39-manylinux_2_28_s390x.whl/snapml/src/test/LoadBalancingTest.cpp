#include <Loaders.hpp>

void lb_test(uint32_t num_ex, const std::vector<uint32_t>& count, uint32_t numPartitions)
{

    auto partitioning = glm::load_balancing(num_ex, count.data(), numPartitions);

    std::cout << "partitioning: " << std::endl;
    for (size_t i = 0; i < partitioning.size(); i++) {
        std::cout << i << " " << partitioning[i].first << " " << partitioning[i].second << std::endl;
    }
    std::cout << std::endl;

    for (size_t i = 0; i < partitioning.size(); i++) {
        assert(partitioning[i].second - partitioning[i].first > 0);
    }
}

int main()
{

    // dense corner case (inspired by HIGGS)
    std::vector<uint32_t> count;

    for (uint32_t i = 0; i < 28; i++) {
        count.push_back(7500);
    }

    lb_test(count.size(), count, 8);
    lb_test(count.size(), count, 11);

    // sparse corner case (1)
    count.resize(4);
    count[0] = 1;
    count[1] = 1;
    count[2] = 1;
    count[3] = 100;

    lb_test(count.size(), count, 2);
    lb_test(count.size(), count, 4);

    // sparse corner case (2)
    count.resize(4);
    count[0] = 1;
    count[1] = 1;
    count[2] = 1;
    count[3] = 100;

    lb_test(count.size(), count, 2);
    lb_test(count.size(), count, 4);
}
