# Copy Object Utility

This utility provides functions to copy PyVisual UI objects with the same parameters, allowing you to duplicate objects and then modify them as needed.

## Functions

### `copy_object(original_object, container=None, **overrides)`

Creates a copy of a UI object with the same parameters.

**Parameters:**
- `original_object`: The original UI object to copy
- `container`: The container for the new object (if None, uses the same container as original)
- `**overrides`: Any parameters to override in the new object

**Returns:** A new instance of the same class with the same parameters

### `copy_and_offset(original_object, x_offset=0, y_offset=0, container=None, **overrides)`

Convenience function to copy an object and offset its position.

**Parameters:**
- `original_object`: The original UI object to copy
- `x_offset`: Horizontal offset for the new object
- `y_offset`: Vertical offset for the new object
- `container`: The container for the new object (if None, uses the same container as original)
- `**overrides`: Any other parameters to override

**Returns:** A new instance with offset position

## Usage Examples

### Basic Button Copying

```python
from pyvisual.ui.inputs.pv_button import PvButton
from pyvisual.utils.copy_object import copy_object, copy_and_offset

# Create original button
button1 = PvButton(container, x=100, y=100, text="Original", idle_color=(56, 182, 255, 1))

# Method 1: Copy with overrides
button2 = copy_object(button1, x=250, text="Copied", idle_color=(255, 100, 100, 1))

# Method 2: Copy and then use setters
button3 = copy_object(button1)
button3.x = button1.x - 100  # Move 100px to the left
button3.text = "Modified"
button3.idle_color = (100, 255, 100, 1)

# Method 3: Copy with offset
button4 = copy_and_offset(button1, x_offset=-100, y_offset=50)
```

### Circle Copying

```python
from pyvisual.ui.shapes.pv_circle import PvCircle

# Create original circle
circle1 = PvCircle(container, radius=30, x=100, y=200, idle_color=(255, 200, 0, 1))

# Copy with different position and size
circle2 = copy_object(circle1, x=200, radius=40, idle_color=(0, 255, 200, 1))

# Copy with offset
circle3 = copy_and_offset(circle1, x_offset=150, y_offset=-50)
```

### Text Copying

```python
from pyvisual.ui.outputs.pv_text import PvText

# Create original text
text1 = PvText(container, text="Hello", x=50, y=300, font_size=16, bold=True)

# Copy with modifications
text2 = copy_object(text1, x=200, text="World", italic=True, font_color=(255, 200, 100, 1))

# Copy and modify with setters
text3 = copy_and_offset(text1, y_offset=40)
text3.text = "Modified Text"
text3.underline = True
```

## Supported UI Classes

The copy functions work with all PyVisual UI classes including:

### Inputs
- `PvButton`
- `PvCheckbox`
- `PvTextInput`
- `PvSlider`
- `PvFileDialog`

### Outputs
- `PvText`
- `PvImage`
- `PvIcon`
- `PvWebcam`
- `PvOpencvImage`
- `PvOpencvVideo`

### Shapes
- `PvCircle`
- `PvRectangle`
- `PvLine`

## Key Features

1. **Complete Parameter Copying**: All initialization parameters are copied from the original object
2. **Independent Objects**: Copied objects are completely independent - modifying one doesn't affect others
3. **Flexible Overrides**: You can override any parameter during copying
4. **Setter Support**: After copying, you can use all the property setters to modify the object
5. **Container Flexibility**: You can copy objects to different containers
6. **Deep Copying**: Mutable parameters (lists, dicts) are deep copied to avoid shared references

## Import Options

```python
# Direct import
from pyvisual.utils.copy_object import copy_object, copy_and_offset

# Or from utils package
from pyvisual.utils import copy_object, copy_and_offset
```

## Example Application

See `pyvisual/examples/copy_objects_example.py` for a complete working example that demonstrates copying various UI elements. 