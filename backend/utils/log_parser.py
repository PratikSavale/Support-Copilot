import re

# Common exception types and fail-signature regex patterns
EXCEPTION_PATTERN = re.compile(
    r"\b([a-zA-Z_]\w*(?:Error|Exception|Failure|Panic|Crash|Fault))\b",
    re.IGNORECASE
)

# Java Stack Trace line pattern: e.g. "at com.example.Service.method(Service.java:73)"
JAVA_TRACE_PATTERN = re.compile(
    r"at\s+([\w\.\$]+)\.([\w\<]+)\(([^:]+):(\d+)\)"
)

# Python Traceback line pattern: e.g. "File \"app.py\", line 42, in method"
PYTHON_TRACE_PATTERN = re.compile(
    r"File\s+[\"']([^\"']+)[\"'],\s+line\s+(\d+),\s+in\s+([a-zA-Z_]\w*)"
)

# Node.js / JavaScript Stack Trace line pattern: e.g. "at Object.method (/app/index.js:58:21)"
NODE_TRACE_PATTERN = re.compile(
    r"at\s+([^\(]+)\s+\(([^:]+):(\d+):(\d+)\)"
)

def extract_diagnostic_signature(text: str) -> str | None:
    """Extracts a normalized, deterministic diagnostic signature from stack traces or log text.
    
    Returns a normalized signature string like "NullPointerException in PaymentGatewayConfig.loadApiKey line 73"
    or None if no structured exception/stack trace is detected.
    """
    if not text:
        return None

    # 1. Identify the exception type
    exception_match = EXCEPTION_PATTERN.search(text)
    exception = exception_match.group(1) if exception_match else None

    # 2. Extract failing code location
    failing_class = None
    failing_method = None
    line_number = None

    # Try Java format
    java_match = JAVA_TRACE_PATTERN.search(text)
    if java_match:
        full_class, method, _, line = java_match.groups()
        # Extract the simple class name (last element of package)
        failing_class = full_class.split(".")[-1]
        failing_method = method
        line_number = line

    # Try Python format
    if not failing_class:
        python_match = PYTHON_TRACE_PATTERN.search(text)
        if python_match:
            filepath, line, method = python_match.groups()
            failing_class = filepath.split("/")[-1].split("\\")[-1] # filename only
            failing_method = method
            line_number = line

    # Try Node.js format
    if not failing_class:
        node_match = NODE_TRACE_PATTERN.search(text)
        if node_match:
            method_scope, filepath, line, _ = node_match.groups()
            failing_class = filepath.split("/")[-1].split("\\")[-1] # filename only
            failing_method = method_scope.strip().split(".")[-1]
            line_number = line

    # If we extracted at least an exception and some code reference, build the signature
    if exception and failing_class:
        method_part = f".{failing_method}" if failing_method else ""
        line_part = f" line {line_number}" if line_number else ""
        return f"{exception} in {failing_class}{method_part}{line_part}".strip()

    # Fallback: if we just have a solid exception but no trace reference, see if there is an error message
    if exception:
        # Look for the line containing the exception and capture the core statement
        for line in text.splitlines():
            if exception in line:
                # Limit length to keep semantic signal clean
                clean_line = re.sub(r"[\{\}\[\]\(\)]", "", line).strip()
                return f"Exception: {clean_line[:100]}"

    return None
