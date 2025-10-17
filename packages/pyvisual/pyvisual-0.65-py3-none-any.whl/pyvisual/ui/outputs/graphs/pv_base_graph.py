from PySide6.QtCore import Qt, Signal, Property, QThread, QMutex, QWaitCondition, QTimer, QRectF, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QGraphicsDropShadowEffect, QFrame, QGraphicsView, QGraphicsScene
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QRegion
from queue import Queue
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pyqtgraph as pg
    import numpy as np

# Global variables to hold our lazy-loaded modules.
_pg: Optional["pg"] = None
_np: Optional["np"] = None

def get_pg():
    """Lazily load and return the pyqtgraph module."""
    global _pg
    if _pg is None:
        import pyqtgraph as pg_module
        _pg = pg_module
    return _pg

def get_np():
    """Lazily load and return the numpy module."""
    global _np
    if _np is None:
        import numpy as np_module
        _np = np_module
    return _np

# Thread class for handling graph updates in the background
class GraphUpdateThread(QThread):
    """Thread for handling graph updates without blocking the UI thread"""
    
    # Signal emitted when data needs to be updated on the UI thread
    updateSignal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._condition = QWaitCondition()
        self._running = True
        self._data_queue = Queue()
        self._update_interval = 16  # Default: ~60fps (16ms)
        
    def run(self):
        """Main thread loop"""
        while self._running:
            # Process all queued updates
            if not self._data_queue.empty():
                # Data is available, emit signal to update in UI thread
                self.updateSignal.emit()
                
            # Sleep to prevent excessive CPU usage
            time.sleep(self._update_interval / 1000.0)
            
    def enqueue_update(self, update_function, *args, **kwargs):
        """Add an update operation to the queue"""
        self._data_queue.put((update_function, args, kwargs))
        
    def get_next_update(self):
        """Get the next update from the queue if available"""
        if not self._data_queue.empty():
            return self._data_queue.get()
        return None
        
    def stop(self):
        """Stop the thread safely"""
        self._running = False
        self._condition.wakeAll()
        self.wait()
        
    def set_update_interval(self, interval_ms):
        """Set the update interval in milliseconds"""
        self._update_interval = max(1, interval_ms)  # Ensure minimum 1ms

class RoundedGraphFrame(QFrame):
    """Custom frame with rounded corners that properly clips its contents"""
    
    def __init__(self, parent=None, corner_radius=0, border_thickness=0):
        super().__init__(parent)
        self.corner_radius = corner_radius
        self.border_thickness = border_thickness
        self.setObjectName("roundedGraphFrame")
        # Use QFrame's built-in frame functionality
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(border_thickness)
        
        # Essential for proper rendering of rounded corners
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def setFrameWidth(self, width):
        """Set the frame border thickness"""
        self.border_thickness = width
        # Use QFrame's built-in method
        self.setLineWidth(width)
    
    def paintEvent(self, event):
        """Override paint event to create rounded corners with proper clipping"""
        painter = QPainter(self)
        # This is critical for smooth corners
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        
        # Get background color from palette
        background = self.palette().color(self.backgroundRole())
        
        # Draw the rounded rectangle background
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # Set proper composition mode for high-quality rendering
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        
        # Fill with background color
        painter.fillPath(path, background)
        
        # If we have a border, draw it as well
        if self.border_thickness > 0:
            # Draw border using QPainter directly (more control)
            pen = QPen(self.palette().color(self.foregroundRole()))
            pen.setWidth(self.border_thickness)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            
            # Adjust the rectangle to account for pen width properly
            # We want to draw inside the frame to prevent overlap with content
            inset = self.border_thickness
            adjusted_rect = rect.adjusted(
                inset / 2, 
                inset / 2, 
                -inset / 2, 
                -inset / 2
            )
            
            # Draw the border with properly adjusted corner radius
            adjusted_radius = max(0, self.corner_radius - inset / 2)
            painter.drawRoundedRect(
                adjusted_rect, 
                adjusted_radius, 
                adjusted_radius
            )
        
        # Set clip path to ensure content doesn't extend outside the rounded corners
        painter.setClipPath(path)
    
    def resizeEvent(self, event):
        """Override resize event to ensure proper painting on resize"""
        super().resizeEvent(event)
        self.update()

class PvBaseGraph(QWidget):
    """
    A base class for customizable graph widgets based on PyQtGraph.
    Provides common functionality for all types of plots.
    """
    
    def __init__(self, container, x=100, y=100, width=400, height=300, 
                 title="", x_label="", y_label="", 
                 background_color=(255, 255, 255, 1), axis_color=(0, 0, 0, 1),
                 grid=True, grid_color=(200, 200, 200, 1), grid_alpha=0.5,
                 legend=False, crosshair=False, 
                 x_range=None, y_range=None, log_x=False, log_y=False,
                 anti_aliasing=True, border_thickness=0, corner_radius=50,
                 border_color=None, is_visible=True, opacity=1.0, tag=None, 
                 is_dynamic=False, update_interval=16, **kwargs):
        """
        Initialize a base graph widget with customizable properties.
        
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
            border_thickness: Border thickness of the graph widget
            corner_radius: Corner radius of the graph widget
            border_color: Border color as RGBA tuple (if None, a darker shade of background color is used)
            is_visible: Whether the widget is initially visible
            opacity: Widget opacity (0-1)
            tag: Optional user-defined tag for identification
            is_dynamic: Whether to use a background thread for graph updates
            update_interval: Interval between graph updates in milliseconds
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
        self._border_thickness = border_thickness
        self._corner_radius = corner_radius
        self._border_color = border_color
        
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
        # Threading properties
        # --------------------------------------------------------------------
        self._is_dynamic = is_dynamic
        self._update_interval = update_interval
        self._update_thread = None
        self._update_timer = None
        
        # Initialize the layout and graph
        self._init_ui()
        
        # Force background color to be applied after setup
        self._force_background_update()
        
        self._configure_style()
        
        # Set up threading if enabled
        if self._is_dynamic:
            self._setup_threading()
    
    def _init_ui(self):
        """Initialize the UI components and layout."""
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)
        
        # Create main layout with zero margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Set up the parent widget to be transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create the rounded corner frame with our custom class
        self._container_frame = RoundedGraphFrame(self, 
                                                 corner_radius=self._corner_radius,
                                                 border_thickness=self._border_thickness)
        
        # Calculate padding based on corner radius to keep content away from edges
        # Use asymmetric padding with less on the left
        # Use larger padding when corner_radius is larger to prevent content from overlapping with rounded corners
        corner_factor = 0.5  # Increase this factor for more padding
        right_padding = max(5, int(self._corner_radius * corner_factor))
        top_padding = max(5, int(self._corner_radius * corner_factor))
        bottom_padding = max(5, int(self._corner_radius * corner_factor))
        left_padding = max(2, int(self._corner_radius * 0.25))  # Reduced left padding
        
        # Create a layout for the container frame with asymmetric padding
        frame_layout = QVBoxLayout(self._container_frame)
        frame_layout.setContentsMargins(left_padding, top_padding, right_padding, bottom_padding)
        frame_layout.setSpacing(0)
        
        # Get pyqtgraph module
        pg = get_pg()
        
        # Create PyQtGraph plot widget
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setAttribute(Qt.WA_NoSystemBackground)
        self._plot_widget.setAttribute(Qt.WA_TranslucentBackground)
        
        # Format axis items with asymmetric margins - less on the left
        # Right and bottom margins
        right_margin = max(2, int(self._corner_radius * 0.25))
        bottom_margin = max(2, int(self._corner_radius * 0.25))
        # Left margin (reduced)
        left_margin = max(0, int(self._corner_radius * 0.1))
        # Top margin
        top_margin = max(2, int(self._corner_radius * 0.25))
        
        # Set axis height/width with reasonable defaults
        self._plot_widget.getPlotItem().getAxis('bottom').setHeight(25)
        self._plot_widget.getPlotItem().getAxis('bottom').setContentsMargins(left_margin, 0, right_margin, 0)
        self._plot_widget.getPlotItem().getAxis('left').setWidth(40)  # Narrower left axis
        self._plot_widget.getPlotItem().getAxis('left').setContentsMargins(0, top_margin, 0, bottom_margin)
        
        # Use asymmetric plot content margins
        self._plot_widget.getPlotItem().setContentsMargins(left_margin, top_margin, 
                                                          right_margin, bottom_margin)
        
        # Add plot widget to frame layout
        frame_layout.addWidget(self._plot_widget)
        
        # Add container to main layout
        main_layout.addWidget(self._container_frame)
        
        # Get the plot item for customization
        self._plot_item = self._plot_widget.getPlotItem()
        
        # Configure crosshair
        # Use a high-contrast pen that will be visible on any background
        crosshair_pen = pg.mkPen(color=(255, 255, 255), width=1, style=Qt.DashLine)
        self._vertical_line = pg.InfiniteLine(angle=90, movable=False, pen=crosshair_pen)
        self._horizontal_line = pg.InfiniteLine(angle=0, movable=False, pen=crosshair_pen) 
        self._crosshair_visible = False
        
        # Set up crosshair behavior if needed
        if self._crosshair:
            self._setup_crosshair()
        
        # Configure standard plot properties
        if self._title:
            self._plot_item.setTitle(self._title)
        if self._x_label:
            self._plot_item.setLabel('bottom', self._x_label)
        if self._y_label:
            self._plot_item.setLabel('left', self._y_label)
        
        # Configure legend
        if self._legend:
            self._plot_item.addLegend()
        
        # Configure axis ranges
        if self._x_range:
            self._plot_item.setXRange(self._x_range[0], self._x_range[1], padding=0)
            # Disable auto-ranging on x-axis
            self._plot_item.getViewBox().setAutoVisible(x=False)
            self._plot_item.getViewBox().enableAutoRange(x=False)
        if self._y_range:
            self._plot_item.setYRange(self._y_range[0], self._y_range[1], padding=0)
            # Disable auto-ranging on y-axis
            self._plot_item.getViewBox().setAutoVisible(y=False)
            self._plot_item.getViewBox().enableAutoRange(y=False)
        
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
        
        # Apply initial styling
        self._configure_style()
    
    def _force_background_update(self):
        """Force background color to be applied to all components"""
        if not hasattr(self, '_plot_widget'):
            return
            
        # Get pyqtgraph module
        pg = get_pg()
            
        # Extract RGB components and convert to 0-1 range for PyQtGraph
        r, g, b = [c/255.0 for c in self._background_color[:3]]
        a = self._background_color[3]
        
        # Try multiple methods to set the background color
        # Method 1: Using PyQtGraph's direct method
        self._plot_widget.setBackground((r, g, b, a))
        
        # Method 2: Using QColor with PlotWidget's API
        qcolor = QColor(int(r*255), int(g*255), int(b*255), int(a*255))
        if hasattr(self._plot_widget, 'setBackgroundColor'):
            self._plot_widget.setBackgroundColor(qcolor)
            
        # Method 3: Set style sheet directly on the widget
        css_color = f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {int(a*255)})"
        self._plot_widget.setStyleSheet(f"background-color: {css_color};")
        
        # Method 4: Set palette
        palette = self._plot_widget.palette()
        palette.setColor(self._plot_widget.backgroundRole(), qcolor)
        self._plot_widget.setPalette(palette)
        self._plot_widget.setAutoFillBackground(True)
        
        # Method 5: ViewBox background
        try:
            viewbox = self._plot_widget.getPlotItem().getViewBox()
            if viewbox:
                viewbox.setBackgroundColor((r, g, b, a))
        except:
            pass
        
        # Force immediate update
        self._plot_widget.update()
    
    def _configure_style(self):
        """Configure the visual style of the graph."""
        # Get pyqtgraph module
        pg = get_pg()
        
        # Apply all other styles
        # Apply background color to the frame
        self._apply_background_color()
        
        # Convert RGBA to PyQtGraph format for other elements
        axis_color = tuple(c/255.0 for c in self._axis_color[:3])
        axis_alpha = self._axis_color[3]
        
        grid_color = tuple(c/255.0 for c in self._grid_color[:3])
        
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
            
            # Try to set the grid pen via getAxis
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
                # Fallback
                pass
            
            # Set axis grid visibility
            self._plot_widget.getPlotItem().getAxis('left').setGrid(self._grid_alpha)
            self._plot_widget.getPlotItem().getAxis('bottom').setGrid(self._grid_alpha)
        else:
            # Explicitly hide grid when grid=False
            self._plot_item.showGrid(x=False, y=False)
            
            # Also disable grid on each axis
            try:
                self._plot_item.getAxis('left').grid = False
                self._plot_item.getAxis('bottom').grid = False
                
                # Make sure gridLines are hidden
                for axis in ['left', 'bottom']:
                    grid_lines = self._plot_item.getAxis(axis).gridLines
                    if len(grid_lines) > 0:
                        for line in grid_lines:
                            line.setVisible(False)
                            
                # Explicitly set grid off on axis
                self._plot_widget.getPlotItem().getAxis('left').setGrid(False)
                self._plot_widget.getPlotItem().getAxis('bottom').setGrid(False)
            except:
                # Fallback
                pass
        
        # Set widget visibility and opacity
        self.setVisible(self._is_visible)
        self.setWindowOpacity(self._opacity)
        
        # Update the corner radius and border thickness on the container
        self._container_frame.corner_radius = self._corner_radius
        self._container_frame.border_thickness = self._border_thickness
        
        # Set proper border frame color
        if self._border_thickness > 0:
            border_color = None
            
            # Use specified border color if provided
            if self._border_color is not None:
                r_border, g_border, b_border = self._border_color[:3]
                bg_alpha = self._border_color[3] if len(self._border_color) >= 4 else 1.0
            else:
                # Otherwise create a slightly darker color from the background
                bg_color = tuple(c/255.0 for c in self._background_color[:3])
                bg_alpha = self._background_color[3]
                
                # Create a slightly darker color for the border
                r_border, g_border, b_border = [max(0, min(255, int(c * 0.8 * 255))) for c in bg_color]
            
            # Set the frame properties
            palette = self._container_frame.palette()
            palette.setColor(self._container_frame.foregroundRole(), QColor(r_border, g_border, b_border, int(bg_alpha * 255)))
            self._container_frame.setPalette(palette)
            
            # Use the custom method instead
            self._container_frame.setFrameWidth(self._border_thickness)
        
        # Force background color to be applied again after all styling
        self._force_background_update()
    
    def _apply_background_color(self):
        """Apply the background color to all elements of the widget"""
        # Get pyqtgraph module
        pg = get_pg()
        
        # Extract RGB components (0-255) and alpha (0-1)
        r, g, b = self._background_color[:3]
        alpha = self._background_color[3]
        
        # Create QColor
        qt_color = QColor(r, g, b, int(alpha * 255))
        
        # Apply to container frame
        palette = self._container_frame.palette()
        palette.setColor(self._container_frame.backgroundRole(), qt_color)
        self._container_frame.setPalette(palette)
        
        # Apply to plot widget - need to convert to normalized [0-1] for pyqtgraph
        bg_color_norm = tuple(c/255.0 for c in (r, g, b))
        # Use PyQtGraph's method to set the background
        self._plot_widget.setBackground(pg.mkColor(*bg_color_norm, alpha))
        
        # Also apply to viewbox if available
        viewbox = self._plot_item.getViewBox()
        if viewbox:
            viewbox.setBackgroundColor(pg.mkColor(*bg_color_norm, alpha))
        
        # Force update to ensure changes are shown
        self._container_frame.update()
        self._plot_widget.update()
    
    # -----------------------------------------------------------------------
    # Threading Methods
    # -----------------------------------------------------------------------
    
    def _setup_threading(self):
        """Set up the background thread for graph updates"""
        if self._update_thread is None:
            # Create and start the update thread
            self._update_thread = GraphUpdateThread(self)
            self._update_thread.updateSignal.connect(self._process_queued_updates)
            self._update_thread.set_update_interval(self._update_interval)
            self._update_thread.start()
            
            # Create a timer for polling updates at a fixed rate
            self._update_timer = QTimer(self)
            self._update_timer.timeout.connect(self._check_for_updates)
            self._update_timer.start(self._update_interval)
    
    def _process_queued_updates(self):
        """Process any queued updates in the UI thread"""
        if self._update_thread:
            update_data = self._update_thread.get_next_update()
            while update_data:
                # Unpack the update function and arguments
                update_function, args, kwargs = update_data
                
                # Execute the update function in the UI thread
                update_function(*args, **kwargs)
                
                # Get the next update if available
                update_data = self._update_thread.get_next_update()
    
    def _check_for_updates(self):
        """Check if there are any updates to process"""
        if self._update_thread and not self._update_thread.isRunning():
            # Restart the thread if it stopped for some reason
            self._update_thread.start()
    
    def set_dynamic_updates(self, enabled):
        """Enable or disable dynamic (threaded) updates"""
        if enabled != self._is_dynamic:
            self._is_dynamic = enabled
            
            if enabled:
                # Start threading if it wasn't already enabled
                self._setup_threading()
            else:
                # Stop threading if it was enabled
                if self._update_thread:
                    self._update_thread.stop()
                    self._update_thread = None
                
                if self._update_timer:
                    self._update_timer.stop()
                    self._update_timer = None
    
    def set_update_interval(self, interval_ms):
        """Set the update interval in milliseconds"""
        self._update_interval = max(1, interval_ms)  # Ensure minimum 1ms
        
        if self._update_thread:
            self._update_thread.set_update_interval(self._update_interval)
        
        if self._update_timer:
            self._update_timer.setInterval(self._update_interval)
    
    def queue_update(self, update_function, *args, **kwargs):
        """Queue an update to be processed in the background thread"""
        if self._is_dynamic and self._update_thread:
            self._update_thread.enqueue_update(update_function, *args, **kwargs)
            return True
        else:
            # If threading is disabled, execute immediately
            update_function(*args, **kwargs)
            return False
    
    # -----------------------------------------------------------------------
    # Common Methods
    # -----------------------------------------------------------------------
    
    def update(self):
        """Force update of the plot widget to ensure data is displayed."""
        if self._is_dynamic:
            self.queue_update(self._do_update)
        else:
            self._do_update()
    
    def _do_update(self):
        """Actual implementation of the update that runs in the UI thread"""
        from PySide6.QtWidgets import QApplication
        if hasattr(self, '_plot_widget'):
            # Check if we need to enforce fixed ranges
            if self._y_range is not None:
                self._plot_item.getViewBox().enableAutoRange(y=False)
                self._plot_item.setYRange(self._y_range[0], self._y_range[1], padding=0)
            
            if self._x_range is not None:
                self._plot_item.getViewBox().enableAutoRange(x=False)
                self._plot_item.setXRange(self._x_range[0], self._x_range[1], padding=0)
            
            self._plot_widget.update()
            QApplication.processEvents()
            
    def redraw(self):
        """Force a complete redraw of the graph and all its data."""
        if self._is_dynamic:
            self.queue_update(self._do_redraw)
        else:
            self._do_redraw()
    
    def _do_redraw(self):
        """Actual implementation of the redraw that runs in the UI thread"""
        from PySide6.QtWidgets import QApplication
        
        if hasattr(self, '_plot_widget'):
            # Make sure items are visible
            for item in self._data_items:
                if hasattr(item, 'setVisible'):
                    item.setVisible(True)
            
            # Force the plotItem to redraw
            if hasattr(self, '_plot_item') and self._plot_item is not None:
                # Don't reset view limits if fixed ranges are set
                if self._x_range is None and self._y_range is None:
                    self._plot_item.enableAutoRange()
                else:
                    # Selectively enable auto-range based on settings
                    viewBox = self._plot_item.getViewBox()
                    if viewBox:
                        if self._x_range is None:
                            viewBox.enableAutoRange(x=True)
                        else:
                            viewBox.enableAutoRange(x=False)
                            self._plot_item.setXRange(self._x_range[0], self._x_range[1], padding=0)
                            
                        if self._y_range is None:
                            viewBox.enableAutoRange(y=True)
                        else:
                            viewBox.enableAutoRange(y=False)
                            self._plot_item.setYRange(self._y_range[0], self._y_range[1], padding=0)
                
                # Force view to update
                view_box = self._plot_item.getViewBox()
                if view_box:
                    view_box.update()
            
            # Force the widget to update
            self._plot_widget.update()
            QApplication.processEvents()
    
    def clear(self):
        """Clear all plots from the graph."""
        if self._is_dynamic:
            self.queue_update(self._do_clear)
        else:
            self._do_clear()
    
    def _do_clear(self):
        """Actual implementation of clear that runs in the UI thread"""
        self._plot_item.clear()
        self._data_items = []
    
    # -----------------------------------------------------------------------
    # Override closeEvent to properly clean up threads
    # -----------------------------------------------------------------------
    
    def closeEvent(self, event):
        """Clean up resources when the widget is closed"""
        # Stop the update thread if it's running
        if self._update_thread:
            self._update_thread.stop()
        
        # Stop the timer if it's running
        if self._update_timer:
            self._update_timer.stop()
        
        # Let the base class handle the rest
        super().closeEvent(event)
    
    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    
    @property
    def is_dynamic(self):
        return self._is_dynamic
    
    @is_dynamic.setter
    def is_dynamic(self, value):
        self.set_dynamic_updates(value)
    
    @property
    def update_interval(self):
        return self._update_interval
    
    @update_interval.setter
    def update_interval(self, value):
        self.set_update_interval(value)
    
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
        
        # Apply the background color immediately
        if hasattr(self, '_plot_widget'):
            self._force_background_update()
    
    @property
    def axis_color(self):
        return self._axis_color
    
    @axis_color.setter
    def axis_color(self, color):
        self._axis_color = color
        pg = get_pg()
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
        self._plot_item.showGrid(x=value, y=value, alpha=self._grid_alpha if value else 0)
        
        # Reconfigure to ensure grid lines are properly shown/hidden
        self._configure_style()
    
    @property
    def grid_color(self):
        return self._grid_color
    
    @grid_color.setter
    def grid_color(self, color):
        self._grid_color = color
        if self._grid:
            pg = get_pg()
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
        if value != self._crosshair:
            self._crosshair = value
            if value:
                self._setup_crosshair()
                self._plot_widget.setCursor(Qt.CrossCursor)
            else:
                # Hide crosshair lines if they exist
                if hasattr(self, '_vertical_line'):
                    self._vertical_line.setVisible(False)
                    self._horizontal_line.setVisible(False)
                    self._crosshair_visible = False
                self._plot_widget.setCursor(Qt.ArrowCursor)
    
    @property
    def x_range(self):
        return self._x_range
    
    @x_range.setter
    def x_range(self, value):
        if value and len(value) == 2:
            self._x_range = value
            
            # Disable auto-ranging and set fixed x-range
            if hasattr(self, '_plot_item'):
                self._plot_item.setXRange(value[0], value[1], padding=0)
                self._plot_item.getViewBox().setAutoVisible(x=False)
                self._plot_item.getViewBox().enableAutoRange(x=False)
        else:
            self._x_range = None
            
            # Enable auto-ranging again
            if hasattr(self, '_plot_item'):
                self._plot_item.getViewBox().enableAutoRange(x=True)
                self._plot_item.getViewBox().setAutoVisible(x=True)
            self._plot_item.autoRange()
    
    @property
    def y_range(self):
        return self._y_range
    
    @y_range.setter
    def y_range(self, value):
        if value and len(value) == 2:
            self._y_range = value
            
            # Disable auto-ranging and set fixed y-range
            if hasattr(self, '_plot_item'):
                self._plot_item.setYRange(value[0], value[1], padding=0)
                self._plot_item.getViewBox().setAutoVisible(y=False)
                self._plot_item.getViewBox().enableAutoRange(y=False)
        else:
            self._y_range = None
            
            # Enable auto-ranging again
            if hasattr(self, '_plot_item'):
                self._plot_item.getViewBox().enableAutoRange(y=True)
                self._plot_item.getViewBox().setAutoVisible(y=True)
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
        pg = get_pg()
        pg.setConfigOptions(antialias=value)
    
    @property
    def border_thickness(self):
        return self._border_thickness
    
    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value
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
        old_value = self._corner_radius
        self._corner_radius = value
        
        # Update corner radius on container frame if it exists
        if hasattr(self, '_container_frame'):
            # Update the corner radius
            self._container_frame.corner_radius = value
            
            # If the layout exists and padding needs to be updated
            if value != old_value and hasattr(self, '_container_frame'):
                # Recalculate padding with asymmetric values (less on the left)
                corner_factor = 0.5  # Increase this factor for more padding
                right_padding = max(5, int(value * corner_factor))
                top_padding = max(5, int(value * corner_factor))
                bottom_padding = max(5, int(value * corner_factor))
                left_padding = max(2, int(value * 0.25))  # Reduced left padding
                
                # Calculate axis margins - less on the left
                right_margin = max(2, int(value * 0.25))
                bottom_margin = max(2, int(value * 0.25))
                left_margin = max(0, int(value * 0.1))   # Reduced left margin
                top_margin = max(2, int(value * 0.25))
                
                # Get the layout and update margins
                layout = self._container_frame.layout()
                if layout:
                    layout.setContentsMargins(left_padding, top_padding, right_padding, bottom_padding)
                
                # Update plot margins if available
                if hasattr(self, '_plot_widget'):
                    self._plot_widget.getPlotItem().getAxis('bottom').setContentsMargins(left_margin, 0, right_margin, 0)
                    self._plot_widget.getPlotItem().getAxis('left').setContentsMargins(0, top_margin, 0, bottom_margin)
                    self._plot_widget.getPlotItem().setContentsMargins(left_margin, top_margin, 
                                                                      right_margin, bottom_margin)
            
            # Force a repaint
            self._container_frame.update()
    
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
    
    @property
    def border_color(self):
        return self._border_color
    
    @border_color.setter
    def border_color(self, color):
        self._border_color = color

    def _setup_crosshair(self):
        """Set up the crosshair functionality"""
        # Add the crosshair lines to the plot but initially make them invisible
        self._plot_item.addItem(self._vertical_line)
        self._plot_item.addItem(self._horizontal_line)
        self._vertical_line.setVisible(False)
        self._horizontal_line.setVisible(False)
        
        # Connect to the mouse move signal in the view box
        self._plot_item.scene().sigMouseMoved.connect(self._update_crosshair)
        self._crosshair_visible = True
    
    def _update_crosshair(self, pos):
        """Update the crosshair position when mouse moves"""
        if not self._crosshair_visible:
            return
            
        # Convert scene position to view coordinates
        view_pos = self._plot_item.getViewBox().mapSceneToView(pos)
        
        # Update crosshair lines
        self._vertical_line.setPos(view_pos.x())
        self._horizontal_line.setPos(view_pos.y())
        
        # Make sure lines are visible
        if not self._vertical_line.isVisible():
            self._vertical_line.setVisible(True)
            self._horizontal_line.setVisible(True)


# Example usage of the base graph class
if __name__ == "__main__":
    import pyvisual as pv
    
    # Create app and window
    app = pv.PvApp()
    window = pv.PvWindow(title="Base Graph Example", is_resizable=True)
    window.resize(800, 600)
    
    # Verify lazy loading works
    print("Before importing: pyqtgraph lazy loaded?", _pg is not None)
    print("Before importing: numpy lazy loaded?", _np is not None)
    
    # Access the get functions to trigger imports
    pg = get_pg()
    np = get_np()
    
    print("After importing: pyqtgraph lazy loaded?", _pg is not None)
    print("After importing: numpy lazy loaded?", _np is not None)
    
    # Create a base graph with custom settings
    graph = PvBaseGraph(
        container=window,
        x=50, y=50,
        width=700, height=500,
        title="PvBaseGraph Example",
        x_label="X-Axis", 
        y_label="Y-Axis",
        background_color=(240, 0, 245, 1),  # Vivid purple
        axis_color=(0, 0, 0, 1),            # Black axes
        grid=True,
        grid_color=(180, 180, 180, 1),      # Gray grid
        grid_alpha=0.5,
        legend=True,
        crosshair=True,
        x_range=(-10, 10),
        y_range=(-5, 5),
        border_thickness=0,
        corner_radius=0
    )
    
    # Generate some data
    x = np.linspace(-10, 10, 100)
    y = np.sin(x)
    
    # Create a plot using PyQtGraph directly
    plot_item = graph._plot_item.plot(
        x=x, y=y, 
        pen=pg.mkPen(color=(255, 0, 0), width=2),
        name="sin(x)"
    )
    
    # Add the plot item to our list for tracking
    graph._data_items.append(plot_item)
    
    # Show the window
    window.show()
    app.run() 