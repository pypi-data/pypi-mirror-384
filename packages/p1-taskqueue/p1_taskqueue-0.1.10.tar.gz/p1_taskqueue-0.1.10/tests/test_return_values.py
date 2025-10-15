from taskqueue.cmanager import dynamic_class_method_executor
from taskqueue.cmanager import dynamic_function_executor


def function_that_returns_value():
    return "function_return_value"


class TestClass:
    def method_that_returns_value(self):
        return "method_return_value"


class TestExecutorReturnValues:

    def test_dynamic_function_executor_given_function_returns_value_expect_return_none(self):
        result = dynamic_function_executor(
            "tests.test_return_values",
            "function_that_returns_value",
            [],
            {},
            None
        )

        assert result is None

    def test_dynamic_class_method_executor_given_method_returns_value_expect_return_none(self):
        result = dynamic_class_method_executor(
            "tests.test_return_values",
            "TestClass",
            "method_that_returns_value",
            [],
            {},
            None
        )

        assert result is None

    def test_dynamic_function_executor_given_function_with_side_effects_expect_function_executed_and_return_none(self):
        global function_executed
        function_executed = False

        def function_with_side_effect():
            global function_executed
            function_executed = True
            return "should_be_ignored"

        import sys
        sys.modules[__name__].function_with_side_effect = function_with_side_effect

        result = dynamic_function_executor(
            "tests.test_return_values",
            "function_with_side_effect",
            [],
            {},
            None
        )

        assert function_executed
        assert result is None

    def test_dynamic_class_method_executor_given_method_with_side_effects_expect_method_executed_and_return_none(self):
        class TestClassWithSideEffect:
            def __init__(self):
                self.method_executed = False

            def method_with_side_effect(self):
                self.method_executed = True
                return "should_be_ignored"

        import sys
        sys.modules[__name__].TestClassWithSideEffect = TestClassWithSideEffect

        result = dynamic_class_method_executor(
            "tests.test_return_values",
            "TestClassWithSideEffect",
            "method_with_side_effect",
            [],
            {},
            None
        )

        assert result is None
