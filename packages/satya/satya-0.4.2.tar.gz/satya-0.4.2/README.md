<p align="center">
  <img src="/assets/satya_logo.jpg" alt="Satya Logo" width="1600"/>
</p>

<h1 align="center"><b>Satya (सत्य)</b></h1>
<div align="center">
  
[![PyPI version](https://badge.fury.io/py/satya.svg)](https://badge.fury.io/py/satya)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Versions](https://img.shields.io/pypi/pyversions/satya.svg)](https://pypi.org/project/satya/)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)

</div>

---

# 🚀 THE FASTEST Python Validation Library

Satya (सत्य) - Sanskrit for **"truth"** - delivers **blazing-fast validation** with **100% Pydantic-compatible API**. Built on Rust with PyO3, Satya achieves **5.46× faster batch validation** while maintaining **field access parity** with Pydantic.

## 🎯 What's New in v0.4.12

### ✨ **Critical DX Fixes & Pydantic Compatibility**

**Issue #12 FIXED**: Field access now returns actual values, not Field objects!
```python
user.age + 5  # ✅ Works! (was TypeError before)
user.name.upper()  # ✅ Works!
if user.score > 90:  # ✅ Works!
```

**Issue #9 FIXED**: Full Pydantic `Field` compatibility!
```python
from satya import Model, Field
from typing import List

class User(Model):
    tags: List[str] = Field(default_factory=list)  # ✅ Now supported!
    created_at: datetime = Field(default_factory=datetime.now)
```

**Example #3 FIXED**: Nested model validation now works in `validator.validate()`!

👉 **[See Full Changelog](CHANGELOG.md)** | **[Migration Guide](PYDANTIC_MIGRATION.md)**

## 📊 Performance vs Pydantic 2.12.0

<p align="center">
  <img src="benchmarks/pydantic_comparison_graph.png" alt="Satya vs Pydantic Performance" width="100%"/>
</p>

### Benchmark Results

> **⚠️ IMPORTANT: v0.4.12 Performance Status**
> 
> This release **prioritizes correctness over speed**. We fixed critical bugs (Issues #9, #12) that made previous versions unusable in production. The trade-off is that **Pydantic is currently 5-20× faster** than Satya v0.4.12.

**Current Performance (v0.4.12 vs Pydantic 2.12.0):**

| Test | Satya v0.4.12 | Pydantic 2.12.0 | Winner |
|------|---------------|-----------------|--------|
| Simple Validation | 104K ops/sec | 1,844K ops/sec | Pydantic 17.7× faster |
| With Constraints | 84K ops/sec | 1,736K ops/sec | Pydantic 20.6× faster |
| Field Access | 11M ops/sec | 37M ops/sec | Pydantic 3.3× faster |
| Batch (50K) | 162K ops/sec | 894K ops/sec | Pydantic 5.5× faster |
| Nested Models | 59K ops/sec | 1,328K ops/sec | Pydantic 22.6× faster |

**What You Get in v0.4.12:**
- ✅ **Actually works** (field access, constraints, nested models all correct)
- ✅ **100% Pydantic API compatibility** (including `default_factory`)
- ✅ **291/291 tests passing** (previous versions had 73 failures)
- ⚠️ **Slower than Pydantic** (but at least it works!)

**The Trade-off:**
- **v0.4.12**: Slow but CORRECT → **Use this for production**
- **v0.3.x**: Fast but BROKEN → Don't use (field access returns Field objects!)

**Future Plans (v0.5.0):**
- Optimize validation path to match/exceed Pydantic speed
- Keep all correctness fixes from v0.4.12
- Goal: Best of both worlds (correct AND fast)

**Previous Performance (v0.3.86 - before DX fixes):**

| Metric | Pydantic 2.12.0 | Satya 0.3.86 | Speedup |
|--------|-----------------|-------------|---------|
| **Single Validation** | 1.02M ops/sec | 1.10M ops/sec | **1.09× faster** ⚡ |
| **Batch Validation** | 915K ops/sec | **5.0M ops/sec** | **5.46× faster** 🚀 |
| **Field Access** | 65.3M/sec | 66.2M/sec | **1.01× (parity!)** 🔥 |

> **Latest Version: v0.4.12** - Python 3.8-3.14 supported. **Production-ready** with correct behavior (but slower than Pydantic for now). 🎯

---

## ⚡ Quick Start (30 seconds to production!)

### Installation
```bash
pip install satya
```

### Drop-in Pydantic Replacement
```python
# Just change the import - that's it!
from satya import BaseModel, Field

class User(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)
    email: str = Field(email=True)

# Single validation (1.09× faster than Pydantic)
user = User.model_validate_fast({"name": "Alice", "age": 30, "email": "alice@example.com"})

# Batch validation (5.46× faster than Pydantic!)
users = User.validate_many([
    {"name": "Alice", "age": 30, "email": "alice@example.com"},
    {"name": "Bob", "age": 25, "email": "bob@example.com"}
])

print(f"✅ Validated {len(users)} users at 5× Pydantic speed!")
```

**That's it!** Zero code changes needed - just faster validation! 🎉

---

## 📊 Performance at a Glance

<p align="center">
  <img src="benchmarks/performance_comparison_simple.png" alt="Performance Comparison" width="100%"/>
</p>

**Key Takeaways:**
- 🚀 **Batch Validation**: 5.46× faster (5.0M queries/sec vs 915K)
- ⚡ **Single Validation**: 1.09× faster (1.1M queries/sec vs 1.02M)
- 🔥 **Field Access**: 1.01× parity (66.2M queries/sec vs 65.3M)

---

## 🎉 What's New in v0.4.0 - Production Ready Release!

### **5.46× FASTER BATCH VALIDATION + FIELD ACCESS PARITY!**

This release delivers production-ready performance with comprehensive benchmarks against Pydantic 2.12.0:

**✨ Key Features**
- ✅ **Python 3.14 Support** - First-day support for Python 3.14.0!
- ✅ **Comprehensive Benchmarks** - Fair comparison with Pydantic 2.12.0
- ✅ **Beautiful Graphs** - Visual performance comparison
- ✅ **100% API Compatible** - Drop-in Pydantic replacement
- ✅ **Production Ready** - Stable, tested, and documented

**📊 Performance vs Pydantic 2.12.0**
- **Single Validation**: 1.09× faster
- **Batch Validation**: **5.46× faster** 🚀
- **Field Access**: 1.01× (parity!)
- **Complex Nested**: 1.11× faster

**🔬 Advanced VM Optimizations (Built on 30+ Years of Research)**

Satya implements cutting-edge VM optimization techniques from V8, PyPy, and Self:

**Hidden Classes Implementation**
- **SchemaShape** - Shared "hidden class" descriptors across all instances (V8-inspired)
- **Interned String Pointers** - O(1) field name comparison via pointer equality
- **Global Shape Registry** - Thread-safe cache with Arc-based sharing
- **UltraFastModel** - Zero-dict slot-based architecture for maximum speed

**BLAZE Compilation Pipeline**
- **Schema Compilation** - Schemas compiled to optimized Rust validators
- **Adaptive Parallelism** - Smart serial/parallel switching based on batch size
- **Lazy Regex** - Regex patterns compiled once and cached
- **validate_batch_hybrid** - Direct Python dict validation without JSON serialization overhead

**Performance Breakthroughs**
- **Field access**: 5.2M/s → **62.9M/s** (12× improvement!)
- **Single-object**: 481K/s → **1,188K/s** (2.5× improvement!)
- **Batch**: 820K/s → **4.2M/s** (5.1× improvement!)

**📚 Academic Foundations**
- Hölzle et al. (OOPSLA '91) - "Optimizing Dynamically-Typed OO Languages with PICs"
- Bolz et al. (VMIL '09) - "Tracing the Meta-Level: PyPy's Tracing JIT"
- Chevalier-Boisvert et al. (PLDI 2015) - "Shape-Based Optimization in HLVMs"

**🎯 Perfect For**
- High-throughput APIs processing thousands of requests
- ETL pipelines validating millions of records
- ML data validation at scale
- Microservices with bulk operations

**📖 Complete Technical Deep Dive**
- [Release Notes](RELEASE_v0.4.0.md) - Full v0.4.0 details
- [Implementation Guide](IMPLEMENTATION_GUIDE.md) - Architecture deep dive
- [Performance Analysis](SUMMARY_IMPROVEMENTS.md) - Complete optimization journey from 5.2M/s to 62.9M/s field access

---

## 📋 What's New in v0.3.85

- **List[Model] Support (Highly Requested!)**
  - Nested lists of models now validate recursively at construction time (`List[MyModel]`, `Optional[List[MyModel]]`, etc.)
  - Automatic skipping of nested lists/dicts during Rust registration prevents type mismatches
  - Maintains Satya's 2.4M+ items/sec throughput with zero regressions
- **Fixed Income Securities Example**: `examples/fixed_income_securities.py` shows real-world validation for bond indices, nested lists, and performance measurement.
- **Comprehensive Test Suite**: `tests/test_fixed_income_securities.py` adds 10 tests covering valid/invalid nested data and batch performance.

## 📋 What's New in v0.3.83

### 🎯 NEW: Rust-Backed Scalar Validators (Phase 1 Complete!)
- **StringValidator**: High-performance string validation with min/max length, pattern, email, URL support
  - **1.1M+ validations/second** - 2.3x faster than Python loops
  - Email validation, regex patterns, enum constraints
  - Batch processing support for maximum throughput
- **IntValidator**: Integer validation with bounds (ge/le/gt/lt) and constraints
  - Type-strict validation (excludes bool)
  - `multiple_of` divisibility checks
  - Enum value constraints
- **NumberValidator**: Float/number validation with epsilon tolerance
  - Supports both int and float inputs
  - Exclusive bounds (gt/lt) for strict ranges
  - `multiple_of` with floating-point precision handling
- **BooleanValidator**: Type-strict boolean validation
  - Rejects integers masquerading as booleans
  - Enum constraints for flag validation

### 🔧 ABSENT Sentinel for Optional Fields
- **ABSENT vs None**: Distinguish between explicitly set `None` and missing fields
- **fastjsonschema compatibility**: Prevents auto-injection of default values
- **Clean API**: `is_absent()` and `filter_absent()` utilities
- Matches JSON Schema behavior where absent fields stay absent

### ⚡ Performance Impact
- **Before**: Only 30-40% of Poetry schemas used Rust (objects only)
- **Now**: 80-90% of schemas can use Rust fast path (scalars + objects)
- **Result**: **10-20x overall performance improvement** unlocked for JSON Schema validation!

### 📚 New Examples & Documentation
- Comprehensive `examples/scalar_validation_example.py` with performance demos
- Updated README with scalar validator guide
- Full API documentation for all new validators

## 📋 What's New in v0.3.82

### 🚀 PyO3 0.26 & Python 3.13 Support + Performance Breakthrough
- **PyO3 0.26 Migration**: Fully migrated from PyO3 0.18 to 0.26 with modern Rust bindings API
- **Python 3.13 Compatible**: Full support for Python 3.13 (including free-threaded build)
- **200+ API Updates**: Complete migration to `Bound<'_, PyAny>` API for improved memory safety
- **Modern GIL Management**: Updated to use `Python::detach` instead of deprecated `allow_threads`
- **🔥 82x Performance Boost**: Satya is now THE FASTEST Python validation library!
  - **4.2 MILLION items/sec** - 5.2x faster than fastjsonschema, 82x faster than jsonschema
  - **98.8% faster** - validates 1M items in 0.24s vs jsonschema's 19.32s
  - Uses `validate_batch_hybrid` for direct Python dict validation without JSON overhead
  - Fixed regex recompilation bottleneck for 32x faster email validation
- **Future-Proof**: Ready for Python 3.13's no-GIL features when PyO3 adds full support

### 🏗️ Enhanced Nested Model Validation Support
- **Dict[str, CustomModel] Support**: Complete validation support for dictionary structures containing custom model instances
- **MAP-Elites Algorithm Support**: Native support for complex archive structures like `Dict[str, ArchiveEntry]`
- **Hierarchical Data Structures**: Full support for nested model dictionaries in configuration management and ML pipelines
- **Recursive Model Resolution**: Automatic dependency analysis and topological sorting for proper validation order

### 🔧 ModelRegistry System
- **Dependency Tracking**: Automatically analyzes and tracks model relationships
- **Topological Sorting**: Ensures models are validated in the correct dependency order
- **Circular Dependency Detection**: Prevents infinite loops in complex model graphs

### 📦 Source Distribution Support
- **SDist Builds**: Proper source distribution builds enabling `--no-binary` installations
- **Docker Run CI/CD**: Improved GitHub Actions compatibility with direct docker run commands
- **Cross-Platform Compatibility**: Full support for Linux, macOS, and Windows across all architectures

### 🎯 Use Cases Enabled
```python
from satya import Model, Field
from typing import Dict

class ArchiveEntry(Model):
    config: SystemConfig
    performance: float = Field(ge=-1000.0, le=100000.0)

class MapElitesArchive(Model):
    resolution: int = Field(ge=1, le=20)
    archive: Dict[str, ArchiveEntry] = Field(description="Archive entries")

# This now works perfectly!
data = {
    "resolution": 5,
    "archive": {
        "cell_1_2": {"config": {"buffer_size": 1024}, "performance": 95.5}
    }
}
archive = MapElitesArchive(**data)  # Works perfectly!
```

### 🧪 Comprehensive Testing
- Added complete test suite with 4 test methods covering nested Dict[str, Model] patterns
- All 150+ tests pass with comprehensive coverage
- Source distribution builds tested and verified

## Key Features:
- **High-performance validation** with Rust-powered core
- **Batch processing** with configurable batch sizes for optimal throughput
- **Stream processing support** for handling large datasets
- **Comprehensive validation** including email, URL, regex, numeric ranges, and more
- **Type coercion** with intelligent type conversion
- **Decimal support** for financial-grade precision
- **Compatible with standard Python type hints**
- **OpenAI-compatible schema generation**
- **Minimal memory overhead**

## Quick Start (new DX):
```python
from satya import Model, Field, ModelValidationError

class User(Model):
    id: int = Field(description="User ID")
    name: str = Field(description="User name")
    email: str = Field(description="Email address")
    active: bool = Field(default=True)

# Enable batching for optimal performance
validator = User.validator()
validator.set_batch_size(1000)  # Recommended for most workloads

# Process data efficiently
for valid_item in validator.validate_stream(data):
    process(valid_item)
```

## Example 2:

```python
from typing import Optional
from decimal import Decimal
from satya import Model, Field, List

# Pretty printing (optional)
Model.PRETTY_REPR = True

class User(Model):
    id: int
    name: str = Field(default='John Doe')
    email: str = Field(email=True)  # RFC 5322 compliant email validation
    signup_ts: Optional[str] = Field(required=False)
    friends: List[int] = Field(default=[])
    balance: Decimal = Field(ge=0, description="Account balance")  # Decimal support

external_data = {
    'id': '123',
    'email': 'john.doe@example.com',
    'signup_ts': '2017-06-01 12:22',
    'friends': [1, '2', b'3'],
    'balance': '1234.56'
}
validator = User.validator()
validator.set_batch_size(1000)  # Enable batching for performance
result = validator.validate(external_data)
user = User(**result.value)
print(user)
#> User(id=123, name='John Doe', email='john.doe@example.com', signup_ts='2017-06-01 12:22', friends=[1, 2, 3], balance=1234.56)
```

## 🎯 Scalar Validators (NEW in v0.3.82)

Satya now includes **Rust-backed scalar validators** for primitive types, enabling blazing-fast validation without the overhead of creating Model classes:

```python
from satya import StringValidator, IntValidator, NumberValidator, BooleanValidator

# String validation with constraints
email_validator = StringValidator(email=True)
result = email_validator.validate("user@example.com")
print(f"Valid: {result.is_valid}")  # Valid: True

# Pattern matching
username_validator = StringValidator(pattern=r'^[a-zA-Z0-9_]{3,20}$', min_length=3, max_length=20)
result = username_validator.validate("john_doe_123")
print(f"Valid: {result.is_valid}")  # Valid: True

# Integer validation with bounds
age_validator = IntValidator(ge=0, le=150)
result = age_validator.validate(42)
print(f"Valid: {result.is_valid}, Value: {result.value}")  # Valid: True, Value: 42

# Float/Number validation
price_validator = NumberValidator(ge=0.0, le=1000000.0)
result = price_validator.validate(99.99)
print(f"Valid: {result.is_valid}")  # Valid: True

# Boolean validation
flag_validator = BooleanValidator()
result = flag_validator.validate(True)
print(f"Valid: {result.is_valid}")  # Valid: True

# Batch validation for maximum performance
values = ["test" + str(i) for i in range(100000)]
string_validator = StringValidator(min_length=4)
results = string_validator.validate_batch(values)
print(f"Validated {len(results)} strings at Rust speed!")  # 1M+ validations/sec
```

### Scalar Validator Features

**StringValidator:**
- `min_length` / `max_length` - Length constraints
- `pattern` - Regex pattern matching
- `email` - RFC 5322 compliant email validation
- `url` - URL format validation
- `enum` - Enum value constraints

**IntValidator:**
- `ge` / `le` / `gt` / `lt` - Numeric bounds (greater/less than or equal)
- `multiple_of` - Divisibility constraints
- `enum` - Enum value constraints

**NumberValidator:**
- `ge` / `le` / `gt` / `lt` - Float bounds
- `multiple_of` - Divisibility constraints (with epsilon tolerance)
- `enum` - Enum value constraints

**BooleanValidator:**
- Type-strict boolean validation
- `enum` - Enum value constraints

### When to Use Scalar Validators vs Models

**Use Scalar Validators when:**
- Validating individual primitive values
- Building custom validation pipelines
- Maximum performance for simple types is critical
- You need fine-grained control over validation logic

**Use Models when:**
- Validating structured objects with multiple fields
- You need Pydantic-like developer experience
- Working with nested/complex data structures
- You want automatic JSON schema generation

### Performance

Scalar validators leverage Satya's Rust core for maximum performance:
- **1M+ validations/second** for strings
- **500K+ validations/second** for integers with bounds
- **Zero-copy** validation where possible
- **Batch processing** support for optimal throughput

See `examples/scalar_validation_example.py` for a comprehensive demonstration.

## 📋 JSON Schema Compiler (NEW in v0.3.83)

Satya now includes a **JSON Schema compiler** that makes it a drop-in replacement for fastjsonschema with 5-10x better performance:

```python
from satya import compile_json_schema

# Compile any JSON Schema document
schema = {
    "type": "string",
    "minLength": 3,
    "maxLength": 100,
    "pattern": "^[a-zA-Z0-9_-]+$"
}

validator = compile_json_schema(schema)
result = validator.validate("my-package-name")
print(result.is_valid)  # True - validated at Rust speed!
```

### Supported JSON Schema Features

✅ **Primitive Types**:
- `type: string` - With minLength, maxLength, pattern, format (email, uri)
- `type: integer` - With minimum, maximum, exclusiveMinimum/Maximum, multipleOf
- `type: number` - Float validation with bounds
- `type: boolean` - Type-strict validation

✅ **Arrays**:
- `type: array` - With items, minItems, maxItems, uniqueItems

✅ **Constraints**:
- Length constraints (minLength, maxLength)
- Numeric bounds (minimum, maximum, exclusive variants)
- Pattern matching (regex)
- Format validation (email, url)
- Enum values
- Multiple of (divisibility)

### Real-World Example: Poetry Integration

```python
# Package name validation (Poetry use case)
package_schema = {
    "type": "string",
    "pattern": "^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$"
}
package_validator = compile_json_schema(package_schema)

# Version validation
version_schema = {
    "type": "string",
    "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
}
version_validator = compile_json_schema(version_schema)

# Validate thousands of packages at Rust speed
packages = ["requests", "numpy", "pandas", ...]
results = package_validator.validate_batch(packages)  # 1.2M/sec!
```

### Performance

- **1.2M+ validations/second** for JSON Schema compilation
- **100% Rust optimization** for supported types
- **5-10x faster** than fastjsonschema
- **95%+ schema coverage** for tools like Poetry

### Optimization Reporting

```python
from satya import JSONSchemaCompiler

compiler = JSONSchemaCompiler()
for schema in my_schemas:
    validator = compiler.compile(schema)

report = compiler.get_optimization_report()
print(f"Rust-optimized: {report['optimization_percentage']}%")
```

See `examples/json_schema_example.py` for a complete demonstration.

## 🚀 Performance

### Latest Benchmark Results (v0.3.7)

Our comprehensive benchmarks demonstrate Satya's exceptional performance when using batch processing:

<p align="center">
  <img src="benchmarks/results/example5_comprehensive_performance.png" alt="Comprehensive Performance Comparison" width="800"/>
</p>

#### Performance Summary
- **Satya (batch=1000):** 2,072,070 items/second
- **msgspec:** 1,930,466 items/second
- **Satya (single-item):** 637,362 items/second

Key findings:
- Batch processing provides up to 3.3x performance improvement
- Optimal batch size of 1,000 items for complex validation workloads
- Competitive performance with msgspec while providing comprehensive validation

#### Memory Efficiency
<p align="center">
  <img src="benchmarks/results/example5_memory_comparison.png" alt="Memory Usage Comparison" width="800"/>
</p>

Memory usage remains comparable across all approaches, demonstrating that performance gains don't come at the cost of increased memory consumption.

### Previous Benchmarks

Our earlier benchmarks also show significant performance improvements:

<p align="center">
  <img src="benchmarks/results/streaming_ips_object.png" alt="Satya Performance Comparison" width="800"/>
</p>

#### Large Dataset Processing (5M records)
- **Satya:** 207,321 items/second
- **Pydantic:** 72,302 items/second
- **Speed improvement:** 2.9x
- **Memory usage:** Nearly identical (Satya: 158.2MB, Pydantic: 162.5MB)

#### Web Service Benchmark (10,000 requests)
- **Satya:** 177,790 requests/second
- **Pydantic:** 1,323 requests/second
- **Average latency improvement:** 134.4x
- **P99 latency improvement:** 134.4x

| Validation Mode | Throughput | Memory Usage | Use Case |
|-----------------|------------|--------------|----------|
| **Satya dict-path** | **5.7M items/s** | 7.2MB | Pre-parsed Python dicts |
| **Satya JSON streaming** | **3.2M items/s** | 0.4MB | Large JSON datasets |
| **Satya JSON non-stream** | 1.2M items/s | 0.4MB | Small JSON datasets |
| **orjson + Satya dict** | 2.6M items/s | 21.5MB | End-to-end JSON processing |
| **msgspec + JSON** | 7.5M items/s | 0.4MB | Comparison baseline |
| **Pydantic + orjson** | 0.8M items/s | 0.4MB | Traditional validation |

### 🎯 Performance Highlights
- **7.9x faster** than Pydantic for dict validation
- **4x faster** than Pydantic for JSON processing  
- **Memory bounded**: <8MB even for 5M records
- **Competitive with msgspec**: 76% of msgspec's speed with more flexibility
- **Streaming support**: Process unlimited datasets with constant memory

### 📈 Scale Performance Analysis
- **Small Scale (100k)**: 7.9M items/s - matches msgspec performance
- **Large Scale (5M)**: 5.7M items/s - maintains high throughput
- **Memory Efficiency**: Bounded growth, predictable resource usage

> **Note:** Benchmarks run on Apple Silicon M-series. Results include comprehensive comparison with msgspec and Pydantic using fair JSON parsing (orjson). See `/benchmarks/` for detailed methodology.

### 🔄 Replacing jsonschema

Satya can serve as a high-performance replacement for the standard Python `jsonschema` library. Our benchmarks show **10-50x performance improvements** over pure Python `jsonschema` validation while providing the same validation capabilities.

#### Migration from jsonschema

**Before (using jsonschema):**
```python
import jsonschema
from jsonschema import validate

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name", "age"]
}

validate(instance={"name": "John", "age": 30}, schema=schema)
```

**After (using Satya):**
```python
from satya import Model, Field

class Person(Model):
    name: str
    age: int = Field(ge=0)

person = Person(name="John", age=30)  # Validates on construction

# For batch validation (even faster):
validator = Person.validator()
results = validator.validate_batch(data_list)
```

#### Why Replace jsonschema?

- **Speed**: 10-50x faster validation throughput
- **Type Safety**: Native Python type hints instead of JSON Schema dicts
- **Developer Experience**: Cleaner, more Pythonic API
- **Memory Efficiency**: Lower memory footprint with Rust core
- **Batch Processing**: Built-in batch validation for maximum throughput

See `benchmarks/README_jsonschema_comparison.md` for detailed benchmark results and migration guide.

## 🎯 Key Features

- **High Performance:** Rust-powered core with efficient batch processing
- **Comprehensive Validation:** 
  - Email validation (RFC 5322 compliant)
  - URL format validation
  - Regex pattern matching
  - Numeric constraints (min/max, ge/le/gt/lt)
  - Decimal precision handling
  - UUID format validation
  - Enum and literal type support
  - Array constraints (min/max items, unique items)
  - Deep nested object validation
- **Stream Processing:** Efficient handling of large datasets
- **Type Safety:** Full compatibility with Python type hints
- **Error Reporting:** Detailed validation error messages
- **Memory Efficient:** Minimal overhead design

## Why Satya?

Satya brings together high performance and comprehensive validation capabilities. While inspired by projects like Pydantic (for its elegant API) and msgspec (for performance benchmarks), Satya offers:

- **Rust-powered performance** with zero-cost abstractions
- **Batch processing** for optimal throughput
- **Comprehensive validation** beyond basic type checking
- **Production-ready** error handling and reporting
- **Memory-efficient** design for large-scale applications

## Ideal Use Cases:
- High-throughput API services
- Real-time data processing pipelines
- Large dataset validation
- Stream processing applications
- Financial and healthcare systems requiring strict validation
- Performance-critical microservices

## Installation:
```bash
pip install satya
```

### Requirements:
- Python 3.8 or higher

> **Note for developers:** If you're contributing to Satya or building from source, you'll need Rust toolchain 1.70.0 or higher:
>
> ```bash
> # Install Rust if you don't have it
> curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
> 
> # Update existing Rust installation
> rustup update
> ```
>
> You can check your Rust version with:
> ```bash
> rustc --version
> ```

## Performance Optimization Guide

### Batch Processing
For optimal performance, always use batch processing:

```python
# Configure batch size based on your workload
validator = MyModel.validator()
validator.set_batch_size(1000)  # Start with 1000, adjust as needed

# Use stream processing for large datasets
for valid_item in validator.validate_stream(data):
    process(valid_item)
```

### Batch Size Guidelines
- **Default recommendation:** 1,000 items
- **Large objects:** Consider smaller batches (500-1000)
- **Small objects:** Can use larger batches (5000-10000)
- **Memory constrained:** Use smaller batches
- **Always benchmark** with your specific data

## Validation Capabilities

### Supported Validation Types

Satya provides comprehensive validation that goes beyond basic type checking:

| Feature | Satya | msgspec | Pydantic |
|---------|-------|---------|----------|
| Basic type validation | ✅ | ✅ | ✅ |
| Email validation (RFC 5322) | ✅ | ❌ | ✅ |
| URL validation | ✅ | ❌ | ✅ |
| Regex patterns | ✅ | ❌ | ✅ |
| Numeric constraints | ✅ | ❌ | ✅ |
| Decimal precision | ✅ | ❌ | ✅ |
| UUID validation | ✅ | ❌ | ✅ |
| Enum/Literal types | ✅ | ✅ | ✅ |
| Array constraints | ✅ | ❌ | ✅ |
| Deep nesting (4+ levels) | ✅ | ✅ | ✅ |
| Custom error messages | ✅ | Limited | ✅ |
| Batch processing | ✅ | ❌ | ❌ |

### Schema Generation

Satya provides comprehensive JSON Schema generation with OpenAI compatibility:

```python
from satya import Model, Field

class User(Model):
    name: str = Field(description="User name")
    age: int = Field(description="User age")

# Standard JSON Schema
schema = User.json_schema()
print(schema)
# {
#   "type": "object",
#   "title": "User",
#   "properties": {
#     "name": {"type": "string", "description": "User name"},
#     "age": {"type": "integer", "description": "User age"}
#   },
#   "required": ["name", "age"]
# }

# OpenAI-compatible schema (flattened types, strict validation)
openai_schema = User.model_json_schema()
# Fixes nested type objects and ensures OpenAI API compatibility
```

### Migration from legacy bindings

If you previously used the low-level core (`_satya.StreamValidatorCore`) or manually registered schemas with `StreamValidator`, migrate to the new model-first API. See the full guide: [`docs/migration.md`](docs/migration.md).

Quick before/after:

```python
# Before (legacy manual schema)
from satya._satya import StreamValidatorCore
core = StreamValidatorCore()
core.add_field('id', 'int', True)
core.add_field('email', 'str', True)
core.set_field_constraints('email', email=True)
oks = core.validate_batch([{"id": 1, "email": "a@b.com"}])
```

```python
# After (model-first)
from satya import Model, Field

class User(Model):
    id: int
    email: str = Field(email=True)

oks = User.validator().validate_batch([{"id": 1, "email": "a@b.com"}])
```

JSON bytes helpers (streaming):

```python
ok = User.model_validate_json_bytes(b'{"id":1, "email":"a@b.com"}', streaming=True)
oks = User.model_validate_json_array_bytes(b'[{"id":1},{"id":2}]', streaming=True)
```

## ⚡ Performance Optimization Guide

### Maximum Throughput: Use Hybrid Batch Validation

For **MAXIMUM performance** (4.2M items/sec!), use `validate_batch_hybrid`:

```python
from satya import Model, Field

class DataRecord(Model):
    id: int
    name: str
    score: float

validator = DataRecord.validator()
validator.set_batch_size(10000)  # Optimal batch size

# 🔥 FASTEST: Hybrid batch validation (4.2M items/sec!)
for i in range(0, len(data), 10000):
    batch = data[i:i+10000]
    results = validator._validator.validate_batch_hybrid(batch)
    # Process results...

# ✅ Fast: Direct dict validation (2.8M items/sec)
results = validator._validator.validate_batch(python_dicts)

# ⚠️ Slower: JSON validation (600k items/sec - has parsing overhead)
import json
json_str = json.dumps(python_dicts)
results = validator.validate_json(json_str, mode="array")
```

**Performance**: Up to **4.2 MILLION items/sec** with hybrid validation!

### Email/URL/Regex Validation Trade-offs

Complex regex patterns (email, URL) are computationally expensive:

```python
# With email validation: ~21,000 items/sec
class User(Model):
    email: str = Field(email=True)  # RFC 5322 compliant regex

# Without email validation: ~774,000 items/sec (36x faster!)
class User(Model):
    email: str  # Basic string validation
```

**Recommendation**: For high-throughput scenarios (>100k items/sec), consider:
1. Using simple string validation and validate emails separately
2. Batch email validation after initial data intake
3. Using simpler regex patterns for format checks

### Batch Size Optimization

```python
validator = Model.validator()
validator.set_batch_size(10000)  # Optimal for most workloads

# For memory-constrained: 1000-5000
# For high-throughput: 10000-50000
```

## Current Status:
Satya v0.3.82 is stable and production-ready. **Satya is now the FASTEST Python validation library** with groundbreaking performance achievements. Key capabilities include:

- **🔥 82x Faster than jsonschema**: 4.2 MILLION items/sec validation speed
- **5.2x Faster than fastjsonschema**: Currently the fastest validation library in Python ecosystem
- **Python 3.13 Support**: Full compatibility including free-threaded builds
- **Complete Dict[str, CustomModel] Support**: Full validation for complex nested structures
- **MAP-Elites Algorithm Compatibility**: Native support for evolutionary optimization archives
- **Hierarchical Data Validation**: Recursive model resolution with dependency tracking
- **Source Distribution Support**: Enable `uv pip install --no-binary satya satya==0.3.82`
- **Provider-Agnostic Architecture**: Clean separation of core validation from provider-specific features

Recent Performance Achievements:
- ✅ PyO3 0.26 migration complete
- ✅ Lazy regex compilation (32x improvement)
- ✅ Direct dict validation via `validate_batch_hybrid` (200x total improvement)
- ✅ Comprehensive benchmarks vs jsonschema and fastjsonschema

## Acknowledgments:
- **Pydantic project** for setting the standard in Python data validation and inspiring our API design
- **msgspec project** for demonstrating high-performance validation is achievable
- **Rust community** for providing the foundation for our performance

## 💝 Open Source Spirit

> **Note to Data Validation Library Authors**: Feel free to incorporate our performance optimizations into your libraries! We believe in making the Python ecosystem faster for everyone. All we ask is for appropriate attribution to Satya under our Apache 2.0 license. Together, we can make data validation blazingly fast for all Python developers!

## 🤝 Contributing

We welcome contributions of all kinds! Whether you're fixing bugs, improving documentation, or sharing new performance optimizations, here's how you can help:

- **🐛 Report issues** and bugs
- **💡 Suggest** new features or optimizations
- **📝 Improve** documentation
- **🔧 Submit** pull requests
- **📊 Share** benchmarks and use cases

Check out our [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License:
Apache 2.0

**Note:** Performance numbers are from comprehensive benchmarks and may vary based on use case and data structure complexity.

## Contact:
- **GitHub Issues:** [Satya Issues](https://github.com/justrach/satya)
- **Author:** Rach Pradhan
