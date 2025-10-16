/*===- TableGen'erated file -------------------------------------*- C++ -*-===*\
|*                                                                            *|
|* Enum Utility Declarations                                                  *|
|*                                                                            *|
|* Automatically generated file, do not edit!                                 *|
|* From: MitigationOps.td                                                     *|
|*                                                                            *|
\*===----------------------------------------------------------------------===*/

namespace catalyst {
namespace mitigation {
// Folding types
enum class Folding : uint32_t {
  global = 1,
  all = 2,
  random = 3,
};

::std::optional<Folding> symbolizeFolding(uint32_t);
::llvm::StringRef stringifyFolding(Folding);
::std::optional<Folding> symbolizeFolding(::llvm::StringRef);
inline constexpr unsigned getMaxEnumValForFolding() {
  return 3;
}


inline ::llvm::StringRef stringifyEnum(Folding enumValue) {
  return stringifyFolding(enumValue);
}

template <typename EnumType>
::std::optional<EnumType> symbolizeEnum(::llvm::StringRef);

template <>
inline ::std::optional<Folding> symbolizeEnum<Folding>(::llvm::StringRef str) {
  return symbolizeFolding(str);
}
} // namespace mitigation
} // namespace catalyst

namespace mlir {
template <typename T, typename>
struct FieldParser;

template<>
struct FieldParser<catalyst::mitigation::Folding, catalyst::mitigation::Folding> {
  template <typename ParserT>
  static FailureOr<catalyst::mitigation::Folding> parse(ParserT &parser) {
    // Parse the keyword/string containing the enum.
    std::string enumKeyword;
    auto loc = parser.getCurrentLocation();
    if (failed(parser.parseOptionalKeywordOrString(&enumKeyword)))
      return parser.emitError(loc, "expected keyword for Folding types");

    // Symbolize the keyword.
    if (::std::optional<catalyst::mitigation::Folding> attr = catalyst::mitigation::symbolizeEnum<catalyst::mitigation::Folding>(enumKeyword))
      return *attr;
    return parser.emitError(loc, "expected one of [global, all, random] for Folding types, got: ") << enumKeyword;
  }
};

/// Support for std::optional, useful in attribute/type definition where the enum is
/// used as:
///
///    let parameters = (ins OptionalParameter<"std::optional<TheEnumName>">:$value);
template<>
struct FieldParser<std::optional<catalyst::mitigation::Folding>, std::optional<catalyst::mitigation::Folding>> {
  template <typename ParserT>
  static FailureOr<std::optional<catalyst::mitigation::Folding>> parse(ParserT &parser) {
    // Parse the keyword/string containing the enum.
    std::string enumKeyword;
    auto loc = parser.getCurrentLocation();
    if (failed(parser.parseOptionalKeywordOrString(&enumKeyword)))
      return std::optional<catalyst::mitigation::Folding>{};

    // Symbolize the keyword.
    if (::std::optional<catalyst::mitigation::Folding> attr = catalyst::mitigation::symbolizeEnum<catalyst::mitigation::Folding>(enumKeyword))
      return attr;
    return parser.emitError(loc, "expected one of [global, all, random] for Folding types, got: ") << enumKeyword;
  }
};
} // namespace mlir

namespace llvm {
inline ::llvm::raw_ostream &operator<<(::llvm::raw_ostream &p, catalyst::mitigation::Folding value) {
  auto valueStr = stringifyEnum(value);
  return p << valueStr;
}
} // namespace llvm

namespace llvm {
template<> struct DenseMapInfo<catalyst::mitigation::Folding> {
  using StorageInfo = ::llvm::DenseMapInfo<uint32_t>;

  static inline catalyst::mitigation::Folding getEmptyKey() {
    return static_cast<catalyst::mitigation::Folding>(StorageInfo::getEmptyKey());
  }

  static inline catalyst::mitigation::Folding getTombstoneKey() {
    return static_cast<catalyst::mitigation::Folding>(StorageInfo::getTombstoneKey());
  }

  static unsigned getHashValue(const catalyst::mitigation::Folding &val) {
    return StorageInfo::getHashValue(static_cast<uint32_t>(val));
  }

  static bool isEqual(const catalyst::mitigation::Folding &lhs, const catalyst::mitigation::Folding &rhs) {
    return lhs == rhs;
  }
};
}

