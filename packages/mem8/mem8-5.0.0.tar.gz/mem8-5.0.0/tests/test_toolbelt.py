"""
Tests for CLI toolbelt management functionality.

Tests version checking, tool detection, and auto-fix features.
"""
import pytest
from unittest.mock import Mock, patch

from mem8.core.memory import MemoryManager
from mem8.core.config import Config
from mem8.core.template_source import ToolbeltTool, ToolbeltDefinition


class TestVersionChecking:
    """Test version comparison and detection."""

    def test_get_command_version_gh(self):
        """Test extracting version from gh --version output."""
        manager = MemoryManager(Config())

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout='gh version 2.60.1 (2024-01-01)\n',
                stderr='',
                returncode=0
            )

            version = manager._get_command_version('gh')
            assert version == '2.60.1'

    def test_get_command_version_no_match(self):
        """Test when version cannot be extracted."""
        manager = MemoryManager(Config())

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout='some output without version',
                stderr='',
                returncode=0
            )

            version = manager._get_command_version('unknown')
            assert version is None

    def test_compare_versions_greater_equal(self):
        """Test >= version comparison."""
        manager = MemoryManager(Config())

        # Exact match
        assert manager._compare_versions('2.60.0', '>=2.60')
        assert manager._compare_versions('2.60.0', '>=2.60.0')

        # Greater
        assert manager._compare_versions('2.61.0', '>=2.60')
        assert manager._compare_versions('3.0.0', '>=2.60')

        # Less (should fail)
        assert not manager._compare_versions('2.59.9', '>=2.60')
        assert not manager._compare_versions('1.0.0', '>=2.60')

    def test_compare_versions_equal(self):
        """Test == version comparison."""
        manager = MemoryManager(Config())

        assert manager._compare_versions('2.60.0', '==2.60.0')
        assert not manager._compare_versions('2.60.1', '==2.60.0')
        assert not manager._compare_versions('2.61.0', '==2.60.0')

    def test_compare_versions_greater(self):
        """Test > version comparison."""
        manager = MemoryManager(Config())

        assert manager._compare_versions('2.61.0', '>2.60')
        assert not manager._compare_versions('2.60.0', '>2.60')
        assert not manager._compare_versions('2.59.0', '>2.60')

    def test_compare_versions_less_equal(self):
        """Test <= version comparison."""
        manager = MemoryManager(Config())

        assert manager._compare_versions('2.60.0', '<=2.60')
        assert manager._compare_versions('2.59.0', '<=2.60')
        assert not manager._compare_versions('2.61.0', '<=2.60')

    def test_compare_versions_not_equal(self):
        """Test != version comparison."""
        manager = MemoryManager(Config())

        assert manager._compare_versions('2.61.0', '!=2.60.0')
        assert not manager._compare_versions('2.60.0', '!=2.60.0')

    def test_compare_versions_invalid(self):
        """Test that invalid comparisons return True (fail-open)."""
        manager = MemoryManager(Config())

        # Invalid version string - should not crash, returns True
        assert manager._compare_versions('2.60.0', 'invalid')
        assert manager._compare_versions('not-a-version', '>=2.60')


class TestToolbeltChecking:
    """Test toolbelt detection and checking."""

    def test_check_toolbelt_all_present(self):
        """Test when all required tools are present."""
        manager = MemoryManager(Config())

        with patch.object(manager, '_check_command_available', return_value=True):
            with patch('mem8.core.template_source.create_template_source') as mock_create:
                mock_source = Mock()
                mock_manifest = Mock()
                mock_manifest.toolbelt = ToolbeltDefinition(
                    required=[
                        ToolbeltTool(
                            name='git',
                            command='git',
                            description='Version control',
                            install={'windows': 'winget install Git.Git'}
                        )
                    ],
                    optional=[]
                )
                mock_source.load_manifest.return_value = mock_manifest
                mock_create.return_value = mock_source

                issues = manager._check_toolbelt()
                assert len(issues) == 0

    def test_check_toolbelt_missing_required(self):
        """Test detection of missing required tools."""
        manager = MemoryManager(Config())

        with patch.object(manager, '_check_command_available', return_value=False):
            with patch.object(manager, '_get_platform_key', return_value='windows'):
                with patch('mem8.core.template_source.create_template_source') as mock_create:
                    mock_source = Mock()
                    mock_manifest = Mock()
                    mock_manifest.toolbelt = ToolbeltDefinition(
                        required=[
                            ToolbeltTool(
                                name='ripgrep',
                                command='rg',
                                description='Fast search',
                                install={'windows': 'winget install ripgrep'}
                            )
                        ],
                        optional=[]
                    )
                    mock_source.load_manifest.return_value = mock_manifest
                    mock_create.return_value = mock_source

                    issues = manager._check_toolbelt()
                    assert len(issues) == 1
                    assert issues[0]['severity'] == 'warning'
                    assert 'Missing 1 required CLI tools' in issues[0]['description']
                    assert len(issues[0]['missing_tools']) == 1

    def test_check_toolbelt_version_mismatch(self):
        """Test detection of version mismatches."""
        manager = MemoryManager(Config())

        with patch.object(manager, '_check_command_available', return_value=True):
            with patch.object(manager, '_get_command_version', return_value='2.50.0'):
                with patch.object(manager, '_get_platform_key', return_value='windows'):
                    with patch('mem8.core.template_source.create_template_source') as mock_create:
                        mock_source = Mock()
                        mock_manifest = Mock()
                        mock_manifest.toolbelt = ToolbeltDefinition(
                            required=[
                                ToolbeltTool(
                                    name='gh',
                                    command='gh',
                                    description='GitHub CLI',
                                    install={'windows': 'winget install GitHub.cli'},
                                    version='>=2.60'
                                )
                            ],
                            optional=[]
                        )
                        mock_source.load_manifest.return_value = mock_manifest
                        mock_create.return_value = mock_source

                        issues = manager._check_toolbelt()
                        assert len(issues) == 1
                        assert issues[0]['severity'] == 'warning'
                        assert issues[0]['missing_tools'][0]['current_version'] == '2.50.0'
                        assert issues[0]['missing_tools'][0]['version'] == '>=2.60'

    def test_check_toolbelt_optional_missing(self):
        """Test detection of missing optional tools."""
        manager = MemoryManager(Config())

        with patch.object(manager, '_check_command_available', return_value=False):
            with patch.object(manager, '_get_platform_key', return_value='macos'):
                with patch('mem8.core.template_source.create_template_source') as mock_create:
                    mock_source = Mock()
                    mock_manifest = Mock()
                    mock_manifest.toolbelt = ToolbeltDefinition(
                        required=[],
                        optional=[
                            ToolbeltTool(
                                name='bat',
                                command='bat',
                                description='Better cat',
                                install={'macos': 'brew install bat'}
                            )
                        ]
                    )
                    mock_source.load_manifest.return_value = mock_manifest
                    mock_create.return_value = mock_source

                    issues = manager._check_toolbelt()
                    assert len(issues) == 1
                    assert issues[0]['severity'] == 'info'
                    assert 'optional CLI tools' in issues[0]['description']


class TestAutoFix:
    """Test auto-fix functionality."""

    def test_install_tool_success(self):
        """Test successful tool installation."""
        manager = MemoryManager(Config())

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr='')

            success, message = manager._install_tool('test-tool', 'echo "installing"')
            assert success
            assert 'Successfully installed' in message

    def test_install_tool_failure(self):
        """Test failed tool installation."""
        manager = MemoryManager(Config())

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr='Installation failed')

            success, message = manager._install_tool('test-tool', 'false')
            assert not success
            assert 'Installation failed' in message

    def test_install_tool_timeout(self):
        """Test installation timeout handling."""
        manager = MemoryManager(Config())

        with patch('subprocess.run') as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired('cmd', 300)

            success, message = manager._install_tool('test-tool', 'sleep 1000')
            assert not success
            assert 'timed out' in message.lower()

    def test_check_toolbelt_with_autofix(self):
        """Test auto-fix during toolbelt checking."""
        manager = MemoryManager(Config())
        fixes_applied = []

        with patch.object(manager, '_check_command_available', return_value=False):
            with patch.object(manager, '_get_platform_key', return_value='linux'):
                with patch.object(manager, '_install_tool', return_value=(True, 'Installed successfully')):
                    with patch('mem8.core.template_source.create_template_source') as mock_create:
                        mock_source = Mock()
                        mock_manifest = Mock()
                        mock_manifest.toolbelt = ToolbeltDefinition(
                            required=[
                                ToolbeltTool(
                                    name='ripgrep',
                                    command='rg',
                                    description='Fast search',
                                    install={'linux': 'apt install ripgrep'}
                                )
                            ],
                            optional=[]
                        )
                        mock_source.load_manifest.return_value = mock_manifest
                        mock_create.return_value = mock_source

                        issues = manager._check_toolbelt(auto_fix=True, fixes_applied=fixes_applied)

                        # Should have no issues since auto-fix succeeded
                        assert len(issues) == 0
                        # Should have recorded the fix
                        assert len(fixes_applied) == 1
                        assert 'Installed successfully' in fixes_applied[0]


class TestDiagnoseWorkspace:
    """Test complete workspace diagnostics."""

    def test_diagnose_returns_json_structure(self):
        """Test that diagnose_workspace returns proper structure."""
        config = Config()
        manager = MemoryManager(config)

        with patch.object(manager, '_check_toolbelt', return_value=[]):
            diagnosis = manager.diagnose_workspace(auto_fix=False)

            assert 'issues' in diagnosis
            assert 'fixes_applied' in diagnosis
            assert 'health_score' in diagnosis
            assert 'recommendations' in diagnosis
            assert isinstance(diagnosis['issues'], list)
            assert isinstance(diagnosis['fixes_applied'], list)
            assert isinstance(diagnosis['health_score'], (int, float))

    def test_diagnose_exit_code_behavior(self):
        """Test that diagnosis results can be used for exit codes."""
        config = Config()
        manager = MemoryManager(config)

        with patch.object(manager, '_check_toolbelt', return_value=[]):
            diagnosis = manager.diagnose_workspace(auto_fix=False)

            # When there are no issues, should exit 0
            has_issues = len(diagnosis['issues']) > 0
            expected_exit_code = 1 if has_issues else 0

            # This mimics the CLI behavior
            assert (expected_exit_code == 1) == has_issues


class TestPlatformDetection:
    """Test platform-specific behavior."""

    def test_get_platform_key_windows(self):
        """Test Windows platform detection."""
        manager = MemoryManager(Config())

        with patch('platform.system', return_value='Windows'):
            assert manager._get_platform_key() == 'windows'

    def test_get_platform_key_macos(self):
        """Test macOS platform detection."""
        manager = MemoryManager(Config())

        with patch('platform.system', return_value='Darwin'):
            assert manager._get_platform_key() == 'macos'

    def test_get_platform_key_linux(self):
        """Test Linux platform detection."""
        manager = MemoryManager(Config())

        with patch('platform.system', return_value='Linux'):
            assert manager._get_platform_key() == 'linux'

    def test_platform_specific_install_commands(self):
        """Test that correct install command is selected per platform."""
        manager = MemoryManager(Config())

        with patch.object(manager, '_check_command_available', return_value=False):
            with patch.object(manager, '_get_platform_key', return_value='windows'):
                with patch('mem8.core.template_source.create_template_source') as mock_create:
                    mock_source = Mock()
                    mock_manifest = Mock()
                    mock_manifest.toolbelt = ToolbeltDefinition(
                        required=[
                            ToolbeltTool(
                                name='ripgrep',
                                command='rg',
                                description='Fast search',
                                install={
                                    'windows': 'winget install ripgrep',
                                    'macos': 'brew install ripgrep',
                                    'linux': 'apt install ripgrep'
                                }
                            )
                        ],
                        optional=[]
                    )
                    mock_source.load_manifest.return_value = mock_manifest
                    mock_create.return_value = mock_source

                    issues = manager._check_toolbelt()
                    assert 'winget install ripgrep' in issues[0]['missing_tools'][0]['install']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
