---
name: tc-cpp
description: Write, review, or refactor Teamcenter server-side C/C++ customization code (ITK, workflow handlers, extensions, user exits, runtime properties, utilities). Covers memory ownership of ITK output, error handling across extern "C" boundaries, logging, and legacy C idioms to replace.
---

# Teamcenter C++ customization

Rules for code that runs inside `tcserver` or ITK utilities. Google C++ style (`clang-format` with the project's `.clang-format`).

## 1. Find APIs in the headers, never from memory

- C APIs: `$TC_ROOT/include`. C++ APIs: `$TC_ROOT/include_cpp`.
- Grep for the function, then read its full doc comment before calling it.

```sh
grep -rn "extern .* AOM_ask_value_strings\s*(" "$TC_ROOT/include"
grep -rln "class .*Logger\b" "$TC_ROOT/include_cpp"
```

Every parameter carries a direction tag. `(OF)` marks output that the caller frees. Its comment says how:

| Doc comment says | Free with |
|---|---|
| `(OF)` on `char**` / `tag_t**` / `int**` | one `MEM_free` -> `scoped_smptr<T>` |
| "packed format ... MEM_free on the container only" | one `MEM_free` -> `scoped_smptr<char*>` |
| "Iterate through the output array and call MEM_free on each element" | nested free -> `SmStringArray` (below) |

If grep finds nothing, say so and ask the user. A plausible-looking API name that is not in the headers is a bug.

## 2. Memory: the allocator decides the deallocator

Whatever allocated the memory determines how it is freed. Mixing them is undefined behaviour (`malloc` + `delete`, `new` + `MEM_free`, `MEM_alloc` + `free`).

| Memory | Owner |
|---|---|
| Returned by ITK (`MEM_alloc` family, `(OF)` outputs) | `Teamcenter::scoped_smptr<T>` (`base_utils/ScopedSmPtr.hxx`) |
| Your own objects | `std::unique_ptr`, `std::shared_ptr`, values |
| Your own strings and arrays | `std::string`, `std::vector` |
| Third-party C library | `std::unique_ptr<T, Deleter>` with that library's free function |

Every manual `MEM_free`, `delete`, or `free` in the normal control flow is a bug. Report it and suggest the RAII replacement. The user decides whether to change it.

```cpp
#include <base_utils/ScopedSmPtr.hxx>

Teamcenter::scoped_smptr<char> name;
ok = AOM_ask_value_string(obj, "object_name", &name);
std::string result = name.getString();  // NULL-safe; copy out of SM memory early

Teamcenter::scoped_smptr<tag_t> children;
int n = 0;
ok = AOM_ask_value_tags(obj, "my_children", &n, &children);
std::vector<tag_t> tags(children.get(), children.get() + n);
```

**One `scoped_smptr` per API output. Never reuse an instance for another call.** Its `operator&` returns the raw `&bucket` without freeing, so a second call through the same instance leaks the first allocation.

```cpp
Teamcenter::scoped_smptr<char> name;
Teamcenter::scoped_smptr<char> desc;
ok = AOM_ask_value_string(obj, "object_name", &name);
ok = AOM_ask_value_string(obj, "object_desc", &desc);
```

Other `scoped_smptr` behaviour (see `ScopedSmPtr.hxx`):
- It calls `MEM_free` only, never a destructor. Use it only for SM-allocated memory.
- It frees the container only. Using it on a nested string array leaks every element.

`Teamcenter::scoped_ptr` (`ScopedPtr.hxx`) is documented as "for reference only, not for general customization use". Use `std::unique_ptr` instead.

Nested arrays need an RAII wrapper. Here is a sketch for `char***` outputs:

```cpp
// Owns an ITK "free each element, then the container" string array.
class SmStringArray {
 public:
  SmStringArray() = default;
  SmStringArray(const SmStringArray&) = delete;
  SmStringArray& operator=(const SmStringArray&) = delete;
  ~SmStringArray() {
    for (int i = 0; i < count_; ++i) MEM_free(data_[i]);
    MEM_free(data_);
  }
  int* count() { return &count_; }
  char*** data() { return &data_; }
  std::vector<std::string> ToVector() const { return {data_, data_ + count_}; }

 private:
  int count_ = 0;
  char** data_ = nullptr;
};

SmStringArray values;
ok = AOM_ask_value_strings(obj, "my_prop", values.count(), values.data());
```

Before adding a wrapper like this, check the codebase for an existing one.

## 3. Error handling: exceptions inside, return codes at the boundary

Teamcenter has one central error stack. ITK calls push onto it and return an `int` (`ITK_ok` == 0).

- **Operation-invalidating failure**: throw. Assign the return code to `ResultStatus` (`base_utils/TcResultStatus.hxx`), which throws `IFail` using the top error on the stack. To raise your own error, use `throw IFail(code, s1, ...)` (`base_utils/IFail.hxx`), which pushes the error onto the stack.
- **Locally recoverable failure**: check the `int` where it is returned and handle it. Wrap expected failures in an `ErrorStoreProtector` scope (`base_utils/ErrorStoreProtector.hxx`) so their errors are cleared from the stack. Read that header's note on whether to return OK or NOT_OK afterwards.
- **`extern "C"` boundary** (handlers, extension methods, runtime property functions, user exits, `main` of utilities): no exception may cross it. Each entry point is a thin shim that ends in `catch (...)`.

```cpp
namespace {
void ValidateBom(tag_t task) {           // pure C++, throws IFail
  ResultStatus ok;
  ok = AOM_ask_value_string(task, ...);
  if (bad) throw IFail(kMyErrInvalidBom, item_id);
}
}  // namespace

extern "C" int my_validate_bom(EPM_action_message_t msg) {
  try {
    ValidateBom(msg.task);
    return ITK_ok;
  } catch (const IFail& e) {
    return e.ifail();                    // error is already on the stack
  } catch (const std::exception& e) {
    // store the project's generic error code (see AGENTS.md), log e.what()
  } catch (...) {
    // same, without a message
  }
  return /* project generic error code */;
}
```

`METHOD_function_t` (`tccore/method.h`) must return `ITK_ok` or the value of the top error from the error store. Returning a nonzero code with an empty error stack is invalid.

Log an error once, at the layer that has the context. Logging and rethrowing at every layer floods the syslog.

## 4. Logging

Use `Teamcenter::Logging::Logger` (`mld/logging/Logger.hxx`), configured through `TC_DATA/logger.properties` (or `TC_LOGGER_CONFIGURATION`). Keep `TC_write_syslog`, `printf`, and `std::cout` out of application logging.

```cpp
static Teamcenter::Logging::Logger* logger =
    Teamcenter::Logging::Logger::getLogger("Company.Module.Unit");

if (logger->isDebugEnabled()) {
  logger->debug("expanded " + std::to_string(lines.size()) + " lines");
}
logger->error(__FILE__, __LINE__, e.ifail(), e.getMessage());
```

- Use stable, hierarchical logger names, one per module.
- Guard expensive `debug`/`trace` message construction with `isDebugEnabled()` / `isTraceEnabled()`.
- Never log passwords, tokens, credentials, personal data, or full business-object dumps.

## 5. Legacy idioms to replace

| Legacy | Replace with |
|---|---|
| `ITK_CALL(x)` / `CALL(x)` / `if (ifail != ITK_ok) goto CLEANUP;` macros | `ResultStatus ok; ok = x;` plus RAII |
| `goto CLEANUP` blocks with `MEM_free` lists | RAII owners (section 2) |
| `char buf[WSO_name_size_c + 1]` + `tc_strcpy` / `strcat` / `sprintf` | `std::string`, `std::to_string`, `std::ostringstream` |
| Own APIs with `char**` / `tag_t**` out-params | return `std::string` / `std::vector<tag_t>` / `std::optional` |
| `NULL`, C-style casts | `nullptr`, `static_cast` / `reinterpret_cast` |
| `#define` constants and function-like macros | `constexpr`, inline functions, templates |
| Hungarian notation (`szName`, `iCount`, `ptTag`) | Google naming |
| `va_arg` reading in the wrong order or with the wrong type in method handlers | extract exactly the arguments, in the order, that the message's header documents |

When refactoring, change one idiom at a time and keep each diff reviewable. Report any legacy code that you see but are not changing.

## 6. Design

- Put the `extern "C"` shim at the edge and the logic in namespaced C++ functions that take `tag_t`s and return values. One shim per registration.
- Registration code (`*_register_callbacks`, `CUSTOM_register_exit`, `EPM_register_*_handler`) only registers. Business logic belongs elsewhere.
- Read preferences and lookups once per call path, not inside loops. Batch ITK calls when the header offers a bulk variant (for example `AOM_load_instances`).
- Keep static mutable state out of handlers unless the user confirms the lifetime and session semantics.

## 7. Naming

C++ identifiers follow Google style:

```cpp
class BomValidator;              // PascalCase type
void ValidateBom(tag_t line);    // PascalCase function
int line_count;                  // snake_case variable
std::string item_id_;            // private member: trailing underscore
constexpr int kMaxDepth = 10;    // k + PascalCase constant
extern "C" int my_validate_bom(EPM_action_message_t msg);  // extern "C": snake_case
```

Other artifacts:

| Artifact | Convention | Example |
|---|---|---|
| Files, extension symbols, tools, handler functions | lower_snake_case | `validate_bom.cxx`, `import_bom` |
| Handler friendly name | UPPER prefix + lowercase-hyphen words, no `ah`/`rh` | `MY-validate-bom` |
| Libraries | letters and digits | `MY4Custom` |
| Utility arguments | `-name=value` only, no positionals, no `--long` | `-item_id=000123` |
| AW kits and modules | camelCase | `customKit` |

## Done when

Writing or reviewing, the work is done only when each of these holds:
- Every ITK return code is consumed, either by `ResultStatus` or by an explicit check.
- Every `(OF)` output is owned by its own RAII object, one per call, matching its doc comment (single, packed, or nested).
- Every `extern "C"` entry point ends in `catch (...)` and returns `ITK_ok` or an error that is on the stack.
- No new manual free calls, error macros, fixed-size char buffers, or `TC_write_syslog` calls.
- Every API used was confirmed by grep in `$TC_ROOT/include` or `$TC_ROOT/include_cpp`.
