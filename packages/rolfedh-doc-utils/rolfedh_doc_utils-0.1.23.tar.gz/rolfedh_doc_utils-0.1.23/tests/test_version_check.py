"""Tests for version_check module."""
import sys
import os
from unittest.mock import patch
import pytest

from doc_utils.version_check import (
    detect_install_method,
    parse_version,
    show_update_notification,
)


class TestDetectInstallMethod:
    """Tests for install method detection."""

    def test_detect_pipx_from_prefix(self):
        """Test detection when sys.prefix contains 'pipx'."""
        with patch('sys.prefix', '/home/user/.local/pipx/venvs/rolfedh-doc-utils'):
            assert detect_install_method() == 'pipx'

    def test_detect_pipx_from_env(self):
        """Test detection from PIPX_HOME environment variable."""
        with patch('sys.prefix', '/home/user/.local/share/pipx/venvs/rolfedh-doc-utils'):
            with patch.dict(os.environ, {'PIPX_HOME': '/home/user/.local/share/pipx'}):
                assert detect_install_method() == 'pipx'

    def test_detect_pip(self):
        """Test detection defaults to pip."""
        with patch('sys.prefix', '/usr'):
            # Clear PIPX_HOME if set
            env = {k: v for k, v in os.environ.items() if k != 'PIPX_HOME'}
            with patch.dict(os.environ, env, clear=True):
                assert detect_install_method() == 'pip'

    def test_detect_pip_user(self):
        """Test detection for pip --user installations."""
        with patch('sys.prefix', '/home/user/.local'):
            # Clear PIPX_HOME if set
            env = {k: v for k, v in os.environ.items() if k != 'PIPX_HOME'}
            with patch.dict(os.environ, env, clear=True):
                assert detect_install_method() == 'pip'


class TestParseVersion:
    """Tests for version parsing."""

    def test_parse_simple_version(self):
        """Test parsing simple semantic version."""
        assert parse_version('0.1.19') == (0, 1, 19)

    def test_parse_version_with_prerelease(self):
        """Test parsing version with pre-release suffix."""
        assert parse_version('0.1.19-dev') == (0, 1, 19)

    def test_parse_version_with_build(self):
        """Test parsing version with build metadata."""
        assert parse_version('0.1.19+g1234567') == (0, 1, 19)

    def test_parse_invalid_version(self):
        """Test parsing invalid version returns (0,)."""
        assert parse_version('invalid') == (0,)

    def test_version_comparison(self):
        """Test that parsed versions can be compared."""
        assert parse_version('0.1.20') > parse_version('0.1.19')
        assert parse_version('0.2.0') > parse_version('0.1.99')
        assert parse_version('1.0.0') > parse_version('0.99.99')


class TestShowUpdateNotification:
    """Tests for update notification display."""

    def test_show_notification_pipx(self, capsys):
        """Test notification recommends pipx for pipx installations."""
        with patch('doc_utils.version_check.detect_install_method', return_value='pipx'):
            show_update_notification('0.1.20', '0.1.19')
            captured = capsys.readouterr()
            assert 'pipx upgrade' in captured.err
            assert 'pip install' not in captured.err

    def test_show_notification_pip(self, capsys):
        """Test notification recommends pip for pip installations."""
        with patch('doc_utils.version_check.detect_install_method', return_value='pip'):
            show_update_notification('0.1.20', '0.1.19')
            captured = capsys.readouterr()
            assert 'pip install --upgrade' in captured.err
            assert 'pipx' not in captured.err

    def test_notification_includes_versions(self, capsys):
        """Test notification includes both current and latest versions."""
        with patch('doc_utils.version_check.detect_install_method', return_value='pip'):
            show_update_notification('0.1.20', '0.1.19')
            captured = capsys.readouterr()
            assert '0.1.19' in captured.err
            assert '0.1.20' in captured.err
            assert '📦' in captured.err
