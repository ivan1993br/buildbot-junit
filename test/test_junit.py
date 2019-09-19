import re
import textwrap

from twisted.internet import defer
from twisted.trial import unittest

from buildbot import config
from buildbot.process import properties
from buildbot.process import remotetransfer
from buildbot.process.results import EXCEPTION
from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
from buildbot.steps import shell
from buildbot.test.fake.remotecommand import Expect
from buildbot.test.fake.remotecommand import ExpectRemoteRef
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.test.util import config as configmixin
from buildbot.test.util import steps
from buildbot.test.util.misc import TestReactorMixin

from buildbot_junit import JUnitShellCommand

class TestShellJUnitCommandExecution(steps.BuildStepMixin,
                                configmixin.ConfigErrorsMixin,
                                TestReactorMixin,
                                unittest.TestCase):

    def setUp(self):
        self.setUpTestReactor()
        return self.setUpBuildStep()

    def tearDown(self):
        return self.tearDownBuildStep()

    def assertLegacySummary(self, step, running, done=None):
        done = done or running
        self.assertEqual(
            (step._getLegacySummary(done=False),
             step._getLegacySummary(done=True)),
            (running, done))

    def test_doStepIf_False(self):
        self.setupStep(JUnitShellCommand("faker_report_dir", command="echo hello"))
        self.expectCommands(
            ExpectShell(workdir='wkdir',
                        command='echo hello')
            + ExpectShell.log('stdio', stdout='hello')
            + ExpectShell(workdir='wkdir',
                        command=['stat', {'file': '~/dev/install/log/test-results/ros_driver_base'}])
        )
        # self.expectOutcome(result=SKIPPED,
        #                    state_string="'echo hello' (skipped)")
        return self.runStep()

    def test_constructor_args_kwargs(self):
        # this is an ugly way to define an API, but for now check that
        # the RemoteCommand arguments are properly passed on
        step = JUnitShellCommand("faker_report_dir", command="echo hello", doStepIf=False)
        self.assertEqual(step.remote_kwargs, dict(want_stdout=0,
                                                  logEnviron=False,
                                                  workdir='build',
                                                  usePTY=None))

    def test_constructor_args_validity(self):
        # this checks that an exception is raised for invalid arguments
        with self.assertRaisesConfigError(
                "Invalid argument(s) passed to RemoteShellCommand: "):
            shell.ShellCommand(workdir='build', command="echo Hello World",
                                       wrongArg1=1, wrongArg2='two')

    def test_getLegacySummary_from_empty_command(self):
        # this is more of a regression test for a potential failure, really
        step = JUnitShellCommand("faker_report_dir", command="echo hello", doStepIf=False, workdir='build')
        step.rendered = True
        self.runStep()

    def test_getLegacySummary_from_short_command(self):
        step = shell.ShellCommand(workdir='build', command="true")
        step.rendered = True
        self.assertLegacySummary(step, "'true'")

    def test_getLegacySummary_from_short_command_list(self):
        step = shell.ShellCommand(workdir='build', command=["true"])
        step.rendered = True
        self.assertLegacySummary(step, "'true'")

    def test_getLegacySummary_from_med_command(self):
        step = shell.ShellCommand(command="echo hello")
        step.rendered = True
        self.assertLegacySummary(step, "'echo hello'")

    def test_getLegacySummary_from_med_command_list(self):
        step = shell.ShellCommand(command=["echo", "hello"])
        step.rendered = True
        self.assertLegacySummary(step, "'echo hello'")

# self.setupStep(shell.TreeSize())
#         self.expectCommands(
#             ExpectShell(workdir='wkdir',
#                         command=['du', '-s', '-k', '.'])
#             + ExpectShell.log('stdio', stdout='9292    .\n')
#             + 0
#         )