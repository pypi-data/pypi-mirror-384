#
# SPDX-FileCopyrightText: 2025 Lauterbach GmbH
#
# SPDX-License-Identifier: MIT
#

import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from lauterbach.trace32.doxypractice.doxypractice import DoxyPractice


class TestDoxyPracticeMocked(unittest.TestCase):
    def setUp(self):
        self.dp = DoxyPractice()

    def mock_macro_node(self, name):
        macro = MagicMock()
        macro.type = "macro"
        macro.text.decode.return_value = name
        return macro

    def mock_param_declaration(self, macro_names):
        param = MagicMock()
        param.type = "parameter_declaration"
        param.children = [self.mock_macro_node(name) for name in macro_names]
        return param

    def test_collect_params_from_expression_with_arguments(self):
        block = MagicMock()
        block.type = "block"
        block.children = [self.mock_param_declaration(["param1"]), self.mock_param_declaration(["param2"])]

        params = self.dp.collect_params(block)
        self.assertEqual(params, ["LOCAL param1", "LOCAL param2"])

    def test_collect_params_from_expression_with_no_arguments(self):
        param = MagicMock()
        param.type = "parameter_declaration"
        param.children = []  # no params

        block = MagicMock()
        block.type = "block"
        block.children = [param]

        params = self.dp.collect_params(block)
        self.assertEqual(params, [])

    def test_collect_params_omit_other_type(self):
        param = MagicMock()
        param.type = "non_declaration"

        block = MagicMock()
        block.type = "block"
        block.children = [param]

        params = self.dp.collect_params(block)
        self.assertEqual(params, [])

    def test_labeled_expression_print(self):
        labeled = MagicMock()
        labeled.type = "labeled_expression"
        label = MagicMock()
        label.text.decode.return_value = "myFunc"
        labeled.child_by_field_name.return_value = label
        labeled.text.decode.return_value = "myFunc:\n{\nparam1;\n}"

        block = MagicMock()
        block.type = "block"
        block.children = [self.mock_param_declaration(["paramX"])]
        labeled.children = [block]

        with patch("sys.stdout", new=StringIO()) as output:
            self.dp.labeled_expression(labeled)
            self.assertIn("myFunc(LOCAL paramX)", output.getvalue())

    def test_subroutine_block_print(self):
        labeled = MagicMock()
        labeled.type = "subroutine_block"
        label = MagicMock()
        label.text.decode.return_value = "myFunc"
        labeled.child_by_field_name.return_value = label
        labeled.text.decode.return_value = "myFunc:\n{\nparam1;\n}"

        block = MagicMock()
        block.type = "block"
        block.children = [self.mock_param_declaration(["paramX"])]
        labeled.children = [block]

        with patch("sys.stdout", new=StringIO()) as output:
            self.dp.subroutine_block(labeled)
            self.assertIn("myFunc(LOCAL paramX)", output.getvalue())

    @patch.object(DoxyPractice, "_get_macro_assignment")
    def test_macro_definition_with_assignment(self, mock_get_assignment):
        mock_get_assignment.return_value = ["Local", "42"]

        name_node = MagicMock()
        name_node.text.decode.return_value = "MY_MACRO"

        node = MagicMock()
        node.child_by_field_name.return_value = name_node

        with patch("sys.stdout", new=StringIO()) as output:
            self.dp.macro_definition(node)
            self.assertIn("Local MY_MACRO= 42", output.getvalue())
            mock_get_assignment.assert_called_once_with(node, "MY_MACRO")

    def test_macro_assignment_found(self):
        left = MagicMock()
        left.text.decode.return_value = "MY_MACRO"

        right = MagicMock()
        right.text.decode.return_value = "42"

        assign_expr = MagicMock()
        assign_expr.type = "assignment_expression"
        assign_expr.child_by_field_name.side_effect = lambda name: {"left": left, "right": right}[name]
        assign_expr.next_sibling = None

        macro_def = MagicMock()
        macro_def.next_sibling = assign_expr

        value = self.dp._get_macro_assignment(macro_def, "MY_MACRO")

        self.assertEqual(value, ("number", "42"))

    def test_macro_assignment_not_found(self):
        left = MagicMock()
        left.text.decode.return_value = "OTHER_MACRO"

        right = MagicMock()
        right.text.decode.return_value = "99"

        assign_expr = MagicMock()
        assign_expr.type = "assignment_expression"
        assign_expr.child_by_field_name.side_effect = lambda name: {"left": left, "right": right}[name]
        assign_expr.next_sibling = None

        macro_def = MagicMock()
        macro_def.next_sibling = assign_expr

        value = self.dp._get_macro_assignment(macro_def, "MY_MACRO")

        self.assertEqual(value, ("", ""))

    def test_replace_title_tag(self):
        result = self.dp.replace_practice_metadata("@Title: Example")
        self.assertEqual(result, "@brief Example")

    def test_replace_author_tag(self):
        result = self.dp.replace_practice_metadata("@Author: John Doe")
        self.assertEqual(result, "@author John Doe")

    def test_remove_description_tag(self):
        result = self.dp.replace_practice_metadata("@Description: Multi-line header")
        self.assertEqual(result, "@details Multi-line header")

    def test_replace_board_tag(self):
        result = self.dp.replace_practice_metadata("@Board: TMDSDOCK2838x")
        self.assertEqual(result, "@brief \\b Board TMDSDOCK2838x")

    def test_replace_chip_tag(self):
        result = self.dp.replace_practice_metadata("@Chip: TMS320F2838x")
        self.assertEqual(result, "@brief \\b Chip TMS320F2838x")

    def test_replace_copyright_tag(self):
        result = self.dp.replace_practice_metadata("@Copyright: 2025 Lauterbach")
        self.assertEqual(result, "@copyright 2025 Lauterbach")

    def test_no_change_on_unmatched_text(self):
        result = self.dp.replace_practice_metadata("Just a regular comment")
        self.assertEqual(result, "Just a regular comment")

    def test_multiple_tags_in_one_line(self):
        result = self.dp.replace_practice_metadata("@Title: Test @Author: Dev")
        self.assertEqual(result, "@brief Test @author Dev")

    def test_comment_skips_dashed_lines(self):
        node = MagicMock()
        node.text.decode.return_value = "; -----"
        node.next_sibling = None

        with patch("sys.stdout", new=StringIO()) as output:
            self.dp.comment(node)
            self.assertEqual(output.getvalue().strip(), "/// @file")

    @patch.object(DoxyPractice, "replace_practice_metadata")
    def test_comment_prints_processed_text(self, mock_replace):
        node = MagicMock()
        node.text.decode.return_value = "; @Title: Hello World"
        mock_replace.return_value = "/// @brief Hello World"

        with patch("sys.stdout", new=StringIO()) as output:
            self.dp.comment(node)
            output = output.getvalue().strip().splitlines()
            self.assertEqual(output[0], "/// @brief Hello World")
            mock_replace.assert_called_once()

    @patch.object(DoxyPractice, "replace_practice_metadata")
    def test_comment_adds_newline_if_next_node_not_on_same_line(self, mock_replace):
        node = MagicMock()
        node.text.decode.return_value = "; @Author: Jane"
        mock_replace.return_value = "/// @author Jane"

        with patch("sys.stdout", new=StringIO()) as output:
            self.dp.comment(node)
            output = output.getvalue().strip().splitlines()

            self.assertIn("/// @author Jane", output)
            mock_replace.assert_called_once()

    @patch.object(DoxyPractice, "comment")
    @patch.object(DoxyPractice, "macro_definition")
    @patch.object(DoxyPractice, "labeled_expression")
    def test_walk_calls_expected_functions(self, mock_labeled, mock_macro, mock_comment):
        labeled_node = MagicMock()
        labeled_node.type = "labeled_expression"
        labeled_node.next_sibling = None
        labeled_node.start_point = [2, 0]

        macro_node = MagicMock()
        macro_node.type = "macro_definition"
        macro_node.next_sibling = labeled_node
        macro_node.start_point = [1, 0]

        comment_node = MagicMock()
        comment_node.type = "comment"
        comment_node.next_sibling = macro_node
        comment_node.start_point = [0, 0]

        root = MagicMock()
        root.child.return_value = comment_node

        self.dp.walk(root)

        # Assert that all methods are called
        mock_comment.assert_called_once_with(comment_node)
        mock_macro.assert_called_once_with(macro_node)
        mock_labeled.assert_called_once_with(labeled_node)

    def test_variable_type_bool_on_true(self):
        result = self.dp._get_variable_type("TRUE()")
        self.assertEqual(result, "bool")

    def test_variable_type_bool_on_false(self):
        result = self.dp._get_variable_type("FALSE()")
        self.assertEqual(result, "bool")

    def test_variable_type_string_on_quotation(self):
        result = self.dp._get_variable_type('"string_variable"')
        self.assertEqual(result, "string")

    def test_variable_type_string_on_string_function(self):
        result = self.dp._get_variable_type('String("value")')
        self.assertEqual(result, "string")

    def test_variable_type_undefined_on_macro(self):
        result = self.dp._get_variable_type("&unknwn")
        self.assertEqual(result, "undefined")

    def test_is_return_command_return_false(self):
        command_node = MagicMock()
        command_node.type = "command_expression"
        self.assertFalse(self.dp._is_command_return(command_node))

    def test_is_return_command_return_true(self):
        command_node = MagicMock()
        command_node.type = "command_expression"

        command_child = MagicMock()
        command_child.text = b"return"

        command_node.child_by_field_name.side_effect = lambda field: command_child if field == "command" else None

        self.assertTrue(self.dp._is_command_return(command_node))

    def test_is_return_command_on_command_expression_with_no_return(self):
        command_node = MagicMock()
        command_node.type = "command_expression"

        command_child = MagicMock()
        command_child.text = b"non return"

        command_node.child_by_field_name.side_effect = lambda field: command_child if field == "command" else None

        self.assertFalse(self.dp._is_command_return(command_node))

    def test_is_return_command_on_non_command(self):
        node = MagicMock()
        node.type = "labeled_expression"

        self.assertFalse(self.dp._is_command_return(node))

    @patch.object(DoxyPractice, "_is_command_return")
    def test_get_return_type_no_return_command(self, mock_is_return):
        mock_is_return.return_value = False
        node = MagicMock()
        node.children = [MagicMock(), MagicMock()]
        self.assertEqual(self.dp._get_return_type(node), "")

    @patch.object(DoxyPractice, "_is_command_return")
    def test_get_return_type_return_without_arguments(self, mock_is_return):
        mock_is_return.side_effect = [False, True]
        ret_node = MagicMock()
        ret_node.child_by_field_name.return_value = None
        node = MagicMock()
        node.children = [MagicMock(), ret_node]
        self.assertEqual(self.dp._get_return_type(node), "")

    @patch.object(DoxyPractice, "_is_command_return")
    def test_get_return_type_multiple_arguments_returns_list(self, mock_is_return):
        mock_is_return.return_value = True
        arg1 = MagicMock()
        arg1.text = b'"a"'

        arg2 = MagicMock()
        arg2.text = b'"b"'

        values = MagicMock()
        values.children = [arg1, arg2]

        ret_child = MagicMock()
        ret_child.child_by_field_name.return_value = values
        ret_child.children = values

        node = MagicMock()
        node.children = [ret_child]

        self.assertEqual(self.dp._get_return_type(node), "list")

    @patch.object(DoxyPractice, "_get_variable_type")
    @patch.object(DoxyPractice, "_is_command_return")
    def test_get_return_type_single_argument_maps_type(self, mock_is_return, mock_get_type):
        mock_is_return.return_value = True
        mock_get_type.return_value = "string"

        arg1 = MagicMock()
        arg1.text = b'  "hello"  '

        values = MagicMock()
        values.children = [arg1]
        values.child.side_effect = lambda i: values.children[i]

        ret_child = MagicMock()
        ret_child.child_by_field_name.side_effect = lambda field: values if field == "arguments" else None
        ret_child.children = [values]

        node = MagicMock()
        node.children = [ret_child]

        self.assertEqual(self.dp._get_return_type(node), "string")
        mock_get_type.assert_called_once_with('"hello"')

    def test_get_argument_type_returns_matching_command(self):
        cmd = MagicMock()
        cmd.text = b"Global"

        md = MagicMock()
        md.type = "macro_definition"
        md.child_by_field_name.side_effect = lambda f: cmd if f == "command" else None

        m1 = MagicMock()
        m1.type = "macro"
        m1.text = b"paramX"

        m2 = MagicMock()
        m2.type = "macro"
        m2.text = b"other"

        md.children = [m1, m2]

        node = MagicMock()
        node.children = [MagicMock(), md]

        self.assertEqual(self.dp._get_argument_type(node, "paramX"), "Global")

    def test_get_argument_type_skips_non_macro_definition_nodes(self):
        non_md = MagicMock()
        non_md.type = "parameter_declaration"

        cmd = MagicMock()
        cmd.text = b"In"

        md = MagicMock()
        md.type = "macro_definition"
        md.child_by_field_name.side_effect = lambda f: cmd if f == "command" else None

        a = MagicMock()
        a.type = "macro"
        a.text = b"a"

        b = MagicMock()
        b.type = "macro"
        b.text = b"b"

        md.children = [a, b]

        node = MagicMock()
        node.children = [non_md, md]

        self.assertEqual(self.dp._get_argument_type(node, "b"), "In")

    def test_get_argument_type_no_match_returns_local(self):
        cmd = MagicMock()
        cmd.text = b"Global"

        md = MagicMock()
        md.type = "macro_definition"
        md.child_by_field_name.side_effect = lambda f: cmd if f == "command" else None

        a = MagicMock()
        a.type = "macro"
        a.text = b"a"

        b = MagicMock()
        b.type = "macro"
        b.text = b"b"

        md.children = [a, b]

        node = MagicMock()
        node.children = [md]

        self.assertEqual(self.dp._get_argument_type(node, "paramX"), "LOCAL")

    def test_get_argument_type_asserts_when_command_missing(self):
        md = MagicMock()
        md.type = "macro_definition"
        md.child_by_field_name.return_value = None

        m = MagicMock()
        m.type = "macro"
        m.text = b"paramX"

        md.children = [m]

        node = MagicMock()
        node.children = [md]

        with self.assertRaises(AssertionError):
            self.dp._get_argument_type(node, "paramX")

    def test_get_argument_type_asserts_when_command_text_none(self):
        cmd = MagicMock()
        cmd.text = None

        md = MagicMock()
        md.type = "macro_definition"
        md.child_by_field_name.side_effect = lambda f: cmd if f == "command" else None

        m = MagicMock()
        m.type = "macro"
        m.text = b"paramX"

        md.children = [m]

        node = MagicMock()
        node.children = [md]

        with self.assertRaises(AssertionError):
            self.dp._get_argument_type(node, "paramX")

    def test_get_argument_type_asserts_when_macro_text_none(self):
        cmd = MagicMock()
        cmd.text = b"Global"

        md = MagicMock()
        md.type = "macro_definition"
        md.child_by_field_name.side_effect = lambda f: cmd if f == "command" else None

        bad = MagicMock()
        bad.type = "macro"
        bad.text = None

        md.children = [bad]

        node = MagicMock()
        node.children = [md]

        with self.assertRaises(AssertionError):
            self.dp._get_argument_type(node, "paramX")

    @patch.object(DoxyPractice, "_is_command_return", return_value=False)
    def test_build_block_until_return_collects_all_and_builds_text_no_return(self, mock_is_return):
        first = MagicMock()
        first.text = b"LINE1\r\n"
        first.start_point = (1, 0)
        first.end_point = (1, 5)

        second = MagicMock()
        second.text = b"LINE2\r\n"
        second.start_point = (3, 0)
        second.end_point = (3, 5)

        third = MagicMock()
        third.text = b"LINE3\r\n"
        third.start_point = (4, 0)
        third.end_point = (4, 5)

        first.next_sibling = second
        second.next_sibling = third
        third.next_sibling = None

        node = MagicMock()
        node.next_sibling = first
        node.end_point = (1, 0)

        block = self.dp._build_block_until_return(node)

        self.assertEqual(block.type, "block")
        self.assertEqual(block.children, [first, second, third])

        expected = (b"(" + b"LINE1\r\n" + b"\r\n" * 2 + b"LINE2\r\n" + b"\r\n" * 1 + b"LINE3\r\n").rstrip(
            b" \r\n"
        ) + b")\r\n"

        self.assertEqual(block.text, expected)

    @patch.object(DoxyPractice, "_is_command_return")
    def test_build_block_until_return_stops_at_first_return_and_builds_text(self, mock_is_return):
        first = MagicMock()
        first.text = b"FIRST\r\n"
        first.start_point = (10, 0)
        first.end_point = (10, 5)

        second = MagicMock()
        second.text = b'RETURN "ok"\r\n'
        # gap 2 -> inserts 2*CRLF
        second.start_point = (12, 0)
        second.end_point = (12, 10)

        third = MagicMock()
        third.text = b"SHOULD_NOT_APPEAR\r\n"
        third.start_point = (20, 0)
        third.end_point = (20, 5)

        first.next_sibling = second
        second.next_sibling = third
        third.next_sibling = None

        node = MagicMock()
        node.next_sibling = first
        node.end_point = (10, 0)

        mock_is_return.side_effect = [False, True]

        block = self.dp._build_block_until_return(node)

        self.assertEqual(block.children, [first, second])

        expected = (b"(" + b"FIRST\r\n" + b"\r\n" * 2 + b'RETURN "ok"\r\n').rstrip(b" \r\n") + b")\r\n"

        self.assertEqual(block.text, expected)

    @patch.object(DoxyPractice, "_is_command_return", return_value=True)
    def test_build_block_until_return_includes_only_first_when_first_is_return(self, mock_is_return):
        only = MagicMock()
        only.text = b'RETURN "x"\r\n'
        only.start_point = (5, 0)
        only.end_point = (5, 10)
        only.next_sibling = None

        node = MagicMock()
        node.next_sibling = only
        node.end_point = (5, 0)

        block = self.dp._build_block_until_return(node)

        self.assertEqual(block.children, [only])

        expected = (b"(" + b'RETURN "x"\r\n').rstrip(b" \r\n") + b")\r\n"
        self.assertEqual(block.text, expected)

    def test_build_block_until_return_empty_when_no_siblings(self):
        node = MagicMock()
        node.next_sibling = None

        block = self.dp._build_block_until_return(node)

        self.assertEqual(block.children, [])
        self.assertEqual(block.text, b")\r\n")
