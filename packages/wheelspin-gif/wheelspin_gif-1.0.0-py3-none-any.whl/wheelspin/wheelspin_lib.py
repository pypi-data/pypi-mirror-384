"""
WheelSpin Library - Create animated spinning wheel GIFs

A simple Python library for generating spinning wheel animations for games,
contests, decision-making, and more!

Example usage:
    from wheelspin import create_spinning_wheel
    
    names = ["Alice", "Bob", "Charlie", "Diana"]
    winner = create_spinning_wheel(names, "my_wheel.gif")
    print(f"The winner is: {winner}!")
"""

from .wheel_generator import WheelGenerator
import random
from typing import List, Tuple, Optional


def create_spinning_wheel(
    segments: List[str], 
    output_file: str = 'wheel.gif', 
    size: int = 500,
    colors: Optional[List[str]] = None
) -> str:
    """
    Create an animated spinning wheel GIF and return the winning segment.
    
    Args:
        segments: List of segment names/labels (e.g., ["Alice", "Bob", "Charlie"])
        output_file: Path where to save the GIF (default: 'wheel.gif')
        size: Image size in pixels (default: 500)
        colors: List of colors for segments (optional, uses default colors if None)
    
    Returns:
        str: The name of the winning segment
        
    Example:
        >>> winner = create_spinning_wheel(['Pizza', 'Burgers', 'Tacos'], 'dinner.gif')
        >>> print(f"Tonight we're having: {winner}!")
    """
    if not segments:
        raise ValueError("Segments list cannot be empty")
    
    if len(segments) > 100:
        print("Warning: Many segments may result in small, hard-to-read text")
    
    # Generate random starting rotation
    start_rotation = random.uniform(0, 360)
    
    # Create the wheel generator
    generator = WheelGenerator(
        size=size, 
        colors=colors or ['#eeb312', '#d61126', '#346ae9', '#019b26']
    )
    
    # Generate the spinning wheel GIF
    frames_count = generator.create_gif(segments, start_rotation, output_file)
    
    # Calculate and return the winner
    winner_index, winner_name = generator.calculate_winner(start_rotation, segments)
    
    print(f"✅ Wheel created: {output_file}")
    print(f"🎯 Winner: {winner_name} (segment {winner_index + 1}/{len(segments)})")
    print(f"📊 Animation: {frames_count} frames")
    
    return winner_name


def create_spinning_wheel_advanced(
    segments: List[str],
    output_file: str = 'wheel.gif',
    size: int = 500,
    start_rotation: Optional[float] = None,
    colors: Optional[List[str]] = None,
    font_size: int = 11,
    animation_speed: float = 1.0
) -> Tuple[str, dict]:
    """
    Create an animated spinning wheel GIF with advanced customization options.
    
    Args:
        segments: List of segment names/labels
        output_file: Path where to save the GIF
        size: Image size in pixels (default: 500)
        start_rotation: Starting rotation angle in degrees (random if None)
        colors: List of hex colors for segments (cycles if fewer than segments)
        font_size: Font size for text labels (default: 11)
        animation_speed: Speed multiplier (1.0 = normal, 2.0 = twice as fast)
    
    Returns:
        Tuple[str, dict]: Winner name and detailed information dictionary
        
    Example:
        >>> winner, info = create_spinning_wheel_advanced(
        ...     ['Option A', 'Option B', 'Option C'], 
        ...     'decision.gif',
        ...     size=600,
        ...     colors=['#ff0000', '#00ff00', '#0000ff'],
        ...     animation_speed=1.5
        ... )
        >>> print(f"Winner: {winner}")
        >>> print(f"Started at: {info['start_rotation']:.1f}°")
    """
    if not segments:
        raise ValueError("Segments list cannot be empty")
    
    if start_rotation is None:
        start_rotation = random.uniform(0, 360)
    
    if colors is None:
        colors = ['#eeb312', '#d61126', '#346ae9', '#019b26', '#9b59b6', '#e67e22']
    
    # Create the wheel generator with custom settings
    generator = WheelGenerator(
        size=size,
        colors=colors,
        font_size=font_size,
        animation_speed=animation_speed
    )
    
    # Generate the spinning wheel GIF
    frames_count = generator.create_gif(segments, start_rotation, output_file)
    
    # Calculate winner and detailed info
    winner_index, winner_name = generator.calculate_winner(start_rotation, segments)
    
    info = {
        'winner_index': winner_index,
        'winner_name': winner_name,
        'start_rotation': start_rotation,
        'total_segments': len(segments),
        'frames_generated': frames_count,
        'output_file': output_file,
        'size': size,
        'animation_speed': animation_speed,
        'colors_used': colors[:len(segments)]
    }
    
    print(f"✅ Advanced wheel created: {output_file}")
    print(f"🎯 Winner: {winner_name} (segment {winner_index + 1}/{len(segments)})")
    print(f"📊 Animation: {frames_count} frames at {animation_speed}x speed")
    print(f"🎨 Size: {size}x{size}px")
    
    return winner_name, info


def quick_spin(names: List[str], filename: str = 'wheel.gif') -> str:
    """
    Quick spin with minimal configuration.
    
    Args:
        names: List of names/options to choose from
        filename: Output filename (default: 'wheel.gif')
    
    Returns:
        str: The winning name
        
    Example:
        >>> winner = quick_spin(['heads', 'tails'])
        >>> print(f"Coin flip result: {winner}")
    """
    return create_spinning_wheel(names, filename)


def decision_wheel(options: List[str], question: str = "What should I choose?") -> str:
    """
    Create a decision-making wheel.
    
    Args:
        options: List of options to choose from
        question: Question being asked (for display purposes)
    
    Returns:
        str: The chosen option
        
    Example:
        >>> choice = decision_wheel(['Study', 'Netflix', 'Exercise'], "What should I do tonight?")
        >>> print(f"Decision: {choice}")
    """
    print(f"🤔 {question}")
    print(f"📝 Options: {', '.join(options)}")
    
    winner = create_spinning_wheel(options, 'decision_wheel.gif')
    
    print(f"🎲 The wheel has decided: {winner}!")
    return winner


# Library metadata
__version__ = "1.0.0"
__author__ = "WheelSpin Library"
__description__ = "Create animated spinning wheel GIFs for games and decision-making"

# Export main functions
__all__ = [
    'create_spinning_wheel',
    'create_spinning_wheel_advanced', 
    'quick_spin',
    'decision_wheel'
]