
# pre-commit-hooks for TwinCAT
Some out-of-the-box pre-commit hooks for TwinCAT.

See also: https://github.com/pre-commit/pre-commit

## Using pre-commit-hooks with pre-commit
Add this to your .pre-commit-config.yaml

```
-   repo: https://github.com/janbirki/pre-commit-hooks.git
    rev: v1.0.0  # Use the ref you want to point at
    hooks:
    -   id: trailing-whitespace
    # -   id: ...
```

## Hooks available

### TwinCAT default core settings
This hook is changing the core settings to default by deleting the Element "Settings" inside your *.tsproj file

It's needed to run unit tests in a simulated enviromnent, where the actual available cores doesn't matter.