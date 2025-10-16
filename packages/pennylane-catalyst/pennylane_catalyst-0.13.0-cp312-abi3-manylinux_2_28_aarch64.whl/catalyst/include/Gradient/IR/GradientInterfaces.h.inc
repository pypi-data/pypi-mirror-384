/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Interface Declarations                                                     *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace gradient {
/// This interface provides a generic way to interact with instructions that 
///         are considered gradient operations. Currently these include GradOP, JVPOp, 
///         and VJPOp.
class GradientOpInterface;
namespace detail {
struct GradientOpInterfaceInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    llvm::StringRef (*getMethod)(const Concept *impl, ::mlir::Operation *);
    mlir::SymbolRefAttr (*getCallee)(const Concept *impl, ::mlir::Operation *);
    std::optional<mlir::DenseIntElementsAttr> (*getDiffArgIndices)(const Concept *impl, ::mlir::Operation *);
    mlir::DenseIntElementsAttr (*getDiffArgIndicesAttr)(const Concept *impl, ::mlir::Operation *);
    std::optional<mlir::FloatAttr> (*getFiniteDiffParam)(const Concept *impl, ::mlir::Operation *);
    mlir::FloatAttr (*getFiniteDiffParamAttr)(const Concept *impl, ::mlir::Operation *);
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::gradient::GradientOpInterface;
    Model() : Concept{getMethod, getCallee, getDiffArgIndices, getDiffArgIndicesAttr, getFiniteDiffParam, getFiniteDiffParamAttr} {}

    static inline llvm::StringRef getMethod(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::SymbolRefAttr getCallee(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline std::optional<mlir::DenseIntElementsAttr> getDiffArgIndices(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::DenseIntElementsAttr getDiffArgIndicesAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline std::optional<mlir::FloatAttr> getFiniteDiffParam(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::FloatAttr getFiniteDiffParamAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::gradient::GradientOpInterface;
    FallbackModel() : Concept{getMethod, getCallee, getDiffArgIndices, getDiffArgIndicesAttr, getFiniteDiffParam, getFiniteDiffParamAttr} {}

    static inline llvm::StringRef getMethod(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::SymbolRefAttr getCallee(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline std::optional<mlir::DenseIntElementsAttr> getDiffArgIndices(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::DenseIntElementsAttr getDiffArgIndicesAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline std::optional<mlir::FloatAttr> getFiniteDiffParam(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::FloatAttr getFiniteDiffParamAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
  };
};
template <typename ConcreteOp>
struct GradientOpInterfaceTrait;

} // namespace detail
class GradientOpInterface : public ::mlir::OpInterface<GradientOpInterface, detail::GradientOpInterfaceInterfaceTraits> {
public:
  using ::mlir::OpInterface<GradientOpInterface, detail::GradientOpInterfaceInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::GradientOpInterfaceTrait<ConcreteOp> {};

  /// Return the gradient method, which can be one of ["auto", "fd"].
  llvm::StringRef getMethod();

  /// Return the name of the callee, aka the function being differentiated by the gradient operation.
  mlir::SymbolRefAttr getCallee();

  /// Return the indices of the arguments being differentiated.
  std::optional<mlir::DenseIntElementsAttr> getDiffArgIndices();

  /// Return the indices of the arguments being differentiated, as an MLIR attribute.
  mlir::DenseIntElementsAttr getDiffArgIndicesAttr();

  /// Return the finite difference parameter.
  std::optional<mlir::FloatAttr> getFiniteDiffParam();

  /// Return the finite difference parameter, as an MLIR attribute.
  mlir::FloatAttr getFiniteDiffParamAttr();
};
namespace detail {
  template <typename ConcreteOp>
  struct GradientOpInterfaceTrait : public ::mlir::OpInterface<GradientOpInterface, detail::GradientOpInterfaceInterfaceTraits>::Trait<ConcreteOp> {
  };
}// namespace detail
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
template<typename ConcreteOp>
llvm::StringRef detail::GradientOpInterfaceInterfaceTraits::Model<ConcreteOp>::getMethod(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getMethod();
}
template<typename ConcreteOp>
mlir::SymbolRefAttr detail::GradientOpInterfaceInterfaceTraits::Model<ConcreteOp>::getCallee(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getCallee();
}
template<typename ConcreteOp>
std::optional<mlir::DenseIntElementsAttr> detail::GradientOpInterfaceInterfaceTraits::Model<ConcreteOp>::getDiffArgIndices(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getDiffArgIndices();
}
template<typename ConcreteOp>
mlir::DenseIntElementsAttr detail::GradientOpInterfaceInterfaceTraits::Model<ConcreteOp>::getDiffArgIndicesAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getDiffArgIndicesAttr();
}
template<typename ConcreteOp>
std::optional<mlir::FloatAttr> detail::GradientOpInterfaceInterfaceTraits::Model<ConcreteOp>::getFiniteDiffParam(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getFiniteDiffParam();
}
template<typename ConcreteOp>
mlir::FloatAttr detail::GradientOpInterfaceInterfaceTraits::Model<ConcreteOp>::getFiniteDiffParamAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getFiniteDiffParamAttr();
}
template<typename ConcreteOp>
llvm::StringRef detail::GradientOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::getMethod(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getMethod(tablegen_opaque_val);
}
template<typename ConcreteOp>
mlir::SymbolRefAttr detail::GradientOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::getCallee(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getCallee(tablegen_opaque_val);
}
template<typename ConcreteOp>
std::optional<mlir::DenseIntElementsAttr> detail::GradientOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::getDiffArgIndices(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getDiffArgIndices(tablegen_opaque_val);
}
template<typename ConcreteOp>
mlir::DenseIntElementsAttr detail::GradientOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::getDiffArgIndicesAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getDiffArgIndicesAttr(tablegen_opaque_val);
}
template<typename ConcreteOp>
std::optional<mlir::FloatAttr> detail::GradientOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::getFiniteDiffParam(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getFiniteDiffParam(tablegen_opaque_val);
}
template<typename ConcreteOp>
mlir::FloatAttr detail::GradientOpInterfaceInterfaceTraits::FallbackModel<ConcreteOp>::getFiniteDiffParamAttr(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getFiniteDiffParamAttr(tablegen_opaque_val);
}
} // namespace gradient
} // namespace catalyst
