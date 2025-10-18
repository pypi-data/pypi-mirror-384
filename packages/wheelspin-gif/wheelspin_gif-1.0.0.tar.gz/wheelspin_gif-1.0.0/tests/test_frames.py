"""Test animation frame calculation and duration scaling"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wheelspin.wheel_generator import WheelGenerator


@pytest.fixture
def generator():
    """Fixture to create a WheelGenerator instance"""
    return WheelGenerator(size=500, animation_speed=1.0)


def calculate_expected_frames(segments):
    """Helper function to calculate expected frames"""
    base_frames = 60
    base_segments = 8
    frame_multiplier = max(1.0, segments / base_segments * 0.27)
    return int(base_frames * frame_multiplier)


def test_8_segments_duration(generator):
    """Test that 8 segments produces correct frame count"""
    frames = generator.calculate_frames(8)
    expected = 60
    
    assert frames == expected, f"8 segments should produce {expected} frames"
    
    duration = frames * 0.05  # 50ms per frame
    print(f"\n8 segments: {frames} frames ({duration:.1f}s)")


def test_16_segments_duration(generator):
    """Test that 16 segments produces correct frame count"""
    frames = generator.calculate_frames(16)
    expected = calculate_expected_frames(16)
    
    assert frames == expected
    
    duration = frames * 0.05
    print(f"\n16 segments: {frames} frames ({duration:.1f}s)")


def test_50_segments_duration(generator):
    """Test that 50 segments produces correct frame count"""
    frames = generator.calculate_frames(50)
    expected = calculate_expected_frames(50)
    
    assert frames == expected
    
    duration = frames * 0.05
    assert duration >= 5.0, "50 segments should take at least 5 seconds"
    
    print(f"\n50 segments: {frames} frames ({duration:.1f}s)")


def test_100_segments_duration(generator):
    """Test that 100 segments produces correct frame count"""
    frames = generator.calculate_frames(100)
    expected = 202
    
    assert frames == expected, f"100 segments should produce {expected} frames"
    
    duration = frames * 0.05
    assert 10.0 <= duration <= 10.2, "100 segments should take ~10 seconds"
    
    print(f"\n100 segments: {frames} frames ({duration:.1f}s)")


def test_200_segments_duration(generator):
    """Test that 200 segments produces correct frame count"""
    frames = generator.calculate_frames(200)
    expected = calculate_expected_frames(200)
    
    assert frames == expected
    
    duration = frames * 0.05
    assert duration >= 20.0, "200 segments should take at least 20 seconds"
    
    print(f"\n200 segments: {frames} frames ({duration:.1f}s)")


@pytest.mark.parametrize("segments,min_duration", [
    (8, 3.0),
    (32, 3.0),
    (50, 5.0),
    (100, 10.0),
    (200, 20.0),
])
def test_minimum_duration(generator, segments, min_duration):
    """Test that animation duration meets minimum requirements"""
    frames = generator.calculate_frames(segments)
    duration = frames * 0.05
    
    assert duration >= min_duration, \
        f"{segments} segments should have duration >= {min_duration}s"


def test_frame_count_increases_with_segments(generator):
    """Test that more segments result in more frames"""
    frames_8 = generator.calculate_frames(8)
    frames_50 = generator.calculate_frames(50)
    frames_100 = generator.calculate_frames(100)
    
    assert frames_8 < frames_50 < frames_100, \
        "Frame count should increase with segment count"
    
    print(f"\nProgression: 8seg={frames_8}f, 50seg={frames_50}f, 100seg={frames_100}f")


def test_animation_speed_multiplier():
    """Test that animation_speed parameter affects frame count"""
    gen_normal = WheelGenerator(size=500, animation_speed=1.0)
    gen_fast = WheelGenerator(size=500, animation_speed=2.0)
    gen_slow = WheelGenerator(size=500, animation_speed=0.5)
    
    segments = 50
    frames_normal = gen_normal.calculate_frames(segments)
    frames_fast = gen_fast.calculate_frames(segments)
    frames_slow = gen_slow.calculate_frames(segments)
    
    assert frames_fast > frames_normal, "Faster speed should produce more frames"
    assert frames_slow < frames_normal, "Slower speed should produce fewer frames"
    
    print(f"\nSpeed test (50 segments): slow={frames_slow}f, normal={frames_normal}f, fast={frames_fast}f")