"""Test text positioning based on segment count"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wheelspin.wheel_generator import WheelGenerator


@pytest.fixture
def generator():
    """Fixture to create a WheelGenerator instance"""
    return WheelGenerator(size=500)


@pytest.fixture
def radius():
    """Standard radius for testing"""
    return 250


def test_inner_position_few_segments(generator, radius):
    """Test that few segments use inner position"""
    segments = 8
    labels = ["Prize 1"]
    angle_per_segment = 360 / segments
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels)
    
    assert result['position'] == 'inner', "8 segments should use inner position"
    assert result['text_radius_ratio'] == 0.65
    
    print(f"\n8 segments: {result['position']} position, radius={result['text_radius']:.1f}px")


def test_inner_position_medium_segments(generator, radius):
    """Test that medium segment count still uses inner position"""
    segments = 20
    labels = ["Prize 1"]
    angle_per_segment = 360 / segments
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels)
    
    assert result['position'] == 'inner', "20 segments with short text should use inner position"
    
    print(f"\n20 segments: {result['position']} position, radius={result['text_radius']:.1f}px")


def test_outer_position_many_segments(generator, radius):
    """Test that many segments use outer position"""
    segments = 50
    labels = ["Prize 1"]
    angle_per_segment = 360 / segments
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels)
    
    assert result['position'] == 'outer', "50 segments should use outer position"
    assert result['text_radius_ratio'] == 0.85
    
    print(f"\n50 segments: {result['position']} position, radius={result['text_radius']:.1f}px")


def test_outer_position_100_segments(generator, radius):
    """Test that 100 segments use outer position"""
    segments = 100
    labels = ["Prize 1"]
    angle_per_segment = 360 / segments
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels)
    
    assert result['position'] == 'outer', "100 segments should use outer position"
    
    print(f"\n100 segments: {result['position']} position, radius={result['text_radius']:.1f}px")


def test_longer_text_100_segments(generator, radius):
    """Test that longer text with 100 segments uses outer position"""
    segments = 100
    labels = ["Prize 100"]
    angle_per_segment = 360 / segments
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels)
    
    assert result['position'] == 'outer', "100 segments with longer text should use outer position"
    
    print(f"\n100 segments (longer text): {result['position']} position, radius={result['text_radius']:.1f}px")


@pytest.mark.parametrize("segments,expected_position", [
    (5, "inner"),
    (10, "inner"),
    (30, "inner"),
    (75, "outer"),
    (150, "outer"),
])
def test_position_by_segment_count(generator, radius, segments, expected_position):
    """Parametrized test for various segment counts"""
    labels = ["Item"]
    angle_per_segment = 360 / segments
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels)
    
    assert result['position'] == expected_position, \
        f"Segments={segments} should use {expected_position} position"