/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Interface Declarations                                                     *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace mlir {
namespace triton {
namespace gpu {
/// This interface is for operations that upcast floating-point numbers.
class UpcastFpOpInterface;
} // namespace gpu
} // namespace triton
} // namespace mlir
namespace mlir {
namespace triton {
namespace gpu {
/// This interface is for operations that upcast floating-point numbers.
namespace detail {
struct UpcastFpOpInterfaceInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    mlir::Attribute (*inferDstEncoding)(const Concept *impl, ::mlir::Operation *, unsigned, mlir::Attribute);
    mlir::Attribute (*inferSrcEncoding)(const Concept *impl, ::mlir::Operation *, unsigned, mlir::Attribute);
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::mlir::triton::gpu::UpcastFpOpInterface;
    Model() : Concept{inferDstEncoding, inferSrcEncoding} {}

    static inline mlir::Attribute inferDstEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute srcEnc);
    static inline mlir::Attribute inferSrcEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute dstEnc);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::mlir::triton::gpu::UpcastFpOpInterface;
    FallbackModel() : Concept{inferDstEncoding, inferSrcEncoding} {}

    static inline mlir::Attribute inferDstEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute srcEnc);
    static inline mlir::Attribute inferSrcEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute dstEnc);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
  };
};
template <typename ConcreteOp>
struct UpcastFpOpInterfaceTrait;

} // namespace detail
class UpcastFpOpInterface : public ::mlir::OpInterface<UpcastFpOpInterface, detail::UpcastFpOpInterfaceInterfaceTraits> {
public:
  using ::mlir::OpInterface<UpcastFpOpInterface, detail::UpcastFpOpInterfaceInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::UpcastFpOpInterfaceTrait<ConcreteOp> {};

  /// Infer destination encoding
  mlir::Attribute inferDstEncoding(unsigned opIdx, mlir::Attribute srcEnc);

  /// Infer operand encoding from dst encoding
  mlir::Attribute inferSrcEncoding(unsigned opIdx, mlir::Attribute dstEnc);
};
} // namespace gpu
} // namespace triton
} // namespace mlir
namespace mlir {
namespace triton {
namespace gpu {
namespace detail {
  template <typename ConcreteOp>
  struct UpcastFpOpInterfaceTrait : public ::mlir::OpInterface<UpcastFpOpInterface, detail::UpcastFpOpInterfaceInterfaceTraits>::Trait<ConcreteOp> {
  };
}// namespace detail
} // namespace gpu
} // namespace triton
} // namespace mlir
namespace mlir {
namespace triton {
namespace gpu {
template<typename ConcreteOp>
mlir::Attribute detail::UpcastFpOpInterfaceInterfaceTraits::Model<ConcreteOp>::inferDstEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute srcEnc) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).inferDstEncoding(opIdx, srcEnc);
}
template<typename ConcreteOp>
mlir::Attribute detail::UpcastFpOpInterfaceInterfaceTraits::Model<ConcreteOp>::inferSrcEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute dstEnc) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).inferSrcEncoding(opIdx, dstEnc);
}
template<typename ConcreteOp>
mlir::Attribute detail::UpcastFpOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::inferDstEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute srcEnc) {
  return static_cast<const ConcreteOp *>(impl)->inferDstEncoding(tablegen_opaque_val, opIdx, srcEnc);
}
template<typename ConcreteOp>
mlir::Attribute detail::UpcastFpOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::inferSrcEncoding(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, unsigned opIdx, mlir::Attribute dstEnc) {
  return static_cast<const ConcreteOp *>(impl)->inferSrcEncoding(tablegen_opaque_val, opIdx, dstEnc);
}
} // namespace gpu
} // namespace triton
} // namespace mlir
