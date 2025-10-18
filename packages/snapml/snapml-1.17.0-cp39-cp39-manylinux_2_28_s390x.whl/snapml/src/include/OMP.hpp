/*********************************************************************
 * Copyright
 *
 * IBM Confidential
 * (C) COPYRIGHT IBM CORP. 2021
 * IBM Zurich Research Laboratory - Cloud Storage & Analytics Group
 * All rights reserved.
 *
 * This software contains the valuable trade secrets of IBM or its
 * licensors.  The software is protected under international copyright
 * laws and treaties.  This software may only be used in accordance with
 * the terms of its accompanying license agreement.
 *
 * Authors      : Martin Petermann
 *
 * End Copyright
 ********************************************************************/

#ifndef OMPCLASS
#define OMPCLASS

#ifndef WITH_ZOS
#include <omp.h>
#else
static void omp_set_num_threads(int num) __attribute__((unused));
static int  omp_get_thread_num() __attribute__((unused));
static int  omp_get_max_threads() __attribute__((unused));
static void omp_set_nested(bool b) __attribute__((unused));

static void omp_set_num_threads(int num) { }
static int  omp_get_thread_num() { return 0; }
static int  omp_get_max_threads() { return 1; }
static void omp_set_nested(bool b) { }
#endif

#include "Dataset.hpp"

/*!
 * @brief The class `OMP` is designed to provide a exception save facility for OpenMP.
 */
class OMP {
public:
    /*! @brief Member function `OMP::parallel_for` is used to replace `#pragma omp parallel for` directives.
     *
     *  A directive like
     *
     *      std::vector<int> v(10);
     *      #pragma omp parallel for
     *      for (int i = 0; i < 10; i++)
     *          v[i] = i;
     *
     *  can be replaced with
     *
     *      std::vector<int> v(10);
     *      OMP::parallel_for<int>(0, 10, [&v](int i) {
     *          v[i] = i;
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     */

    template <typename Iterator, typename Function>
    static void parallel_for(Iterator start, Iterator end, const Function& f)
    // static void parallel_for(long start, long end, const std::function<void(long, int)>& f) //slower
    {
        std::exception_ptr eptr;
#pragma omp parallel for
        for (Iterator i = start; i < end; i++) {
            try {
                f(i);
            } catch (...) {
#pragma omp critical
                eptr = std::current_exception();
            }
        }
        if (eptr)
            std::rethrow_exception(eptr);
    }

    /*! @brief Member function `OMP::parallel_for_collapse_2` is used to replace `#pragma omp parallel for collapse(2)`
     *  directives.
     *
     *  A directive like
     *
     *      std::vector<int> v(200);
     *      #pragma omp parallel for collapse(2)
     *      for (int i = 0; i < 10; i++)
     *          for (int j = 0; j < 20; j++)
     *              v[10*i+j] = i + j;
     *
     *  can be replaced with
     *
     *      std::vector<int> v(200);
     *      OMP::parallel_for_collapse_2<int>(0, 10, 0, 20, [&v](int i, int j) {
     *          v[10*i+j] = i + j;
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     */

    template <typename Iterator_1, typename Iterator_2, typename Function>
    static void parallel_for_collapse_2(Iterator_1 start_1, Iterator_1 end_1, Iterator_2 start_2, Iterator_2 end_2,
                                        const Function& f)
    {
        std::exception_ptr eptr;
#pragma omp parallel for COLPS(2)
        for (Iterator_1 i = start_1; i < end_1; i++) {
            for (Iterator_2 j = start_2; j < end_2; j++) {
                try {
                    f(i, j);
                } catch (...) {
#pragma omp critical
                    eptr = std::current_exception();
                }
            }
        }
        if (eptr)
            std::rethrow_exception(eptr);
    }

    /*! @brief Member function `OMP::parallel_for_sched_dynamic` is used to replace `#pragma omp parallel for
     *  schedule(dynamic)` directives.
     *
     *  A directive like
     *
     *      std::vector<int> v(10);
     *      #pragma omp parallel for schedule(dynamic)
     *      for (int i = 0; i < 10; i += 2)
     *          v[i] = i;
     *
     *  can be replaced with
     *
     *      std::vector<int> v(10);
     *      OMP::parallel_for_sched_dynamic<int>(0, 10, 2, [&v](int i) {
     *          v[i] = i;
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     */

    template <typename Iterator, typename Function>
    static void parallel_for_sched_dynamic(Iterator start, Iterator end, Iterator incr, const Function& f)
    {
        std::exception_ptr eptr;
#pragma omp parallel for schedule(dynamic)
        for (Iterator i = start; i < end; i += incr) {
            try {
                f(i);
            } catch (...) {
#pragma omp critical
                eptr = std::current_exception();
            }
        }
        if (eptr)
            std::rethrow_exception(eptr);
    }

    /*! @brief Member function `OMP::_for` is used to replace `#pragma omp for` directives.
     *
     *  A directive like
     *
     *      std::vector<int> v(10);
     *      #pragma omp parallel
     *      {
     *          thrd_nr = omp_get_thread_num();
     *      #pragma omp for
     *          for (int i = 0; i < 10; i++)
     *              v[i] = thrd_nr;
     *      }
     *
     *  can be replaced with
     *
     *      std::vector<int> v(10);
     *      OMP::parallel([&v](int i) {
     *          thrd_nr = omp_get_thread_num();
     *          OMP::_for<int>(0, 10, [&](int i) {
     *              v[i] = thrd_nr;
     *          });
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     */

    template <typename Iterator, typename Function>
    static void _for(Iterator start, Iterator end, std::exception_ptr& eptr, const Function& f)
    {
#pragma omp for
        for (Iterator i = start; i < end; i++) {
            try {
                f(i);
            } catch (...) {
#pragma omp critical
                eptr = std::current_exception();
            }
        }
    }

    /*! @brief Member function `OMP::parallel` is used to replace `#pragma omp parallel` directives.
     *
     *  A directive like
     *
     *      std::vector<int> v(10);
     *      #pragma omp parallel
     *      {
     *          thrd_nr = omp_get_thread_num();
     *      #pragma omp for
     *          for (int i = 0; i < 10; i++)
     *              v[i] = thrd_nr;
     *      }
     *
     *  can be replaced with
     *
     *      std::vector<int> v(10);
     *      OMP::parallel([&v](int i) {
     *          thrd_nr = omp_get_thread_num();
     *          OMP::_for<int>(0, 10, [&](int i) {
     *              v[i] = thrd_nr;
     *          });
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     */

    template <typename Function> static void parallel(const Function& f)
    {
        std::exception_ptr eptr = nullptr;
#pragma omp parallel
        {
            try {
                f(eptr);
            } catch (...) {
#pragma omp critical
                eptr = std::current_exception();
            }
        }
        if (eptr)
            std::rethrow_exception(eptr);
    }

    /*! @brief Member function `OMP::parallel_for_reduction` is used to replace `#pragma omp parallel for reduction(+ :
     *  <redvar>)` directives.
     *
     *  A directive like
     *
     *      int sum = 0;
     *      #pragma omp parallel for reduction(+ : sum)
     *      for (int i = 0; i < 10; i++)
     *          sum += i;
     *
     *  can be replaced with
     *
     *      int sum = 0;
     *      OMP::parallel_for_reduction<int>(0, 10, sum, [](int i, int sum) {
     *          sum += i;
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     *
     *  For code compatibility on Windows since Visual Studio only supports OpenMP 2.0
     *  standard where \<redvar> reference type is not allowed to be used as reduction,
     *  \<redvar> needed to be copied into the local variable and after performing
     *  `omp parallel for reduction` the local variable is copied back to \<redvar>.
     */

    template <typename Iterator, typename T, typename Function>
    static void parallel_for_reduction(Iterator start, Iterator end, T& redvar, const Function& f)
    {
        T                  redvar_loc = redvar;
        std::exception_ptr eptr       = nullptr;
#pragma omp parallel for reduction(+ : redvar_loc)
        for (Iterator i = start; i < end; i++) {
            try {
                f(i, redvar_loc);
            } catch (...) {
#pragma omp critical
                eptr = std::current_exception();
            }
        }
        redvar = redvar_loc;
        if (eptr)
            std::rethrow_exception(eptr);
    }

    /*! @brief Member function `OMP::critical` is used to replace `#pragma omp critical` directives.
     *
     *  A directive like (example in conjunction with OMP::parallel and OMP::_for_nowait)
     *
     *      #pragma omp parallel
     *          {
     *              std::vector<long> v(len1);
     *      #pragma omp for nowait
     *              for (int i = 0; i < len2; i++)
     *                  for (int j = 0; j < len1; j++)
     *                      v[j] += i+j + i;
     *      #pragma omp critical
     *              for (int j = 0; j < len1; j++)
     *                  p2[j] += v[j];
     *              std::vector<long>().swap(v);
     *          }
     *
     *  can be replaced with
     *
     *      OMP::parallel([&p3, &len1, &len2](std::exception_ptr& eptr) {
     *          std::vector<long> v(len1);
     *          OMP::_for_nowait<int>(0, len2, eptr, [&] (int i) {
     *              for (int j = 0; j < len1; j++)
     *                  v[j] += i+j + i;
     *          });
     *          OMP::critical([&](){
     *              for (int j = 0; j < len1; j++)
     *                  p3[j] += v[j];
     *              std::vector<long>().swap(v);
     *          });
     *      });
     *
     *  where in [] a list of variables is specified to pass to the lambda expression.
     */

    template <typename Function> static void critical(const Function& f)
    {
#pragma omp critical
        f();
    }

    /*! @brief Member function `OMP::_for_nowait` is used to replace `#pragma omp for nowait` directives.
     *
     *  It's similar to the OMP::_for function template.
     */

    template <typename Iterator, typename Function>
    static void _for_nowait(Iterator start, Iterator end, std::exception_ptr& eptr, const Function& f)
    {
#pragma omp for nowait
        for (Iterator i = start; i < end; i++) {
            try {
                f(i);
            } catch (...) {
#pragma omp critical
                eptr = std::current_exception();
            }
        }
    }
};

#endif
