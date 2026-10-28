"""Keep legacy source fences while allowing the explicit MCP transport seam."""
import ast
import subprocess


def assert_readonly_core_unchanged(test, root):
    path = "AI.extension/lib/bimcode_ai_pane/ai_tool.py"
    before = subprocess.check_output(["git", "show", "HEAD:" + path], cwd=root)
    after = (root / path).read_bytes()

    def protected(source):
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Coordinator":
                # Authorized MCP seam: local queue + execution guard. Provider
                # protocol/one-call/routing parity remains behavior-tested by
                # test_bimcode_ai_tool and the specialty regression suites.
                allowed = {"queue", "queue_readonly", "_queue_action", "execute_approved"}
                node.body = [method for method in node.body
                             if not isinstance(method, ast.FunctionDef) or method.name not in allowed]
        return ast.dump(tree, include_attributes=False)

    test.assertEqual(protected(before), protected(after))
