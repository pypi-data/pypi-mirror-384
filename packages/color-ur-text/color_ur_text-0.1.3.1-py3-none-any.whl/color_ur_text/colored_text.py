"""
# colored_text.py
# Original Author: Basit Ahmad Ganie
# email: basitahmed1412@gmail.com
# Enhanced version with improved table and progress bar functionality
# Complete version with all original features + enhancements
"""

import time
import sys
import random
import math
from typing import List, Dict, Union, Tuple, Optional, Callable

class ColoredText:
    # Foreground Colors
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    
    # Bright Foreground Colors
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97
    
    # Background Colors
    BG_BLACK = 40
    BG_RED = 41
    BG_GREEN = 42
    BG_YELLOW = 43
    BG_BLUE = 44
    BG_MAGENTA = 45
    BG_CYAN = 46
    BG_WHITE = 47
    
    # Bright Background Colors
    BG_BRIGHT_BLACK = 100
    BG_BRIGHT_RED = 101
    BG_BRIGHT_GREEN = 102
    BG_BRIGHT_YELLOW = 103
    BG_BRIGHT_BLUE = 104
    BG_BRIGHT_MAGENTA = 105
    BG_BRIGHT_CYAN = 106
    BG_BRIGHT_WHITE = 107
    
    # Styles
    BOLD = 1
    DIM = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5
    RAPID_BLINK = 6
    REVERSE = 7
    HIDDEN = 8
    STRIKETHROUGH = 9
    RESET = 0
    
    # Common color presets (RGB values)
    COLOR_PRESETS = {
        "forest_green": (34, 139, 34),
        "sky_blue": (135, 206, 235),
        "coral": (255, 127, 80),
        "gold": (255, 215, 0),
        "lavender": (230, 230, 250),
        "tomato": (255, 99, 71),
        "teal": (0, 128, 128),
        "salmon": (250, 128, 114),
        "violet": (238, 130, 238),
        "khaki": (240, 230, 140),
        "turquoise": (64, 224, 208),
        "firebrick": (178, 34, 34),
        "navy": (0, 0, 128),
        "steel_blue": (70, 130, 180),
        "olive": (128, 128, 0),
        "spring_green": (0, 255, 127),
        "crimson": (220, 20, 60),
        "chocolate": (210, 105, 30),
        "midnight_blue": (25, 25, 112),
        "orchid": (218, 112, 214),
    }
    
    # Terminal theme presets
    THEME_PRESETS = {
        "matrix": {"fg": (0, 255, 0), "bg": (0, 0, 0), "style": BOLD},
        "ocean": {"fg": (0, 191, 255), "bg": (0, 0, 139), "style": None},
        "sunset": {"fg": (255, 165, 0), "bg": (178, 34, 34), "style": None},
        "forest": {"fg": (34, 139, 34), "bg": (0, 100, 0), "style": None},
        "neon": {"fg": (255, 0, 255), "bg": (0, 0, 0), "style": BOLD},
        "pastel": {"fg": (255, 192, 203), "bg": (230, 230, 250), "style": None},
        "retro": {"fg": (255, 165, 0), "bg": (0, 0, 0), "style": BOLD},
        "cyberpunk": {"fg": (0, 255, 255), "bg": (139, 0, 139), "style": BOLD},
        "desert": {"fg": (210, 180, 140), "bg": (244, 164, 96), "style": None},
        "dracula": {"fg": (248, 248, 242), "bg": (40, 42, 54), "style": None},
    }
    
    @staticmethod
    def colorize(text, fg_color=None, bg_color=None, style=None):
        """Apply color and style to text."""
        codes = []
        if style is not None:
            codes.append(str(style))
        if fg_color is not None:
            codes.append(str(fg_color))
        if bg_color is not None:
            codes.append(str(bg_color))
        
        color_prefix = f"\033[{';'.join(codes)}m" if codes else ''
        color_suffix = "\033[0m"
        return f"{color_prefix}{text}{color_suffix}"
    
    @staticmethod
    def print_colored(text, fg_color=None, bg_color=None, style=None):
        """Print text with color and style."""
        print(ColoredText.colorize(text, fg_color, bg_color, style))
    
    @staticmethod
    def color256(text, color_code, bg_code=None, style=None):
        """Apply a color from the 256-color palette."""
        fg_code = f"38;5;{color_code}"
        bg_code = f"48;5;{bg_code}" if bg_code is not None else ''
        codes = [fg_code]
        if bg_code:
            codes.append(bg_code)
        if style:
            codes.insert(0, str(style))
        
        color_prefix = f"\033[{';'.join(codes)}m"
        color_suffix = "\033[0m"
        return f"{color_prefix}{text}{color_suffix}"
    
    @staticmethod
    def rgb(text, r, g, b, bg=False, style=None):
        """Apply an RGB color to text."""
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        fg_code = f"38;2;{r};{g};{b}"
        bg_code = f"48;2;{r};{g};{b}" if bg else ''
        codes = [fg_code]
        if bg_code:
            codes.append(bg_code)
        if style:
            codes.insert(0, str(style))
        
        color_prefix = f"\033[{';'.join(codes)}m"
        color_suffix = "\033[0m"
        return f"{color_prefix}{text}{color_suffix}"
    
    @staticmethod
    def rgb_bg(text, r, g, b, fg_r=None, fg_g=None, fg_b=None, style=None):
        """Apply an RGB background color with optional RGB foreground."""
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        codes = []
        if style is not None:
            codes.append(str(style))
        
        if fg_r is not None and fg_g is not None and fg_b is not None:
            fg_r = max(0, min(255, fg_r))
            fg_g = max(0, min(255, fg_g))
            fg_b = max(0, min(255, fg_b))
            codes.append(f"38;2;{fg_r};{fg_g};{fg_b}")
        
        codes.append(f"48;2;{r};{g};{b}")
        
        color_prefix = f"\033[{';'.join(codes)}m"
        color_suffix = "\033[0m"
        return f"{color_prefix}{text}{color_suffix}"
    
    @staticmethod
    def hex_color(text, hex_code, bg=False, style=None):
        """Apply a color using a hex color code (e.g., #FF5733)."""
        hex_code = hex_code.lstrip('#')
        if len(hex_code) == 3:
            hex_code = ''.join([c * 2 for c in hex_code])
        
        if len(hex_code) != 6:
            raise ValueError("Invalid hex code. Expected format: #RRGGBB")
        
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        
        return ColoredText.rgb(text, r, g, b, bg=bg, style=style)
    
    @staticmethod
    def hex_bg(text, hex_code, fg_hex=None, style=None):
        """Apply a hex background color with optional hex foreground."""
        hex_code = hex_code.lstrip('#')
        if len(hex_code) == 3:
            hex_code = ''.join([c * 2 for c in hex_code])
        
        if len(hex_code) != 6:
            raise ValueError("Invalid hex code for background. Expected format: #RRGGBB")
        
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        
        fg_r, fg_g, fg_b = None, None, None
        if fg_hex:
            fg_hex = fg_hex.lstrip('#')
            if len(fg_hex) == 3:
                fg_hex = ''.join([c * 2 for c in fg_hex])
            
            if len(fg_hex) != 6:
                raise ValueError("Invalid hex code for foreground. Expected format: #RRGGBB")
            
            fg_r = int(fg_hex[0:2], 16)
            fg_g = int(fg_hex[2:4], 16)
            fg_b = int(fg_hex[4:6], 16)
        
        return ColoredText.rgb_bg(text, r, g, b, fg_r, fg_g, fg_b, style)
    
    @staticmethod
    def hsl_to_rgb(h, s, l):
        """Convert HSL to RGB color values."""
        h = h % 360
        s = max(0, min(1, s))
        l = max(0, min(1, l))
        
        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                t %= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h / 360 + 1/3)
            g = hue_to_rgb(p, q, h / 360)
            b = hue_to_rgb(p, q, h / 360 - 1/3)
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def hsl(text, h, s, l, bg=False, style=None):
        """Apply an HSL color to text."""
        r, g, b = ColoredText.hsl_to_rgb(h, s, l)
        return ColoredText.rgb(text, r, g, b, bg=bg, style=style)
    
    @staticmethod
    def hsl_bg(text, h, s, l, fg_h=None, fg_s=None, fg_l=None, style=None):
        """Apply an HSL background color with optional HSL foreground."""
        r, g, b = ColoredText.hsl_to_rgb(h, s, l)
        
        fg_r, fg_g, fg_b = None, None, None
        if fg_h is not None and fg_s is not None and fg_l is not None:
            fg_r, fg_g, fg_b = ColoredText.hsl_to_rgb(fg_h, fg_s, fg_l)
        
        return ColoredText.rgb_bg(text, r, g, b, fg_r, fg_g, fg_b, style)
    
    @staticmethod
    def from_preset(text, preset_name, style=None):
        """Use a predefined color preset."""
        if preset_name not in ColoredText.COLOR_PRESETS:
            available = ', '.join(ColoredText.COLOR_PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available}")
        
        r, g, b = ColoredText.COLOR_PRESETS[preset_name]
        return ColoredText.rgb(text, r, g, b, style=style)
    
    @staticmethod
    def from_theme(text, theme_name):
        """Apply a predefined theme (foreground and background colors)."""
        if theme_name not in ColoredText.THEME_PRESETS:
            available = ', '.join(ColoredText.THEME_PRESETS.keys())
            raise ValueError(f"Unknown theme '{theme_name}'. Available themes: {available}")
        
        theme = ColoredText.THEME_PRESETS[theme_name]
        fg_r, fg_g, fg_b = theme["fg"]
        bg_r, bg_g, bg_b = theme["bg"]
        style = theme["style"]
        
        return ColoredText.rgb_bg(text, bg_r, bg_g, bg_b, fg_r, fg_g, fg_b, style)
    
    @staticmethod
    def random_color(text, style=None):
        """Apply a random color to text."""
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return ColoredText.rgb(text, r, g, b, style=style)
    
    @staticmethod
    def random_bg(text, style=None):
        """Apply a random background color to text with auto-contrasting foreground."""
        bg_r = random.randint(0, 255)
        bg_g = random.randint(0, 255)
        bg_b = random.randint(0, 255)
        
        luminance = (0.299 * bg_r + 0.587 * bg_g + 0.114 * bg_b) / 255
        fg_r, fg_g, fg_b = (0, 0, 0) if luminance > 0.5 else (255, 255, 255)
        
        return ColoredText.rgb_bg(text, bg_r, bg_g, bg_b, fg_r, fg_g, fg_b, style)
    
    @staticmethod
    def gradient_text(text, start_rgb, end_rgb, style=None):
        """Apply a horizontal gradient to text."""
        start_r, start_g, start_b = start_rgb
        end_r, end_g, end_b = end_rgb
        
        result = ""
        for i, char in enumerate(text):
            if char.isspace():
                result += char
                continue
            
            ratio = i / max(1, len(text) - 1)
            r = int(start_r + (end_r - start_r) * ratio)
            g = int(start_g + (end_g - start_g) * ratio)
            b = int(start_b + (end_b - start_b) * ratio)
            
            result += ColoredText.rgb(char, r, g, b, style=style)
        
        return result
    
    @staticmethod
    def rainbow(text, style=None):
        """Apply rainbow colors to text."""
        colors = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (143, 0, 255)
        ]
        
        result = ""
        for i, char in enumerate(text):
            if char.isspace():
                result += char
                continue
            
            color_idx = i % len(colors)
            r, g, b = colors[color_idx]
            result += ColoredText.rgb(char, r, g, b, style=style)
        
        return result
    
    @staticmethod
    def animate_text(text, animation_type='typing', speed=0.05, cycles=1):
        """
        Animate text using various effects.
        
        animation_type options:
        - 'typing': Simulates typing effect
        - 'fade_in': Characters fade in from dim to bright
        - 'blink': Text blinks
        - 'rainbow_wave': Rainbow colors moving through the text
        - 'bounce': Text appears to bounce
        """
        def clear_line():
            sys.stdout.write('\r')
            sys.stdout.write(' ' * (len(text) + 10))
            sys.stdout.write('\r')
            sys.stdout.flush()
        
        if animation_type == 'typing':
            for i in range(len(text) + 1):
                sys.stdout.write('\r' + text[:i])
                sys.stdout.flush()
                time.sleep(speed)
            print()
        
        elif animation_type == 'fade_in':
            for brightness in range(0, 101, 5):
                value = int(brightness * 2.55)
                colored_text = ColoredText.rgb(text, value, value, value)
                sys.stdout.write('\r' + colored_text)
                sys.stdout.flush()
                time.sleep(speed)
            print()
        
        elif animation_type == 'blink':
            for _ in range(cycles):
                sys.stdout.write('\r' + text)
                sys.stdout.flush()
                time.sleep(speed)
                
                clear_line()
                time.sleep(speed)
            
            print(text)
        
        elif animation_type == 'rainbow_wave':
            hue_offset = 0
            for _ in range(cycles * 360):
                result = ""
                for i, char in enumerate(text):
                    if char.isspace():
                        result += char
                        continue
                    
                    hue = (i * 10 + hue_offset) % 360
                    r, g, b = ColoredText.hsl_to_rgb(hue, 1, 0.5)
                    result += ColoredText.rgb(char, r, g, b)
                
                sys.stdout.write('\r' + result)
                sys.stdout.flush()
                time.sleep(speed)
                hue_offset = (hue_offset + 5) % 360
            
            print()
        
        elif animation_type == 'bounce':
            for _ in range(cycles):
                for amplitude in list(range(0, 5)) + list(reversed(range(1, 4))):
                    result = ""
                    for i, char in enumerate(text):
                        if char.isspace():
                            result += char
                            continue
                        
                        char_amplitude = amplitude * math.sin(i / 2)
                        padding = ' ' * int(abs(char_amplitude))
                        
                        if char_amplitude >= 0:
                            result += padding + char
                        else:
                            result += char + padding
                    
                    sys.stdout.write('\r' + result)
                    sys.stdout.flush()
                    time.sleep(speed)
            
            print()
        
        else:
            print(f"Unknown animation type: {animation_type}")
    
    @staticmethod
    def table(data: Union[List[List[str]], List[Dict[str, str]], str], 
              headers: Optional[List[str]] = None,
              padding: int = 1,
              border_style: str = 'single',
              fg_color: Optional[int] = None,
              bg_color: Optional[int] = None,
              style: Optional[int] = None,
              header_color: Optional[Tuple[int, int, int]] = None,
              cell_colors: Optional[List[List[Tuple[int, int, int]]]] = None,
              align: str = 'left'):
        """
        Create a box around text OR formatted table with rows and columns.
        
        Args:
            data: String for simple box, List[List] for table rows, or List[Dict] for keyed data
            headers: Optional list of header names (for table mode)
            padding: Padding around content
            border_style: 'single', 'double', 'rounded', 'bold', 'dashed'
            fg_color/bg_color/style: For simple box mode
            header_color: RGB tuple for header color (table mode)
            cell_colors: 2D list of RGB tuples for each cell (table mode)
            align: 'left', 'right', or 'center' (table mode)
        """
        # Simple box mode (original functionality)
        if isinstance(data, str):
            lines = data.split('\n')
            width = max(len(line) for line in lines)
            
            if border_style == 'single':
                tl, t, tr = '┌', '─', '┐'
                l, r = '│', '│'
                bl, b, br = '└', '─', '┘'
            elif border_style == 'double':
                tl, t, tr = '╔', '═', '╗'
                l, r = '║', '║'
                bl, b, br = '╚', '═', '╝'
            elif border_style == 'rounded':
                tl, t, tr = '╭', '─', '╮'
                l, r = '│', '│'
                bl, b, br = '╰', '─', '╯'
            elif border_style == 'bold':
                tl, t, tr = '┏', '━', '┓'
                l, r = '┃', '┃'
                bl, b, br = '┗', '━', '┛'
            elif border_style == 'dashed':
                tl, t, tr = '┌', '┄', '┐'
                l, r = '┆', '┆'
                bl, b, br = '└', '┄', '┘'
            else:
                tl, t, tr = '+', '-', '+'
                l, r = '|', '|'
                bl, b, br = '+', '-', '+'
            
            horizontal_border = tl + t * (width + padding * 2) + tr
            bottom_border = bl + b * (width + padding * 2) + br
            padding_line = l + ' ' * (width + padding * 2) + r
            
            result = [horizontal_border]
            for _ in range(padding):
                result.append(padding_line)
            
            for line in lines:
                padded_line = l + ' ' * padding + line.ljust(width) + ' ' * padding + r
                result.append(padded_line)
            
            for _ in range(padding):
                result.append(padding_line)
            
            result.append(bottom_border)
            
            if fg_color is not None or bg_color is not None or style is not None:
                return ColoredText.colorize('\n'.join(result), fg_color, bg_color, style)
            
            return '\n'.join(result)
        
        # Table mode (new functionality)
        if data and isinstance(data[0], dict):
            if not headers:
                headers = list(data[0].keys())
            data = [[str(row.get(h, '')) for h in headers] for row in data]
        else:
            data = [[str(cell) for cell in row] for row in data]
        
        borders = {
            'single': {'tl': '┌', 't': '─', 'tr': '┐', 'l': '│', 'r': '│',
                      'ml': '├', 'm': '─', 'mr': '┤', 'bl': '└', 'b': '─', 'br': '┘', 'c': '┼'},
            'double': {'tl': '╔', 't': '═', 'tr': '╗', 'l': '║', 'r': '║',
                      'ml': '╠', 'm': '═', 'mr': '╣', 'bl': '╚', 'b': '═', 'br': '╝', 'c': '╬'},
            'rounded': {'tl': '╭', 't': '─', 'tr': '╮', 'l': '│', 'r': '│',
                       'ml': '├', 'm': '─', 'mr': '┤', 'bl': '╰', 'b': '─', 'br': '╯', 'c': '┼'},
            'bold': {'tl': '┏', 't': '━', 'tr': '┓', 'l': '┃', 'r': '┃',
                    'ml': '┣', 'm': '━', 'mr': '┫', 'bl': '┗', 'b': '━', 'br': '┛', 'c': '╋'},
            'dashed': {'tl': '┌', 't': '┄', 'tr': '┐', 'l': '┆', 'r': '┆',
                      'ml': '├', 'm': '┄', 'mr': '┤', 'bl': '└', 'b': '┄', 'br': '┘', 'c': '┼'}
        }
        b = borders.get(border_style, borders['single'])
        
        all_rows = [headers] + data if headers else data
        col_widths = [max(len(str(row[i])) for row in all_rows) for i in range(len(all_rows[0]))]
        
        def format_cell(content, width, alignment):
            if alignment == 'right':
                return content.rjust(width)
            elif alignment == 'center':
                return content.center(width)
            else:
                return content.ljust(width)
        
        def create_separator(left, mid, right, fill):
            return left + fill.join([fill * (w + padding * 2) for w in col_widths]) + right
        
        result = []
        result.append(create_separator(b['tl'], b['t'], b['tr'], b['t']))
        
        if headers:
            header_row = b['l']
            for i, (header, width) in enumerate(zip(headers, col_widths)):
                cell = ' ' * padding + format_cell(header, width, align) + ' ' * padding
                if header_color:
                    cell = ColoredText.rgb(cell, *header_color)
                header_row += cell + b['l']
            result.append(header_row)
            result.append(create_separator(b['ml'], b['m'], b['mr'], b['m']))
        
        for row_idx, row in enumerate(data):
            row_str = b['l']
            for col_idx, (cell, width) in enumerate(zip(row, col_widths)):
                cell_content = ' ' * padding + format_cell(str(cell), width, align) + ' ' * padding
                
                if cell_colors and row_idx < len(cell_colors) and col_idx < len(cell_colors[row_idx]):
                    if cell_colors[row_idx][col_idx]:
                        cell_content = ColoredText.rgb(cell_content, *cell_colors[row_idx][col_idx])
                
                row_str += cell_content + b['l']
            result.append(row_str)
        
        result.append(create_separator(b['bl'], b['b'], b['br'], b['b']))
        
        return '\n'.join(result)
    
    @staticmethod
    def progress_bar(progress: float,
                     width: int = 50,
                     fill_char: str = '█',
                     empty_char: str = '░',
                     start_char: str = '|',
                     end_char: str = '|',
                     show_percentage: bool = True,
                     bar_color: Optional[Union[int, Tuple[int, int, int]]] = None,
                     percentage_color: Optional[Union[int, Tuple[int, int, int]]] = None):
        """Create a customizable progress bar."""
        progress = max(0, min(1, progress))
        filled_width = int(width * progress)
        empty_width = width - filled_width
        
        filled_part = fill_char * filled_width
        empty_part = empty_char * empty_width
        
        if bar_color is not None:
            if isinstance(bar_color, tuple) and len(bar_color) == 3:
                filled_part = ColoredText.rgb(filled_part, *bar_color)
            else:
                filled_part = ColoredText.colorize(filled_part, bar_color)
        
        bar = f"{start_char}{filled_part}{empty_part}{end_char}"
        
        if show_percentage:
            percentage = f" {int(progress * 100)}%"
            if percentage_color is not None:
                if isinstance(percentage_color, tuple) and len(percentage_color) == 3:
                    percentage = ColoredText.rgb(percentage, *percentage_color)
                else:
                    percentage = ColoredText.colorize(percentage, percentage_color)
            bar += percentage
        
        return bar
    
    @staticmethod
    def progress_bar_track(func: Callable,
                           total_steps: Optional[int] = None,
                           width: int = 50,
                           desc: str = "",
                           bar_color: Tuple[int, int, int] = (0, 255, 0),
                           show_time: bool = True):
        """
        Track progress of a function execution with a progress bar.
        
        Args:
            func: Function to execute. Should yield progress values (0.0 to 1.0) or items
            total_steps: Total number of steps (if func yields items, not progress)
            width: Width of progress bar
            desc: Description to show
            bar_color: RGB color for the bar
            show_time: Whether to show elapsed time
        """
        start_time = time.time()
        result = None
        
        try:
            gen = func()
            step = 0
            
            for value in gen:
                if isinstance(value, (int, float)) and 0 <= value <= 1:
                    progress = value
                else:
                    step += 1
                    progress = step / total_steps if total_steps else 0
                
                elapsed = time.time() - start_time
                time_str = f" {elapsed:.1f}s" if show_time else ""
                
                bar = ColoredText.progress_bar(
                    progress,
                    width=width,
                    bar_color=bar_color,
                    show_percentage=True
                )
                
                sys.stdout.write(f'\r{desc} {bar}{time_str}')
                sys.stdout.flush()
                
                result = value
            
            print()
            return result
            
        except Exception as e:
            print(f"\nError: {e}")
            raise
    
    @staticmethod
    def multi_color_text(text, color_map=None):
        """
        Apply different colors to different parts of text based on a color map.
        
        Args:
            text: String to color
            color_map: Dictionary mapping substrings to colors (RGB tuples or color constants)
        """
        if color_map is None:
            return text
        
        result = text
        for substring, color in color_map.items():
            if substring in text:
                colored_substring = ''
                if isinstance(color, tuple) and len(color) == 3:
                    colored_substring = ColoredText.rgb(substring, *color)
                else:
                    colored_substring = ColoredText.colorize(substring, color)
                result = result.replace(substring, colored_substring)
        
        return result
    
    @staticmethod
    def highlight_text(text, pattern, fg_color=None, bg_color=None, style=None, case_sensitive=False):
        """
        Highlight occurrences of a pattern within text.
        
        Args:
            text: String to search in
            pattern: String to highlight
            fg_color/bg_color/style: Styling for the highlighted text
            case_sensitive: Whether pattern matching should be case sensitive
        """
        if not pattern or pattern not in text:
            if not case_sensitive and pattern.lower() in text.lower():
                import re
                result = ''
                last_idx = 0
                for match in re.finditer(re.escape(pattern), text, re.IGNORECASE):
                    result += text[last_idx:match.start()]
                    result += ColoredText.colorize(text[match.start():match.end()], fg_color, bg_color, style)
                    last_idx = match.end()
                result += text[last_idx:]
                return result
            else:
                return text
        
        parts = text.split(pattern)
        return pattern.join([parts[0]] + [ColoredText.colorize(pattern, fg_color, bg_color, style) + part for part in parts[1:]])
    
    @staticmethod
    def typewriter_effect(text, speed=0.05, style=None, color=None):
        """
        Display text with a typewriter effect and optional styling.
        
        Args:
            text: String to display
            speed: Delay between characters in seconds
            style: Text style to apply
            color: Text color to apply (RGB tuple or color constant)
        """
        for char in text:
            if color is not None:
                if isinstance(color, tuple) and len(color) == 3:
                    char_display = ColoredText.rgb(char, *color, style=style)
                else:
                    char_display = ColoredText.colorize(char, color, style=style)
            else:
                char_display = char
            
            sys.stdout.write(char_display)
            sys.stdout.flush()
            time.sleep(speed)
        print()
    
    @staticmethod
    def spinner(text: str = "Loading",
                duration: float = 5.0,
                spinner_style: str = 'dots',
                color: Optional[Tuple[int, int, int]] = None):
        """
        Display a spinner animation.
        
        Args:
            text: Text to display next to spinner
            duration: How long to spin (in seconds)
            spinner_style: 'dots', 'line', 'arrow', 'circle', 'box', 'bounce'
            color: RGB color tuple
        """
        spinners = {
            'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
            'line': ['|', '/', '-', '\\'],
            'arrow': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
            'circle': ['◐', '◓', '◑', '◒'],
            'box': ['◰', '◳', '◲', '◱'],
            'bounce': ['⠁', '⠂', '⠄', '⠂'],
        }
        
        frames = spinners.get(spinner_style, spinners['dots'])
        start = time.time()
        idx = 0
        
        try:
            while time.time() - start < duration:
                frame = frames[idx % len(frames)]
                if color:
                    frame = ColoredText.rgb(frame, *color)
                sys.stdout.write(f'\r{frame} {text}')
                sys.stdout.flush()
                time.sleep(0.1)
                idx += 1
        finally:
            sys.stdout.write('\r' + ' ' * (len(text) + 10) + '\r')
            sys.stdout.flush()


# Example usage
if __name__ == '__main__':
    print("\n" + ColoredText.rgb("="*50, 0, 255, 255, style=ColoredText.BOLD))
    print(ColoredText.rgb("  ENHANCED COLORED TEXT LIBRARY DEMO", 0, 255, 255, style=ColoredText.BOLD))
    print(ColoredText.rgb("="*50, 0, 255, 255, style=ColoredText.BOLD))
    
    # Simple box (original functionality)
    print("\n" + ColoredText.rgb("=== Simple Box ===", 255, 215, 0, style=ColoredText.BOLD))
    box = ColoredText.table("Hello World\nThis is a box!", border_style='rounded', padding=1)
    print(box)
    
    # Table with rows and columns
    print("\n" + ColoredText.rgb("=== Data Table ===", 255, 215, 0, style=ColoredText.BOLD))
    data = [
        ["Alice", "25", "Engineer"],
        ["Bob", "30", "Designer"],
        ["Charlie", "28", "Manager"]
    ]
    headers = ["Name", "Age", "Role"]
    
    table = ColoredText.table(
        data,
        headers=headers,
        border_style='double',
        header_color=(0, 255, 255),
        align='center'
    )
    print(table)
    
    # Dict-based table
    print("\n" + ColoredText.rgb("=== Dict-Based Table ===", 255, 215, 0, style=ColoredText.BOLD))
    dict_data = [
        {"Product": "Laptop", "Price": "$999", "Stock": "15"},
        {"Product": "Mouse", "Price": "$25", "Stock": "150"},
        {"Product": "Keyboard", "Price": "$75", "Stock": "80"}
    ]
    dict_table = ColoredText.table(dict_data, border_style='rounded', header_color=(255, 127, 80))
    print(dict_table)
    
    # Progress bar
    print("\n" + ColoredText.rgb("=== Static Progress Bar ===", 255, 215, 0, style=ColoredText.BOLD))
    for i in range(0, 101, 20):
        bar = ColoredText.progress_bar(i/100, bar_color=(0, 255, 0))
        print(f"Progress: {bar}")
    
    # Progress bar tracking
    print("\n" + ColoredText.rgb("=== Progress Bar Tracking ===", 255, 215, 0, style=ColoredText.BOLD))
    def sample_task():
        for i in range(50):
            time.sleep(0.02)
            yield i / 49
    
    ColoredText.progress_bar_track(sample_task, desc="Processing", bar_color=(24, 64, 84))
    
    # Gradient text
    print("\n" + ColoredText.rgb("=== Gradient Text ===", 255, 215, 0, style=ColoredText.BOLD))
    print(ColoredText.gradient_text("Beautiful Gradient from Red to Blue!", (255, 0, 0), (0, 0, 255)))
    
    # Rainbow text
    print("\n" + ColoredText.rgb("=== Rainbow Text ===", 255, 215, 0, style=ColoredText.BOLD))
    print(ColoredText.rainbow("Rainbow Colored Text is Amazing!"))
    
    # Color presets
    print("\n" + ColoredText.rgb("=== Color Presets ===", 255, 215, 0, style=ColoredText.BOLD))
    print(ColoredText.from_preset("Forest Green Text", "forest_green"))
    print(ColoredText.from_preset("Sky Blue Text", "sky_blue"))
    print(ColoredText.from_preset("Coral Text", "coral"))
    
    # Themes
    print("\n" + ColoredText.rgb("=== Themes ===", 255, 215, 0, style=ColoredText.BOLD))
    print(ColoredText.from_theme("Matrix Theme", "matrix"))
    print(ColoredText.from_theme("Cyberpunk Theme", "cyberpunk"))
    print(ColoredText.from_theme("Ocean Theme", "ocean"))
    
    # Multi-color text
    print("\n" + ColoredText.rgb("=== Multi-Color Text ===", 255, 215, 0, style=ColoredText.BOLD))
    text = "Error: Connection failed! Warning: Retrying..."
    colored = ColoredText.multi_color_text(text, {
        "Error": (255, 0, 0),
        "Warning": (255, 255, 0),
        "failed": (255, 0, 0)
    })
    print(colored)
    
    # Highlight text
    print("\n" + ColoredText.rgb("=== Highlight Text ===", 255, 215, 0, style=ColoredText.BOLD))
    text = "The quick brown fox jumps over the lazy dog"
    highlighted = ColoredText.highlight_text(text, "fox", bg_color=ColoredText.BG_YELLOW, fg_color=ColoredText.BLACK, case_sensitive=True)
    print(highlighted)
    
    # Typewriter effect
    print("\n" + ColoredText.rgb("=== Typewriter Effect ===", 255, 215, 0, style=ColoredText.BOLD))
    ColoredText.typewriter_effect("This text appears character by character...", speed=0.05, color=(0, 255, 0))
    
    # Spinner
    print("\n" + ColoredText.rgb("=== Spinner ===", 255, 215, 0, style=ColoredText.BOLD))
    ColoredText.spinner("Loading data", duration=2.0, spinner_style='dots', color=(255, 0, 255))
    print("Done!")
    
    # Hex colors
    print("\n" + ColoredText.rgb("=== Hex Colors ===", 255, 215, 0, style=ColoredText.BOLD))
    print(ColoredText.hex_color("Hex Color #FF5733", "#FF5733"))
    print(ColoredText.hex_bg("Hex Background", "#1E90FF", fg_hex="#FFD700"))
    
    # HSL colors
    print("\n" + ColoredText.rgb("=== HSL Colors ===", 255, 215, 0, style=ColoredText.BOLD))
    print(ColoredText.hsl("HSL Color (Hue: 120)", 120, 1, 0.5))
    
    # Animations (uncomment to see)
    # print("\n" + ColoredText.rgb("=== Typing Animation ===", 255, 215, 0, style=ColoredText.BOLD))
    # ColoredText.animate_text("Hello, World!", animation_type='typing', speed=0.1)
    
    # print("\n" + ColoredText.rgb("=== Rainbow Wave ===", 255, 215, 0, style=ColoredText.BOLD))
    # ColoredText.animate_text("WAVE ANIMATION", animation_type='rainbow_wave', speed=0.03, cycles=1)
    
    print("\n" + ColoredText.rgb("="*50, 0, 255, 255, style=ColoredText.BOLD))
    print(ColoredText.rgb("  DEMO COMPLETE!", 0, 255, 0, style=ColoredText.BOLD))
    print(ColoredText.rgb("="*50, 0, 255, 255, style=ColoredText.BOLD) + "\n")

