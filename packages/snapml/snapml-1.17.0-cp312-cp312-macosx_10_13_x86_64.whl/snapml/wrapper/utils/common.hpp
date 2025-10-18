/******************************************************************
 *
 * Licensed Materials - Property of IBM
 *
 * (C) Copyright IBM Corp. 2017, 2019. All Rights Reserved.
 *
 * US Government Users Restricted Rights - Use, duplication or
 * disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
 *
 *******************************************************************/

#define MAX_NODES_FOR_BASE 1
#define MAX_GPUS_FOR_BASE  2

#define STR(x)  STR2(x)
#define STR2(x) #x
#define NODES_ERRMSG                                                                                                   \
    ("Attempting to use more than " STR(MAX_NODES_FOR_BASE) " host(s) without a WML Accelerator License")
#define GPUS_ERRMSG                                                                                                    \
    ("Attempting to use more than " STR(MAX_GPUS_FOR_BASE) " accelerators without a WML Accelerator License")
#define PROCESSES_ERRMSG                                                                                               \
    ("Attempting to use more than " STR(MAX_GPUS_FOR_BASE) " MPI processes without a WML Accelerator License")

#define NODES_INFOMSG ("WML Accelerator license is required to use more than " STR(MAX_NODES_FOR_BASE) " host(s).")
#define GPUS_INFOMSG  ("WML Accelerator license is required to use more than " STR(MAX_GPUS_FOR_BASE) " accelerators.")
#define PROCS_INFOMSG ("WML Accelerator license is required to use more than " STR(MAX_GPUS_FOR_BASE) " MPI processes.")

int enterprise_license_exist();
