/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Dialect Declarations                                                       *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: NVVMOps.td                                                           *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace mlir {
namespace NVVM {
/// The NVVM dialect that models NVIDIA's public ISA
/// The NVVM dialect is MLIR's LLVM-IR-based, NVIDIA-specific backend dialect. It
///     models NVVM intrinsics and public ISA functionality and introduces NVIDIA
///     extensions to the MLIR/LLVM type system and address spaces (e.g., global,
///     shared, and cluster memory), enabling faithful lowering of GPU kernels to the
///     NVPTX toolchain. While a NVVM op usually maps to a single LLVM IR intrinsic,
///     the NVVM dialect uses type polymorphism and other attributes so that a single
///     NVVM op can map to different LLVM intrinsics.
/// 
///     **Scope and capabilities:** The dialect covers core GPU features such as
///     thread/block builtins, barriers and atomics, warp-level collectives (e.g.,
///     shuffle/vote), matrix/tensor core operations (e.g., `mma.sync`, `wgmma`),
///     tensor memory accelerator (TMA) operations, asynchronous copies (`cp.async`,
///     bulk/tensor variants) with memory barriers, cache and prefetch controls, and
///     NVVM-specific attributes and enums (e.g., FP rounding modes, memory scopes,
///     and MMA types/layouts).
/// 
///     **Non-goals:** NVVM is not a place for convenience or “wrapper” ops. It is
///     not intended to introduce high-level ops that expand into multiple unrelated
///     NVVM intrinsics or that lower to no intrinsic at all. Such abstractions belong
///     in higher-level dialects (e.g., `nvgpu`, `gpu`, or project-specific dialects).
///     The design intent is a thin, predictable, low-level surface with
///     near-mechanical lowering to NVVM/LLVM IR.
/// 
///     **Placement in the lowering pipeline:** NVVM sits below target-agnostic
///     dialects like `gpu` and NVIDIA's `nvgpu`. Typical pipelines convert
///     `gpu`/`nvgpu` ops into NVVM using `-convert-gpu-to-nvvm` and
///     `-convert-nvgpu-to-nvvm`, then translate into LLVM for final code
///     generation via NVPTX backend.
/// 
///     **Target configuration and serialization:** NVVM provides a `#nvvm.target`
///     attribute to describe the GPU target (SM, features, and flags). In
///     conjunction with `gpu` serialization (e.g., `gpu-module-to-binary`), this
///     enables producing architecture-specific GPU binaries (such as CUBIN) from
///     nested GPU modules.
/// 
///     **Inline PTX:** When an intrinsic is unavailable or a performance-critical
///     sequence must be expressed directly, NVVM provides an `nvvm.inline_ptx` op to
///     embed PTX inline as a last-resort escape hatch, with explicit operands and
///     results.
class NVVMDialect : public ::mlir::Dialect {
  explicit NVVMDialect(::mlir::MLIRContext *context);

  void initialize();
  friend class ::mlir::MLIRContext;
public:
  ~NVVMDialect() override;
  static constexpr ::llvm::StringLiteral getDialectNamespace() {
    return ::llvm::StringLiteral("nvvm");
  }

  /// Parse an attribute registered to this dialect.
  ::mlir::Attribute parseAttribute(::mlir::DialectAsmParser &parser,
                                   ::mlir::Type type) const override;

  /// Print an attribute registered to this dialect.
  void printAttribute(::mlir::Attribute attr,
                      ::mlir::DialectAsmPrinter &os) const override;

    /// Provides a hook for verifying dialect attributes attached to the given
    /// op.
    ::llvm::LogicalResult verifyOperationAttribute(
        ::mlir::Operation *op, ::mlir::NamedAttribute attribute) override;

    /// Get the name of the attribute used to annotate external kernel
    /// functions.
    static StringRef getKernelFuncAttrName() { return "nvvm.kernel"; }
    /// Get the name of the attribute used to annotate max threads required
    /// per CTA for kernel functions.
    static StringRef getMaxntidAttrName() { return "nvvm.maxntid"; }
    /// Get the name of the metadata names for each dimension
    static StringRef getMaxntidXName() { return "maxntidx"; }
    static StringRef getMaxntidYName() { return "maxntidy"; }
    static StringRef getMaxntidZName() { return "maxntidz"; }

    /// Get the name of the attribute used to annotate exact threads required
    /// per CTA for kernel functions.
    static StringRef getReqntidAttrName() { return "nvvm.reqntid"; }
    /// Get the name of the metadata names for each dimension
    static StringRef getReqntidXName() { return "reqntidx"; }
    static StringRef getReqntidYName() { return "reqntidy"; }
    static StringRef getReqntidZName() { return "reqntidz"; }

    /// Get the name of the attribute used to annotate exact CTAs required
    /// per cluster for kernel functions.
    static StringRef getClusterDimAttrName() { return "nvvm.cluster_dim"; }
    /// Get the name of the metadata names for each dimension
    static StringRef getClusterDimXName() { return "cluster_dim_x"; }
    static StringRef getClusterDimYName() { return "cluster_dim_y"; }
    static StringRef getClusterDimZName() { return "cluster_dim_z"; }

    /// Get the name of the attribute used to annotate maximum number of
    /// CTAs per cluster for kernel functions.
    static StringRef getClusterMaxBlocksAttrName() {  return "nvvm.cluster_max_blocks"; }

    /// Get the name of the attribute used to annotate min CTA required
    /// per SM for kernel functions.
    static StringRef getMinctasmAttrName() { return "nvvm.minctasm"; }

    /// Get the name of the attribute used to annotate max number of
    /// registers that can be allocated per thread.
    static StringRef getMaxnregAttrName() { return "nvvm.maxnreg"; }

    /// Get the name of the attribute used to annotate kernel arguments that
    /// are grid constants.
    static StringRef getGridConstantAttrName() { return "nvvm.grid_constant"; }

    /// Get the name of the attribute used to annotate the `.blocksareclusters`
    /// PTX directive for kernel functions.
    /// This attribute implies that the grid launch configuration for the
    /// corresponding kernel function is specifying the number of clusters
    /// instead of the number of thread blocks. This attribute is only
    /// allowed for kernel functions and requires nvvm.reqntid and
    /// nvvm.cluster_dim attributes.
    static StringRef getBlocksAreClustersAttrName() { return "nvvm.blocksareclusters"; }

    /// Verify an attribute from this dialect on the argument at 'argIndex' for
    /// the region at 'regionIndex' on the given operation. Returns failure if
    /// the verification failed, success otherwise. This hook may optionally be
    /// invoked from any operation containing a region.
    LogicalResult verifyRegionArgAttribute(Operation *op,
                                           unsigned regionIndex,
                                           unsigned argIndex,
                                           NamedAttribute argAttr) override;
  };
} // namespace NVVM
} // namespace mlir
MLIR_DECLARE_EXPLICIT_TYPE_ID(::mlir::NVVM::NVVMDialect)
