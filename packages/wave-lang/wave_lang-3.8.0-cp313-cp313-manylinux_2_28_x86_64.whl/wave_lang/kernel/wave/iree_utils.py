# Copyright 2025 The IREE Authors
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

import torch

from wave_lang.runtime.launch import Launchable
from wave_lang.support.conversions import TORCH_DTYPE_TO_IREE_TYPE_ASM
from .utils.run_utils import get_benchmark_flags, print_bench_result
from .profiling import benchmark_module
from .utils.compile_utils import compile_to_vmfb
import iree.runtime as rt


def get_chain_mmt_asm(
    query_type: str, key_type: str, value_type: str, output_type: str
) -> tuple[str, str]:
    B, M, K1, input_dtype = query_type.split("x")
    B, K2, K1, input_dtype = key_type.split("x")
    B, N, K2, input_dtype = value_type.split("x")
    B, N, M, output_dtype = output_type.split("x")
    intermediate_output_type = f"{B}x{K2}x{M}x{output_dtype}"
    intermediate_cast_type = f"{B}x{K2}x{M}x{input_dtype}"
    transposed_query_type = f"{B}x{K1}x{M}x{input_dtype}"
    transposed_value_type = f"{B}x{K2}x{N}x{input_dtype}"
    transposed_cast_type = f"{B}x{M}x{K2}x{input_dtype}"
    transposed_output_type = f"{B}x{M}x{N}x{output_dtype}"
    return (
        f"""
    func.func @chain_mmt(%query: tensor<{query_type}>, %key: tensor<{key_type}>, %value: tensor<{value_type}>) -> tensor<{output_type}> {{
      %c0 = arith.constant 0.0 : f32
      %init = tensor.empty() : tensor<{intermediate_output_type}>
      %inital_result = linalg.fill ins(%c0 : f32) outs(%init : tensor<{intermediate_output_type}>) -> tensor<{intermediate_output_type}>
      %init_transpose_query = tensor.empty() : tensor<{transposed_query_type}>
      %transpose_query = linalg.transpose ins(%query: tensor<{query_type}>) outs(%init_transpose_query: tensor<{transposed_query_type}>) permutation=[0, 2, 1]
      %result = linalg.batch_matmul ins(%key, %transpose_query : tensor<{key_type}>, tensor<{transposed_query_type}>)
                outs(%inital_result : tensor<{intermediate_output_type}>) -> tensor<{intermediate_output_type}>
      %trunc = arith.truncf %result : tensor<{intermediate_output_type}> to tensor<{intermediate_cast_type}>
      %init2 = tensor.empty() : tensor<{transposed_cast_type}>
      %transpose = linalg.transpose ins(%trunc: tensor<{intermediate_cast_type}>) outs(%init2: tensor<{transposed_cast_type}>) permutation=[0, 2, 1]
      %init3 = tensor.empty() : tensor<{transposed_output_type}>
      %inital_result3 = linalg.fill ins(%c0 : f32) outs(%init3 : tensor<{transposed_output_type}>) -> tensor<{transposed_output_type}>
      %init_transpose_value = tensor.empty() : tensor<{transposed_value_type}>
      %transpose_value = linalg.transpose ins(%value: tensor<{value_type}>) outs(%init_transpose_value: tensor<{transposed_value_type}>) permutation=[0, 2, 1]
      %result2 = linalg.batch_matmul ins(%transpose, %transpose_value: tensor<{transposed_cast_type}>, tensor<{transposed_value_type}>)
                outs(%inital_result3 : tensor<{transposed_output_type}>) -> tensor<{transposed_output_type}>
      %init4 = tensor.empty() : tensor<{output_type}>
      %transpose2 = linalg.transpose ins(%result2: tensor<{transposed_output_type}>) outs(%init4: tensor<{output_type}>) permutation=[0, 2, 1]
      return %transpose2 : tensor<{output_type}>
    }}""",
        "chain_mmt",
    )


def get_chain_mmt_f8_asm(
    query_type: str, key_type: str, value_type: str, output_type: str
) -> tuple[str, str]:
    B, M, K1, input_dtype = query_type.split("x")
    B, K2, K1, input_dtype = key_type.split("x")
    B, N, K2, input_dtype = value_type.split("x")
    B, N, M, output_dtype = output_type.split("x")
    f8_dtype = "f8E4M3FNUZ"
    intermediate_output_type = f"{B}x{K2}x{M}x{output_dtype}"
    intermediate_cast_type = f"{B}x{K2}x{M}x{f8_dtype}"
    transposed_query_type = f"{B}x{K1}x{M}x{f8_dtype}"
    transposed_value_type = f"{B}x{K2}x{N}x{f8_dtype}"
    transposed_cast_type = f"{B}x{M}x{K2}x{f8_dtype}"
    transposed_output_type = f"{B}x{M}x{N}x{output_dtype}"
    query_f8_type = "x".join([B, M, K1, f8_dtype])
    key_f8_type = "x".join([B, K2, K1, f8_dtype])
    value_f8_type = "x".join([B, N, K2, f8_dtype])
    return (
        f"""
    func.func @chain_mmt_f8(%query: tensor<{query_type}>, %key: tensor<{key_type}>, %value: tensor<{value_type}>) -> tensor<{output_type}> {{
      %c0 = arith.constant 0.0 : f32
      %init = tensor.empty() : tensor<{intermediate_output_type}>
      %query_f8 = arith.truncf %query : tensor<{query_type}> to tensor<{query_f8_type}>
      %key_f8 = arith.truncf %key : tensor<{key_type}> to tensor<{key_f8_type}>
      %inital_result = linalg.fill ins(%c0 : f32) outs(%init : tensor<{intermediate_output_type}>) -> tensor<{intermediate_output_type}>
      %init_transpose_query = tensor.empty() : tensor<{transposed_query_type}>
      %transpose_query = linalg.transpose ins(%query_f8: tensor<{query_f8_type}>) outs(%init_transpose_query: tensor<{transposed_query_type}>) permutation=[0, 2, 1]
      %result = linalg.batch_matmul ins(%key_f8, %transpose_query : tensor<{key_f8_type}>, tensor<{transposed_query_type}>)
                outs(%inital_result : tensor<{intermediate_output_type}>) -> tensor<{intermediate_output_type}>
      %trunc = arith.truncf %result : tensor<{intermediate_output_type}> to tensor<{intermediate_cast_type}>
      %init2 = tensor.empty() : tensor<{transposed_cast_type}>
      %transpose = linalg.transpose ins(%trunc: tensor<{intermediate_cast_type}>) outs(%init2: tensor<{transposed_cast_type}>) permutation=[0, 2, 1]
      %init3 = tensor.empty() : tensor<{transposed_output_type}>
      %inital_result3 = linalg.fill ins(%c0 : f32) outs(%init3 : tensor<{transposed_output_type}>) -> tensor<{transposed_output_type}>
      %value_f8 = arith.truncf %value : tensor<{value_type}> to tensor<{value_f8_type}>
      %init_transpose_value = tensor.empty() : tensor<{transposed_value_type}>
      %transpose_value = linalg.transpose ins(%value_f8: tensor<{value_f8_type}>) outs(%init_transpose_value: tensor<{transposed_value_type}>) permutation=[0, 2, 1]
      %result2 = linalg.batch_matmul ins(%transpose, %transpose_value: tensor<{transposed_cast_type}>, tensor<{transposed_value_type}>)
                outs(%inital_result3 : tensor<{transposed_output_type}>) -> tensor<{transposed_output_type}>
      %init4 = tensor.empty() : tensor<{output_type}>
      %transpose2 = linalg.transpose ins(%result2: tensor<{transposed_output_type}>) outs(%init4: tensor<{output_type}>) permutation=[0, 2, 1]
      return %transpose2 : tensor<{output_type}>
    }}""",
        "chain_mmt_f8",
    )


def get_mmt_asm(
    lhs_type: str,
    rhs_type: str,
    acc_type: str,
    batch: bool = False,
    cast_fp8: bool = False,
) -> tuple[str, str]:
    acc_dtype = acc_type.split("x")[-1]
    *rhs_shape, rhs_dtype = rhs_type.split("x")
    rhs_type_t = "x".join(rhs_shape[:-2] + [rhs_shape[-1], rhs_shape[-2], rhs_dtype])
    operator = "batch_matmul" if batch else "matmul"
    func_name = "bmmt" if batch else "mmt"
    func_name = func_name + "_f8" if cast_fp8 else func_name
    perm = [0, 2, 1] if batch else [1, 0]
    if not cast_fp8:
        matmul_function = f"""
        func.func @{func_name}(%lhs: tensor<{lhs_type}>, %rhs: tensor<{rhs_type}>) -> tensor<{acc_type}> {{
          %c0 = arith.constant {"0.0" if acc_dtype.startswith("f") else "0"} : {acc_dtype}
          %init = tensor.empty() : tensor<{acc_type}>
          %inital_result = linalg.fill ins(%c0 : {acc_dtype}) outs(%init : tensor<{acc_type}>) -> tensor<{acc_type}>
          %rhs_transpose_init = tensor.empty() : tensor<{rhs_type_t}>
          %rhs_transpose = linalg.transpose ins(%rhs: tensor<{rhs_type}>) outs(%rhs_transpose_init: tensor<{rhs_type_t}>) permutation={perm}
          %result = linalg.{operator} ins(%lhs, %rhs_transpose: tensor<{lhs_type}>, tensor<{rhs_type_t}>)
                     outs(%inital_result: tensor<{acc_type}>) -> tensor<{acc_type}>
          return %result : tensor<{acc_type}>
        }}"""
    else:
        dtype = lhs_type.split("x")[-1]
        f8_dtype = "f8E4M3FNUZ"
        lhs_type_f8 = lhs_type.replace(dtype, f8_dtype)
        dtype = rhs_type.split("x")[-1]
        rhs_type_f8 = rhs_type.replace(dtype, f8_dtype)
        rhs_type_f8_t = rhs_type_t.replace(dtype, f8_dtype)
        matmul_function = f"""
        func.func @{func_name}(%lhs: tensor<{lhs_type}>, %rhs: tensor<{rhs_type}>) -> tensor<{acc_type}> {{
          %c0 = arith.constant 0.0 : {acc_dtype}
          %init = tensor.empty() : tensor<{acc_type}>
          %inital_result = linalg.fill ins(%c0 : {acc_dtype}) outs(%init : tensor<{acc_type}>) -> tensor<{acc_type}>
          %lhs_f8 = arith.truncf %lhs : tensor<{lhs_type}> to tensor<{lhs_type_f8}>
          %rhs_f8 = arith.truncf %rhs : tensor<{rhs_type}> to tensor<{rhs_type_f8}>
          %rhs_transpose_init = tensor.empty() : tensor<{rhs_type_f8_t}>
          %rhs_transpose = linalg.transpose ins(%rhs_f8: tensor<{rhs_type_f8}>) outs(%rhs_transpose_init: tensor<{rhs_type_f8_t}>) permutation={perm}
          %result = linalg.{operator} ins(%lhs_f8, %rhs_transpose: tensor<{lhs_type_f8}>, tensor<{rhs_type_f8_t}>)
                     outs(%inital_result: tensor<{acc_type}>) -> tensor<{acc_type}>
          return %result : tensor<{acc_type}>
        }}"""
    return matmul_function, func_name


def get_conv_asm(
    conv_type: str, lhs_type: str, rhs_type: str, res_type: str, stride: int
) -> tuple[str, str]:
    res_dtype = res_type.split("x")[-1]
    return (
        f"""
    func.func @conv_{conv_type}(%lhs: tensor<{lhs_type}>, %rhs: tensor<{rhs_type}>) -> tensor<{res_type}> {{
      %c0 = arith.constant 0.0 : {res_dtype}
      %init = tensor.empty() : tensor<{res_type}>
      %inital_result = linalg.fill ins(%c0 : {res_dtype}) outs(%init : tensor<{res_type}>) -> tensor<{res_type}>
      %result = linalg.conv_{conv_type}
                {{dilations = dense<1> : tensor<2xi64>, strides = dense<{stride}> : tensor<2xi64>}}
                ins(%lhs, %rhs : tensor<{lhs_type}>, tensor<{rhs_type}>)
                outs(%inital_result : tensor<{res_type}>) -> tensor<{res_type}>
      return %result : tensor<{res_type}>
    }}""",
        f"conv_{conv_type}",
    )


def dtype_str(dtype: torch.dtype) -> str:
    dtype_str = TORCH_DTYPE_TO_IREE_TYPE_ASM[dtype]
    if dtype_str is None:
        raise ValueError(f"Unsupported dtype: {dtype}")
    return dtype_str


def get_type_str(shape: tuple[int], dtype: torch.dtype) -> str:
    return "x".join([str(x) for x in shape] + [dtype_str(dtype)])


def generate_iree_ref(
    kernel_type: str,
    kernel_inputs: list[torch.Tensor],
    kernel_outputs: list[torch.Tensor],
    options: "WaveCompileOptions",
):
    """
    Generate a reference output for the given kernel type and arguments.
    """

    asm = None
    conv_str = "conv_"
    if kernel_type == "mmt" or kernel_type == "mmt_f8":
        lhs_type = get_type_str(kernel_inputs[0].shape, kernel_inputs[0].dtype)
        rhs_type = get_type_str(kernel_inputs[1].shape, kernel_inputs[1].dtype)
        acc_type = get_type_str(kernel_outputs[0].shape, kernel_outputs[0].dtype)
        asm, func_name = get_mmt_asm(
            lhs_type,
            rhs_type,
            acc_type,
            batch=False,
            cast_fp8=kernel_type == "mmt_f8",
        )
    elif kernel_type == "bmmt":
        lhs_type = get_type_str(kernel_inputs[0].shape, kernel_inputs[0].dtype)
        rhs_type = get_type_str(kernel_inputs[1].shape, kernel_inputs[1].dtype)
        acc_type = get_type_str(kernel_outputs[0].shape, kernel_outputs[0].dtype)
        asm, func_name = get_mmt_asm(lhs_type, rhs_type, acc_type, batch=True)
    elif kernel_type == "chain_mmt":
        query_type = get_type_str(kernel_inputs[0].shape, kernel_inputs[0].dtype)
        key_type = get_type_str(kernel_inputs[1].shape, kernel_inputs[1].dtype)
        value_type = get_type_str(kernel_inputs[2].shape, kernel_inputs[2].dtype)
        output_type = get_type_str(kernel_outputs[0].shape, kernel_outputs[0].dtype)
        asm, func_name = get_chain_mmt_asm(
            query_type, key_type, value_type, output_type
        )
    elif kernel_type == "chain_mmt_f8":
        query_type = get_type_str(kernel_inputs[0].shape, kernel_inputs[0].dtype)
        key_type = get_type_str(kernel_inputs[1].shape, kernel_inputs[1].dtype)
        value_type = get_type_str(kernel_inputs[2].shape, kernel_inputs[2].dtype)
        output_type = get_type_str(kernel_outputs[0].shape, kernel_outputs[0].dtype)
        asm, func_name = get_chain_mmt_f8_asm(
            query_type, key_type, value_type, output_type
        )
    elif kernel_type.startswith(conv_str):
        lhs_type = get_type_str(kernel_inputs[0].shape, kernel_inputs[0].dtype)
        rhs_type = get_type_str(kernel_inputs[1].shape, kernel_inputs[1].dtype)
        acc_type = get_type_str(kernel_outputs[0].shape, kernel_outputs[0].dtype)
        conv_type = kernel_type[len(conv_str) :]
        asm, func_name = get_conv_asm(
            conv_type, lhs_type, rhs_type, acc_type, int(kwargs["stride"])
        )
    else:
        raise ValueError(f"Unknown kernel type: {kernel_type}")

    vmfb = compile_to_vmfb(asm, options)

    def loader(device):
        vm_instance = device.vm_instance
        return rt.VmModule.copy_buffer(vm_instance, vmfb)

    launchable = Launchable.from_vm_module(loader, entry_point=func_name)
    res = launchable(*kernel_inputs, outputs=kernel_outputs)
    if len(kernel_outputs) == 1:
        kernel_outputs[0][:] = res
    else:
        for r, k in zip(res, kernel_outputs):
            k[:] = r

    if options.run_bench:
        benchmark_flags = get_benchmark_flags(options)

        benchmark_results = benchmark_module(
            options,
            kernel_inputs,
            [],  # kernel_outputs,
            vmfb,
            func_name,
            **benchmark_flags,
        )
        print_bench_result(benchmark_results, options.benchmark_results_file)
