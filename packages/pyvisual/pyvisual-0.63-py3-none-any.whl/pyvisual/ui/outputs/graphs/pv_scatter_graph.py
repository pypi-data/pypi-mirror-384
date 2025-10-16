from pyvisual.ui.outputs.graphs.pv_base_graph import PvBaseGraph, get_pg, get_np
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pyqtgraph as pg
    import numpy as np

class PvScatterGraph(PvBaseGraph):
    """
    A specialized graph class for scatter plots, inheriting from PvBaseGraph.
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
        Initialize a scatter plot with customizable properties.
        """
        super().__init__(
            container, x, y, width, height, title, x_label, y_label,
            background_color, axis_color, grid, grid_color, grid_alpha,
            legend, crosshair, x_range, y_range, log_x, log_y,
            anti_aliasing, border_thickness, corner_radius, border_color, is_visible, opacity,
            tag, **kwargs
        )
    
    def add_scatter(self, x=None, y=None, name=None, color=(0, 0, 255, 1), 
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
        # Get required modules
        pg = get_pg()
        np = get_np()
        
        # Create default x values if not provided
        if x is None and y is not None:
            x = np.arange(len(y))
        elif y is None:
            print("Error: No Y data provided for scatter plot")
            return None
            
        # Make sure we have numpy arrays for consistent behavior
        try:
            x = np.array(x)
            y = np.array(y)
            
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
            color_obj = pg.mkColor(int(color[0]), int(color[1]), int(color[2]), int(plot_alpha*255))
            symbol_brush = pg.mkBrush(color_obj)
        else:
            symbol_brush = brush
        
        # Add the scatter plot (line pen set to None for scatter only)
        try:
            plot = self._plot_item.plot(x=x, y=y, name=name, pen=None,
                                       symbol=sym, symbolSize=symbol_size,
                                       symbolBrush=symbol_brush)
                                       
            # Store plot for later reference
            self._data_items.append(plot)
            
            # Make sure autorange is enabled to show all data
            self._plot_item.enableAutoRange()
            
            # Force update to ensure data is visible
            self.update()
            
            return plot
            
        except Exception as e:
            print(f"Error in standard plotting: {e}")
            
            # If that fails, try the scatter plot item directly
            try:
                scatter = pg.ScatterPlotItem(x=x, y=y, symbol=sym, 
                                         size=symbol_size,
                                         brush=symbol_brush,
                                         name=name)
                                         
                self._plot_item.addItem(scatter)
                self._data_items.append(scatter)
                
                # Make sure autorange is enabled to show all data
                self._plot_item.enableAutoRange()
                
                # Force update to ensure data is visible
                self.update()
                
                return scatter
                
            except Exception as e2:
                print(f"ScatterPlotItem error: {e2}")
                return None
    
    def update_scatter(self, scatter_index, x=None, y=None):
        """
        Update an existing scatter plot's data.
        
        Args:
            scatter_index: Index of the scatter plot to update
            x: New x data
            y: New y data
        """
        # Get numpy module
        np = get_np()
        
        if 0 <= scatter_index < len(self._data_items):
            scatter = self._data_items[scatter_index]
            
            if y is not None:
                if x is None:
                    x = np.arange(len(y))
                
                # Handle both PlotDataItem and ScatterPlotItem
                if hasattr(scatter, 'setData'):
                    scatter.setData(x=x, y=y)
                else:
                    # For other plot types, try different methods
                    try:
                        scatter.setPoints(x=x, y=y)
                    except:
                        try:
                            scatter.setData(x, y)
                        except:
                            print("Error: Unable to update scatter plot data")
                            return False
                
                # Force update
                self.update()
                return True
        
        return False


# Example usage of the scatter graph class
if __name__ == "__main__":
    import pyvisual as pv
    import random
    
    # Create app and window
    app = pv.PvApp()
    window = pv.PvWindow(title="Scatter Graph Example", is_resizable=True)
    window.resize(800, 600)
    
    # Get numpy module
    np = get_np()
    
    # Create a scatter graph with custom settings
    scatter_graph = PvScatterGraph(
        container=window,
        x=50, y=50,
        width=700, height=500,
        title="PvScatterGraph Example",
        x_label="X-Axis", 
        y_label="Y-Axis",
        background_color=(245, 245, 245, 1),  # Light gray background
        grid=True,
        legend=True,
        crosshair=True
    )
    
    # Example 1: Random scatter plot with circle symbols
    num_points = 50
    x1 = np.random.normal(0, 1, num_points)  # Normal distribution
    y1 = np.random.normal(0, 1, num_points)
    scatter_graph.add_scatter(
        x=x1, 
        y=y1,
        name="Random Normal",
        color=(255, 0, 0, 1),  # Red
        symbol='o',            # Circle
        symbol_size=10
    )
    
    # Example 2: Clustered data with square symbols
    num_points = 30
    cluster1_x = np.random.normal(-2, 0.5, num_points) 
    cluster1_y = np.random.normal(2, 0.5, num_points)
    scatter_graph.add_scatter(
        x=cluster1_x, 
        y=cluster1_y,
        name="Cluster 1",
        color=(0, 0, 255, 1),  # Blue
        symbol='s',            # Square
        symbol_size=8
    )
    
    # Example 3: Another cluster with triangle symbols
    cluster2_x = np.random.normal(2, 0.5, num_points) 
    cluster2_y = np.random.normal(-2, 0.5, num_points)
    scatter_graph.add_scatter(
        x=cluster2_x, 
        y=cluster2_y,
        name="Cluster 2",
        color=(0, 180, 0, 1),  # Green
        symbol='t',            # Triangle
        symbol_size=12
    )
    
    # Example 4: Create cross symbols for centers of clusters
    centers_x = [-2, 2]
    centers_y = [2, -2]
    scatter_graph.add_scatter(
        x=centers_x, 
        y=centers_y,
        name="Cluster Centers",
        color=(255, 120, 0, 1),  # Orange
        symbol='x',             # X symbol
        symbol_size=20
    )
    
    # Show the window
    window.show()
    app.run()
    
    # Example of updating data (not part of the running example, but shows the syntax)
    # This would be called when you want to update a scatter plot's data
    new_x = np.random.normal(0, 2, num_points)
    new_y = np.random.normal(0, 2, num_points)
    scatter_graph.update_scatter(0, x=new_x, y=new_y)  # Update the first scatter plot 