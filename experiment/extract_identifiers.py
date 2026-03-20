#!/usr/bin/env python3
"""
extract_identifiers.py — Extract all Java identifiers from a project.

Parses .java files using tree-sitter, extracts class names, method names,
field names, parameter names, enum constants, and record components.
Returns identifiers both as-is and split by camelCase/PascalCase.
"""

import re
import sys
from pathlib import Path

import tree_sitter_java as tsjava
from tree_sitter import Language, Parser

JAVA_LANGUAGE = Language(tsjava.language())

# Map: parent node type -> field name that holds the identifier
# Used for tree-walking extraction (stable across tree-sitter versions)
IDENTIFIER_RULES = {
    "class_declaration":        ("class_name", "name"),
    "interface_declaration":    ("interface_name", "name"),
    "enum_declaration":         ("enum_name", "name"),
    "enum_constant":            ("enum_constant", "name"),
    "record_declaration":       ("record_name", "name"),
    "method_declaration":       ("method_name", "name"),
}


def split_camel_case(name: str) -> list[str]:
    """Split a camelCase or PascalCase identifier into constituent words.

    Examples:
        RightsHolder -> ["Rights", "Holder"]
        calculateRoyalties -> ["calculate", "Royalties"]
        getISWCCode -> ["get", "ISWC", "Code"]
        UUID -> ["UUID"]
    """
    # Split on transitions: lowercase->uppercase, uppercase->uppercase+lowercase
    parts = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    parts = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", parts)
    return [p for p in parts.split("_") if p]


def _walk_tree(node, results: dict[str, set[str]]):
    """Recursively walk the syntax tree and collect identifiers."""
    node_type = node.type

    # Check direct identifier rules (class, interface, enum, record, method)
    if node_type in IDENTIFIER_RULES:
        category, field = IDENTIFIER_RULES[node_type]
        name_node = node.child_by_field_name(field)
        if name_node and name_node.type == "identifier":
            results.setdefault(category, set()).add(
                name_node.text.decode("utf-8"))

    # Field declarations: extract variable names
    if node_type == "field_declaration":
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node and name_node.type == "identifier":
                    results.setdefault("field_name", set()).add(
                        name_node.text.decode("utf-8"))

    # Formal parameters
    if node_type == "formal_parameter":
        name_node = node.child_by_field_name("name")
        if name_node and name_node.type == "identifier":
            results.setdefault("parameter_name", set()).add(
                name_node.text.decode("utf-8"))

    # Local variable declarations
    if node_type == "local_variable_declaration":
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node and name_node.type == "identifier":
                    results.setdefault("local_variable", set()).add(
                        name_node.text.decode("utf-8"))

    # Recurse into children
    for child in node.children:
        _walk_tree(child, results)


def extract_from_file(parser: Parser, file_path: Path) -> dict[str, set[str]]:
    """Extract identifiers from a single Java file.

    Returns a dict mapping identifier category to sets of identifier strings.
    """
    source = file_path.read_bytes()
    tree = parser.parse(source)

    results = {}
    _walk_tree(tree.root_node, results)
    return results


def extract_from_project(source_root: str) -> dict:
    """Extract all identifiers from a Java project.

    Returns:
        {
            "raw_identifiers": set of all identifier strings as-is,
            "split_terms": set of all constituent words (lowercased),
            "by_category": dict mapping category -> set of identifiers,
            "by_file": dict mapping file path -> set of identifiers,
        }
    """
    parser = Parser(JAVA_LANGUAGE)
    root = Path(source_root)

    all_identifiers = set()
    all_split_terms = set()
    by_category = {}
    by_file = {}

    for java_file in sorted(root.rglob("*.java")):
        file_identifiers = set()
        file_results = extract_from_file(parser, java_file)

        for category, names in file_results.items():
            if category not in by_category:
                by_category[category] = set()
            by_category[category].update(names)
            file_identifiers.update(names)

        all_identifiers.update(file_identifiers)
        by_file[str(java_file)] = file_identifiers

        for name in file_identifiers:
            for part in split_camel_case(name):
                all_split_terms.add(part.lower())

    return {
        "raw_identifiers": all_identifiers,
        "split_terms": all_split_terms,
        "by_category": by_category,
        "by_file": by_file,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_identifiers.py <source_root>")
        sys.exit(1)

    source_root = sys.argv[1]
    result = extract_from_project(source_root)

    print(f"Total unique identifiers: {len(result['raw_identifiers'])}")
    print(f"Total split terms: {len(result['split_terms'])}")
    print()

    for category, names in sorted(result["by_category"].items()):
        print(f"  {category}: {sorted(names)}")

    print()
    print("Raw identifiers:")
    for name in sorted(result["raw_identifiers"]):
        parts = split_camel_case(name)
        print(f"  {name} -> {[p.lower() for p in parts]}")


if __name__ == "__main__":
    main()
