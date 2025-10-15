# Copyright 2025 The IREE Authors
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

import tempfile
import json
from pathlib import Path
import linecache
import os
import subprocess
import sys
import math
from typing import Any, Sequence
import importlib

from wave_lang.support.ir_imports import (
    Attribute,
    BlockArgument,
    FunctionType,
    InsertionPoint,
    IntegerType,
    MemRefType,
    Module,
    Operation,
    TypeAttr,
    WalkResult,
    gpu_d,
    llvm_d,
    memref_d,
    stream_d,
)


def _find_single_nested(name: str, parent: Operation) -> Operation:
    """Find a single operation with the specified name in a single-block parent operation.

    Raises a RuntimeError if there is no such operation or if there are multiple.
    Raises a ValueError if the parent operation is not a single-block one.
    """

    if len(parent.regions) != 1 or len(parent.regions[0].blocks) != 1:
        raise ValueError("Expected a single-block operation.")
    captured = None
    for op in parent.regions[0].blocks[0].operations:
        # Dynamic typing is hard: must to op.operation.name in case some specific class has .name that has a different meaning.
        if op.operation.name == name:
            if captured:
                raise RuntimeError(f"More than one '{name}' operation found.")
            captured = op
    if not captured:
        raise RuntimeError(f"No {name} operation found.")
    return captured


def _get_numeric_memory_space(memory_space: Attribute) -> int | None:
    """Return the numeric address space used in LLVM pointers that matches the given GPU dialect address space."""

    # TODO: expose construction of these attributes in upstream bindings.
    if memory_space == Attribute.parse("#gpu.address_space<workgroup>"):
        return int(gpu_d.AddressSpace.Workgroup)
    if memory_space == Attribute.parse("#gpu.address_space<global>"):
        return int(gpu_d.AddressSpace.Global)
    if memory_space == Attribute.parse("#gpu.address_space<private>"):
        return int(gpu_d.AddressSpace.Private)
    return None


def _deiree(module: Module) -> str:
    """Return a copy of the module without IREE-specific operations, suitable for MLIR processing."""
    # Uglily clone the module by printing and parsing back.
    module = Module.parse(module.operation.get_asm(), context=module.context)

    executable = _find_single_nested("stream.executable", module.operation)
    local_module = _find_single_nested("builtin.module", executable)
    func = _find_single_nested("func.func", local_module)

    # TODO: add launch bounds

    to_delete = []  # type: list[Operation]
    subspans = []  # type: list[stream_d.BindingSubspanOp]

    def replace_ops_and_collect_subspans(op: Operation) -> WalkResult:
        """Callback for the function walk dispatching based on the operation kind."""

        # Replace IREE workgroup IDs with GPU dialect block IDs.
        if isinstance(op.opview, stream_d.DispatchWorkgroupIDOp):
            dispatch = op.opview  # type: stream_d.DispatchWorkgroupIDOp
            match dispatch.dimension.value:
                case 0:
                    dimension = gpu_d.Dimension.x
                case 1:
                    dimension = gpu_d.Dimension.y
                case 2:
                    dimension = gpu_d.Dimension.z
            with InsertionPoint(op), op.location:
                block_id = gpu_d.BlockIdOp(dimension)
            op.result.replace_all_uses_with(block_id.result)
            to_delete.append(op)
            return WalkResult.ADVANCE

        # Record IREE subspans so they can be replaced with function arguments.
        if isinstance(op.opview, stream_d.BindingSubspanOp):
            subspan = op.opview  # type: stream_d.BindingSubspanOp
            subspans.append(subspan)
            return WalkResult.ADVANCE

        # Replace allocations with poison values, at this point we don't support indirect loads/stores.
        # TODO: when adding support for indirect loads/stores, implement a check for not using data from local allocations in control flow or address computation; potentially with a fallback to allocating in another memory space.
        if isinstance(op.opview, memref_d.AllocOp):
            with op.context, InsertionPoint(op), op.location:
                original_memref_type = MemRefType(op.opview.memref.type)
                llvm_ptr_type = llvm_d.PointerType.get(
                    address_space=_get_numeric_memory_space(
                        original_memref_type.memory_space
                    )
                )
                llvm_descriptor_type = llvm_d.StructType.get_literal(
                    [llvm_ptr_type, llvm_ptr_type, IntegerType.get_signless(64)]
                )
                poison = llvm_d.PoisonOp(llvm_descriptor_type)
                base_memref_type = MemRefType.get(
                    [],
                    element_type=original_memref_type.element_type,
                    memory_space=original_memref_type.memory_space,
                )
                cast = Operation.create(
                    "builtin.unrealized_conversion_cast",
                    results=[base_memref_type],
                    operands=[poison.results[0]],
                )
                strides, _ = original_memref_type.get_strides_and_offset()
                assert (
                    MemRefType.get_dynamic_stride_or_offset() not in strides
                ), "Allocation is not expected to have dynamic strides."
                cast2 = memref_d.ReinterpretCastOp(
                    original_memref_type,
                    cast.results[0],
                    [],
                    op.opview.dynamicSizes,
                    [],
                    static_offsets=[0] * len(original_memref_type.shape),
                    static_sizes=original_memref_type.shape,
                    static_strides=strides,
                )
                op.opview.memref.replace_all_uses_with(cast2.result)
                to_delete.append(op)
                return WalkResult.ADVANCE

        return WalkResult.ADVANCE

    func.walk(replace_ops_and_collect_subspans)
    old_func_type = func.attributes["function_type"].value
    func_input_types = old_func_type.inputs
    for subspan in subspans:
        subspan.binding.set_type(subspan.result.type)
        arg_number = BlockArgument(subspan.binding).arg_number
        func_input_types[arg_number] = subspan.result.type
        subspan.result.replace_all_uses_except(subspan.binding, subspan.operation)
        to_delete.append(subspan)

    with old_func_type.context:
        func.attributes["function_type"] = TypeAttr.get(
            FunctionType.get(func_input_types, old_func_type.results)
        )

    for op in to_delete:
        op.erase()

    if int(os.environ.get("WAVE_WATER_DUMP_MLIR_BEFORE", "0")) != 0:
        print(local_module, file=sys.stderr)
    return local_module.get_asm(binary=False, print_generic_op_form=True)


def is_water_available() -> bool:
    """Returns True of the water_mlir package is available."""
    return importlib.util.find_spec("water_mlir") is not None


def water_leak_in_bounds_check(module: Module, override_ir: str = ""):
    try:
        from water_mlir import binaries as water_bin
    except ImportError as err:
        raise RuntimeError(
            "optional water_mlir module not installed but its use is requested"
        ) from err
    binary = water_bin.find_binary("water-opt")
    generic_mlir = _deiree(module) if override_ir == "" else override_ir
    pipeline = [
        (
            "water-assert-in-bounds",
            {"include-vector-load-store": 1, "create-speculative-funcs": 1},
        ),
        "lower-affine",
        "canonicalize",
        "cse",
        "loop-invariant-code-motion",
        "int-range-optimizations",
        "canonicalize",
        "water-check-static-assertions",
    ]

    def make_linear_pass_pipeline(
        pipeline: Sequence[tuple[str, dict[str, Any]] | str],
    ) -> str:
        def make_pass_arguments(name: str, args: dict[str, Any]) -> str:
            return (
                name
                + "{"
                + " ".join("=".join((key, str(value))) for (key, value) in args.items())
                + "}"
            )

        return (
            "--pass-pipeline=builtin.module("
            + ",".join(
                entry if isinstance(entry, str) else make_pass_arguments(*entry)
                for entry in pipeline
            )
            + ")"
        )

    def get_code_context(
        filename: str, start_line: int, end_line, context: int = 2
    ) -> str:
        """
        Retrieves a line and a few lines of context around it.

        Args:
            filename (str): The path to the file.
            line_number (int): The central line number to retrieve.
            context (int): The number of lines to show before and after.

        Returns:
            A string with the code + context.
        """
        start = max(1, start_line - context)
        end = end_line + context + 1

        num_characters = int(math.ceil(math.log10(end)))
        format_string = "{0:" + str(num_characters) + "d}"

        lines = []
        for i in range(start, end + 1):
            line = linecache.getline(filename, i)
            if not line:
                break
            lines.append(
                format_string.format(i)
                + f"{'*' if start_line <= i <= end_line else ' '}| {line.rstrip()}"
            )

        return "\n".join(lines)

    def diagnostic_from_json(
        json_obj: dict[str, Any], *, include_context: bool = False
    ) -> str:
        if "unknown" in json_obj:
            return "<unknown location>"
        if "name" in json_obj:
            child = diagnostic_from_json(
                json_obj["loc"], include_context=include_context
            )
            return '"' + json_obj["name"] + '" at' + child
        if "fused" in json_obj:
            result = "fused<["
            for d in json_obj["fused"]:
                result += "\n  " + diagnostic_from_json(
                    d, include_context=include_context
                )
            result += "]>"
            return result
        if "start_line" in json_obj:
            start_line, end_line, start_col, end_col = tuple(
                int(json_obj[key])
                for key in ("start_line", "end_line", "start_column", "end_column")
            )
            result = json_obj["file"] + ":" + str(start_line)
            zero_column = start_col == 0
            if not zero_column:
                result += ":" + str(start_col)
            same_line = start_line == end_line
            same_column = start_col == end_col
            if not same_line or (not same_column and not zero_column):
                result += " to "
                if not same_line:
                    result += str(end_line)
                if not same_column and not zero_column:
                    result += ":" + str(end_col)
            if include_context:
                result += "\n" + get_code_context(
                    json_obj["file"], start_line, end_line
                )
            return result
        if "callstack" in json_obj:
            # TODO: consider capturing Python stack frame objects in a
            # dictionary with unique names, using those names in named locations
            # in MLIR and then reconstructing the traceback programmatically.
            return "\ncalled from ".join(
                diagnostic_from_json(d, include_context=(i == 0 and include_context))
                for i, d in enumerate(json_obj["callstack"])
            )
        raise ValueError(f"Unhandled diagnostic: {json_obj}")

    exceptions = []

    with tempfile.TemporaryDirectory() as temp_dir:
        diagnosticsFile = Path(temp_dir) / "diagnostics.txt"
        result = subprocess.run(
            [
                binary,
                "--diagnostics-file",
                diagnosticsFile,
                "--allow-unregistered-dialect",
                make_linear_pass_pipeline(pipeline),
            ],
            input=generic_mlir,
            capture_output=True,
            text=True,
        )
        if diagnosticsFile.is_file():
            with open(diagnosticsFile, "r") as file:
                for line in file:
                    diag = json.loads(line.rstrip())
                    msg = (
                        diag["severity"]
                        + ": "
                        + diag["message"]
                        + "\nAt "
                        + diagnostic_from_json(diag, include_context=True)
                    )
                    exception = RuntimeError(f"{msg}")
                    exceptions.append(exception)

    if len(result.stderr) != 0:
        exceptions.append(RuntimeError("Water MLIR error (stderr): " + result.stderr))

    if int(os.environ.get("WAVE_WATER_DUMP_MLIR_AFTER", "0")) != 0:
        print(result.stdout, file=sys.stderr)

    if len(exceptions) > 0:
        # Exception groups are only available for Python >= 3.11
        assert sys.version_info.major == 3, "Unexpected Python version"
        if sys.version_info.minor >= 11:
            raise ExceptionGroup("Water errors: ", exceptions)

        if len(exceptions) == 1:
            raise exceptions[0]
        e = exceptions[0]
        e.add_note(f"{len(exceptions) - 1} other exceptions were generated")
        raise e

    if "cf.assert" in result.stdout:
        print(
            "[warning] Couldn't statically determine the absence of out-of-bounds accesses."
        )
    else:
        print("[info] No out-of-bounds accesses detected.")
