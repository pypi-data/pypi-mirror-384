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
namespace catalyst {
namespace quantum {
/// Known named observables
class NamedObservableAttr;
namespace detail {
struct NamedObservableAttrStorage;
} // namespace detail
class NamedObservableAttr : public ::mlir::Attribute::AttrBase<NamedObservableAttr, ::mlir::Attribute, detail::NamedObservableAttrStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "quantum.named_observable";
  static constexpr ::llvm::StringLiteral dialectName = "quantum";
  static NamedObservableAttr get(::mlir::MLIRContext *context, catalyst::quantum::NamedObservable value);
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"named_observable"};
  }

  static ::mlir::Attribute parse(::mlir::AsmParser &odsParser, ::mlir::Type odsType);
  void print(::mlir::AsmPrinter &odsPrinter) const;
  catalyst::quantum::NamedObservable getValue() const;
};
} // namespace quantum
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::quantum::NamedObservableAttr)

#endif  // GET_ATTRDEF_CLASSES

