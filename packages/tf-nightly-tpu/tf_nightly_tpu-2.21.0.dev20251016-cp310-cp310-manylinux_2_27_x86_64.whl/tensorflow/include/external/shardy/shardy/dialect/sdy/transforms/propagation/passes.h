/* Copyright 2024 The Shardy Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#ifndef SHARDY_DIALECT_SDY_TRANSFORMS_PROPAGATION_PASSES_H_
#define SHARDY_DIALECT_SDY_TRANSFORMS_PROPAGATION_PASSES_H_

// IWYU pragma: begin_keep

#include <memory>

#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassManager.h"
#include "mlir/Support/LLVM.h"
#include "shardy/dialect/sdy/ir/dialect.h"
#include "shardy/dialect/sdy/transforms/common/propagation_options.h"

// IWYU pragma: end_keep

namespace mlir {
namespace sdy {

#define GEN_PASS_DECL
#define GEN_PASS_REGISTRATION
#include "shardy/dialect/sdy/transforms/propagation/passes.h.inc"

// Adds the SDY propagation pass, preceded by a sequence of import passes needed
// as a pre-processing step for propagation.
//
// The added propagation pass is the top-level layer of propagation, which
// includes all conflict resolution strategies in a hierarchy.
//
// Takes the current index of the module dump, which will be included as a
// prefix in the file name, and incremented after each stage (dumped module).
void addPropagationPipeline(OpPassManager& pm, int& dumpIndex,
                            const PropagationOptions& options = {});

// Same as above, but initializes a default dump index to 0.
void addPropagationPipeline(OpPassManager& pm,
                            const PropagationOptions& options = {});

// Register the sdy-propagation-pipeline.
void registerPropagationPipeline();

}  // namespace sdy
}  // namespace mlir

#endif  // SHARDY_DIALECT_SDY_TRANSFORMS_PROPAGATION_PASSES_H_
