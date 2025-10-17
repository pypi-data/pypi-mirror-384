/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Dialect Definitions                                                        *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: TritonAMDGPUDialect.td                                               *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

MLIR_DEFINE_EXPLICIT_TYPE_ID(::mlir::triton::amdgpu::TritonAMDGPUDialect)
namespace mlir {
namespace triton {
namespace amdgpu {

TritonAMDGPUDialect::TritonAMDGPUDialect(::mlir::MLIRContext *context)
    : ::mlir::Dialect(getDialectNamespace(), context, ::mlir::TypeID::get<TritonAMDGPUDialect>())
    
     {
  getContext()->loadDialect<triton::TritonDialect>();
  initialize();
}

TritonAMDGPUDialect::~TritonAMDGPUDialect() = default;

} // namespace amdgpu
} // namespace triton
} // namespace mlir
