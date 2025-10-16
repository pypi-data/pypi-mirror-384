from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
import pyqtgraph as pg
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from pyvisual.utils.pv_timer import PvTimer

class PvGraph(QWidget):
    """
    A customizable graph widget based on PyQtGraph.
    Allows for plotting line graphs, scatter plots, and bar charts with various styling options.
    """
    
    def __init__(self, container, x=100, y=100, width=400, height=300, 
                 title="", x_label="", y_label="", 
                 background_color=(255, 255, 255, 1), axis_color=(0, 0, 0, 1),
                 grid=True, grid_color=(200, 200, 200, 1), grid_alpha=0.5,
                 legend=False, crosshair=False, 
                 x_range=None, y_range=None, log_x=False, log_y=False,
                 anti_aliasing=True, border_width=0, corner_radius=0, 
                 is_visible=True, opacity=1.0, tag=None, auto_update=True,
                 update_interval=100, **kwargs):
        """
        Initialize a PvGraph widget with customizable properties.
        
        Args:
            container: Parent widget
            x, y: Position of the widget
            width, height: Size of the widget
            title: Graph title
            x_label, y_label: Axis labels
            background_color: Graph background color as RGBA tuple
            axis_color: Color of the axes as RGBA tuple
            grid: Whether to show grid lines
            grid_color: Color of grid lines as RGBA tuple
            grid_alpha: Grid transparency (0-1)
            legend: Whether to show the legend
            crosshair: Whether to show a crosshair cursor
            x_range, y_range: Initial axis ranges as (min, max) tuples or None for auto
            log_x, log_y: Whether to use logarithmic scaling for axes
            anti_aliasing: Whether to use anti-aliasing for smoother lines
            border_width: Border width of the graph widget
            corner_radius: Corner radius of the graph widget
            is_visible: Whether the widget is initially visible
            opacity: Widget opacity (0-1)
            tag: Optional user-defined tag for identification
            auto_update: Whether to automatically update the graph at regular intervals
            update_interval: Milliseconds between updates when auto_update is True
        """
        super().__init__(container)
        
        # --------------------------------------------------------------------
        # Geometry properties
        # --------------------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        
        # --------------------------------------------------------------------
        # Graph appearance properties
        # --------------------------------------------------------------------
        self._title = title
        self._x_label = x_label
        self._y_label = y_label
        self._background_color = background_color
        self._axis_color = axis_color
        self._grid = grid
        self._grid_color = grid_color
        self._grid_alpha = grid_alpha
        self._legend = legend
        self._crosshair = crosshair
        self._x_range = x_range
        self._y_range = y_range
        self._log_x = log_x
        self._log_y = log_y
        self._anti_aliasing = anti_aliasing
        self._border_width = border_width
        self._corner_radius = corner_radius
        
        # --------------------------------------------------------------------
        # Widget properties
        # --------------------------------------------------------------------
        self._is_visible = is_visible
        self._opacity = opacity
        self._tag = tag
        
        # --------------------------------------------------------------------
        # Data properties
        # --------------------------------------------------------------------
        self._data_items = []  # List to keep track of all plot items
        
        # --------------------------------------------------------------------
        # Timer properties
        # --------------------------------------------------------------------
        self._auto_update = auto_update
        self._update_interval = update_interval
        self._timer = None
        
        # Initialize the layout and graph
        self._init_ui()
        self._configure_style()
        
        # Start timer if auto_update is enabled
        if self._auto_update:
            self.start_update_timer()
        
    def _init_ui(self):
        """Initialize the UI components and layout."""
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create PyQtGraph plot widget
        self._plot_widget = pg.PlotWidget()
        
        # Apply background color immediately
        bg_color = tuple(c/255.0 for c in self._background_color[:3])
        bg_alpha = self._background_color[3]
        self._plot_widget.setBackground(pg.mkColor(*bg_color, bg_alpha))
        
        # Set size policy for the widget
        self._plot_widget.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Expanding
        )
        
        # Add to layout
        layout.addWidget(self._plot_widget)
        
        # Get the plot item for customization
        self._plot_item = self._plot_widget.getPlotItem()
        
        # Apply background to viewbox as well
        viewbox = self._plot_item.getViewBox()
        if viewbox:
            viewbox.setBackgroundColor(pg.mkColor(*bg_color, bg_alpha))
        
        # Set initial properties
        if self._title:
            self._plot_item.setTitle(self._title)
        if self._x_label:
            self._plot_item.setLabel('bottom', self._x_label)
        if self._y_label:
            self._plot_item.setLabel('left', self._y_label)
        
        # Configure crosshair cursor
        if self._crosshair:
            self._plot_widget.setCursor(Qt.CrossCursor)
        
        # Configure legend
        if self._legend:
            self._plot_item.addLegend()
        
        # Configure axis ranges
        if self._x_range:
            self._plot_item.setXRange(self._x_range[0], self._x_range[1])
        if self._y_range:
            self._plot_item.setYRange(self._y_range[0], self._y_range[1])
        
        # Configure logarithmic axes
        if self._log_x:
            self._plot_item.setLogMode(x=True, y=self._log_y)
        elif self._log_y:
            self._plot_item.setLogMode(x=False, y=True)
        
        # Configure grid
        self._plot_item.showGrid(x=self._grid, y=self._grid, alpha=self._grid_alpha)
        
        # Set anti-aliasing
        if self._anti_aliasing:
            pg.setConfigOptions(antialias=True)
        
        # Apply layout
        self.setLayout(layout)
    
    def _configure_style(self):
        """Configure the visual style of the graph."""
        # Convert RGBA to PyQtGraph format
        bg_color = tuple(c/255.0 for c in self._background_color[:3])
        bg_alpha = self._background_color[3]
        
        axis_color = tuple(c/255.0 for c in self._axis_color[:3])
        axis_alpha = self._axis_color[3]
        
        grid_color = tuple(c/255.0 for c in self._grid_color[:3])
        
        # Set background color - multiple approaches for compatibility
        try:
            # Method 1: Direct color setting
            self._plot_widget.setBackground(pg.mkColor(*bg_color, bg_alpha))
            
            # Method 2: Set the background on the viewbox directly
            view_box = self._plot_item.getViewBox()
            if view_box:
                view_box.setBackgroundColor(pg.mkColor(*bg_color, bg_alpha))
            
            # Method 3: Use stylesheet
            r, g, b = [int(c * 255) for c in bg_color]
            alpha_percent = int(bg_alpha * 100)
            self._plot_widget.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {alpha_percent}%);")
            
            # Method 4: Create a background item using a rectangle
            try:
                # Remove any existing background rectangles
                if hasattr(self, '_bg_rect') and self._bg_rect is not None:
                    self._plot_item.removeItem(self._bg_rect)
                
                # Create a new background rectangle that fills the view
                view_box = self._plot_item.getViewBox()
                if view_box:
                    # Get the view range
                    view_rect = view_box.viewRange()
                    x_min, x_max = view_rect[0]
                    y_min, y_max = view_rect[1]
                    
                    # Make the rectangle much larger to ensure it covers the view
                    x_size = (x_max - x_min) * 1000
                    y_size = (y_max - y_min) * 1000
                    x_center = (x_max + x_min) / 2
                    y_center = (y_max + y_min) / 2
                    
                    # Create the rectangle
                    self._bg_rect = pg.QtGui.QGraphicsRectItem(
                        x_center - x_size/2, 
                        y_center - y_size/2,
                        x_size, 
                        y_size
                    )
                    # Set Z value to be behind everything
                    self._bg_rect.setZValue(-1000)
                    # Set its color
                    self._bg_rect.setBrush(pg.mkBrush(pg.mkColor(*bg_color, bg_alpha)))
                    self._bg_rect.setPen(pg.mkPen(None))  # No border
                    
                    # Add it to the plot
                    self._plot_item.addItem(self._bg_rect)
            except Exception as e:
                print(f"Error creating background rectangle: {e}")
            
        except Exception as e:
            print(f"Background color setting error: {e}")
        
        # Set axis colors
        axis_pen = pg.mkPen(color=pg.mkColor(*axis_color, axis_alpha), width=1)
        for ax in ['left', 'bottom', 'top', 'right']:
            axis = self._plot_item.getAxis(ax)
            axis.setPen(axis_pen)
        
        # Set grid color and visibility
        if self._grid:
            # Create a grid pen with the desired color
            grid_pen = pg.mkPen(color=pg.mkColor(*grid_color, self._grid_alpha), width=1)
            
            # Set the grid using only alpha
            self._plot_item.showGrid(x=self._grid, y=self._grid, alpha=self._grid_alpha)
            
            # In PyQtGraph, we need to customize grid lines after showing them
            # Try to set the grid pen via getAxis - this works for most PyQtGraph versions
            try:
                self._plot_item.getAxis('left').grid = self._grid
                self._plot_item.getAxis('bottom').grid = self._grid
                
                # Access the internal grid pen of the axes
                for axis in ['left', 'bottom']:
                    grid_lines = self._plot_item.getAxis(axis).gridLines
                    if len(grid_lines) > 0:
                        for line in grid_lines:
                            line.setPen(grid_pen)
            except:
                # Fallback - just show the grid without custom color
                pass
            
            # Set axis grid visibility
            self._plot_widget.getPlotItem().getAxis('left').setGrid(self._grid_alpha)
            self._plot_widget.getPlotItem().getAxis('bottom').setGrid(self._grid_alpha)
        
        # Set widget visibility and opacity
        self.setVisible(self._is_visible)
        self.setWindowOpacity(self._opacity)
        
        # Set border and corner radius
        if self._border_width > 0 or self._corner_radius > 0:
            self.setStyleSheet(f"""
                QWidget {{
                    border: {self._border_width}px solid black;
                    border-radius: {self._corner_radius}px;
                }}
            """)
    
    # -----------------------------------------------------------------------
    # Public Methods for Data Plotting
    # -----------------------------------------------------------------------
    
    def update(self):
        """Force update of the plot widget to ensure data is displayed."""
        from PySide6.QtWidgets import QApplication
        if hasattr(self, '_plot_widget'):
            self._plot_widget.update()
            QApplication.processEvents()
            
    def redraw(self):
        """Force a complete redraw of the graph and all its data."""
        from PySide6.QtWidgets import QApplication
        
        if hasattr(self, '_plot_widget'):
            # Make sure items are visible
            for item in self._data_items:
                if hasattr(item, 'setVisible'):
                    item.setVisible(True)
            
            # Force the plotItem to redraw
            if hasattr(self, '_plot_item') and self._plot_item is not None:
                # Reset view limits if needed
                self._plot_item.enableAutoRange()
                
                # Force view to update
                view_box = self._plot_item.getViewBox()
                if view_box:
                    view_box.update()
            
            # Force the widget to update
            self._plot_widget.update()
            QApplication.processEvents()
            
    def add_line_plot(self, x=None, y=None, name=None, color=(0, 0, 255, 1), width=1, 
                     style='solid', symbol=None, symbol_size=10, symbol_color=None):
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
            
        Returns:
            Plot item for further customization
        """
        # Ensure we have data to plot
        if y is None:
            print("Error: No Y data provided for line plot")
            return None
            
        # Create default x values if not provided
        if x is None:
            x = np.arange(len(y))
        
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
        
        # Debug output
        print(f"Line plot data: {len(x)} points.")
        print(f"X range: {np.min(x)} to {np.max(x)}")
        print(f"Y range: {np.min(y)} to {np.max(y)}")
        print(f"First 5 points: {list(zip(x[:min(5, len(x))], y[:min(5, len(y))]))}")
        print(f"Line color: {color}")
        
        # Make sure color is valid
        if len(color) < 3:
            print(f"Warning: Invalid color format: {color}. Using default blue.")
            color = (0, 0, 255, 1)
        elif len(color) == 3:
            # Add alpha if not provided
            color = (*color, 1)
            
        # Convert RGBA to PyQtGraph format
        plot_color = tuple(c/255.0 for c in color[:3])
        plot_alpha = color[3]
        
        # Make sure the color values are valid
        r, g, b = color[:3]
        print(f"RGB values: {r}, {g}, {b}")
        
        # Create pen for the line with a more explicit color creation
        color_obj = pg.mkColor(int(r), int(g), int(b), int(plot_alpha*255))
        print(f"Created color: {color_obj.getRgb()}")
        
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
            'x': 'x'   # x
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
                
            sym_r, sym_g, sym_b = symbol_color[:3]
            sym_alpha = symbol_color[3]
            
            sym_color_obj = pg.mkColor(int(sym_r), int(sym_g), int(sym_b), int(sym_alpha*255))
            symbol_brush = pg.mkBrush(sym_color_obj)
        
        # Try different approaches to plotting
        plot = None
        success = False
        
        # Approach 1: Direct data passing (most reliable)
        try:
            print("Trying direct plotting approach")
            plot = self._plot_widget.plot(x=x, y=y, pen=pen, symbol=sym, 
                                         symbolSize=symbol_size, 
                                         symbolBrush=symbol_brush, 
                                         name=name)
            if plot is not None:
                success = True
        except Exception as e:
            print(f"Direct plotting error: {e}")
            
            # Approach 2: Use plot item
            try:
                print("Trying plot item approach")
                plot = self._plot_item.plot(x=x, y=y, pen=pen, 
                                           symbol=sym, symbolSize=symbol_size, 
                                           symbolBrush=symbol_brush, name=name)
                if plot is not None:
                    success = True
            except Exception as e:
                print(f"Plot item error: {e}")
                
                # Approach 3: Use PlotDataItem
                try:
                    print("Creating PlotDataItem")
                    plot = pg.PlotDataItem(x=x, y=y, pen=pen, symbol=sym,
                                         symbolSize=symbol_size,
                                         symbolBrush=symbol_brush, name=name)
                    self._plot_item.addItem(plot)
                    if plot is not None:
                        success = True
                except Exception as e:
                    print(f"PlotDataItem error: {e}")
                    
                    # Approach 4: Absolute simplest approach - just draw a line
                    try:
                        print("Trying direct line drawing")
                        plot = pg.PlotCurveItem(x=x, y=y, pen=pen)
                        self._plot_item.addItem(plot)
                        
                        # Add symbols separately if needed
                        if sym:
                            scatter = pg.ScatterPlotItem(x=x, y=y, symbol=sym, 
                                                       size=symbol_size,
                                                       brush=symbol_brush,
                                                       pen=pen)
                            self._plot_item.addItem(scatter)
                        
                        if plot is not None:
                            success = True
                    except Exception as e:
                        print(f"Direct line drawing error: {e}")
        
        # Store plot for later reference
        if success and plot is not None:
            self._data_items.append(plot)
            
            # Auto range to show all data
            self._plot_item.enableAutoRange()
            
            # Force redraw to ensure data is visible
            self.update()
            
            return plot
        else:
            print("WARNING: Failed to create line plot")
            return None
    
    def add_scatter_plot(self, x=None, y=None, name=None, color=(0, 0, 255, 1), 
                        symbol='o', symbol_size=10, brush=None):
        """
        Add a scatter plot to the graph.
        
        Args:
            x: X-axis data (array-like)
            y: Y-axis data (array-like)
            name: Name of the scatter plot (for legend)
            color: Point color as RGBA tuple
            symbol: Symbol type ('o', 's', 't', 'd', '+', 'x')
            symbol_size: Size of symbols
            brush: Optional custom brush for filling symbols
            
        Returns:
            Plot item for further customization
        """
        # Create default x values if not provided
        if x is None and y is not None:
            x = np.arange(len(y))
            
        # Make sure we have numpy arrays for consistent behavior
        x = np.array(x)
        y = np.array(y)
        
        # Debug output
        print(f"Plotting scatter with {len(x)} points. First few points: {list(zip(x[:5], y[:5]))}")
        
        # Convert RGBA to PyQtGraph format
        plot_color = tuple(c/255.0 for c in color[:3])
        plot_alpha = color[3]
        
        # Symbol settings
        symbol_map = {
            'o': 'o',  # circle
            's': 's',  # square
            't': 't',  # triangle
            'd': 'd',  # diamond
            '+': '+',  # plus
            'x': 'x'   # x
        }
        
        sym = symbol_map.get(symbol, 'o')
        
        # Create brush for symbol filling
        if brush is None:
            symbol_brush = pg.mkBrush(pg.mkColor(*plot_color, plot_alpha))
        else:
            symbol_brush = brush
        
        # Add the scatter plot (line pen set to None for scatter only)
        try:
            plot = self._plot_item.plot(x=x, y=y, name=name, pen=None,
                                       symbol=sym, symbolSize=symbol_size,
                                       symbolBrush=symbol_brush)
        except Exception as e:
            print(f"Error in standard plotting: {e}")
            # If that fails, try the alternate way by passing data directly
            plot = self._plot_item.plot(x, y, name=name, pen=None,
                                       symbol=sym, symbolSize=symbol_size,
                                       symbolBrush=symbol_brush)
        
        # Store plot for later reference
        self._data_items.append(plot)
        
        # Make sure autorange is enabled to show all data
        self._plot_item.enableAutoRange()
        
        return plot
    
    def add_bar_graph(self, x=None, height=None, width=0.8, name=None, color=(0, 0, 255, 1), 
                     brush=None, edge_color=None, label_rotation=0):
        """
        Add a bar graph to the plot.
        
        Args:
            x: X-axis positions for bars (array-like)
            height: Heights of bars (array-like)
            width: Width of bars (0-1)
            name: Name of the bar graph (for legend)
            color: Bar color as RGBA tuple
            brush: Optional custom brush for filling bars
            edge_color: Optional edge color for bars as RGBA tuple
            label_rotation: Rotation angle for x-axis labels
            
        Returns:
            Bar graph item for further customization
        """
        # Ensure we have height data
        if height is None:
            print("Error: No height data provided for bar graph")
            return None
            
        # Create default x values if not provided
        if x is None:
            x = np.arange(len(height))
        
        # Ensure data is properly formatted
        x = np.array(x, dtype=float)
        height = np.array(height, dtype=float)
        
        # Debug output
        print(f"Bar graph data: {len(x)} bars")
        print(f"X values: {x}")
        print(f"Heights: {height}")
        
        # Convert RGBA to PyQtGraph format
        bar_color = tuple(c/255.0 for c in color[:3])
        bar_alpha = color[3]
        
        # Create brush for bar filling
        if brush is None:
            bar_brush = pg.mkBrush(pg.mkColor(*bar_color, bar_alpha))
        else:
            bar_brush = brush
        
        # Create pen for bar edges
        if edge_color is None:
            # Default edge as slightly darker version of fill color
            edge_rgb = tuple(max(0, c-30) for c in color[:3])
            bar_pen = pg.mkPen(color=pg.mkColor(*(c/255.0 for c in edge_rgb), bar_alpha), width=1)
        else:
            edge_color_rgb = tuple(c/255.0 for c in edge_color[:3])
            edge_alpha = edge_color[3]
            bar_pen = pg.mkPen(color=pg.mkColor(*edge_color_rgb, edge_alpha), width=1)
        
        # Multiple approaches to create bar graphs
        bar_graph = None
        
        # Approach 1: Standard BarGraphItem
        try:
            print("Trying standard BarGraphItem")
            bar_graph = pg.BarGraphItem(x=x, height=height, width=width, brush=bar_brush, pen=bar_pen)
            self._plot_item.addItem(bar_graph)
        except Exception as e:
            print(f"Standard BarGraphItem error: {e}")
            
            # Approach 2: Simple approach with lists
            try:
                print("Trying BarGraphItem with list data")
                bar_graph = pg.BarGraphItem(x=x.tolist(), height=height.tolist(), width=width)
                self._plot_item.addItem(bar_graph)
            except Exception as e:
                print(f"List BarGraphItem error: {e}")
                
                # Approach 3: Manual bar creation using rectangle items
                try:
                    print("Creating bars manually using rectangle items")
                    bar_graph = pg.ItemGroup()
                    half_width = width/2
                    
                    for i, (xi, hi) in enumerate(zip(x, height)):
                        # Create rectangle for each bar
                        bar_rect = pg.QtGui.QGraphicsRectItem(xi-half_width, 0, width, hi)
                        bar_rect.setPen(bar_pen)
                        bar_rect.setBrush(bar_brush)
                        bar_graph.addToGroup(bar_rect)
                    
                    self._plot_item.addItem(bar_graph)
                except Exception as e:
                    print(f"Manual bar creation error: {e}")
        
        # Store for later reference
        if bar_graph:
            self._data_items.append(bar_graph)
            
            # Make sure autorange is enabled to show all data
            self._plot_item.enableAutoRange()
            
            # Set x-axis tick labels if needed
            if label_rotation != 0:
                self._plot_item.getAxis('bottom').setRotation(label_rotation)
            
            return bar_graph
        else:
            print("WARNING: Failed to create bar graph")
            return None
    
    def clear(self):
        """Clear all plots from the graph."""
        self._plot_item.clear()
        self._data_items = []
    
    def set_data(self, item_index, x=None, y=None):
        """
        Update data for an existing plot item.
        
        Args:
            item_index: Index of the item to update
            x: New x data
            y: New y data
        """
        if 0 <= item_index < len(self._data_items):
            plot_item = self._data_items[item_index]
            if isinstance(plot_item, pg.PlotDataItem):
                # For line or scatter plots
                if x is not None and y is not None:
                    plot_item.setData(x=x, y=y)
                elif y is not None:
                    if x is None:
                        x = np.arange(len(y))
                    plot_item.setData(x=x, y=y)
            elif isinstance(plot_item, pg.BarGraphItem):
                # For bar graphs
                if x is not None:
                    plot_item.setOpts(x=x)
                if y is not None:
                    plot_item.setOpts(height=y)
    
    # -----------------------------------------------------------------------
    # Timer Methods
    # -----------------------------------------------------------------------
    
    def _init_update_timer(self):
        """Initialize the timer for automatic updates."""
        if self._timer is None:
            self._timer = PvTimer(
                interval=self._update_interval,
                callback=self._timer_update
            )
            
    def _timer_update(self):
        """Update method called by the timer."""
        self.update()  # Use the existing update method
    
    def start_update_timer(self):
        """Start the timer for automatic updates."""
        self._init_update_timer()
        if not self._timer.is_active():
            self._timer.start()
            
    def stop_update_timer(self):
        """Stop the timer for automatic updates."""
        if self._timer and self._timer.is_active():
            self._timer.stop()
    
    @property
    def auto_update(self):
        """Get whether auto-update is enabled."""
        return self._auto_update
    
    @auto_update.setter
    def auto_update(self, value):
        """Set whether auto-update is enabled."""
        self._auto_update = value
        if value:
            self.start_update_timer()
        else:
            self.stop_update_timer()
    
    @property
    def update_interval(self):
        """Get the update interval in milliseconds."""
        return self._update_interval
    
    @update_interval.setter
    def update_interval(self, value):
        """Set the update interval in milliseconds."""
        self._update_interval = value
        if self._timer:
            self._timer.interval = value
    
    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    
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
        self.setFixedSize(self._width, self._height)
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, value):
        self._height = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)
    
    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, value):
        self._title = value
        self._plot_item.setTitle(value)
    
    @property
    def x_label(self):
        return self._x_label
    
    @x_label.setter
    def x_label(self, value):
        self._x_label = value
        self._plot_item.setLabel('bottom', value)
    
    @property
    def y_label(self):
        return self._y_label
    
    @y_label.setter
    def y_label(self, value):
        self._y_label = value
        self._plot_item.setLabel('left', value)
    
    @property
    def background_color(self):
        return self._background_color
    
    @background_color.setter
    def background_color(self, color):
        self._background_color = color
        # Convert RGBA to PyQtGraph format
        bg_color = tuple(c/255.0 for c in color[:3])
        bg_alpha = color[3]
        # Apply the background color directly
        try:
            self._plot_widget.setBackground(pg.mkColor(*bg_color, bg_alpha))
            # Also try brush method for better compatibility
            brush = pg.mkBrush(pg.mkColor(*bg_color, bg_alpha))
            if hasattr(self._plot_widget, 'setBackgroundBrush'):
                self._plot_widget.setBackgroundBrush(brush)
        except Exception as e:
            print(f"Error updating background color: {e}")
    
    @property
    def axis_color(self):
        return self._axis_color
    
    @axis_color.setter
    def axis_color(self, color):
        self._axis_color = color
        axis_color = tuple(c/255.0 for c in color[:3])
        axis_alpha = color[3]
        axis_pen = pg.mkPen(color=pg.mkColor(*axis_color, axis_alpha), width=1)
        for ax in ['left', 'bottom', 'top', 'right']:
            axis = self._plot_item.getAxis(ax)
            axis.setPen(axis_pen)
    
    @property
    def grid(self):
        return self._grid
    
    @grid.setter
    def grid(self, value):
        self._grid = value
        self._plot_item.showGrid(x=value, y=value, alpha=self._grid_alpha)
    
    @property
    def grid_color(self):
        return self._grid_color
    
    @grid_color.setter
    def grid_color(self, color):
        self._grid_color = color
        if self._grid:
            grid_color = tuple(c/255.0 for c in color[:3])
            grid_pen = pg.mkPen(color=pg.mkColor(*grid_color, self._grid_alpha), width=1)
            
            # Re-show the grid with our desired alpha
            self._plot_item.showGrid(x=self._grid, y=self._grid, alpha=self._grid_alpha)
            
            # Simple approach: just recreate the grid
            self._configure_style()
    
    @property
    def grid_alpha(self):
        return self._grid_alpha
    
    @grid_alpha.setter
    def grid_alpha(self, value):
        self._grid_alpha = value
        if self._grid:
            # Re-show the grid with the new alpha
            self._plot_item.showGrid(x=self._grid, y=self._grid, alpha=value)
            
            # Simple approach: just recreate the grid with the new settings
            self._configure_style()
    
    @property
    def legend(self):
        return self._legend
    
    @legend.setter
    def legend(self, value):
        if value != self._legend:
            self._legend = value
            if value:
                self._plot_item.addLegend()
            else:
                # Remove legend if it exists
                if self._plot_item.legend is not None:
                    self._plot_item.legend.scene().removeItem(self._plot_item.legend)
                    self._plot_item.legend = None
    
    @property
    def crosshair(self):
        return self._crosshair
    
    @crosshair.setter
    def crosshair(self, value):
        self._crosshair = value
        if value:
            self._plot_widget.setCursor(Qt.CrossCursor)
        else:
            self._plot_widget.setCursor(Qt.ArrowCursor)
    
    @property
    def x_range(self):
        return self._x_range
    
    @x_range.setter
    def x_range(self, value):
        if value and len(value) == 2:
            self._x_range = value
            self._plot_item.setXRange(value[0], value[1])
        else:
            self._x_range = None
            self._plot_item.autoRange()
    
    @property
    def y_range(self):
        return self._y_range
    
    @y_range.setter
    def y_range(self, value):
        if value and len(value) == 2:
            self._y_range = value
            self._plot_item.setYRange(value[0], value[1])
        else:
            self._y_range = None
            self._plot_item.autoRange()
    
    @property
    def log_x(self):
        return self._log_x
    
    @log_x.setter
    def log_x(self, value):
        self._log_x = value
        self._plot_item.setLogMode(x=value, y=self._log_y)
    
    @property
    def log_y(self):
        return self._log_y
    
    @log_y.setter
    def log_y(self, value):
        self._log_y = value
        self._plot_item.setLogMode(x=self._log_x, y=value)
    
    @property
    def anti_aliasing(self):
        return self._anti_aliasing
    
    @anti_aliasing.setter
    def anti_aliasing(self, value):
        self._anti_aliasing = value
        pg.setConfigOptions(antialias=value)
    
    @property
    def border_width(self):
        return self._border_width
    
    @border_width.setter
    def border_width(self, value):
        self._border_width = value
        self.setStyleSheet(f"""
            QWidget {{
                border: {value}px solid black;
                border-radius: {self._corner_radius}px;
            }}
        """)
    
    @property
    def corner_radius(self):
        return self._corner_radius
    
    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        self.setStyleSheet(f"""
            QWidget {{
                border: {self._border_width}px solid black;
                border-radius: {value}px;
            }}
        """)
    
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
    
    @property
    def tag(self):
        return self._tag
    
    @tag.setter
    def tag(self, value):
        self._tag = value


# Example usage
if __name__ == "__main__":
    import pyvisual as pv
    import numpy as np
    import sys
    import random
    import time
    from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
    
    app = pv.PvApp()
    window = pv.PvWindow(title="PyVisual Graph Auto-Update Demo", is_resizable=True)
    window.resize(1000, 800)
    
    # Create a container for additional controls
    control_widget = QWidget(window)
    control_widget.setGeometry(50, 50, 900, 100)
    control_layout = QVBoxLayout(control_widget)
    
    # Add explanation labels
    title_label = QLabel("Auto-Update Feature Demonstration")
    title_label.setFont(QFont("Arial", 16, QFont.Bold))
    title_label.setAlignment(Qt.AlignCenter)
    control_layout.addWidget(title_label)
    
    explanation = QLabel(
        "The counter below increases every 50ms (20 times per second)\n"
        "Top graph (auto_update=FALSE): Updates ONLY when you click 'Force Update'\n"
        "Bottom graph (auto_update=TRUE): Updates automatically every 500ms"
    )
    explanation.setAlignment(Qt.AlignCenter)
    explanation.setFont(QFont("Arial", 10))
    control_layout.addWidget(explanation)
    
    # Add button row
    button_container = QWidget()
    button_layout = QHBoxLayout(button_container)
    
    # Counter display
    counter_label = QLabel("Counter: 0")
    counter_label.setFont(QFont("Arial", 12, QFont.Bold))
    counter_label.setAlignment(Qt.AlignCenter)
    counter_label.setStyleSheet("color: blue;")
    button_layout.addWidget(counter_label)
    
    # Force update button
    update_button = QPushButton("Force Update Graph 1")
    update_button.setStyleSheet("background-color: #ffcccc; font-weight: bold; padding: 8px;")
    button_layout.addWidget(update_button)
    
    # Status indicators
    status_label1 = QLabel("WAITING FOR MANUAL UPDATE")
    status_label1.setStyleSheet("color: red; font-weight: bold;")
    status_label1.setAlignment(Qt.AlignCenter)
    button_layout.addWidget(status_label1)
    
    status_label2 = QLabel("AUTO UPDATING")
    status_label2.setStyleSheet("color: green; font-weight: bold;")
    status_label2.setAlignment(Qt.AlignCenter)
    button_layout.addWidget(status_label2)
    
    control_layout.addWidget(button_container)
    
    # Create graph with auto_update OFF
    graph1 = PvGraph(window, x=50, y=180, width=900, height=280,
                   title="Graph 1: auto_update=False (Manual Updates Only)",
                   x_label="Time", y_label="Values",
                   background_color=(255, 220, 220, 1),  # Light red
                   grid=True, legend=True, auto_update=False, update_interval=500)
    
    # Create graph with auto_update ON
    graph2 = PvGraph(window, x=50, y=480, width=900, height=280,
                   title="Graph 2: auto_update=True (Updates Every 500ms)",
                   x_label="Time", y_label="Values",
                   background_color=(220, 255, 220, 1),  # Light green
                   grid=True, legend=True, auto_update=True, update_interval=500)
    
    # Create data buffers - we'll use a simple list for direct access
    data_points = 50
    x_data = list(range(data_points))
    sine_data = [0] * data_points
    random_data = [0] * data_points
    
    # Create the plots
    line1_g1 = graph1._plot_item.plot(x=x_data, y=sine_data, name="Sine Wave", 
                                    pen=pg.mkPen(color=(255, 0, 0), width=2))
    line2_g1 = graph1._plot_item.plot(x=x_data, y=random_data, name="Random Data", 
                                    pen=pg.mkPen(color=(0, 0, 255), width=2))
    
    # Similar plots for graph 2
    line1_g2 = graph2._plot_item.plot(x=x_data, y=sine_data, name="Sine Wave", 
                                    pen=pg.mkPen(color=(255, 0, 0), width=2))
    line2_g2 = graph2._plot_item.plot(x=x_data, y=random_data, name="Random Data", 
                                    pen=pg.mkPen(color=(0, 0, 255), width=2))
    
    # Store the last update times
    last_data_update = time.time()
    last_graph1_update = time.time()
    last_graph2_update = time.time()
    counter = 0
    
    # This demonstrates the key difference:
    # With auto_update=False, we need to manually trigger the update
    # With auto_update=True, the graph refreshes automatically
    
    # Create data update function
    def update_data():
        global counter, last_data_update, sine_data, random_data
        current_time = time.time()
        
        # Update the counter
        counter += 1
        counter_label.setText(f"Counter: {counter}")
        
        # Update the data values
        sine_data.pop(0)
        sine_data.append(np.sin(counter * 0.1) * 0.8)
        
        random_data.pop(0)
        random_data.append(random.uniform(-0.8, 0.8))
        
        # These are critical lines - for both graphs, we directly update
        # the plot data but DON'T call setData() which forces a redraw
        line1_g1.setData(x=x_data, y=sine_data)
        line2_g1.setData(x=x_data, y=random_data)
        line1_g2.setData(x=x_data, y=sine_data)
        line2_g2.setData(x=x_data, y=random_data)
        
        # We're deliberately NOT calling graph1.update() here
        # Graph1 will only update when the button is clicked
        # Graph2 will update automatically due to its timer
    
    # Start data timer (updates data but not display)
    data_timer = PvTimer(interval=50, callback=update_data)
    data_timer.start()
    
    # Connect the update button to manually update graph1
    def force_update_graph1():
        global last_graph1_update
        graph1.update()  # Force a redraw
        last_graph1_update = time.time()
        
        # Update status indicator
        status_label1.setText("UPDATED NOW!")
        status_label1.setStyleSheet("color: red; font-weight: bold; background-color: yellow;")
        
        # Reset after a moment
        def reset_status():
            status_label1.setText("WAITING FOR MANUAL UPDATE")
            status_label1.setStyleSheet("color: red; font-weight: bold;")
            
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, reset_status)
    
    update_button.clicked.connect(force_update_graph1)
    
    # For graph2, update its status label when auto-update fires
    original_timer_update = graph2._timer_update
    
    def custom_timer_update():
        global last_graph2_update
        # Call the original update method
        original_timer_update()
        
        # Update the status
        last_graph2_update = time.time()
        status_label2.setText("UPDATED NOW!")
        status_label2.setStyleSheet("color: green; font-weight: bold; background-color: yellow;")
        
        # Reset after a moment
        def reset_status():
            status_label2.setText("AUTO UPDATING")
            status_label2.setStyleSheet("color: green; font-weight: bold;")
            
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, reset_status)
    
    # Replace the timer update method with our custom one
    graph2._timer_update = custom_timer_update
    
    # Make sure both graphs are visible
    graph1.setVisible(True)
    graph2.setVisible(True)
    
    window.show()
    app.run()
