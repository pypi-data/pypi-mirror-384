#
#   Imandra Inc.
#
#   iml_utils.py
#

import re, sys, unittest, copy
from pathlib import Path
from collections import defaultdict, deque

# ----------------------
# Regex & Helpers
# ----------------------
DEF_RE = re.compile(r"^(let|type|val|verify)\s*([a-zA-Z0-9_']*)", re.MULTILINE)
ID_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_']*")
KEYWORDS = {"let", "type", "val", "in", "match", "fun", "if", "then", "else", "with", "rec", "and", "verify"}

def extract_definitions(source: str):
    """Return dict { name: full_definition_text }"""
    defs = {}
    lines = source.splitlines()
    current_name = None
    current_buf = []

    def flush():
        nonlocal current_name, current_buf
        if current_name and current_buf:
            defs[current_name] = "\n".join(current_buf).strip() + "\n"
        current_name, current_buf = None, []

    for line in lines:
        m = DEF_RE.match(line.strip())
        if m:
            flush()
            current_name = m.group(2)
            current_buf = [line]
        elif current_buf is not None:
            current_buf.append(line)
    flush()
    return defs

def free_vars(def_text: str):
    tokens = set(ID_RE.findall(def_text))
    return tokens - KEYWORDS

def topo_sort_definitions(defs: dict):
    """
    Topologically sort definitions based on dependencies on other defs only.
    """
    # Build dependency graph: node -> set of nodes it depends on (only other defs)
    graph = {name: ((free_vars(body) & set(defs.keys())) - set([name])) for name, body in defs.items()}


    # Compute in-degree
    in_degree = {name: len(deps) for name, deps in graph.items()}

    queue = deque([name for name, deg in in_degree.items() if deg == 0])
    sorted_list = []

    while queue:
        n = queue.popleft()
        sorted_list.append(n)

        # Remove n from dependencies of other nodes
        for m in defs:
            if n in graph[m]:
                graph[m].remove(n)
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    queue.append(m)

    if len(sorted_list) != len(defs):
        # Optional: print graph for debugging
        for name, deps in graph.items():
            if deps:
                print(f"{name} still depends on {deps}")
        raise RuntimeError("Cycle detected in definitions, cannot sort topologically.")

    return sorted_list

# ----------------------
# Operations
# ----------------------

def add_definition(source: str, new_def: str) -> str:
    defs = extract_definitions(source)
    m = DEF_RE.search(new_def)
    
    is_verify = False
    
    if not m:
        raise ValueError("New definition must start with let/type/val or verify")
    
    kind, new_name = m.groups()
    if kind == "verify":
        is_verify = True
        # for verify, generate a pseudo-name if empty
        if not new_name:
            new_name = f"__verify_{hash(new_def) & 0xFFFF}"

    defs = extract_definitions(source)

    if new_name in defs:
        raise ValueError(f"Definition {new_name} already exists")

    combined = source.strip() + "\n" + new_def.strip() + "\n"
    new_defs = extract_definitions(combined)

    if is_verify:
        new_defs[new_name] = new_def

    sorted_defs = topo_sort_definitions(new_defs)

    return "".join(list(new_defs[d] for d in sorted_defs))
    #return source.strip() + "\n" + new_def.strip() + "\n"

def update_definition(source: str, name: str, new_def: str, verify_index: int = 0) -> str:
    """
    Updates a definition (let/type/val) or a verify statement in the source IML code.

    - For let/type/val, 'name' must be the identifier.
    - For verify statements, set name="verify" and use verify_index to choose which one to update.
    """
    # Handle verify statements
    if name == "verify":
        regex = re.compile(r"(verify\s*\([^\n]*?\);{0,2})", re.MULTILINE)
        matches = list(regex.finditer(source))
        if not matches:
            raise ValueError("No verify statements found to update")
        if verify_index >= len(matches):
            raise ValueError(f"verify_index {verify_index} out of range (found {len(matches)} verify statements)")
        match = matches[verify_index]
        start, end = match.span()
        return source[:start] + new_def.strip() + source[end:]

    # Normal let/type/val updates
    pattern = rf"(let|type|val)\s+{re.escape(name)}\b[^\n]*?=(?:[\s\S]*?)(?=\n(let|type|val|verify|end|\Z))"
    regex = re.compile(pattern, re.MULTILINE)
    if regex.search(source):
        return regex.sub(new_def.strip(), source)

    raise ValueError(f"Failed to perform update: definition {name} not found")

def remove_definition(source: str, name: str, verify_index: int | None = None) -> str:
    """
    Removes a definition (let/type/val) or a verify statement from the source IML code.

    - For let/type/val, 'name' must be the identifier.
    - For verify statements, set name="verify" and optionally provide verify_index to remove a specific one.
      If verify_index is None, all verify statements will be removed.
    """
    # Handle verify statements
    if name == "verify":
        regex = re.compile(r"(verify\s*\([^\n]*?\);{0,2})", re.MULTILINE)
        matches = list(regex.finditer(source))
        if not matches:
            raise ValueError("No verify statements found to remove")

        if verify_index is None:
            # Remove all verify statements
            return regex.sub("", source)
        else:
            if verify_index >= len(matches):
                raise ValueError(f"verify_index {verify_index} out of range (found {len(matches)} verify statements)")
            match = matches[verify_index]
            start, end = match.span()
            return source[:start] + source[end:]

    # Normal let/type/val removal
    pattern = rf"\n?(let|type|val)\s+{re.escape(name)}\b[^\n]*?=(?:[\s\S]*?)(?=\n(let|type|val|verify|end|\Z))"
    regex = re.compile(pattern, re.MULTILINE)
    if regex.search(source):
        return regex.sub("", source)

    raise ValueError(f"Failed to perform remove: definition {name} not found")

def sync_definitions_topo(
        combined: str, 
        originals:dict[str,str], 
        misc_file_name="misc.iml"
    ):
    
    originals = copy.deepcopy(originals)

    combined_defs = extract_definitions(combined)

    applied_defs = set()
    known_defs = {}

    # Update originals
    for orig_file_path in originals:
        src = originals[orig_file_path]
        orig_defs = extract_definitions(src)
        updated_src = src

        for name, body in orig_defs.items():
            known_defs[name] = body

        for name, body in orig_defs.items():
            if name in combined_defs and combined_defs[name] != body:
                updated_src = updated_src.replace(body, combined_defs[name])
                applied_defs.add(name)
                known_defs[name] = combined_defs[name]
                #print(f"✅ Updated {name} in {orig_file_path}")

        originals[orig_file_path] = updated_src.strip()

    # New definitions
    new_defs = {n: b for n, b in combined_defs.items() if n not in applied_defs}
    if new_defs:
        sorted_names = topo_sort_definitions(new_defs)
        misc_path = misc_file_name

        if misc_path in originals:
            target_text = originals[misc_path]
        else:
            target_text = ""

        all_known_defs = dict(known_defs)
        for name in sorted_names:
            body = new_defs[name]
            deps = free_vars(body) & set(all_known_defs.keys())
            lines = list(map (lambda x: x.strip(), target_text.splitlines()))
            insert_index = 0
            for i, line in enumerate(lines):
                m = DEF_RE.match(line.strip())
                if m and m.group(2) in deps:
                    insert_index = i + 1
            target_text = lines[:insert_index] + [""] + [body] + [""] + lines[insert_index:]
            target_text = "\n".join(target_text)
            all_known_defs[name] = body
            #print(f"➕ Added new definition {name} to {misc_file_name}")

        
        if len(target_text):
            originals[misc_path] = target_text.strip()
    
    return originals
