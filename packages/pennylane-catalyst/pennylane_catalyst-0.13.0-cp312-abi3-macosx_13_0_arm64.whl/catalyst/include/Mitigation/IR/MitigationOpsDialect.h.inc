/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Dialect Declarations                                                       *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: MitigationOps.td                                                     *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace mitigation {

/// A dialect for quantum mitigation.
/// This dialect contains operations to represent mitigation on quantum functions,
///         as well as lowering mechanisms to compute the mitigated expectation value.
class MitigationDialect : public ::mlir::Dialect {
  explicit MitigationDialect(::mlir::MLIRContext *context);

  void initialize();
  friend class ::mlir::MLIRContext;
public:
  ~MitigationDialect() override;
  static constexpr ::llvm::StringLiteral getDialectNamespace() {
    return ::llvm::StringLiteral("mitigation");
  }

  /// Parse an attribute registered to this dialect.
  ::mlir::Attribute parseAttribute(::mlir::DialectAsmParser &parser,
                                   ::mlir::Type type) const override;

  /// Print an attribute registered to this dialect.
  void printAttribute(::mlir::Attribute attr,
                      ::mlir::DialectAsmPrinter &os) const override;
};
} // namespace mitigation
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::mitigation::MitigationDialect)
