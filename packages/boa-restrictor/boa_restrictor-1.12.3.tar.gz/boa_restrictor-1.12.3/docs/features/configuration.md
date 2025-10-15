# Configuration

## Exclude certain files

You can easily exclude certain files, for example, your tests, by using the `exclude` parameter from `pre-commit`:

```yaml
  - repo: https://github.com/ambient-innovation/boa-restrictor
    rev: v{{ version }}
    hooks:
      - id: boa-restrictor
        ...
        exclude: |
          (?x)^(
            /.*/tests/.*
            |.*/test_.*\.py
          )$
```

## Globally exclude configuration rule

You can disable any rule in your `pyproject.toml` file as follows:

```toml
[tool.boa-restrictor]
exclude = [
    "PBR001",
    "PBR002",
]
```

## Disable Django rules

You can disable Django-specific rules by setting `enable_django_rules` to `false`.

```toml
[tool.boa-restrictor]
enable_django_rules = false
```

## Per-file exclusion of configuration rule

You can disable rules on a per-file-basis in your `pyproject.toml` file as follows:

```toml
[tool.boa-restrictor.per-file-excludes]
"*/tests/*.py" = [
    "PBR001",
    "PBR002",
]
"scripts/*.py" = [
    "DBR001",
]
"*/my_app/*.py" = [
    "PBR003",
]
```

Take care that the path is relative to the location of your pyproject.toml. This means that example two targets all
files living in a `scripts/` directory on the projects top level.

## noqa & ruff support

As any other linter, you can disable certain rules on a per-line basis with `#noqa`.

````python
def function_with_args(arg1, arg2):  # noqa: PBR001
    ...
````

If you are using `ruff`, you need to tell it about our linting rules. Otherwise, ruff will remove all `# noqa`
statements from your codebase.

```toml
[tool.ruff.lint]
# Avoiding flagging (and removing) any codes starting with `PBR` from any
# `# noqa` directives, despite Ruff's lack of support for `boa-restrictor`.
external = ["PBR", "DBR"]
```

https://docs.astral.sh/ruff/settings/#lint_extend-unsafe-fixes
