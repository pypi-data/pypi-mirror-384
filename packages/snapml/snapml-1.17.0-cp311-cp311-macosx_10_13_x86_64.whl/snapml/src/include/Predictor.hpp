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
 * Authors      : Thomas Parnell
 *
 * End Copyright
 ********************************************************************/

#ifndef PREDICTOR
#define PREDICTOR

#include "DenseDataset.hpp"

namespace tree {

class Predictor {

public:
    // virtual dtor
    virtual ~Predictor() { }

    // for regression returns predicted value for each example
    // for binary classification returns a class label in {-1, +1} for each example
    // for multi-class classification return a class label in {0, 1, ..., num_classes-1} for each example
    virtual void predict(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const = 0;

    // for regression this function is undefined
    // returns a vector for probabilities (p_0, p_1, ..., p_{num_classes-1}) for each example
    virtual void predict_proba(glm::DenseDataset* const data, double* const preds, uint32_t num_threads = 1) const = 0;
};

}

#endif
