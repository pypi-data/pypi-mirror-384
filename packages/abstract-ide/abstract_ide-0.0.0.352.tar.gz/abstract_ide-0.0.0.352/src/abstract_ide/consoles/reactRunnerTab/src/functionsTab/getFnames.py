from abstract_utilities import read_from_file, write_to_file
import os, re, textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
all_tabs = [str(HERE / "flowLayout"), str(HERE / "functionsTab")]

for ROOT in all_tabs:
    FUNCS_DIR = os.path.join(ROOT, "functions")
    
    if_fun_dir = os.path.isdir(FUNCS_DIR)
    if if_fun_dir:
    # Only .py files, skip __init__.py
        filepaths = [
            os.path.join(FUNCS_DIR, item)
            for item in os.listdir(FUNCS_DIR)
            if item.endswith(".py") and item != "__init__.py"
               and os.path.isfile(os.path.join(FUNCS_DIR, item))
        ]
    else:
        candidate = os.path.join(ROOT, "functions.py")
        filepaths = [candidate] if os.path.isfile(candidate) else []
    
    # Parse top-level def names
    def extract_funcs(path: str):
        funcs = []
        for line in read_from_file(path).splitlines():
            m = re.match(r"^def\s+([A-Za-z_]\w*)\s*\(", line)
            if m:
                funcs.append(m.group(1))
        return funcs

    # Build functions/__init__.py that re-exports all discovered functions
    import_lines = []
    all_funcs = []
    for fp in filepaths:
        module = os.path.splitext(os.path.basename(fp))[0]
        funcs = extract_funcs(fp)
        if funcs:
            import_lines.append(f"from .{module} import ({', '.join(funcs)})")
            all_funcs.extend(funcs)
    if if_fun_dir:
        functions_init = "\n".join(import_lines) + ("\n" if import_lines else "")
        write_to_file(contents=functions_init, file_path=os.path.join(FUNCS_DIR, "__init__.py"))

    # Prepare the tuple literal of function names for import + loop
    uniq_funcs = sorted(set(all_funcs))
    if not uniq_funcs:
        continue
    func_tuple = ", ".join(uniq_funcs) + ("," if len(uniq_funcs) == 1 else "")
    
    # Generate apiConsole/initFuncs.py using the safer setattr-loop
    init_funcs_src = textwrap.dedent(f"""\
        

        from .functions import ({func_tuple})

        def initFuncs(self):
            try:
                for f in ({func_tuple}):
                    setattr(self, f.__name__, f)
            except Exception as e:
                logger.info(f"{{e}}")
            return self
    """)

    write_to_file(contents=init_funcs_src, file_path=os.path.join(ROOT, "initFuncs.py"))
