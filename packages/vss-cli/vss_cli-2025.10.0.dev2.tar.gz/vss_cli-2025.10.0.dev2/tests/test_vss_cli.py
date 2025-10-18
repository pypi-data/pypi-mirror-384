import datetime
import os
import unittest

from click.testing import CliRunner
import click_log.core as logcore
import pytz

import vss_cli.cli as cli
from vss_cli.const import __version__
from vss_cli.utils.emoji import EMOJI_UNICODE

logcore.basic_config()


class TestVssCLI(unittest.TestCase):
    def setUp(self):
        self.test_folder = os.environ.get('VSS_API_TEST_FOLDER')
        self.test_network = os.environ.get('VSS_API_TEST_NETWORK')
        self.timestamp_dt = datetime.datetime.now(pytz.timezone('US/Eastern'))
        self.timestamp = self.timestamp_dt.strftime('%Y%d%M%H%M%S')
        self.timestamp_snap = self.timestamp_dt.strftime('%Y-%m-%d %H:%M')

    @classmethod
    def setUpClass(cls):
        super(TestVssCLI, cls).setUpClass()
        # setting up the CLI
        cls.runner = CliRunner()
        # Setting up credentials and endpoint
        cls.vss_api_user = os.environ.get('_VSS_API_USER')
        cls.vss_api_pass = os.environ.get('_VSS_API_USER_PASS')
        cls.vss_api_endpoint = os.environ.get('_VSS_API_ENDPOINT')
        cls.vss_api_endpoint_alt = os.environ.get('_VSS_API_ENDPOINT_ALT')
        # create main cli endpoint
        r = cls.runner.invoke(
            cli.cli,
            [
                '--username',
                cls.vss_api_user,
                '--password',
                cls.vss_api_pass,
                '--endpoint',
                cls.vss_api_endpoint,
                'configure',
                'mk',
                '--replace',
                '--endpoint-name',
                'cloud-api',
            ],
            catch_exceptions=False,
        )
        assert r.exit_code == 0
        print(r.output.encode())

    def test_alt_config(self):
        r = self.runner.invoke(
            cli.cli,
            [
                '--username',
                self.vss_api_user,
                '--password',
                self.vss_api_pass,
                '--endpoint',
                self.vss_api_endpoint_alt,
                'configure',
                'mk',
                '--replace',
                '--endpoint-name',
                'vss-api',
            ],
            catch_exceptions=False,
        )
        assert r.exit_code == 0

    def test_config_set_general(self):
        r = self.runner.invoke(
            cli.cli,
            ['configure', 'set', 'check_for_messages', 'yes'],
            catch_exceptions=False,
        )
        assert r.exit_code == 0
        r = self.runner.invoke(
            cli.cli,
            ['configure', 'set', 'timeout', '120'],
            catch_exceptions=False,
        )
        assert r.exit_code == 0

    def test_config_default_endpoint(self):
        default_mark = EMOJI_UNICODE.get(":white_heavy_check_mark:")
        r = self.runner.invoke(
            cli.cli,
            ['configure', 'set', 'default_endpoint_name', 'vss-api'],
            catch_exceptions=False,
        )
        assert r.exit_code == 0
        r = self.runner.invoke(
            cli.cli, ['configure', 'ls'], catch_exceptions=False
        )
        assert r.exit_code == 0
        o_lines = r.output.split('\n')
        # get default endpoint line
        default = [line for line in o_lines if default_mark in line]
        # check if line is not empty
        self.assertGreater(len(default), 0)
        # check if vss-api is default
        self.assertIn('vss-api', ''.join(default))
        # cloud-api (original)
        r = self.runner.invoke(
            cli.cli,
            ['configure', 'set', 'default_endpoint_name', 'cloud-api'],
            catch_exceptions=False,
        )
        r = self.runner.invoke(
            cli.cli, ['configure', 'ls'], catch_exceptions=False
        )
        assert r.exit_code == 0
        o_lines = r.output.split('\n')
        # get default endpoint line
        default = [line for line in o_lines if default_mark in line]
        # check if line is not empty
        self.assertGreater(len(default), 0)
        # check if vss-api is default
        self.assertIn('cloud-api', ''.join(default))

    def test_version(self):
        result = self.runner.invoke(
            cli.cli, ['--version'], catch_exceptions=False
        )
        self.assertEqual(result.exit_code, 0)
        assert __version__ in result.output

    def test_vss_shell(self):
        result = self.runner.invoke(
            cli.cli, ['shell'], input=':q\n', catch_exceptions=False
        )
        self.assertIn('history', result.output)
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(
            cli.cli,
            ['shell', '--history', '~/vss-cli/history'],
            input=':q\n',
            catch_exceptions=False,
        )
        self.assertIn('History', result.output)
        self.assertEqual(result.exit_code, 0)

    def test_account_get_personal(self):
        result = self.runner.invoke(
            cli.cli,
            [
                '--endpoint',
                self.vss_api_endpoint,
                'account',
                'get',
                'personal',
            ],
            catch_exceptions=False,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('username', result.output)

    def test_account_get_groups(self):
        result = self.runner.invoke(
            cli.cli,
            ['--endpoint', self.vss_api_endpoint, 'account', 'get', 'groups'],
            catch_exceptions=False,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('hig-web-services', result.output)
