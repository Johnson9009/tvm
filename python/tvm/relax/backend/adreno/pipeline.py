# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""The Relax Adreno GPU backend compilation pipeline and other passes."""
import tvm
from tvm import dlight as dl
from tvm import relax


def library_dispatch_passes(target: tvm.target.Target):  # pylint: disable=unused-argument
    """The default library dispatch passes for Adreno GPU backend."""
    if "clml" in target.keys:
        return [relax.backend.adreno.clml.OpenCLMLOffLoad()]
    else:
        return []


def legalize_passes(target: tvm.target.Target):  # pylint: disable=unused-argument
    """The default legalization passes for Adreno GPU backend."""
    return [
        relax.transform.DecomposeOpsForInference(),
        relax.transform.FoldConstant(),
        relax.transform.LegalizeOps(),
        relax.transform.AnnotateTIROpPattern(),
        relax.transform.FoldConstant(),
        relax.transform.FuseOps(),
        relax.transform.FuseTIR(),
        relax.transform.DeadCodeElimination(),
        dl.ApplyDefaultSchedule(
            dl.gpu.Reduction(),
            dl.gpu.GeneralReduction(),
            dl.gpu.Fallback(),
        ),
    ]


def dataflow_lower_passes(target: tvm.target.Target):  # pylint: disable=unused-argument
    """The default dataflow lowering passes for Adreno GPU backend."""
    return relax.backend.gpu_generic.dataflow_lower_passes(target)


def finalize_passes(target: tvm.target.Target):  # pylint: disable=unused-argument
    """The default finalization passes for Adreno GPU backend."""
    return relax.backend.gpu_generic.finalize_passes(target)


def get_default_pipeline(target: tvm.target.Target):
    """Return the default compilation pipeline for Adreno GPU."""

    @tvm.transform.module_pass(opt_level=0)
    def _pipeline(mod: tvm.ir.IRModule, _ctx: tvm.transform.PassContext):
        with target:
            seq = tvm.transform.Sequential(
                library_dispatch_passes(target)
                + legalize_passes(target)
                + dataflow_lower_passes(target)
                + finalize_passes(target)
            )
            mod = seq(mod)
        return mod

    return _pipeline
