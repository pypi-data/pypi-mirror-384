import os
import ast
import zipfile
import tempfile

def extract_code_chunks(file_path):
    """Parse Python code and return sorted normalized code chunks (functions, classes, top-level)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []  # Return empty for non-Python files or syntax errors

    chunks = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            chunks.append(ast.unparse(node).strip())
        else:
            # Capture top-level code (e.g., assignments, expressions)
            chunks.append(ast.unparse(node).strip())

    # Normalize and sort to make order irrelevant
    normalized = sorted([chunk for chunk in chunks if chunk])
    return normalized

def compare_code_files(file1, file2):
    """Compare two Python code files ignoring chunk order but ensuring chunk content matches."""
    chunks1 = extract_code_chunks(file1)
    chunks2 = extract_code_chunks(file2)
    return chunks1 == chunks2


def compare_js_code_files(file1, file2):
    """TODO : Compare two javascript/typescript code files ignoring chunk order but ensuring chunk content matches."""
    # chunks1 = extract_code_chunks(file1)
    # chunks2 = extract_code_chunks(file2)
    # return chunks1 == chunks2


def compare_zip_code_folders(zip1_path, zip2_path):
    """Compare two zipped Python code folders with chunk-level matching (order-independent), skipping sb_*.yaml files."""
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        # Extract both zips
        with zipfile.ZipFile(zip1_path, 'r') as zip1:
            zip1.extractall(dir1)
        with zipfile.ZipFile(zip2_path, 'r') as zip2:
            zip2.extractall(dir2)

        # Build relative file list from dir1
        for root, _, files in os.walk(dir1):
            for filename in files:
                rel_path = os.path.relpath(os.path.join(root, filename), dir1)
                file1 = os.path.join(dir1, rel_path)
                file2 = os.path.join(dir2, rel_path)

                # Skip files that start with sb_ and end with .yaml
                if filename.startswith('sb_') and filename.endswith('.yaml'):
                    continue

                # Check existence
                if not os.path.exists(file2):
                    print(f"Missing file in second zip: {rel_path}")
                    return False

                # For .py files, do chunk comparison
                if filename.endswith("py"):
                    if not compare_code_files(file1, file2):
                        print(f"Python file mismatch: {rel_path}")
                        return False
                # elif filename.split(".")[-1] in ["js","ts"]:
                #     if not compare_js_code_files(file1, file2):
                #         return False
                else:
                    # For other files, compare exact content
                    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
                        if f1.read() != f2.read():
                            print(f"Binary or non-Python file mismatch: {rel_path}",file1,file2)
                            return False

        # Check for extra files in second dir
        for root, _, files in os.walk(dir2):
            for filename in files:
                rel_path = os.path.relpath(os.path.join(root, filename), dir2)
                file1 = os.path.join(dir1, rel_path)

                # Skip files that start with sb_ and end with .yaml
                if filename.startswith('sb_') and filename.endswith('.yaml'):
                    continue

                if not os.path.exists(file1):
                    print(f"Extra file in second zip: {rel_path}")
                    return False

        return True