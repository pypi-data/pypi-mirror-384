#!/usr/bin/env python3
import sys, re, time

# 🌿 Global context
variables = {}
functions = {}

# =========================
# Expression Evaluator
# =========================
def eval_expr(expr):
    """Evaluate expression within current variable scope."""
    try:
        # Allow use of joda, ghatau, guna, bhaag in eval()
        safe_builtins = {
            "joda": lambda a, b: a + b,
            "ghatau": lambda a, b: a - b,
            "guna": lambda a, b: a * b,
            "bhaag": lambda a, b: a / b,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
        }
        return eval(expr, {"__builtins__": None}, {**safe_builtins, **variables})
    except Exception:
        return expr.strip('"')

# =========================
# Core Runner
# =========================
def run_sathi(lines, start=0, end=None):
    """Execute Sathi code between start and end line numbers."""
    i = start
    while i < (end if end is not None else len(lines)):
        line = lines[i].strip()

        # Skip blank or comment lines
        if not line or line.startswith("#"):
            i += 1
            continue

        # -----------------------------
        # PRINT
        # -----------------------------
        if line.startswith("sathi bhana"):
            content = line.split("bhana", 1)[1].strip()

            # Handle bhana naya / sangai
            if content.startswith("naya"):
                msg = content.replace("naya", "", 1).strip()
                print(eval_expr(msg))
            elif content.startswith("sangai"):
                msg = content.replace("sangai", "", 1).strip()
                print(eval_expr(msg), end="")
            else:
                print(eval_expr(content))

        # -----------------------------
        # VARIABLE - sathi yo ho x = 5
        # -----------------------------
        elif "yo ho" in line:
            match = re.match(r"sathi yo ho (\w+)\s*=\s*(.+)", line)
            if match:
                var, val = match.groups()
                variables[var] = eval_expr(val)

        # -----------------------------
        # IF CONDITION - sathi bhane x > 5
        # -----------------------------
        elif line.startswith("sathi bhane"):
            cond = line.split("bhane", 1)[1].strip()
            condition_result = bool(eval_expr(cond))

            block_start = i + 1
            block_end = find_block_end(lines, i + 1)
            else_index = find_keyword(lines, "sathi natra", block_start, block_end)

            if condition_result:
                run_sathi(lines, block_start, else_index or block_end)
            elif else_index:
                run_sathi(lines, else_index + 1, block_end)
            i = block_end

        # -----------------------------
        # LOOP - sathi dohoryau 5 choti
        # -----------------------------
        elif line.startswith("sathi dohoryau"):
            match = re.match(r"sathi dohoryau (\d+) choti", line)
            if match:
                times = int(match.group(1))
                block_start = i + 1
                block_end = find_block_end(lines, i + 1)
                for _ in range(times):
                    run_sathi(lines, block_start, block_end)
                i = block_end

        # -----------------------------
        # FUNCTION DEFINE - sathi kam gar greet(name)
        # -----------------------------
        elif line.startswith("sathi kam gar"):
            match = re.match(r"sathi kam gar (\w+)\((.*?)\)", line)
            if match:
                func_name, params = match.groups()
                params = [p.strip() for p in params.split(",") if p.strip()]
                block_start = i + 1
                block_end = find_block_end(lines, i + 1)
                functions[func_name] = {
                    "params": params,
                    "body": lines[block_start:block_end],
                }
                i = block_end

        # -----------------------------
        # FUNCTION CALL - sathi gara greet("Ram")
        # -----------------------------
        elif line.startswith("sathi gara"):
            match = re.match(r"sathi gara (\w+)\((.*?)\)", line)
            if match:
                func_name, args_str = match.groups()
                args = [eval_expr(a.strip()) for a in args_str.split(",") if a.strip()]
                if func_name in functions:
                    func = functions[func_name]
                    local_vars = dict(zip(func["params"], args))
                    prev_vars = variables.copy()
                    variables.update(local_vars)

                    result = run_function(func["body"])

                    variables.clear()
                    variables.update(prev_vars)

                    # Return value if assigned
                    if result is not None:
                        variables["_"] = result
                else:
                    print(f"Sathi Error: Function '{func_name}' not defined")

        # -----------------------------
        # WAIT - sathi parkha 2
        # -----------------------------
        elif line.startswith("sathi parkha"):
            match = re.match(r"sathi parkha (\d+)", line)
            if match:
                time.sleep(int(match.group(1)))

        i += 1


# =========================
# FUNCTION HANDLER
# =========================
def run_function(body):
    """Run a function block and capture 'sathi farki'."""
    i = 0
    while i < len(body):
        line = body[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        if line.startswith("sathi farki"):
            val = line.split("farki", 1)[1].strip()
            return eval_expr(val)

        # Recursively handle inside-block statements
        if line.startswith("sathi bhana"):
            content = line.split("bhana", 1)[1].strip()
            if content.startswith("naya"):
                msg = content.replace("naya", "", 1).strip()
                print(eval_expr(msg))
            elif content.startswith("sangai"):
                msg = content.replace("sangai", "", 1).strip()
                print(eval_expr(msg), end="")
            else:
                print(eval_expr(content))

        i += 1
    return None


# =========================
# HELPERS
# =========================
def find_block_end(lines, start):
    """Find where a sathi block ends (sakkyo)."""
    for i in range(start, len(lines)):
        if lines[i].strip() == "sathi sakkyo":
            return i
    return len(lines)

def find_keyword(lines, keyword, start, end):
    """Find a specific keyword inside a block."""
    for i in range(start, end):
        if lines[i].strip().startswith(keyword):
            return i
    return None


# =========================
# MAIN ENTRY
# =========================
def main():
    if len(sys.argv) < 2:
        print("Usage: sathi <file.sathi>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        run_sathi(lines)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print("Sathi Error:", e)


if __name__ == "__main__":
    main()
