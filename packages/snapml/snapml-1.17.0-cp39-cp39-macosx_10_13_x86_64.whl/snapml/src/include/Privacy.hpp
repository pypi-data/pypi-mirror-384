/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2018
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Thomas Parnell
 *                Nikoalos Papandreou
 *
 * End Copyright
 ********************************************************************/

#ifndef GLM_PRIVACY
#define GLM_PRIVACY

#include <iostream>
#include <cmath>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace glm {
namespace privacy {

    double compute_delta(uint32_t num_batches, double q, double sigma, double eps, uint32_t& lam_opt)
    {

        double f_min = std::numeric_limits<double>::max();

        lam_opt = 0;

        for (uint32_t lam = 1; lam <= 128; lam++) {
            double E2 = 0.0;
            for (uint32_t k = 0; k <= lam; k++) {
                double log_lam_choose_k = std::lgamma(static_cast<double>(lam + 1))
                                          - std::lgamma(static_cast<double>(k + 1))
                                          - std::lgamma(static_cast<double>(lam - k + 1));
                double logB = log_lam_choose_k + static_cast<double>(k) * std::log(q)
                              + static_cast<double>(lam - k) * std::log(1 - q);
                double term1 = logB + std::log(1.0 - q)
                               + static_cast<double>(k) * (static_cast<double>(k) - 1.0) / 2.0 / sigma / sigma;
                double term2 = logB + std::log(q)
                               + static_cast<double>(k) * (static_cast<double>(k) + 1.0) / 2.0 / sigma / sigma;
                double res = exp(term1) + exp(term2);
                E2 += res;
            }
            double f_val = num_batches * std::log(E2) - lam * eps;
            /*
        if(lam == 1) {
            double f_chk = num_batches*std::log(1-q*q+q*q*exp(1.0/sigma/sigma))-eps;
            printf("%e %e\n", f_val, f_chk);
        }
        */
            if (f_val < f_min) {
                f_min   = f_val;
                lam_opt = lam;
            }
        }

        return exp(f_min);
    }

    // find the value of sigma that provides a given (eps,delta) privacy constraint
    // throws exception if it can't find one
    double find_sigma_for_privacy(uint32_t num_epochs, uint32_t num_ex, uint32_t batch_size, double target_eps,
                                  double target_delta)
    {

        double q = static_cast<double>(batch_size) / static_cast<double>(num_ex);
        double num_batches
            = static_cast<double>(num_epochs) * static_cast<double>(num_ex) / static_cast<double>(batch_size);

        // Try to find a satisfies a privacy guarantee
        uint32_t lam_opt {};
        double   sigma = 0.0001;
        double   delta {};
        while (sigma < 1000.0) {
            delta = compute_delta(num_batches, q, sigma, target_eps, lam_opt);
            if (delta <= target_delta) {
                // we have found a sigma that works
                break;
            } else {
                // increase sigma
                sigma *= 1.1;
            }
        }

        if (delta > target_delta) {
            std::stringstream msg;
            msg << "Could not satisfy requested privacy guarantee ";
            msg << "eps:" << std::scientific << target_eps << ", ";
            msg << "delta:" << std::scientific << target_delta;
            throw std::runtime_error(msg.str());
        }

        // if lam_opt = 1, we can refine the solution
        if (lam_opt == 1) {
            double term  = std::exp((std::log(target_delta) + target_eps) / num_batches);
            double term2 = (term - 1 + q * q) / q / q;
            sigma        = sqrt(1.0 / std::log(term2));
            printf("eps:%e, delta:%e, sigma:%e, lam_opt:%d\n", target_eps, target_delta, sigma, lam_opt);
            return sigma;
        } else {
            printf("eps:%e, delta:%e, sigma:%e, lam_opt:%d\n", target_eps, delta, sigma, lam_opt);
            return sigma;
        }
    }

} // namespace privacy
} // namespace glm

#endif
