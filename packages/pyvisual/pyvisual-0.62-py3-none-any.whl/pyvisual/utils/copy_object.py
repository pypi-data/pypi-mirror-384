import inspect
import copy


def copy_object(original_object, container=None, **overrides):
    """
    Creates a copy of a UI object with the same parameters.
    
    Args:
        original_object: The original UI object to copy
        container: The container for the new object (if None, uses the same container as original)
        **overrides: Any parameters to override in the new object
        
    Returns:
        A new instance of the same class with the same parameters
        
    Example:
        # Create original button
        button1 = PvButton(container, x=100, y=100, text="Original")
        
        # Copy button and move it 100px to the left
        button2 = copy_object(button1, x=button1.x - 100)
        
        # Or copy and then use setters
        button3 = copy_object(button1)
        button3.x = button1.x - 100
        button3.text = "Copied"
    """
    
    # Get the class of the original object
    original_class = original_object.__class__
    
    # Get the constructor signature
    sig = inspect.signature(original_class.__init__)
    
    # Extract current values from the original object
    init_params = {}
    
    # Use the same container if not specified
    if container is None:
        container = original_object.parent()
    
    init_params['container'] = container
    
    # Map common property names to their private attribute names
    property_mappings = {
        'x': '_x',
        'y': '_y', 
        'width': '_width',
        'height': '_height',
        'text': '_text',
        'font': '_font',
        'font_size': '_font_size',
        'font_color': '_font_color',
        'font_color_hover': '_font_color_hover',
        'bold': '_bold',
        'italic': '_italic',
        'underline': '_underline',
        'strikeout': '_strikeout',
        'idle_color': '_idle_color',
        'hover_color': '_hover_color',
        'clicked_color': '_clicked_color',
        'disabled_color': '_disabled_color',
        'border_color': '_border_color',
        'border_color_hover': '_border_color_hover',
        'border_thickness': '_border_thickness',
        'corner_radius': '_corner_radius',
        'border_style': '_border_style',
        'box_shadow': '_box_shadow',
        'box_shadow_hover': '_box_shadow_hover',
        'icon_path': '_icon_path',
        'icon_position': '_icon_position',
        'icon_spacing': '_icon_spacing',
        'icon_scale': '_icon_scale',
        'icon_color': '_icon_color',
        'icon_color_hover': '_icon_color_hover',
        'is_visible': '_is_visible',
        'is_disabled': '_is_disabled',
        'opacity': '_opacity',
        'paddings': '_paddings',
        'on_hover': '_on_hover',
        'on_click': '_on_click',
        'on_release': '_on_release',
        'tag': '_tag',
        'alignment': '_alignment',
        'is_hover_disabled': '_is_hover_disabled',
        'radius': '_radius',
        'text_alignment': '_text_alignment',
        'multiline': '_multiline',
        'line_spacing': '_line_spacing'
    }
    
    # Extract parameters from the constructor signature
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'container']:
            continue
            
        # Try to get the value from the original object
        value = None
        
        # First try the direct private attribute
        private_attr = property_mappings.get(param_name, f'_{param_name}')
        if hasattr(original_object, private_attr):
            value = getattr(original_object, private_attr)
        # Then try the property
        elif hasattr(original_object, param_name):
            try:
                value = getattr(original_object, param_name)
            except:
                # If property getter fails, use default
                value = param.default if param.default != inspect.Parameter.empty else None
        # Use default value if we can't find the attribute
        elif param.default != inspect.Parameter.empty:
            value = param.default
        else:
            value = None
            
        # Deep copy mutable objects to avoid shared references
        if isinstance(value, (list, dict, tuple)):
            value = copy.deepcopy(value)
            
        init_params[param_name] = value
    
    # Apply any overrides
    init_params.update(overrides)
    
    # Create the new object
    new_object = original_class(**init_params)
    
    return new_object


def copy_and_offset(original_object, x_offset=0, y_offset=0, container=None, **overrides):
    """
    Convenience function to copy an object and offset its position.
    
    Args:
        original_object: The original UI object to copy
        x_offset: Horizontal offset for the new object
        y_offset: Vertical offset for the new object  
        container: The container for the new object (if None, uses the same container as original)
        **overrides: Any other parameters to override
        
    Returns:
        A new instance with offset position
        
    Example:
        # Copy button and move it 100px to the left
        button2 = copy_and_offset(button1, x_offset=-100)
        
        # Copy button and move it 50px right and 30px down
        button3 = copy_and_offset(button1, x_offset=50, y_offset=30)
    """
    
    # Get current position
    current_x = getattr(original_object, 'x', 0)
    current_y = getattr(original_object, 'y', 0)
    
    # Calculate new position
    new_x = current_x + x_offset
    new_y = current_y + y_offset
    
    # Add position overrides
    overrides['x'] = new_x
    overrides['y'] = new_y
    
    return copy_object(original_object, container=container, **overrides) 