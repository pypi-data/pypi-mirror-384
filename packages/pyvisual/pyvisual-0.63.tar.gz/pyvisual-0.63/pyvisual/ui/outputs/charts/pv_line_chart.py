import random
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt


class PvLineChart:
    def __init__(self, container, x=0, y=0, width=600, height=400, title="", x_data=None, y_data=None,
                 line_color="blue", label=None, line_style="-", line_width=1.5, marker=None, marker_size=6, alpha=1.0,
                 show_grid=False, show_x_labels=True, show_y_labels=True, x_min=None, x_max=None, y_min=None,
                 y_max=None,
                 dynamic_x=None, dynamic_y=None, x_offset=0, y_offset=0):
        """
        Line Chart widget for PyVisual with dynamic axis limits.

        Args:
            dynamic_x (int): Fixed size for the X-axis range (dynamic) or None for static.
            dynamic_y (int): Fixed size for the Y-axis range (dynamic) or None for static.
            x_offset (int): Offset for the X-axis when dynamic_x is set.
            y_offset (int): Offset for the Y-axis when dynamic_y is set.
        """
        self.container = container
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.x_data = x_data or []
        self.y_data = y_data or []
        self.line_color = line_color
        self.label = label
        self.line_style = line_style
        self.line_width = line_width
        self.marker = marker
        self.marker_size = marker_size
        self.alpha = alpha
        self.show_grid = show_grid
        self.show_x_labels = show_x_labels
        self.show_y_labels = show_y_labels
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.dynamic_x = dynamic_x
        self.dynamic_y = dynamic_y
        self.x_offset = x_offset
        self.y_offset = y_offset

        # Initialize Matplotlib figure and axis
        self.fig, self.ax = plt.subplots(figsize=(width / 100, height / 100))
        self.ax.set_title(self.title)

        # Add the Matplotlib figure to the PyVisual container
        self.canvas_widget = FigureCanvasKivyAgg(self.fig)
        if container:
            self.canvas_widget.size_hint = (None, None)
            self.canvas_widget.size = (self.width - 20, self.height - 20)  # Internal padding of 20px
            self.canvas_widget.pos = (self.x + 10, self.y + 10)  # Offset by 10px
            container.add_widget(self.canvas_widget)

        # Render the initial chart
        self._render_chart()

    def _render_chart(self):
        """Render the line chart based on current data and properties."""
        self.ax.clear()  # Clear the previous chart
        self.ax.plot(
            self.x_data, self.y_data,
            color=self.line_color,
            label=self.label,
            linestyle=self.line_style,
            linewidth=self.line_width,
            marker=self.marker,
            markersize=self.marker_size,
            alpha=self.alpha
        )

        if self.label:
            self.ax.legend()

        self.ax.set_title(self.title)

        # Handle dynamic X-axis and Y-axis limits
        if self.dynamic_x is not None and self.x_data:
            x_end = max(self.x_data) + self.x_offset
            x_start = x_end - self.dynamic_x
            self.ax.set_xlim(x_start, x_end)
        elif self.x_min is not None and self.x_max is not None:
            self.ax.set_xlim(self.x_min, self.x_max)

        if self.dynamic_y is not None and self.y_data:
            y_end = max(self.y_data) + self.y_offset
            y_start = y_end - self.dynamic_y
            self.ax.set_ylim(y_start, y_end)
        elif self.y_min is not None and self.y_max is not None:
            self.ax.set_ylim(self.y_min, self.y_max)

        # Remove spines (bounding rectangle)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)

        # Apply grid and label visibility
        self.ax.grid(self.show_grid)
        self.ax.xaxis.set_visible(self.show_x_labels)
        self.ax.yaxis.set_visible(self.show_y_labels)

        self.fig.tight_layout()
        self.canvas_widget.draw()

    def add_point(self, x, y):
        """
        Add a new point to the line chart and update the graph.

        Args:
            x: X-coordinate of the point.
            y: Y-coordinate of the point.
        """
        self.x_data.append(x)
        self.y_data.append(y)
        self._render_chart()

    def set_dynamic_x(self, range_size=None, offset=0):
        """
        Set dynamic behavior for the X-axis.

        Args:
            range_size (int): Fixed size for the X-axis range or None to disable.
            offset (int): Offset for the X-axis range.
        """
        self.dynamic_x = range_size
        self.x_offset = offset
        self._render_chart()

    def set_dynamic_y(self, range_size=None, offset=0):
        """
        Set dynamic behavior for the Y-axis.

        Args:
            range_size (int): Fixed size for the Y-axis range or None to disable.
            offset (int): Offset for the Y-axis range.
        """
        self.dynamic_y = range_size
        self.y_offset = offset
        self._render_chart()

    def set_x_axis_limits(self, x_min, x_max):
        """
        Set the limits for the X-axis.

        Args:
            x_min (float): Minimum value for the X-axis.
            x_max (float): Maximum value for the X-axis.
        """
        self.x_min = x_min
        self.x_max = x_max
        self._render_chart()

    def set_y_axis_limits(self, y_min, y_max):
        """
        Set the limits for the Y-axis.

        Args:
            y_min (float): Minimum value for the Y-axis.
            y_max (float): Maximum value for the Y-axis.
        """
        self.y_min = y_min
        self.y_max = y_max
        self._render_chart()

    def set_show_grid(self, show_grid):
        """
        Set the visibility of the grid.

        Args:
            show_grid (bool): Whether to show the grid.
        """
        self.show_grid = show_grid
        self._render_chart()

    def set_show_x_labels(self, show_x_labels):
        """
        Set the visibility of the x-axis labels.

        Args:
            show_x_labels (bool): Whether to show the x-axis labels.
        """
        self.show_x_labels = show_x_labels
        self._render_chart()

    def set_show_y_labels(self, show_y_labels):
        """
        Set the visibility of the y-axis labels.

        Args:
            show_y_labels (bool): Whether to show the y-axis labels.
        """
        self.show_y_labels = show_y_labels
        self._render_chart()

    def set_data(self, x_data, y_data):
        """
        Update the data for the line chart.

        Args:
            x_data (list): Updated X-axis data points.
            y_data (list): Updated Y-axis data points.
        """
        self.x_data = x_data
        self.y_data = y_data
        self._render_chart()

    def add_point(self, x, y):
        """
        Add a new point to the line chart and update the graph.

        Args:
            x: X-coordinate of the point.
            y: Y-coordinate of the point.
        """
        self.x_data.append(x)
        self.y_data.append(y)
        self._render_chart()

    def set_title(self, title):
        """
        Set a new title for the chart.

        Args:
            title (str): New title of the chart.
        """
        self.title = title
        self._render_chart()

    def set_position(self, x, y):
        """
        Update the position of the chart.

        Args:
            x (int): New X position of the chart.
            y (int): New Y position of the chart.
        """
        self.x = x
        self.y = y
        self.canvas_widget.pos = (self.x + 10, self.y + 10)

    def set_size(self, width, height):
        """
        Dynamically change the size of the chart.

        Args:
            width (int): New width of the chart.
            height (int): New height of the chart.
        """
        self.width = width
        self.height = height
        self.fig.set_size_inches(self.width / 100, self.height / 100)
        self.canvas_widget.size = (self.width - 20, self.height - 20)
        self._render_chart()

    # Getters and Setters for additional properties
    def set_line_color(self, color):
        self.line_color = color
        self._render_chart()

    def get_line_color(self):
        return self.line_color

    def set_label(self, label):
        self.label = label
        self._render_chart()

    def get_label(self):
        return self.label

    def set_line_style(self, line_style):
        self.line_style = line_style
        self._render_chart()

    def get_line_style(self):
        return self.line_style

    def set_line_width(self, line_width):
        self.line_width = line_width
        self._render_chart()

    def get_line_width(self):
        return self.line_width

    def set_marker(self, marker):
        self.marker = marker
        self._render_chart()

    def get_marker(self):
        return self.marker

    def set_marker_size(self, marker_size):
        self.marker_size = marker_size
        self._render_chart()

    def get_marker_size(self):
        return self.marker_size

    def set_alpha(self, alpha):
        self.alpha = alpha
        self._render_chart()

    def get_alpha(self):
        return self.alpha


# Usage example with dynamic axis limits
# Usage example with dynamic axis limits
if __name__ == "__main__":
    import pyvisual as pv

    # Create a PyVisual window
    window = pv.PvWindow()

    # Line Chart
    line_chart = PvLineChart(
        container=window,
        x=50, y=50,
        width=700,
        height=500,
        x_data=[1, 2, 3, 4, 5],
        y_data=[10, 20, 15, 25, 18],
        line_color="green",
        line_style=":",
        line_width=1,
        marker="o",
        marker_size=8,
        alpha=0.75,
        dynamic_x=35,
        x_offset=15,
        y_min=0,
        y_max=1000,
        show_x_labels=False,
        show_y_labels=False
    )


    def add_points(instance):
        line_chart.add_point(len(line_chart.x_data) + 1, random.randint(300, 700))


    pv.PvTimer.schedule_function(add_points, 0.01)

    # Show the PyVisual window
    window.show()
