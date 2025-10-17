"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from pathlib import Path

from perceptra_zero_shot.cli.main import cli
from perceptra_zero_shot.core.result import DetectionResult


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestCLI:
    """Tests for CLI commands."""
    
    def test_cli_version(self, runner):
        """Test version command."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
    
    def test_list_models_command(self, runner):
        """Test list-models command."""
        result = runner.invoke(cli, ['list-models'])
        assert result.exit_code == 0
        assert "owlv2-base" in result.output
    
    @patch('perceptra_zero_shot.cli.main.ZeroShotDetector')
    @patch('perceptra_zero_shot.cli.main.Image')
    def test_detect_command(self, mock_image, mock_detector_class, runner):
        """Test detect command."""
        # Setup mocks
        mock_detector = Mock()
        mock_result = DetectionResult()
        mock_detector.detect.return_value = mock_result
        mock_detector_class.return_value = mock_detector
        
        mock_img = Mock()
        mock_image.open.return_value = mock_img
        
        # Run command
        with runner.isolated_filesystem():
            # Create a dummy file
            Path("test.jpg").touch()
            
            result = runner.invoke(cli, [
                'detect', 'test.jpg', 'cat', 'dog',
                '--model', 'owlv2-base'
            ])
            
            assert result.exit_code == 0