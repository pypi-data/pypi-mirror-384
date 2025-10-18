#
# SPDX-FileCopyrightText: 2025 Lauterbach GmbH
#
# SPDX-License-Identifier: MIT
#

import os

import chardet
import tree_sitter_t32
from tree_sitter import Language, Node, Parser

METATAG_MAP = {
    "@Title": "@brief",
    "@Author": "@author",
    "@Description": "@details",
    "@Board": "@brief \\b Board",
    "@Chip": "@brief \\b Chip",
    "@Copyright": "@copyright",
    "@Keywords": "@brief \\b Keywords",
    "@Props": "@brief \\b Props",
}

MACROS_TYPES = {}


class CustomBlock:
    type: str = "block"
    children: list[Node] = []
    text: bytes

    def __init__(self, children: list[Node], start: int) -> None:
        self.children = children
        self.text = self._build_text(children, start)

    def _build_text(self, children: list[Node], start_point: int) -> bytes:
        out = bytearray()
        prev_end_row = None

        for idx, child in enumerate(children):
            t = child.text
            assert t is not None

            start = child.start_point
            end = child.end_point

            if idx == 0:
                # start a function body
                gap_rows = max(0, child.start_point[0] - start_point)
                gap_bytes = ("\r\n" * gap_rows).encode("utf-8")
                t = b"(" + gap_bytes + t
            else:
                # Insert blank lines between previous end and this start
                if start is not None and prev_end_row is not None:
                    gap_rows = max(0, start[0] - prev_end_row)
                    if gap_rows:
                        out.extend(b"\r\n" * gap_rows)

            out.extend(t)
            if end is not None:
                prev_end_row = end[0]

        # close function body
        return bytes(out).rstrip(b" \r\n") + b")\r\n"


class DoxyPractice:
    _parser: Parser = Parser(Language(tree_sitter_t32.language()))
    _line_count: int = 0
    _file: str = ""

    def print(self, *args: str, **kwargs: str | None) -> None:
        text = " ".join(str(arg) for arg in args)
        # Count number of lines
        self._line_count += text.count("\n") if "\n" in text else +1
        print(args, kwargs)

    def parse(self, cmm: str) -> None:
        assert os.path.exists(cmm), f"file not found: {cmm}"
        data = open(cmm, "rb").read()

        charset = chardet.detect(data)["encoding"]
        assert charset is not None

        import sys

        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding=charset, errors="replace")
        tree = self._parser.parse(bytes(data.decode(charset), encoding="utf-8"))

        assert tree.root_node.type == "script", "Unknown language, please use PRACTICE"
        self._file = os.path.basename(cmm)
        self.walk(tree.root_node)

    def macro_definition(self, node: Node) -> None:
        command = node.child_by_field_name("command")
        assert command is not None, "no command found"
        assert command.text is not None, "empty command"

        name_node = node.child_by_field_name("macro")
        assert name_node is not None, "no macro found"
        assert name_node.text is not None, "empty macro"

        name = name_node.text.decode("utf-8")
        identifier = command.text.decode("utf-8")
        type, value = self._get_macro_assignment(node, name)

        MACROS_TYPES[name.lower()] = type
        self.print(f"{identifier} {type} {name}= {value};")

    def _get_variable_type(self, value: str) -> str:
        value = value.lower()
        if value in MACROS_TYPES:
            return MACROS_TYPES[value]
        if value.startswith("string") or value.startswith('"'):
            return "string"
        if value in {"true()", "false()"}:
            return "bool"
        if value[0].isdigit():
            return "number"
        return "undefined"

    def _get_macro_assignment(self, node: Node, name: str) -> tuple[str, str]:
        assert node is not None

        sibling = node.next_sibling
        while sibling is not None:
            if sibling.type == "assignment_expression":
                left = sibling.child_by_field_name("left")
                right = sibling.child_by_field_name("right")

                assert left is not None
                assert left.text is not None
                assert right is not None
                assert right.text is not None

                if left.text.decode("utf-8").strip() == name:
                    value = right.text.decode("utf-8").strip()
                    val_type = self._get_variable_type(value)
                    return val_type, value

            sibling = sibling.next_sibling

        return "", ""

    def _is_command_return(self, node: Node) -> bool:
        if node.type != "command_expression":
            return False

        command = node.child_by_field_name("command")
        assert command is not None
        assert command.text is not None

        if command.text.decode("utf-8").strip().lower() != "return":
            return False
        return True

    def _get_return_type(self, node: Node | CustomBlock) -> str:
        assert node is not None

        for child in node.children:
            if not self._is_command_return(child):
                continue

            values = child.child_by_field_name("arguments")
            if values is None:
                return ""

            # if its list of values then return no return list value?
            if len(values.children) > 1:
                return "list"

            value = values.child(0)
            assert value is not None
            assert value.text is not None

            return_type = self._get_variable_type(value.text.decode("utf-8").strip())
            return return_type if return_type != "undefined" else ""

        return ""

    def _get_argument_type(self, node: Node | CustomBlock, name: str) -> str:
        for child in node.children:
            if child.type != "macro_definition":
                continue

            command = child.child_by_field_name("command")
            assert command is not None, "no command found"
            assert command.text is not None, "empty command"

            for macro in child.children:
                if macro.type == "macro":
                    assert macro.text is not None, "empty macro"
                    macro_text = macro.text.decode("utf-8")
                    if macro_text == name:
                        return command.text.decode("utf-8")  # type: ignore[no-any-return]
        return "LOCAL"

    def collect_params(self, node: Node | CustomBlock) -> list[str]:
        assert node.type == "block"
        parameters: list[str] = []

        for child in node.children:
            if child.type == "subroutine_call_expression":
                break
            if child.type != "parameter_declaration":
                continue
            macros = []
            type = ""
            if child.text and "PARAMETERS" in child.text.decode("utf-8"):
                type = "PRIVATE"

            for macro in child.children:
                if macro.type == "macro":
                    assert macro.text is not None, "empty macro"
                    macro_text = macro.text.decode("utf-8")
                    if type == "":
                        type = self._get_argument_type(node, macro_text)
                    macros.append(f"{type} {macro_text}")
            parameters.extend(macros)

        return parameters

    def _build_block_until_return(self, node: Node) -> CustomBlock:
        children = []

        sibling = node.next_sibling
        while sibling:
            children.append(sibling)
            if self._is_command_return(sibling):
                break
            sibling = sibling.next_sibling

        return CustomBlock(children=children, start=node.end_point[0])

    def subroutine_block(self, node: Node) -> None:
        self._print_function(node, "subroutine")

    def labeled_expression(self, node: Node) -> None:
        self._print_function(node, "label")

    def _print_function(self, node: Node, label: str) -> None:
        name_node = node.child_by_field_name(label)
        assert name_node is not None, f"no {label} found"
        assert name_node.text is not None, f"empty {label}"

        block = next((c for c in node.children if c.type == "block"), None)
        if block is None:
            block = self._build_block_until_return(node)

        assert block.text is not None

        parameters = self.collect_params(block)
        name = name_node.text.decode("utf-8")
        return_type = self._get_return_type(block)

        function_body = block.text.decode("utf-8")
        function_body = function_body.replace("(", "{", 1)
        function_body = function_body[::-1].replace(")", "}", 1)[::-1]
        self.print(f"{(return_type + ' ') if return_type else ''}{name}({', '.join(parameters)})\n{function_body}")

    def replace_practice_metadata(self, text: str) -> str:
        for old, new in METATAG_MAP.items():
            text = text.replace(f"{old}:", new)

        return text

    def comment(self, node: Node) -> None:
        assert node.text is not None
        text = node.text.decode("utf-8").replace(";", "///").strip()

        # Omit dashed comments
        if set(text) <= {"/", "-", " "}:
            if self._line_count == 0:
                text = f"/// @file {self._file}"
            else:
                text = "///"

        text = self.replace_practice_metadata(text)
        self.print(text)

        # There is some difference when counting lines for
        # multiline comment block, we can override it with incrementing
        if text.count("\n") > 1:
            self._line_count += 1

    def _is_labeled_expression_without_block(self, node: Node) -> bool:
        if node.type != "labeled_expression":
            return False

        block = next((c for c in node.children if c.type == "block"), None)
        return block is None

    def _go_to_return(self, node: Node) -> Node | None:
        child = node.next_sibling

        while child is not None and not self._is_command_return(child):
            child = child.next_sibling

        return child

    def walk(self, node: Node) -> None:
        child = node.child(0)
        assert child is not None

        if child.start_point[0] != 0:
            self.print(f"/// @file {self._file}")

        self._print_blank_lines(child.start_point[0] - self._line_count)

        while child is not None:
            self._process_node(child)

            if self._is_labeled_expression_without_block(child):
                child = self._go_to_return(child)
                if child is None:
                    return

            self._print_gap_to_next(child)

            child = child.next_sibling

    def _process_node(self, node: Node) -> None:
        assert self._line_count == node.start_point[0]

        dispatch = {
            "labeled_expression": self.labeled_expression,
            "subroutine_block": self.subroutine_block,
            "macro_definition": self.macro_definition,
            "comment": self.comment,
        }

        handler = dispatch.get(node.type)
        if handler:
            handler(node)
        else:
            assert node.text is not None
            self._print_blank_lines(node.text.decode("utf-8").count("\n"))

    def _print_gap_to_next(self, node: Node) -> None:
        next_node = node.next_sibling
        if next_node is not None:
            gap = next_node.start_point[0] - node.end_point[0]
            self._print_blank_lines(gap)

    def _print_blank_lines(self, count: int) -> None:
        for _ in range(count):
            self.print("")
