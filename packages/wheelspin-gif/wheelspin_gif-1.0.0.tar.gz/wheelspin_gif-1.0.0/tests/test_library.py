"""Test the WheelSpin library public API"""

import pytest
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wheelspin import (
    create_spinning_wheel,
    create_spinning_wheel_advanced,
    quick_spin,
    decision_wheel
)


@pytest.fixture
def test_output_dir(tmp_path):
    """Create a temporary directory for test outputs"""
    return tmp_path


def test_create_spinning_wheel_basic(test_output_dir):
    """Test basic spinning wheel creation"""
    names = ["Alice", "Bob", "Charlie", "Diana"]
    output_file = test_output_dir / "test_basic.gif"
    
    winner = create_spinning_wheel(names, str(output_file), size=400)
    
    assert winner in names, "Winner should be one of the input names"
    assert output_file.exists(), "GIF file should be created"
    assert output_file.stat().st_size > 0, "GIF file should not be empty"
    
    print(f"\nBasic test: winner={winner}")


def test_create_spinning_wheel_returns_string():
    """Test that create_spinning_wheel returns a string"""
    names = ["Option1", "Option2", "Option3"]
    
    winner = create_spinning_wheel(names, "temp_test.gif", size=300)
    
    assert isinstance(winner, str), "Winner should be a string"
    assert winner in names, "Winner should be from input list"
    
    # Cleanup
    if os.path.exists("temp_test.gif"):
        os.remove("temp_test.gif")


def test_create_spinning_wheel_advanced(test_output_dir):
    """Test advanced spinning wheel creation with custom options"""
    names = ["Red", "Blue", "Green"]
    output_file = test_output_dir / "test_advanced.gif"
    colors = ["#ff0000", "#0000ff", "#00ff00"]
    
    winner, info = create_spinning_wheel_advanced(
        segments=names,
        output_file=str(output_file),
        size=500,
        colors=colors,
        font_size=12,
        animation_speed=1.5
    )
    
    assert winner in names, "Winner should be one of the input names"
    assert isinstance(info, dict), "Should return info dictionary"
    assert 'winner_index' in info, "Info should contain winner_index"
    assert 'start_rotation' in info, "Info should contain start_rotation"
    assert 'frames_generated' in info, "Info should contain frames_generated"
    assert output_file.exists(), "GIF file should be created"
    
    print(f"\nAdvanced test: winner={winner}, frames={info['frames_generated']}")


def test_quick_spin(test_output_dir):
    """Test quick_spin convenience function"""
    names = ["Yes", "No", "Maybe"]
    output_file = test_output_dir / "test_quick.gif"
    
    winner = quick_spin(names, str(output_file))
    
    assert winner in names, "Winner should be one of the input names"
    assert output_file.exists(), "GIF file should be created"
    
    print(f"\nQuick spin: winner={winner}")


def test_decision_wheel(test_output_dir):
    """Test decision_wheel with question context"""
    options = ["Pizza", "Sushi", "Burgers"]
    
    # Temporarily change to test directory
    original_dir = os.getcwd()
    os.chdir(test_output_dir)
    
    try:
        winner = decision_wheel(options, "What should we eat?")
        
        assert winner in options, "Winner should be one of the options"
        assert Path("decision_wheel.gif").exists(), "Default decision_wheel.gif should be created"
    finally:
        os.chdir(original_dir)
    
    print(f"\nDecision wheel: winner={winner}")


def test_empty_segments_raises_error():
    """Test that empty segments list raises an error"""
    with pytest.raises(ValueError, match="cannot be empty"):
        create_spinning_wheel([], "test.gif")


def test_custom_colors(test_output_dir):
    """Test using custom color palette"""
    names = ["A", "B", "C", "D", "E"]
    output_file = test_output_dir / "test_colors.gif"
    custom_colors = ["#ff6b6b", "#ee5a24", "#feca57", "#48cae4", "#023047"]
    
    winner = create_spinning_wheel(names, str(output_file), size=400, colors=custom_colors)
    
    assert winner in names
    assert output_file.exists()
    
    print(f"\nCustom colors test: winner={winner}")


def test_large_segment_count(test_output_dir):
    """Test with many segments"""
    names = [f"Item_{i}" for i in range(50)]
    output_file = test_output_dir / "test_many.gif"
    
    winner = create_spinning_wheel(names, str(output_file), size=600)
    
    assert winner in names
    assert output_file.exists()
    
    print(f"\n50 segments test: winner={winner}")


def test_single_segment():
    """Test with just one segment (edge case)"""
    names = ["OnlyOption"]
    
    winner = create_spinning_wheel(names, "temp_single.gif", size=300)
    
    assert winner == "OnlyOption", "Single segment should always win"
    
    # Cleanup
    if os.path.exists("temp_single.gif"):
        os.remove("temp_single.gif")