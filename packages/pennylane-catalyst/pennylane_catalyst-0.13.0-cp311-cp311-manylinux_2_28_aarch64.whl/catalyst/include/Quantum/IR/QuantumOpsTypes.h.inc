/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* TypeDef Declarations                                                       *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

#ifdef GET_TYPEDEF_CLASSES
#undef GET_TYPEDEF_CLASSES


namespace mlir {
class AsmParser;
class AsmPrinter;
} // namespace mlir
namespace catalyst {
namespace quantum {
/// A value-semantic qubit (state).
class QubitType;
/// An array of value-semantic qubits (i.e. quantum register).
class QuregType;
/// A quantum observable for use in measurements.
class ObservableType;
/// A quantum measurement result.
class ResultType;
class QubitType : public ::mlir::Type::TypeBase<QubitType, ::mlir::Type, ::mlir::TypeStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "quantum.bit";
  static constexpr ::llvm::StringLiteral dialectName = "quantum";
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"bit"};
  }

};
class QuregType : public ::mlir::Type::TypeBase<QuregType, ::mlir::Type, ::mlir::TypeStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "quantum.reg";
  static constexpr ::llvm::StringLiteral dialectName = "quantum";
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"reg"};
  }

};
class ObservableType : public ::mlir::Type::TypeBase<ObservableType, ::mlir::Type, ::mlir::TypeStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "quantum.obs";
  static constexpr ::llvm::StringLiteral dialectName = "quantum";
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"obs"};
  }

};
class ResultType : public ::mlir::Type::TypeBase<ResultType, ::mlir::Type, ::mlir::TypeStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "quantum.res";
  static constexpr ::llvm::StringLiteral dialectName = "quantum";
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"res"};
  }

};
} // namespace quantum
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::quantum::QubitType)
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::quantum::QuregType)
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::quantum::ObservableType)
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::quantum::ResultType)

#endif  // GET_TYPEDEF_CLASSES

