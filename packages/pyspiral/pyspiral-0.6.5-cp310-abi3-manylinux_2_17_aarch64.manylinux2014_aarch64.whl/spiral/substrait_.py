import betterproto2
import pyarrow as pa

import spiral.expressions as se
from spiral.expressions.base import Expr
from spiral.protogen._.substrait import (
    Expression,
    ExpressionFieldReference,
    ExpressionLiteral,
    ExpressionLiteralList,
    ExpressionLiteralStruct,
    ExpressionLiteralUserDefined,
    ExpressionMaskExpression,
    ExpressionReferenceSegment,
    ExpressionReferenceSegmentListElement,
    ExpressionReferenceSegmentStructField,
    ExpressionScalarFunction,
    ExtendedExpression,
)
from spiral.protogen._.substrait.extensions import (
    SimpleExtensionDeclaration,
    SimpleExtensionDeclarationExtensionFunction,
    SimpleExtensionDeclarationExtensionType,
    SimpleExtensionDeclarationExtensionTypeVariation,
)


class SubstraitConverter:
    def __init__(self, scope: Expr, schema: pa.Schema, key_schema: pa.Schema):
        self.scope = scope
        self.schema = schema
        self.key_names = set(key_schema.names)

        # Extension URIs, keyed by extension URI anchor
        self.extension_uris = {}

        # Functions, keyed by function_anchor
        self.functions = {}

        # Types, keyed by type anchor
        self.type_factories = {}

    def convert(self, buffer: pa.Buffer) -> Expr:
        """Convert a Substrait Extended Expression into a Spiral expression."""

        expr: ExtendedExpression = ExtendedExpression().parse(buffer)
        assert len(expr.referred_expr) == 1, "Only one expression is supported"

        # Parse the extension URIs from the plan.
        for ext_uri in expr.extension_uris:
            self.extension_uris[ext_uri.extension_uri_anchor] = ext_uri.uri

        # Parse the extensions from the plan.
        for ext in expr.extensions:
            self._extension_declaration(ext)

        # Convert the expression
        return self._expr(expr.referred_expr[0].expression)

    def _extension_declaration(self, ext: SimpleExtensionDeclaration):
        match betterproto2.which_one_of(ext, "mapping_type"):
            case "extension_function", ext_func:
                self._extension_function(ext_func)
            case "extension_type", ext_type:
                self._extension_type(ext_type)
            case "extension_type_variation", ext_type_variation:
                self._extension_type_variation(ext_type_variation)
            case _:
                raise AssertionError("Invalid substrait plan")

    def _extension_function(self, ext: SimpleExtensionDeclarationExtensionFunction):
        ext_uri: str = self.extension_uris[ext.extension_uri_reference]
        match ext_uri:
            case "https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml":
                match ext.name:
                    case "or":
                        self.functions[ext.function_anchor] = se.or_
                    case "and":
                        self.functions[ext.function_anchor] = se.and_
                    case "xor":
                        self.functions[ext.function_anchor] = se.xor
                    case "not":
                        self.functions[ext.function_anchor] = se.not_
                    case _:
                        raise NotImplementedError(f"Function name {ext.name} not supported")
            case "https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml":
                match ext.name:
                    case "equal":
                        self.functions[ext.function_anchor] = se.eq
                    case "not_equal":
                        self.functions[ext.function_anchor] = se.neq
                    case "lt":
                        self.functions[ext.function_anchor] = se.lt
                    case "lte":
                        self.functions[ext.function_anchor] = se.lte
                    case "gt":
                        self.functions[ext.function_anchor] = se.gt
                    case "gte":
                        self.functions[ext.function_anchor] = se.gte
                    case "is_null":
                        self.functions[ext.function_anchor] = se.is_null
                    case "is_not_null":
                        self.functions[ext.function_anchor] = se.is_not_null
                    case _:
                        raise NotImplementedError(f"Function name {ext.name} not supported")
            case uri:
                raise NotImplementedError(f"Function extension URI {uri} not supported")

    def _extension_type(self, ext: SimpleExtensionDeclarationExtensionType):
        ext_uri: str = self.extension_uris[ext.extension_uri_reference]
        match ext_uri:
            case "https://github.com/apache/arrow/blob/main/format/substrait/extension_types.yaml":
                match ext.name:
                    case "null":
                        self.type_factories[ext.type_anchor] = pa.null
                    case "interval_month_day_nano":
                        self.type_factories[ext.type_anchor] = pa.month_day_nano_interval
                    case "u8":
                        self.type_factories[ext.type_anchor] = pa.uint8
                    case "u16":
                        self.type_factories[ext.type_anchor] = pa.uint16
                    case "u32":
                        self.type_factories[ext.type_anchor] = pa.uint32
                    case "u64":
                        self.type_factories[ext.type_anchor] = pa.uint64
                    case "fp16":
                        self.type_factories[ext.type_anchor] = pa.float16
                    case "date_millis":
                        self.type_factories[ext.type_anchor] = pa.date64
                    case "time_seconds":
                        self.type_factories[ext.type_anchor] = lambda: pa.time32("s")
                    case "time_millis":
                        self.type_factories[ext.type_anchor] = lambda: pa.time32("ms")
                    case "time_nanos":
                        self.type_factories[ext.type_anchor] = lambda: pa.time64("ns")
                    case "large_string":
                        self.type_factories[ext.type_anchor] = pa.large_string
                    case "large_binary":
                        self.type_factories[ext.type_anchor] = pa.large_binary
                    case "decimal256":
                        self.type_factories[ext.type_anchor] = pa.decimal256
                    case "large_list":
                        self.type_factories[ext.type_anchor] = pa.large_list
                    case "fixed_size_list":
                        self.type_factories[ext.type_anchor] = pa.list_
                    case "duration":
                        self.type_factories[ext.type_anchor] = pa.duration
            case uri:
                raise NotImplementedError(f"Type extension URI {uri} not support")

    def _extension_type_variation(self, ext: SimpleExtensionDeclarationExtensionTypeVariation):
        raise NotImplementedError()

    def _expr(self, expr: Expression) -> Expr:
        match betterproto2.which_one_of(expr, "rex_type"):
            case "literal", e:
                return self._expr_literal(e)
            case "selection", e:
                return self._expr_selection(e)
            case "scalar_function", e:
                return self._expr_scalar_function(e)
            case "window_function", _:
                raise ValueError("Window functions are not supported in Spiral push-down")
            case "if_then", e:
                return self._expr_if_then(e)
            case "switch", e:
                return self._expr_switch(e)
            case "singular_or_list", _:
                raise ValueError("singular_or_list is not supported in Spiral push-down")
            case "multi_or_list", _:
                raise ValueError("multi_or_list is not supported in Spiral push-down")
            case "cast", e:
                return self._expr_cast(e)
            case "subquery", _:
                raise ValueError("Subqueries are not supported in Spiral push-down")
            case "nested", e:
                return self._expr_nested(e)
            case _:
                raise NotImplementedError(f"Expression type {expr.rex_type} not implemented")

    def _expr_literal(self, expr: ExpressionLiteral):
        # TODO(ngates): the Spiral literal expression is quite weakly typed...
        #  Maybe we can switch to Vortex?
        simple = {
            "boolean",
            "i8",
            "i16",
            "i32",
            "i64",
            "fp32",
            "fp64",
            "string",
            "binary",
            "fixed_char",
            "var_char",
            "fixed_binary",
        }

        match betterproto2.which_one_of(expr, "literal_type"):
            case type_, v if type_ in simple:
                return se.scalar(pa.scalar(v))
            case "timestamp", v:
                return se.scalar(pa.scalar(v, type=pa.timestamp("us")))
            case "date", v:
                return se.scalar(pa.scalar(v, type=pa.date32()))
            case "time", v:
                # Substrait time is us since midnight. PyArrow only supports ms.
                v: int
                v = int(v / 1000)
                return se.scalar(pa.scalar(v, type=pa.time32("ms")))
            case "null", _null_type:
                # We need a typed null value
                raise NotImplementedError()
            case "struct", v:
                v: ExpressionLiteralStruct
                # Hmm, v has fields, but no field names. I guess we return a list and the type is applied later?
                raise NotImplementedError()
            case "list", v:
                v: ExpressionLiteralList
                return pa.scalar([self._expr_literal(e) for e in v.values])
            case "user_defined", v:
                v: ExpressionLiteralUserDefined
                raise NotImplementedError()
            case literal_type, _:
                raise NotImplementedError(f"Literal type not supported: {literal_type}")

    def _expr_selection(self, expr: ExpressionFieldReference):
        match betterproto2.which_one_of(expr, "root_type"):
            case "root_reference", _:
                # The reference is relative to the root
                base_expr = self.scope
                base_type = pa.struct(self.schema)
            case _:
                raise NotImplementedError("Only root_reference expressions are supported")

        match betterproto2.which_one_of(expr, "reference_type"):
            case "direct_reference", direct_ref:
                return self._expr_direct_reference(base_expr, base_type, direct_ref)
            case "masked_reference", masked_ref:
                return self._expr_masked_reference(base_expr, base_type, masked_ref)
            case _:
                raise NotImplementedError()

    def _expr_direct_reference(self, scope: Expr, scope_type: pa.StructType, expr: ExpressionReferenceSegment):
        match betterproto2.which_one_of(expr, "reference_type"):
            case "map_key", ref:
                raise NotImplementedError("Map types not yet supported in Spiral")
            case "struct_field", ref:
                ref: ExpressionReferenceSegmentStructField
                field_name = scope_type.field(ref.field).name
                scope = se.getitem(scope, field_name)
                scope_type = scope_type.field(ref.field).type
                if ref.is_set("child"):
                    return self._expr_direct_reference(scope, scope_type, ref.child)
                return scope
            case "list_element", ref:
                ref: ExpressionReferenceSegmentListElement
                scope = se.getitem(scope, ref.offset)
                scope_type = scope_type.field(ref.field).type
                if ref.is_set("child"):
                    return self._expr_direct_reference(scope, scope_type, ref.child)
                return scope
            case "", ref:
                # Because Proto... we hit this case when we recurse into a child node and it's actually "None".
                return scope
            case _:
                raise NotImplementedError()

    def _expr_masked_reference(self, scope: Expr, scope_type: pa.StructType, expr: ExpressionMaskExpression):
        raise NotImplementedError("Masked references are not yet supported in Spiral push-down")

    def _expr_scalar_function(self, expr: ExpressionScalarFunction):
        args = [self._expr(arg.value) for arg in expr.arguments]
        return self.functions[expr.function_reference](*args)
