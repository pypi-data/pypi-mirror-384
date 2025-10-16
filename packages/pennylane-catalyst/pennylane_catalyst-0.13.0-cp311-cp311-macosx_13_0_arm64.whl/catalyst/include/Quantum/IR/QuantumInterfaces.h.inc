/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Interface Declarations                                                     *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace quantum {
/// This interface provides a generic way to interact with instructions that are
///         considered quantum regions. These are characterized by operating on a single
///         qubit register, and returning a new register value.
class QuantumRegion;
namespace detail {
struct QuantumRegionInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    mlir::Value (*getRegisterOperand)(const Concept *impl, ::mlir::Operation *);
    mlir::Value (*getRegisterResult)(const Concept *impl, ::mlir::Operation *);
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::quantum::QuantumRegion;
    Model() : Concept{getRegisterOperand, getRegisterResult} {}

    static inline mlir::Value getRegisterOperand(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::Value getRegisterResult(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::quantum::QuantumRegion;
    FallbackModel() : Concept{getRegisterOperand, getRegisterResult} {}

    static inline mlir::Value getRegisterOperand(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::Value getRegisterResult(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
  };
};
template <typename ConcreteOp>
struct QuantumRegionTrait;

} // namespace detail
class QuantumRegion : public ::mlir::OpInterface<QuantumRegion, detail::QuantumRegionInterfaceTraits> {
public:
  using ::mlir::OpInterface<QuantumRegion, detail::QuantumRegionInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::QuantumRegionTrait<ConcreteOp> {};

  /// Return the quantum register operand.
  mlir::Value getRegisterOperand();

  /// Return the quantum register result.
  mlir::Value getRegisterResult();
};
namespace detail {
  template <typename ConcreteOp>
  struct QuantumRegionTrait : public ::mlir::OpInterface<QuantumRegion, detail::QuantumRegionInterfaceTraits>::Trait<ConcreteOp> {
    static ::llvm::LogicalResult verifyTrait(::mlir::Operation *op) {
      if (op->getNumOperands() != 1)
            return op->emitOpError("must have exactly one operand (quantum register)");

        if (op->getNumResults() != 1)
            return op->emitOpError("must have exactly one result (quantum register)");

        return mlir::success();
    }
  };
}// namespace detail
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
/// This interface provides a generic way to interact with instructions that are
///         considered quantum logic gates. These are characterized by operating on zero
///         or more qubit values, and returning the same amount of qubit values.
class QuantumOperation;
namespace detail {
struct QuantumOperationInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    std::vector<mlir::Value> (*getQubitOperands)(const Concept *impl, ::mlir::Operation *);
    void (*setQubitOperands)(const Concept *impl, ::mlir::Operation *, mlir::ValueRange);
    std::vector<mlir::OpResult> (*getQubitResults)(const Concept *impl, ::mlir::Operation *);
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::quantum::QuantumOperation;
    Model() : Concept{getQubitOperands, setQubitOperands, getQubitResults} {}

    static inline std::vector<mlir::Value> getQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline std::vector<mlir::OpResult> getQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::quantum::QuantumOperation;
    FallbackModel() : Concept{getQubitOperands, setQubitOperands, getQubitResults} {}

    static inline std::vector<mlir::Value> getQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline std::vector<mlir::OpResult> getQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
  };
};
template <typename ConcreteOp>
struct QuantumOperationTrait;

} // namespace detail
class QuantumOperation : public ::mlir::OpInterface<QuantumOperation, detail::QuantumOperationInterfaceTraits> {
public:
  using ::mlir::OpInterface<QuantumOperation, detail::QuantumOperationInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::QuantumOperationTrait<ConcreteOp> {};

  /// Return all operands which are considered input qubit values (including controls).
  std::vector<mlir::Value> getQubitOperands();

  /// Set all operands which are considered input qubit values (including controls).
  void setQubitOperands(mlir::ValueRange replacements);

  /// Return all results which are considered output qubit values (including controls).
  std::vector<mlir::OpResult> getQubitResults();
};
namespace detail {
  template <typename ConcreteOp>
  struct QuantumOperationTrait : public ::mlir::OpInterface<QuantumOperation, detail::QuantumOperationInterfaceTraits>::Trait<ConcreteOp> {
    static ::llvm::LogicalResult verifyTrait(::mlir::Operation *op) {
      auto gate = mlir::cast<ConcreteOp>(op);

        if (gate.getQubitOperands().size() != gate.getQubitResults().size())
            return op->emitError() <<
                "number of qubits in input (" << gate.getQubitOperands().size() << ") " <<
                "and output (" << gate.getQubitResults().size() << ") must be the same";

        return mlir::success();
    }
  };
}// namespace detail
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
/// This interface provides a generic way to interact with instructions that are
///         considered 'unitary' gates, which in addition to the properties of the
///         "QuantumOperation" can be inverted and controlled.
class QuantumGate;
namespace detail {
struct QuantumGateInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    mlir::ValueRange (*getNonCtrlQubitOperands)(const Concept *impl, ::mlir::Operation *);
    void (*setNonCtrlQubitOperands)(const Concept *impl, ::mlir::Operation *, mlir::ValueRange);
    mlir::ResultRange (*getNonCtrlQubitResults)(const Concept *impl, ::mlir::Operation *);
    mlir::ValueRange (*getCtrlQubitOperands)(const Concept *impl, ::mlir::Operation *);
    void (*setCtrlQubitOperands)(const Concept *impl, ::mlir::Operation *, mlir::ValueRange);
    mlir::ValueRange (*getCtrlValueOperands)(const Concept *impl, ::mlir::Operation *);
    void (*setCtrlValueOperands)(const Concept *impl, ::mlir::Operation *, mlir::ValueRange);
    mlir::ResultRange (*getCtrlQubitResults)(const Concept *impl, ::mlir::Operation *);
    bool (*getAdjointFlag)(const Concept *impl, ::mlir::Operation *);
    void (*setAdjointFlag)(const Concept *impl, ::mlir::Operation *, bool);
    /// The base classes of this interface.
    const ::catalyst::quantum::QuantumOperation::Concept *implQuantumOperation = nullptr;

    void initializeInterfaceConcept(::mlir::detail::InterfaceMap &interfaceMap) {
      implQuantumOperation = interfaceMap.lookup<::catalyst::quantum::QuantumOperation>();
      assert(implQuantumOperation && "`::catalyst::quantum::QuantumGate` expected its base interface `::catalyst::quantum::QuantumOperation` to be registered");
    }
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::quantum::QuantumGate;
    Model() : Concept{getNonCtrlQubitOperands, setNonCtrlQubitOperands, getNonCtrlQubitResults, getCtrlQubitOperands, setCtrlQubitOperands, getCtrlValueOperands, setCtrlValueOperands, getCtrlQubitResults, getAdjointFlag, setAdjointFlag} {}

    static inline mlir::ValueRange getNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline mlir::ResultRange getNonCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::ValueRange getCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline mlir::ValueRange getCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline mlir::ResultRange getCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline bool getAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, bool adjoint);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::quantum::QuantumGate;
    FallbackModel() : Concept{getNonCtrlQubitOperands, setNonCtrlQubitOperands, getNonCtrlQubitResults, getCtrlQubitOperands, setCtrlQubitOperands, getCtrlValueOperands, setCtrlValueOperands, getCtrlQubitResults, getAdjointFlag, setAdjointFlag} {}

    static inline mlir::ValueRange getNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline mlir::ResultRange getNonCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline mlir::ValueRange getCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline mlir::ValueRange getCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements);
    static inline mlir::ResultRange getCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline bool getAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline void setAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, bool adjoint);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
  };
};
template <typename ConcreteOp>
struct QuantumGateTrait;

} // namespace detail
class QuantumGate : public ::mlir::OpInterface<QuantumGate, detail::QuantumGateInterfaceTraits> {
public:
  using ::mlir::OpInterface<QuantumGate, detail::QuantumGateInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::QuantumGateTrait<ConcreteOp> {};

  /// Return operands which are considered non-controlled input qubit values.
  mlir::ValueRange getNonCtrlQubitOperands();

  /// Set all operands which are considered non-controlled input qubit values.
  void setNonCtrlQubitOperands(mlir::ValueRange replacements);

  /// Return results which are considered non-controlled output qubit values.
  mlir::ResultRange getNonCtrlQubitResults();

  /// Return all operands which are considered controlling input qubit values.
  mlir::ValueRange getCtrlQubitOperands();

  /// Set all operands which are considered controlling input qubit values.
  void setCtrlQubitOperands(mlir::ValueRange replacements);

  /// Return all operands which are considered controlling input boolean values.
  mlir::ValueRange getCtrlValueOperands();

  /// Set all operands which are considered controlling input boolean values.
  void setCtrlValueOperands(mlir::ValueRange replacements);

  /// Return all operands which are considered controlling output qubit values.
  mlir::ResultRange getCtrlQubitResults();

  /// Return adjoint flag.
  bool getAdjointFlag();

  /// Set adjoint flag.
  void setAdjointFlag(bool adjoint);
  //===----------------------------------------------------------------===//
  // Inherited from ::catalyst::quantum::QuantumOperation
  //===----------------------------------------------------------------===//

  operator ::catalyst::quantum::QuantumOperation () const {
    if (!*this) return nullptr;
    return ::catalyst::quantum::QuantumOperation(*this, getImpl()->implQuantumOperation);
  }


  /// Return all operands which are considered input qubit values (including controls).
  std::vector<mlir::Value> getQubitOperands();

  /// Set all operands which are considered input qubit values (including controls).
  void setQubitOperands(mlir::ValueRange replacements);

  /// Return all results which are considered output qubit values (including controls).
  std::vector<mlir::OpResult> getQubitResults();
};
namespace detail {
  template <typename ConcreteOp>
  struct QuantumGateTrait : public ::mlir::OpInterface<QuantumGate, detail::QuantumGateInterfaceTraits>::Trait<ConcreteOp> {
    static ::llvm::LogicalResult verifyTrait(::mlir::Operation *op) {
      auto gate = mlir::cast<ConcreteOp>(op);

        if (gate.getCtrlValueOperands().size() != gate.getCtrlQubitOperands().size())
            return op->emitError() <<
                "number of controlling qubits in input (" <<
                gate.getCtrlQubitOperands().size() << ") " <<
                "and controlling values (" <<
                gate.getCtrlValueOperands().size() <<
                ") must be the same";

        if (gate.getCtrlQubitOperands().size() != gate.getCtrlQubitResults().size())
            return op->emitError() <<
                "number of controlling qubits in input (" <<
                gate.getCtrlQubitOperands().size() << ") " <<
                "and output (" <<
                gate.getCtrlQubitResults().size() <<
                ") must be the same";

        return mlir::success();
    }
  };
}// namespace detail
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
/// This interface provides a generic way to interact with parametrized
///         quantum instructions. These are quantum operations with arbitrary
///         classical gate parameters.
class ParametrizedGate;
namespace detail {
struct ParametrizedGateInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    mlir::ValueRange (*getAllParams)(const Concept *impl, ::mlir::Operation *);
    size_t (*getParamOperandIdx)(const Concept *impl, ::mlir::Operation *);
    /// The base classes of this interface.
    const ::catalyst::quantum::QuantumOperation::Concept *implQuantumOperation = nullptr;
    const ::catalyst::quantum::QuantumGate::Concept *implQuantumGate = nullptr;

    void initializeInterfaceConcept(::mlir::detail::InterfaceMap &interfaceMap) {
      implQuantumOperation = interfaceMap.lookup<::catalyst::quantum::QuantumOperation>();
      assert(implQuantumOperation && "`::catalyst::quantum::ParametrizedGate` expected its base interface `::catalyst::quantum::QuantumOperation` to be registered");
      implQuantumGate = interfaceMap.lookup<::catalyst::quantum::QuantumGate>();
      assert(implQuantumGate && "`::catalyst::quantum::ParametrizedGate` expected its base interface `::catalyst::quantum::QuantumGate` to be registered");
    }
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::quantum::ParametrizedGate;
    Model() : Concept{getAllParams, getParamOperandIdx} {}

    static inline mlir::ValueRange getAllParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline size_t getParamOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::quantum::ParametrizedGate;
    FallbackModel() : Concept{getAllParams, getParamOperandIdx} {}

    static inline mlir::ValueRange getAllParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline size_t getParamOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
    size_t getParamOperandIdx(::mlir::Operation *tablegen_opaque_val) const;
  };
};
template <typename ConcreteOp>
struct ParametrizedGateTrait;

} // namespace detail
class ParametrizedGate : public ::mlir::OpInterface<ParametrizedGate, detail::ParametrizedGateInterfaceTraits> {
public:
  using ::mlir::OpInterface<ParametrizedGate, detail::ParametrizedGateInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::ParametrizedGateTrait<ConcreteOp> {};

  /// Return all operands which are considered gate parameters.
  mlir::ValueRange getAllParams();

  /// Return the starting index at which to find gate parameter operands.
  size_t getParamOperandIdx();
  //===----------------------------------------------------------------===//
  // Inherited from ::catalyst::quantum::QuantumOperation
  //===----------------------------------------------------------------===//

  operator ::catalyst::quantum::QuantumOperation () const {
    if (!*this) return nullptr;
    return ::catalyst::quantum::QuantumOperation(*this, getImpl()->implQuantumOperation);
  }


  /// Return all operands which are considered input qubit values (including controls).
  std::vector<mlir::Value> getQubitOperands();

  /// Set all operands which are considered input qubit values (including controls).
  void setQubitOperands(mlir::ValueRange replacements);

  /// Return all results which are considered output qubit values (including controls).
  std::vector<mlir::OpResult> getQubitResults();
  //===----------------------------------------------------------------===//
  // Inherited from ::catalyst::quantum::QuantumGate
  //===----------------------------------------------------------------===//

  operator ::catalyst::quantum::QuantumGate () const {
    if (!*this) return nullptr;
    return ::catalyst::quantum::QuantumGate(*this, getImpl()->implQuantumGate);
  }


  /// Return operands which are considered non-controlled input qubit values.
  mlir::ValueRange getNonCtrlQubitOperands();

  /// Set all operands which are considered non-controlled input qubit values.
  void setNonCtrlQubitOperands(mlir::ValueRange replacements);

  /// Return results which are considered non-controlled output qubit values.
  mlir::ResultRange getNonCtrlQubitResults();

  /// Return all operands which are considered controlling input qubit values.
  mlir::ValueRange getCtrlQubitOperands();

  /// Set all operands which are considered controlling input qubit values.
  void setCtrlQubitOperands(mlir::ValueRange replacements);

  /// Return all operands which are considered controlling input boolean values.
  mlir::ValueRange getCtrlValueOperands();

  /// Set all operands which are considered controlling input boolean values.
  void setCtrlValueOperands(mlir::ValueRange replacements);

  /// Return all operands which are considered controlling output qubit values.
  mlir::ResultRange getCtrlQubitResults();

  /// Return adjoint flag.
  bool getAdjointFlag();

  /// Set adjoint flag.
  void setAdjointFlag(bool adjoint);
};
namespace detail {
  template <typename ConcreteOp>
  struct ParametrizedGateTrait : public ::mlir::OpInterface<ParametrizedGate, detail::ParametrizedGateInterfaceTraits>::Trait<ConcreteOp> {

    /// Return the starting index at which to find gate parameter operands.
    size_t getParamOperandIdx() {
      return 0;
    }
  };
}// namespace detail
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
/// This interface provides a generic way to interact with differentiable
///         quantum instructions. These are quantum operations with differentiable
///         gate parameters (must be scalar F64 values).
class DifferentiableGate;
namespace detail {
struct DifferentiableGateInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
    mlir::ValueRange (*getDiffParams)(const Concept *impl, ::mlir::Operation *);
    size_t (*getDiffOperandIdx)(const Concept *impl, ::mlir::Operation *);
    /// The base classes of this interface.
    const ::catalyst::quantum::QuantumOperation::Concept *implQuantumOperation = nullptr;
    const ::catalyst::quantum::QuantumGate::Concept *implQuantumGate = nullptr;
    const ::catalyst::quantum::ParametrizedGate::Concept *implParametrizedGate = nullptr;

    void initializeInterfaceConcept(::mlir::detail::InterfaceMap &interfaceMap) {
      implQuantumOperation = interfaceMap.lookup<::catalyst::quantum::QuantumOperation>();
      assert(implQuantumOperation && "`::catalyst::quantum::DifferentiableGate` expected its base interface `::catalyst::quantum::QuantumOperation` to be registered");
      implQuantumGate = interfaceMap.lookup<::catalyst::quantum::QuantumGate>();
      assert(implQuantumGate && "`::catalyst::quantum::DifferentiableGate` expected its base interface `::catalyst::quantum::QuantumGate` to be registered");
      implParametrizedGate = interfaceMap.lookup<::catalyst::quantum::ParametrizedGate>();
      assert(implParametrizedGate && "`::catalyst::quantum::DifferentiableGate` expected its base interface `::catalyst::quantum::ParametrizedGate` to be registered");
    }
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::quantum::DifferentiableGate;
    Model() : Concept{getDiffParams, getDiffOperandIdx} {}

    static inline mlir::ValueRange getDiffParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline size_t getDiffOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::quantum::DifferentiableGate;
    FallbackModel() : Concept{getDiffParams, getDiffOperandIdx} {}

    static inline mlir::ValueRange getDiffParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
    static inline size_t getDiffOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val);
  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
    mlir::ValueRange getDiffParams(::mlir::Operation *tablegen_opaque_val) const;
    size_t getDiffOperandIdx(::mlir::Operation *tablegen_opaque_val) const;
  };
};
template <typename ConcreteOp>
struct DifferentiableGateTrait;

} // namespace detail
class DifferentiableGate : public ::mlir::OpInterface<DifferentiableGate, detail::DifferentiableGateInterfaceTraits> {
public:
  using ::mlir::OpInterface<DifferentiableGate, detail::DifferentiableGateInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::DifferentiableGateTrait<ConcreteOp> {};

  /// Return all operands which are considered differentiable gate parameters.
  mlir::ValueRange getDiffParams();

  /// Return the starting index at which to find differentiable operands in the Operation*.Differentiable gate parameter operands do not need to be stored in a single ODS argument or be located in a particular position, but are assumed to be contiguous.
  size_t getDiffOperandIdx();
  //===----------------------------------------------------------------===//
  // Inherited from ::catalyst::quantum::QuantumOperation
  //===----------------------------------------------------------------===//

  operator ::catalyst::quantum::QuantumOperation () const {
    if (!*this) return nullptr;
    return ::catalyst::quantum::QuantumOperation(*this, getImpl()->implQuantumOperation);
  }


  /// Return all operands which are considered input qubit values (including controls).
  std::vector<mlir::Value> getQubitOperands();

  /// Set all operands which are considered input qubit values (including controls).
  void setQubitOperands(mlir::ValueRange replacements);

  /// Return all results which are considered output qubit values (including controls).
  std::vector<mlir::OpResult> getQubitResults();
  //===----------------------------------------------------------------===//
  // Inherited from ::catalyst::quantum::QuantumGate
  //===----------------------------------------------------------------===//

  operator ::catalyst::quantum::QuantumGate () const {
    if (!*this) return nullptr;
    return ::catalyst::quantum::QuantumGate(*this, getImpl()->implQuantumGate);
  }


  /// Return operands which are considered non-controlled input qubit values.
  mlir::ValueRange getNonCtrlQubitOperands();

  /// Set all operands which are considered non-controlled input qubit values.
  void setNonCtrlQubitOperands(mlir::ValueRange replacements);

  /// Return results which are considered non-controlled output qubit values.
  mlir::ResultRange getNonCtrlQubitResults();

  /// Return all operands which are considered controlling input qubit values.
  mlir::ValueRange getCtrlQubitOperands();

  /// Set all operands which are considered controlling input qubit values.
  void setCtrlQubitOperands(mlir::ValueRange replacements);

  /// Return all operands which are considered controlling input boolean values.
  mlir::ValueRange getCtrlValueOperands();

  /// Set all operands which are considered controlling input boolean values.
  void setCtrlValueOperands(mlir::ValueRange replacements);

  /// Return all operands which are considered controlling output qubit values.
  mlir::ResultRange getCtrlQubitResults();

  /// Return adjoint flag.
  bool getAdjointFlag();

  /// Set adjoint flag.
  void setAdjointFlag(bool adjoint);
  //===----------------------------------------------------------------===//
  // Inherited from ::catalyst::quantum::ParametrizedGate
  //===----------------------------------------------------------------===//

  operator ::catalyst::quantum::ParametrizedGate () const {
    if (!*this) return nullptr;
    return ::catalyst::quantum::ParametrizedGate(*this, getImpl()->implParametrizedGate);
  }


  /// Return all operands which are considered gate parameters.
  mlir::ValueRange getAllParams();

  /// Return the starting index at which to find gate parameter operands.
  size_t getParamOperandIdx();
};
namespace detail {
  template <typename ConcreteOp>
  struct DifferentiableGateTrait : public ::mlir::OpInterface<DifferentiableGate, detail::DifferentiableGateInterfaceTraits>::Trait<ConcreteOp> {

    /// Return all operands which are considered differentiable gate parameters.
    mlir::ValueRange getDiffParams() {
      return (*static_cast<ConcreteOp *>(this)).getAllParams();
    }

    /// Return the starting index at which to find differentiable operands in the Operation*.Differentiable gate parameter operands do not need to be stored in a single ODS argument or be located in a particular position, but are assumed to be contiguous.
    size_t getDiffOperandIdx() {
      return (*static_cast<ConcreteOp *>(this)).getParamOperandIdx();
    }
  };
}// namespace detail
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
/// This interface provides a generic way to interact with quantum measurement processes.
///         These are instructions that represent some information extraction procedure on the
///         underlying statevector. On simulators, they may be implemented by direct manipulation
///         of the statevector, but on hardware they typically turn into procedures over the quantum
///         program as a whole, usually requiring many executions of the same circuit.
class MeasurementProcess;
namespace detail {
struct MeasurementProcessInterfaceTraits {
  struct Concept {
    /// The methods defined by the interface.
  };
  template<typename ConcreteOp>
  class Model : public Concept {
  public:
    using Interface = ::catalyst::quantum::MeasurementProcess;
    Model() : Concept{} {}

  };
  template<typename ConcreteOp>
  class FallbackModel : public Concept {
  public:
    using Interface = ::catalyst::quantum::MeasurementProcess;
    FallbackModel() : Concept{} {}

  };
  template<typename ConcreteModel, typename ConcreteOp>
  class ExternalModel : public FallbackModel<ConcreteModel> {
  public:
    using ConcreteEntity = ConcreteOp;
  };
};
template <typename ConcreteOp>
struct MeasurementProcessTrait;

} // namespace detail
class MeasurementProcess : public ::mlir::OpInterface<MeasurementProcess, detail::MeasurementProcessInterfaceTraits> {
public:
  using ::mlir::OpInterface<MeasurementProcess, detail::MeasurementProcessInterfaceTraits>::OpInterface;
  template <typename ConcreteOp>
  struct Trait : public detail::MeasurementProcessTrait<ConcreteOp> {};
};
namespace detail {
  template <typename ConcreteOp>
  struct MeasurementProcessTrait : public ::mlir::OpInterface<MeasurementProcess, detail::MeasurementProcessInterfaceTraits>::Trait<ConcreteOp> {
  };
}// namespace detail
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
template<typename ConcreteOp>
mlir::Value detail::QuantumRegionInterfaceTraits::Model<ConcreteOp>::getRegisterOperand(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val))->getOperand(0);
}
template<typename ConcreteOp>
mlir::Value detail::QuantumRegionInterfaceTraits::Model<ConcreteOp>::getRegisterResult(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val))->getResult(0);
}
template<typename ConcreteOp>
mlir::Value detail::QuantumRegionInterfaceTraits::FallbackModel<ConcreteOp>::getRegisterOperand(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getRegisterOperand(tablegen_opaque_val);
}
template<typename ConcreteOp>
mlir::Value detail::QuantumRegionInterfaceTraits::FallbackModel<ConcreteOp>::getRegisterResult(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getRegisterResult(tablegen_opaque_val);
}
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
template<typename ConcreteOp>
std::vector<mlir::Value> detail::QuantumOperationInterfaceTraits::Model<ConcreteOp>::getQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getQubitOperands();
}
template<typename ConcreteOp>
void detail::QuantumOperationInterfaceTraits::Model<ConcreteOp>::setQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).setQubitOperands(replacements);
}
template<typename ConcreteOp>
std::vector<mlir::OpResult> detail::QuantumOperationInterfaceTraits::Model<ConcreteOp>::getQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getQubitResults();
}
template<typename ConcreteOp>
std::vector<mlir::Value> detail::QuantumOperationInterfaceTraits::FallbackModel<ConcreteOp>::getQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getQubitOperands(tablegen_opaque_val);
}
template<typename ConcreteOp>
void detail::QuantumOperationInterfaceTraits::FallbackModel<ConcreteOp>::setQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return static_cast<const ConcreteOp *>(impl)->setQubitOperands(tablegen_opaque_val, replacements);
}
template<typename ConcreteOp>
std::vector<mlir::OpResult> detail::QuantumOperationInterfaceTraits::FallbackModel<ConcreteOp>::getQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getQubitResults(tablegen_opaque_val);
}
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
template<typename ConcreteOp>
mlir::ValueRange detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::getNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getNonCtrlQubitOperands();
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::setNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).setNonCtrlQubitOperands(replacements);
}
template<typename ConcreteOp>
mlir::ResultRange detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::getNonCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getNonCtrlQubitResults();
}
template<typename ConcreteOp>
mlir::ValueRange detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::getCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getCtrlQubitOperands();
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::setCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).setCtrlQubitOperands(replacements);
}
template<typename ConcreteOp>
mlir::ValueRange detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::getCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getCtrlValueOperands();
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::setCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).setCtrlValueOperands(replacements);
}
template<typename ConcreteOp>
mlir::ResultRange detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::getCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getCtrlQubitResults();
}
template<typename ConcreteOp>
bool detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::getAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getAdjointFlag();
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::Model<ConcreteOp>::setAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, bool adjoint) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).setAdjointFlag(adjoint);
}
template<typename ConcreteOp>
mlir::ValueRange detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::getNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getNonCtrlQubitOperands(tablegen_opaque_val);
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::setNonCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return static_cast<const ConcreteOp *>(impl)->setNonCtrlQubitOperands(tablegen_opaque_val, replacements);
}
template<typename ConcreteOp>
mlir::ResultRange detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::getNonCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getNonCtrlQubitResults(tablegen_opaque_val);
}
template<typename ConcreteOp>
mlir::ValueRange detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::getCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getCtrlQubitOperands(tablegen_opaque_val);
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::setCtrlQubitOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return static_cast<const ConcreteOp *>(impl)->setCtrlQubitOperands(tablegen_opaque_val, replacements);
}
template<typename ConcreteOp>
mlir::ValueRange detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::getCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getCtrlValueOperands(tablegen_opaque_val);
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::setCtrlValueOperands(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, mlir::ValueRange replacements) {
  return static_cast<const ConcreteOp *>(impl)->setCtrlValueOperands(tablegen_opaque_val, replacements);
}
template<typename ConcreteOp>
mlir::ResultRange detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::getCtrlQubitResults(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getCtrlQubitResults(tablegen_opaque_val);
}
template<typename ConcreteOp>
bool detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::getAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getAdjointFlag(tablegen_opaque_val);
}
template<typename ConcreteOp>
void detail::QuantumGateInterfaceTraits::FallbackModel<ConcreteOp>::setAdjointFlag(const Concept *impl, ::mlir::Operation *tablegen_opaque_val, bool adjoint) {
  return static_cast<const ConcreteOp *>(impl)->setAdjointFlag(tablegen_opaque_val, adjoint);
}
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
template<typename ConcreteOp>
mlir::ValueRange detail::ParametrizedGateInterfaceTraits::Model<ConcreteOp>::getAllParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getAllParams();
}
template<typename ConcreteOp>
size_t detail::ParametrizedGateInterfaceTraits::Model<ConcreteOp>::getParamOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getParamOperandIdx();
}
template<typename ConcreteOp>
mlir::ValueRange detail::ParametrizedGateInterfaceTraits::FallbackModel<ConcreteOp>::getAllParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getAllParams(tablegen_opaque_val);
}
template<typename ConcreteOp>
size_t detail::ParametrizedGateInterfaceTraits::FallbackModel<ConcreteOp>::getParamOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getParamOperandIdx(tablegen_opaque_val);
}
template<typename ConcreteModel, typename ConcreteOp>
size_t detail::ParametrizedGateInterfaceTraits::ExternalModel<ConcreteModel, ConcreteOp>::getParamOperandIdx(::mlir::Operation *tablegen_opaque_val) const {
return 0;
}
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
template<typename ConcreteOp>
mlir::ValueRange detail::DifferentiableGateInterfaceTraits::Model<ConcreteOp>::getDiffParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getDiffParams();
}
template<typename ConcreteOp>
size_t detail::DifferentiableGateInterfaceTraits::Model<ConcreteOp>::getDiffOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getDiffOperandIdx();
}
template<typename ConcreteOp>
mlir::ValueRange detail::DifferentiableGateInterfaceTraits::FallbackModel<ConcreteOp>::getDiffParams(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getDiffParams(tablegen_opaque_val);
}
template<typename ConcreteOp>
size_t detail::DifferentiableGateInterfaceTraits::FallbackModel<ConcreteOp>::getDiffOperandIdx(const Concept *impl, ::mlir::Operation *tablegen_opaque_val) {
  return static_cast<const ConcreteOp *>(impl)->getDiffOperandIdx(tablegen_opaque_val);
}
template<typename ConcreteModel, typename ConcreteOp>
mlir::ValueRange detail::DifferentiableGateInterfaceTraits::ExternalModel<ConcreteModel, ConcreteOp>::getDiffParams(::mlir::Operation *tablegen_opaque_val) const {
return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getAllParams();
}
template<typename ConcreteModel, typename ConcreteOp>
size_t detail::DifferentiableGateInterfaceTraits::ExternalModel<ConcreteModel, ConcreteOp>::getDiffOperandIdx(::mlir::Operation *tablegen_opaque_val) const {
return (llvm::cast<ConcreteOp>(tablegen_opaque_val)).getParamOperandIdx();
}
} // namespace quantum
} // namespace catalyst
namespace catalyst {
namespace quantum {
} // namespace quantum
} // namespace catalyst
