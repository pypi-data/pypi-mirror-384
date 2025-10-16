/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Op Declarations                                                            *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: GradientOps.td                                                       *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace gradient {
/// Perform quantum AD using the adjoint method on a device.
class AdjointOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Perform classic automatic differentiation using Enzyme AD.
class BackpropOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Operation denoting the registration of the custom gradient with Enzyme.
/// A triple of three functions. The function itself, the forward and reverse pass.
class CustomGradOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Operation denoting the forward pass that is registered with Enzyme.
/// Wrapper around the concrete function. This wrapper ensures calling convention.
/// 
///     This function matches the expected calling convention from Enzyme.
///     Enzyme's calling convention expects a shadow argument for every pointer.
///     Since the callbacks all expect tensors, all of them are pointers.
///     Also, since the callbacks passes out parameters, then these are also duplicated.
/// 
///     After lowered to LLVM, this function will have the following parameters:
/// 
///     @foo(%inp0: !llvm.ptr, %diff0: !llvm.ptr,
///          ...
///          %inpArgc-1: !llvm.ptr, %diffArgc-1: !llvm.ptr,
///          %out0: !llvm.ptr, %cotangent0: !llvm.ptr,
///          ...
///          %outputResc-1: !llvm.ptr, %cotangentResc-1: !llvm.ptr)
/// 
///     The return value of enzyme is expected to be the tape.
///     Enzyme's documentation has the following to say:
/// 
///         The return type of the augmented forward pass is a struct type containing first the tape type,
///         followed by the original return type, if any.
///         If the return type is a duplicated type,
///         then there is a third argument which contains the shadow of the return.
/// 
///     Let's just break this down a bit:
/// 
///         The return type of the augmented forward pass is a struct type containing first the tape type,
/// 
///     This means that the return type for function foo will be the following in pseudocode
/// 
///         %tape0Type = { memref elements }
///         ...
///         %tapeTapec-1Type = { memref elements }
///         %tape = { %tape0Type, ... %tapeTapec-1Type }
///         %returnTy = { %tape, ... }
/// 
///     Then:
/// 
///         followed by the original return type, if any.
///     
///     since there is none, then:
/// 
///         %returnTy = { %tape }
/// 
///     Then:
/// 
///         If the return type is a duplicated type,
///         then there is a third argument which contains the shadow of the return.
/// 
///      this one is also nothing to worry for the current implementation because there are no returns.
/// 
///      One thing that was found experimentally and through tests in Enzyme is that the tape can also be a pointer.
///      We use this in the case when there is no tape to return. Instead of returning an empty struct, we return a null
///      pointer that is just never dereferenced.
class ForwardOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Compute the gradient of a function.
/// The `gradient.grad` operation computes the gradient of a function
///         using the finite difference method.
/// 
///         This operation acts much like the `func.call` operation, taking a
///         symbol reference and arguments to the original function as input.
///         However, instead of the function result, the gradient of the function
///         is returned.
/// 
///         Example:
/// 
///         ```mlir
///         func.func @foo(%arg0: f64) -> f64 {
///             %res = arith.mulf %arg0, %arg0 : f64
///             func.return %res : f64
///         }
/// 
///         %0 = arith.constant 2.0 : f64
///         %1 = gradient.grad @foo(%0) : (f64) -> f64
///         ```
class GradOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Compute the jvp of a function.
class JVPOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Return tapes or nothing
class ReturnOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Operation denoting the reverse pass that is registered with Enzyme.
/// Wrapper around the concrete function. This wrapper ensures calling convention.
/// 
///     This matches Enzyme's calling convention. From the documentation:
/// 
///         The final argument is a custom “tape” type that can be used to pass information from the forward to the reverse pass.
/// 
///     Experimentally, it looks like whenever there are no return values, the type passed to this function is the following type
///     which matches the return type of the forward op, but it is somewhat ambiguous with what it says in the documentation.
/// 
///         %returnTy = { %tape }
class ReverseOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Compute the vjp of a function.
class VJPOp;
} // namespace gradient
} // namespace catalyst
namespace catalyst {
namespace gradient {
/// Compute the value and gradient of a function.
class ValueAndGradOp;
} // namespace gradient
} // namespace catalyst
#ifdef GET_OP_CLASSES
#undef GET_OP_CLASSES

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::AdjointOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class AdjointOpGenericAdaptorBase {
public:
  struct Properties {
    using calleeTy = ::mlir::SymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::SymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::SymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using operandSegmentSizesTy = std::array<int32_t, 3>;
    operandSegmentSizesTy operandSegmentSizes;
    ::llvm::ArrayRef<int32_t> getOperandSegmentSizes() const {
      auto &propStorage = this->operandSegmentSizes;
      return propStorage;
    }
    void setOperandSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->operandSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.callee == this->callee &&
        rhs.operandSegmentSizes == this->operandSegmentSizes &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  AdjointOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.adjoint", odsAttrs.getContext());
  }

  AdjointOpGenericAdaptorBase(AdjointOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::SymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::mlir::SymbolRefAttr getCallee();
};
} // namespace detail
template <typename RangeT>
class AdjointOpGenericAdaptor : public detail::AdjointOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::AdjointOpGenericAdaptorBase;
public:
  AdjointOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  AdjointOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : AdjointOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  AdjointOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs) : AdjointOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  AdjointOpGenericAdaptor(RangeT values, const AdjointOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = AdjointOp, typename = std::enable_if_t<std::is_same_v<LateInst, AdjointOp>>>
  AdjointOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  ValueT getGradSize() {
    return (*getODSOperands(0).begin());
  }

  RangeT getArgs() {
    return getODSOperands(1);
  }

  RangeT getDataIn() {
    return getODSOperands(2);
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class AdjointOpAdaptor : public AdjointOpGenericAdaptor<::mlir::ValueRange> {
public:
  using AdjointOpGenericAdaptor::AdjointOpGenericAdaptor;
  AdjointOpAdaptor(AdjointOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class AdjointOp : public ::mlir::Op<AdjointOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::VariadicResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::AtLeastNOperands<1>::Impl, ::mlir::OpTrait::AttrSizedOperandSegments, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = AdjointOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = AdjointOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("callee"), ::llvm::StringRef("operandSegmentSizes")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getOperandSegmentSizesAttrName() {
   return (*this)->getName().getAttributeNames().back();
  }

  static ::mlir::StringAttr getOperandSegmentSizesAttrName(::mlir::OperationName name) {
   return name.getAttributeNames().back();
  }

  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.adjoint");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::TypedValue<::mlir::IndexType> getGradSize() {
    return ::llvm::cast<::mlir::TypedValue<::mlir::IndexType>>(*getODSOperands(0).begin());
  }

  ::mlir::Operation::operand_range getArgs() {
    return getODSOperands(1);
  }

  ::mlir::Operation::operand_range getDataIn() {
    return getODSOperands(2);
  }

  ::mlir::OpOperand &getGradSizeMutable() {
    auto range = getODSOperandIndexAndLength(0);
    return getOperation()->getOpOperand(range.first);
  }

  ::mlir::MutableOperandRange getArgsMutable();
  ::mlir::MutableOperandRange getDataInMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index);
  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::SymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
  }

  ::mlir::SymbolRefAttr getCallee();
  void setCalleeAttr(::mlir::SymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultType0, ::mlir::SymbolRefAttr callee, ::mlir::Value gradSize, ::mlir::ValueRange args, ::mlir::ValueRange data_in);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 1 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::AdjointOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::BackpropOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class BackpropOpGenericAdaptorBase {
public:
  struct Properties {
    using calleeTy = ::mlir::SymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::SymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::SymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using diffArgIndicesTy = ::mlir::DenseIntElementsAttr;
    diffArgIndicesTy diffArgIndices;

    auto getDiffArgIndices() const {
      auto &propStorage = this->diffArgIndices;
      return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(propStorage);
    }
    void setDiffArgIndices(const ::mlir::DenseIntElementsAttr &propValue) {
      this->diffArgIndices = propValue;
    }
    using keepValueResultsTy = ::mlir::BoolAttr;
    keepValueResultsTy keepValueResults;

    auto getKeepValueResults() const {
      auto &propStorage = this->keepValueResults;
      return ::llvm::dyn_cast_or_null<::mlir::BoolAttr>(propStorage);
    }
    void setKeepValueResults(const ::mlir::BoolAttr &propValue) {
      this->keepValueResults = propValue;
    }
    using operandSegmentSizesTy = std::array<int32_t, 4>;
    operandSegmentSizesTy operandSegmentSizes;
    ::llvm::ArrayRef<int32_t> getOperandSegmentSizes() const {
      auto &propStorage = this->operandSegmentSizes;
      return propStorage;
    }
    void setOperandSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->operandSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    using resultSegmentSizesTy = std::array<int32_t, 2>;
    resultSegmentSizesTy resultSegmentSizes;
    ::llvm::ArrayRef<int32_t> getResultSegmentSizes() const {
      auto &propStorage = this->resultSegmentSizes;
      return propStorage;
    }
    void setResultSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->resultSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.callee == this->callee &&
        rhs.diffArgIndices == this->diffArgIndices &&
        rhs.keepValueResults == this->keepValueResults &&
        rhs.operandSegmentSizes == this->operandSegmentSizes &&
        rhs.resultSegmentSizes == this->resultSegmentSizes &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  BackpropOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.backprop", odsAttrs.getContext());
  }

  BackpropOpGenericAdaptorBase(BackpropOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::SymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
    return attr;
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::BoolAttr getKeepValueResultsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::BoolAttr>(getProperties().keepValueResults);
    return attr;
  }

  ::std::optional< bool > getKeepValueResults();
};
} // namespace detail
template <typename RangeT>
class BackpropOpGenericAdaptor : public detail::BackpropOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::BackpropOpGenericAdaptorBase;
public:
  BackpropOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  BackpropOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : BackpropOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  BackpropOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs) : BackpropOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  BackpropOpGenericAdaptor(RangeT values, const BackpropOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = BackpropOp, typename = std::enable_if_t<std::is_same_v<LateInst, BackpropOp>>>
  BackpropOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getArgs() {
    return getODSOperands(0);
  }

  RangeT getDiffArgShadows() {
    return getODSOperands(1);
  }

  RangeT getCalleeResults() {
    return getODSOperands(2);
  }

  RangeT getCotangents() {
    return getODSOperands(3);
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class BackpropOpAdaptor : public BackpropOpGenericAdaptor<::mlir::ValueRange> {
public:
  using BackpropOpGenericAdaptor::BackpropOpGenericAdaptor;
  BackpropOpAdaptor(BackpropOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class BackpropOp : public ::mlir::Op<BackpropOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::VariadicResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::VariadicOperands, ::mlir::OpTrait::AttrSizedOperandSegments, ::mlir::OpTrait::AttrSizedResultSegments, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::SymbolUserOpInterface::Trait, ::mlir::OpAsmOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = BackpropOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = BackpropOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("callee"), ::llvm::StringRef("diffArgIndices"), ::llvm::StringRef("keepValueResults"), ::llvm::StringRef("operandSegmentSizes")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getDiffArgIndicesAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getDiffArgIndicesAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getKeepValueResultsAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getKeepValueResultsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getOperandSegmentSizesAttrName() {
   return (*this)->getName().getAttributeNames().back();
  }

  static ::mlir::StringAttr getOperandSegmentSizesAttrName(::mlir::OperationName name) {
   return name.getAttributeNames().back();
  }

  void getAsmResultNames(::mlir::OpAsmSetValueNameFn setNameFn);
  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.backprop");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::operand_range getArgs() {
    return getODSOperands(0);
  }

  ::mlir::Operation::operand_range getDiffArgShadows() {
    return getODSOperands(1);
  }

  ::mlir::Operation::operand_range getCalleeResults() {
    return getODSOperands(2);
  }

  ::mlir::Operation::operand_range getCotangents() {
    return getODSOperands(3);
  }

  ::mlir::MutableOperandRange getArgsMutable();
  ::mlir::MutableOperandRange getDiffArgShadowsMutable();
  ::mlir::MutableOperandRange getCalleeResultsMutable();
  ::mlir::MutableOperandRange getCotangentsMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index);
  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::result_range getVals() {
    return getODSResults(0);
  }

  ::mlir::Operation::result_range getGradients() {
    return getODSResults(1);
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::SymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::BoolAttr getKeepValueResultsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::BoolAttr>(getProperties().keepValueResults);
  }

  ::std::optional< bool > getKeepValueResults();
  void setCalleeAttr(::mlir::SymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  void setDiffArgIndicesAttr(::mlir::DenseIntElementsAttr attr) {
    getProperties().diffArgIndices = attr;
  }

  void setKeepValueResultsAttr(::mlir::BoolAttr attr) {
    getProperties().keepValueResults = attr;
  }

  void setKeepValueResults(::std::optional<bool> attrValue);
  ::mlir::Attribute removeDiffArgIndicesAttr() {
      auto attr = getProperties().diffArgIndices;
      getProperties().diffArgIndices = {};
      return attr;
  }

  ::mlir::Attribute removeKeepValueResultsAttr() {
      auto attr = getProperties().keepValueResults;
      getProperties().keepValueResults = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange vals, ::mlir::TypeRange gradients, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange args, ::mlir::ValueRange diffArgShadows, ::mlir::ValueRange calleeResults, ::mlir::ValueRange cotangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::BoolAttr keepValueResults);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange args, ::mlir::ValueRange diffArgShadows, ::mlir::ValueRange calleeResults, ::mlir::ValueRange cotangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::BoolAttr keepValueResults);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::llvm::LogicalResult verify();
  ::llvm::LogicalResult verifySymbolUses(::mlir::SymbolTableCollection &symbolTable);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 3 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::BackpropOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::CustomGradOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class CustomGradOpGenericAdaptorBase {
public:
  struct Properties {
    using calleeTy = ::mlir::FlatSymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::FlatSymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::FlatSymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using forwardTy = ::mlir::FlatSymbolRefAttr;
    forwardTy forward;

    auto getForward() const {
      auto &propStorage = this->forward;
      return ::llvm::cast<::mlir::FlatSymbolRefAttr>(propStorage);
    }
    void setForward(const ::mlir::FlatSymbolRefAttr &propValue) {
      this->forward = propValue;
    }
    using reverseTy = ::mlir::FlatSymbolRefAttr;
    reverseTy reverse;

    auto getReverse() const {
      auto &propStorage = this->reverse;
      return ::llvm::cast<::mlir::FlatSymbolRefAttr>(propStorage);
    }
    void setReverse(const ::mlir::FlatSymbolRefAttr &propValue) {
      this->reverse = propValue;
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.callee == this->callee &&
        rhs.forward == this->forward &&
        rhs.reverse == this->reverse &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  CustomGradOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.custom_grad", odsAttrs.getContext());
  }

  CustomGradOpGenericAdaptorBase(CustomGradOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize) {
    return {index, 1};
  }

  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::FlatSymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::llvm::StringRef getCallee();
  ::mlir::FlatSymbolRefAttr getForwardAttr() {
    auto attr = ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().forward);
    return attr;
  }

  ::llvm::StringRef getForward();
  ::mlir::FlatSymbolRefAttr getReverseAttr() {
    auto attr = ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().reverse);
    return attr;
  }

  ::llvm::StringRef getReverse();
};
} // namespace detail
template <typename RangeT>
class CustomGradOpGenericAdaptor : public detail::CustomGradOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::CustomGradOpGenericAdaptorBase;
public:
  CustomGradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  CustomGradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : CustomGradOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  CustomGradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs = nullptr) : CustomGradOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  CustomGradOpGenericAdaptor(RangeT values, const CustomGradOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = CustomGradOp, typename = std::enable_if_t<std::is_same_v<LateInst, CustomGradOp>>>
  CustomGradOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class CustomGradOpAdaptor : public CustomGradOpGenericAdaptor<::mlir::ValueRange> {
public:
  using CustomGradOpGenericAdaptor::CustomGradOpGenericAdaptor;
  CustomGradOpAdaptor(CustomGradOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class CustomGradOp : public ::mlir::Op<CustomGradOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::ZeroResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::ZeroOperands, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::SymbolUserOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = CustomGradOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = CustomGradOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("callee"), ::llvm::StringRef("forward"), ::llvm::StringRef("reverse")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getForwardAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getForwardAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getReverseAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getReverseAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.custom_grad");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::FlatSymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().callee);
  }

  ::llvm::StringRef getCallee();
  ::mlir::FlatSymbolRefAttr getForwardAttr() {
    return ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().forward);
  }

  ::llvm::StringRef getForward();
  ::mlir::FlatSymbolRefAttr getReverseAttr() {
    return ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().reverse);
  }

  ::llvm::StringRef getReverse();
  void setCalleeAttr(::mlir::FlatSymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  void setCallee(::llvm::StringRef attrValue);
  void setForwardAttr(::mlir::FlatSymbolRefAttr attr) {
    getProperties().forward = attr;
  }

  void setForward(::llvm::StringRef attrValue);
  void setReverseAttr(::mlir::FlatSymbolRefAttr attr) {
    getProperties().reverse = attr;
  }

  void setReverse(::llvm::StringRef attrValue);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::FlatSymbolRefAttr callee, ::mlir::FlatSymbolRefAttr forward, ::mlir::FlatSymbolRefAttr reverse);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::FlatSymbolRefAttr callee, ::mlir::FlatSymbolRefAttr forward, ::mlir::FlatSymbolRefAttr reverse);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::llvm::StringRef callee, ::llvm::StringRef forward, ::llvm::StringRef reverse);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::llvm::StringRef callee, ::llvm::StringRef forward, ::llvm::StringRef reverse);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::llvm::LogicalResult verifySymbolUses(::mlir::SymbolTableCollection &symbolTable);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 3 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::CustomGradOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::ForwardOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class ForwardOpGenericAdaptorBase {
public:
  struct Properties {
    using arg_attrsTy = ::mlir::ArrayAttr;
    arg_attrsTy arg_attrs;

    auto getArgAttrs() const {
      auto &propStorage = this->arg_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setArgAttrs(const ::mlir::ArrayAttr &propValue) {
      this->arg_attrs = propValue;
    }
    using argcTy = ::mlir::IntegerAttr;
    argcTy argc;

    auto getArgc() const {
      auto &propStorage = this->argc;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setArgc(const ::mlir::IntegerAttr &propValue) {
      this->argc = propValue;
    }
    using function_typeTy = ::mlir::TypeAttr;
    function_typeTy function_type;

    auto getFunctionType() const {
      auto &propStorage = this->function_type;
      return ::llvm::cast<::mlir::TypeAttr>(propStorage);
    }
    void setFunctionType(const ::mlir::TypeAttr &propValue) {
      this->function_type = propValue;
    }
    using implementationTy = ::mlir::FlatSymbolRefAttr;
    implementationTy implementation;

    auto getImplementation() const {
      auto &propStorage = this->implementation;
      return ::llvm::cast<::mlir::FlatSymbolRefAttr>(propStorage);
    }
    void setImplementation(const ::mlir::FlatSymbolRefAttr &propValue) {
      this->implementation = propValue;
    }
    using res_attrsTy = ::mlir::ArrayAttr;
    res_attrsTy res_attrs;

    auto getResAttrs() const {
      auto &propStorage = this->res_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setResAttrs(const ::mlir::ArrayAttr &propValue) {
      this->res_attrs = propValue;
    }
    using rescTy = ::mlir::IntegerAttr;
    rescTy resc;

    auto getResc() const {
      auto &propStorage = this->resc;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setResc(const ::mlir::IntegerAttr &propValue) {
      this->resc = propValue;
    }
    using sym_nameTy = ::mlir::StringAttr;
    sym_nameTy sym_name;

    auto getSymName() const {
      auto &propStorage = this->sym_name;
      return ::llvm::cast<::mlir::StringAttr>(propStorage);
    }
    void setSymName(const ::mlir::StringAttr &propValue) {
      this->sym_name = propValue;
    }
    using tapeTy = ::mlir::IntegerAttr;
    tapeTy tape;

    auto getTape() const {
      auto &propStorage = this->tape;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setTape(const ::mlir::IntegerAttr &propValue) {
      this->tape = propValue;
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.arg_attrs == this->arg_attrs &&
        rhs.argc == this->argc &&
        rhs.function_type == this->function_type &&
        rhs.implementation == this->implementation &&
        rhs.res_attrs == this->res_attrs &&
        rhs.resc == this->resc &&
        rhs.sym_name == this->sym_name &&
        rhs.tape == this->tape &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  ForwardOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.forward", odsAttrs.getContext());
  }

  ForwardOpGenericAdaptorBase(ForwardOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize) {
    return {index, 1};
  }

  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::StringAttr getSymNameAttr() {
    auto attr = ::llvm::cast<::mlir::StringAttr>(getProperties().sym_name);
    return attr;
  }

  ::llvm::StringRef getSymName();
  ::mlir::TypeAttr getFunctionTypeAttr() {
    auto attr = ::llvm::cast<::mlir::TypeAttr>(getProperties().function_type);
    return attr;
  }

  ::mlir::FunctionType getFunctionType();
  ::mlir::FlatSymbolRefAttr getImplementationAttr() {
    auto attr = ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().implementation);
    return attr;
  }

  ::llvm::StringRef getImplementation();
  ::mlir::IntegerAttr getArgcAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().argc);
    return attr;
  }

  uint64_t getArgc();
  ::mlir::IntegerAttr getRescAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().resc);
    return attr;
  }

  uint64_t getResc();
  ::mlir::IntegerAttr getTapeAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().tape);
    return attr;
  }

  uint64_t getTape();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  ::mlir::Region &getBody() {
    return *odsRegions[0];
  }

  ::mlir::RegionRange getRegions() {
    return odsRegions;
  }

};
} // namespace detail
template <typename RangeT>
class ForwardOpGenericAdaptor : public detail::ForwardOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::ForwardOpGenericAdaptorBase;
public:
  ForwardOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  ForwardOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : ForwardOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  ForwardOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs = nullptr) : ForwardOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  ForwardOpGenericAdaptor(RangeT values, const ForwardOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = ForwardOp, typename = std::enable_if_t<std::is_same_v<LateInst, ForwardOp>>>
  ForwardOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class ForwardOpAdaptor : public ForwardOpGenericAdaptor<::mlir::ValueRange> {
public:
  using ForwardOpGenericAdaptor::ForwardOpGenericAdaptor;
  ForwardOpAdaptor(ForwardOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class ForwardOp : public ::mlir::Op<ForwardOp, ::mlir::OpTrait::OneRegion, ::mlir::OpTrait::ZeroResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::ZeroOperands, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::SymbolOpInterface::Trait, ::mlir::CallableOpInterface::Trait, ::mlir::FunctionOpInterface::Trait, ::mlir::OpTrait::IsIsolatedFromAbove> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = ForwardOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = ForwardOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("arg_attrs"), ::llvm::StringRef("argc"), ::llvm::StringRef("function_type"), ::llvm::StringRef("implementation"), ::llvm::StringRef("res_attrs"), ::llvm::StringRef("resc"), ::llvm::StringRef("sym_name"), ::llvm::StringRef("tape")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getArgAttrsAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getArgAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getArgcAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getArgcAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getFunctionTypeAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getFunctionTypeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getImplementationAttrName() {
    return getAttributeNameForIndex(3);
  }

  static ::mlir::StringAttr getImplementationAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 3);
  }

  ::mlir::StringAttr getResAttrsAttrName() {
    return getAttributeNameForIndex(4);
  }

  static ::mlir::StringAttr getResAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 4);
  }

  ::mlir::StringAttr getRescAttrName() {
    return getAttributeNameForIndex(5);
  }

  static ::mlir::StringAttr getRescAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 5);
  }

  ::mlir::StringAttr getSymNameAttrName() {
    return getAttributeNameForIndex(6);
  }

  static ::mlir::StringAttr getSymNameAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 6);
  }

  ::mlir::StringAttr getTapeAttrName() {
    return getAttributeNameForIndex(7);
  }

  static ::mlir::StringAttr getTapeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 7);
  }

  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.forward");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Region &getBody() {
    return (*this)->getRegion(0);
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::StringAttr getSymNameAttr() {
    return ::llvm::cast<::mlir::StringAttr>(getProperties().sym_name);
  }

  ::llvm::StringRef getSymName();
  ::mlir::TypeAttr getFunctionTypeAttr() {
    return ::llvm::cast<::mlir::TypeAttr>(getProperties().function_type);
  }

  ::mlir::FunctionType getFunctionType();
  ::mlir::FlatSymbolRefAttr getImplementationAttr() {
    return ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().implementation);
  }

  ::llvm::StringRef getImplementation();
  ::mlir::IntegerAttr getArgcAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().argc);
  }

  uint64_t getArgc();
  ::mlir::IntegerAttr getRescAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().resc);
  }

  uint64_t getResc();
  ::mlir::IntegerAttr getTapeAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().tape);
  }

  uint64_t getTape();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  void setSymNameAttr(::mlir::StringAttr attr) {
    getProperties().sym_name = attr;
  }

  void setSymName(::llvm::StringRef attrValue);
  void setFunctionTypeAttr(::mlir::TypeAttr attr) {
    getProperties().function_type = attr;
  }

  void setFunctionType(::mlir::FunctionType attrValue);
  void setImplementationAttr(::mlir::FlatSymbolRefAttr attr) {
    getProperties().implementation = attr;
  }

  void setImplementation(::llvm::StringRef attrValue);
  void setArgcAttr(::mlir::IntegerAttr attr) {
    getProperties().argc = attr;
  }

  void setArgc(uint64_t attrValue);
  void setRescAttr(::mlir::IntegerAttr attr) {
    getProperties().resc = attr;
  }

  void setResc(uint64_t attrValue);
  void setTapeAttr(::mlir::IntegerAttr attr) {
    getProperties().tape = attr;
  }

  void setTape(uint64_t attrValue);
  void setArgAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().arg_attrs = attr;
  }

  void setResAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().res_attrs = attr;
  }

  ::mlir::Attribute removeArgAttrsAttr() {
      auto attr = getProperties().arg_attrs;
      getProperties().arg_attrs = {};
      return attr;
  }

  ::mlir::Attribute removeResAttrsAttr() {
      auto attr = getProperties().res_attrs;
      getProperties().res_attrs = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, mlir::StringRef name, mlir::FunctionType type, mlir::ArrayRef<mlir::NamedAttribute> attrs = {});
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &p);
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 8 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
  //===------------------------------------------------------------------===//
  // FunctionOpInterface Methods
  //===------------------------------------------------------------------===//

  /// Returns the argument types of this function.
  mlir::ArrayRef<mlir::Type> getArgumentTypes() { return getFunctionType().getInputs(); }

  /// Returns the result types of this function.
  mlir::ArrayRef<mlir::Type> getResultTypes() { return getFunctionType().getResults(); }

  mlir::Region *getCallableRegion() { return &getBody(); }
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::ForwardOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::GradOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class GradOpGenericAdaptorBase {
public:
  struct Properties {
    using arg_attrsTy = ::mlir::ArrayAttr;
    arg_attrsTy arg_attrs;

    auto getArgAttrs() const {
      auto &propStorage = this->arg_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setArgAttrs(const ::mlir::ArrayAttr &propValue) {
      this->arg_attrs = propValue;
    }
    using calleeTy = ::mlir::SymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::SymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::SymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using diffArgIndicesTy = ::mlir::DenseIntElementsAttr;
    diffArgIndicesTy diffArgIndices;

    auto getDiffArgIndices() const {
      auto &propStorage = this->diffArgIndices;
      return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(propStorage);
    }
    void setDiffArgIndices(const ::mlir::DenseIntElementsAttr &propValue) {
      this->diffArgIndices = propValue;
    }
    using finiteDiffParamTy = ::mlir::FloatAttr;
    finiteDiffParamTy finiteDiffParam;

    auto getFiniteDiffParam() const {
      auto &propStorage = this->finiteDiffParam;
      return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(propStorage);
    }
    void setFiniteDiffParam(const ::mlir::FloatAttr &propValue) {
      this->finiteDiffParam = propValue;
    }
    using methodTy = ::mlir::StringAttr;
    methodTy method;

    auto getMethod() const {
      auto &propStorage = this->method;
      return ::llvm::cast<::mlir::StringAttr>(propStorage);
    }
    void setMethod(const ::mlir::StringAttr &propValue) {
      this->method = propValue;
    }
    using res_attrsTy = ::mlir::ArrayAttr;
    res_attrsTy res_attrs;

    auto getResAttrs() const {
      auto &propStorage = this->res_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setResAttrs(const ::mlir::ArrayAttr &propValue) {
      this->res_attrs = propValue;
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.arg_attrs == this->arg_attrs &&
        rhs.callee == this->callee &&
        rhs.diffArgIndices == this->diffArgIndices &&
        rhs.finiteDiffParam == this->finiteDiffParam &&
        rhs.method == this->method &&
        rhs.res_attrs == this->res_attrs &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  GradOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.grad", odsAttrs.getContext());
  }

  GradOpGenericAdaptorBase(GradOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::StringAttr getMethodAttr() {
    auto attr = ::llvm::cast<::mlir::StringAttr>(getProperties().method);
    return attr;
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
    return attr;
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
    return attr;
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
};
} // namespace detail
template <typename RangeT>
class GradOpGenericAdaptor : public detail::GradOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::GradOpGenericAdaptorBase;
public:
  GradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  GradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : GradOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  GradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs = nullptr) : GradOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  GradOpGenericAdaptor(RangeT values, const GradOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = GradOp, typename = std::enable_if_t<std::is_same_v<LateInst, GradOp>>>
  GradOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getOperands() {
    return getODSOperands(0);
  }

private:
  RangeT odsOperands;
};
class GradOpAdaptor : public GradOpGenericAdaptor<::mlir::ValueRange> {
public:
  using GradOpGenericAdaptor::GradOpGenericAdaptor;
  GradOpAdaptor(GradOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class GradOp : public ::mlir::Op<GradOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::VariadicResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::VariadicOperands, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::CallOpInterface::Trait, ::mlir::SymbolUserOpInterface::Trait, ::catalyst::gradient::GradientOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = GradOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = GradOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("arg_attrs"), ::llvm::StringRef("callee"), ::llvm::StringRef("diffArgIndices"), ::llvm::StringRef("finiteDiffParam"), ::llvm::StringRef("method"), ::llvm::StringRef("res_attrs")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getArgAttrsAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getArgAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getDiffArgIndicesAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getDiffArgIndicesAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getFiniteDiffParamAttrName() {
    return getAttributeNameForIndex(3);
  }

  static ::mlir::StringAttr getFiniteDiffParamAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 3);
  }

  ::mlir::StringAttr getMethodAttrName() {
    return getAttributeNameForIndex(4);
  }

  static ::mlir::StringAttr getMethodAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 4);
  }

  ::mlir::StringAttr getResAttrsAttrName() {
    return getAttributeNameForIndex(5);
  }

  static ::mlir::StringAttr getResAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 5);
  }

  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.grad");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::operand_range getOperands() {
    return getODSOperands(0);
  }

  ::mlir::MutableOperandRange getOperandsMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index);
  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::StringAttr getMethodAttr() {
    return ::llvm::cast<::mlir::StringAttr>(getProperties().method);
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  void setMethodAttr(::mlir::StringAttr attr) {
    getProperties().method = attr;
  }

  void setMethod(::llvm::StringRef attrValue);
  void setCalleeAttr(::mlir::SymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  void setDiffArgIndicesAttr(::mlir::DenseIntElementsAttr attr) {
    getProperties().diffArgIndices = attr;
  }

  void setFiniteDiffParamAttr(::mlir::FloatAttr attr) {
    getProperties().finiteDiffParam = attr;
  }

  void setArgAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().arg_attrs = attr;
  }

  void setResAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().res_attrs = attr;
  }

  ::mlir::Attribute removeDiffArgIndicesAttr() {
      auto attr = getProperties().diffArgIndices;
      getProperties().diffArgIndices = {};
      return attr;
  }

  ::mlir::Attribute removeFiniteDiffParamAttr() {
      auto attr = getProperties().finiteDiffParam;
      getProperties().finiteDiffParam = {};
      return attr;
  }

  ::mlir::Attribute removeArgAttrsAttr() {
      auto attr = getProperties().arg_attrs;
      getProperties().arg_attrs = {};
      return attr;
  }

  ::mlir::Attribute removeResAttrsAttr() {
      auto attr = getProperties().res_attrs;
      getProperties().res_attrs = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultType0, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange operands, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultType0, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange operands, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::llvm::LogicalResult verify();
  ::mlir::CallInterfaceCallable getCallableForCallee();
  void setCalleeFromCallable(::mlir::CallInterfaceCallable callee);
  ::mlir::Operation::operand_range getArgOperands();
  ::mlir::MutableOperandRange getArgOperandsMutable();
  ::llvm::LogicalResult verifySymbolUses(::mlir::SymbolTableCollection &symbolTable);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 6 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::GradOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::JVPOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class JVPOpGenericAdaptorBase {
public:
  struct Properties {
    using arg_attrsTy = ::mlir::ArrayAttr;
    arg_attrsTy arg_attrs;

    auto getArgAttrs() const {
      auto &propStorage = this->arg_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setArgAttrs(const ::mlir::ArrayAttr &propValue) {
      this->arg_attrs = propValue;
    }
    using calleeTy = ::mlir::SymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::SymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::SymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using diffArgIndicesTy = ::mlir::DenseIntElementsAttr;
    diffArgIndicesTy diffArgIndices;

    auto getDiffArgIndices() const {
      auto &propStorage = this->diffArgIndices;
      return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(propStorage);
    }
    void setDiffArgIndices(const ::mlir::DenseIntElementsAttr &propValue) {
      this->diffArgIndices = propValue;
    }
    using finiteDiffParamTy = ::mlir::FloatAttr;
    finiteDiffParamTy finiteDiffParam;

    auto getFiniteDiffParam() const {
      auto &propStorage = this->finiteDiffParam;
      return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(propStorage);
    }
    void setFiniteDiffParam(const ::mlir::FloatAttr &propValue) {
      this->finiteDiffParam = propValue;
    }
    using methodTy = ::mlir::StringAttr;
    methodTy method;

    auto getMethod() const {
      auto &propStorage = this->method;
      return ::llvm::cast<::mlir::StringAttr>(propStorage);
    }
    void setMethod(const ::mlir::StringAttr &propValue) {
      this->method = propValue;
    }
    using res_attrsTy = ::mlir::ArrayAttr;
    res_attrsTy res_attrs;

    auto getResAttrs() const {
      auto &propStorage = this->res_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setResAttrs(const ::mlir::ArrayAttr &propValue) {
      this->res_attrs = propValue;
    }
    using operandSegmentSizesTy = std::array<int32_t, 2>;
    operandSegmentSizesTy operandSegmentSizes;
    ::llvm::ArrayRef<int32_t> getOperandSegmentSizes() const {
      auto &propStorage = this->operandSegmentSizes;
      return propStorage;
    }
    void setOperandSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->operandSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.arg_attrs == this->arg_attrs &&
        rhs.callee == this->callee &&
        rhs.diffArgIndices == this->diffArgIndices &&
        rhs.finiteDiffParam == this->finiteDiffParam &&
        rhs.method == this->method &&
        rhs.res_attrs == this->res_attrs &&
        rhs.operandSegmentSizes == this->operandSegmentSizes &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  JVPOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.jvp", odsAttrs.getContext());
  }

  JVPOpGenericAdaptorBase(JVPOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::StringAttr getMethodAttr() {
    auto attr = ::llvm::cast<::mlir::StringAttr>(getProperties().method);
    return attr;
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
    return attr;
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
    return attr;
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
};
} // namespace detail
template <typename RangeT>
class JVPOpGenericAdaptor : public detail::JVPOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::JVPOpGenericAdaptorBase;
public:
  JVPOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  JVPOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : JVPOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  JVPOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs) : JVPOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  JVPOpGenericAdaptor(RangeT values, const JVPOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = JVPOp, typename = std::enable_if_t<std::is_same_v<LateInst, JVPOp>>>
  JVPOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getParams() {
    return getODSOperands(0);
  }

  RangeT getTangents() {
    return getODSOperands(1);
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class JVPOpAdaptor : public JVPOpGenericAdaptor<::mlir::ValueRange> {
public:
  using JVPOpGenericAdaptor::JVPOpGenericAdaptor;
  JVPOpAdaptor(JVPOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class JVPOp : public ::mlir::Op<JVPOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::VariadicResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::VariadicOperands, ::mlir::OpTrait::AttrSizedOperandSegments, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::CallOpInterface::Trait, ::mlir::SymbolUserOpInterface::Trait, ::catalyst::gradient::GradientOpInterface::Trait, ::mlir::OpAsmOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = JVPOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = JVPOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("arg_attrs"), ::llvm::StringRef("callee"), ::llvm::StringRef("diffArgIndices"), ::llvm::StringRef("finiteDiffParam"), ::llvm::StringRef("method"), ::llvm::StringRef("res_attrs"), ::llvm::StringRef("operandSegmentSizes")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getArgAttrsAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getArgAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getDiffArgIndicesAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getDiffArgIndicesAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getFiniteDiffParamAttrName() {
    return getAttributeNameForIndex(3);
  }

  static ::mlir::StringAttr getFiniteDiffParamAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 3);
  }

  ::mlir::StringAttr getMethodAttrName() {
    return getAttributeNameForIndex(4);
  }

  static ::mlir::StringAttr getMethodAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 4);
  }

  ::mlir::StringAttr getResAttrsAttrName() {
    return getAttributeNameForIndex(5);
  }

  static ::mlir::StringAttr getResAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 5);
  }

  ::mlir::StringAttr getOperandSegmentSizesAttrName() {
   return (*this)->getName().getAttributeNames().back();
  }

  static ::mlir::StringAttr getOperandSegmentSizesAttrName(::mlir::OperationName name) {
   return name.getAttributeNames().back();
  }

  void getAsmResultNames(::mlir::OpAsmSetValueNameFn setNameFn);
  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.jvp");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::operand_range getParams() {
    return getODSOperands(0);
  }

  ::mlir::Operation::operand_range getTangents() {
    return getODSOperands(1);
  }

  ::mlir::MutableOperandRange getParamsMutable();
  ::mlir::MutableOperandRange getTangentsMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index);
  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::result_range getCalleeResults() {
    return getODSResults(0);
  }

  ::mlir::Operation::result_range getJvps() {
    return getODSResults(1);
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::StringAttr getMethodAttr() {
    return ::llvm::cast<::mlir::StringAttr>(getProperties().method);
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  void setMethodAttr(::mlir::StringAttr attr) {
    getProperties().method = attr;
  }

  void setMethod(::llvm::StringRef attrValue);
  void setCalleeAttr(::mlir::SymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  void setDiffArgIndicesAttr(::mlir::DenseIntElementsAttr attr) {
    getProperties().diffArgIndices = attr;
  }

  void setFiniteDiffParamAttr(::mlir::FloatAttr attr) {
    getProperties().finiteDiffParam = attr;
  }

  void setArgAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().arg_attrs = attr;
  }

  void setResAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().res_attrs = attr;
  }

  ::mlir::Attribute removeDiffArgIndicesAttr() {
      auto attr = getProperties().diffArgIndices;
      getProperties().diffArgIndices = {};
      return attr;
  }

  ::mlir::Attribute removeFiniteDiffParamAttr() {
      auto attr = getProperties().finiteDiffParam;
      getProperties().finiteDiffParam = {};
      return attr;
  }

  ::mlir::Attribute removeArgAttrsAttr() {
      auto attr = getProperties().arg_attrs;
      getProperties().arg_attrs = {};
      return attr;
  }

  ::mlir::Attribute removeResAttrsAttr() {
      auto attr = getProperties().res_attrs;
      getProperties().res_attrs = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange calleeResults, ::mlir::TypeRange jvps, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange tangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange tangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange calleeResults, ::mlir::TypeRange jvps, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange tangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange tangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::llvm::LogicalResult verify();
  ::mlir::CallInterfaceCallable getCallableForCallee();
  void setCalleeFromCallable(::mlir::CallInterfaceCallable callee);
  ::mlir::Operation::operand_range getArgOperands();
  ::mlir::MutableOperandRange getArgOperandsMutable();
  ::llvm::LogicalResult verifySymbolUses(::mlir::SymbolTableCollection &symbolTable);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 6 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::JVPOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::ReturnOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class ReturnOpGenericAdaptorBase {
public:
  struct Properties {
    using emptyTy = ::mlir::IntegerAttr;
    emptyTy empty;

    auto getEmpty() const {
      auto &propStorage = this->empty;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setEmpty(const ::mlir::IntegerAttr &propValue) {
      this->empty = propValue;
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.empty == this->empty &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  ReturnOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.return", odsAttrs.getContext());
  }

  ReturnOpGenericAdaptorBase(ReturnOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::IntegerAttr getEmptyAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().empty);
    return attr;
  }

  bool getEmpty();
};
} // namespace detail
template <typename RangeT>
class ReturnOpGenericAdaptor : public detail::ReturnOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::ReturnOpGenericAdaptorBase;
public:
  ReturnOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  ReturnOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : ReturnOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  ReturnOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs = nullptr) : ReturnOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  ReturnOpGenericAdaptor(RangeT values, const ReturnOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = ReturnOp, typename = std::enable_if_t<std::is_same_v<LateInst, ReturnOp>>>
  ReturnOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getTape() {
    return getODSOperands(0);
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class ReturnOpAdaptor : public ReturnOpGenericAdaptor<::mlir::ValueRange> {
public:
  using ReturnOpGenericAdaptor::ReturnOpGenericAdaptor;
  ReturnOpAdaptor(ReturnOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class ReturnOp : public ::mlir::Op<ReturnOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::ZeroResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::VariadicOperands, ::mlir::OpTrait::HasParent<ForwardOp, ReverseOp>::Impl, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::RegionBranchTerminatorOpInterface::Trait, ::mlir::OpTrait::ReturnLike, ::mlir::OpTrait::IsTerminator> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = ReturnOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = ReturnOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("empty")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getEmptyAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getEmptyAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.return");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::operand_range getTape() {
    return getODSOperands(0);
  }

  ::mlir::MutableOperandRange getTapeMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::IntegerAttr getEmptyAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().empty);
  }

  bool getEmpty();
  void setEmptyAttr(::mlir::IntegerAttr attr) {
    getProperties().empty = attr;
  }

  void setEmpty(bool attrValue);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::ValueRange tape, ::mlir::IntegerAttr empty);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange tape, ::mlir::IntegerAttr empty);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::ValueRange tape, bool empty);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange tape, bool empty);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::mlir::MutableOperandRange getMutableSuccessorOperands(::mlir::RegionBranchPoint point);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 1 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::ReturnOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::ReverseOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class ReverseOpGenericAdaptorBase {
public:
  struct Properties {
    using arg_attrsTy = ::mlir::ArrayAttr;
    arg_attrsTy arg_attrs;

    auto getArgAttrs() const {
      auto &propStorage = this->arg_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setArgAttrs(const ::mlir::ArrayAttr &propValue) {
      this->arg_attrs = propValue;
    }
    using argcTy = ::mlir::IntegerAttr;
    argcTy argc;

    auto getArgc() const {
      auto &propStorage = this->argc;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setArgc(const ::mlir::IntegerAttr &propValue) {
      this->argc = propValue;
    }
    using function_typeTy = ::mlir::TypeAttr;
    function_typeTy function_type;

    auto getFunctionType() const {
      auto &propStorage = this->function_type;
      return ::llvm::cast<::mlir::TypeAttr>(propStorage);
    }
    void setFunctionType(const ::mlir::TypeAttr &propValue) {
      this->function_type = propValue;
    }
    using implementationTy = ::mlir::FlatSymbolRefAttr;
    implementationTy implementation;

    auto getImplementation() const {
      auto &propStorage = this->implementation;
      return ::llvm::cast<::mlir::FlatSymbolRefAttr>(propStorage);
    }
    void setImplementation(const ::mlir::FlatSymbolRefAttr &propValue) {
      this->implementation = propValue;
    }
    using res_attrsTy = ::mlir::ArrayAttr;
    res_attrsTy res_attrs;

    auto getResAttrs() const {
      auto &propStorage = this->res_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setResAttrs(const ::mlir::ArrayAttr &propValue) {
      this->res_attrs = propValue;
    }
    using rescTy = ::mlir::IntegerAttr;
    rescTy resc;

    auto getResc() const {
      auto &propStorage = this->resc;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setResc(const ::mlir::IntegerAttr &propValue) {
      this->resc = propValue;
    }
    using sym_nameTy = ::mlir::StringAttr;
    sym_nameTy sym_name;

    auto getSymName() const {
      auto &propStorage = this->sym_name;
      return ::llvm::cast<::mlir::StringAttr>(propStorage);
    }
    void setSymName(const ::mlir::StringAttr &propValue) {
      this->sym_name = propValue;
    }
    using tapeTy = ::mlir::IntegerAttr;
    tapeTy tape;

    auto getTape() const {
      auto &propStorage = this->tape;
      return ::llvm::cast<::mlir::IntegerAttr>(propStorage);
    }
    void setTape(const ::mlir::IntegerAttr &propValue) {
      this->tape = propValue;
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.arg_attrs == this->arg_attrs &&
        rhs.argc == this->argc &&
        rhs.function_type == this->function_type &&
        rhs.implementation == this->implementation &&
        rhs.res_attrs == this->res_attrs &&
        rhs.resc == this->resc &&
        rhs.sym_name == this->sym_name &&
        rhs.tape == this->tape &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  ReverseOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.reverse", odsAttrs.getContext());
  }

  ReverseOpGenericAdaptorBase(ReverseOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize) {
    return {index, 1};
  }

  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::StringAttr getSymNameAttr() {
    auto attr = ::llvm::cast<::mlir::StringAttr>(getProperties().sym_name);
    return attr;
  }

  ::llvm::StringRef getSymName();
  ::mlir::TypeAttr getFunctionTypeAttr() {
    auto attr = ::llvm::cast<::mlir::TypeAttr>(getProperties().function_type);
    return attr;
  }

  ::mlir::FunctionType getFunctionType();
  ::mlir::FlatSymbolRefAttr getImplementationAttr() {
    auto attr = ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().implementation);
    return attr;
  }

  ::llvm::StringRef getImplementation();
  ::mlir::IntegerAttr getArgcAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().argc);
    return attr;
  }

  uint64_t getArgc();
  ::mlir::IntegerAttr getRescAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().resc);
    return attr;
  }

  uint64_t getResc();
  ::mlir::IntegerAttr getTapeAttr() {
    auto attr = ::llvm::cast<::mlir::IntegerAttr>(getProperties().tape);
    return attr;
  }

  uint64_t getTape();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  ::mlir::Region &getBody() {
    return *odsRegions[0];
  }

  ::mlir::RegionRange getRegions() {
    return odsRegions;
  }

};
} // namespace detail
template <typename RangeT>
class ReverseOpGenericAdaptor : public detail::ReverseOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::ReverseOpGenericAdaptorBase;
public:
  ReverseOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  ReverseOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : ReverseOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  ReverseOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs = nullptr) : ReverseOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  ReverseOpGenericAdaptor(RangeT values, const ReverseOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = ReverseOp, typename = std::enable_if_t<std::is_same_v<LateInst, ReverseOp>>>
  ReverseOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class ReverseOpAdaptor : public ReverseOpGenericAdaptor<::mlir::ValueRange> {
public:
  using ReverseOpGenericAdaptor::ReverseOpGenericAdaptor;
  ReverseOpAdaptor(ReverseOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class ReverseOp : public ::mlir::Op<ReverseOp, ::mlir::OpTrait::OneRegion, ::mlir::OpTrait::ZeroResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::ZeroOperands, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::SymbolOpInterface::Trait, ::mlir::CallableOpInterface::Trait, ::mlir::FunctionOpInterface::Trait, ::mlir::OpTrait::IsIsolatedFromAbove> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = ReverseOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = ReverseOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("arg_attrs"), ::llvm::StringRef("argc"), ::llvm::StringRef("function_type"), ::llvm::StringRef("implementation"), ::llvm::StringRef("res_attrs"), ::llvm::StringRef("resc"), ::llvm::StringRef("sym_name"), ::llvm::StringRef("tape")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getArgAttrsAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getArgAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getArgcAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getArgcAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getFunctionTypeAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getFunctionTypeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getImplementationAttrName() {
    return getAttributeNameForIndex(3);
  }

  static ::mlir::StringAttr getImplementationAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 3);
  }

  ::mlir::StringAttr getResAttrsAttrName() {
    return getAttributeNameForIndex(4);
  }

  static ::mlir::StringAttr getResAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 4);
  }

  ::mlir::StringAttr getRescAttrName() {
    return getAttributeNameForIndex(5);
  }

  static ::mlir::StringAttr getRescAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 5);
  }

  ::mlir::StringAttr getSymNameAttrName() {
    return getAttributeNameForIndex(6);
  }

  static ::mlir::StringAttr getSymNameAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 6);
  }

  ::mlir::StringAttr getTapeAttrName() {
    return getAttributeNameForIndex(7);
  }

  static ::mlir::StringAttr getTapeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 7);
  }

  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.reverse");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index) {
    return {index, 1};
  }

  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Region &getBody() {
    return (*this)->getRegion(0);
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::StringAttr getSymNameAttr() {
    return ::llvm::cast<::mlir::StringAttr>(getProperties().sym_name);
  }

  ::llvm::StringRef getSymName();
  ::mlir::TypeAttr getFunctionTypeAttr() {
    return ::llvm::cast<::mlir::TypeAttr>(getProperties().function_type);
  }

  ::mlir::FunctionType getFunctionType();
  ::mlir::FlatSymbolRefAttr getImplementationAttr() {
    return ::llvm::cast<::mlir::FlatSymbolRefAttr>(getProperties().implementation);
  }

  ::llvm::StringRef getImplementation();
  ::mlir::IntegerAttr getArgcAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().argc);
  }

  uint64_t getArgc();
  ::mlir::IntegerAttr getRescAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().resc);
  }

  uint64_t getResc();
  ::mlir::IntegerAttr getTapeAttr() {
    return ::llvm::cast<::mlir::IntegerAttr>(getProperties().tape);
  }

  uint64_t getTape();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  void setSymNameAttr(::mlir::StringAttr attr) {
    getProperties().sym_name = attr;
  }

  void setSymName(::llvm::StringRef attrValue);
  void setFunctionTypeAttr(::mlir::TypeAttr attr) {
    getProperties().function_type = attr;
  }

  void setFunctionType(::mlir::FunctionType attrValue);
  void setImplementationAttr(::mlir::FlatSymbolRefAttr attr) {
    getProperties().implementation = attr;
  }

  void setImplementation(::llvm::StringRef attrValue);
  void setArgcAttr(::mlir::IntegerAttr attr) {
    getProperties().argc = attr;
  }

  void setArgc(uint64_t attrValue);
  void setRescAttr(::mlir::IntegerAttr attr) {
    getProperties().resc = attr;
  }

  void setResc(uint64_t attrValue);
  void setTapeAttr(::mlir::IntegerAttr attr) {
    getProperties().tape = attr;
  }

  void setTape(uint64_t attrValue);
  void setArgAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().arg_attrs = attr;
  }

  void setResAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().res_attrs = attr;
  }

  ::mlir::Attribute removeArgAttrsAttr() {
      auto attr = getProperties().arg_attrs;
      getProperties().arg_attrs = {};
      return attr;
  }

  ::mlir::Attribute removeResAttrsAttr() {
      auto attr = getProperties().res_attrs;
      getProperties().res_attrs = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, mlir::StringRef name, mlir::FunctionType type, mlir::ArrayRef<mlir::NamedAttribute> attrs = {});
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &p);
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 8 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
  //===------------------------------------------------------------------===//
  // FunctionOpInterface Methods
  //===------------------------------------------------------------------===//

  /// Returns the argument types of this function.
  mlir::ArrayRef<mlir::Type> getArgumentTypes() { return getFunctionType().getInputs(); }

  /// Returns the result types of this function.
  mlir::ArrayRef<mlir::Type> getResultTypes() { return getFunctionType().getResults(); }

  mlir::Region *getCallableRegion() { return &getBody(); }
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::ReverseOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::VJPOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class VJPOpGenericAdaptorBase {
public:
  struct Properties {
    using arg_attrsTy = ::mlir::ArrayAttr;
    arg_attrsTy arg_attrs;

    auto getArgAttrs() const {
      auto &propStorage = this->arg_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setArgAttrs(const ::mlir::ArrayAttr &propValue) {
      this->arg_attrs = propValue;
    }
    using calleeTy = ::mlir::SymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::SymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::SymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using diffArgIndicesTy = ::mlir::DenseIntElementsAttr;
    diffArgIndicesTy diffArgIndices;

    auto getDiffArgIndices() const {
      auto &propStorage = this->diffArgIndices;
      return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(propStorage);
    }
    void setDiffArgIndices(const ::mlir::DenseIntElementsAttr &propValue) {
      this->diffArgIndices = propValue;
    }
    using finiteDiffParamTy = ::mlir::FloatAttr;
    finiteDiffParamTy finiteDiffParam;

    auto getFiniteDiffParam() const {
      auto &propStorage = this->finiteDiffParam;
      return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(propStorage);
    }
    void setFiniteDiffParam(const ::mlir::FloatAttr &propValue) {
      this->finiteDiffParam = propValue;
    }
    using methodTy = ::mlir::StringAttr;
    methodTy method;

    auto getMethod() const {
      auto &propStorage = this->method;
      return ::llvm::cast<::mlir::StringAttr>(propStorage);
    }
    void setMethod(const ::mlir::StringAttr &propValue) {
      this->method = propValue;
    }
    using res_attrsTy = ::mlir::ArrayAttr;
    res_attrsTy res_attrs;

    auto getResAttrs() const {
      auto &propStorage = this->res_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setResAttrs(const ::mlir::ArrayAttr &propValue) {
      this->res_attrs = propValue;
    }
    using operandSegmentSizesTy = std::array<int32_t, 2>;
    operandSegmentSizesTy operandSegmentSizes;
    ::llvm::ArrayRef<int32_t> getOperandSegmentSizes() const {
      auto &propStorage = this->operandSegmentSizes;
      return propStorage;
    }
    void setOperandSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->operandSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    using resultSegmentSizesTy = std::array<int32_t, 2>;
    resultSegmentSizesTy resultSegmentSizes;
    ::llvm::ArrayRef<int32_t> getResultSegmentSizes() const {
      auto &propStorage = this->resultSegmentSizes;
      return propStorage;
    }
    void setResultSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->resultSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.arg_attrs == this->arg_attrs &&
        rhs.callee == this->callee &&
        rhs.diffArgIndices == this->diffArgIndices &&
        rhs.finiteDiffParam == this->finiteDiffParam &&
        rhs.method == this->method &&
        rhs.res_attrs == this->res_attrs &&
        rhs.operandSegmentSizes == this->operandSegmentSizes &&
        rhs.resultSegmentSizes == this->resultSegmentSizes &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  VJPOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.vjp", odsAttrs.getContext());
  }

  VJPOpGenericAdaptorBase(VJPOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::StringAttr getMethodAttr() {
    auto attr = ::llvm::cast<::mlir::StringAttr>(getProperties().method);
    return attr;
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
    return attr;
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
    return attr;
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
};
} // namespace detail
template <typename RangeT>
class VJPOpGenericAdaptor : public detail::VJPOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::VJPOpGenericAdaptorBase;
public:
  VJPOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  VJPOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : VJPOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  VJPOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs) : VJPOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  VJPOpGenericAdaptor(RangeT values, const VJPOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = VJPOp, typename = std::enable_if_t<std::is_same_v<LateInst, VJPOp>>>
  VJPOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getParams() {
    return getODSOperands(0);
  }

  RangeT getCotangents() {
    return getODSOperands(1);
  }

  RangeT getOperands() {
    return odsOperands;
  }

private:
  RangeT odsOperands;
};
class VJPOpAdaptor : public VJPOpGenericAdaptor<::mlir::ValueRange> {
public:
  using VJPOpGenericAdaptor::VJPOpGenericAdaptor;
  VJPOpAdaptor(VJPOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class VJPOp : public ::mlir::Op<VJPOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::VariadicResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::VariadicOperands, ::mlir::OpTrait::AttrSizedOperandSegments, ::mlir::OpTrait::AttrSizedResultSegments, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::CallOpInterface::Trait, ::mlir::SymbolUserOpInterface::Trait, ::catalyst::gradient::GradientOpInterface::Trait, ::mlir::OpAsmOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = VJPOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = VJPOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("arg_attrs"), ::llvm::StringRef("callee"), ::llvm::StringRef("diffArgIndices"), ::llvm::StringRef("finiteDiffParam"), ::llvm::StringRef("method"), ::llvm::StringRef("res_attrs"), ::llvm::StringRef("operandSegmentSizes")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getArgAttrsAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getArgAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getDiffArgIndicesAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getDiffArgIndicesAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getFiniteDiffParamAttrName() {
    return getAttributeNameForIndex(3);
  }

  static ::mlir::StringAttr getFiniteDiffParamAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 3);
  }

  ::mlir::StringAttr getMethodAttrName() {
    return getAttributeNameForIndex(4);
  }

  static ::mlir::StringAttr getMethodAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 4);
  }

  ::mlir::StringAttr getResAttrsAttrName() {
    return getAttributeNameForIndex(5);
  }

  static ::mlir::StringAttr getResAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 5);
  }

  ::mlir::StringAttr getOperandSegmentSizesAttrName() {
   return (*this)->getName().getAttributeNames().back();
  }

  static ::mlir::StringAttr getOperandSegmentSizesAttrName(::mlir::OperationName name) {
   return name.getAttributeNames().back();
  }

  void getAsmResultNames(::mlir::OpAsmSetValueNameFn setNameFn);
  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.vjp");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::operand_range getParams() {
    return getODSOperands(0);
  }

  ::mlir::Operation::operand_range getCotangents() {
    return getODSOperands(1);
  }

  ::mlir::MutableOperandRange getParamsMutable();
  ::mlir::MutableOperandRange getCotangentsMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index);
  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::result_range getCalleeResults() {
    return getODSResults(0);
  }

  ::mlir::Operation::result_range getVjps() {
    return getODSResults(1);
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::StringAttr getMethodAttr() {
    return ::llvm::cast<::mlir::StringAttr>(getProperties().method);
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  void setMethodAttr(::mlir::StringAttr attr) {
    getProperties().method = attr;
  }

  void setMethod(::llvm::StringRef attrValue);
  void setCalleeAttr(::mlir::SymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  void setDiffArgIndicesAttr(::mlir::DenseIntElementsAttr attr) {
    getProperties().diffArgIndices = attr;
  }

  void setFiniteDiffParamAttr(::mlir::FloatAttr attr) {
    getProperties().finiteDiffParam = attr;
  }

  void setArgAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().arg_attrs = attr;
  }

  void setResAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().res_attrs = attr;
  }

  ::mlir::Attribute removeDiffArgIndicesAttr() {
      auto attr = getProperties().diffArgIndices;
      getProperties().diffArgIndices = {};
      return attr;
  }

  ::mlir::Attribute removeFiniteDiffParamAttr() {
      auto attr = getProperties().finiteDiffParam;
      getProperties().finiteDiffParam = {};
      return attr;
  }

  ::mlir::Attribute removeArgAttrsAttr() {
      auto attr = getProperties().arg_attrs;
      getProperties().arg_attrs = {};
      return attr;
  }

  ::mlir::Attribute removeResAttrsAttr() {
      auto attr = getProperties().res_attrs;
      getProperties().res_attrs = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange calleeResults, ::mlir::TypeRange vjps, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange cotangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange cotangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange calleeResults, ::mlir::TypeRange vjps, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange cotangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange params, ::mlir::ValueRange cotangents, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::llvm::LogicalResult verify();
  ::mlir::CallInterfaceCallable getCallableForCallee();
  void setCalleeFromCallable(::mlir::CallInterfaceCallable callee);
  ::mlir::Operation::operand_range getArgOperands();
  ::mlir::MutableOperandRange getArgOperandsMutable();
  ::llvm::LogicalResult verifySymbolUses(::mlir::SymbolTableCollection &symbolTable);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 6 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::VJPOp)

namespace catalyst {
namespace gradient {

//===----------------------------------------------------------------------===//
// ::catalyst::gradient::ValueAndGradOp declarations
//===----------------------------------------------------------------------===//

namespace detail {
class ValueAndGradOpGenericAdaptorBase {
public:
  struct Properties {
    using arg_attrsTy = ::mlir::ArrayAttr;
    arg_attrsTy arg_attrs;

    auto getArgAttrs() const {
      auto &propStorage = this->arg_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setArgAttrs(const ::mlir::ArrayAttr &propValue) {
      this->arg_attrs = propValue;
    }
    using calleeTy = ::mlir::SymbolRefAttr;
    calleeTy callee;

    auto getCallee() const {
      auto &propStorage = this->callee;
      return ::llvm::cast<::mlir::SymbolRefAttr>(propStorage);
    }
    void setCallee(const ::mlir::SymbolRefAttr &propValue) {
      this->callee = propValue;
    }
    using diffArgIndicesTy = ::mlir::DenseIntElementsAttr;
    diffArgIndicesTy diffArgIndices;

    auto getDiffArgIndices() const {
      auto &propStorage = this->diffArgIndices;
      return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(propStorage);
    }
    void setDiffArgIndices(const ::mlir::DenseIntElementsAttr &propValue) {
      this->diffArgIndices = propValue;
    }
    using finiteDiffParamTy = ::mlir::FloatAttr;
    finiteDiffParamTy finiteDiffParam;

    auto getFiniteDiffParam() const {
      auto &propStorage = this->finiteDiffParam;
      return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(propStorage);
    }
    void setFiniteDiffParam(const ::mlir::FloatAttr &propValue) {
      this->finiteDiffParam = propValue;
    }
    using methodTy = ::mlir::StringAttr;
    methodTy method;

    auto getMethod() const {
      auto &propStorage = this->method;
      return ::llvm::cast<::mlir::StringAttr>(propStorage);
    }
    void setMethod(const ::mlir::StringAttr &propValue) {
      this->method = propValue;
    }
    using res_attrsTy = ::mlir::ArrayAttr;
    res_attrsTy res_attrs;

    auto getResAttrs() const {
      auto &propStorage = this->res_attrs;
      return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(propStorage);
    }
    void setResAttrs(const ::mlir::ArrayAttr &propValue) {
      this->res_attrs = propValue;
    }
    using resultSegmentSizesTy = std::array<int32_t, 2>;
    resultSegmentSizesTy resultSegmentSizes;
    ::llvm::ArrayRef<int32_t> getResultSegmentSizes() const {
      auto &propStorage = this->resultSegmentSizes;
      return propStorage;
    }
    void setResultSegmentSizes(::llvm::ArrayRef<int32_t> propValue) {
      auto &propStorage = this->resultSegmentSizes;
      ::llvm::copy(propValue, propStorage.begin());
    }
    bool operator==(const Properties &rhs) const {
      return 
        rhs.arg_attrs == this->arg_attrs &&
        rhs.callee == this->callee &&
        rhs.diffArgIndices == this->diffArgIndices &&
        rhs.finiteDiffParam == this->finiteDiffParam &&
        rhs.method == this->method &&
        rhs.res_attrs == this->res_attrs &&
        rhs.resultSegmentSizes == this->resultSegmentSizes &&
        true;
    }
    bool operator!=(const Properties &rhs) const {
      return !(*this == rhs);
    }
  };
protected:
  ::mlir::DictionaryAttr odsAttrs;
  ::std::optional<::mlir::OperationName> odsOpName;
  Properties properties;
  ::mlir::RegionRange odsRegions;
public:
  ValueAndGradOpGenericAdaptorBase(::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : odsAttrs(attrs), properties(properties), odsRegions(regions) {  if (odsAttrs)
      odsOpName.emplace("gradient.value_and_grad", odsAttrs.getContext());
  }

  ValueAndGradOpGenericAdaptorBase(ValueAndGradOp op);

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index, unsigned odsOperandsSize);
  const Properties &getProperties() {
    return properties;
  }

  ::mlir::DictionaryAttr getAttributes() {
    return odsAttrs;
  }

  ::mlir::StringAttr getMethodAttr() {
    auto attr = ::llvm::cast<::mlir::StringAttr>(getProperties().method);
    return attr;
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    auto attr = ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
    return attr;
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
    return attr;
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
    return attr;
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    auto attr = ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
    return attr;
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
};
} // namespace detail
template <typename RangeT>
class ValueAndGradOpGenericAdaptor : public detail::ValueAndGradOpGenericAdaptorBase {
  using ValueT = ::llvm::detail::ValueOfRange<RangeT>;
  using Base = detail::ValueAndGradOpGenericAdaptorBase;
public:
  ValueAndGradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, const Properties &properties, ::mlir::RegionRange regions = {}) : Base(attrs, properties, regions), odsOperands(values) {}

  ValueAndGradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs, ::mlir::OpaqueProperties properties, ::mlir::RegionRange regions = {}) : ValueAndGradOpGenericAdaptor(values, attrs, (properties ? *properties.as<Properties *>() : Properties{}), regions) {}

  ValueAndGradOpGenericAdaptor(RangeT values, ::mlir::DictionaryAttr attrs = nullptr) : ValueAndGradOpGenericAdaptor(values, attrs, Properties{}, {}) {}

  ValueAndGradOpGenericAdaptor(RangeT values, const ValueAndGradOpGenericAdaptorBase &base) : Base(base), odsOperands(values) {}

  template <typename LateInst = ValueAndGradOp, typename = std::enable_if_t<std::is_same_v<LateInst, ValueAndGradOp>>>
  ValueAndGradOpGenericAdaptor(RangeT values, LateInst op) : Base(op), odsOperands(values) {}

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index) {
    return Base::getODSOperandIndexAndLength(index, odsOperands.size());
  }

  RangeT getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(odsOperands.begin(), valueRange.first),
             std::next(odsOperands.begin(), valueRange.first + valueRange.second)};
  }

  RangeT getOperands() {
    return getODSOperands(0);
  }

private:
  RangeT odsOperands;
};
class ValueAndGradOpAdaptor : public ValueAndGradOpGenericAdaptor<::mlir::ValueRange> {
public:
  using ValueAndGradOpGenericAdaptor::ValueAndGradOpGenericAdaptor;
  ValueAndGradOpAdaptor(ValueAndGradOp op);

  ::llvm::LogicalResult verify(::mlir::Location loc);
};
class ValueAndGradOp : public ::mlir::Op<ValueAndGradOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::VariadicResults, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::VariadicOperands, ::mlir::OpTrait::AttrSizedResultSegments, ::mlir::OpTrait::OpInvariants, ::mlir::BytecodeOpInterface::Trait, ::mlir::CallOpInterface::Trait, ::mlir::SymbolUserOpInterface::Trait, ::catalyst::gradient::GradientOpInterface::Trait, ::mlir::OpAsmOpInterface::Trait> {
public:
  using Op::Op;
  using Op::print;
  using Adaptor = ValueAndGradOpAdaptor;
  template <typename RangeT>
  using GenericAdaptor = ValueAndGradOpGenericAdaptor<RangeT>;
  using FoldAdaptor = GenericAdaptor<::llvm::ArrayRef<::mlir::Attribute>>;
  using Properties = FoldAdaptor::Properties;
  static ::llvm::ArrayRef<::llvm::StringRef> getAttributeNames() {
    static ::llvm::StringRef attrNames[] = {::llvm::StringRef("arg_attrs"), ::llvm::StringRef("callee"), ::llvm::StringRef("diffArgIndices"), ::llvm::StringRef("finiteDiffParam"), ::llvm::StringRef("method"), ::llvm::StringRef("res_attrs")};
    return ::llvm::ArrayRef(attrNames);
  }

  ::mlir::StringAttr getArgAttrsAttrName() {
    return getAttributeNameForIndex(0);
  }

  static ::mlir::StringAttr getArgAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 0);
  }

  ::mlir::StringAttr getCalleeAttrName() {
    return getAttributeNameForIndex(1);
  }

  static ::mlir::StringAttr getCalleeAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 1);
  }

  ::mlir::StringAttr getDiffArgIndicesAttrName() {
    return getAttributeNameForIndex(2);
  }

  static ::mlir::StringAttr getDiffArgIndicesAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 2);
  }

  ::mlir::StringAttr getFiniteDiffParamAttrName() {
    return getAttributeNameForIndex(3);
  }

  static ::mlir::StringAttr getFiniteDiffParamAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 3);
  }

  ::mlir::StringAttr getMethodAttrName() {
    return getAttributeNameForIndex(4);
  }

  static ::mlir::StringAttr getMethodAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 4);
  }

  ::mlir::StringAttr getResAttrsAttrName() {
    return getAttributeNameForIndex(5);
  }

  static ::mlir::StringAttr getResAttrsAttrName(::mlir::OperationName name) {
    return getAttributeNameForIndex(name, 5);
  }

  void getAsmResultNames(::mlir::OpAsmSetValueNameFn setNameFn);
  static constexpr ::llvm::StringLiteral getOperationName() {
    return ::llvm::StringLiteral("gradient.value_and_grad");
  }

  std::pair<unsigned, unsigned> getODSOperandIndexAndLength(unsigned index);
  ::mlir::Operation::operand_range getODSOperands(unsigned index) {
    auto valueRange = getODSOperandIndexAndLength(index);
    return {std::next(getOperation()->operand_begin(), valueRange.first),
             std::next(getOperation()->operand_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::operand_range getOperands() {
    return getODSOperands(0);
  }

  ::mlir::MutableOperandRange getOperandsMutable();
  std::pair<unsigned, unsigned> getODSResultIndexAndLength(unsigned index);
  ::mlir::Operation::result_range getODSResults(unsigned index) {
    auto valueRange = getODSResultIndexAndLength(index);
    return {std::next(getOperation()->result_begin(), valueRange.first),
             std::next(getOperation()->result_begin(), valueRange.first + valueRange.second)};
  }

  ::mlir::Operation::result_range getVals() {
    return getODSResults(0);
  }

  ::mlir::Operation::result_range getGradients() {
    return getODSResults(1);
  }

  static ::llvm::LogicalResult setPropertiesFromAttr(Properties &prop, ::mlir::Attribute attr, ::llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::mlir::Attribute getPropertiesAsAttr(::mlir::MLIRContext *ctx, const Properties &prop);
  static llvm::hash_code computePropertiesHash(const Properties &prop);
  static std::optional<mlir::Attribute> getInherentAttr(::mlir::MLIRContext *ctx, const Properties &prop, llvm::StringRef name);
  static void setInherentAttr(Properties &prop, llvm::StringRef name, mlir::Attribute value);
  static void populateInherentAttrs(::mlir::MLIRContext *ctx, const Properties &prop, ::mlir::NamedAttrList &attrs);
  static ::llvm::LogicalResult verifyInherentAttrs(::mlir::OperationName opName, ::mlir::NamedAttrList &attrs, llvm::function_ref<::mlir::InFlightDiagnostic()> emitError);
  static ::llvm::LogicalResult readProperties(::mlir::DialectBytecodeReader &reader, ::mlir::OperationState &state);
  void writeProperties(::mlir::DialectBytecodeWriter &writer);
  ::mlir::StringAttr getMethodAttr() {
    return ::llvm::cast<::mlir::StringAttr>(getProperties().method);
  }

  ::llvm::StringRef getMethod();
  ::mlir::SymbolRefAttr getCalleeAttr() {
    return ::llvm::cast<::mlir::SymbolRefAttr>(getProperties().callee);
  }

  ::mlir::SymbolRefAttr getCallee();
  ::mlir::DenseIntElementsAttr getDiffArgIndicesAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::DenseIntElementsAttr>(getProperties().diffArgIndices);
  }

  ::std::optional< ::mlir::DenseIntElementsAttr > getDiffArgIndices();
  ::mlir::FloatAttr getFiniteDiffParamAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::FloatAttr>(getProperties().finiteDiffParam);
  }

  ::std::optional<::mlir::FloatAttr> getFiniteDiffParam();
  ::mlir::ArrayAttr getArgAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().arg_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getArgAttrs();
  ::mlir::ArrayAttr getResAttrsAttr() {
    return ::llvm::dyn_cast_or_null<::mlir::ArrayAttr>(getProperties().res_attrs);
  }

  ::std::optional< ::mlir::ArrayAttr > getResAttrs();
  void setMethodAttr(::mlir::StringAttr attr) {
    getProperties().method = attr;
  }

  void setMethod(::llvm::StringRef attrValue);
  void setCalleeAttr(::mlir::SymbolRefAttr attr) {
    getProperties().callee = attr;
  }

  void setDiffArgIndicesAttr(::mlir::DenseIntElementsAttr attr) {
    getProperties().diffArgIndices = attr;
  }

  void setFiniteDiffParamAttr(::mlir::FloatAttr attr) {
    getProperties().finiteDiffParam = attr;
  }

  void setArgAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().arg_attrs = attr;
  }

  void setResAttrsAttr(::mlir::ArrayAttr attr) {
    getProperties().res_attrs = attr;
  }

  ::mlir::Attribute removeDiffArgIndicesAttr() {
      auto attr = getProperties().diffArgIndices;
      getProperties().diffArgIndices = {};
      return attr;
  }

  ::mlir::Attribute removeFiniteDiffParamAttr() {
      auto attr = getProperties().finiteDiffParam;
      getProperties().finiteDiffParam = {};
      return attr;
  }

  ::mlir::Attribute removeArgAttrsAttr() {
      auto attr = getProperties().arg_attrs;
      getProperties().arg_attrs = {};
      return attr;
  }

  ::mlir::Attribute removeResAttrsAttr() {
      auto attr = getProperties().res_attrs;
      getProperties().res_attrs = {};
      return attr;
  }

  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange vals, ::mlir::TypeRange gradients, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange operands, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::StringAttr method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange operands, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange vals, ::mlir::TypeRange gradients, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange operands, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &odsBuilder, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::llvm::StringRef method, ::mlir::SymbolRefAttr callee, ::mlir::ValueRange operands, /*optional*/::mlir::DenseIntElementsAttr diffArgIndices, /*optional*/::mlir::FloatAttr finiteDiffParam, /*optional*/::mlir::ArrayAttr arg_attrs, /*optional*/::mlir::ArrayAttr res_attrs);
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, ::llvm::ArrayRef<::mlir::NamedAttribute> attributes = {});
  static void build(::mlir::OpBuilder &, ::mlir::OperationState &odsState, ::mlir::TypeRange resultTypes, ::mlir::ValueRange operands, const Properties &properties, ::llvm::ArrayRef<::mlir::NamedAttribute> discardableAttributes = {});
  ::llvm::LogicalResult verifyInvariantsImpl();
  ::llvm::LogicalResult verifyInvariants();
  ::llvm::LogicalResult verify();
  ::mlir::CallInterfaceCallable getCallableForCallee();
  void setCalleeFromCallable(::mlir::CallInterfaceCallable callee);
  ::mlir::Operation::operand_range getArgOperands();
  ::mlir::MutableOperandRange getArgOperandsMutable();
  ::llvm::LogicalResult verifySymbolUses(::mlir::SymbolTableCollection &symbolTable);
  static ::mlir::ParseResult parse(::mlir::OpAsmParser &parser, ::mlir::OperationState &result);
  void print(::mlir::OpAsmPrinter &_odsPrinter);
private:
  ::mlir::StringAttr getAttributeNameForIndex(unsigned index) {
    return getAttributeNameForIndex((*this)->getName(), index);
  }

  static ::mlir::StringAttr getAttributeNameForIndex(::mlir::OperationName name, unsigned index) {
    assert(index < 6 && "invalid attribute index");
    assert(name.getStringRef() == getOperationName() && "invalid operation name");
    assert(name.isRegistered() && "Operation isn't registered, missing a "
          "dependent dialect loading?");
    return name.getAttributeNames()[index];
  }

public:
};
} // namespace gradient
} // namespace catalyst
MLIR_DECLARE_EXPLICIT_TYPE_ID(::catalyst::gradient::ValueAndGradOp)


#endif  // GET_OP_CLASSES

