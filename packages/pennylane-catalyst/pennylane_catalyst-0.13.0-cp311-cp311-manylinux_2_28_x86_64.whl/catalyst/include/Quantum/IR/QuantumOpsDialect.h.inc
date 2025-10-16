/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Dialect Declarations                                                       *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: QuantumOps.td                                                        *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace quantum {

/// A quantum computing dialect with value semantics.
/// The quantum dialect extends core MLIR with the necessary types and operations to form
///         the core IR of the Catalyst compiler.
/// 
///         At a minimum, a representation of quantum programs typically contains qubit management,
///         quantum gate operations, and measurements. The chosen representation for this dialect is
///         closely aligned with the operations in the [PennyLane](https://docs.pennylane.ai/en/stable/)
///         quantum computing framework, but also allows for custom instruction sets.
/// 
///         In this dialect, quantum operations are expressed using value semantics. That is abstract
///         qubit values are consumed and produced by operations, instead of operations merely acting on
///         qubit references. This exposes the dataflow of the quantum program in the SSA graph of the
///         MLIR. See [QIRO: An SSA-based Quantum IR for Optimization](https://doi.org/10.1145/3491247).
class QuantumDialect : public ::mlir::Dialect {
  explicit QuantumDialect(::mlir::MLIRContext *context);

  void initialize();
  friend class ::mlir::MLIRContext;
public:
  ~QuantumDialect() override;
  static constexpr ::llvm::StringLiteral getDialectNamespace() {
    return ::llvm::StringLiteral("quantum");
  }

  /// Parse an attribute registered to this dialect.
  ::mlir::Attribute parseAttribute(::mlir::DialectAsmParser &parser,
                                   ::mlir::Type type) const override;

  /// Print an attribute registered to this dialect.
  void printAttribute(::mlir::Attribute attr,
                      ::mlir::DialectAsmPrinter &os) const override;

  /// Parse a type registered to this dialect.
  ::mlir::Type parseType(::mlir::DialectAsmParser &parser) const override;

  /// Print a type registered to this dialect.
  void printType(::mlir::Type type,
                 ::mlir::DialectAsmPrinter &os) const override;
};
} // namespace quantum
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::quantum::QuantumDialect)
