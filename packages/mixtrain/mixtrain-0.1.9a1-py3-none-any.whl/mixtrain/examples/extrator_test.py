import ast
import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class MixFlowParam:
    """Represents a mixflow_param() decorated property."""

    name: str
    type_annotation: str | None = (
        None  # The type hint (e.g., 'str', 'int', 'List[str]')
    )
    default_value: object = None
    param_kwargs: dict[str, object] = field(
        default_factory=dict
    )  # Args passed to mixflow_param()
    lineno: int | None = None


@dataclass
class MixFlowClass:
    """Represents a class that subclasses MixFlow."""

    name: str
    file_path: str
    base_classes: list[str]
    params: list[MixFlowParam]  # Only mixflow_param() decorated properties
    docstring: str | None = None
    lineno: int | None = None


class MixFlowExtractor(ast.NodeVisitor):
    """AST visitor to extract classes that subclass MixFlow."""

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.mixflow_classes: list[MixFlowClass] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions and check if they inherit from MixFlow."""
        base_classes: list[str] = []
        is_mixflow_subclass = False

        # Extract base class names
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
                if base.id == "MixFlow":
                    is_mixflow_subclass = True
            elif isinstance(base, ast.Attribute):
                # Handle cases like module.MixFlow
                base_name = self._get_attribute_name(base)
                base_classes.append(base_name)
                if base_name.endswith("MixFlow"):
                    is_mixflow_subclass = True

        if is_mixflow_subclass:
            # Extract mixflow_param() decorated properties only
            params = self._extract_mixflow_params(node)

            # Get docstring
            docstring = ast.get_docstring(node)

            mixflow_class = MixFlowClass(
                name=node.name,
                file_path=self.file_path,
                base_classes=base_classes,
                params=params,
                docstring=docstring,
                lineno=node.lineno,
            )
            self.mixflow_classes.append(mixflow_class)

        # Continue visiting nested classes
        self.generic_visit(node)

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Recursively get the full attribute name."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _extract_mixflow_params(self, class_node: ast.ClassDef) -> list[MixFlowParam]:
        """Extract only attributes decorated with mixflow_param()."""
        params: list[MixFlowParam] = []

        for item in class_node.body:
            # We're looking for annotated assignments like: name: str = mixflow_param()
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name) and item.value:
                    # Check if the value is a call to mixflow_param()
                    if self._is_mixflow_param_call(item.value):
                        param_name = item.target.id
                        type_annotation = self._get_type_annotation(item.annotation)
                        # Type narrowing: we know it's a Call if _is_mixflow_param_call returned True
                        param_kwargs = (
                            self._extract_call_kwargs(item.value)
                            if isinstance(item.value, ast.Call)
                            else {}
                        )

                        params.append(
                            MixFlowParam(
                                name=param_name,
                                type_annotation=type_annotation,
                                param_kwargs=param_kwargs,
                                lineno=item.lineno,
                            )
                        )

            # Also handle non-annotated assignments: name = mixflow_param()
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if self._is_mixflow_param_call(item.value):
                            param_name = target.id
                            # Type narrowing: we know it's a Call if _is_mixflow_param_call returned True
                            param_kwargs = (
                                self._extract_call_kwargs(item.value)
                                if isinstance(item.value, ast.Call)
                                else {}
                            )

                            params.append(
                                MixFlowParam(
                                    name=param_name,
                                    type_annotation=None,
                                    param_kwargs=param_kwargs,
                                    lineno=item.lineno,
                                )
                            )

        return params

    def _is_mixflow_param_call(self, node: ast.expr) -> bool:
        """Check if a node is a call to mixflow_param()."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id == "mixflow_param"
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr == "mixflow_param"
        return False

    def _get_type_annotation(self, annotation: ast.expr) -> str:
        """Convert type annotation AST node to string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            # Handle generic types like List[str], Dict[str, int]
            value = self._get_type_annotation(annotation.value)
            slice_val = self._get_type_annotation(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Tuple):
            # Handle multiple types in subscript
            elements = [self._get_type_annotation(elt) for elt in annotation.elts]
            return ", ".join(elements)
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_name(annotation)
        else:
            return (
                ast.unparse(annotation) if hasattr(ast, "unparse") else str(annotation)
            )

    def _extract_call_kwargs(self, call_node: ast.Call) -> dict[str, object]:
        """Extract keyword arguments from a function call."""
        kwargs: dict[str, object] = {}

        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg:
                kwargs[keyword.arg] = self._extract_value(keyword.value)

        # Extract positional arguments (if any) as 'default'
        if call_node.args and len(call_node.args) > 0:
            kwargs["default"] = self._extract_value(call_node.args[0])

        return kwargs

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return self._get_attribute_name(decorator)
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return self._get_attribute_name(decorator.func)
        return str(decorator)

    def _extract_value(self, node: ast.expr) -> object:
        """Extract literal value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._extract_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._extract_value(k) if k else None: self._extract_value(v)
                for k, v in zip(node.keys, node.values)
            }
        elif isinstance(node, ast.Name):
            return f"<Name: {node.id}>"
        else:
            return f"<{node.__class__.__name__}>"


def extract_mixflow_classes_from_file(file_path: str) -> list[MixFlowClass]:
    """Extract MixFlow subclasses from a single Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)
        extractor = MixFlowExtractor(file_path)
        extractor.visit(tree)
        return extractor.mixflow_classes
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def extract_mixflow_classes_from_folder(folder_path: str) -> list[MixFlowClass]:
    """Extract MixFlow subclasses from all Python files in a folder."""
    folder = Path(folder_path)
    all_classes: list[MixFlowClass] = []

    # Find all Python files recursively
    for py_file in folder.rglob("*.py"):
        if py_file.is_file():
            classes = extract_mixflow_classes_from_file(str(py_file))
            all_classes.extend(classes)

    return all_classes


def print_mixflow_class_info(mixflow_class: MixFlowClass) -> None:
    """Pretty print information about a MixFlow subclass."""
    print(f"\n{'=' * 80}")
    print(f"Class: {mixflow_class.name}")
    print(f"File: {mixflow_class.file_path}:{mixflow_class.lineno}")
    print(f"Base Classes: {', '.join(mixflow_class.base_classes)}")

    if mixflow_class.docstring:
        print(f"Docstring: {mixflow_class.docstring[:100]}...")

    print(f"\nMixFlow Parameters ({len(mixflow_class.params)}):")

    if not mixflow_class.params:
        print("  (No mixflow_param() properties found)")
        return

    for param in mixflow_class.params:
        # Format the parameter declaration
        type_str = f": {param.type_annotation}" if param.type_annotation else ""
        print(f"\n  - {param.name}{type_str} (line {param.lineno})")

        # Show any kwargs passed to mixflow_param()
        if param.param_kwargs:
            print("    mixflow_param() kwargs:")
            for key, value in param.param_kwargs.items():
                print(f"      {key}: {value}")


def main() -> None:
    """Example usage of the MixFlow extractor."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extrator_test.py <folder_path>")
        print("\nExample:")
        print("  python extrator_test.py ./examples/routing")
        return

    folder_path = sys.argv[1]

    if not os.path.exists(folder_path):
        print(f"Error: Path '{folder_path}' does not exist")
        return

    print(f"Scanning for MixFlow subclasses in: {folder_path}")
    print("=" * 80)

    mixflow_classes = extract_mixflow_classes_from_folder(folder_path)

    if not mixflow_classes:
        print("\nNo MixFlow subclasses found.")
        return

    print(f"\nFound {len(mixflow_classes)} MixFlow subclass(es):")

    for mixflow_class in mixflow_classes:
        print_mixflow_class_info(mixflow_class)

    print(f"\n{'=' * 80}")
    print(f"Total: {len(mixflow_classes)} MixFlow subclass(es) found")


if __name__ == "__main__":
    main()
