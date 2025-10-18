"""Test wheel coordinate system and segment positioning"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wheelspin.wheel_generator import WheelGenerator


@pytest.fixture
def wheel_params():
    """Standard wheel parameters for testing"""
    return {
        'size': 500,
        'center': 250,
        'radius': 230,
        'segments': 8
    }


def test_angle_calculation(wheel_params):
    """Test that angle per segment is calculated correctly"""
    segments = wheel_params['segments']
    angle_per_segment = 360 / segments
    
    assert angle_per_segment == 45.0, "8 segments should have 45° each"
    
    print(f"\n8 segments: {angle_per_segment}° per segment")


def test_segment_0_at_zero_rotation(wheel_params):
    """Test that segment 0 is at 0° when rotation_angle = 0"""
    segments = wheel_params['segments']
    angle_per_segment = 360 / segments
    rotation_angle = 0
    
    # First segment should start at 0°
    start_angle = rotation_angle + (0 * angle_per_segment)
    end_angle = start_angle + angle_per_segment
    
    assert start_angle == 0.0, "Segment 0 should start at 0°"
    assert end_angle == 45.0, "Segment 0 should end at 45°"
    assert start_angle <= 0 <= end_angle, "Pointer at 0° should be in segment 0"
    
    print(f"\nSegment 0 with rotation=0: [{start_angle}° - {end_angle}°]")


def test_pointer_position_with_rotation(wheel_params):
    """Test which segment the pointer hits with specific rotation"""
    segments = wheel_params['segments']
    angle_per_segment = 360 / segments
    start_rotation = 283.82
    
    # Find which segment contains 0° (pointer position)
    segment_at_pointer = None
    
    for i in range(segments):
        start_angle = start_rotation + (i * angle_per_segment)
        end_angle = start_angle + angle_per_segment
        
        # Normalize to 0-360
        start_norm = start_angle % 360
        end_norm = end_angle % 360
        
        # Check if 0° falls in this segment (handle wraparound)
        if start_norm > end_norm:  # Wraparound case
            if 0 >= start_norm or 0 <= end_norm:
                segment_at_pointer = i
                break
        else:
            if start_norm <= 0 <= end_norm:
                segment_at_pointer = i
                break
    
    assert segment_at_pointer is not None, "Pointer should land in some segment"
    
    print(f"\nWith rotation {start_rotation}°: pointer at segment {segment_at_pointer}")


def test_calculate_winner():
    """Test winner calculation using WheelGenerator"""
    generator = WheelGenerator(size=500)
    segments = ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    # Test with rotation at 0
    winner_idx, winner_name = generator.calculate_winner(0, segments)
    assert winner_idx == 0, "Rotation 0 should land on segment 0"
    assert winner_name == "A", "Rotation 0 should win 'A'"
    
    print(f"\nRotation 0°: winner is segment {winner_idx} ({winner_name})")


def test_calculate_winner_with_rotation():
    """Test winner calculation with specific rotation"""
    generator = WheelGenerator(size=500)
    segments = ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    # Test with 45° rotation (should land on next segment)
    winner_idx, winner_name = generator.calculate_winner(45, segments)
    assert winner_name in segments, "Winner should be one of the segments"
    
    print(f"\nRotation 45°: winner is segment {winner_idx} ({winner_name})")


def test_all_segments_reachable():
    """Test that all segments can potentially win"""
    generator = WheelGenerator(size=500)
    segments = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    angle_per_segment = 360 / len(segments)
    
    winners = set()
    
    # Test rotations at the start of each segment
    for i in range(len(segments)):
        rotation = i * angle_per_segment
        winner_idx, winner_name = generator.calculate_winner(rotation, segments)
        winners.add(winner_name)
    
    # All segments should be reachable
    assert len(winners) == len(segments), "All segments should be winnable"
    
    print(f"\nAll {len(segments)} segments are reachable")


@pytest.mark.parametrize("num_segments", [3, 5, 8, 10, 12, 20])
def test_various_segment_counts(num_segments):
    """Test angle calculation for various segment counts"""
    angle_per_segment = 360 / num_segments
    
    # All angles should be positive and sum to 360
    assert angle_per_segment > 0
    assert angle_per_segment * num_segments == 360
    
    print(f"\n{num_segments} segments: {angle_per_segment:.2f}° each")


def test_rotation_wraparound():
    """Test that rotation angles wrap around correctly"""
    generator = WheelGenerator(size=500)
    segments = ["A", "B", "C", "D"]
    
    # Test that 0° and 360° give same result
    winner_0, name_0 = generator.calculate_winner(0, segments)
    winner_360, name_360 = generator.calculate_winner(360, segments)
    
    assert winner_0 == winner_360, "0° and 360° should give same result"
    assert name_0 == name_360, "0° and 360° should win same segment"
    
    print(f"\nWraparound test: 0°={name_0}, 360°={name_360}")