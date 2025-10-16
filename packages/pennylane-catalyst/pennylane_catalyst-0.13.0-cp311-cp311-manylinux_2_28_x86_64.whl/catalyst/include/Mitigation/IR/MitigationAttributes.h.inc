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
namespace mitigation {
/// Folding types
class FoldingAttr;
namespace detail {
struct FoldingAttrStorage;
} // namespace detail
class FoldingAttr : public ::mlir::Attribute::AttrBase<FoldingAttr, ::mlir::Attribute, detail::FoldingAttrStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "mitigation.folding";
  static constexpr ::llvm::StringLiteral dialectName = "mitigation";
  static FoldingAttr get(::mlir::MLIRContext *context, catalyst::mitigation::Folding value);
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"folding"};
  }

  static ::mlir::Attribute parse(::mlir::AsmParser &odsParser, ::mlir::Type odsType);
  void print(::mlir::AsmPrinter &odsPrinter) const;
  catalyst::mitigation::Folding getValue() const;
};
} // namespace mitigation
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::mitigation::FoldingAttr)

#endif  // GET_ATTRDEF_CLASSES

