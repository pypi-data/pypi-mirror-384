/*********************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2022, 2023. All Rights Reserved.

 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 ********************************************************************/

#pragma once

namespace snapml {

//! @ingroup c-api
enum class task_t { classification, regression };

//! @ingroup c-api
enum class objective_t { mse, poisson };

//! @ingroup c-api
enum class split_t { gini, mse };

//! @ingroup c-api
enum class ensemble_t { forest, boosting };

//! @ingroup c-api
enum class compare_t { less_than, less_or_equal };

}
