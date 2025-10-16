# PyForma

A Python template engine featuring partial substitution.

[![Tests](https://github.com/jan-moeller/pyforma/actions/workflows/uv.yml/badge.svg)](https://github.com/jan-moeller/pyforma/actions/workflows/uv.yml)

## Example

```python
from pyforma import Template

template = Template("Hello, {{ subject }}! This is {{ lib_name }}.")
assert template.unresolved_identifiers() == {"subject", "lib_name"}

template = template.substitute({"lib_name": "PyForma"})
assert template.unresolved_identifiers() == {"subject"}

print(template.render({"subject": "World"}))  # Prints "Hello, World! This is PyForma."
```

## Features

- 100% Python
- Python-like expressions in templates
- Special-purpose environments for more expressive templates
- Templates can be inspected for what variables need to be substituted
- Can partially substitute variables within templates
- Rendering with undefined variables results in an error
- Fully statically typed

## API

### `pyforma.Template(content, /, *, syntax)`

The primary template class.

**Parameters**:

- `content: str | Path`:  
  If `str`, parses the string as a template.  
  If `Path`, reads the file at that path and parses it as a template.
- `syntax: TemplateSyntaxConfig | None `:  
  Optional syntax definition.

**Return Value**:

Returns the template object.

**Exceptions**:

- `ValueError`: The provided input is not a valid template.
- `OSError`: If a path is passed and the file cannot be opened

#### `pyforma.Template.unresolved_identifiers() -> set[str]`

Reports all identifiers that need to be substituted to render the template.

**Return Value**:

Returns the set of all remaining identifiers in the template.

#### `pyforma.Template.substitute(variables, *, keep_comments, renderers) -> Template`

Partially substitutes variables in the template and evaluates expressions that can be evaluated.

**Parameters**:

- `variables: dict[str, Any]`:  
  Dictionary mapping variable identifiers to their values.
- `keep_comments: bool`:  
  By default, comments are kept until the final rendering. Set to `False` to strip all comments.
- `renderers: Sequence[tuple[type, Callable[[Any], str]]] | None`:  
  Optional sequence of renderers for stringification. By default, only `str`, `int` and `float` are
  rendered to `str` during template substitution. This argument can be used to automatically
  render additional types. Alternatively, the template needs to explicitly format other types as
  `str`.

**Return Value**:

A new template identical to self, but with the provided `variables` substituted.

**Exceptions**:

- `ValueError`: An expression evaluates to a type that can not be rendered.

#### `pyforma.Template.render(variables, *, renderers) -> str`

Renders a template to a string.

**Parameters**:

- `variables: dict[str, Any] | None`:  
  Optional dictionary mapping variable identifiers to their values.
- `renderers: Sequence[tuple[type, Callable[[Any], str]]] | None`:  
  Optional sequence of renderers for stringification. See `substitute()` for details.

**Return Value**:

The rendered string with all variables substituted.

**Exceptions**:

- `ValueError`:
    - Some unresolved variables remain after substitution.
    - An expression evaluates to a type that can not be rendered.

### `pyforma.TemplateSyntaxConfig(comment, expression, environment)`

Template syntax configuration class.

**Parameters**:

- `comment: BlockSyntaxConfig`:  
  Configuration for comment blocks.
  Defaults to `BlockSyntaxConfig("{#", "#}")`.
- `expression: BlockSyntaxConfig`:  
  Configuration for expression blocks.
  Defaults to `BlockSyntaxConfig("{{", "}}")`.
- `environment: BlockSyntaxConfig`:  
  Configuration for environment blocks.
  Defaults to `BlockSyntaxConfig("{%", "%}")`.

**Exceptions**:

- `ValueError`: The configured symbols are not sufficiently distinct.

### `pyforma.BlockSyntaxConfig(open, close)`

Class used for configuring the syntax of a block type.

**Parameters**:

- `open: str`:  
  Open block syntax. Must not be empty.
- `close: str`:  
  Close block syntax. Must not be empty.

**Exceptions**:

- `ValueError`:
    - Either of the parameters is empty.
    - The provided parameters are identical.

## Alternatives

- **[Jinja2](https://pypi.org/project/Jinja2/)**:
  The de-facto standard Python template engine. It's popular, fast, expressive and extensible, but doesn't support
  partial template substitution.
- **[Mako](https://pypi.org/project/Mako/)**:
  Compiles templates to Python bytecode.
- **[Chameleon](https://pypi.org/project/Chameleon/)**:
  HTML/XML-compatible template engine.
- **[string.Template](https://docs.python.org/3/library/string.html#string.Template)**:
  The actual standard Python template engine. Pretty limited functionality.