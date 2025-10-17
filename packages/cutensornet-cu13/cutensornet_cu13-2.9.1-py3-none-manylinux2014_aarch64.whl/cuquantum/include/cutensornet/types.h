/*
 * Copyright (c) 2021-2025, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
 *
 * NVIDIA CORPORATION and its licensors retain all intellectual property
 * and proprietary rights in and to this software, related documentation
 * and any modifications thereto.  Any use, reproduction, disclosure or
 * distribution of this software and related documentation without an express
 * license agreement from NVIDIA CORPORATION is strictly prohibited.
 */

/**
 * @file
 * @brief This file defines the types provided by the cuTensorNet library.
 */

#pragma once

#include <stdint.h>

#include <cuda_runtime.h>
#include <cuComplex.h>

/**
 * \brief The maximal length of the name for a user-provided mempool.
 */
#define CUTENSORNET_ALLOCATOR_NAME_LEN 64

/**
 * \brief cuTensorNet status type returns
 *
 * \details The type is used for function status returns. All cuTensorNet library functions return their status, which can have the following values.
 */
typedef enum
{
    /** The operation completed successfully.*/
    CUTENSORNET_STATUS_SUCCESS                = 0,
    /** The cuTensorNet library was not initialized.*/
    CUTENSORNET_STATUS_NOT_INITIALIZED        = 1,
    /** Resource allocation failed inside the cuTensorNet library.*/
    CUTENSORNET_STATUS_ALLOC_FAILED           = 3,
    /** An unsupported value or parameter was passed to the function (indicates a user error).*/
    CUTENSORNET_STATUS_INVALID_VALUE          = 7,
    /** The device is either not ready, or the target architecture is not supported.*/
    CUTENSORNET_STATUS_ARCH_MISMATCH          = 8,
    /** An access to GPU memory space failed, which is usually caused by a failure to bind a texture.*/
    CUTENSORNET_STATUS_MAPPING_ERROR          = 11,
    /** The GPU program failed to execute. This is often caused by a launch failure of the kernel on the GPU, which can be caused by multiple reasons.*/
    CUTENSORNET_STATUS_EXECUTION_FAILED       = 13,
    /** An internal cuTensorNet error has occurred.*/
    CUTENSORNET_STATUS_INTERNAL_ERROR         = 14,
    /** The requested operation is not supported.*/
    CUTENSORNET_STATUS_NOT_SUPPORTED          = 15,
    /** The functionality requested requires some license and an error was detected when trying to check the current licensing.*/
    CUTENSORNET_STATUS_LICENSE_ERROR          = 16,
    /** A call to CUBLAS did not succeed.*/
    CUTENSORNET_STATUS_CUBLAS_ERROR           = 17,
    /** Some unknown CUDA error has occurred.*/
    CUTENSORNET_STATUS_CUDA_ERROR             = 18,
    /** The provided workspace was insufficient.*/
    CUTENSORNET_STATUS_INSUFFICIENT_WORKSPACE = 19,
    /** The driver version is insufficient.*/
    CUTENSORNET_STATUS_INSUFFICIENT_DRIVER    = 20,
    /** An error occurred related to file I/O.*/
    CUTENSORNET_STATUS_IO_ERROR               = 21,
    /** The dynamically linked cuTENSOR library is incompatible.*/
    CUTENSORNET_STATUS_CUTENSOR_VERSION_MISMATCH = 22,
    /** Drawing device memory from a mempool is requested, but the mempool is not set.*/
    CUTENSORNET_STATUS_NO_DEVICE_ALLOCATOR    = 23,
    /** All hyper samples failed for one or more errors please enable LOGs via export CUTENSORNET_LOG_LEVEL= > 1 for details.*/
    CUTENSORNET_STATUS_ALL_HYPER_SAMPLES_FAILED = 24,
    /** A call to cuSOLVER did not succeed.*/
    CUTENSORNET_STATUS_CUSOLVER_ERROR = 25,
    /** Operation with the device memory pool failed.*/
    CUTENSORNET_STATUS_DEVICE_ALLOCATOR_ERROR = 26,
    /** Distributed communication service failed.*/
    CUTENSORNET_STATUS_DISTRIBUTED_FAILURE = 27,
    /** Operation interrupted by user and cannot recover or complete.*/
    CUTENSORNET_STATUS_INTERRUPTED = 28,
    /** Operation not implemented.*/
} cutensornetStatus_t;

/**
 * \brief Encodes cuTensorNet's compute type (see "User Guide - Accuracy Guarantees" for details).
 */
typedef enum
{
    CUTENSORNET_COMPUTE_16F    = (1U << 0U),  ///< floating-point: 5-bit exponent and 10-bit mantissa (aka half)
    CUTENSORNET_COMPUTE_16BF   = (1U << 10U), ///< floating-point: 8-bit exponent and 7-bit mantissa (aka bfloat)
    CUTENSORNET_COMPUTE_TF32   = (1U << 12U), ///< floating-point: 8-bit exponent and 10-bit mantissa (aka tensor-float-32)
    CUTENSORNET_COMPUTE_3XTF32 = (1U << 13U), ///< floating-point: More precise than TF32, but less precise than float
    CUTENSORNET_COMPUTE_32F    = (1U << 2U),  ///< floating-point: 8-bit exponent and 23-bit mantissa (aka float)
    CUTENSORNET_COMPUTE_64F    = (1U << 4U),  ///< floating-point: 11-bit exponent and 52-bit mantissa (aka double)
    CUTENSORNET_COMPUTE_8U     = (1U << 6U),  ///< 8-bit unsigned integer
    CUTENSORNET_COMPUTE_8I     = (1U << 8U),  ///< 8-bit signed integer
    CUTENSORNET_COMPUTE_32U    = (1U << 7U),  ///< 32-bit unsigned integer
    CUTENSORNET_COMPUTE_32I    = (1U << 9U),  ///< 32-bit signed integer
} cutensornetComputeType_t;

/**
 * This enum lists all attributes of a ::cutensornetNetworkDescriptor_t that are accessible.
 */
typedef enum
{
    CUTENSORNET_NETWORK_INPUT_TENSORS_NUM_CONSTANT      = 0,   ///< int32_t: The number of input tensors that are constant (get-only).
    CUTENSORNET_NETWORK_INPUT_TENSORS_CONSTANT          = 1,   ///< ::cutensornetTensorIDList_t: Structure holding number of, and indices of input tensors that are constant. Setting this attribute will override previous setting of `CUTENSORNET_NETWORK_INPUT_TENSORS_CONSTANT`.
    CUTENSORNET_NETWORK_INPUT_TENSORS_NUM_CONJUGATED    = 10,  ///< int32_t: The number of input tensors that are conjugated (get-only).
    CUTENSORNET_NETWORK_INPUT_TENSORS_CONJUGATED        = 11,  ///< ::cutensornetTensorIDList_t: Structure holding number of, and indices of input tensors that are conjugated. Setting number of conjugated tesnors to -1 will select all tensors. Setting this attribute will override previous setting of `CUTENSORNET_NETWORK_INPUT_TENSORS_CONJUGATED`.
    CUTENSORNET_NETWORK_INPUT_TENSORS_NUM_REQUIRE_GRAD  = 20,  ///< int32_t: The number of input tensors that require gradient computation (get-only).
    CUTENSORNET_NETWORK_INPUT_TENSORS_REQUIRE_GRAD      = 21,  ///< ::cutensornetTensorIDList_t: Structure holding number of, and indices of input tensors that require gradient computation. Setting number of tensors requiring gradient computation to -1 will select all tensors. Setting this attribute will override previous setting of `CUTENSORNET_NETWORK_INPUT_TENSORS_REQUIRE_GRAD`.
    CUTENSORNET_NETWORK_COMPUTE_TYPE                    = 30,  ///< cutensornetComputeType_t: Set compute type.
} cutensornetNetworkAttributes_t;

/**
 * \brief This enum lists graph algorithms that can be set.
 */
typedef enum
{
    CUTENSORNET_GRAPH_ALGO_RB,
    CUTENSORNET_GRAPH_ALGO_KWAY,
} cutensornetGraphAlgo_t;

/**
 * \brief This enum lists memory models used to determine workspace size.
 */
typedef enum
{
    CUTENSORNET_MEMORY_MODEL_HEURISTIC,
    CUTENSORNET_MEMORY_MODEL_CUTENSOR,
} cutensornetMemoryModel_t;

/**
 * \brief This enum lists various cost functions to optimize with.
 */
typedef enum
{
    CUTENSORNET_OPTIMIZER_COST_FLOPS,      ///< Conventional flops (default)
    CUTENSORNET_OPTIMIZER_COST_TIME,       ///< Time estimation based on arithmetic intensity (experimental). It is only available for Volta and later architectures.
} cutensornetOptimizerCost_t;

/**
 * \brief This enum lists various smart optimization options 
 */
typedef enum
{
    CUTENSORNET_SMART_OPTION_DISABLED = 0, ///< No smart options are enabled
    CUTENSORNET_SMART_OPTION_ENABLED  = 1,  ///< Automatic configuration (SMART) options of the contractionOptimizer are enabled (default behavior). This include but not limited to limit the pathfinder elapsed time and to avoid meaningless configuration as well as adjusting configuration on the fly.
} cutensornetSmartOption_t;

/**
 * This enum lists all attributes of a ::cutensornetContractionOptimizerConfig_t that can be modified.
 */
typedef enum
{
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_GRAPH_NUM_PARTITIONS      = 0,  ///< int32_t: The network is recursively split over `num_partitions` until the size of each partition is less than or equal to the cutoff.
                                                                             ///<          The allowed range for `num_partitions` is [2, 30]. When the hyper-optimizer is disabled the default value is 8.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_GRAPH_CUTOFF_SIZE         = 1,  ///< int32_t: The network is recursively split over `num_partitions` until the size of each partition is less than or equal to this cutoff.
                                                                             ///<          The allowed range for `cutoff_size` is [4, 50]. When the hyper-optimizer is disabled the default value is 8.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_GRAPH_ALGORITHM           = 2,  ///< ::cutensornetGraphAlgo_t: the graph algorithm to be used in graph partitioning. Choices include
                                                                             ///<          CUTENSORNET_GRAPH_ALGO_KWAY (default) or CUTENSORNET_GRAPH_ALGO_RB.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_GRAPH_IMBALANCE_FACTOR    = 3,  ///< int32_t: Specifies the maximum allowed size imbalance among the partitions. Allowed range [30, 2000]. When the hyper-optimizer is disabled the default value is 200.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_GRAPH_NUM_ITERATIONS      = 4,  ///< int32_t: Specifies the number of iterations for the refinement algorithms at each stage of the uncoarsening process of the graph partitioner.
                                                                             ///<          Allowed range [1, 500]. When the hyper-optimizer is disabled the default value is 60.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_GRAPH_NUM_CUTS            = 5,  ///< int32_t: Specifies the number of different partitioning that the graph partitioner will compute. The final partitioning is the one that achieves the best edge-cut or communication volume.
                                                                             ///<          Allowed range [1, 40]. When the hyper-optimizer is disabled the default value is 10.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_RECONFIG_NUM_ITERATIONS   = 10, ///< int32_t: Specifies the number of subtrees to be chosen for reconfiguration.
                                                                             ///<          A value of 0 disables reconfiguration. The default value is 500. The amount of time spent in reconfiguration, which usually dominates the pathfinder run time, is proportional to this.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_RECONFIG_NUM_LEAVES       = 11, ///< int32_t: Specifies the maximum number of leaves in the subtree chosen for optimization in each reconfiguration iteration.
                                                                             ///<          The default value is 8. The amount of time spent in reconfiguration, which usually dominates the pathfinder run time, is proportional to this.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SLICER_DISABLE_SLICING    = 20, ///< int32_t: If set to 1, disables slicing regardless of memory available.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SLICER_MEMORY_MODEL       = 21, ///< ::cutensornetMemoryModel_t: Memory model used to determine workspace size.
                                                                             ///<                           CUTENSORNET_MEMORY_MODEL_HEURISTIC uses a simple memory model that does not require external calls.
                                                                             ///<                           CUTENSORNET_MEMORY_MODEL_CUTENSOR (default) uses cuTENSOR to more precisely evaluate the amount of memory cuTENSOR will need for the contraction.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SLICER_MEMORY_FACTOR      = 22, ///< int32_t: The memory limit for the first slice-finding iteration as a percentage of the workspace size.
                                                                             ///<          Allowed range [1, 100]. The default is 80 when using CUTENSORNET_MEMORY_MODEL_CUTENSOR for the memory model and 100 when using CUTENSORNET_MEMORY_MODEL_HEURISTIC.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SLICER_MIN_SLICES         = 23, ///< int32_t: Minimum number of slices to produce at the first round of slicing. Default is 1.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SLICER_SLICE_FACTOR       = 24, ///< int32_t: Factor by which to increase the total number of slice at each slicing round. Default is 32, must be at least 2.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_HYPER_NUM_SAMPLES         = 30, ///< int32_t: Number of hyper-optimizer random samples. Default 0 (disabled).
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_HYPER_NUM_THREADS         = 31, ///< int32_t: Number of parallel hyper-optimizer threads. Default is number-of-cores / 2.
                                                                             ///<          When user-provided, it will be limited by the number of cores.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SIMPLIFICATION_DISABLE_DR = 40, ///< int32_t: If set to 1, disable deferred rank simplification.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SEED                      = 60,              ///< int32_t: Random seed to be used internally in order to reproduce same path.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_COST_FUNCTION_OBJECTIVE   = 61, ///< ::cutensornetOptimizerCost_t: the objective function to use for finding the optimal contraction path.
                                                                             ///<     CUTENSORNET_OPTIMIZER_COST_FLOPS (default) find a path that minimizes FLOP count.
                                                                             ///<     CUTENSORNET_OPTIMIZER_COST_TIME (experimental) find a path that minimizes the estimated time. The estimated time is computed based on arithmetic intensity.
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_CACHE_REUSE_NRUNS         = 62, ///< int32_t: Number of runs that utilize cache-reuse
    CUTENSORNET_CONTRACTION_OPTIMIZER_CONFIG_SMART_OPTION              = 63, ///< ::cutensornetSmartOption_t: enable or disable smart options.
} cutensornetContractionOptimizerConfigAttributes_t;

/**
 * This enum lists all attributes of a ::cutensornetContractionOptimizerInfo_t that are accessible.
 */
typedef enum
{
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_PATH                   = 0,  ///< ::cutensornetContractionPath_t: Pointer to the contraction path.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_NUM_SLICES             = 10, ///< int64_t: Total number of slices.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_NUM_SLICED_MODES       = 11, ///< int32_t: Total number of sliced modes. (get-only)
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_SLICED_MODE            = 12, ///< DEPRECATED int32_t* slicedModes: slicedModes[i] with i < \p numSlicedModes refers to the mode label of the i-th sliced mode (see \p modesIn w.r.t. cutensornetCreateNetworkDescriptor()). (get-only)
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_SLICED_EXTENT          = 13, ///< DEPRECATED int64_t* slicedExtents: slicedExtents[i] with i < \p numSlicedModes refers to the sliced extent of the i-th sliced mode (see \p extentsIn w.r.t. cutensornetCreateNetworkDescriptor()).  (get-only)  
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_SLICING_CONFIG         = 14, ///< cutensornetSlicingConfig_t*: Pointer to the slice configuration settings (number of slices, sliced modes, and sliced extents) used with the given path.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_SLICING_OVERHEAD       = 15, ///< double: Overhead due to slicing.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_PHASE1_FLOP_COUNT      = 20, ///< double: FLOP count for the given network after phase 1 of pathfinding (i.e., before slicing and reconfig).
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_FLOP_COUNT             = 21, ///< double: FLOP count for the given network after slicing.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_EFFECTIVE_FLOPS_EST    = 22, ///< double: Experimental. Returns the total flop-equivalent for one pass for all slices based on the cost function. When the cost function is flops, conventional flops are returned. When a time-based cost function is chosen,  effectiveFlopsEstimation = RuntimeEstimation * ops_peak.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_RUNTIME_EST            = 23, ///< double: Experimental. Returns the runtime estimation in [s] based on the time cost function objective for one pass for all slices.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_LARGEST_TENSOR         = 24, ///< double: The number of elements in the largest intermediate tensor.
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_INTERMEDIATE_MODES     = 30, ///< int32_t* intermediateModes: The modes in \f$[\text{intermediateModes}[\sum_{n=0}^{i-1}\text{numIntermediateModes}[n]], \text{intermediateModes}[\sum_{n=0}^{i}\text{numIntermediateModes}[n]])\f$ are the modes for the intermediate tensor \p i (so the total bytes to store \p intermediateModes is \f$\text{sizeof}(\text{int32_t})*\left(\sum_n \text{numIntermediateModes}[n]\right)\f$).
    CUTENSORNET_CONTRACTION_OPTIMIZER_INFO_NUM_INTERMEDIATE_MODES = 31, ///< int32_t* numIntermediateModes: numIntermediateModes[i] with i < \p numInputs - 1 is the number of modes for the intermediate tensor \p i (see \p numInputs w.r.t. cutensornetCreateNetworkDescriptor()).
} cutensornetContractionOptimizerInfoAttributes_t;


/**
 * DEPRECATED: This enum lists all attributes of a ::cutensornetContractionAutotunePreference_t that are accessible.
 */
typedef enum
{
    CUTENSORNET_CONTRACTION_AUTOTUNE_MAX_ITERATIONS,     ///< int32_t: Maximal number of auto-tune iterations for each pairwise contraction (default: 3).
    CUTENSORNET_CONTRACTION_AUTOTUNE_INTERMEDIATE_MODES, ///< int32_t: 0=OFF, 1=ON, 2=AUTO (default). If set to 1, cutensorContractionAutotune() auto-tunes the intermediate mode order by executing one slice of the network a few times in order to determine how to achieve the best performance with cuTENSOR. If set to 2, heuristically chooses whether to auto-tune the intermediate mode order based upon network characteristics.
} cutensornetContractionAutotunePreferenceAttributes_t;

/**
 * This enum lists all attributes of a ::cutensornetNetworkAutotunePreference_t that are accessible.
 */
typedef enum
{
    CUTENSORNET_NETWORK_AUTOTUNE_MAX_ITERATIONS,     ///< int32_t: Maximal number of auto-tune iterations for each pairwise contraction (default: 3).
    CUTENSORNET_NETWORK_AUTOTUNE_INTERMEDIATE_MODES, ///< int32_t: 0=OFF, 1=ON, 2=AUTO (default). If set to 1, cutensornetNetworkAutotuneContraction() auto-tunes the intermediate mode order by executing one slice of the network a few times in order to determine how to achieve the best performance with cuTENSOR. If set to 2, heuristically chooses whether to auto-tune the intermediate mode order based upon network characteristics.
} cutensornetNetworkAutotunePreferenceAttributes_t;


/**
 * \brief Opaque structure holding cuTensorNet's network descriptor.
 */
typedef void *cutensornetNetworkDescriptor_t;

/**
 * \brief DEPRECATED: Opaque structure holding cuTensorNet's contraction plan.
 */
typedef void *cutensornetContractionPlan_t;

/**
 * \brief Opaque structure holding cuTensorNet's library context.
 * \details This handle holds the cuTensorNet library context (device properties, system information, etc.).
 * The handle must be initialized and destroyed with cutensornetCreate() and cutensornetDestroy() functions,
 * respectively.
 */
typedef void *cutensornetHandle_t;

/**
 * \brief Opaque structure that holds information about the user-provided workspace.
 */
typedef void *cutensornetWorkspaceDescriptor_t;

/**
 * \brief Workspace preference enumeration.
 */
typedef enum
{
    CUTENSORNET_WORKSIZE_PREF_MIN = 0,         ///< At least one algorithm will be available for each contraction
    CUTENSORNET_WORKSIZE_PREF_RECOMMENDED = 1, ///< The most suitable algorithm will be available for each contraction
    CUTENSORNET_WORKSIZE_PREF_MAX = 2,         ///< All algorithms will be available for each contraction
} cutensornetWorksizePref_t;

/**
 * \brief Memory space enumeration for workspace allocation.
 */
typedef enum
{
    CUTENSORNET_MEMSPACE_DEVICE = 0, ///< Device memory space. Workspace memory buffers allocated on this memory space must be device accessible. Memory buffers are device accessible if allocated natively on device (`cudaMalloc`), or on managed memory (`cudaMallocManaged`), or registered on host (`cudaMallocHost`, `cudaHostAlloc`, or `cudaHostRegister`), or a system memory with Full CUDA Unified Memory support.
    CUTENSORNET_MEMSPACE_HOST = 1,   ///< Host memory space. Workspace memory buffers allocated on this memory space must be CPU accessible. Memory buffers are CPU accessible if allocated natively on host (e.g. `malloc`), or on managed memory (`cudaMallocManaged`), or registered on host (`cudaMallocHost` or `cudaHostAlloc`).
} cutensornetMemspace_t;

/**
 * \brief Type enumeration for workspace allocation.
 */
typedef enum
{
    CUTENSORNET_WORKSPACE_SCRATCH = 0, ///< Scratch workspace memory.
    CUTENSORNET_WORKSPACE_CACHE = 1    ///< Cache workspace memory, must be maintained valid and contents not modified until referencing operation iterations are completed.
} cutensornetWorkspaceKind_t;

/**
 * \brief Holds a list of input tensor IDs.
 */
typedef struct
{
    int32_t numTensors; ///< total number of tensors.
    int32_t *data;      ///< array of size \p numTensors holding tensor IDs.
} cutensornetTensorIDList_t;

/**
 * \brief A pair of int32_t values (typically referring to tensor IDs inside of the network).
 */
typedef struct __attribute__((aligned(4), packed))
{
    int32_t first;  ///< the first tensor
    int32_t second; ///< the second tensor
} cutensornetNodePair_t;

/**
 * \brief Holds information about the contraction path.
 *
 * The provided path is interchangeable with the path returned by <a href="https://numpy.org/doc/stable/reference/generated/numpy.einsum_path.html">numpy.einsum_path</a>.
 */
typedef struct
{
    int32_t numContractions;     ///< total number of tensor contractions.
    cutensornetNodePair_t *data; ///< array of size \p numContractions. The tensors corresponding to `data[i].first` and `data[i].second` will be contracted.
} cutensornetContractionPath_t;

/**
 * \brief A pair of int32_t and int64_t values holding the sliced Mode and intended extent size of mode.
 */
typedef struct
{
    int32_t slicedMode;   ///< Mode
    int64_t slicedExtent; ///< Extent of Mode
} cutensornetSliceInfoPair_t;

/**
 * \brief Holds information about slicing.
 */
typedef struct
{
    uint32_t numSlicedModes;          ///< total number of sliced modes.
    cutensornetSliceInfoPair_t *data; ///< array of size \p numSlicedModes.
} cutensornetSlicingConfig_t;

/**
 * \brief Opaque structure holding cuTensorNet's pathfinder config.
 */
typedef void *cutensornetContractionOptimizerConfig_t;

/**
 * \brief Opaque structure holding information about the optimized path and the slices (see ::cutensornetContractionOptimizerInfoAttributes_t).
 */
typedef void *cutensornetContractionOptimizerInfo_t;

/**
 * \brief DEPRECATED: Opaque structure information about the auto-tuning phase.
 */
typedef void *cutensornetContractionAutotunePreference_t;

/**
 * \brief Opaque structure information about the auto-tuning phase.
 */
typedef void *cutensornetNetworkAutotunePreference_t;

/**
 * \brief Opaque structure capturing a group of slices.
 */
typedef void *cutensornetSliceGroup_t;

/**
 * \brief Holds qualifiers/flags about the input tensors.
 */
typedef struct
{
    int32_t isConjugate;      ///< if set to 1, indicates the tensor should be complex-conjugated (applies only to complex data types).
    int32_t isConstant;       ///< if set to 1, indicates the tensor's data will not change across different network contractions.
    int32_t requiresGradient; ///< if set to 1, indicates the tensor required gradient computation.
} cutensornetTensorQualifiers_t;

/**
 * \brief Opaque structure holding cuTensorNet's tensor descriptor.
 */
typedef void *cutensornetTensorDescriptor_t;

/**
 * \brief Opaque structure holding cuTensorNet's tensor SVD configuration.
 */
typedef void *cutensornetTensorSVDConfig_t;

/**
 * This enum lists all attributes of a ::cutensornetTensorSVDConfig_t that can be modified.
 * \note When multiple truncation cutoffs (CUTENSORNET_TENSOR_SVD_CONFIG_ABS_CUTOFF, CUTENSORNET_TENSOR_SVD_CONFIG_REL_CUTOFF,
 * CUTENSORNET_TENSOR_SVD_CONFIG_DISCARDED_WEIGHT_CUTOFF) or maximal extent in input ::cutensornetTensorDescriptor_t are specified.
 * The runtime reduced extent will be determined as the lowest among all.
 */
typedef enum
{
    CUTENSORNET_TENSOR_SVD_CONFIG_ABS_CUTOFF,              ///< double: The absolute cutoff value for truncation and the default is 0.
    CUTENSORNET_TENSOR_SVD_CONFIG_REL_CUTOFF,              ///< double: The cutoff value for truncation (relative to the largest singular value) and the default is 0.
    CUTENSORNET_TENSOR_SVD_CONFIG_S_NORMALIZATION,         ///< cutensornetTensorSVDNormalization_t: How to normalize the singular values (after potential truncation). Default is no normalization.
    CUTENSORNET_TENSOR_SVD_CONFIG_S_PARTITION,             ///< cutensornetTensorSVDPartition_t: How to partition the singular values.
    CUTENSORNET_TENSOR_SVD_CONFIG_ALGO,                    ///< cutensornetTensorSVDAlgo_t: The SVD algorithm and the default is `gesvd`.
    CUTENSORNET_TENSOR_SVD_CONFIG_ALGO_PARAMS,             ///< Optional, the parameters specific to the SVD algorithm `cutensornetTensorSVDAlgo_t`. Current supports cutensornetGesvdjParams_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDJ and cutensornetGesvdrParams_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDR.
    CUTENSORNET_TENSOR_SVD_CONFIG_DISCARDED_WEIGHT_CUTOFF, ///< double: The maxiaml cumulative discarded weight (square sum of discarded singular values divided by square sum of all singular values) and the default is 0. This option is not allowed when CUTENSORNET_TENSOR_SVD_ALGO_GESVDR is used.
} cutensornetTensorSVDConfigAttributes_t;

/**
 * \brief This enum lists various algorithms for SVD.
 */
typedef enum
{
    CUTENSORNET_TENSOR_SVD_ALGO_GESVD,  ///< `cusolverDnGesvd` (default).
    CUTENSORNET_TENSOR_SVD_ALGO_GESVDJ, ///< `cusolverDnGesvdj`.
    CUTENSORNET_TENSOR_SVD_ALGO_GESVDP, ///< `cusolverDnXgesvdp`.
    CUTENSORNET_TENSOR_SVD_ALGO_GESVDR  ///< `cusolverDnXgesvdr`.
} cutensornetTensorSVDAlgo_t;

/**
 * \brief This struct holds parameters for the gesvdj setting.
 */
typedef struct
{
    double tol;        ///< The tolerance to control the accuracy of numerical singular values and the default (setting tol to 0.) adopts the default tolerance (machine precision) from cuSolver.
    int32_t maxSweeps; ///< The maximum number of sweeps for gesvdj and the default (setting maxSweep to 0) adopts the default gesvdj max sweep setting from cuSolver.
} cutensornetGesvdjParams_t;

/**
 * \brief This struct holds parameters for the gesvdr setting.
 */
typedef struct
{
    int64_t oversampling; ///< The size of oversampling and the default (setting oversampling to 0) is the lower of 4 times the truncated extent `k` and the difference between full rank and `k`.
    int64_t niters;       ///< Number of iteration of power method for `gesvdr` and the default (setting niters to 0) is 10.
} cutensornetGesvdrParams_t;

/**
 * \brief This enum lists various partition schemes for singular values.
 */
typedef enum
{
    CUTENSORNET_TENSOR_SVD_PARTITION_NONE,    ///< Return U, S, V as defined (default).
    CUTENSORNET_TENSOR_SVD_PARTITION_US,      ///< Absorb S onto U, i.e, US, nullptr, V.
    CUTENSORNET_TENSOR_SVD_PARTITION_SV,      ///< Absorb S onto V, i.e, U, nullptr, SV.
    CUTENSORNET_TENSOR_SVD_PARTITION_UV_EQUAL ///< Absorb S onto U and V equally, i.e, US^{1/2}, nullptr, S^{1/2}V.
} cutensornetTensorSVDPartition_t;

/**
 * \brief This enum lists various normalization methods for singular values.
 */
typedef enum
{
    CUTENSORNET_TENSOR_SVD_NORMALIZATION_NONE, ///< No normalization.
    CUTENSORNET_TENSOR_SVD_NORMALIZATION_L1,   ///< Normalize the truncated singular values such that the L1 norm becomes 1.
    CUTENSORNET_TENSOR_SVD_NORMALIZATION_L2,   ///< Normalize the truncated singular values such that the L2 norm becomes 1.
    CUTENSORNET_TENSOR_SVD_NORMALIZATION_LINF  ///< Normalize the truncated singular values such that the L-Infinty norm becomes 1.
} cutensornetTensorSVDNormalization_t;

/**
 * \brief Opaque structure holding cuTensorNet's tensor SVD information.
 */
typedef void *cutensornetTensorSVDInfo_t;

/**
 * \brief This enum lists all attributes of a ::cutensornetTensorSVDInfo_t.
 */
typedef enum
{
    CUTENSORNET_TENSOR_SVD_INFO_FULL_EXTENT,      ///< int64_t: The expected extent of the shared mode if no truncation takes place.
    CUTENSORNET_TENSOR_SVD_INFO_REDUCED_EXTENT,   ///< int64_t: The true extent of the shared mode found at runtime.
    CUTENSORNET_TENSOR_SVD_INFO_DISCARDED_WEIGHT, ///< double: The discarded weight of a singular value truncation. This information is not computed when fixed extent truncation is enabled with svd algorithm set to `CUTENSORNET_TENSOR_SVD_ALGO_GESVDR`.
    CUTENSORNET_TENSOR_SVD_INFO_ALGO,             ///< cutensornetTensorSVDAlgo_t: The SVD algorithm used for computation.
    CUTENSORNET_TENSOR_SVD_INFO_ALGO_STATUS,      /// The information specific to the SVD algorithm `cutensornetTensorSVDAlgo_t`. Current supports cutensornetGesvdjStatus_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDJ and cutensornetGesvdpStatus_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDP.
} cutensornetTensorSVDInfoAttributes_t;

/**
 * \brief This struct holds information for the gesvdj execution.
 */
typedef struct
{
    double residual; ///< The residual of gesvdj.
    int32_t sweeps;  ///< The number of executed sweeps of gesvdj.
} cutensornetGesvdjStatus_t;

/**
 * \brief This struct holds information for the gesvdp execution.
 */
typedef struct
{
    double errSigma; ///< The magnitude of the perturbation in gesvdp, showing the accuracy of SVD.
} cutensornetGesvdpStatus_t;

/**
 * \brief This enum lists algorithms for applying a gate tensor to two connected tensors.
 */
typedef enum
{
    CUTENSORNET_GATE_SPLIT_ALGO_DIRECT, ///< The direct algorithm with contraction and SVD for the gate split process.
    CUTENSORNET_GATE_SPLIT_ALGO_REDUCED ///< The reduced algorithm with additional QR for the gate split process.
} cutensornetGateSplitAlgo_t;

/**
 * \brief The device memory handler structure holds information about the user-provided, \em stream-ordered device memory pool (mempool).
 */
typedef struct
{
    /**
     * A pointer to the user-owned mempool/context object.
     */
    void *ctx;
    /**
     * A function pointer to the user-provided routine for allocating device memory of \p size on \p stream.
     *
     * The allocated memory should be made accessible to the current device (or more
     * precisely, to the current CUDA context bound to the library handle).
     *
     * This interface supports any stream-ordered memory allocator \p ctx. Upon success,
     * the allocated memory can be immediately used on the given stream by any
     * operations enqueued/ordered on the same stream after this call.
     *
     * It is the caller’s responsibility to ensure a proper stream order is established.
     *
     * The allocated memory should be at least 256-byte aligned.
     *
     * \param[in] ctx A pointer to the user-owned mempool object.
     * \param[out] ptr On success, a pointer to the allocated buffer.
     * \param[in] size The amount of memory in bytes to be allocated.
     * \param[in] stream The CUDA stream on which the memory is allocated (and the stream order is established).
     * \return Error status of the invocation. Return 0 on success and any nonzero integer otherwise. This function must not throw if it is a C++ function.
     *
     */
    int (*device_alloc)(void *ctx, void **ptr, size_t size, cudaStream_t stream);
    /**
     * A function pointer to the user-provided routine for de-allocating device memory of \p size on \p stream.
     *
     * This interface supports any stream-ordered memory allocator. Upon success, any
     * subsequent accesses (of the memory pointed to by the pointer \p ptr) ordered after
     * this call are undefined behaviors.
     *
     * It is the caller’s responsibility to ensure a proper stream order is established.
     *
     * If the arguments \p ctx and \p size are not the same as those passed to \p device_alloc to
     * allocate the memory pointed to by \p ptr, the behavior is undefined.
     *
     * The argument \p stream need not be identical to the one used for allocating \p ptr, as
     * long as the stream order is correctly established. The behavior is undefined if
     * this assumption is not held.
     *
     * \param[in] ctx A pointer to the user-owned mempool object.
     * \param[in] ptr The pointer to the allocated buffer.
     * \param[in] size The size of the allocated memory.
     * \param[in] stream The CUDA stream on which the memory is de-allocated (and the stream ordering is established).
     * \return Error status of the invocation. Return 0 on success and any nonzero integer otherwise. This function must not throw if it is a C++ function.
     */
    int (*device_free)(void *ctx, void *ptr, size_t size, cudaStream_t stream);
    /**
     * The name of the provided mempool.
     */
    char name[CUTENSORNET_ALLOCATOR_NAME_LEN];
} cutensornetDeviceMemHandler_t;

/**
 * \brief Opaque structure holding the tensor network state.
 */
typedef void *cutensornetState_t;

/**
 * \brief This enum captures tensor network state purity.
 */
typedef enum
{
    CUTENSORNET_STATE_PURITY_PURE, ///< Pure tensor network state (belongs to the primary tensor space)
//  CUTENSORNET_STATE_PURITY_MIXED ///< Mixed tensor network state (belongs to the direct product of the primary tensor space with its dual space)
} cutensornetStatePurity_t;

/**
 * \brief Opaque structure holding the tensor network state amplitudes (a slice of the full output state tensor).
 */
typedef void *cutensornetStateAccessor_t;

/**
 * \brief This enum lists attributes associated with computation of tensor network state amplitudes.
 */
typedef enum
{
    CUTENSORNET_ACCESSOR_OPT_NUM_HYPER_SAMPLES = 0,    ///< DEPRECATED int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_ACCESSOR_CONFIG_NUM_HYPER_SAMPLES = 1, ///< int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_ACCESSOR_INFO_FLOPS = 64               ///< double: Total Flop count estimate associated with computing the specified set of tensor network state amplitudes.
} cutensornetAccessorAttributes_t;

/**
 * \brief Opaque structure holding the tensor network state expectation value.
 */
typedef void *cutensornetStateExpectation_t;

/**
 * \brief This enum lists attributes associated with computation of a tensor network state expectation value.
 */
typedef enum
{
    CUTENSORNET_EXPECTATION_OPT_NUM_HYPER_SAMPLES = 0,    ///< DEPRECATED int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_EXPECTATION_CONFIG_NUM_HYPER_SAMPLES = 1, ///< int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_EXPECTATION_INFO_FLOPS = 64               ///< double: Total Flop count estimate associated with computing the tensor network state expectation value.
} cutensornetExpectationAttributes_t;

/**
 * \brief Opaque structure holding the tensor network state marginal (aka reduced density matrix).
 */
typedef void *cutensornetStateMarginal_t;

/**
 * \brief This enum lists attributes associated with computation of a tensor network state marginal tensor.
 */
typedef enum
{
    CUTENSORNET_MARGINAL_OPT_NUM_HYPER_SAMPLES = 0,    ///< DEPRECATED int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_MARGINAL_CONFIG_NUM_HYPER_SAMPLES = 1, ///< int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_MARGINAL_INFO_FLOPS = 64               ///< double: Total Flop count estimate associated with computing the tensor network state marginal tensor.
} cutensornetMarginalAttributes_t;

/**
 * \brief Opaque structure holding the tensor network state sampler.
 */
typedef void *cutensornetStateSampler_t;

/**
 * \brief Opaque structure holding the tensor network state projection MPS.
 */
typedef void *cutensornetStateProjectionMPS_t;

/**
 * \brief This enum lists attributes associated with tensor network state sampling.
 */
typedef enum
{
    CUTENSORNET_SAMPLER_OPT_NUM_HYPER_SAMPLES = 0,    ///< DEPRECATED int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_SAMPLER_CONFIG_NUM_HYPER_SAMPLES = 1, ///< int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_SAMPLER_CONFIG_DETERMINISTIC = 2,     ///< int32_t: A positive random seed will ensure deterministic sampling results across multiple application runs.
    CUTENSORNET_SAMPLER_INFO_FLOPS = 64               ///< double: Total Flop count estimate associated with generating a single sample from the tensor network state.
} cutensornetSamplerAttributes_t;

/**
 * \brief This enum lists supported boundary conditions for supported tensor network factorizations.
 */
typedef enum
{
    CUTENSORNET_BOUNDARY_CONDITION_OPEN,     ///< Open boundary condition.
//  CUTENSORNET_BOUNDARY_CONDITION_PERIODIC  ///< Periodic boundary condition.
} cutensornetBoundaryCondition_t;

/**
 * \brief This enum lists all attributes associated with computation of a ::cutensornetState_t.
 */
typedef enum
{
    // Deprecated attribute names
    CUTENSORNET_STATE_MPS_CANONICAL_CENTER = 0,                   ///< DEPRECATED int32_t: The site where canonical center of the target MPS should be placed at. If less than 0 (default -1), no canonical center will be enforced.
    CUTENSORNET_STATE_MPS_SVD_CONFIG_ABS_CUTOFF = 1,              ///< DEPRECATED double: The absolute cutoff value for SVD truncation (default is 0).
    CUTENSORNET_STATE_MPS_SVD_CONFIG_REL_CUTOFF = 2,              ///< DEPRECATED double: The cutoff value for SVD truncation relative to the largest singular value (default is 0).
    CUTENSORNET_STATE_MPS_SVD_CONFIG_S_NORMALIZATION = 3,         ///< DEPRECATED cutensornetTensorSVDNormalization_t: How to normalize singular values after potential truncation. Default is no normalization.
    CUTENSORNET_STATE_MPS_SVD_CONFIG_ALGO = 4,                    ///< DEPRECATED cutensornetTensorSVDAlgo_t: The SVD algorithm (default is `gesvd`).
    CUTENSORNET_STATE_MPS_SVD_CONFIG_ALGO_PARAMS = 5,             /// DEPRECATED Optional, the parameters specific to the SVD algorithm `cutensornetTensorSVDAlgo_t`, currently supporting cutensornetGesvdjParams_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDJ and cutensornetGesvdrParams_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDR.
    CUTENSORNET_STATE_MPS_SVD_CONFIG_DISCARDED_WEIGHT_CUTOFF = 6, ///< DEPRECATED double: The maximal cumulative discarded weight (square sum of discarded singular values divided by the square sum of all singular values), defaults to 0. This option is not allowed when CUTENSORNET_TENSOR_SVD_ALGO_GESVDR is chosen.
    CUTENSORNET_STATE_NUM_HYPER_SAMPLES = 7,                      ///< DEPRECATED int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    // New attribute names
    CUTENSORNET_STATE_CONFIG_MPS_CANONICAL_CENTER = 16,            ///< int32_t: The site where canonical center of the target MPS should be placed at. If less than 0 (default -1), no canonical center will be enforced.
    CUTENSORNET_STATE_CONFIG_MPS_SVD_ABS_CUTOFF = 17,              ///< double: The absolute cutoff value for SVD truncation (default is 0).
    CUTENSORNET_STATE_CONFIG_MPS_SVD_REL_CUTOFF = 18,              ///< double: The cutoff value for SVD truncation relative to the largest singular value (default is 0).
    CUTENSORNET_STATE_CONFIG_MPS_SVD_S_NORMALIZATION = 19,         ///< cutensornetTensorSVDNormalization_t: How to normalize singular values after potential truncation. Default is no normalization.
    CUTENSORNET_STATE_CONFIG_MPS_SVD_ALGO = 20,                    ///< cutensornetTensorSVDAlgo_t: The SVD algorithm (default is `gesvd`).
    CUTENSORNET_STATE_CONFIG_MPS_SVD_ALGO_PARAMS = 21,             ///< Optional, the parameters specific to the SVD algorithm `cutensornetTensorSVDAlgo_t`, currently supporting cutensornetGesvdjParams_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDJ and cutensornetGesvdrParams_t for CUTENSORNET_TENSOR_SVD_ALGO_GESVDR.
    CUTENSORNET_STATE_CONFIG_MPS_SVD_DISCARDED_WEIGHT_CUTOFF = 22, ///< double: The maximal cumulative discarded weight (square sum of discarded singular values divided by the square sum of all singular values), defaults to 0. This option is not allowed when CUTENSORNET_TENSOR_SVD_ALGO_GESVDR is chosen.
    CUTENSORNET_STATE_CONFIG_MPS_MPO_APPLICATION = 23,             ///< Optional, the computational setting for all contraction and decomposition operations in MPS-MPO computation (swap included). Default is set to `CUTENSORNET_STATE_MPO_APPLICATION_INEXACT`.
    CUTENSORNET_STATE_CONFIG_MPS_GAUGE_OPTION = 24,                ///< cutensornetStateMPSGaugeOption_t: The MPS gauge option (default is `CUTENSORNET_STATE_MPS_GAUGE_FREE`).
    CUTENSORNET_STATE_CONFIG_NUM_HYPER_SAMPLES = 30,               ///< int32_t: Number of hyper-samples used by the tensor network contraction path finder.
    CUTENSORNET_STATE_INFO_FLOPS = 64                              ///< double: Total Flop count estimate associated with explicit computation of the tensor network state.
} cutensornetStateAttributes_t;


/**
 * \brief This enum lists all options for contraction and decomposition operations in MPS-MPO computation.
 */
typedef enum
{
    CUTENSORNET_STATE_MPO_APPLICATION_INEXACT,   ///< All swap and decomposition operations in MPS-MPO multiplication will follow the same constraints set by the underlying SVD configurations and target extents set by cutensornetStateFinalizeMPS().
    CUTENSORNET_STATE_MPO_APPLICATION_EXACT,     ///< All swap and decomposition operations in MPS-MPO multiplication will be performed in an exact manner with all constraints from underlying SVD configuration and target extents specification dismissed. Note as of current version, this option shall only be used when exact MPS computation is required.
} cutensornetStateMPOApplication_t;

/**
 * \brief Opaque structure holding the tensor network operator object.
 */
typedef void *cutensornetNetworkOperator_t;

/**
 * \typedef cutensornetLoggerCallback_t
 * \brief A callback function pointer type for logging APIs. Use cutensornetLoggerSetCallback() to set the callback function.
 * \param[in] logLevel the log level
 * \param[in] functionName the name of the API that logged this message
 * \param[in] message the log message
 */
typedef void (*cutensornetLoggerCallback_t)(
    int32_t logLevel,
    const char *functionName,
    const char *message);

/**
 * \typedef cutensornetLoggerCallbackData_t
 * \brief A callback function pointer type for logging APIs. Use cutensornetLoggerSetCallbackData() to set the callback function and user data.
 * \param[in] logLevel the log level
 * \param[in] functionName the name of the API that logged this message
 * \param[in] message the log message
 * \param[in] userData user's data to be used by the callback
 */
typedef void (*cutensornetLoggerCallbackData_t)(
    int32_t logLevel,
    const char *functionName,
    const char *message,
    void *userData);

/**
 * \brief This enum lists various gauge options on MPS.
 */
typedef enum
{
    CUTENSORNET_STATE_MPS_GAUGE_FREE = 0,      ///< No gauge is enabled
    CUTENSORNET_STATE_MPS_GAUGE_SIMPLE  = 1,   ///< Gauge is enabled to improve accuracy using simple update algorithm.
} cutensornetStateMPSGaugeOption_t;

/**
 * \brief Specification of domain of tensor environment for a ::cutensornetStateProjectionMPS_t through the
 * site indices to the left and right of it.
 */
 typedef struct {
    /**
    Site index to the left of environment (allowed range -1 to number of qudits - 1).
    */
    int32_t lowerBound;
    /** 
    Site index to the right of environment (allowed range +1 to number of qudits + 1).
    */
    int32_t upperBound;
} cutensornetMPSEnvBounds_t;

/**
 * \brief This enum lists orthonormalization behaviour for ProjectionMPS.
 */
typedef enum
{
    CUTENSORNET_STATE_PROJECTION_MPS_ORTHO_AUTO = 0,   ///< Orthogonality center of MPS is moved to region which is being manipulated.
} cutensornetStateProjectionMPSOrthoOption_t;

/**
 * \brief This enum lists all attributes associated with computation of a
 * ::cutensornetStateProjectionMPS_t.
 */
typedef enum
{
    CUTENSORNET_STATE_PROJECTION_MPS_CONFIG_ORTHO_OPTION = 0,               ///< cutensornetStateProjectionMPSOrthoOption_t: Orthogonalization behaviour upon tensor extraction.
    CUTENSORNET_STATE_PROJECTION_MPS_CONFIG_NUM_HYPER_SAMPLES = 10,         ///< int32_t: Number of hyper-samples used by the tensor network contraction path
} cutensornetStateProjectionMPSAttributes_t;

