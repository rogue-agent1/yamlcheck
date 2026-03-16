# yamlcheck

YAML linter and validator. Zero dependencies.

## Usage

```bash
yamlcheck check config.yaml
yamlcheck lint *.yaml
yamlcheck to-json config.yaml   # requires PyYAML
```

## Checks

- ❌ Tab indentation (not allowed in YAML)
- ❌ Unmatched quotes
- ⚠️ Boolean gotchas (`yes`/`no`/`on`/`off` → booleans)
- ⚠️ Norway problem (`NO` parsed as `false`)
- ⚠️ Inconsistent indentation
- ⚠️ Trailing whitespace

## Requirements

- Python 3.6+ (stdlib only)
