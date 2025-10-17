from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QFontDatabase
from PySide6.QtWidgets import QGraphicsOpacityEffect
from pyqtgraph.widgets.TableWidget import TableWidget, TableWidgetItem
import pyvisual as pv

class PvTable(TableWidget):
    
    def __init__(self, container, x=0, y=0, width=350, height=200, 
                 cell_width=87, cell_height=50, rows=4, columns=4, data=None, header_data=None,
                 header_color=(192, 192, 192, 1), idle_color=(255, 255, 255, 1),
                 border_color=(200, 200, 200, 1), border_thickness=0, corner_radius=0, table_width=2, font="Poppins", font_size=15,
                 font_color=(0, 0, 0, 1), text_alignment="left", underline=False, strikeout=False, bold=False, italic=False,
                 is_visible=True, allow_edit=True, tag=None, **kwargs):
        
        
        # Initialize parent with sorting disabled
        super().__init__(container, sortable=False)
        
        # --------------------------------------------------------------------
        # Geometry properties
        # --------------------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._cell_width = cell_width
        self._cell_height = cell_height
        
        # --------------------------------------------------------------------
        # Table structure properties
        # --------------------------------------------------------------------
        self._rows = rows
        self._columns = columns
        self._data = data if data is not None else [["" for _ in range(columns)] for _ in range(rows)]
        self._header_data = header_data if header_data is not None else [f"Column {i+1}" for i in range(columns)]
        
        # --------------------------------------------------------------------
        # Style properties
        # --------------------------------------------------------------------
        self._header_color = header_color
        self._idle_color = idle_color
        self._border_color = border_color
        self._border_thickness = border_thickness
        self._table_width = table_width
        self._corner_radius = corner_radius
        # --------------------------------------------------------------------
        # Font properties
        # --------------------------------------------------------------------
        self._font = font
        self._font_size = font_size
        self._font_color = font_color
        self._text_alignment = text_alignment
        
        # --------------------------------------------------------------------
        # State properties
        # --------------------------------------------------------------------
        self._is_visible = is_visible
        self._allow_edit = allow_edit
        self._opacity = kwargs.get('opacity', 1)
        self._is_disabled = kwargs.get('is_disabled', False)
        
        # --------------------------------------------------------------------
        # Metadata
        # --------------------------------------------------------------------
        self._tag = tag
        self._id = id
        
        # --------------------------------------------------------------------
        # Text formatting properties
        # --------------------------------------------------------------------
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._strikeout = strikeout
        # Initialize the table
        self.initialize_table()
        self.set_opacity(self._opacity)
        self.setEnabled(not self._is_disabled)
        

    # -------------------------------------------------
    # Create layout
    # -------------------------------------------------
    def initialize_table(self):
        """Initialize the table with the configured properties."""
        # Set geometry
        self.setGeometry(self._x, self._y, self._width, self._height)
        
        # Set row and column count
        self.setRowCount(self._rows)
        self.setColumnCount(self._columns)
        
        # Hide vertical header (row numbers)
        self.verticalHeader().setVisible(False)
        
        # Set header data
        self.setHorizontalHeaderLabels(self._header_data)
        
        # Configure cell dimensions
        for i in range(self._columns):
            self.setColumnWidth(i, self._cell_width)
        for i in range(self._rows):
            self.setRowHeight(i, self._cell_height)
            
        # Set header dimensions to match cell dimensions
        header = self.horizontalHeader()
        header.setFixedHeight(self._cell_height)
        header.setDefaultSectionSize(self._cell_width)
            
        # Enable grid lines and set their style
        self.setShowGrid(True)  # Enable grid lines
        self.setGridStyle(Qt.SolidLine)  # Set grid line style
        
        # Set initial data
        for i in range(self._rows):
            for j in range(self._columns):
                # Get data value if it exists, otherwise use empty string
                value = ""
                if i < len(self._data) and j < len(self._data[i]):
                    value = self._data[i][j]
                item = TableWidgetItem(str(value), i)  # Keep the row index for internal use
                item.setEditable(self._allow_edit)  # Set editability based on allow_edit property
                self.setItem(i, j, item)
                
        # Configure styling
        self.configure_style()
        
        # Set visibility
        self.setVisible(self._is_visible)
        
    def _create_cell(self, row, col, value=""):
        """Helper method to create a cell with all properties."""
        item = TableWidgetItem(str(value), row)
        
        # Set font properties
        font = QFont()
        font.setFamily(self._font)
        font.setPixelSize(self._font_size)
        item.setFont(font)
        
        # Set text alignment
        alignment = Qt.AlignLeft | Qt.AlignVCenter
        if self._text_alignment == "center":
            alignment = Qt.AlignCenter
        elif self._text_alignment == "right":
            alignment = Qt.AlignRight | Qt.AlignVCenter
        elif self._text_alignment == "center-left":
            alignment = Qt.AlignLeft | Qt.AlignVCenter
        elif self._text_alignment == "center-right":
            alignment = Qt.AlignRight | Qt.AlignVCenter
        item.setTextAlignment(alignment)
        
        # Set font color
        item.setForeground(QColor(*[int(c * 255) for c in self._font_color]))
        
        # Set editability
        item.setEditable(self._allow_edit)
        
        self.setItem(row, col, item)
        return item
        
    # -------------------------------------------------
    # Configure Style
    # -------------------------------------------------
    def configure_style(self):
        """Configure the visual style of the table."""
        # Font loading logic
        if isinstance(self._font, str) and (self._font.endswith('.ttf') or self._font.endswith('.otf')):
            font_id = QFontDatabase.addApplicationFont(self._font)
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
            font_family = families[0] if families else "Arial"
        else:
            font_family = self._font  # Use the font name directly

        # Set table border
        self.setStyleSheet(f"""
            QTableWidget {{
                border: {self._border_thickness}px solid rgba{self._border_color};
                background-color: rgba{self._idle_color};
                gridline-color: rgba(200, 200, 200, 1);
                outline: none;
                border-radius: {self._corner_radius}px;
            }}
            QHeaderView {{
                background-color: rgba{self._idle_color};
            }}
            QHeaderView::section {{
                background-color: rgba{self._header_color};
                border: {self._table_width}px solid rgba(200, 200, 200, 1);
                font-family: {font_family};
                font-size: {self._font_size}px;
                color: rgba{self._font_color};
                padding: 3px;
                font-weight: {700 if self._bold else 400};
                font-style: {'italic' if self._italic else 'normal'};
                text-decoration: {'underline' if self._underline else 'none'} {'line-through' if self._strikeout else 'none'};
            }}
            QTableWidget::item {{
                border: {self._table_width}px solid rgba(200, 200, 200, 1);
                font-family: {font_family};
                font-size: {self._font_size}px;
                color: rgba{self._font_color};
                padding: 3px;
                font-weight: {700 if self._bold else 400};
                font-style: {'italic' if self._italic else 'normal'};
                text-decoration: {'underline' if self._underline else 'none'} {'line-through' if self._strikeout else 'none'};
            }}
            QLineEdit {{
                background-color: rgba{self._idle_color};
                color: rgba{self._font_color};
                font-family: {font_family};
                font-size: {self._font_size}px;
                border: none;
                padding: 3px;
                font-weight: {700 if self._bold else 400};
                font-style: {'italic' if self._italic else 'normal'};
                text-decoration: {'underline' if self._underline else 'none'} {'line-through' if self._strikeout else 'none'};
            }}
        """)
        
        # Set text alignment using Qt's alignment flags
        alignment = Qt.AlignLeft | Qt.AlignVCenter  # Default alignment
        if self._text_alignment == "center":
            alignment = Qt.AlignCenter
        elif self._text_alignment == "right":
            alignment = Qt.AlignRight | Qt.AlignVCenter
        elif self._text_alignment == "center-left":
            alignment = Qt.AlignLeft | Qt.AlignVCenter
        elif self._text_alignment == "center-right":
            alignment = Qt.AlignRight | Qt.AlignVCenter
            
        # Apply alignment to all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    # Set font properties
                    font = QFont()
                    font.setFamily(font_family)
                    font.setPixelSize(self._font_size)
                    font.setBold(self._bold)
                    font.setItalic(self._italic)
                    font.setUnderline(self._underline)
                    font.setStrikeOut(self._strikeout)
                    item.setFont(font)
                    
                    # Set text alignment
                    item.setTextAlignment(alignment)
                    
                    # Set font color
                    item.setForeground(QColor(*[int(c * 255) for c in self._font_color]))
                    
                    # Set editability
                    item.setEditable(self._allow_edit)
                    
        # Apply alignment to header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                # Set font properties
                font = QFont()
                font.setFamily(font_family)
                font.setPixelSize(self._font_size)
                font.setBold(self._bold)
                font.setItalic(self._italic)
                font.setUnderline(self._underline)
                font.setStrikeOut(self._strikeout)
                header_item.setFont(font)
                
                # Set text alignment
                header_item.setTextAlignment(alignment)
                
                # Set font color
                header_item.setForeground(QColor(*[int(c * 255) for c in self._font_color]))
        

    # -------------------------------------------------
    # Events
    # -------------------------------------------------
        
    def mousePressEvent(self, event):
        """Handles mouse press events."""
        super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handles mouse release events."""
        super().mouseReleaseEvent(event)
                    
        
    # -------------------------------------------------
    # Getters and Setters using @property
    # -------------------------------------------------
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
        # Set the width
        self._width = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        
        # Ensure scroll bars are visible when needed
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Calculate total content width
        total_content_width = self._cell_width * self._columns
        
        # If content width is greater than table width, enable horizontal scrolling
        if total_content_width > self._width:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
    @property
    def height(self):
        return self._height
        
    @height.setter
    def height(self, value):
        # Set the height
        self._height = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        
        # Ensure scroll bars are visible when needed
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Calculate total content height (including header)
        total_content_height = (self._cell_height * self._rows) + self._cell_height  # Include header height
        
        # If content height is greater than table height, enable vertical scrolling
        if total_content_height > self._height:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
    @property
    def cell_width(self):
        return self._cell_width
        
    @cell_width.setter
    def cell_width(self, value):
        self._cell_width = value
        for i in range(self._columns):
            self.setColumnWidth(i, value)
        # Update header width to match cell width
        header = self.horizontalHeader()
        header.setDefaultSectionSize(value)
            
    @property
    def cell_height(self):
        return self._cell_height
        
    @cell_height.setter
    def cell_height(self, value):
        self._cell_height = value
        for i in range(self._rows):
            self.setRowHeight(i, value)
        # Update header height to match cell height
        header = self.horizontalHeader()
        header.setFixedHeight(value)
            
    @property
    def rows(self):
        return self._rows
        
    @rows.setter
    def rows(self, value):
        # Update data array
        while len(self._data) < value:
            self._data.append(["" for _ in range(self._columns)])
        while len(self._data) > value:
            self._data.pop()
            
        # Ensure each row has the correct number of columns
        for row in self._data:
            while len(row) < self._columns:
                row.append("")
            while len(row) > self._columns:
                row.pop()
            
        # Update row count and dimensions
        self._rows = value
        self.setRowCount(value)
        
        # Create new cells if needed
        for i in range(value):
            self.setRowHeight(i, self._cell_height)
            for j in range(self._columns):
                if not self.item(i, j):
                    self._create_cell(i, j, self._data[i][j])
        
        # Update stylesheet once for all cells
        self.configure_style()
        
    @property
    def columns(self):
        return self._columns
        
    @columns.setter
    def columns(self, value):
        # Update header data
        if len(self._header_data) < value:
            self._header_data.extend([f"Column {i+1}" for i in range(len(self._header_data), value)])
        elif len(self._header_data) > value:
            self._header_data = self._header_data[:value]
            
        # Update data array
        for row in self._data:
            while len(row) < value:
                row.append("")
            while len(row) > value:
                row.pop()
                
        # Update column count and dimensions
        self._columns = value
        self.setColumnCount(value)
        
        # Create new cells if needed
        for i in range(self._rows):
            for j in range(value):
                if not self.item(i, j):
                    self._create_cell(i, j, self._data[i][j])
        
        # Update column widths
        for j in range(value):
            self.setColumnWidth(j, self._cell_width)
            
        # Update header width
        header = self.horizontalHeader()
        header.setDefaultSectionSize(self._cell_width)
        
        # Update header labels and styling
        self.setHorizontalHeaderLabels(self._header_data)
        for col in range(value):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                # Set font properties
                font = QFont()
                font.setFamily(self._font)
                font.setPixelSize(self._font_size)
                header_item.setFont(font)
                
                # Set text alignment
                alignment = Qt.AlignLeft | Qt.AlignVCenter
                if self._text_alignment == "center":
                    alignment = Qt.AlignCenter
                elif self._text_alignment == "right":
                    alignment = Qt.AlignRight | Qt.AlignVCenter
                elif self._text_alignment == "center-left":
                    alignment = Qt.AlignLeft | Qt.AlignVCenter
                elif self._text_alignment == "center-right":
                    alignment = Qt.AlignRight | Qt.AlignVCenter
                header_item.setTextAlignment(alignment)
                
                # Set font color
                header_item.setForeground(QColor(*[int(c * 255) for c in self._font_color]))
        
        # Update stylesheet
        self.configure_style()
        
    @property
    def data(self):
        return self._data
        
    @data.setter
    def data(self, value):
        self._data = value
        for i in range(min(len(value), self._rows)):
            for j in range(min(len(value[i]), self._columns)):
                item = self.item(i, j)
                if item:
                    item.setText(str(value[i][j]))
                    
    @property
    def header_data(self):
        return self._header_data
        
    @header_data.setter
    def header_data(self, value):
        # Ensure header data matches column count
        if len(value) > self._columns:
            value = value[:self._columns]  # Truncate if too many headers
        elif len(value) < self._columns:
            # Pad with default headers if too few
            value.extend([f"Column {i+1}" for i in range(len(value), self._columns)])
            
        self._header_data = value
        self.setHorizontalHeaderLabels(value)
        
        # Update header styling
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                # Set font properties
                font = QFont()
                font.setFamily(self._font)
                font.setPixelSize(self._font_size)
                header_item.setFont(font)
                
                # Set text alignment
                alignment = Qt.AlignLeft | Qt.AlignVCenter
                if self._text_alignment == "center":
                    alignment = Qt.AlignCenter
                elif self._text_alignment == "right":
                    alignment = Qt.AlignRight | Qt.AlignVCenter
                elif self._text_alignment == "center-left":
                    alignment = Qt.AlignLeft | Qt.AlignVCenter
                elif self._text_alignment == "center-right":
                    alignment = Qt.AlignRight | Qt.AlignVCenter
                header_item.setTextAlignment(alignment)
                
                # Set font color
                header_item.setForeground(QColor(*[int(c * 255) for c in self._font_color]))
        
        # Update stylesheet
        self.configure_style()
        
    @property
    def is_visible(self):
        return self._is_visible
        
    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)
        
    @property
    def tag(self):
        return self._tag
        
    @tag.setter
    def tag(self, value):
        self._tag = value
        
    @property
    def id(self):
        return self._id
        
    @id.setter
    def id(self, value):
        self._id = value
        
    @property
    def header_color(self):
        return self._header_color

    @header_color.setter
    def header_color(self, value):
        self._header_color = value
        self.configure_style()

    @property
    def idle_color(self):
        return self._idle_color

    @idle_color.setter
    def idle_color(self, value):
        self._idle_color = value
        self.configure_style()

    @property
    def border_color(self):
        return self._border_color

    @border_color.setter
    def border_color(self, value):
        self._border_color = value
        self.configure_style()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value
        self.configure_style()

    @property
    def table_width(self):
        return self._table_width

    @table_width.setter
    def table_width(self, value):
        self._table_width = value
        self.configure_style()

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        self._font = value
        # Update font family for all cells
        if isinstance(value, str) and (value.endswith('.ttf') or value.endswith('.otf')):
            font_id = QFontDatabase.addApplicationFont(value)
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
            font_family = families[0] if families else "Arial"
        else:
            font_family = value

        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setFamily(font_family)
                    item.setFont(font)
        # Update font family for header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                font = header_item.font()
                font.setFamily(font_family)
                header_item.setFont(font)
        self.configure_style()

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = value
        # Update font size for all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setPixelSize(value)
                    item.setFont(font)
        # Update font size for header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                font = header_item.font()
                font.setPixelSize(value)
                header_item.setFont(font)
        # Update stylesheet
        self.configure_style()

    @property
    def font_color(self):
        return self._font_color

    @font_color.setter
    def font_color(self, value):
        self._font_color = value
        # Update font color for all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setForeground(QColor(*[int(c * 255) for c in value]))
        # Update font color for header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                header_item.setForeground(QColor(*[int(c * 255) for c in value]))
        self.configure_style()

    @property
    def text_alignment(self):
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, value):
        if value not in ["left", "center", "right", "center-left", "center-right"]:
            raise ValueError("text_alignment must be one of: 'left', 'center', 'right', 'center-left', 'center-right'")
        self._text_alignment = value
        self.configure_style()

    @property
    def allow_edit(self):
        return self._allow_edit
        
    @allow_edit.setter
    def allow_edit(self, value):
        self._allow_edit = value
        # Update all existing cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setEditable(value)
        
    @property
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value):
        self._bold = value
        # Update all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setBold(value)
                    item.setFont(font)
        
        # Update header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                font = header_item.font()
                font.setBold(value)
                header_item.setFont(font)
        
        self.configure_style()

    @property
    def italic(self):
        return self._italic

    @italic.setter
    def italic(self, value):
        self._italic = value
        # Update all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setItalic(value)
                    item.setFont(font)
        
        # Update header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                font = header_item.font()
                font.setItalic(value)
                header_item.setFont(font)
        
        self.configure_style()

    @property
    def underline(self):
        return self._underline

    @underline.setter
    def underline(self, value):
        self._underline = value
        # Update all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setUnderline(value)
                    item.setFont(font)
        
        # Update header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                font = header_item.font()
                font.setUnderline(value)
                header_item.setFont(font)
        
        self.configure_style()

    @property
    def strikeout(self):
        return self._strikeout

    @strikeout.setter
    def strikeout(self, value):
        self._strikeout = value
        # Update all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    font = item.font()
                    font.setStrikeOut(value)
                    item.setFont(font)
        # Update header
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                font = header_item.font()
                font.setStrikeOut(value)
                header_item.setFont(font)
        self.configure_style()

    @property
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        self.configure_style()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.set_opacity(value)

    @property
    def is_disabled(self):
        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, value):
        self._is_disabled = value
        self.setEnabled(not value)

    # -------------------------------------------------
    # Print Properties
    # -------------------------------------------------
    def print_properties(self):
        """Prints all the current properties of the table."""
        # Filter out empty cells from data
        non_empty_data = []
        for row in self._data:
            non_empty_row = [cell for cell in row if cell != ""]
            if non_empty_row:  # Only add rows that have at least one non-empty cell
                non_empty_data.append(non_empty_row)

        print(f"""
        Table Properties:
        ------------------
        position: ({self.x}, {self.y})
        size: ({self.width}, {self.height})
        cell_size: ({self.cell_width}, {self.cell_height})
        dimensions: {self.rows}x{self.columns}
        data: {non_empty_data}
        header_data: {self.header_data}
        is_visible: {self.is_visible}
        tag: {self.tag}
        """)

    def set_opacity(self, value):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(value)
        self.setGraphicsEffect(effect)
        self.setWindowOpacity(value)

# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------

if __name__ == "__main__":

    app = pv.PvApp()
    window = pv.PvWindow(title="PvTable Example", is_resizable=True)

    # Example table with text formatting
    table1 = PvTable(container=window, x=47, y=70, width=409,
        height=267, border_color=(200, 200, 200, 1), border_thickness=0, corner_radius=0,
        cell_width=85, cell_height=50, columns=4, rows=4,
        header_data=["Column 1", "Column 2", "Column 3", "Column 4"], header_color=(0, 59, 128, 1), idle_color=(150, 0, 0, 1), table_width=3,
        text_alignment="left", font='assets/fonts/Poppins/Poppins.ttf', font_size=15, font_color=(0, 0, 0, 1),
        bold=False, italic=False, underline=False, strikethrough=False,
        is_visible=True, opacity=1)


    window.show()
    app.run() 