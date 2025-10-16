/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Enum Utility Declarations                                                  *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: QuantumOps.td                                                        *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace quantum {
// Known named observables
enum class NamedObservable : uint32_t {
  Identity = 0,
  PauliX = 1,
  PauliY = 2,
  PauliZ = 3,
  Hadamard = 4,
};

::std::optional<NamedObservable> symbolizeNamedObservable(uint32_t);
::llvm::StringRef stringifyNamedObservable(NamedObservable);
::std::optional<NamedObservable> symbolizeNamedObservable(::llvm::StringRef);
inline constexpr unsigned getMaxEnumValForNamedObservable() {
  return 4;
}


inline ::llvm::StringRef stringifyEnum(NamedObservable enumValue) {
  return stringifyNamedObservable(enumValue);
}

template <typename EnumType>
::std::optional<EnumType> symbolizeEnum(::llvm::StringRef);

template <>
inline ::std::optional<NamedObservable> symbolizeEnum<NamedObservable>(::llvm::StringRef str) {
  return symbolizeNamedObservable(str);
}
} // namespace quantum
} // namespace catalyst

namespace mlir {
template <typename T, typename>
struct FieldParser;

template<>
struct FieldParser<catalyst::quantum::NamedObservable, catalyst::quantum::NamedObservable> {
  template <typename ParserT>
  static FailureOr<catalyst::quantum::NamedObservable> parse(ParserT &parser) {
    // Parse the keyword/string containing the enum.
    std::string enumKeyword;
    auto loc = parser.getCurrentLocation();
    if (failed(parser.parseOptionalKeywordOrString(&enumKeyword)))
      return parser.emitError(loc, "expected keyword for Known named observables");

    // Symbolize the keyword.
    if (::std::optional<catalyst::quantum::NamedObservable> attr = catalyst::quantum::symbolizeEnum<catalyst::quantum::NamedObservable>(enumKeyword))
      return *attr;
    return parser.emitError(loc, "expected one of [Identity, PauliX, PauliY, PauliZ, Hadamard] for Known named observables, got: ") << enumKeyword;
  }
};

/// Support for std::optional, useful in attribute/type definition where the enum is
/// used as:
///
///    let parameters = (ins OptionalParameter<"std::optional<TheEnumName>">:$value);
template<>
struct FieldParser<std::optional<catalyst::quantum::NamedObservable>, std::optional<catalyst::quantum::NamedObservable>> {
  template <typename ParserT>
  static FailureOr<std::optional<catalyst::quantum::NamedObservable>> parse(ParserT &parser) {
    // Parse the keyword/string containing the enum.
    std::string enumKeyword;
    auto loc = parser.getCurrentLocation();
    if (failed(parser.parseOptionalKeywordOrString(&enumKeyword)))
      return std::optional<catalyst::quantum::NamedObservable>{};

    // Symbolize the keyword.
    if (::std::optional<catalyst::quantum::NamedObservable> attr = catalyst::quantum::symbolizeEnum<catalyst::quantum::NamedObservable>(enumKeyword))
      return attr;
    return parser.emitError(loc, "expected one of [Identity, PauliX, PauliY, PauliZ, Hadamard] for Known named observables, got: ") << enumKeyword;
  }
};
} // namespace mlir

namespace llvm {
inline ::llvm::raw_ostream &operator<<(::llvm::raw_ostream &p, catalyst::quantum::NamedObservable value) {
  auto valueStr = stringifyEnum(value);
  return p << valueStr;
}
} // namespace llvm

namespace llvm {
template<> struct DenseMapInfo<catalyst::quantum::NamedObservable> {
  using StorageInfo = ::llvm::DenseMapInfo<uint32_t>;

  static inline catalyst::quantum::NamedObservable getEmptyKey() {
    return static_cast<catalyst::quantum::NamedObservable>(StorageInfo::getEmptyKey());
  }

  static inline catalyst::quantum::NamedObservable getTombstoneKey() {
    return static_cast<catalyst::quantum::NamedObservable>(StorageInfo::getTombstoneKey());
  }

  static unsigned getHashValue(const catalyst::quantum::NamedObservable &val) {
    return StorageInfo::getHashValue(static_cast<uint32_t>(val));
  }

  static bool isEqual(const catalyst::quantum::NamedObservable &lhs, const catalyst::quantum::NamedObservable &rhs) {
    return lhs == rhs;
  }
};
}

