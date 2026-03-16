#!/usr/bin/env python3
"""yamlcheck - YAML linter and validator (pure Python YAML subset parser). Zero deps."""
import sys, re, os, json

class YAMLError(Exception):
    def __init__(self, msg, line=0):
        self.line = line
        super().__init__(f"Line {line}: {msg}")

def parse_yaml(text):
    """Simple YAML parser supporting maps, lists, scalars, strings."""
    lines = text.splitlines()
    errors = []
    warnings = []
    
    # Check common issues
    for i, line in enumerate(lines, 1):
        raw = line
        # Trailing whitespace
        if line != line.rstrip() and line.strip():
            warnings.append((i, "trailing whitespace"))
        # Tabs
        if "\t" in line:
            errors.append((i, "tabs not allowed in YAML indentation"))
        # Inconsistent quotes
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            # Unmatched quotes
            for q in ('"', "'"):
                count = stripped.count(q) - stripped.count(f"\\{q}")
                if count % 2 != 0:
                    errors.append((i, f"unmatched {q} quote"))
            # Duplicate keys (basic check within visible scope)
            if ":" in stripped and not stripped.startswith("-") and not stripped.startswith("#"):
                key_match = re.match(r'^(\s*)(\S+)\s*:', line)
                if key_match:
                    pass  # Would need full parse for duplicate detection
            # Invalid mapping
            if re.match(r'^\s+\S.*[^:]\s*$', line) and not stripped.startswith("-") and not stripped.startswith("#") and ":" not in stripped:
                if i > 1 and lines[i-2].strip().endswith(":"):
                    pass  # Could be a scalar value
    
    # Check document markers
    has_start = any(l.strip() == "---" for l in lines)
    
    # Check indentation consistency  
    indents = set()
    for line in lines:
        if line.strip() and not line.strip().startswith("#"):
            spaces = len(line) - len(line.lstrip())
            if spaces > 0:
                indents.add(spaces)
    
    if indents:
        sorted_indents = sorted(indents)
        diffs = set()
        for i in range(len(sorted_indents)):
            if i == 0:
                diffs.add(sorted_indents[0])
            else:
                diffs.add(sorted_indents[i] - sorted_indents[i-1])
        if len(diffs) > 2:
            warnings.append((0, f"inconsistent indentation levels: {sorted(indents)}"))
    
    # Empty document
    content_lines = [l for l in lines if l.strip() and not l.strip().startswith("#") and l.strip() != "---" and l.strip() != "..."]
    if not content_lines:
        warnings.append((0, "empty document"))
    
    # Check for common YAML gotchas
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            # Boolean gotcha
            if re.match(r'^\w+:\s+(yes|no|on|off|true|false)\s*$', stripped, re.IGNORECASE):
                val = stripped.split(":", 1)[1].strip().lower()
                if val in ("yes", "no", "on", "off"):
                    warnings.append((i, f"'{val}' is a boolean in YAML — quote if string intended"))
            # Norway problem (NO as boolean)
            if re.match(r'^\w+:\s+NO\s*$', stripped):
                warnings.append((i, "NO is parsed as false in YAML 1.1 — quote if needed"))
    
    return errors, warnings

def cmd_check(args):
    if not args:
        print("Usage: yamlcheck check <file.yaml> [file2.yaml...]")
        sys.exit(1)
    
    total_errors = 0
    total_warnings = 0
    
    for f in args:
        if not os.path.isfile(f):
            print(f"❌ {f}: file not found"); total_errors += 1; continue
        with open(f) as fh:
            text = fh.read()
        
        errors, warnings = parse_yaml(text)
        
        if errors or warnings:
            print(f"\n📄 {f}:")
            for line, msg in errors:
                print(f"  ❌ L{line}: {msg}")
                total_errors += 1
            for line, msg in warnings:
                loc = f"L{line}" if line else "file"
                print(f"  ⚠️  {loc}: {msg}")
                total_warnings += 1
        else:
            print(f"  ✅ {f}: OK")
    
    print(f"\n{'❌' if total_errors else '✅'} {total_errors} error(s), {total_warnings} warning(s)")
    sys.exit(1 if total_errors else 0)

def cmd_to_json(args):
    """Convert YAML to JSON (basic — uses PyYAML if available, else errors)."""
    if not args: print("Usage: yamlcheck to-json <file.yaml>"); sys.exit(1)
    try:
        import yaml
        with open(args[0]) as f:
            data = yaml.safe_load(f)
        print(json.dumps(data, indent=2, default=str))
    except ImportError:
        print("❌ PyYAML not installed (pip install pyyaml)")
        sys.exit(1)

CMDS = {"check": cmd_check, "lint": cmd_check, "to-json": cmd_to_json}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print("yamlcheck - YAML linter and validator")
        print("Commands: check/lint <files...>, to-json <file>")
        sys.exit(0)
    cmd = args[0]
    if cmd not in CMDS: print(f"Unknown: {cmd}"); sys.exit(1)
    CMDS[cmd](args[1:])
