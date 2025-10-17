#!/bin/bash

# Copyright (c) 2021-2023, NVIDIA CORPORATION & AFFILIATES
# SPDX-License-Identifier: BSD-3-Clause

# This script will build and activate the cuTensorNet MPI interface.
# It requires a GNU C compiler (gcc).
#
# Please check/set the following environment variables:
#  - $CUDA_PATH = Path to your CUDA installation directory.
#  - $MPI_PATH = Path to your MPI library installation directory.
#                If your MPI library is installed in system
#                directories as opposed to its own (root) directory,
#                ${MPI_PATH}/include is expected to contain the mpi.h header.
#                ${MPI_PATH}/lib64 or ${MPI_PATH}/lib is expected to contain libmpi.so.
#
# Run (inside this directory): source ./activate_mpi.sh

# Libraries to be linked with your application (dynamically or statically):
#  libcutensornet, libcutensor, libcusolver, libcublasLt, libmpi, libcudart, libdl

# This script exports an environment variable $CUTENSORNET_COMM_LIB (below).
# This environment variable is mandatory for enabling distributed execution.
# You should add it to your ~/.bashrc file.

if [ -z "${CUDA_PATH}" ]
then
    echo "Environment variable CUDA_PATH is not set. Plese set it to point to the CUDA root directory!"
    return
fi

if [ -z "${MPI_PATH}" ]
then
    echo "Environment variable MPI_PATH is not set. Plese set it to point to the MPI root directory!"
    echo "Note that MPI_PATH/include is expected to contain the mpi.h header."
    return
fi

gcc -shared -std=c99 -fPIC \
    -I${CUDA_PATH}/include -I../include -I${MPI_PATH}/include \
    cutensornet_distributed_interface_mpi.c \
    -L${MPI_PATH}/lib64 -L${MPI_PATH}/lib -lmpi \
    -o libcutensornet_distributed_interface_mpi.so
export CUTENSORNET_COMM_LIB=${PWD}/libcutensornet_distributed_interface_mpi.so
