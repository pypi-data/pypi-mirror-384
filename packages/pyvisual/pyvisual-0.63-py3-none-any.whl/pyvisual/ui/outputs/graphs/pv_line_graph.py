from pyvisual.ui.outputs.graphs.pv_base_graph import PvBaseGraph, get_pg, get_np
from PySide6.QtCore import Qt
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pyqtgraph as pg
    import numpy as np


class PvLineGraph(PvBaseGraph):
    """
    A specialized graph class for line plots, inheriting from PvBaseGraph.
    """

    def __init__(self, container, x=100, y=100, width=400, height=300,
                 title="", x_label="", y_label="",
                 idle_color=(255, 255, 255, 1), axis_color=(0, 0, 0, 1),
                 grid=True, grid_color=(200, 200, 200, 1), grid_alpha=0.5,
                 legend=False, crosshair=False,
                 x_range=None, y_range=None, log_x=False, log_y=False,
                 anti_aliasing=True, border_thickness=0, border_color=None, corner_radius=20,
                 is_visible=True, opacity=1.0, tag=None, default_buffer_size=None,
                 is_dynamic=True, update_interval=16,
                 # For backwards compatibility - these will be used for the line
                 fill_area=False, fill_color=None, color=None,
                 # Default line parameters
                 line_x=None, line_y=None, line_name=None, line_color=(0, 0, 255, 1), line_width=1,
                 line_style='solid', line_symbol=None, line_symbol_size=10, line_symbol_color=None,
                 line_buffer_size=None, line_fill_color=None, line_fill_area=False,
                 **kwargs):
        """
        Initialize a line graph with all base graph parameters plus line-specific options.
        
        Args:
            container: Parent widget
            x, y: Position of the widget
            width, height: Size of the widget
            title: Graph title
            x_label, y_label: Axis labels
            idle_color: Graph background color as RGBA tuple
            axis_color: Color of the axes as RGBA tuple
            grid: Whether to show grid lines
            grid_color: Color of grid lines as RGBA tuple
            grid_alpha: Grid transparency (0-1)
            legend: Whether to show the legend
            crosshair: Whether to show a crosshair cursor
            x_range, y_range: Initial axis ranges as (min, max) tuples or None for auto
            log_x, log_y: Whether to use logarithmic scaling for axes
            anti_aliasing: Whether to use anti-aliasing for smoother lines
            border_thickness: Border thickness of the graph widget
            border_color: Border color as RGBA tuple (if None, a darker shade of background color is used)
            corner_radius: Corner radius of the graph widget
            is_visible: Whether the widget is initially visible
            opacity: Widget opacity (0-1)
            tag: Optional user-defined tag for identification
            default_buffer_size: Default size for line data buffers (if None, no buffering)
            is_dynamic: Whether to use a background thread for graph updates
            update_interval: Interval between graph updates in milliseconds
            
            # For backwards compatibility
            fill_area: Whether to fill the area below the curve (deprecated, use line_fill_area)
            fill_color: Color for the area below the curve (deprecated, use line_fill_color)
            color: Line color (deprecated, use line_color)
            
            # Default line parameters
            line_x: X-axis data for default line (array-like)
            line_y: Y-axis data for default line (array-like)
            line_name: Name of the default line (for legend)
            line_color: Default line color as RGBA tuple
            line_width: Default line width
            line_style: Default line style ('solid', 'dash', 'dot', 'dashdot')
            line_symbol: Default symbol type (None, 'o', 's', 't', 'd', '+', 'x')
            line_symbol_size: Default size of symbols
            line_symbol_color: Default symbol color as RGBA tuple (defaults to line color)
            line_buffer_size: Default size of internal buffer (if None, uses default_buffer_size)
            line_fill_color: Default color for the area below the curve as RGBA tuple (if None, no fill)
            line_fill_area: Whether to fill the area below the curve (default is False)
        """
        # Handle deprecated parameters
        # For backwards compatibility, use the top-level parameters if provided
        if color is not None:
            # Use provided color as line_color
            line_color = color
        elif kwargs.get('line_color') is not None:
            # For backwards compatibility
            line_color = kwargs.pop('line_color')
            
        # Use fill_color parameter if provided
        if fill_color is not None:
            line_fill_color = fill_color
            
        # Use fill_area parameter if provided
        if fill_area:
            line_fill_area = True
            
        # For a proper fill, ensure there's a fill color if fill_area is True but no fill_color
        if line_fill_area and line_fill_color is None:
            # Use a semi-transparent version of the line color as fill color
            if line_color is not None:
                if len(line_color) >= 3:
                    if len(line_color) == 3:
                        # Add alpha if not provided
                        line_fill_color = (*line_color, 0.2)
                    else:
                        # Use reduced alpha
                        line_fill_color = (*line_color[:3], line_color[3] * 0.2 if line_color[3] <= 1 else 0.2)
            
        super().__init__(
            container, x, y, width, height, title, x_label, y_label,
            idle_color, axis_color, grid, grid_color, grid_alpha,
            legend, crosshair, x_range, y_range, log_x, log_y,
            anti_aliasing, border_thickness, corner_radius, border_color, is_visible, opacity,
            tag, is_dynamic=is_dynamic, update_interval=update_interval, **kwargs
        )

        # List to store internal data buffers for each line
        self._data_buffers = []
        self._buffer_sizes = []
        self._auto_x = []

        # Track how many valid points are in each buffer
        self._data_lengths = []

        # Default buffer size for all lines
        self._default_buffer_size = default_buffer_size

        # Store line parameters for potential use with dummy data
        self._line_params = {
            'color': line_color,
            'width': line_width,
            'style': line_style,
            'symbol': line_symbol,
            'symbol_size': line_symbol_size,
            'symbol_color': line_symbol_color,
            'buffer_size': line_buffer_size,
            'fill_color': line_fill_color,
            'fill_area': line_fill_area,
            'name': line_name
        }

        # Add a line with the provided data or dummy data if no data provided
        if line_y is not None or line_x is not None:
            # Use provided data
            self.add_line(
                x=line_x, 
                y=line_y, 
                name=line_name,
                color=line_color,
                width=line_width,
                style=line_style,
                symbol=line_symbol,
                symbol_size=line_symbol_size,
                symbol_color=line_symbol_color,
                buffer_size=line_buffer_size,
                fill_color=line_fill_color,
                fill_area=line_fill_area
            )
        else:
            # Use dummy data since no data was provided
            self._add_dummy_data()

    def _add_dummy_data(self):
        """
        Add dummy data to the graph for testing purposes.
        This method is called if no initial data is provided in __init__.
        """
        # Get numpy module
        np = get_np()
        
        # Generate 50 data points with scaled sine wave (sin(i*0.1)*50 + 50)
        x1 = np.arange(50)
        y1 = np.sin(x1 * 0.1) * 50 + 50
        
        # Use the stored line parameters for the dummy data
        self.add_line(
            x=x1,
            y=y1,
            name=self._line_params['name'],
            color=self._line_params['color'],
            width=self._line_params['width'],
            style=self._line_params['style'],
            symbol=self._line_params['symbol'],
            symbol_size=self._line_params['symbol_size'],
            symbol_color=self._line_params['symbol_color'],
            buffer_size=self._line_params['buffer_size'],
            fill_color=self._line_params['fill_color'],
            fill_area=self._line_params['fill_area']
        )

        # Force redraw to ensure data is visible
        self.redraw()

    def add_line(self, x=None, y=None, name=None, color=(0, 0, 255, 1), width=1,
                 style='solid', symbol=None, symbol_size=10, symbol_color=None,
                 buffer_size=None, fill_color=None, fill_area=False):
        """
        Add a line plot to the graph.
        
        Args:
            x: X-axis data (array-like)
            y: Y-axis data (array-like)
            name: Name of the line (for legend)
            color: Line color as RGBA tuple
            width: Line width
            style: Line style ('solid', 'dash', 'dot', 'dashdot')
            symbol: Symbol type (None, 'o', 's', 't', 'd', '+', 'x')
            symbol_size: Size of symbols
            symbol_color: Symbol color as RGBA tuple (defaults to line color)
            buffer_size: Size of internal buffer (if None, uses default_buffer_size)
            fill_color: Color for the area below the curve as RGBA tuple (if None, no fill)
            fill_area: Whether to fill the area below the curve (default is False)
            
        Returns:
            Plot item for further customization
        """
        # Get modules
        pg = get_pg()
        np = get_np()
        
        # Use the default buffer size if not specified
        if buffer_size is None:
            buffer_size = self._default_buffer_size

        # Create default y values if not provided
        if y is None:
            if buffer_size is not None:
                # If buffer_size is specified but no y data, create a single zero
                # (not a full buffer of zeros)
                y = np.array([0.0])
            else:
                print("Error: No Y data provided for line plot")
                return None

        # Create default x values if not provided
        if x is None:
            x = np.arange(len(y))
            auto_x = True
        else:
            auto_x = False

        # Ensure data is properly formatted
        try:
            x = np.array(x, dtype=float)
            y = np.array(y, dtype=float)

            # Check for invalid data
            if np.isnan(x).any() or np.isnan(y).any():
                print("Warning: Data contains NaN values, which may prevent display")

            if len(x) != len(y):
                print(f"Warning: X and Y arrays have different lengths! X: {len(x)}, Y: {len(y)}")
                # Use the minimum length
                min_len = min(len(x), len(y))
                x = x[:min_len]
                y = y[:min_len]

            if len(x) == 0 or len(y) == 0:
                print("Error: Empty data arrays provided")
                return None

        except Exception as e:
            print(f"Error converting data to numpy arrays: {e}")
            return None

        # Make sure color is valid
        if len(color) < 3:
            print(f"Warning: Invalid color format: {color}. Using default blue.")
            color = (0, 0, 255, 1)
        elif len(color) == 3:
            # Add alpha if not provided
            color = (*color, 1)

        # Convert RGBA to PyQtGraph format
        plot_color = tuple(c / 255.0 for c in color[:3])
        plot_alpha = color[3]

        # Create pen for the line
        color_obj = pg.mkColor(int(color[0]), int(color[1]), int(color[2]), int(plot_alpha * 255))

        line_style_map = {
            'solid': Qt.SolidLine,
            'dash': Qt.DashLine,
            'dot': Qt.DotLine,
            'dashdot': Qt.DashDotLine
        }

        pen = pg.mkPen(color=color_obj,
                       width=width,
                       style=line_style_map.get(style, Qt.SolidLine))

        # Symbol settings
        symbol_map = {
            'o': 'o',  # circle
            's': 's',  # square
            't': 't',  # triangle
            'd': 'd',  # diamond
            '+': '+',  # plus
            'x': 'x'  # x
        }

        sym = symbol_map.get(symbol, None)

        # Symbol color
        if symbol_color is None:
            symbol_brush = pg.mkBrush(color_obj)
        else:
            # Make sure symbol color is valid
            if len(symbol_color) < 3:
                print(f"Warning: Invalid symbol color format: {symbol_color}. Using line color.")
                symbol_color = color
            elif len(symbol_color) == 3:
                # Add alpha if not provided
                symbol_color = (*symbol_color, 1)

            sym_color_obj = pg.mkColor(int(symbol_color[0]), int(symbol_color[1]),
                                       int(symbol_color[2]), int(symbol_color[3] * 255))
            symbol_brush = pg.mkBrush(sym_color_obj)

        # Fill settings
        fill_brush = None
        if fill_color is not None and fill_area:
            # Make sure fill color is valid
            if len(fill_color) < 3:
                print(f"Warning: Invalid fill color format: {fill_color}.")
                # Use line color with reduced alpha
                fill_color = (*color[:3], 0.3 if len(color) == 4 else color[3] * 0.3)
            elif len(fill_color) == 3:
                # Add alpha if not provided (use 30% opacity by default)
                fill_color = (*fill_color, 0.3)

            fill_color_obj = pg.mkColor(
                int(fill_color[0]),
                int(fill_color[1]),
                int(fill_color[2]),
                int(fill_color[3] * 255)
            )
            fill_brush = pg.mkBrush(fill_color_obj)

        # Try to add the plot
        try:
            # Important: Initially only plot the provided data, not a full buffer of zeros
            plot = self._plot_widget.plot(
                x=x, y=y,
                pen=pen,
                symbol=sym,
                symbolSize=symbol_size,
                symbolBrush=symbol_brush,
                name=name,
                fillLevel=0 if fill_area and fill_color is not None else None,
                fillBrush=fill_brush
            )

            # Store plot for later reference
            self._data_items.append(plot)

            # Set up internal buffer if buffer_size is provided
            if buffer_size is not None:
                # Create buffer of the right size but only filled with zeros
                x_buffer = np.zeros(buffer_size)
                y_buffer = np.zeros(buffer_size)

                # Store initial data in the buffer, but don't show the zeros
                data_len = len(y)
                if data_len > buffer_size:
                    # If we have more data than buffer size, use the most recent points
                    x_buffer[:] = x[-buffer_size:]
                    y_buffer[:] = y[-buffer_size:]
                else:
                    # If we have less data than buffer size, store at end of buffer
                    x_buffer[-data_len:] = x
                    y_buffer[-data_len:] = y

                self._data_buffers.append((x_buffer, y_buffer))
                self._buffer_sizes.append(buffer_size)

                # Store current valid data length (0 means empty)
                # This helps us track how much of the buffer is actually used
                if not hasattr(self, '_data_lengths'):
                    self._data_lengths = []
                self._data_lengths.append(min(data_len, buffer_size))
            else:
                # No internal buffering for this line
                self._data_buffers.append(None)
                self._buffer_sizes.append(None)
                if not hasattr(self, '_data_lengths'):
                    self._data_lengths = []
                self._data_lengths.append(0)

            # Store whether x is auto-generated
            self._auto_x.append(auto_x)

            # Auto range to show all data
            self._plot_item.enableAutoRange()

            # Force redraw to ensure data is visible
            self.redraw()

            return plot

        except Exception as e:
            print(f"Error creating line plot: {e}")

            # Try an alternative approach
            try:
                plot = self._plot_item.plot(
                    x=x, y=y,
                    pen=pen,
                    symbol=sym,
                    symbolSize=symbol_size,
                    symbolBrush=symbol_brush,
                    name=name,
                    fillLevel=0 if fill_area and fill_color is not None else None,
                    fillBrush=fill_brush
                )

                self._data_items.append(plot)
                self._data_buffers.append(None)
                self._buffer_sizes.append(None)
                if not hasattr(self, '_data_lengths'):
                    self._data_lengths = []
                self._data_lengths.append(0)
                self._auto_x.append(auto_x)
                self._plot_item.enableAutoRange()
                self.redraw()
                return plot

            except Exception as e2:
                print(f"Alternative plotting error: {e2}")
                return None

    def update_line(self, line_index, x=None, y=None, fill_color=None, fill_area=None):
        """
        Update an existing line's data completely.
        
        Args:
            line_index: Index of the line to update
            x: New x data
            y: New y data
            fill_color: New fill color as RGBA tuple (if None, doesn't change)
            fill_area: Whether to fill the area below the curve (if None, doesn't change)
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= line_index < len(self._data_items):
            if self._is_dynamic:
                # Queue the update to run in the background thread
                return self.queue_update(self._do_update_line, line_index, x, y, fill_color, fill_area)
            else:
                # Run immediately in the current thread
                return self._do_update_line(line_index, x, y, fill_color, fill_area)
        return False

    def _do_update_line(self, line_index, x=None, y=None, fill_color=None, fill_area=None):
        """Implementation of update_line that runs in UI thread"""
        # Get modules
        pg = get_pg()
        np = get_np()
        
        line = self._data_items[line_index]
        updated = False

        # Update fill options if provided
        if fill_color is not None:
            try:
                # Make sure fill color is valid
                if len(fill_color) < 3:
                    print(f"Warning: Invalid fill color format: {fill_color}.")
                    return False
                elif len(fill_color) == 3:
                    # Add alpha if not provided
                    fill_color = (*fill_color, 0.3)

                fill_color_obj = pg.mkColor(
                    int(fill_color[0]),
                    int(fill_color[1]),
                    int(fill_color[2]),
                    int(fill_color[3] * 255)
                )
                line.setFillBrush(fill_color_obj)
                updated = True
            except Exception as e:
                print(f"Error setting fill brush: {e}")
                return False

        if fill_area is not None:
            try:
                if fill_area:
                    line.setFillLevel(0)
                else:
                    line.setFillLevel(None)
                updated = True
            except Exception as e:
                print(f"Error setting fill level: {e}")
                return False

        if y is not None:
            try:
                # Convert to numpy arrays
                y_data = np.array(y, dtype=float)
                
                # Create corresponding x data if not provided
                if x is None:
                    if self._auto_x[line_index]:
                        x_data = np.arange(len(y_data))
                    elif line_index < len(self._data_items) and hasattr(self._data_items[line_index], 'xData'):
                        # Try to use existing x data
                        existing_x = self._data_items[line_index].xData
                        if existing_x is not None and len(existing_x) == len(y_data):
                            x_data = existing_x
                        else:
                            x_data = np.arange(len(y_data))
                    else:
                        x_data = np.arange(len(y_data))
                else:
                    x_data = np.array(x, dtype=float)
                
                # Ensure x and y are the same length
                if len(x_data) != len(y_data):
                    print(f"Warning: X and Y arrays have different lengths. X: {len(x_data)}, Y: {len(y_data)}")
                    min_len = min(len(x_data), len(y_data))
                    x_data = x_data[:min_len]
                    y_data = y_data[:min_len]
                
                # Check if this line has a buffer
                if self._data_buffers[line_index] is not None and self._buffer_sizes[line_index] is not None:
                    buffer_size = self._buffer_sizes[line_index]
                    
                    # If there's more data than buffer size, only use the most recent points
                    if len(y_data) > buffer_size:
                        y_data = y_data[-buffer_size:]
                        x_data = x_data[-buffer_size:]
                    
                    # Update our internal buffer
                    new_x = np.zeros(buffer_size)
                    new_y = np.zeros(buffer_size)
                    
                    # Place data at the beginning of buffer
                    data_len = len(y_data)
                    new_y[:data_len] = y_data
                    new_x[:data_len] = x_data
                    
                    # Update buffers and length
                    self._data_buffers[line_index] = (new_x, new_y)
                    self._data_lengths[line_index] = data_len
                
                # Update the plot with the data
                line.setData(x=x_data, y=y_data)
                updated = True
                
            except Exception as e:
                print(f"Error updating line data: {e}")
                return False

        # Force redraw if anything was updated
        if updated:
            self._do_redraw()
            
        return True

    def add_point(self, line_index, y_value, x_value=None):
        """
        Add a single data point to a line's buffer and update the plot.
        
        Args:
            line_index: Index of the line to update
            y_value: New Y value to add
            x_value: New X value to add (if None and auto_x is True, will be auto-generated)
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= line_index < len(self._data_items):
            if self._is_dynamic:
                # Queue the point addition to run in the background thread
                return self.queue_update(self._do_add_point, line_index, y_value, x_value)
            else:
                # Run immediately in the current thread
                return self._do_add_point(line_index, y_value, x_value)
        return False

    def _do_add_point(self, line_index, y_value, x_value=None):
        """Implementation of add_point that runs in UI thread"""
        # Get modules
        pg = get_pg()
        np = get_np()
        
        # Check if this line has a buffer
        if self._data_buffers[line_index] is None:
            print("Error: This line doesn't have an internal buffer. Use update_line() instead.")
            return False

        # Create new arrays directly instead of modifying in place
        # This avoids reference issues that might cause display problems
        x_buffer, y_buffer = self._data_buffers[line_index]
        buffer_size = self._buffer_sizes[line_index]
        current_length = self._data_lengths[line_index]

        # Create numpy arrays for the updated data
        if current_length < buffer_size:
            # Buffer isn't full yet, just append the new value
            new_length = current_length + 1
            
            # Create new y array
            new_y = np.zeros(new_length)
            if current_length > 0:
                new_y[:current_length] = y_buffer[:current_length]
            new_y[-1] = y_value
            
            # Create new x array
            new_x = np.zeros(new_length)
            if current_length > 0:
                new_x[:current_length] = x_buffer[:current_length]
                
            # Set the x value for the new point
            if x_value is None and self._auto_x[line_index]:
                # Auto-generate X value
                if current_length > 0:
                    # Increment from last X
                    new_x[-1] = new_x[-2] + 1
                else:
                    # Start at 0
                    new_x[-1] = 0
            else:
                # Use provided X value
                new_x[-1] = x_value if x_value is not None else new_length - 1
        else:
            # Buffer is full, create new arrays with the oldest point removed
            new_length = buffer_size
            
            # Shift data (remove oldest point)
            new_y = np.zeros(buffer_size)
            new_y[:-1] = y_buffer[1:]
            new_y[-1] = y_value
            
            # Handle x values
            new_x = np.zeros(buffer_size)
            new_x[:-1] = x_buffer[1:]
            
            # Set the x value for the new point
            if x_value is None and self._auto_x[line_index]:
                # Auto-generate X value (increment from the last one)
                new_x[-1] = new_x[-2] + 1
            else:
                # Use provided X value
                new_x[-1] = x_value if x_value is not None else new_x[-2] + 1

        # Update our internal record of the buffers with the new arrays
        self._data_buffers[line_index] = (new_x, new_y)
        self._data_lengths[line_index] = new_length

        # Update the plot with fresh copies of the data
        try:
            # Always create a new copy for PyQtGraph to avoid reference issues
            self._data_items[line_index].setData(
                x=np.array(new_x, dtype=float), 
                y=np.array(new_y, dtype=float)
            )
            
            # Force redraw
            self._do_redraw()
            return True
        except Exception as e:
            print(f"Error updating plot: {e}")
            return False

    def add_points(self, line_index, y_values, x_values=None):
        """
        Add multiple data points to a line's buffer and update the plot.
        
        Args:
            line_index: Index of the line to update
            y_values: Array of new Y values to add
            x_values: Array of new X values to add (if None and auto_x is True, will be auto-generated)
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= line_index < len(self._data_items):
            if self._is_dynamic:
                # Queue the points addition to run in the background thread
                return self.queue_update(self._do_add_points, line_index, y_values, x_values)
            else:
                # Run immediately in the current thread
                return self._do_add_points(line_index, y_values, x_values)
        return False

    def _do_add_points(self, line_index, y_values, x_values=None):
        """Implementation of add_points that runs in UI thread"""
        # Get modules
        pg = get_pg()
        np = get_np()
        
        # Check if this line has a buffer
        if self._data_buffers[line_index] is None:
            print("Error: This line doesn't have an internal buffer. Use update_line() instead.")
            return False

        # Convert input to numpy arrays if they aren't already
        try:
            y_values = np.array(y_values, dtype=float)
            if x_values is not None:
                x_values = np.array(x_values, dtype=float)
                
            # Ensure same length
            if x_values is not None and len(x_values) != len(y_values):
                print(f"Warning: X and Y arrays have different lengths. X: {len(x_values)}, Y: {len(y_values)}")
                min_len = min(len(x_values), len(y_values))
                x_values = x_values[:min_len]
                y_values = y_values[:min_len]
                
            if len(y_values) == 0:
                print("Warning: No data points provided")
                return True
        except Exception as e:
            print(f"Error converting input data: {e}")
            return False

        # Get current buffer info
        x_buffer, y_buffer = self._data_buffers[line_index]
        buffer_size = self._buffer_sizes[line_index]
        current_length = self._data_lengths[line_index]
        num_new_points = len(y_values)
        
        # Create auto-generated x values if needed
        if x_values is None and self._auto_x[line_index]:
            # Generate sequential x values
            if current_length > 0:
                # Start from last x value + 1
                start_x = x_buffer[current_length - 1] + 1
                x_values = np.arange(start_x, start_x + num_new_points)
            else:
                # Start from 0
                x_values = np.arange(num_new_points)
        elif x_values is None:
            # Use indices as x values if not auto-generating
            x_values = np.arange(current_length, current_length + num_new_points)
            
        # Calculate how many points we'll have after adding new ones
        total_points = current_length + num_new_points
        
        if total_points <= buffer_size:
            # All points will fit in the buffer
            new_length = total_points
            
            # Create new arrays with existing data plus new data
            new_y = np.zeros(new_length)
            new_x = np.zeros(new_length)
            
            # Copy existing data
            if current_length > 0:
                new_y[:current_length] = y_buffer[:current_length]
                new_x[:current_length] = x_buffer[:current_length]
                
            # Add new data
            new_y[current_length:] = y_values
            new_x[current_length:] = x_values
        else:
            # Not all points will fit - need to decide what to keep
            new_length = buffer_size
            
            if num_new_points >= buffer_size:
                # If there are more new points than buffer size,
                # just use the most recent new points
                new_y = y_values[-buffer_size:]
                new_x = x_values[-buffer_size:]
            else:
                # Keep some old points plus all new points
                keep_old = buffer_size - num_new_points
                
                # Create new arrays
                new_y = np.zeros(buffer_size)
                new_x = np.zeros(buffer_size)
                
                # Copy the most recent old points to the beginning
                new_y[:keep_old] = y_buffer[current_length-keep_old:current_length]
                new_x[:keep_old] = x_buffer[current_length-keep_old:current_length]
                
                # Add new points at the end
                new_y[keep_old:] = y_values
                new_x[keep_old:] = x_values

        # Update our internal record of the buffers
        self._data_buffers[line_index] = (new_x, new_y)
        self._data_lengths[line_index] = new_length

        # Update the plot with fresh data
        try:
            # Create fresh copies to avoid reference issues
            self._data_items[line_index].setData(
                x=np.array(new_x, dtype=float),
                y=np.array(new_y, dtype=float)
            )
            
            # Force redraw
            self._do_redraw()
            return True
        except Exception as e:
            print(f"Error updating plot: {e}")
            return False

    def get_buffer(self, line_index):
        """
        Get the current data buffer for a line.
        
        Args:
            line_index: Index of the line
            
        Returns:
            Tuple of (x_buffer, y_buffer) or None if no buffer exists
        """
        if 0 <= line_index < len(self._data_buffers):
            return self._data_buffers[line_index]
        return None

    def set_buffer_size(self, line_index, buffer_size):
        """
        Change the buffer size for a line.
        
        Args:
            line_index: Index of the line
            buffer_size: New buffer size
            
        Returns:
            True if successful, False otherwise
        """
        np = get_np()
        
        if 0 <= line_index < len(self._data_items):
            # Get current buffer
            current_buffer = self._data_buffers[line_index]

            # If line doesn't have a buffer yet, create one
            if current_buffer is None:
                x_buffer = np.zeros(buffer_size)
                y_buffer = np.zeros(buffer_size)
                self._data_buffers[line_index] = (x_buffer, y_buffer)
                self._buffer_sizes[line_index] = buffer_size
                return True

            # Resize existing buffer
            x_buffer, y_buffer = current_buffer
            old_size = len(x_buffer)

            if buffer_size > old_size:
                # New buffer is larger, pad with zeros
                new_x = np.zeros(buffer_size)
                new_y = np.zeros(buffer_size)
                new_x[-old_size:] = x_buffer
                new_y[-old_size:] = y_buffer
            else:
                # New buffer is smaller, keep most recent data
                new_x = x_buffer[-buffer_size:]
                new_y = y_buffer[-buffer_size:]

            self._data_buffers[line_index] = (new_x, new_y)
            self._buffer_sizes[line_index] = buffer_size

            # Update the plot
            self._data_items[line_index].setData(x=new_x, y=new_y)
            self.redraw()
            return True

        return False


# Example usage of the line graph class
if __name__ == "__main__":
    import pyvisual as pv
    from pyvisual.utils.pv_timer import PvTimer
    import random
    import time

    # Create app and window
    app = pv.PvApp()
    window = pv.PvWindow(title="Line Graph Examples", is_resizable=True)
    window.resize(1200, 800)

    # Get numpy module
    np = get_np()

    # ---------------------------------------------------------------------------
    # Example 1: Static Line Graph with default line (explicitly provided data)
    # ---------------------------------------------------------------------------
    # Create sine wave data for the default line
    x1 = np.linspace(0, 10, 100)
    y1 = np.sin(x1)
    
    line_graph = PvLineGraph(
        container=window,
        x=50, y=50,
        width=500, height=350,
        title="Static Line Graph Example",
        x_label="X-Axis",
        y_label="Y-Axis",
        idle_color=(240, 240, 250, 1),  # Light blue background
        grid=True,
        legend=True,
        crosshair=True,
        corner_radius=5,
        # Default line parameters
        line_x=x1,
        line_y=y1,
        line_name="sin(x)",
        line_color=(255, 0, 0, 1),  # Red
        line_width=2
    )

    # Example 2: Cosine wave with symbols and custom style
    x2 = np.linspace(0, 10, 50)
    y2 = np.cos(x2)
    line_graph.add_line(
        x=x2,
        y=y2,
        name="cos(x)",
        color=(0, 100, 255, 1),  # Blue
        width=2,
        style='dash',
        symbol='o',  # Circle symbols
        symbol_size=8,
        symbol_color=(0, 100, 255, 1)  # Same color as line
    )

    # Example 3: Exponential decay with different symbols and fill
    x3 = np.linspace(0, 10, 30)
    y3 = np.exp(-0.5 * x3)
    line_graph.add_line(
        x=x3,
        y=y3,
        name="exp(-0.5x)",
        color=(0, 180, 0, 1),  # Green
        width=2,
        style='solid',
        symbol='s',  # Square symbols
        symbol_size=10,
        symbol_color=(0, 120, 0, 1),  # Darker green for symbols
        fill_color=(0, 180, 0, 0.2),  # Light green fill with 20% opacity
        fill_area=True  # Enable area filling
    )

    # ---------------------------------------------------------------------------
    # Example 2: Real-time updating with default line using default buffer
    # ---------------------------------------------------------------------------

    # Define a default buffer size for the entire graph
    buffer_size = 100

    # Create a real-time graph with a default buffer size and default line
    default_buffer_graph = PvLineGraph(
        container=window,
        x=600, y=50,
        width=550, height=350,
        title="Default Buffer Size Example",
        x_label="Time",
        y_label="Value",
        idle_color=(245, 245, 245, 1),  # Light gray background
        grid=True,
        legend=True,
        crosshair=True,
        x_range=(0, 100),  # Fixed x-range for scrolling effect
        y_range=(-1.5, 1.5),  # Fixed y-range
        default_buffer_size=buffer_size,  # Set default buffer size for all lines
        # Default line parameters (this will be index 0)
        line_name="Sine Wave",
        line_color=(255, 0, 0, 1),  # Red
        line_width=2,
        line_fill_color=(255, 0, 0, 0.2),  # Light red fill
        line_fill_area=True  # Enable area filling
    )

    # Add a second line (this will be index 1)
    noise_line = default_buffer_graph.add_line(
        name="Noisy Data",
        color=(0, 0, 255, 1),  # Blue
        width=1,
        symbol='o',  # Circle symbols
        symbol_size=4,
        fill_color=(0, 0, 255, 0.2),  # Light blue fill
        fill_area=True  # Enable area filling
    )

    # ---------------------------------------------------------------------------
    # Example 3: Line Graph with automatic dummy data (no initial data provided)
    # ---------------------------------------------------------------------------
    auto_dummy_graph = PvLineGraph(
        container=window,
        x=50, y=450,
        width=500, height=300,
        title="Automatic Dummy Data Example",
        x_label="X-Axis",
        y_label="Y-Axis",
        idle_color=(250, 250, 250, 1),  # White background
        grid=True,
        legend=True,
        # Custom parameters for the automatic dummy data
        line_name="Auto-generated Data",
        line_color=(36, 152, 243, 1),  # Blue
        line_width=3,
        line_fill_color=(36, 152, 243, 0.2),  # Light blue fill
        line_fill_area=True  # Enable area filling
    )

    # ---------------------------------------------------------------------------
    # Example 4: Using top-level fill parameters (backward compatibility)
    # ---------------------------------------------------------------------------
    # Example with a filled area under the curve using top-level parameters
    x4 = np.linspace(0, 20, 200)
    y4 = np.sin(x4) * np.exp(-0.2 * x4)
    
    backward_compat_graph = PvLineGraph(
        container=window,
        x=600, y=450,
        width=550, height=300,
        title="Top-level Fill Parameters Example",
        x_label="X-Axis",
        y_label="Y-Axis",
        idle_color=(250, 250, 250, 1),  # White background
        grid=True,
        legend=True,
        # Top-level fill parameters
        fill_area=True,  # Enable area filling
        fill_color=(100, 50, 200, 0.3),  # Light purple with 30% opacity
        color=(100, 50, 200, 1),  # Purple
        # Default line parameters
        line_x=x4,
        line_y=y4,
        line_name="Damped Sine Wave",
        line_width=3
    )

    # Animation variables
    phase = 0


    # Update function that will be called by the timer
    def update_data():
        global phase
        
        # Get numpy
        np = get_np()

        # Update phase
        phase += 0.1

        # Calculate new values
        sine_value = np.sin(phase)
        noise_value = sine_value + random.uniform(-0.3, 0.3)

        # Example 2: Add points to default buffer graph
        # Index 0 is the default line (Sine Wave)
        # Index 1 is the added line (Noisy Data)
        default_buffer_graph.add_point(0, sine_value)
        default_buffer_graph.add_point(1, noise_value)


    # Create and start timer for real-time updates (50ms = 20fps)
    timer = PvTimer(interval=50, callback=update_data)
    timer.start()

    # Show the window and start the application
    window.show()
    app.run()
