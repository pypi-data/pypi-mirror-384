from typing import Any, Dict, Iterable, Iterator, Optional, List, get_args, get_origin, Union
from datetime import datetime
from decimal import Decimal
import json
import re
from ._satya import StreamValidatorCore
from . import ValidationError, ValidationResult
from .json_loader import load_json

class StreamValidator:
    def __init__(self):
        self._core = StreamValidatorCore()
        # Compatibility alias expected by some benchmarks (validator._validator)
        self._validator = self._core
        # Keep a simple registry for introspection helpers, if needed later
        self._type_registry: Dict[str, Dict[str, Any]] = {}
        # Record root field Python types for light coercions
        self._root_types: Dict[str, Any] = {}
        # Store constraints at Python level to supplement/override core behavior
        self._constraints: Dict[str, Dict[str, Any]] = {}

    # --- Helpers ---
    def _type_to_str(self, tp: Any) -> str:
        """Convert Python/typing types to the string representation expected by the core."""
        # Handle typing Any
        try:
            from typing import Any as TypingAny
        except Exception:  # pragma: no cover
            TypingAny = object

        if tp is None:
            return "any"
        if tp is TypingAny:
            return "any"
        # Builtins
        if tp is str:
            return "str"
        if tp is int:
            return "int"
        if tp is float:
            return "float"
        if tp is bool:
            return "bool"
        if tp is Decimal:
            # Map Decimal to float for core parsing, we keep Decimal in Python layer
            return "float"
        if tp is datetime:
            # Core treats this as string; we validate/parse at Python layer
            return "str"

        # typing constructs
        origin = get_origin(tp)
        # Optional[T] or Union[..., None]
        if origin is Union:
            args = [a for a in get_args(tp)]
            non_none = [a for a in args if a is not type(None)]  # noqa: E721
            if len(non_none) == 1:
                return self._type_to_str(non_none[0])
        if origin is list or origin is List:  # type: ignore[name-defined]
            inner = get_args(tp)[0] if get_args(tp) else Any
            return f"List[{self._type_to_str(inner)}]"
        if origin is dict or origin is Dict:  # type: ignore[name-defined]
            # Only value type is represented in the core parser
            args = get_args(tp)
            value_tp = args[1] if len(args) >= 2 else Any
            return f"Dict[{self._type_to_str(value_tp)}]"

        # Model subclasses -> custom type by class name
        try:
            # Local import to avoid circular dependency at module import time
            from . import Model  # type: ignore
            if isinstance(tp, type) and issubclass(tp, Model):
                return tp.__name__
        except Exception:
            pass

        # Fallback to string name
        return getattr(tp, "__name__", str(tp))

    # --- Schema definition API ---
    def add_field(self, name: str, field_type: Any, required: bool = True):
        """Add a field to the root schema. Accepts Python/typing types or core type strings."""
        field_str = field_type if isinstance(field_type, str) else self._type_to_str(field_type)
        # Save python type for coercions if possible
        self._root_types[name] = field_type
        return self._core.add_field(name, field_str, required)

    def set_constraints(
        self,
        field_name: str,
        *,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        pattern: Optional[str] = None,
        email: Optional[bool] = None,
        url: Optional[bool] = None,
        ge: Optional[int] = None,
        le: Optional[int] = None,
        gt: Optional[int] = None,
        lt: Optional[int] = None,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        unique_items: Optional[bool] = None,
        enum_values: Optional[List[str]] = None,
    ):
        """Set constraints for a root field on the core validator."""
        # Store for Python-side checks
        self._constraints.setdefault(field_name, {}).update({
            "min_length": min_length,
            "max_length": max_length,
            "min_value": min_value,
            "max_value": max_value,
            "pattern": pattern,
            "email": email,
            "url": url,
            "ge": ge,
            "le": le,
            "gt": gt,
            "lt": lt,
            "min_items": min_items,
            "max_items": max_items,
            "unique_items": unique_items,
            "enum_values": enum_values,
        })
        # Do not pass pattern to core; enforce locally to avoid cross-engine regex differences
        core_pattern = None
        
        # Only pass integer constraints to core (Rust expects integers)
        # Float constraints are enforced in Python layer
        core_ge = int(ge) if ge is not None and isinstance(ge, (int, float)) and ge == int(ge) else None
        core_le = int(le) if le is not None and isinstance(le, (int, float)) and le == int(le) else None
        core_gt = int(gt) if gt is not None and isinstance(gt, (int, float)) and gt == int(gt) else None
        core_lt = int(lt) if lt is not None and isinstance(lt, (int, float)) and lt == int(lt) else None
        
        return self._core.set_field_constraints(
            field_name,
            min_length,
            max_length,
            min_value,
            max_value,
            core_pattern,
            email,
            url,
            core_ge,
            core_le,
            core_gt,
            core_lt,
            min_items,
            max_items,
            unique_items,
            enum_values,
        )

    def define_custom_type(self, type_name: str):
        """Define a new custom type."""
        self._type_registry.setdefault(type_name, {})
        return self._core.define_custom_type(type_name)

    def add_field_to_custom_type(self, type_name: str, field_name: str, field_type: Any, required: bool = True):
        """Add a field to a custom type. Accepts Python/typing types or core type strings."""
        field_str = field_type if isinstance(field_type, str) else self._type_to_str(field_type)
        self._type_registry.setdefault(type_name, {})[field_name] = field_str
        return self._core.add_field_to_custom_type(type_name, field_name, field_str, required)

    # Compatibility with older registration helper
    def define_type(self, type_name: str, fields: Dict[str, Any], doc: Optional[str] = None):
        """Compatibility shim: define a custom type and add its fields.
        'fields' may contain Python/typing types or core type strings.
        """
        self.define_custom_type(type_name)
        for fname, ftype in fields.items():
            self.add_field_to_custom_type(type_name, fname, ftype, required=True)
        return None

    # --- Validation API ---
    def validate_batch(self, items: Iterable[dict]):
        """Validate a batch of items and return a list of booleans."""
        return self._core.validate_batch(list(items))

    def validate(self, item: dict) -> ValidationResult:
        """Validate a single item and return a ValidationResult with optional error details."""
        try:
            # OPTIMIZATION: Use BLAZE validator (ZERO-COPY, SEMI-PERFECT HASHING!)
            if hasattr(self, '_blaze_validator'):
                try:
                    validated = self._blaze_validator.validate(item)
                    # Still need to validate nested models (TODO: move to Rust)
                    validated = self._validate_nested_models(validated)
                    return ValidationResult(value=validated)
                except Exception as e:
                    # Validation failed in Rust
                    return ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])
            
            # FALLBACK: Use old BlazeModelValidator if available
            if hasattr(self, '_blaze_model_validator'):
                try:
                    validated = self._blaze_model_validator.validate(item)
                    validated = self._validate_nested_models(validated)
                    return ValidationResult(value=validated)
                except Exception as e:
                    return ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])
            
            # FALLBACK: Use old Blaze fast path if available
            if hasattr(self, '_blaze_fast_path') and not self._has_complex_constraints():
                try:
                    validated = self._blaze_fast_path.validate_fast(item)
                    validated = self._validate_nested_models(validated)
                    return ValidationResult(value=validated)
                except Exception:
                    # Fall through to full validation
                    pass
            
            # Apply light, best-effort coercions before sending to core
            coerced = self._coerce_item(item)
            # Apply Python-side simple constraints that are reliable locally and accumulate errors
            py_errors: List[ValidationError] = []
            for fname, cons in self._constraints.items():
                if fname not in coerced:
                    continue
                v = coerced.get(fname)
                # Strings: min_length / max_length / pattern
                if isinstance(v, str):
                    s_trim = v.strip()
                    if cons.get("min_length") is not None and len(s_trim) < int(cons["min_length"]):
                        py_errors.append(ValidationError(field=fname, message=f"String shorter than min_length={cons['min_length']}", path=[fname]))
                    if cons.get("max_length") is not None and len(v) > int(cons["max_length"]):
                        py_errors.append(ValidationError(field=fname, message=f"String longer than max_length={cons['max_length']}", path=[fname]))
                    pat = cons.get("pattern")
                    if pat:
                        import re as _re
                        if _re.match(pat, v) is None:
                            py_errors.append(ValidationError(field=fname, message=f"String does not match pattern: {pat}", path=[fname]))
                    # Email
                    if cons.get("email"):
                        import re as _re
                        email_pat = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                        if _re.match(email_pat, v) is None:
                            py_errors.append(ValidationError(field=fname, message="Invalid email format", path=[fname]))
                    # URL (simple http/https)
                    if cons.get("url"):
                        import re as _re
                        if _re.match(r"^https?://[A-Za-z0-9.-]+(?::\d+)?(?:/[^\s]*)?$", v) is None:
                            py_errors.append(ValidationError(field=fname, message="Invalid URL format", path=[fname]))

                # Integers and Floats: ge/le/gt/lt
                if (isinstance(v, (int, float)) and not isinstance(v, bool)):
                    if cons.get("ge") is not None and v < float(cons["ge"]):
                        py_errors.append(ValidationError(field=fname, message=f"Value must be >= {cons['ge']}", path=[fname]))
                    if cons.get("le") is not None and v > float(cons["le"]):
                        py_errors.append(ValidationError(field=fname, message=f"Value must be <= {cons['le']}", path=[fname]))
                    if cons.get("gt") is not None and v <= float(cons["gt"]):
                        py_errors.append(ValidationError(field=fname, message=f"Value must be > {cons['gt']}", path=[fname]))
                    if cons.get("lt") is not None and v >= float(cons["lt"]):
                        py_errors.append(ValidationError(field=fname, message=f"Value must be < {cons['lt']}", path=[fname]))

                # Lists: min_items/max_items/unique_items
                if isinstance(v, list):
                    if cons.get("min_items") is not None and len(v) < int(cons["min_items"]):
                        py_errors.append(ValidationError(field=fname, message=f"Array must have at least {cons['min_items']} items", path=[fname]))
                    if cons.get("max_items") is not None and len(v) > int(cons["max_items"]):
                        py_errors.append(ValidationError(field=fname, message=f"Array must have at most {cons['max_items']} items", path=[fname]))
                    if cons.get("unique_items"):
                        if len(set(v)) != len(v):
                            py_errors.append(ValidationError(field=fname, message="Array items must be unique", path=[fname]))

                # Enums for strings
                if isinstance(v, str) and cons.get("enum_values"):
                    ev = cons["enum_values"]
                    if v not in ev:
                        py_errors.append(ValidationError(field=fname, message=f"Value not in enum: {ev}", path=[fname]))

            if py_errors:
                return ValidationResult(errors=py_errors)

            ok = self._core.validate_item_internal(coerced)
            if ok:
                # Validate nested models if any
                try:
                    validated = self._validate_nested_models(coerced)
                    return ValidationResult(value=validated)
                except ValueError as e:
                    # Nested model validation failed
                    return ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])
            # Fallback (should not happen since core returns True or raises)
            return ValidationResult(errors=[ValidationError(field="root", message="validation failed", path=[])])
        except Exception as e:  # Capture PyErr from core
            return ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])

    def _has_complex_constraints(self) -> bool:
        """Check if we have constraints that require Python validation (Rust can't handle)"""
        from decimal import Decimal
        
        # Check if we have Decimal fields (need special Python handling)
        for field_type in self._root_types.values():
            if field_type is Decimal:
                return True
        
        # Check for constraints that Rust can't handle yet
        # Rust NOW handles: gt, ge, lt, le, min_length, max_length, min_items, max_items
        # Python still handles: pattern (regex), email, url, enum
        for cons in self._constraints.values():
            if cons.get('pattern') or cons.get('email') or cons.get('url') or cons.get('enum_values'):
                return True
        
        # All other constraints are handled in Rust!
        return False
    
    def _validate_nested_models(self, item: dict) -> dict:
        """Recursively validate nested models in the item."""
        from . import Model
        from typing import get_origin, get_args
        
        validated_item = item.copy()
        
        for field_name, field_type in self._root_types.items():
            if field_name not in item:
                continue
            
            value = item[field_name]
            
            # Unwrap Optional[T]
            origin = get_origin(field_type)
            args = get_args(field_type) if origin is not None else ()
            if origin is Union and type(None) in args:
                non_none = [a for a in args if a is not type(None)]
                field_type = non_none[0] if non_none else field_type
                origin = get_origin(field_type)
                args = get_args(field_type) if origin is not None else ()
            
            # Handle List[Model]
            if origin is list and args:
                inner_type = args[0]
                if isinstance(inner_type, type) and issubclass(inner_type, Model):
                    if isinstance(value, list):
                        # Validate each item in the list
                        validated_list = []
                        for i, item_data in enumerate(value):
                            if isinstance(item_data, dict):
                                # Create model instance (which validates)
                                try:
                                    validated_list.append(inner_type(**item_data))
                                except Exception as e:
                                    raise ValueError(f"Invalid item at index {i} in field '{field_name}': {e}")
                            else:
                                validated_list.append(item_data)
                        validated_item[field_name] = validated_list
            
            # Handle Dict[str, Model]
            elif origin is dict and len(args) >= 2:
                value_type = args[1]
                if isinstance(value_type, type) and issubclass(value_type, Model):
                    if isinstance(value, dict):
                        validated_dict = {}
                        for k, v in value.items():
                            if isinstance(v, dict):
                                try:
                                    validated_dict[k] = value_type(**v)
                                except Exception as e:
                                    raise ValueError(f"Invalid value for key '{k}' in field '{field_name}': {e}")
                            else:
                                validated_dict[k] = v
                        validated_item[field_name] = validated_dict
            
            # Handle direct Model
            elif isinstance(field_type, type) and issubclass(field_type, Model):
                if isinstance(value, dict):
                    try:
                        validated_item[field_name] = field_type(**value)
                    except Exception as e:
                        raise ValueError(f"Invalid nested model in field '{field_name}': {e}")
        
        return validated_item

    def validate_stream(self, items: Iterable[dict], collect_errors: bool = False, *, yield_values: bool = False) -> Iterator[Any]:
        """Validate a stream of items.
        If yield_values=True, yield validated dicts directly when valid. Otherwise yield ValidationResult.
        If collect_errors=False and yield_values=True, only valid dicts are yielded.
        """
        for it in items:
            res = self.validate(it)
            if yield_values:
                if res.is_valid:
                    yield res.value
                elif collect_errors:
                    yield res
            else:
                if res.is_valid or collect_errors:
                    yield res

    # --- Zero-Copy Validation API (TurboAPI Enhancement) ---
    def validate_from_bytes(self, data: bytes, *, streaming: bool = True, zero_copy: bool = True) -> bool:
        """Zero-copy validation directly from bytes (TurboAPI-style).
        
        This method provides maximum performance by:
        1. Avoiding JSON parsing to Python objects
        2. Using streaming validation in Rust
        3. No intermediate copies or allocations
        
        Args:
            data: Raw bytes containing JSON object
            streaming: Use streaming parser (default: True)
            zero_copy: Avoid copies where possible (default: True)
        
        Returns:
            True if valid, False otherwise
        
        Example:
            >>> validator = StreamValidator()
            >>> validator.add_field('name', str)
            >>> json_bytes = b'{"name": "test"}'
            >>> validator.validate_from_bytes(json_bytes)  # Ultra-fast!
            True
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Expected bytes or bytearray")
        
        # Use streaming validation for zero-copy performance
        if streaming and zero_copy:
            return self._core.validate_json_bytes_streaming(data)
        else:
            return self._core.validate_json_bytes(data)
    
    def validate_json_stream(self, stream, *, chunk_size: int = 8192, streaming: bool = True) -> Iterator[bool]:
        """Validate JSON objects from a stream with zero-copy.
        
        Processes chunks of data without building full objects in memory.
        Ideal for large payloads or streaming HTTP requests.
        
        Args:
            stream: File-like object or iterator yielding bytes
            chunk_size: Size of chunks to read (default: 8KB)
            streaming: Use streaming parser (default: True)
        
        Yields:
            bool for each validated object
        
        Example:
            >>> with open('data.ndjson', 'rb') as f:
            ...     for is_valid in validator.validate_json_stream(f):
            ...         print(f"Valid: {is_valid}")
        """
        buffer = b''
        for chunk in iter(lambda: stream.read(chunk_size), b''):
            buffer += chunk
            # Split on newlines for NDJSON format
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                if line.strip():
                    yield self.validate_from_bytes(line, streaming=streaming, zero_copy=True)
        
        # Process remaining data
        if buffer.strip():
            yield self.validate_from_bytes(buffer, streaming=streaming, zero_copy=True)
    
    # --- JSON bytes/str Validation API ---
    def validate_json(self, data: Any, mode: str = "object", streaming: bool = False):
        """Validate JSON provided as bytes or str using Rust core.
        mode:
          - 'object': top-level object -> returns bool
          - 'array' : top-level array of objects -> returns List[bool]
          - 'ndjson': newline-delimited JSON objects -> returns List[bool]
        If streaming=True, uses serde_json streaming validation to avoid building intermediate values.
        """
        mode = mode.lower()
        # Early sanity checks for top-level type and malformed JSON to match tests' expectations
        if isinstance(data, (bytes, bytearray)):
            text = data.decode("utf-8", errors="ignore")
        else:
            text = data if isinstance(data, str) else None

        def first_non_ws_char(s: str | None) -> str | None:
            if not s:
                return None
            for ch in s.lstrip():
                return ch
            return None

        top = first_non_ws_char(text)

        if mode == "object":
            if top == '[':
                raise ValueError("Expected top-level object JSON, got array")
            # Raise for malformed JSON explicitly (tests expect exception)
            if text is not None and not streaming:
                try:
                    json.loads(text)
                except Exception as e:
                    raise e
        elif mode == "array":
            if top == '{':
                raise Exception("Expected top-level array JSON, got object")
            if text is not None and not streaming:
                try:
                    obj = json.loads(text)
                except Exception as e:
                    raise e
        elif mode == "ndjson":
            # Allow empty
            pass
        else:
            raise ValueError(f"Unknown mode: {mode}")
        if mode == "object":
            return (
                self._core.validate_json_bytes_streaming(data)
                if streaming else self._core.validate_json_bytes(data)
            )
        if mode == "array":
            return (
                self._core.validate_json_array_bytes_streaming(data)
                if streaming else self._core.validate_json_array_bytes(data)
            )
        if mode == "ndjson":
            return (
                self._core.validate_ndjson_bytes_streaming(data)
                if streaming else self._core.validate_ndjson_bytes(data)
            )
        raise ValueError(f"Unknown mode: {mode}")

    # --- Convenience APIs returning ValidationResult ---
    def validate_json_object(self, data: Any, *, streaming: bool = False) -> ValidationResult:
        """Validate a top-level JSON object and return a ValidationResult."""
        try:
            ok = self.validate_json(data, mode="object", streaming=streaming)
            if not ok:
                return ValidationResult(errors=[ValidationError(field="root", message="validation failed", path=[])])
            text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
            obj = load_json(text)
            if not isinstance(obj, dict):
                return ValidationResult(errors=[ValidationError(field="root", message="JSON must be an object", path=["root"])])
            return self.validate(obj)
        except Exception as e:
            return ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])

    def validate_json_array(self, data: Any, *, streaming: bool = False) -> List[ValidationResult]:
        """Validate a top-level JSON array of objects and return a per-item ValidationResult list."""
        try:
            _ = self.validate_json(data, mode="array", streaming=streaming)
            text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
            arr = load_json(text)
            if not isinstance(arr, list):
                return [ValidationResult(errors=[ValidationError(field="root", message="JSON must be an array", path=["root"])])]
            results: List[ValidationResult] = []
            for idx, obj in enumerate(arr):
                if not isinstance(obj, dict):
                    results.append(ValidationResult(errors=[ValidationError(field="root", message="Array items must be objects", path=["root", str(idx)])]))
                else:
                    results.append(self.validate(obj))
            return results
        except Exception as e:
            return [ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])]

    def validate_ndjson(self, data: Any, *, streaming: bool = False) -> List[ValidationResult]:
        """Validate NDJSON (one JSON object per line). Returns per-line ValidationResult."""
        try:
            _ = self.validate_json(data, mode="ndjson", streaming=streaming)
            text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
            lines = [ln for ln in (text.splitlines() if isinstance(text, str) else []) if ln.strip()]
            results: List[ValidationResult] = []
            for i, ln in enumerate(lines):
                try:
                    obj = load_json(ln)
                    if not isinstance(obj, dict):
                        results.append(ValidationResult(errors=[ValidationError(field="root", message="Line must be a JSON object", path=["root", str(i)])]))
                    else:
                        results.append(self.validate(obj))
                except Exception as inner_e:
                    results.append(ValidationResult(errors=[ValidationError(field="root", message=str(inner_e), path=["root", str(i)])]))
            return results
        except Exception as e:
            return [ValidationResult(errors=[ValidationError(field="root", message=str(e), path=[])])]

    def validate_batch_results(self, items: Iterable[dict]) -> List[ValidationResult]:
        """Validate a batch of items and return a list of ValidationResult (non-breaking addition)."""
        return [self.validate(it) for it in items]

    # --- Internal helpers ---
    def _coerce_item(self, item: dict) -> dict:
        """Light, best-effort coercion based on declared root field types. Provider-agnostic."""
        if not self._root_types:
            return item
        out: dict = {}
        for k, v in item.items():
            tp = self._root_types.get(k)
            if tp is None:
                out[k] = v
                continue
            # If Optional[...] and value is None, omit the key entirely so core treats it as missing
            origin = get_origin(tp)
            if origin is Union and type(None) in get_args(tp) and v is None:
                continue
            out[k] = self._coerce_value(v, tp)
        return out

    def _coerce_value(self, value: Any, tp: Any) -> Any:
        origin = get_origin(tp)
        # Optional[T] or Union[..., None]
        if origin is Union and type(None) in get_args(tp):
            inner = [a for a in get_args(tp) if a is not type(None)][0] if get_args(tp) else Any
            if value is None:
                return None
            return self._coerce_value(value, inner)
        # Primitives
        try:
            if tp is bool:
                if isinstance(value, str):
                    lv = value.strip().lower()
                    if lv == 'true':
                        return True
                    if lv == 'false':
                        return False
                return value
            if tp is int:
                if isinstance(value, str) and value.strip().lstrip('+-').isdigit():
                    return int(value)
                return value
            if tp is float:
                if isinstance(value, str):
                    try:
                        return float(value)
                    except Exception:
                        return value
                return value
            if tp is Decimal:
                # For Decimal, we need to:
                # 1. Convert string/int/float to Decimal for Python layer
                # 2. But send as float to Rust core (which doesn't understand Decimal objects)
                if isinstance(value, (int, float)):
                    # Already a number - convert to float for Rust core
                    return float(value)
                if isinstance(value, str):
                    try:
                        # Parse string to Decimal, then convert to float for Rust
                        return float(Decimal(value))
                    except Exception:
                        return value
                if isinstance(value, Decimal):
                    # Already a Decimal - convert to float for Rust core
                    return float(value)
                return value
            if tp is str:
                if isinstance(value, (bytes, bytearray)):
                    try:
                        return value.decode('utf-8')
                    except Exception:
                        return value
                return value
            if tp is datetime:
                if isinstance(value, str):
                    s = value.strip()
                    if s.endswith('Z'):
                        s = s[:-1] + '+00:00'
                    try:
                        return datetime.fromisoformat(s)
                    except Exception:
                        return value
                return value
        except Exception:
            return value
        # Containers (shallow): leave as-is for now
        return value

    def _check_python_constraints(self, item: dict) -> List[ValidationError]:
        """Check selected constraints in Python to work around core limitations.
        Returns a list of ValidationError (empty if all checks pass).
        """
        errors: List[ValidationError] = []
        for name, cons in self._constraints.items():
            if name not in item:
                continue
            v = item[name]
            # pattern/email/url on strings
            if isinstance(v, str):
                pat = cons.get("pattern")
                if pat and re.fullmatch(pat, v) is None:
                    errors.append(ValidationError(field=name, message=f"String does not match pattern: {pat}", path=[name]))
                if cons.get("email"):
                    email_re = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if re.fullmatch(email_re, v) is None:
                        errors.append(ValidationError(field=name, message="invalid email format", path=[name]))
                if cons.get("url"):
                    if not (v.startswith("http://") or v.startswith("https://")):
                        errors.append(ValidationError(field=name, message="invalid url format", path=[name]))
                # length checks (trimmed)
                ml = cons.get("min_length")
                if ml is not None and len(v.strip()) < ml:
                    errors.append(ValidationError(field=name, message=f"String length < {ml}", path=[name]))
                mx = cons.get("max_length")
                if mx is not None and len(v) > mx:
                    errors.append(ValidationError(field=name, message=f"String length > {mx}", path=[name]))
                # enum
                ev = cons.get("enum_values")
                if ev and v not in ev:
                    errors.append(ValidationError(field=name, message=f"value not in enum", path=[name]))
            # numeric bounds
            if isinstance(v, (int, float)):
                ge = cons.get("ge")
                if ge is not None and not (v >= ge):
                    errors.append(ValidationError(field=name, message=f"Value must be >= {ge}", path=[name]))
                le = cons.get("le")
                if le is not None and not (v <= le):
                    errors.append(ValidationError(field=name, message=f"Value must be <= {le}", path=[name]))
                gt = cons.get("gt")
                if gt is not None and not (v > gt):
                    errors.append(ValidationError(field=name, message=f"Value must be > {gt}", path=[name]))
                lt = cons.get("lt")
                if lt is not None and not (v < lt):
                    errors.append(ValidationError(field=name, message=f"Value must be < {lt}", path=[name]))
        return errors

    @property
    def batch_size(self) -> int:
        """Get the current batch size from the core."""
        return self._core.get_batch_size()

    def set_batch_size(self, size: int):
        """Set the batch size in the core."""
        self._core.set_batch_size(size)
 