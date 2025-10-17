from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6 import QtWidgets
from PySide6.QtSvgWidgets import QSvgWidget

from pyvisual.ui.shapes.pv_rectangle import PvRectangle
from pyvisual.ui.inputs.pv_button import PvButton


class PvSidebar(QWidget):
    def __init__(self, container, x=0, y=0, width=250, height=600,
                 bg_color=(240, 240, 240, 1), border_color=None, border_thickness=0,
                 corner_radius=0, paddings=(10, 10, 10, 10), spacing=5, items=None,
                 is_visible=True, opacity=1, tag=None, pages_widget=None,
                 on_item_hover=None, on_item_click=None, on_item_release=None,
                 # Item style properties
                 item_height=40, item_corner_radius=5,
                 item_idle_color=(225, 225, 225, 1), item_hover_color=None, item_clicked_color=None,
                 item_selected_color=None, allow_deselect=True,
                 item_border_color=None, item_border_thickness=0, item_border_style="solid",
                 item_font="Arial", item_font_size=12, item_font_color=(0, 0, 0, 1),
                 item_font_color_hover=None, item_font_color_selected=None,
                 item_bold=False, item_italic=False,
                 item_icon_position="left", item_icon_spacing=10, item_icon_scale=1.0,
                 item_icon_color=None, item_selected_icon_color=None,
                 item_alignment="left",  # "left", "center", "right"
                 item_paddings=(10, 5, 10, 5),  # (left, top, right, bottom) internal padding
                 item_is_hover_disabled=False,  # Whether hover effects are disabled
                 default_selection=0,  # Default selected item index (-1 for none)
                 **kwargs):
        super().__init__(container)

        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._paddings = paddings
        self._spacing = spacing
        
        # ---------------------------------------------------------
        # Background Rectangle Properties
        # ---------------------------------------------------------
        self._bg_color = bg_color
        self._border_color = border_color
        self._border_thickness = border_thickness
        self._corner_radius = corner_radius
        
        # ---------------------------------------------------------
        # Item Style Properties
        # ---------------------------------------------------------
        self._item_height = item_height
        self._item_corner_radius = item_corner_radius
        self._item_idle_color = item_idle_color
        self._item_hover_color = item_hover_color
        self._item_clicked_color = item_clicked_color
        self._item_selected_color = item_selected_color or (56, 140, 255, 1)  # Default blue if not specified
        self._allow_deselect = allow_deselect
        self._item_border_color = item_border_color
        self._item_border_thickness = item_border_thickness
        self._item_border_style = item_border_style
        self._item_font = item_font
        self._item_font_size = item_font_size
        self._item_font_color = item_font_color
        self._item_font_color_hover = item_font_color_hover
        self._item_font_color_selected = item_font_color_selected
        self._item_bold = item_bold
        self._item_italic = item_italic
        self._item_icon_position = item_icon_position
        self._item_icon_spacing = item_icon_spacing
        self._item_icon_scale = item_icon_scale
        self._item_icon_color = item_icon_color  # Can be None to use font color
        # If selected icon color is not provided, use selected font color by default
        self._item_selected_icon_color = item_selected_icon_color
        self._item_alignment = item_alignment if item_alignment in ["left", "center", "right"] else "left"
        self._item_paddings = item_paddings
        self._item_is_hover_disabled = item_is_hover_disabled
        self._default_selection = default_selection
        
        # ---------------------------------------------------------
        # Selection State
        # ---------------------------------------------------------
        self._selected_item = None
        self._selected_index = -1
        
        # ---------------------------------------------------------
        # Element State and Appearance
        # ---------------------------------------------------------
        self._is_visible = is_visible
        self._opacity = opacity
        
        # ---------------------------------------------------------
        # Callbacks and Custom Tag
        # ---------------------------------------------------------
        self._on_item_hover = on_item_hover
        self._on_item_click = on_item_click
        self._on_item_release = on_item_release
        self._tag = tag
        
        # ---------------------------------------------------------
        # Page Navigation Properties
        # ---------------------------------------------------------
        self._pages_widget = pages_widget
        
        # ---------------------------------------------------------
        # Item Collection
        # ---------------------------------------------------------
        self._items = []  # Will store all sidebar items
        
        # ---------------------------------------------------------
        # Create UI Components
        # ---------------------------------------------------------
        self._create_layout()
        self._configure_style()
        
        # Add initial items if provided
        if items:
            for item in items:
                self.add_item(**item)
        
        # Use QTimer to apply default selection after all initialization is complete
        # This ensures the items are fully created and painted before selection is applied
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._apply_default_selection)
    
    def _apply_default_selection(self):
        """Apply the default selection after initialization is complete."""
        if self._default_selection >= 0 and len(self._items) > self._default_selection:
            # Direct call to _apply_selected_style to ensure proper highlighting
            item = self._items[self._default_selection]
            self._apply_selected_style(item)
            
            # Update selection state
            self._selected_item = item
            self._selected_index = self._default_selection
            
            # Navigate to the selected page if pages_widget is set
            if self._pages_widget is not None:
                if hasattr(item, '_page_index'):
                    page_index = getattr(item, '_page_index')
                    if hasattr(self._pages_widget, 'set_current_page') and callable(self._pages_widget.set_current_page):
                        try:
                            # Make sure the index is valid
                            if 0 <= page_index < self._pages_widget.count():
                                self._pages_widget.set_current_page(page_index)
                        except Exception as e:
                            print(f"Error changing to default page: {e}")
    
    # ---------------------------------------------------------
    # Create Layout and Configure Style
    # ---------------------------------------------------------
    def _create_layout(self):
        """Create the sidebar layout with background rectangle and vertical item layout."""
        # Set widget position and size
        self.setGeometry(self._x, self._y, self._width, self._height)
        
        # Create main container widget first to host the layout
        self._content_widget = QWidget(self)
        self._content_widget.setGeometry(0, 0, self._width, self._height)
        
        # Create background rectangle (without border)
        self._background = PvRectangle(
            container=self._content_widget,  # Attach to content widget
            x=0,
            y=0,
            width=self._width,
            height=self._height,
            corner_radius=self._corner_radius,
            idle_color=self._bg_color,
            border_color=None,  # No border on rectangle
            border_thickness=0,  # No border thickness
            is_visible=True,
            opacity=self._opacity
        )
        
        # Create layout for items on the content widget
        self._layout = QVBoxLayout(self._content_widget)
        self._layout.setContentsMargins(*self._paddings)
        self._layout.setSpacing(self._spacing)
        self._layout.setAlignment(Qt.AlignTop)
        
        # Create right border line directly on the main widget (not on content widget)
        self._right_border = QFrame(self)  # Parent is main widget
        self._right_border.setFrameShape(QFrame.VLine)
        self._right_border.setFrameShadow(QFrame.Plain)
        self._right_border.setLineWidth(0)  # Remove the frame line
        
        # Set line style
        if self._border_color:
            r, g, b, a = self._border_color
            style = f"QFrame {{ background-color: rgba({r},{g},{b},{a}); border: none; }}"
            self._right_border.setStyleSheet(style)
        else:
            self._right_border.setVisible(False)
            
        # Position the line at the right edge of the sidebar
        self._right_border.setGeometry(self._width - self._border_thickness, 0, 
                                     self._border_thickness, self._height)
        
        # Ensure border is on top
        self._right_border.raise_()
    
    def _configure_style(self):
        """Apply styling to the sidebar."""
        self.setVisible(self._is_visible)
        self.setWindowOpacity(self._opacity)
    
    # ---------------------------------------------------------
    # Item Management Methods
    # ---------------------------------------------------------
    def add_item(self, text="Button", icon_path=None, page_index=None, on_click=None, **item_props):
        """Add a new item to the sidebar.
        
        Args:
            text (str): Text to display on the item
            icon_path (str, optional): Path to the icon file
            page_index (int, optional): Specific page index to navigate to. If None, uses the item's index
            on_click (function, optional): Custom on_click handler. If provided, overrides the default page navigation
            **item_props: Additional properties for PvButton
            
        Returns:
            PvButton: The created item
        """
        # Determine page index for this item if not specified
        if page_index is None:
            page_index = len(self._items)
            
        # Store page index in item properties for use in click handler
        item_props['_page_index'] = page_index
        
        # Set default item properties from sidebar settings
        default_props = {
            'width': self._width - (self._paddings[0] + self._paddings[2]),
            'height': self._item_height,
            'x': 0,  # x and y will be managed by the layout
            'y': 0,
            'corner_radius': self._item_corner_radius,
            'idle_color': self._item_idle_color,
            'hover_color': self._item_idle_color,  # Force hover color to be same as idle color
            'clicked_color': self._item_idle_color,  # Force clicked color to be same as idle color
            'border_color': self._item_border_color,
            'border_thickness': self._item_border_thickness,
            'border_style': self._item_border_style,
            'font': self._item_font,
            'font_size': self._item_font_size,
            'font_color': self._item_font_color,
            'font_color_hover': self._item_font_color,  # Force hover font color same as regular font color
            'bold': self._item_bold,
            'italic': self._item_italic,
            'icon_position': self._item_icon_position,
            'icon_spacing': self._item_icon_spacing,
            'icon_scale': self._item_icon_scale,
            'icon_color': self._item_icon_color,  # Can be None to use font color by default
            'alignment': self._item_alignment,
            'paddings': self._item_paddings,
            'text': text,
            'icon_path': icon_path,
            'on_hover': self._handle_item_hover,
            'on_click': on_click if on_click else self._handle_item_click,
            'on_release': self._handle_item_release,
            'is_hover_disabled': True  # Force hover to be disabled for all buttons
        }
        
        # Store selected icon color as custom attribute for later use
        if self._item_selected_icon_color is not None:
            default_props['_selected_icon_color'] = self._item_selected_icon_color
        elif self._item_font_color_selected is not None:
            # Use selected font color as selected icon color if not specified
            default_props['_selected_icon_color'] = self._item_font_color_selected
        
        # Remove None values to let PvButton use its own defaults
        default_props = {k: v for k, v in default_props.items() if v is not None}
        
        # Explicitly override any provided hover font color to match the normal font color
        if 'font_color' in item_props:
            item_props['font_color_hover'] = item_props['font_color']
        
        # Override defaults with provided properties
        item_props = {**default_props, **item_props}
        
        # Final check to ensure hover font color matches normal font color
        item_props['font_color_hover'] = item_props['font_color']
        
        # Create the item - use content_widget as the container instead of self
        item = PvButton(self._content_widget, **item_props)
        
        # Explicitly set the page index as an attribute on the item object
        setattr(item, '_page_index', page_index)
        
        # If a _selected_icon_color was specified, store it as an attribute on the item
        if '_selected_icon_color' in item_props:
            setattr(item, '_selected_icon_color', item_props['_selected_icon_color'])
        
        # Add to layout and internal list
        self._layout.addWidget(item)
        self._items.append(item)
        
        # Ensure border stays on top after adding items
        if hasattr(self, '_right_border'):
            self._right_border.raise_()
            
        return item
    
    def remove_item(self, item):
        """Remove an item from the sidebar.
        
        Args:
            item: Either the PvButton instance or its index in the sidebar
        """
        if isinstance(item, int) and 0 <= item < len(self._items):
            # Remove by index
            sidebar_item = self._items.pop(item)
            self._layout.removeWidget(sidebar_item)
            sidebar_item.deleteLater()
        elif isinstance(item, PvButton) and item in self._items:
            # Remove by item object
            self._layout.removeWidget(item)
            self._items.remove(item)
            item.deleteLater()
    
    def clear_items(self):
        """Remove all items from the sidebar."""
        for item in self._items[:]:  # Create a copy to iterate over
            self.remove_item(item)
    
    def get_item(self, index):
        """Get an item by its index.
        
        Args:
            index (int): Index of the item
            
        Returns:
            PvButton: The item at the specified index
        """
        if 0 <= index < len(self._items):
            return self._items[index]
        return None
    
    def get_item_count(self):
        """Get the number of items in the sidebar.
        
        Returns:
            int: Number of items
        """
        return len(self._items)
    
    def set_pages_widget(self, pages_widget):
        """Set the pages widget that this sidebar will navigate.
        
        Args:
            pages_widget: The pages widget containing multiple pages
        """
        self._pages_widget = pages_widget
    
    # ---------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------
    def _handle_item_hover(self, item):
        """Internal handler for item hover events."""
        if self._on_item_hover:
            self._on_item_hover(item)
    
    def _handle_item_click(self, item):
        """Internal handler for item click events.
        
        If pages_widget is set, this will navigate to the corresponding page based on the item's index.
        Selects the clicked item and deselects previously selected item.
        If a custom on_item_click is set, it will also be called.
        """
        # Select this item
        if item in self._items:
            self.select_item(item)
        
        # Navigate to the corresponding page if pages_widget is set
        if self._pages_widget is not None:
            if hasattr(item, '_page_index'):
                page_index = getattr(item, '_page_index')
                print(f"Navigating to page {page_index}")
                
                # Check if the method exists and is callable
                if hasattr(self._pages_widget, 'set_current_page') and callable(self._pages_widget.set_current_page):
                    try:
                        # Make sure the index is valid
                        if 0 <= page_index < self._pages_widget.count():
                            self._pages_widget.set_current_page(page_index)
                        else:
                            print(f"Invalid page index: {page_index}, max index: {self._pages_widget.count()-1}")
                    except Exception as e:
                        print(f"Error changing page: {e}")
                else:
                    print("Pages widget doesn't have a set_current_page method")
            else:
                print(f"Item {item.text} has no _page_index attribute")
        else:
            print("No pages_widget is set")
        
        # Call the user-defined click handler if set
        if self._on_item_click:
            self._on_item_click(item)
    
    def _handle_item_release(self, item):
        """Internal handler for item release events."""
        if self._on_item_release:
            self._on_item_release(item)
    
    # ---------------------------------------------------------
    # Properties using the @property decorator
    # ---------------------------------------------------------
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        self._x = value
        self.setGeometry(self._x, self._y, self._width, self._height)
    
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = value
        self.setGeometry(self._x, self._y, self._width, self._height)
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        self._width = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        
        # Update content widget size
        if hasattr(self, '_content_widget'):
            self._content_widget.setGeometry(0, 0, value, self._height)
        
        # Update background rectangle
        if hasattr(self, '_background'):
            self._background.width = value
            
        # Update right border position
        if hasattr(self, '_right_border'):
            self._right_border.setGeometry(value - self._border_thickness, 0, 
                                         self._border_thickness, self._height)
            
        # Update all item widths
        item_width = value - (self._paddings[0] + self._paddings[2])
        for item in self._items:
            item.width = item_width
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        self._height = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        
        # Update content widget size
        if hasattr(self, '_content_widget'):
            self._content_widget.setGeometry(0, 0, self._width, value)
        
        # Update background rectangle
        if hasattr(self, '_background'):
            self._background.height = value
            
        # Update right border height
        if hasattr(self, '_right_border'):
            self._right_border.setGeometry(self._width - self._border_thickness, 0, 
                                         self._border_thickness, value)
    
    @property
    def bg_color(self):
        return self._bg_color
    
    @bg_color.setter
    def bg_color(self, value):
        self._bg_color = value
        if hasattr(self, '_background'):
            self._background.idle_color = value
    
    @property
    def border_color(self):
        return self._border_color
    
    @border_color.setter
    def border_color(self, value):
        self._border_color = value
        if hasattr(self, '_right_border'):
            if value:
                r, g, b, a = value
                style = f"QFrame {{ background-color: rgba({r},{g},{b},{a}); border: none; }}"
                self._right_border.setStyleSheet(style)
                self._right_border.setVisible(True)
            else:
                self._right_border.setVisible(False)
    
    @property
    def border_thickness(self):
        return self._border_thickness
    
    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value
        if hasattr(self, '_right_border'):
            self._right_border.setGeometry(self._width - value, 0, value, self._height)
            self._right_border.setVisible(value > 0 and self._border_color is not None)
    
    @property
    def corner_radius(self):
        return self._corner_radius
    
    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        if hasattr(self, '_background'):
            self._background.corner_radius = value
    
    @property
    def paddings(self):
        return self._paddings
    
    @paddings.setter
    def paddings(self, value):
        self._paddings = value
        if hasattr(self, '_layout'):
            self._layout.setContentsMargins(*value)
            
            # Update item widths
            item_width = self._width - (value[0] + value[2])
            for item in self._items:
                item.width = item_width
    
    @property
    def spacing(self):
        return self._spacing
    
    @spacing.setter
    def spacing(self, value):
        self._spacing = value
        if hasattr(self, '_layout'):
            self._layout.setSpacing(value)
    
    @property
    def is_visible(self):
        return self._is_visible
    
    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)
    
    @property
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
        if hasattr(self, '_background'):
            self._background.opacity = value
    
    @property
    def tag(self):
        return self._tag
    
    @tag.setter
    def tag(self, value):
        self._tag = value
    
    @property
    def pages_widget(self):
        return self._pages_widget
    
    @pages_widget.setter
    def pages_widget(self, widget):
        self._pages_widget = widget
    
    @property
    def on_item_hover(self):
        return self._on_item_hover
    
    @on_item_hover.setter
    def on_item_hover(self, callback):
        self._on_item_hover = callback
    
    @property
    def on_item_click(self):
        return self._on_item_click
    
    @on_item_click.setter
    def on_item_click(self, callback):
        self._on_item_click = callback
    
    @property
    def on_item_release(self):
        return self._on_item_release
    
    @on_item_release.setter
    def on_item_release(self, callback):
        self._on_item_release = callback
    
    @property
    def items(self):
        """Get a copy of the items list."""
        return self._items.copy()
    
    # ---------------------------------------------------------
    # Item Style Properties
    # ---------------------------------------------------------
    @property
    def item_height(self):
        return self._item_height
    
    @item_height.setter
    def item_height(self, value):
        self._item_height = value
    
    @property
    def item_corner_radius(self):
        return self._item_corner_radius
    
    @item_corner_radius.setter
    def item_corner_radius(self, value):
        self._item_corner_radius = value
    
    @property
    def item_idle_color(self):
        return self._item_idle_color
    
    @item_idle_color.setter
    def item_idle_color(self, value):
        self._item_idle_color = value
    
    @property
    def item_hover_color(self):
        return self._item_hover_color
    
    @item_hover_color.setter
    def item_hover_color(self, value):
        self._item_hover_color = value
    
    @property
    def item_clicked_color(self):
        return self._item_clicked_color
    
    @item_clicked_color.setter
    def item_clicked_color(self, value):
        self._item_clicked_color = value
    
    @property
    def item_selected_color(self):
        return self._item_selected_color
    
    @item_selected_color.setter
    def item_selected_color(self, value):
        self._item_selected_color = value
    
    @property
    def item_border_color(self):
        return self._item_border_color
    
    @item_border_color.setter
    def item_border_color(self, value):
        self._item_border_color = value
    
    @property
    def item_border_thickness(self):
        return self._item_border_thickness
    
    @item_border_thickness.setter
    def item_border_thickness(self, value):
        self._item_border_thickness = value
    
    @property
    def item_border_style(self):
        return self._item_border_style
    
    @item_border_style.setter
    def item_border_style(self, value):
        self._item_border_style = value
    
    @property
    def item_font(self):
        return self._item_font
    
    @item_font.setter
    def item_font(self, value):
        self._item_font = value
    
    @property
    def item_font_size(self):
        return self._item_font_size
    
    @item_font_size.setter
    def item_font_size(self, value):
        self._item_font_size = value
    
    @property
    def item_font_color(self):
        return self._item_font_color
    
    @item_font_color.setter
    def item_font_color(self, value):
        self._item_font_color = value
    
    @property
    def item_font_color_hover(self):
        return self._item_font_color_hover
    
    @item_font_color_hover.setter
    def item_font_color_hover(self, value):
        self._item_font_color_hover = value
    
    @property
    def item_font_color_selected(self):
        return self._item_font_color_selected
    
    @item_font_color_selected.setter
    def item_font_color_selected(self, value):
        self._item_font_color_selected = value
    
    @property
    def item_bold(self):
        return self._item_bold
    
    @item_bold.setter
    def item_bold(self, value):
        self._item_bold = value
    
    @property
    def item_italic(self):
        return self._item_italic
    
    @item_italic.setter
    def item_italic(self, value):
        self._item_italic = value
    
    @property
    def item_icon_position(self):
        return self._item_icon_position
    
    @item_icon_position.setter
    def item_icon_position(self, value):
        self._item_icon_position = value
    
    @property
    def item_icon_spacing(self):
        return self._item_icon_spacing
    
    @item_icon_spacing.setter
    def item_icon_spacing(self, value):
        self._item_icon_spacing = value
    
    @property
    def item_icon_scale(self):
        return self._item_icon_scale
    
    @item_icon_scale.setter
    def item_icon_scale(self, value):
        self._item_icon_scale = value
    
    @property
    def item_icon_color(self):
        return self._item_icon_color
    
    @item_icon_color.setter
    def item_icon_color(self, value):
        self._item_icon_color = value
    
    @property
    def item_selected_icon_color(self):
        return self._item_selected_icon_color
    
    @item_selected_icon_color.setter
    def item_selected_icon_color(self, value):
        self._item_selected_icon_color = value
    
    @property
    def item_alignment(self):
        return self._item_alignment
    
    @item_alignment.setter
    def item_alignment(self, value):
        if value in ["left", "center", "right"]:
            self._item_alignment = value
    
    @property
    def item_paddings(self):
        return self._item_paddings
    
    @item_paddings.setter
    def item_paddings(self, value):
        self._item_paddings = value
    
    @property
    def item_is_hover_disabled(self):
        return self._item_is_hover_disabled
    
    @item_is_hover_disabled.setter
    def item_is_hover_disabled(self, value):
        self._item_is_hover_disabled = value
    
    # ---------------------------------------------------------
    # Print Properties
    # ---------------------------------------------------------
    def print_properties(self):
        """Prints all current properties of the PvSidebar."""
        print(f"""
        PvSidebar Properties:
        ------------------------
        x: {self.x}
        y: {self.y}
        width: {self.width}
        height: {self.height}
        bg_color: {self.bg_color}
        border_color: {self.border_color}
        border_thickness: {self.border_thickness}
        corner_radius: {self.corner_radius}
        paddings: {self.paddings}
        spacing: {self.spacing}
        is_visible: {self.is_visible}
        opacity: {self.opacity}
        tag: {self.tag}
        pages_widget: {self.pages_widget}
        item_count: {self.get_item_count()}
        on_item_hover: {self.on_item_hover}
        on_item_click: {self.on_item_click}
        on_item_release: {self.on_item_release}
        
        Item Style Properties:
        ------------------------
        item_height: {self.item_height}
        item_corner_radius: {self.item_corner_radius}
        item_idle_color: {self.item_idle_color}
        item_hover_color: {self.item_hover_color}
        item_clicked_color: {self.item_clicked_color}
        item_selected_color: {self.item_selected_color}
        item_border_color: {self.item_border_color}
        item_border_thickness: {self.item_border_thickness}
        item_border_style: {self.item_border_style}
        item_font: {self.item_font}
        item_font_size: {self.item_font_size}
        item_font_color: {self.item_font_color}
        item_font_color_hover: {self.item_font_color_hover}
        item_font_color_selected: {self.item_font_color_selected}
        item_bold: {self.item_bold}
        item_italic: {self.item_italic}
        item_icon_position: {self.item_icon_position}
        item_icon_spacing: {self.item_icon_spacing}
        item_icon_scale: {self.item_icon_scale}
        item_icon_color: {self.item_icon_color}
        item_selected_icon_color: {self.item_selected_icon_color}
        item_alignment: {self.item_alignment}
        item_paddings: {self.item_paddings}
        item_is_hover_disabled: {self.item_is_hover_disabled}
        """)

    # ---------------------------------------------------------
    # Item Selection Methods
    # ---------------------------------------------------------
    def select_item(self, index_or_item):
        """Select an item in the sidebar by index or by item reference.
        
        Args:
            index_or_item: Either the index of the item or the item object
        
        Returns:
            bool: True if selection was successful, False otherwise
        """
        # Convert item reference to index if needed
        if isinstance(index_or_item, PvButton) and index_or_item in self._items:
            index = self._items.index(index_or_item)
        elif isinstance(index_or_item, int) and 0 <= index_or_item < len(self._items):
            index = index_or_item
        else:
            return False
        
        # If trying to select the already selected item and deselection is allowed
        if index == self._selected_index and self._allow_deselect:
            return self.deselect_item()
        
        # Deselect the current item if there is one
        if self._selected_item:
            self._reset_item_style(self._selected_item)
        
        # Select the new item
        new_item = self._items[index]
        self._apply_selected_style(new_item)
        
        # Update selection state
        self._selected_item = new_item
        self._selected_index = index
        
        return True

    def deselect_item(self):
        """Deselect the currently selected item.
        
        Returns:
            bool: True if an item was deselected, False if no item was selected
        """
        if self._selected_item:
            self._reset_item_style(self._selected_item)
            self._selected_item = None
            self._selected_index = -1
            return True
        return False

    def get_selected_item(self):
        """Get the currently selected item.
        
        Returns:
            PvButton: The selected item or None if no item is selected
        """
        return self._selected_item

    def get_selected_index(self):
        """Get the index of the currently selected item.
        
        Returns:
            int: The index of the selected item or -1 if no item is selected
        """
        return self._selected_index

    def _apply_selected_style(self, item):
        """Apply the selected style to an item."""
        # Store original colors as attributes if not already stored
        if not hasattr(item, '_original_idle_color'):
            setattr(item, '_original_idle_color', item.idle_color)
        if not hasattr(item, '_original_font_color'):
            setattr(item, '_original_font_color', item.font_color)
        if not hasattr(item, '_original_icon_color') and hasattr(item, '_icon_label'):
            setattr(item, '_original_icon_color', item._icon_color if hasattr(item, '_icon_color') else item._font_color)
        
        # Apply selected colors by directly changing the stylesheet
        if self._item_selected_color and self._item_font_color_selected:
            # Get the selected color components
            r, g, b, a = self._item_selected_color
            
            # Get font color components
            fr, fg, fb, fa = self._item_font_color_selected
            
            # Apply selected background color and font color by setting a new stylesheet directly
            item.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {a});
                    border-radius: {item._corner_radius}px;
                    border: {item._border_thickness}px {item._border_style} rgba({item._border_color[0]}, {item._border_color[1]}, {item._border_color[2]}, {item._border_color[3]});
                }}
            """)
            
            # Update the text label's color - find the text label in the button's children
            for child in item.children():
                if isinstance(child, QtWidgets.QLabel):
                    child.setStyleSheet(f"color: rgba({fr}, {fg}, {fb}, {fa}); background: transparent;")
                    break
            
            # Update icon color if we have an SVG icon
            if hasattr(item, '_icon_label') and isinstance(item._icon_label, QSvgWidget):
                # Use selected icon color if specified, otherwise use selected font color
                if hasattr(item, '_selected_icon_color'):
                    selected_icon_color = getattr(item, '_selected_icon_color')
                    from pyvisual.utils.helper_functions import update_svg_color
                    update_svg_color(item._icon_label, selected_icon_color)
        
    def _reset_item_style(self, item):
        """Reset an item's style to its default."""
        # Restore original colors by directly applying stylesheet
        if hasattr(item, '_original_idle_color'):
            r, g, b, a = getattr(item, '_original_idle_color')
            
            # Restore original color using stylesheet
            item.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {a});
                    border-radius: {item._corner_radius}px;
                    border: {item._border_thickness}px {item._border_style} rgba({item._border_color[0]}, {item._border_color[1]}, {item._border_color[2]}, {item._border_color[3]});
                }}
            """)
            
            # Restore original font color
            if hasattr(item, '_original_font_color'):
                fr, fg, fb, fa = getattr(item, '_original_font_color')
                
                # Update the text label's color - find the text label in the button's children
                for child in item.children():
                    if isinstance(child, QtWidgets.QLabel):
                        child.setStyleSheet(f"color: rgba({fr}, {fg}, {fb}, {fa}); background: transparent;")
                        break
            
            # Restore original icon color
            if hasattr(item, '_original_icon_color') and hasattr(item, '_icon_label') and isinstance(item._icon_label, QSvgWidget):
                from pyvisual.utils.helper_functions import update_svg_color
                update_svg_color(item._icon_label, getattr(item, '_original_icon_color'))
        else:
            # Use default idle color if original wasn't stored
            r, g, b, a = self._item_idle_color
            
            # Apply default color using stylesheet
            item.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {a});
                    border-radius: {item._corner_radius}px;
                    border: {item._border_thickness}px {item._border_style} rgba({item._border_color[0]}, {item._border_color[1]}, {item._border_color[2]}, {item._border_color[3]});
                }}
            """)
            
            # Use default font color
            fr, fg, fb, fa = self._item_font_color
            
            # Update the text label's color - find the text label in the button's children
            for child in item.children():
                if isinstance(child, QtWidgets.QLabel):
                    child.setStyleSheet(f"color: rgba({fr}, {fg}, {fb}, {fa}); background: transparent;")
                    break

    # ---------------------------------------------------------
    # More Property Accessors
    # ---------------------------------------------------------
    @property
    def allow_deselect(self):
        """Whether clicking a selected item will deselect it."""
        return self._allow_deselect

    @allow_deselect.setter
    def allow_deselect(self, value):
        self._allow_deselect = value

    @property
    def selected_item(self):
        """The currently selected item."""
        return self._selected_item

    @property
    def selected_index(self):
        """The index of the currently selected item."""
        return self._selected_index


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------
if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()

    # Create a window
    window = pv.PvWindow(title="PvSidebar Example",width=1200,height=600,bg_color=(245,245,245,1))
    
    # Create pages with animations - using the correct constructor
    pages = pv.PvPages(window, animation_duration=300,animation_orientation="horizontal")
    
    # Create some pages to demonstrate navigation
    page_colors = ["#FFCCCC", "#CCFFCC", "#CCCCFF", "#FFFFCC", "#FFCCFF"]
    for i in range(5):
        # Create the page with a color background
        page_index = pages.create_page(f"page{i}")
        
        # Add a label to show which page we're on
        label = pv.PvButton(window, text=f"This is Page {i}", width=200, height=50,
                        font_size=18)
        pages.add_element_to_page(page_index, label, x=400, y=200)

    # Create first sidebar with hover effects enabled (default)
    sidebar1 = PvSidebar(
        container=window,
        x=0,
        y=0,
        width=260,
        bg_color=(255, 255, 255, 1),
        border_color=(235, 235, 235, 1),
        border_thickness=2,
        corner_radius=0,
        paddings=(0, 50, 0, 20),
        spacing=15,  # Add some spacing between items
        is_visible=True,
        pages_widget=pages,  # Connect to pages widget
        # Custom item styling
        item_height=40,
        item_corner_radius=0,
        item_idle_color=(255, 255, 255, 1),
        item_hover_color=(245, 245, 245, 1),
        item_selected_color=(124, 77, 255, 1),  # Purple for selected state
        item_border_color=(220, 0, 220, 0.5),
        item_border_thickness=0,
        item_font_size=14,
        item_font_color=(50,50, 50, 1),
        item_font_color_selected=(255, 255, 255, 1),  # White text for selected state
        item_icon_scale=0.6,
        item_selected_icon_color=(255, 255, 255, 1),  # White icons when selected to match text
        # item_is_hover_disabled=False (default) - keeps hover effects
        item_paddings=(20, 10, 10, 10),
        on_item_click=lambda item: print(f"Sidebar 1 - Clicked on: {item.text}")
    )

    # Add items to the first sidebar
    sidebar1.add_item(text="Dashboard", icon_path=r"D:\Pycharm Projects\pyvisual\pyvisual\assets\icons\Like\like.svg")
    sidebar1.add_item(text="Profile", icon_path=r"D:\Pycharm Projects\pyvisual\pyvisual\assets\icons\more\email.svg")
    sidebar1.add_item(text="Settings", icon_path=r"D:\Pycharm Projects\pyvisual\pyvisual\assets\icons\more\play.svg")
    
    

    # Show the window
    window.show()
    app.run() 