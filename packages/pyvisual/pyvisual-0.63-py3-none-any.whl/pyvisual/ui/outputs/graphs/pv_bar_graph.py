from pyvisual.ui.outputs.graphs.pv_base_graph import PvBaseGraph
import pyqtgraph as pg
import numpy as np

class PvBarGraph(PvBaseGraph):
    """
    A specialized graph class for bar graphs, inheriting from PvBaseGraph.
    """
    
    def __init__(self, container, x=100, y=100, width=400, height=300, 
                 title="", x_label="", y_label="", 
                 background_color=(255, 255, 255, 1), axis_color=(0, 0, 0, 1),
                 grid=True, grid_color=(200, 200, 200, 1), grid_alpha=0.5,
                 legend=False, crosshair=False, 
                 x_range=None, y_range=None, log_x=False, log_y=False,
                 anti_aliasing=True, border_thickness=0, border_color=None, corner_radius=0,
                 is_visible=True, opacity=1.0, tag=None, **kwargs):
        """
        Initialize a bar graph with customizable properties.
        """
        super().__init__(
            container, x, y, width, height, title, x_label, y_label,
            background_color, axis_color, grid, grid_color, grid_alpha,
            legend, crosshair, x_range, y_range, log_x, log_y,
            anti_aliasing, border_thickness, corner_radius, border_color, is_visible, opacity,
            tag, **kwargs
        )
    
    def add_bars(self, x=None, height=None, width=0.8, name=None, color=(0, 0, 255, 1), 
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
        try:
            x = np.array(x, dtype=float)
            height = np.array(height, dtype=float)
            
            # Check for invalid data
            if np.isnan(x).any() or np.isnan(height).any():
                print("Warning: Data contains NaN values, which may prevent display")
                
            if len(x) != len(height):
                print(f"Warning: X and height arrays have different lengths! X: {len(x)}, Height: {len(height)}")
                # Use the minimum length
                min_len = min(len(x), len(height))
                x = x[:min_len]
                height = height[:min_len]
                
            if len(x) == 0 or len(height) == 0:
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
        bar_color = tuple(c/255.0 for c in color[:3])
        bar_alpha = color[3]
        color_obj = pg.mkColor(int(color[0]), int(color[1]), int(color[2]), int(bar_alpha*255))
        
        # Create brush for bar filling
        if brush is None:
            bar_brush = pg.mkBrush(color_obj)
        else:
            bar_brush = brush
        
        # Create pen for bar edges
        if edge_color is None:
            # Default edge as slightly darker version of fill color
            edge_rgb = tuple(max(0, c-30) for c in color[:3])
            edge_alpha = color[3]
            edge_color_obj = pg.mkColor(int(edge_rgb[0]), int(edge_rgb[1]), int(edge_rgb[2]), int(edge_alpha*255))
            bar_pen = pg.mkPen(color=edge_color_obj, width=1)
        else:
            # Make sure edge color is valid
            if len(edge_color) < 3:
                print(f"Warning: Invalid edge color format: {edge_color}. Using darker version of fill color.")
                edge_rgb = tuple(max(0, c-30) for c in color[:3])
                edge_alpha = color[3]
            elif len(edge_color) == 3:
                # Add alpha if not provided
                edge_rgb = edge_color
                edge_alpha = color[3]
            else:
                edge_rgb = edge_color[:3]
                edge_alpha = edge_color[3]
                
            edge_color_obj = pg.mkColor(int(edge_rgb[0]), int(edge_rgb[1]), int(edge_rgb[2]), int(edge_alpha*255))
            bar_pen = pg.mkPen(color=edge_color_obj, width=1)
        
        # Try to create bar graph with standard BarGraphItem
        try:
            bar_graph = pg.BarGraphItem(x=x, height=height, width=width, brush=bar_brush, pen=bar_pen)
            self._plot_item.addItem(bar_graph)
            
            # Store for later reference
            self._data_items.append(bar_graph)
            
            # Make sure autorange is enabled to show all data
            self._plot_item.enableAutoRange()
            
            # Set x-axis tick labels if needed
            if label_rotation != 0:
                self._plot_item.getAxis('bottom').setRotation(label_rotation)
            
            # Force update to ensure data is visible
            self.update()
            
            return bar_graph
            
        except Exception as e:
            print(f"Error creating bar graph: {e}")
            
            # If that fails, try manual bar creation with rectangle items
            try:
                bar_group = pg.ItemGroup()
                half_width = width/2
                
                for i, (xi, hi) in enumerate(zip(x, height)):
                    # Create rectangle for each bar
                    bar_rect = pg.QtGui.QGraphicsRectItem(xi-half_width, 0, width, hi)
                    bar_rect.setPen(bar_pen)
                    bar_rect.setBrush(bar_brush)
                    bar_group.addToGroup(bar_rect)
                
                self._plot_item.addItem(bar_group)
                
                # Store for later reference
                self._data_items.append(bar_group)
                
                # Make sure autorange is enabled to show all data
                self._plot_item.enableAutoRange()
                
                # Set x-axis tick labels if needed
                if label_rotation != 0:
                    self._plot_item.getAxis('bottom').setRotation(label_rotation)
                
                # Force update to ensure data is visible
                self.update()
                
                return bar_group
                
            except Exception as e2:
                print(f"Manual bar creation error: {e2}")
                return None
    
    def update_bars(self, bar_index, x=None, height=None):
        """
        Update an existing bar graph's data.
        
        Args:
            bar_index: Index of the bar graph to update
            x: New x positions
            height: New heights for bars
        """
        if 0 <= bar_index < len(self._data_items):
            bar_item = self._data_items[bar_index]
            
            # For standard BarGraphItem
            if isinstance(bar_item, pg.BarGraphItem):
                if x is not None:
                    bar_item.setOpts(x=x)
                if height is not None:
                    bar_item.setOpts(height=height)
                    
                # Force update
                self.update()
                return True
                
            # For custom bar groups
            elif isinstance(bar_item, pg.ItemGroup):
                # This is more complicated as we'd need to recreate the bars
                # For now, let's just note that this isn't implemented
                print("Warning: Updating custom bar group not fully implemented")
                
                # Remove existing bar group and create a new one
                try:
                    self._plot_item.removeItem(bar_item)
                    self._data_items.remove(bar_item)
                    
                    # If we have both x and height, we can create a new bar group
                    if x is not None and height is not None:
                        # We don't have the original parameters, so we'll use defaults
                        new_bars = self.add_bars(x=x, height=height)
                        return new_bars is not None
                    
                except Exception as e:
                    print(f"Error updating bar group: {e}")
                    return False
                
            return False
        
        return False


# Example usage of the bar graph class
if __name__ == "__main__":
    import pyvisual as pv
    
    # Create app and window
    app = pv.PvApp()
    window = pv.PvWindow(title="Bar Graph Example", is_resizable=True)
    window.resize(800, 600)
    
    # Create a bar graph with custom settings
    bar_graph = PvBarGraph(
        container=window,
        x=50, y=50,
        width=700, height=500,
        title="PvBarGraph Example",
        x_label="Categories", 
        y_label="Values",
        background_color=(245, 245, 245, 1),  # Light gray background
        grid=True,
        legend=True
    )
    
    # Example 1: Simple bar chart with numerical x-positions
    categories = np.arange(5)
    values = [12, 19, 8, 24, 15]
    bar_graph.add_bars(
        x=categories,
        height=values,
        width=0.7,
        name="Dataset 1",
        color=(65, 105, 225, 1)  # Royal Blue
    )
    
    # For a more practical example, we can add labels to x-axis
    # This is a workaround since PyQtGraph doesn't directly support categorical axes
    axis = bar_graph._plot_item.getAxis('bottom')
    ticks = [(i, f"Category {i+1}") for i in range(5)]
    axis.setTicks([ticks])
    
    # Example 2: Multiple bar groups (side by side)
    # Create a second bar graph to demonstrate a different style
    bar_graph2 = PvBarGraph(
        container=window,
        x=50, y=300,
        width=700, height=250,
        title="Multiple Bar Groups Example",
        x_label="Months", 
        y_label="Sales ($K)",
        background_color=(240, 248, 255, 1),  # Light blue background
        grid=True,
        grid_color=(200, 200, 200, 1),
        legend=True
    )
    
    # Define x positions with an offset for side-by-side bars
    months = np.arange(6)
    bar_width = 0.35
    
    # Dataset 1: 2022 Sales
    sales_2022 = [10.2, 15.8, 18.4, 25.0, 22.3, 19.8]
    bar_graph2.add_bars(
        x=months - bar_width/2,  # Shift to the left
        height=sales_2022,
        width=bar_width,
        name="2022 Sales",
        color=(70, 130, 180, 1),  # Steel Blue
        edge_color=(30, 90, 140, 1)  # Darker blue for edges
    )
    
    # Dataset 2: 2023 Sales
    sales_2023 = [11.5, 17.2, 20.0, 26.8, 24.5, 23.1]
    bar_graph2.add_bars(
        x=months + bar_width/2,  # Shift to the right
        height=sales_2023,
        width=bar_width,
        name="2023 Sales",
        color=(188, 143, 143, 1),  # Rosy Brown
        edge_color=(138, 93, 93, 1)  # Darker rosy brown for edges
    )
    
    # Add custom x-axis labels
    axis = bar_graph2._plot_item.getAxis('bottom')
    ticks = [(i, ["Jan", "Feb", "Mar", "Apr", "May", "Jun"][i]) for i in range(6)]
    axis.setTicks([ticks])
    
    # Show the window
    window.show()
    app.run()
    
    # Example of updating data (not part of the running example, but shows syntax)
    updated_values = [15, 22, 10, 26, 18]
    bar_graph.update_bars(0, height=updated_values)  # Update the first bar graph 