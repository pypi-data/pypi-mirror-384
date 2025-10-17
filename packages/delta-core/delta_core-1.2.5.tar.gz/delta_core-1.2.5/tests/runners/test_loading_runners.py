import unittest
import delta.runners.factory as runner_factory
from delta.exceptions.runners import DeltaRunnerNotFound, DeltaRunnerError
from delta.runners.tests import AbstractDeltaRunnerTest


class TestRunnerFactory(unittest.TestCase):
    def test_create(self):
        model = {"type": 'runner_a'}
        runner = runner_factory.create(model)
        self.assertIsNotNone(runner)
        self.assertIsInstance(runner, AbstractDeltaRunnerTest)
        self.assertEqual('A', runner.value)

        model = {"type": 'runner_b'}
        runner = runner_factory.create(model)
        self.assertIsNotNone(runner)
        self.assertIsInstance(runner, AbstractDeltaRunnerTest)
        self.assertEqual('B', runner.value)

        model = {"type": "foobar"}
        with self.assertRaises(DeltaRunnerNotFound):
            runner = runner_factory.create(model)

        model = {"parameters": {"foo": "bar"}}
        with self.assertRaises(DeltaRunnerError):
            runner = runner_factory.create(model)
