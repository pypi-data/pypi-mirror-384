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
namespace xla::xtile {
/// Contains auxillary information about how a program is tiled.
class TilingInfoAttr;
namespace detail {
struct TilingInfoAttrStorage;
} // namespace detail
class TilingInfoAttr : public ::mlir::Attribute::AttrBase<TilingInfoAttr, ::mlir::Attribute, detail::TilingInfoAttrStorage> {
public:
  using Base::Base;
  static constexpr ::llvm::StringLiteral name = "xtile.tiling_info";
  static constexpr ::llvm::StringLiteral dialectName = "xtile";
  static TilingInfoAttr get(::mlir::MLIRContext *context, int32_t tile_count, int32_t tiles_per_workgroup);
  static constexpr ::llvm::StringLiteral getMnemonic() {
    return {"tiling_info"};
  }

  static ::mlir::Attribute parse(::mlir::AsmParser &odsParser, ::mlir::Type odsType);
  void print(::mlir::AsmPrinter &odsPrinter) const;
  int32_t getTileCount() const;
  int32_t getTilesPerWorkgroup() const;
};
} // namespace xla::xtile
MLIR_DECLARE_EXPLICIT_TYPE_ID(::xla::xtile::TilingInfoAttr)

#endif // GET_ATTRDEF_CLASSES

