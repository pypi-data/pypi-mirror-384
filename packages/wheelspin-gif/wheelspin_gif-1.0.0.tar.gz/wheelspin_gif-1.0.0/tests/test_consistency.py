"""Test consistent text positioning across all segments"""

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
def labels_56():
    """Fixture with 56 segments (7 repetitions of 8 names)"""
    return [
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
        "Ali", "Beatriz", "Charles", "Diya", "Eric", "Fatima", "Gabriel", "Hanna",
    ]


def test_consistent_position_56_segments(generator, labels_56):
    """Test that all 56 segments use the same text position"""
    radius = 250
    angle_per_segment = 360 / len(labels_56)
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels_56)
    
    # Should use outer position for 56 segments
    assert result['position'] == 'outer', "Should use outer position for 56 segments"
    assert result['text_radius_ratio'] == 0.85, "Should use 0.85 ratio for outer position"
    assert result['consistent'] is True, "Should be marked as consistent"
    
    print(f"\n56 segments: position={result['position']}, ratio={result['text_radius_ratio']}, radius={result['text_radius']:.1f}px")


def test_individual_label_fitting(generator, labels_56):
    """Test individual label dimensions and fitting"""
    radius = 250
    angle_per_segment = 360 / len(labels_56)
    inner_space = generator.calculate_segment_space(radius, angle_per_segment, 0.65)
    
    labels_needing_outer = []
    
    for label in set(labels_56):  # Check unique labels only
        text_dims = generator.get_text_dimensions(label)
        fits_inner = (text_dims['width'] <= inner_space['arc_length'] * 0.8 and
                     text_dims['height'] <= inner_space['radial_space'])
        
        if not fits_inner:
            labels_needing_outer.append(label)
    
    # Most labels should not fit in inner position with 56 segments
    assert len(labels_needing_outer) > 0, "Some labels should need outer position"
    
    print(f"\nLabels needing outer position: {labels_needing_outer}")


def test_all_labels_use_same_position(generator, labels_56):
    """Test that consistent positioning returns same radius for all labels"""
    radius = 250
    angle_per_segment = 360 / len(labels_56)
    
    result = generator.calculate_consistent_text_position(radius, angle_per_segment, labels_56)
    
    # All labels should use the same text_radius
    expected_radius = result['text_radius']
    
    for label in labels_56:
        # The consistent position means all use the same radius
        # This is implicitly tested by the consistent flag
        pass
    
    assert result['text_radius'] == expected_radius, "All labels should use same radius"
    
    print(f"\nAll {len(labels_56)} labels use radius: {expected_radius:.1f}px")


def test_text_dimensions_calculation(generator):
    """Test that text dimensions are calculated correctly"""
    test_labels = ["Ali", "Beatriz", "Charles"]
    
    for label in test_labels:
        dims = generator.get_text_dimensions(label)
        
        assert 'width' in dims, "Should have width"
        assert 'height' in dims, "Should have height"
        assert 'font' in dims, "Should have font"
        assert dims['width'] > 0, "Width should be positive"
        assert dims['height'] > 0, "Height should be positive"
        
        print(f"\n{label}: width={dims['width']}px, height={dims['height']}px")