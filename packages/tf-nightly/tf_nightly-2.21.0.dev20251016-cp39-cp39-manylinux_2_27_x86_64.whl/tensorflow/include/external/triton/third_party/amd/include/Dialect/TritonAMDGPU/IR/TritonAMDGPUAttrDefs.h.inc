/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* AttrDef Declarations                                                       *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

#ifdef GET_ATTRDEF_CLASSES
#undef GET_ATTRDEF_CLASSES


namespace mlir {
class AsmParser;
class AsmPrinter;
} // namespace mlir
namespace mlir {
namespace triton {
namespace amdgpu {
/// Instruction Scheduling Hints for AMD GPUs
class SchedHintAttr;
namespace detail {
struct SchedHintAttrStorage;
} // namespace detail
class SchedHintAttr : public ::mlir::Attribute::AttrBase<SchedHintAttr, ::mlir::Attribute, detail::SchedHintAttrStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "amdgpu.SchedHintVariant";
  static constexpr ::llvm::StringLiteral dialectName = "amdgpu";
  static SchedHintAttr get(::mlir::MLIRContext *context, ::mlir::triton::amdgpu::SchedHint value);
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"SchedHintVariant"};
  }

  static ::mlir::Attribute parse(::mlir::AsmParser &odsParser, ::mlir::Type odsType);
  void print(::mlir::AsmPrinter &odsPrinter) const;
  ::mlir::triton::amdgpu::SchedHint getValue() const;
};
} // namespace amdgpu
} // namespace triton
} // namespace mlir
MLIR_DECLARE_EXPLICIT_TYPE_ID(::mlir::triton::amdgpu::SchedHintAttr)

#endif // GET_ATTRDEF_CLASSES

