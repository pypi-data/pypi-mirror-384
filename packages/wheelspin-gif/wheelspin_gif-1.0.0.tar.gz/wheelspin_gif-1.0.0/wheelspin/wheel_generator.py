"""
WheelGenerator - Core implementation for spinning wheel generation
"""

from PIL import Image, ImageDraw, ImageFont
import math
import platform
from typing import List, Tuple, Optional


class WheelGenerator:
    """Core wheel generation class"""
    
    def __init__(self, size: int = 500, colors: List[str] = None, font_size: int = 11, animation_speed: float = 1.0):
        self.size = size
        self.colors = colors or ['#eeb312', '#d61126', '#346ae9', '#019b26']
        self.font_size = font_size
        self.animation_speed = animation_speed
        self.transparent_color = (255, 0, 255, 0)
        self.circle_degrees = 360
        self._font_cache = {}  # Cache loaded fonts
    
    def distribute_colors(self, num_segments: int) -> List[str]:
        """
        Basic color distribution - simply cycles through available colors.
        """
        colors = [self.colors[i % len(self.colors)] for i in range(num_segments)]
        if colors[0] == colors[-1] and num_segments > 1:
            # Swap last color with second to last to avoid adjacent duplicates
            colors[-1], colors[-2] = colors[-2], colors[-1]
        return colors

    def truncate_text(self, text: str, max_length: int = 17) -> str:
        """
        Truncate text to maximum length and add ellipsis if needed.
        """
        if len(text) <= max_length:
            return text
        return text[:max_length-3].rstrip() + "..."

    def _load_font(self, size: int = None, debug: bool = False) -> ImageFont.FreeTypeFont:
        """
        Load a font that supports Unicode characters.
        Note: PIL/Pillow has limited emoji support - emoji may render as outlined symbols.
        Tries multiple font options with fallback to default.
        """
        if size is None:
            size = self.font_size
        
        cache_key = size
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # List of fonts to try, in order of preference
        # These fonts have good Unicode support (emoji will render as black/white symbols)
        font_options = [
            # macOS fonts with best Unicode coverage
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # Best Unicode support
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            # Linux fonts (common in Docker/server environments)
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",  # Good Unicode
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      # Has diacritics
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/unifont/unifont.ttf",
            # Docker/Alpine fonts
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            # Windows fonts
            "Arial Unicode MS",
            # Generic fallbacks (try system fonts)
            "Arial",
            "DejaVuSans", 
            "Helvetica",
            "Liberation Sans",
            "Noto Sans"
        ]
        
        font = None
        font_used = "default"
        
        for font_name in font_options:
            try:
                font = ImageFont.truetype(font_name, size)
                font_used = font_name
                if debug:
                    print(f"✅ Loaded font: {font_name}")
                break
            except (IOError, OSError):
                if debug:
                    print(f"❌ Font not found: {font_name}")
                continue
        
        # Ultimate fallback to PIL default font
        if font is None:
            font = ImageFont.load_default()
            font_used = "PIL default (limited Unicode)"
            if debug:
                print(f"⚠️  Using fallback: {font_used}")
        
        if debug:
            print(f"🎨 Final font: {font_used}")
        
        self._font_cache[cache_key] = font
        return font
    
    def calculate_dynamic_font_size(self, radius: int, angle_per_segment: float, 
                                   position_name: str, num_segments: int) -> int:
        """Calculate dynamic font size based on available space and positioning"""
        # Base font size from initialization
        base_size = self.font_size
        
        # Scale factor based on wheel size
        size_factor = radius / 200.0  # Scale relative to radius 200
        
        # Position factor: inner has more radial space, can use larger text
        if position_name == 'inner':
            position_factor = 1.8  # 80% larger for inner positioning
        else:
            position_factor = 1.2  # 20% larger for outer positioning
        
        # Segment factor: fewer segments = more angular space = larger text
        if num_segments <= 4:
            segment_factor = 1.4
        elif num_segments <= 8:
            segment_factor = 1.2
        elif num_segments <= 16:
            segment_factor = 1.0
        else:
            segment_factor = 0.9
        
        # Calculate final font size
        dynamic_size = int(base_size * size_factor * position_factor * segment_factor)
        
        # Ensure reasonable bounds
        return max(8, min(dynamic_size, 28))
    
    def get_text_dimensions(self, text: str, font_size: int = None) -> dict:
        """Get the dimensions of text when rendered"""
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Use provided font size or default
        size_to_use = font_size if font_size is not None else self.font_size
        font = self._load_font(size_to_use)
        
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        return {
            'width': width,
            'height': height,
            'font': font
        }
    
    def calculate_segment_space(self, radius: int, angle_per_segment: float, text_radius_ratio: float = 0.65) -> dict:
        """Calculate available space for text in a wheel segment"""
        text_radius = radius * text_radius_ratio
        angle_rad = math.radians(angle_per_segment)
        arc_length = text_radius * angle_rad
        radial_space = radius * 0.3
        
        return {
            'arc_length': arc_length,
            'radial_space': radial_space,
            'text_radius': text_radius,
            'angle_degrees': angle_per_segment
        }
    
    def calculate_consistent_text_position(self, radius: int, angle_per_segment: float, labels: List[str]) -> dict:
        """Calculate consistent text position for all labels with dynamic font sizing"""
        needs_outer = False
        num_segments = len(labels)
        
        # Try inner positioning first with dynamic font size
        inner_font_size = self.calculate_dynamic_font_size(radius, angle_per_segment, 'inner', num_segments)
        
        for label in labels:
            # Use truncated text for space calculations
            display_label = self.truncate_text(label, 17)
            text_dims = self.get_text_dimensions(display_label, inner_font_size)
            inner_space = self.calculate_segment_space(radius, angle_per_segment, 0.65)
            
            text_fits_inner = (text_dims['width'] <= inner_space['arc_length'] * 0.8 and
                              text_dims['height'] <= inner_space['radial_space'])
            
            if not text_fits_inner:
                needs_outer = True
                break
        
        position_ratio = 0.85 if needs_outer else 0.65
        position_name = 'outer' if needs_outer else 'inner'
        
        # Calculate final font size for chosen position
        final_font_size = self.calculate_dynamic_font_size(radius, angle_per_segment, position_name, num_segments)
        
        space = self.calculate_segment_space(radius, angle_per_segment, position_ratio)
        
        return {
            'text_radius_ratio': position_ratio,
            'text_radius': space['text_radius'],
            'position': position_name,
            'font_size': final_font_size,
            'consistent': True
        }
    
    def draw_segment_label(self, draw, center: int, radius: int, angle: float, label: str, 
                          angle_per_segment: float, consistent_position: dict):
        """Draw a text label on a wheel segment using calculated position (inner/outer)"""
        angle_rad = math.radians(angle)
        
        # Truncate text to 17 characters max with ellipsis
        display_label = self.truncate_text(label, 17)
        
        # Use dynamic font size from consistent position calculation
        dynamic_font_size = consistent_position['font_size']
        text_dims = self.get_text_dimensions(display_label, dynamic_font_size)
        font = text_dims['font']
        text_width = text_dims['width']
        
        # Calculate positioning so text ends at wheel boundary (with margin)
        wheel_edge_radius = radius * 0.95  # 95% of wheel radius for small margin
        
        # Estimate how much the text extends radially outward from its center
        # For horizontal text, half the text width extends in each direction
        text_radial_extent = text_width * 0.5
        
        # Position text center so its outer edge aligns with wheel boundary
        text_radius = wheel_edge_radius - text_radial_extent
        
        # Ensure text doesn't go too close to center (minimum radius)
        min_radius = radius * 0.3
        text_radius = max(text_radius, min_radius)
        
        text_x = center + text_radius * math.cos(angle_rad)
        text_y = center + text_radius * math.sin(angle_rad)
        
        # Create temporary image for rotated text with adequate size
        temp_size = max(300, int(text_width * 1.5), 100)
        temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Draw text at center of temp image
        temp_center = temp_size // 2
        temp_draw.text((temp_center, temp_center), display_label, fill='black', font=font, anchor='mm')
        
        rotation_angle = -angle
        rotated_text = temp_img.rotate(rotation_angle, expand=True)
        
        paste_x = int(text_x - rotated_text.width / 2)
        paste_y = int(text_y - rotated_text.height / 2)
        
        draw._image.paste(rotated_text, (paste_x, paste_y), rotated_text)
    
    def draw_triangle_pointer(self, draw, center: int, radius: int):
        """Draw a triangle pointer at the 3 o'clock position"""
        leftest_point = center + radius * 0.95
        rightest_point = self.size * 0.99
        triangle_y = center
        size = self.size - leftest_point
        
        triangle_points = [
            (leftest_point, triangle_y),
            (rightest_point, triangle_y - size / 2),
            (rightest_point, triangle_y + size / 2)
        ]
        
        draw.polygon(triangle_points, fill='white', outline='black', width=1)
    
    def create_wheel_frame(self, segments: int, rotation_angle: float, labels: List[str]) -> Image.Image:
        """Create a single frame of the wheel"""
        img = Image.new('RGBA', (self.size, self.size), self.transparent_color)
        draw = ImageDraw.Draw(img)
        
        center = self.size // 2
        radius = self.size // 2 - 20
        angle_per_segment = self.circle_degrees / segments
        
        consistent_position = self.calculate_consistent_text_position(radius, angle_per_segment, labels)
        
        # Get intelligent color distribution
        segment_colors = self.distribute_colors(segments)
        
        for i in range(segments):
            start_angle = rotation_angle + (i * angle_per_segment)
            end_angle = start_angle + angle_per_segment
            
            # Draw pie slice with intelligently distributed color
            draw.pieslice(
                [center - radius, center - radius, center + radius, center + radius],
                start_angle, end_angle,
                fill=segment_colors[i]
            )
            
            # Add text label
            if i < len(labels):
                mid_angle = start_angle + (angle_per_segment / 2)
                self.draw_segment_label(draw, center, radius, mid_angle, labels[i], 
                                      angle_per_segment, consistent_position)
        
        # Draw center circle
        draw.ellipse([center-radius/10, center-radius/10, center+radius/10, center+radius/10], 
                     fill='white')
        
        # Draw triangle pointer
        self.draw_triangle_pointer(draw, center, radius)
        
        return img
    
    def calculate_frames(self, segments: int) -> int:
        """Calculate number of animation frames based on segment count"""
        base_frames = 60
        base_segments = 8
        frame_multiplier = max(1.0, segments / base_segments * 0.27)
        return int(base_frames * frame_multiplier * self.animation_speed)
    
    def create_gif(self, labels: List[str], start_rotation: float, output_file: str) -> int:
        """Create the animated GIF"""
        segments = len(labels)
        num_frames = self.calculate_frames(segments)
        frames = []
        
        print(f"Generating {num_frames} frames for {segments} segments...")
        
        for i in range(num_frames):
            progress = i / num_frames
            eased_progress = 1 - (1 - progress) ** 3  # Cubic easing
            rotation = start_rotation + (eased_progress * 2 * self.circle_degrees)
            
            frame = self.create_wheel_frame(segments, rotation, labels)
            frames.append(frame)
        
        # Save animated GIF
        frames[0].save(
            output_file,
            format='GIF',
            append_images=frames[1:],
            save_all=True,
            duration=50,
            transparency=0,
            disposal=2
        )
        
        return num_frames
    
    def calculate_winner(self, start_rotation: float, segments: List[str]) -> Tuple[int, str]:
        """Calculate which segment wins"""
        angle_per_segment = self.circle_degrees / len(segments)
        relative_angle = (0 - start_rotation) % self.circle_degrees  # Pointer at 0 degrees
        segment_index = int(relative_angle / angle_per_segment) % len(segments)
        
        return segment_index, segments[segment_index]