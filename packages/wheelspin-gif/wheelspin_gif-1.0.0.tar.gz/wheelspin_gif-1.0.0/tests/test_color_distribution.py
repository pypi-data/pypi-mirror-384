"""Test to verify color distribution - no adjacent segments should have the same color"""

import pytest
from wheelspin.wheel_generator import WheelGenerator


@pytest.fixture
def generator():
    """Fixture to create a WheelGenerator instance"""
    return WheelGenerator(size=500)


def check_no_adjacent_duplicates(colors):
    """Helper function to check if any adjacent segments have the same color"""
    for i in range(len(colors)):
        next_i = (i + 1) % len(colors)
        if colors[i] == colors[next_i]:
            return False, f"Segments {i} and {next_i} both have {colors[i]}"
    return True, "No adjacent duplicates"


def test_five_segments_four_colors(generator):
    """Test color distribution with 5 segments and 4 colors (edge case)"""
    colors = generator.distribute_colors(5)
    
    # Should return exactly 5 colors
    assert len(colors) == 5, f"Expected 5 colors, got {len(colors)}"
    
    # All colors should be from the available color palette
    for color in colors:
        assert color in generator.colors, f"Color {color} not in palette"
    
    # No adjacent segments should have the same color
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, msg
    
    # Print distribution for debugging
    print(f"\n5 segments distribution: {colors}")


def test_six_segments_four_colors(generator):
    """Test color distribution with 6 segments and 4 colors"""
    colors = generator.distribute_colors(6)
    
    assert len(colors) == 6
    
    for color in colors:
        assert color in generator.colors
    
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, msg
    
    print(f"\n6 segments distribution: {colors}")


def test_eight_segments_four_colors(generator):
    """Test color distribution with 8 segments and 4 colors"""
    colors = generator.distribute_colors(8)
    
    assert len(colors) == 8
    
    for color in colors:
        assert color in generator.colors
    
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, msg
    
    print(f"\n8 segments distribution: {colors}")


def test_four_segments_four_colors(generator):
    """Test color distribution when segments equal colors"""
    colors = generator.distribute_colors(4)
    
    assert len(colors) == 4
    
    # When segments equal colors, each should be unique
    assert len(set(colors)) == 4, "All colors should be different"
    
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, msg


def test_three_segments_four_colors(generator):
    """Test color distribution when segments are less than colors"""
    colors = generator.distribute_colors(3)
    
    assert len(colors) == 3
    
    # All should be different since we have more colors than segments
    assert len(set(colors)) == 3, "All colors should be different"
    
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, msg


def test_many_segments(generator):
    """Test color distribution with many segments"""
    for num_segments in [10, 20, 50, 100]:
        colors = generator.distribute_colors(num_segments)
        
        assert len(colors) == num_segments
        
        for color in colors:
            assert color in generator.colors
        
        is_valid, msg = check_no_adjacent_duplicates(colors)
        assert is_valid, f"Failed for {num_segments} segments: {msg}"


def test_color_usage_balance(generator):
    """Test that colors are distributed relatively evenly"""
    num_segments = 12  # 3 times the number of colors
    colors = generator.distribute_colors(num_segments)
    
    # Count usage of each color
    from collections import Counter
    color_counts = Counter(colors)
    
    # Each color should appear approximately the same number of times
    # With 12 segments and 4 colors, each should appear 3 times
    expected_count = num_segments // len(generator.colors)
    
    for color in generator.colors:
        count = color_counts.get(color, 0)
        # Allow ±1 difference for uneven distribution
        assert abs(count - expected_count) <= 1, \
            f"Color {color} appears {count} times, expected ~{expected_count}"


def test_alice_eve_case(generator):
    """Test the specific case mentioned: Alice, Bob, Charlie, Diana, Eve"""
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    colors = generator.distribute_colors(len(names))
    
    # Create a mapping for better readability
    color_names = {
        '#eeb312': 'Yellow',
        '#d61126': 'Red',
        '#346ae9': 'Blue',
        '#019b26': 'Green'
    }
    
    distribution = {name: color_names[color] for name, color in zip(names, colors)}
    
    print(f"\nAlice-Eve distribution:")
    for name, color_name in distribution.items():
        print(f"  {name}: {color_name}")
    
    # Alice and Eve should have different colors
    assert colors[0] != colors[4], \
        f"Alice and Eve both have {colors[0]} - they are adjacent!"
    
    # Check all adjacent pairs
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, msg


@pytest.mark.parametrize("num_segments", [5, 6, 7, 8, 9, 10, 11, 12])
def test_various_segment_counts(generator, num_segments):
    """Parametrized test for various segment counts"""
    colors = generator.distribute_colors(num_segments)
    
    assert len(colors) == num_segments
    is_valid, msg = check_no_adjacent_duplicates(colors)
    assert is_valid, f"Failed for {num_segments} segments: {msg}"
