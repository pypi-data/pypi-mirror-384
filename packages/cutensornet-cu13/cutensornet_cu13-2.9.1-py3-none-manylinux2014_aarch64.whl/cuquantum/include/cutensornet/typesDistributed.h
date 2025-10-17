/*
 * Copyright (c) 2022-2023, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
 *
 * NVIDIA CORPORATION and its licensors retain all intellectual property
 * and proprietary rights in and to this software, related documentation
 * and any modifications thereto.  Any use, reproduction, disclosure or
 * distribution of this software and related documentation without an express
 * license agreement from NVIDIA CORPORATION is strictly prohibited.
 */

 /**
 * @file
 * @brief This file provides type declarations for cuTensorNet-Distributed.
 */

#pragma once

#include <stdint.h>

#include <cuda_runtime.h>

/**
 * \typedef cutensornetDistributedCommunicator_t
 * \brief (Internal): The C structure for holding an MPI communicator in a type-erased form. 
 */
typedef struct {
    void* commPtr;   ///< owning pointer to the MPI_Comm data structure
    size_t commSize; ///< size of the MPI_Comm data structure
} cutensornetDistributedCommunicator_t;

#define CUTENSORNET_DISTRIBUTED_INTERFACE_VERSION 2

/**
 * \typedef cutensornetDistributedInterface_t
 * \brief (Internal): Dynamic API wrapper runtime binding table for the distributed communication service.
*/
typedef struct {
    int version;
    int (*getNumRanks)(const cutensornetDistributedCommunicator_t*,
                       int32_t*);
    int (*getNumRanksShared)(const cutensornetDistributedCommunicator_t*,
                             int32_t*);
    int (*getProcRank)(const cutensornetDistributedCommunicator_t*,
                       int32_t*);
    int (*Barrier)(const cutensornetDistributedCommunicator_t*);
    int (*Bcast)(const cutensornetDistributedCommunicator_t*,
                 void*, int32_t, cudaDataType_t, int32_t);
    int (*Allreduce)(const cutensornetDistributedCommunicator_t*,
                     const void*, void*, int32_t, cudaDataType_t);
    int (*AllreduceInPlace)(const cutensornetDistributedCommunicator_t*,
                            void*, int32_t, cudaDataType_t);
    int (*AllreduceInPlaceMin)(const cutensornetDistributedCommunicator_t*,
                               void*, int32_t, cudaDataType_t);
    int (*AllreduceDoubleIntMinloc)(const cutensornetDistributedCommunicator_t*,
                                    const void*, void*);
    int (*Allgather)(const cutensornetDistributedCommunicator_t*,
                     const void*, void*, int32_t, cudaDataType_t);
} cutensornetDistributedInterface_t;
