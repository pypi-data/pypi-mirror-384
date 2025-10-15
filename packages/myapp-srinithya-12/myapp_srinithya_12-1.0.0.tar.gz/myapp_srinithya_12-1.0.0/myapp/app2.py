import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QLineEdit, QTextEdit, 
                             QFileDialog, QProgressBar, QSpinBox, QComboBox,
                             QGroupBox, QGridLayout, QColorDialog, QCheckBox,
                             QSlider, QFrame, QSplitter, QButtonGroup, QRadioButton,
                             QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QPoint, QSize
from PyQt6.QtGui import (QPixmap, QPainter, QFont, QColor, QPen, QMouseEvent, 
                         QFontDatabase, QPaintEvent, QCursor, QFontMetrics)
from PIL import Image, ImageDraw, ImageFont
import json
import traceback

# Debug logging function
def debug_log(message):
    print(f"[DEBUG] {message}")

class DraggableTextLabel(QLabel):
    position_changed = pyqtSignal(int, int)
    size_changed = pyqtSignal(int, int)
    text_edited = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        debug_log("Creating DraggableTextLabel")
        
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #007ACC;
                background-color: rgba(0, 122, 204, 40);
                color: white;
            }
        """)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # State variables
        self.dragging = False
        self.resizing = False
        self.editing = False
        self.drag_start_position = QPoint()
        self.resize_start_position = QPoint()
        self.resize_start_size = None
        self.resize_margin = 15
        
        # Text properties
        self.text_content = "Sample Title"
        self.font_size = 48
        self.is_bold = False
        self.is_italic = False
        self.text_color = QColor(255, 255, 255)
        self.outline_enabled = True
        self.outline_color = QColor(0, 0, 0)
        self.outline_width = 2
        self.text_alignment = Qt.AlignmentFlag.AlignCenter  # Add alignment property
        
        # Long text handling properties
        self.auto_fit_text = True
        self.multi_line_text = False
        self.max_text_width = 80  # Percentage of template width
        self.line_spacing = 120   # Percentage of normal line spacing
        self.h_margin = 5         # Horizontal margin percentage
        self.v_margin = 5         # Vertical margin percentage
        
        self.setMinimumSize(100, 50)
        self.setMaximumSize(2000, 1000)
        
        # Make sure the widget can receive focus and events
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        # Create text editor for inline editing
        self.text_editor = QLineEdit(self)
        self.text_editor.hide()
        self.text_editor.editingFinished.connect(self.finish_editing)
        self.text_editor.returnPressed.connect(self.finish_editing)
        
        self.update_display()
        debug_log(f"DraggableTextLabel created with size: {self.size()}")
        
    def update_display(self):
        try:
            debug_log(f"Updating display - font_size: {self.font_size}, text: '{self.text_content}', alignment: {self.text_alignment}")
            
            # Calculate the font size that should be used in the preview
            preview_font_size = self.font_size
            
            # Get template information for scaling and auto-fitting
            template_size = None
            display_rect = None
            scale_factor = 1.0
            
            if hasattr(self.parent(), 'original_template_size') and self.parent().original_template_size:
                template_size = self.parent().original_template_size
                display_rect = self.parent().template_display_rect
                
                if display_rect.isValid() and display_rect.width() > 0:
                    # Calculate scale factor from template to preview
                    scale_factor = display_rect.width() / template_size.width()
                    preview_font_size = max(8, int(self.font_size * scale_factor))
                    
                    debug_log(f"Font scaling: template_width={template_size.width()}, display_width={display_rect.width()}")
                    debug_log(f"Scale factor: {scale_factor:.3f}, original_font: {self.font_size}, preview_font: {preview_font_size}")
            
            # Calculate available width for text with margins
            available_width = None
            if template_size and self.auto_fit_text:
                # Calculate horizontal margins
                h_margin_px = int(template_size.width() * (self.h_margin / 100))
                
                # Calculate max width based on template size, percentage, and margins
                usable_width = template_size.width() - (2 * h_margin_px)  # Subtract both left and right margins
                max_template_width = int(usable_width * (self.max_text_width / 100))
                available_width = int(max_template_width * scale_factor)
                
                debug_log(f"Template width: {template_size.width()}px")
                debug_log(f"H margin: {self.h_margin}% = {h_margin_px}px each side")
                debug_log(f"Usable width: {usable_width}px")
                debug_log(f"Max text width: {max_template_width}px (template)")
                debug_log(f"Available width for text: {available_width}px (preview)")
            
            # Process text for multi-line and auto-fitting
            processed_text, final_font_size = self.process_text_for_display(
                self.text_content, preview_font_size, available_width
            )
            
            # Create font with final size - use Inter font if available
            font_family = "Inter"  # Try Inter first
            font = QFont(font_family, max(8, min(200, final_font_size)))
            
            # Check if Inter font is available, if not fall back to other fonts
            if font.family() != "Inter":
                # Inter not available, try other fonts
                for fallback_font in ["Arial", "Helvetica", "Sans-serif"]:
                    font = QFont(fallback_font, max(8, min(200, final_font_size)))
                    if font.family() != "":
                        debug_log(f"Using fallback font: {font.family()}")
                        break
            else:
                debug_log(f"Using Inter font for preview")
            
            font.setBold(self.is_bold)
            font.setItalic(self.is_italic)
            
            # Calculate text size
            metrics = QFontMetrics(font)
            if self.multi_line_text and '\n' in processed_text:
                # Multi-line text size calculation
                lines = processed_text.split('\n')
                max_line_width = 0
                total_height = 0
                line_height = metrics.height() * (self.line_spacing / 100)
                
                for line in lines:
                    line_rect = metrics.boundingRect(line)
                    max_line_width = max(max_line_width, line_rect.width())
                    total_height += line_height
                
                text_width = max_line_width
                text_height = int(total_height)
            else:
                # Single line text
                text_rect = metrics.boundingRect(processed_text)
                text_width = text_rect.width()
                text_height = text_rect.height()
            
            # Add padding for outline and border
            padding = max(20, self.outline_width * 2 + 15)
            new_width = max(120, min(2000, text_width + padding))
            new_height = max(60, min(1000, text_height + padding))
            
            debug_log(f"Calculated preview size: {new_width}x{new_height} (font size: {final_font_size})")
            
            self.resize(new_width, new_height)
            
            # Update the label
            self.setFont(font)
            if self.multi_line_text and '\n' in processed_text:
                # For multi-line text, we need to handle line spacing
                self.setText(processed_text.replace('\n', '\n'))
                # Use word wrap
                self.setWordWrap(True)
            else:
                self.setText(processed_text)
                self.setWordWrap(False)
            
            self.setAlignment(self.text_alignment)
            
            # Apply styling with line spacing for multi-line text
            color_style = f"color: rgb({self.text_color.red()}, {self.text_color.green()}, {self.text_color.blue()});"
            border_style = "border: 2px dashed #007ACC; background-color: rgba(0, 122, 204, 40);"
            weight_style = f"font-weight: {'bold' if self.is_bold else 'normal'};"
            style_attr = f"font-style: {'italic' if self.is_italic else 'normal'};"
            
            # Add line spacing for multi-line text
            if self.multi_line_text:
                line_height = f"line-height: {self.line_spacing}%;"
            else:
                line_height = ""
            
            safe_stylesheet = f"""
                QLabel {{
                    {border_style}
                    {color_style}
                    {weight_style}
                    {style_attr}
                    {line_height}
                    padding: 8px;
                }}
            """
            
            self.setStyleSheet(safe_stylesheet)
            debug_log("Display updated successfully")
            
        except Exception as e:
            debug_log(f"Error updating display: {e}")
            traceback.print_exc()
            # Fallback to basic styling
            self.setStyleSheet("QLabel { border: 2px dashed #007ACC; background-color: rgba(0, 122, 204, 40); color: white; padding: 8px; }")
            
    def process_text_for_display(self, text, font_size, available_width):
        """Process text for multi-line wrapping and auto-fitting"""
        try:
            # If no constraints, return as-is
            if not available_width:
                return text, font_size
            
            # Create font for measurement
            font = QFont("Arial", font_size)
            font.setBold(self.is_bold)
            font.setItalic(self.is_italic)
            metrics = QFontMetrics(font)
            
            # Check if text fits in available width
            text_width = metrics.boundingRect(text).width()
            
            if text_width <= available_width:
                # Text fits, no processing needed
                return text, font_size
            
            # Text doesn't fit, decide what to do
            if self.multi_line_text:
                # Wrap text to multiple lines
                wrapped_text = self.wrap_text_to_width(text, font, available_width)
                return wrapped_text, font_size
            elif self.auto_fit_text:
                # Scale font down to fit
                scale_factor = available_width / text_width
                new_font_size = max(8, int(font_size * scale_factor * 0.95))  # 5% margin
                debug_log(f"Auto-fitting font: {font_size} -> {new_font_size} (scale: {scale_factor:.3f})")
                return text, new_font_size
            else:
                # No processing, text may overflow
                return text, font_size
                
        except Exception as e:
            debug_log(f"Error processing text: {e}")
            return text, font_size
    
    def wrap_text_to_width(self, text, font, max_width):
        """Wrap text to multiple lines within the specified width"""
        try:
            metrics = QFontMetrics(font)
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                # Test adding this word to current line
                test_line = ' '.join(current_line + [word])
                test_width = metrics.boundingRect(test_line).width()
                
                if test_width <= max_width or not current_line:
                    # Word fits or it's the first word
                    current_line.append(word)
                else:
                    # Word doesn't fit, start new line
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            # Add the last line
            if current_line:
                lines.append(' '.join(current_line))
            
            return '\n'.join(lines)
            
        except Exception as e:
            debug_log(f"Error wrapping text: {e}")
            return text

    def mouseDoubleClickEvent(self, event):
        """Enable text editing on double click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_editing()
            
    def start_editing(self):
        """Start inline text editing"""
        debug_log("Starting text editing")
        self.editing = True
        self.text_editor.setText(self.text_content)
        self.text_editor.setGeometry(self.rect().adjusted(5, 5, -5, -5))
        self.text_editor.show()
        self.text_editor.setFocus()
        self.text_editor.selectAll()
        
    def finish_editing(self):
        """Finish text editing and update content"""
        if self.editing:
            debug_log("Finishing text editing")
            new_text = self.text_editor.text().strip()
            if new_text and new_text != self.text_content:
                self.text_content = new_text
                self.text_edited.emit(new_text)
                self.update_display()
            
            self.text_editor.hide()
            self.editing = False

    def mousePressEvent(self, event):
        debug_log(f"Mouse press at: {event.pos()}, button: {event.button()}")
        
        if self.editing:
            return  # Don't handle drag/resize while editing
            
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                self.drag_start_position = QPoint(event.pos())
                
                # Check if clicking near edges for resizing
                margin = self.resize_margin
                rect = self.rect()
                
                near_right = event.pos().x() > rect.width() - margin
                near_bottom = event.pos().y() > rect.height() - margin
                near_left = event.pos().x() < margin
                near_top = event.pos().y() < margin
                
                debug_log(f"Edge detection - right: {near_right}, bottom: {near_bottom}, left: {near_left}, top: {near_top}")
                
                if near_right or near_bottom or near_left or near_top:
                    debug_log("Starting resize mode")
                    self.resizing = True
                    self.resize_start_position = QPoint(event.globalPosition().toPoint())
                    self.resize_start_size = self.size()
                    
                    if (near_right and near_bottom) or (near_left and near_top):
                        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                    elif (near_right and near_top) or (near_left and near_bottom):
                        self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                    elif near_right or near_left:
                        self.setCursor(Qt.CursorShape.SizeHorCursor)
                    elif near_bottom or near_top:
                        self.setCursor(Qt.CursorShape.SizeVerCursor)
                else:
                    debug_log("Starting drag mode")
                    self.dragging = True
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    
                event.accept()
                
            except Exception as e:
                debug_log(f"Mouse press error: {e}")
                traceback.print_exc()

    def mouseMoveEvent(self, event):
        if self.editing:
            return
            
        try:
            if self.dragging and (event.buttons() & Qt.MouseButton.LeftButton):
                debug_log(f"Dragging to: {event.globalPosition().toPoint()}")
                
                if self.parent():
                    global_pos = event.globalPosition().toPoint()
                    parent_pos = self.parent().mapFromGlobal(global_pos)
                    new_pos = parent_pos - self.drag_start_position
                    
                    # Keep within parent bounds
                    parent_rect = self.parent().rect()
                    new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - self.width())))
                    new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - self.height())))
                    
                    debug_log(f"Moving to: {new_pos}")
                    self.move(new_pos)
                    self.position_changed.emit(new_pos.x(), new_pos.y())
                
            elif self.resizing and (event.buttons() & Qt.MouseButton.LeftButton):
                debug_log(f"Resizing with mouse at: {event.globalPosition().toPoint()}")
                
                if self.resize_start_size:
                    global_pos = event.globalPosition().toPoint()
                    diff = global_pos - self.resize_start_position
                    
                    new_width = max(120, min(2000, self.resize_start_size.width() + diff.x()))
                    new_height = max(60, min(1000, self.resize_start_size.height() + diff.y()))
                    
                    debug_log(f"New size: {new_width}x{new_height}")
                    
                    # Keep within parent bounds
                    if self.parent():
                        parent_rect = self.parent().rect()
                        max_width = parent_rect.width() - self.x()
                        max_height = parent_rect.height() - self.y()
                        
                        new_width = min(new_width, max_width)
                        new_height = min(new_height, max_height)
                    
                    # Calculate new font size based on resize
                    if self.resize_start_size.width() > 0 and self.resize_start_size.height() > 0:
                        scale_factor = min(new_width / self.resize_start_size.width(), 
                                         new_height / self.resize_start_size.height())
                        new_font_size = max(8, min(200, int(self.font_size * scale_factor)))
                        
                        debug_log(f"Font size changed from {self.font_size} to {new_font_size}")
                        
                        if abs(new_font_size - self.font_size) > 1:
                            self.font_size = new_font_size
                            self.update_display()
                            self.size_changed.emit(new_width, new_height)
            else:
                self.update_cursor_for_position(event.pos())
                
        except Exception as e:
            debug_log(f"Mouse move error: {e}")
            traceback.print_exc()

    def update_cursor_for_position(self, pos):
        if self.editing:
            return
            
        try:
            margin = self.resize_margin
            rect = self.rect()
            
            near_right = pos.x() > rect.width() - margin
            near_bottom = pos.y() > rect.height() - margin
            near_left = pos.x() < margin
            near_top = pos.y() < margin
            
            if (near_right and near_bottom) or (near_left and near_top):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif (near_right and near_top) or (near_left and near_bottom):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif near_right or near_left:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif near_bottom or near_top:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        except Exception as e:
            debug_log(f"Cursor update error: {e}")
                
    def mouseReleaseEvent(self, event):
        if self.editing:
            return
            
        try:
            debug_log(f"Mouse release - was dragging: {self.dragging}, was resizing: {self.resizing}")
            self.dragging = False
            self.resizing = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        except Exception as e:
            debug_log(f"Mouse release error: {e}")
            traceback.print_exc()

    def enterEvent(self, event):
        if not self.editing:
            debug_log("Mouse entered text label")
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        
    def leaveEvent(self, event):
        if not self.editing:
            debug_log("Mouse left text label")
            if not self.dragging and not self.resizing:
                self.setCursor(Qt.CursorShape.ArrowCursor)

class PreviewWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        debug_log("Creating PreviewWidget")
        self.setMinimumSize(400, 500)  # Better default for portrait templates
        self.setStyleSheet("QFrame { border: 1px solid gray; background-color: #f0f0f0; }")
        self.template_pixmap = None
        self.text_label = None
        
        # Store original template size for accurate positioning
        self.original_template_size = None
        self.template_display_rect = QRect()
        self.template_aspect_ratio = 1.0
        
        # Enable mouse events for the preview widget
        self.setMouseTracking(True)
        
    def set_template(self, pixmap):
        debug_log(f"Setting template with size: {pixmap.size()}")
        self.template_pixmap = pixmap
        self.original_template_size = pixmap.size()
        
        # Calculate aspect ratio
        if self.original_template_size.height() > 0:
            self.template_aspect_ratio = self.original_template_size.width() / self.original_template_size.height()
            debug_log(f"Template aspect ratio: {self.template_aspect_ratio:.3f}")
            
            # Adjust preview widget size to match template aspect ratio
            self.adjust_preview_size()
        
        # Force immediate calculation of display rect
        self.calculate_template_display_rect()
        debug_log(f"Template display rect calculated: {self.template_display_rect}")
        self.update()
        
    def adjust_preview_size(self):
        """Adjust preview widget size to better match template aspect ratio"""
        if not self.original_template_size:
            return
            
        # Get parent widget size for reference
        if self.parent():
            parent_width = self.parent().width() - 50  # Leave some margin
            parent_height = self.parent().height() - 100  # Leave space for other widgets
        else:
            parent_width = 800
            parent_height = 600
            
        # Calculate optimal preview size based on template aspect ratio
        target_width = min(parent_width, 700)  # Max width for preview
        target_height = int(target_width / self.template_aspect_ratio)
        
        # If height is too large, scale down
        if target_height > parent_height:
            target_height = parent_height
            target_width = int(target_height * self.template_aspect_ratio)
            
        # Ensure minimum sizes
        target_width = max(400, target_width)
        target_height = max(300, target_height)
        
        debug_log(f"Adjusting preview size to {target_width}x{target_height} for aspect ratio {self.template_aspect_ratio:.3f}")
        
        # Set the preferred size
        self.setMinimumSize(target_width, target_height)
        self.setMaximumSize(target_width + 200, target_height + 200)  # Allow some flexibility
        
    def calculate_template_display_rect(self):
        """Calculate where the template will be displayed within the preview widget"""
        if not self.template_pixmap:
            return
            
        # Get available space in preview widget (with small margins)
        margin = 10
        available_width = self.width() - 2 * margin
        available_height = self.height() - 2 * margin
        
        template_size = self.template_pixmap.size()
        
        # Calculate scale factor to fit template in available space while maintaining aspect ratio
        scale_factor = min(
            available_width / template_size.width(),
            available_height / template_size.height()
        )
        
        # Calculate scaled size
        scaled_width = int(template_size.width() * scale_factor)
        scaled_height = int(template_size.height() * scale_factor)
        
        # Center the template in the available space
        x = margin + (available_width - scaled_width) // 2
        y = margin + (available_height - scaled_height) // 2
        
        self.template_display_rect = QRect(x, y, scaled_width, scaled_height)
        
        debug_log(f"Template display calculation:")
        debug_log(f"  Preview widget size: {self.width()}x{self.height()}")
        debug_log(f"  Template original size: {template_size}")
        debug_log(f"  Available space: {available_width}x{available_height}")
        debug_log(f"  Scale factor: {scale_factor:.3f}")
        debug_log(f"  Scaled size: {scaled_width}x{scaled_height}")
        debug_log(f"  Display rect: {self.template_display_rect}")
        
    def showEvent(self, event):
        """Called when widget is shown - ensure display rect is calculated"""
        super().showEvent(event)
        if self.template_pixmap:
            debug_log("PreviewWidget shown - recalculating display rect")
            self.calculate_template_display_rect()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        debug_log(f"PreviewWidget resized to: {event.size()}")
        self.calculate_template_display_rect()
        # Reposition text label if it exists
        if self.text_label and self.template_pixmap:
            self.reposition_text_label()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.template_pixmap:
            self.calculate_template_display_rect()
            
            # Scale and draw template to fill the calculated display rect exactly
            scaled_pixmap = self.template_pixmap.scaled(
                self.template_display_rect.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Draw the template
            painter.drawPixmap(self.template_display_rect.topLeft(), scaled_pixmap)
            
            # Draw a subtle border around the template area for clarity
            painter.setPen(QPen(QColor(150, 150, 150, 100), 1))
            painter.drawRect(self.template_display_rect)
            
            debug_log(f"Painted template: {self.template_display_rect} -> scaled to {scaled_pixmap.size()}")
        else:
            # Draw placeholder with better styling
            painter.setPen(QPen(QColor(128, 128, 128), 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "Load template image\n(Will resize to match aspect ratio)")
            
    def sizeHint(self):
        """Provide size hint based on template aspect ratio"""
        if self.original_template_size:
            # Calculate a reasonable size based on template aspect ratio
            base_width = 600
            base_height = int(base_width / self.template_aspect_ratio)
            return QSize(base_width, base_height)
        else:
            return QSize(600, 500)
            
    def add_text_label(self, text="Sample Title"):
        debug_log(f"Adding text label with text: '{text}'")
        
        # Safely remove existing text label
        if hasattr(self, 'text_label') and self.text_label:
            try:
                debug_log("Removing existing text label")
                self.text_label.hide()
                self.text_label.deleteLater()
                self.text_label = None
            except Exception as e:
                debug_log(f"Error removing existing label: {e}")
            
        # Create new text label
        self.text_label = DraggableTextLabel(self)
        self.text_label.text_content = text
        
        self.position_text_label_on_template()
        
        self.text_label.show()
        self.text_label.update_display()
        self.text_label.raise_()  # Bring to front
        
        debug_log(f"Text label created and shown with size: {self.text_label.size()}")
        return self.text_label
        
    def position_text_label_on_template(self):
        """Position text label in center of the displayed template"""
        if not self.text_label or not self.template_pixmap:
            return
            
        # IMPORTANT: Update display first to ensure correct scaling
        self.text_label.update_display()
            
        # Position in center of the displayed template area
        center_x = self.template_display_rect.x() + self.template_display_rect.width() // 2
        center_y = self.template_display_rect.y() + self.template_display_rect.height() // 2
        
        # Position text label so its center aligns with template center
        text_x = center_x - self.text_label.width() // 2
        text_y = center_y - self.text_label.height() // 2
        
        # Ensure text stays within template bounds
        text_x = max(self.template_display_rect.x(), 
                    min(text_x, self.template_display_rect.right() - self.text_label.width()))
        text_y = max(self.template_display_rect.y(), 
                    min(text_y, self.template_display_rect.bottom() - self.text_label.height()))
        
        self.text_label.move(text_x, text_y)
        debug_log(f"Positioned text label at ({text_x}, {text_y}) - center at ({center_x}, {center_y}) within template display rect {self.template_display_rect}")
        
        # Manually trigger position change signal with the new position
        self.text_label.position_changed.emit(text_x, text_y)
        
    def reposition_text_label(self):
        """Reposition text label when widget is resized"""
        if self.text_label:
            # Update display first to ensure correct scaling for new size
            self.text_label.update_display()
            # Then reposition
            self.position_text_label_on_template()

    def preview_to_template_coordinates(self, preview_x, preview_y):
        """Convert preview widget coordinates to original template coordinates"""
        debug_log(f"=== COORDINATE CONVERSION DEBUG ===")
        debug_log(f"Input preview coordinates: ({preview_x}, {preview_y})")
        
        if not self.template_pixmap or not self.original_template_size:
            debug_log(f"No template for conversion: preview ({preview_x}, {preview_y})")
            debug_log("=== END CONVERSION (NO TEMPLATE) ===")
            return preview_x, preview_y
            
        debug_log(f"Original template size: {self.original_template_size}")
        debug_log(f"Template display rect: {self.template_display_rect}")
        
        # Ensure display rect is valid
        if not self.template_display_rect.isValid() or self.template_display_rect.width() <= 0 or self.template_display_rect.height() <= 0:
            debug_log(f"ERROR: Invalid template display rect: {self.template_display_rect}")
            return preview_x, preview_y
        
        # Get position relative to displayed template
        rel_x = preview_x - self.template_display_rect.x()
        rel_y = preview_y - self.template_display_rect.y()
        
        debug_log(f"Relative position within display rect: ({rel_x}, {rel_y})")
        
        # Calculate scale factors
        scale_x = self.original_template_size.width() / self.template_display_rect.width()
        scale_y = self.original_template_size.height() / self.template_display_rect.height()
        
        debug_log(f"Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
        
        # Convert to template coordinates
        template_x = int(rel_x * scale_x)
        template_y = int(rel_y * scale_y)
        
        debug_log(f"Calculated template coordinates: ({template_x}, {template_y})")
        
        # Clamp to valid range
        template_x = max(0, min(template_x, self.original_template_size.width()))
        template_y = max(0, min(template_y, self.original_template_size.height()))
        
        debug_log(f"Clamped template coordinates: ({template_x}, {template_y})")
        
        # Validation warnings
        if rel_x < 0 or rel_y < 0:
            debug_log(f"WARNING: Preview coordinates are outside display area (negative relative position)")
        if rel_x > self.template_display_rect.width() or rel_y > self.template_display_rect.height():
            debug_log(f"WARNING: Preview coordinates are outside display area (exceeds display rect)")
            
        debug_log("=== END COORDINATE CONVERSION ===")
        return template_x, template_y

    def mousePressEvent(self, event):
        debug_log(f"PreviewWidget mouse press at: {event.pos()}")
        super().mousePressEvent(event)

class TitleOverlayWorker(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, template_path, titles, output_dir, settings):
        super().__init__()
        self.template_path = template_path
        self.titles = titles
        self.output_dir = output_dir
        self.settings = settings
        self.is_running = True
        
    def run(self):
        try:
            debug_log(f"Worker thread starting with {len(self.titles)} titles")
            
            # Load template image
            template = Image.open(self.template_path)
            total_titles = len(self.titles)
            
            for i, title in enumerate(self.titles):
                if not self.is_running:
                    break
                    
                # Create a copy of the template
                img = template.copy()
                draw = ImageDraw.Draw(img)
                
                # Load font with better error handling
                try:
                    font_path = self.find_font()
                    if font_path:
                        font = ImageFont.truetype(font_path, self.settings['font_size'])
                        debug_log(f"Using font for processing: {font_path}")
                        
                        # Verify font loaded correctly
                        test_bbox = ImageDraw.Draw(Image.new('RGB', (100, 100))).textbbox((0, 0), "Test", font=font)
                        debug_log(f"Font verification successful: {test_bbox}")
                    else:
                        font = ImageFont.load_default()
                        debug_log("Using PIL default font for processing")
                except Exception as font_error:
                    debug_log(f"Font loading error: {font_error}")
                    font = ImageFont.load_default()
                    debug_log("Falling back to PIL default font")
                
                # Use center position from preview settings
                center_x = self.settings['x_position']
                center_y = self.settings['y_position']
                
                # Process text for multi-line and auto-fitting
                processed_title, final_font_size = self.process_text_for_output(
                    title, font, template.size[0], self.settings
                )
                
                # Update font if size was adjusted
                if final_font_size != self.settings['font_size']:
                    try:
                        if font_path:
                            font = ImageFont.truetype(font_path, final_font_size)
                            debug_log(f"Font size adjusted to {final_font_size} using: {font_path}")
                        else:
                            font = ImageFont.load_default()
                            debug_log(f"Font size adjusted to {final_font_size} using default font")
                    except Exception as font_error:
                        debug_log(f"Error adjusting font size: {font_error}")
                        font = ImageFont.load_default()
                
                # Get text dimensions for positioning with margin considerations
                template_width = template.size[0]
                template_height = template.size[1]
                h_margin_px = int(template_width * (self.settings.get('h_margin', 5) / 100))
                v_margin_px = int(template_height * (self.settings.get('v_margin', 5) / 100))
                
                if self.settings.get('multi_line_text') and '\n' in processed_title:
                    # Multi-line text positioning
                    lines = processed_title.split('\n')
                    max_line_width = 0
                    line_height = font.size * (self.settings.get('line_spacing', 120) / 100)
                    total_height = line_height * len(lines)
                    
                    for line in lines:
                        line_bbox = draw.textbbox((0, 0), line, font=font)
                        line_width = line_bbox[2] - line_bbox[0]
                        max_line_width = max(max_line_width, line_width)
                    
                    text_width = max_line_width
                    text_height = total_height
                else:
                    # Single line text
                    bbox = draw.textbbox((0, 0), processed_title, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                
                # Calculate actual draw position based on alignment with margins
                if self.settings.get('text_alignment') == 'center':
                    # Center the text around the center point
                    x = center_x - text_width // 2
                    y = center_y - text_height // 2
                elif self.settings.get('text_alignment') == 'right':
                    # Right align - text ends at right margin
                    x = template_width - h_margin_px - text_width
                    y = center_y - text_height // 2
                elif self.settings.get('text_alignment') == 'left':
                    # Left align - text starts at left margin
                    x = h_margin_px
                    y = center_y - text_height // 2
                else:
                    # Default center
                    x = center_x - text_width // 2
                    y = center_y - text_height // 2
                
                # Ensure text stays within vertical margins
                y = max(v_margin_px, min(y, template_height - v_margin_px - text_height))
                
                debug_log(f"Margin-aware positioning:")
                debug_log(f"  Template size: {template_width}x{template_height}")
                debug_log(f"  H margin: {h_margin_px}px, V margin: {v_margin_px}px")
                debug_log(f"  Text size: {text_width}x{text_height}")
                debug_log(f"  Alignment: {self.settings.get('text_alignment')}")
                debug_log(f"  Final position: ({x}, {y})")
                
                # Draw text (multi-line or single line) with strong bold
                
                # Force debug logging for bold text
                if self.settings.get('is_bold', False):
                    debug_log("=== BATCH BOLD TEXT RENDERING DEBUG ===")
                    debug_log(f"Bold enabled: {self.settings.get('is_bold', False)}")
                    debug_log(f"Processing title: '{title}' -> '{processed_title}'")
                
                if self.settings.get('multi_line_text') and '\n' in processed_title:
                    self.draw_multiline_text(draw, processed_title, x, y, font, self.settings)
                else:
                    self.draw_single_text(draw, processed_title, x, y, font, self.settings)
                    
                if self.settings.get('is_bold', False):
                    debug_log("=== END BATCH BOLD TEXT RENDERING DEBUG ===")
                
                debug_log(f"Processing title '{title}' -> '{processed_title}' at center ({center_x}, {center_y}) -> draw at ({x}, {y}) with font size {final_font_size}, alignment: {self.settings['text_alignment']}")
                
                # Draw text (multi-line or single line)
                if self.settings.get('multi_line_text') and '\n' in processed_title:
                    self.draw_multiline_text(draw, processed_title, x, y, font, self.settings)
                else:
                    self.draw_single_text(draw, processed_title, x, y, font, self.settings)
                
                # Save the image
                safe_title = title.replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]
                output_filename = f"{self.settings['filename_prefix']}{i+1:04d}_{safe_title}.png"
                output_path = os.path.join(self.output_dir, output_filename)
                img.save(output_path, 'PNG')
                
                # Update progress
                progress = int((i + 1) / total_titles * 100)
                self.progress_updated.emit(progress)
                self.status_updated.emit(f"Processing: {title[:50]}... ({i+1}/{total_titles})")
                
            if self.is_running:
                self.status_updated.emit(f"Completed! Generated {total_titles} images.")
                debug_log(f"Processing completed successfully - {total_titles} images generated")
            else:
                self.status_updated.emit("Process cancelled.")
                debug_log("Processing was cancelled")
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.status_updated.emit(error_msg)
            debug_log(f"Worker thread error: {e}")
            traceback.print_exc()
        
        self.finished.emit()
    
    def process_text_for_output(self, text, font, template_width, settings):
        """Process text for output generation with multi-line and auto-fitting"""
        try:
            # Calculate available width with margins
            h_margin_px = int(template_width * (settings.get('h_margin', 5) / 100))
            usable_width = template_width - (2 * h_margin_px)  # Subtract both margins
            max_width = int(usable_width * (settings.get('max_text_width', 80) / 100))
            
            debug_log(f"Output text processing:")
            debug_log(f"  Template width: {template_width}px")
            debug_log(f"  H margin: {settings.get('h_margin', 5)}% = {h_margin_px}px each side")
            debug_log(f"  Usable width: {usable_width}px")
            debug_log(f"  Max text width: {max_width}px")
            
            # Get text width
            temp_img = Image.new('RGB', (100, 100))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                # Text fits as-is
                return text, settings['font_size']
            
            # Text doesn't fit
            if settings.get('multi_line_text', False):
                # Wrap to multiple lines
                wrapped_text = self.wrap_text_for_output(text, font, max_width)
                return wrapped_text, settings['font_size']
            elif settings.get('auto_fit_text', True):
                # Scale font down
                scale_factor = max_width / text_width
                new_font_size = max(8, int(settings['font_size'] * scale_factor * 0.95))
                debug_log(f"Auto-fitting font for output: {settings['font_size']} -> {new_font_size}")
                return text, new_font_size
            else:
                # No processing
                return text, settings['font_size']
                
        except Exception as e:
            debug_log(f"Error processing text for output: {e}")
            return text, settings['font_size']
    
    def wrap_text_for_output(self, text, font, max_width):
        """Wrap text for output generation"""
        try:
            temp_img = Image.new('RGB', (100, 100))
            temp_draw = ImageDraw.Draw(temp_img)
            
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = temp_draw.textbbox((0, 0), test_line, font=font)
                test_width = bbox[2] - bbox[0]
                
                if test_width <= max_width or not current_line:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return '\n'.join(lines)
            
        except Exception as e:
            debug_log(f"Error wrapping text for output: {e}")
            return text
    
    def draw_multiline_text(self, draw, text, x, y, font, settings):
        """Draw multi-line text with proper spacing and bold handling"""
        try:
            font_path = self.find_font()
            lines = text.split('\n')
            line_height = font.size * (settings.get('line_spacing', 120) / 100)
            
            for i, line in enumerate(lines):
                line_y = y + (i * line_height)
                
                # Draw outline if enabled
                if settings['outline_enabled']:
                    outline_color = tuple(settings['outline_color'])
                    outline_width = settings['outline_width']
                    
                    # Get the appropriate font for outline
                    outline_font = font
                    if settings.get('is_bold', False):
                        bold_font = self.get_bold_font(font_path, font.size)
                        if bold_font:
                            outline_font = bold_font
                    
                    for dx in range(-outline_width, outline_width + 1):
                        for dy in range(-outline_width, outline_width + 1):
                            if dx != 0 or dy != 0:
                                draw.text((x + dx, line_y + dy), line, font=outline_font, fill=outline_color)
                                
                                # Strong bold simulation for outline if no dedicated bold font
                                if settings.get('is_bold', False) and outline_font == font:
                                    for bold_offset in [(1, 0), (0, 1), (1, 1), (2, 0), (0, 2)]:
                                        draw.text((x + dx + bold_offset[0], line_y + dy + bold_offset[1]), line, font=outline_font, fill=outline_color)
                
                # Draw main text with strong bold simulation
                text_color = tuple(settings['text_color'])
                main_font = font
                
                if settings.get('is_bold', False):
                    bold_font = self.get_bold_font(font_path, font.size)
                    if bold_font:
                        # Use dedicated bold font
                        main_font = bold_font
                        draw.text((x, line_y), line, font=main_font, fill=text_color)
                    else:
                        # Very strong bold simulation - multiple passes
                        debug_log(f"Using strong bold simulation for line {i}: '{line}'")
                        
                        # First layer - original text
                        draw.text((x, line_y), line, font=main_font, fill=text_color)
                        
                        # Strong bold simulation with multiple offsets
                        bold_offsets = [
                            (1, 0), (2, 0),     # Right offsets
                            (0, 1), (0, 2),     # Down offsets  
                            (1, 1), (2, 1),     # Diagonal offsets
                            (1, 2), (2, 2),     # More diagonal
                            (-1, 0), (-1, 1)    # Left offsets for fill
                        ]
                        
                        for offset in bold_offsets:
                            draw.text((x + offset[0], line_y + offset[1]), line, font=main_font, fill=text_color)
                else:
                    # Regular text
                    draw.text((x, line_y), line, font=main_font, fill=text_color)
                    
        except Exception as e:
            debug_log(f"Error drawing multiline text: {e}")
            # Fallback to basic rendering
            lines = text.split('\n')
            line_height = font.size * 1.2
            for i, line in enumerate(lines):
                line_y = y + (i * line_height)
                draw.text((x, line_y), line, font=font, fill=tuple(settings['text_color']))
    
    def draw_single_text(self, draw, text, x, y, font, settings):
        """Draw single line text with proper bold handling"""
        try:
            font_path = self.find_font()
            
            # Draw outline if enabled
            if settings['outline_enabled']:
                outline_color = tuple(settings['outline_color'])
                outline_width = settings['outline_width']
                
                # Get the appropriate font for outline
                outline_font = font
                if settings.get('is_bold', False):
                    bold_font = self.get_bold_font(font_path, font.size)
                    if bold_font:
                        outline_font = bold_font
                
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), text, font=outline_font, fill=outline_color)
                            
                            # Strong bold simulation for outline if no dedicated bold font
                            if settings.get('is_bold', False) and outline_font == font:
                                # Multiple passes for bolder outline
                                for bold_offset in [(1, 0), (0, 1), (1, 1), (2, 0), (0, 2)]:
                                    draw.text((x + dx + bold_offset[0], y + dy + bold_offset[1]), text, font=outline_font, fill=outline_color)
            
            # Draw main text with strong bold simulation
            text_color = tuple(settings['text_color'])
            main_font = font
            
            if settings.get('is_bold', False):
                bold_font = self.get_bold_font(font_path, font.size)
                if bold_font:
                    # Use dedicated bold font
                    main_font = bold_font
                    draw.text((x, y), text, font=main_font, fill=text_color)
                    debug_log("Used dedicated bold font for main text")
                else:
                    # Very strong bold simulation - multiple passes with various offsets
                    debug_log("Using strong bold simulation for main text")
                    
                    # First layer - original text
                    draw.text((x, y), text, font=main_font, fill=text_color)
                    
                    # Second layer - horizontal and vertical offsets
                    bold_offsets = [
                        (1, 0), (2, 0),     # Right offsets
                        (0, 1), (0, 2),     # Down offsets  
                        (1, 1), (2, 1),     # Diagonal offsets
                        (1, 2), (2, 2),     # More diagonal
                        (-1, 0), (-1, 1)    # Left offsets for more fill
                    ]
                    
                    for offset in bold_offsets:
                        draw.text((x + offset[0], y + offset[1]), text, font=main_font, fill=text_color)
            else:
                # Regular text
                draw.text((x, y), text, font=main_font, fill=text_color)
                
        except Exception as e:
            debug_log(f"Error drawing single text: {e}")
            # Fallback to basic rendering
            draw.text((x, y), text, font=font, fill=tuple(settings['text_color']))
    
    def find_font(self):
        """Try to find a good font on the system, prioritizing Inter font"""
        # Primary font - Inter font from the specified path
        inter_font_path = r"D:\Script\Image Overlay Task\fonts\Inter-VariableFont_opsz,wght.ttf"
        
        # Define font paths for regular and bold variants
        font_paths = {
            'regular': [
                inter_font_path,
                "./fonts/Inter-VariableFont_opsz,wght.ttf",
                "fonts/Inter-VariableFont_opsz,wght.ttf",
                "D:/Script/Image Overlay Task/fonts/Inter-VariableFont_opsz,wght.ttf",
                os.path.join(os.getcwd(), "fonts", "Inter-VariableFont_opsz,wght.ttf"),
                
                # Try Inter Bold specifically
                r"D:\Script\Image Overlay Task\fonts\Inter-Bold.ttf",
                "./fonts/Inter-Bold.ttf",
                "fonts/Inter-Bold.ttf",
                
                # Fallback fonts
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/Arial.ttf",
                "/System/Library/Fonts/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ],
            'bold': [
                r"D:\Script\Image Overlay Task\fonts\Inter-Bold.ttf",
                "./fonts/Inter-Bold.ttf", 
                "fonts/Inter-Bold.ttf",
                inter_font_path,  # Variable font can handle bold weights
                
                # System bold fonts
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/Arial-Bold.ttf",
                "/System/Library/Fonts/Arial-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        }
        
        # Test regular font first
        regular_font = None
        for path in font_paths['regular']:
            if os.path.exists(path):
                try:
                    test_font = ImageFont.truetype(path, 12)
                    debug_log(f"Found regular font: {path}")
                    regular_font = path
                    break
                except Exception as e:
                    debug_log(f"PIL failed to load regular font {path}: {e}")
                    continue
        
        # Test bold font
        bold_font = None
        for path in font_paths['bold']:
            if os.path.exists(path):
                try:
                    test_font = ImageFont.truetype(path, 12)
                    debug_log(f"Found bold font: {path}")
                    bold_font = path
                    break
                except Exception as e:
                    debug_log(f"PIL failed to load bold font {path}: {e}")
                    continue
        
        if regular_font:
            debug_log(f"Using regular font: {regular_font}")
            debug_log(f"Using bold font: {bold_font if bold_font else 'simulated'}")
            return regular_font
        
        debug_log("No custom font found that PIL can load, using default")
        return None
    
    def get_bold_font(self, regular_font_path, font_size):
        """Get bold font variant or return None to use simulation"""
        if not regular_font_path:
            return None
            
        # Try to find bold variant
        bold_paths = [
            # If using Inter variable font, try specific bold file
            regular_font_path.replace("Inter-VariableFont_opsz,wght.ttf", "Inter-Bold.ttf"),
            regular_font_path.replace("Inter-Regular.ttf", "Inter-Bold.ttf"),
            
            # System bold fonts
            regular_font_path.replace("arial.ttf", "arialbd.ttf"),
            regular_font_path.replace("Arial.ttf", "Arial-Bold.ttf"),
        ]
        
        for bold_path in bold_paths:
            if os.path.exists(bold_path):
                try:
                    bold_font = ImageFont.truetype(bold_path, font_size)
                    debug_log(f"Using dedicated bold font: {bold_path}")
                    return bold_font
                except Exception as e:
                    debug_log(f"Failed to load bold font {bold_path}: {e}")
                    continue
        
        # For Inter variable font, try using weight parameter
        if "Inter-VariableFont" in regular_font_path:
            try:
                # Try to use PIL's font variation features for variable fonts
                bold_font = ImageFont.truetype(regular_font_path, font_size)
                # Note: PIL's support for variable font features is limited
                debug_log(f"Using variable font for bold: {regular_font_path}")
                return bold_font
            except Exception as e:
                debug_log(f"Variable font bold failed: {e}")
        
        debug_log("No dedicated bold font found, will use simulation")
        return None
    
    def stop(self):
        debug_log("Worker thread stop requested")
        self.is_running = False

class TitleOverlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        debug_log("Initializing TitleOverlayApp")
        
        self.setWindowTitle("Advanced Title Overlay Generator with Drag & Drop")
        self.setGeometry(100, 100, 1400, 900)  # Made wider for better aspect ratio support
        
        # Initialize variables
        self.template_path = ""
        self.titles = []
        self.output_dir = ""
        self.worker = None
        self.current_text_label = None
        
        # Default settings
        self.settings = {
            'font_size': 48,
            'text_color': [255, 255, 255],  # White
            'outline_enabled': True,
            'outline_color': [0, 0, 0],     # Black
            'outline_width': 2,
            'x_position': 100,
            'y_position': 100,
            'is_bold': False,
            'is_italic': False,
            'filename_prefix': 'title_',
            'text_alignment': 'center',  # Add alignment setting
            'auto_fit_text': True,       # Auto-fit text to template
            'multi_line_text': False,    # Allow multi-line text
            'max_text_width': 80,        # Max width as percentage of template
            'line_spacing': 120,         # Line spacing percentage
            'h_margin': 5,               # Horizontal margin percentage
            'v_margin': 5                # Vertical margin percentage
        }
        
        self.setup_ui()
        self.check_font_status()
        debug_log("TitleOverlayApp initialization complete")
        
    def check_font_status(self):
        """Check which font is available and update status"""
        debug_log("Checking font status")
        
        try:
            # Check if Inter font is available
            inter_font = QFont("Inter")
            
            if inter_font.family() == "Inter":
                self.font_status_label.setText("✅ Inter")
                self.font_status_label.setStyleSheet("font-size: 11px; color: green;")
                debug_log("Inter font is available")
            else:
                # Check for other fonts
                arial_font = QFont("Arial")
                
                if arial_font.family() == "Arial":
                    self.font_status_label.setText("⚠️ Arial")
                    self.font_status_label.setStyleSheet("font-size: 11px; color: orange;")
                    debug_log("Using Arial as fallback font")
                else:
                    self.font_status_label.setText("❌ Default")
                    self.font_status_label.setStyleSheet("font-size: 11px; color: red;")
                    debug_log("Using system default font")
            
            # Also check PIL font availability
            worker = TitleOverlayWorker(None, None, None, None)
            pil_font_path = worker.find_font()
            
            if pil_font_path and "Inter" in pil_font_path:
                debug_log(f"PIL will use Inter font: {pil_font_path}")
            elif pil_font_path:
                debug_log(f"PIL will use fallback font: {pil_font_path}")
            else:
                debug_log("PIL will use default font")
                
        except Exception as e:
            debug_log(f"Error checking font status: {e}")
            self.font_status_label.setText("❓ Unknown")
            self.font_status_label.setStyleSheet("font-size: 11px; color: gray;")
        
    def setup_ui(self):
        debug_log("Setting up UI")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QHBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        
        # Left panel for controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(420)  # Slightly reduced width
        left_panel.setMinimumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # File Selection Group
        file_group = QGroupBox("File Selection")
        file_layout = QGridLayout(file_group)
        
        # Template selection
        file_layout.addWidget(QLabel("Template:"), 0, 0)
        self.template_label = QLabel("No template selected")
        self.template_label.setStyleSheet("QLabel { border: 1px solid gray; padding: 5px; background-color: #2b2b2b; color: white; }")
        self.template_label.setFixedHeight(25)
        file_layout.addWidget(self.template_label, 0, 1)
        
        template_btn = QPushButton("Browse")
        template_btn.setFixedWidth(80)
        template_btn.clicked.connect(self.select_template)
        file_layout.addWidget(template_btn, 0, 2)
        
        # Titles file selection
        file_layout.addWidget(QLabel("Titles:"), 1, 0)
        self.titles_label = QLabel("No titles file selected")
        self.titles_label.setStyleSheet("QLabel { border: 1px solid gray; padding: 5px; background-color: #2b2b2b; color: white; }")
        self.titles_label.setFixedHeight(25)
        file_layout.addWidget(self.titles_label, 1, 1)
        
        titles_btn = QPushButton("Browse")
        titles_btn.setFixedWidth(80)
        titles_btn.clicked.connect(self.select_titles)
        file_layout.addWidget(titles_btn, 1, 2)
        
        # Output directory
        file_layout.addWidget(QLabel("Output:"), 2, 0)
        self.output_label = QLabel("No output directory selected")
        self.output_label.setStyleSheet("QLabel { border: 1px solid gray; padding: 5px; background-color: #2b2b2b; color: white; }")
        self.output_label.setFixedHeight(25)
        file_layout.addWidget(self.output_label, 2, 1)
        
        output_btn = QPushButton("Browse")
        output_btn.setFixedWidth(80)
        output_btn.clicked.connect(self.select_output_dir)
        file_layout.addWidget(output_btn, 2, 2)
        
        left_layout.addWidget(file_group)
        
        # Text Content Group
        text_content_group = QGroupBox("Text Content & Layout")
        text_content_layout = QVBoxLayout(text_content_group)
        
        # Current text input
        text_content_layout.addWidget(QLabel("Current Text:"))
        self.current_text_input = QLineEdit()
        self.current_text_input.setPlaceholderText("Enter text content here...")
        self.current_text_input.textChanged.connect(self.update_current_text)
        text_content_layout.addWidget(self.current_text_input)
        
        # Text handling options in a compact layout
        options_layout = QGridLayout()
        
        # Auto-fit and multi-line checkboxes
        self.auto_fit_check = QCheckBox("Auto-fit")
        self.auto_fit_check.setChecked(True)
        self.auto_fit_check.toggled.connect(self.toggle_auto_fit)
        options_layout.addWidget(self.auto_fit_check, 0, 0)
        
        self.multi_line_check = QCheckBox("Multi-line")
        self.multi_line_check.setChecked(False)
        self.multi_line_check.toggled.connect(self.toggle_multi_line)
        options_layout.addWidget(self.multi_line_check, 0, 1)
        
        # Max text width (percentage of template width)
        options_layout.addWidget(QLabel("Width:"), 1, 0)
        self.max_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_width_slider.setRange(20, 100)
        self.max_width_slider.setValue(80)
        self.max_width_slider.valueChanged.connect(self.update_max_width)
        options_layout.addWidget(self.max_width_slider, 1, 1)
        
        self.max_width_label = QLabel("80%")
        self.max_width_label.setFixedWidth(35)
        options_layout.addWidget(self.max_width_label, 1, 2)
        
        # Line spacing for multi-line text
        options_layout.addWidget(QLabel("Spacing:"), 2, 0)
        self.line_spacing_slider = QSlider(Qt.Orientation.Horizontal)
        self.line_spacing_slider.setRange(80, 200)
        self.line_spacing_slider.setValue(120)
        self.line_spacing_slider.valueChanged.connect(self.update_line_spacing)
        options_layout.addWidget(self.line_spacing_slider, 2, 1)
        
        self.line_spacing_label = QLabel("120%")
        self.line_spacing_label.setFixedWidth(35)
        options_layout.addWidget(self.line_spacing_label, 2, 2)
        
        # Margin controls
        options_layout.addWidget(QLabel("H.Margin:"), 3, 0)
        self.h_margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_margin_slider.setRange(0, 20)
        self.h_margin_slider.setValue(5)  # 5% horizontal margin
        self.h_margin_slider.valueChanged.connect(self.update_h_margin)
        options_layout.addWidget(self.h_margin_slider, 3, 1)
        
        self.h_margin_label = QLabel("5%")
        self.h_margin_label.setFixedWidth(35)
        options_layout.addWidget(self.h_margin_label, 3, 2)
        
        options_layout.addWidget(QLabel("V.Margin:"), 4, 0)
        self.v_margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.v_margin_slider.setRange(0, 20)
        self.v_margin_slider.setValue(5)  # 5% vertical margin
        self.v_margin_slider.valueChanged.connect(self.update_v_margin)
        options_layout.addWidget(self.v_margin_slider, 4, 1)
        
        self.v_margin_label = QLabel("5%")
        self.v_margin_label.setFixedWidth(35)
        options_layout.addWidget(self.v_margin_label, 4, 2)
        
        text_content_layout.addLayout(options_layout)
        
        # Text alignment
        text_content_layout.addWidget(QLabel("Alignment:"))
        alignment_layout = QHBoxLayout()
        
        self.alignment_group = QButtonGroup()
        
        self.left_align_radio = QRadioButton("Left")
        self.center_align_radio = QRadioButton("Center")
        self.right_align_radio = QRadioButton("Right")
        
        self.center_align_radio.setChecked(True)  # Default to center
        
        self.alignment_group.addButton(self.left_align_radio, 0)
        self.alignment_group.addButton(self.center_align_radio, 1)
        self.alignment_group.addButton(self.right_align_radio, 2)
        
        self.alignment_group.buttonToggled.connect(self.update_text_alignment)
        
        alignment_layout.addWidget(self.left_align_radio)
        alignment_layout.addWidget(self.center_align_radio)
        alignment_layout.addWidget(self.right_align_radio)
        text_content_layout.addLayout(alignment_layout)
        
        left_layout.addWidget(text_content_group)
        
        # Text Style Group
        style_group = QGroupBox("Text Style")
        style_layout = QGridLayout(style_group)
        
        # Font size slider
        style_layout.addWidget(QLabel("Font Size:"), 0, 0)
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 200)
        self.font_size_slider.setValue(self.settings['font_size'])
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        style_layout.addWidget(self.font_size_slider, 0, 1)
        
        self.font_size_label = QLabel("48")
        style_layout.addWidget(self.font_size_label, 0, 2)
        
        # Bold and Italic checkboxes
        self.bold_check = QCheckBox("Bold")
        self.bold_check.setChecked(self.settings['is_bold'])
        self.bold_check.toggled.connect(self.toggle_bold)
        style_layout.addWidget(self.bold_check, 1, 0)
        
        self.italic_check = QCheckBox("Italic")
        self.italic_check.setChecked(self.settings['is_italic'])
        self.italic_check.toggled.connect(self.toggle_italic)
        style_layout.addWidget(self.italic_check, 1, 1)
        
        # Text color
        style_layout.addWidget(QLabel("Text Color:"), 2, 0)
        self.text_color_btn = QPushButton()
        self.text_color_btn.setStyleSheet(f"background-color: rgb{tuple(self.settings['text_color'])};")
        self.text_color_btn.clicked.connect(self.select_text_color)
        style_layout.addWidget(self.text_color_btn, 2, 1)
        
        # Outline settings
        self.outline_check = QCheckBox("Enable Outline")
        self.outline_check.setChecked(self.settings['outline_enabled'])
        self.outline_check.toggled.connect(self.toggle_outline)
        style_layout.addWidget(self.outline_check, 3, 0)
        
        self.outline_color_btn = QPushButton("Outline Color")
        self.outline_color_btn.setStyleSheet(f"background-color: rgb{tuple(self.settings['outline_color'])};")
        self.outline_color_btn.clicked.connect(self.select_outline_color)
        style_layout.addWidget(self.outline_color_btn, 3, 1)
        
        style_layout.addWidget(QLabel("Outline Width:"), 4, 0)
        self.outline_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.outline_width_slider.setRange(1, 10)
        self.outline_width_slider.setValue(self.settings['outline_width'])
        self.outline_width_slider.valueChanged.connect(self.update_outline_width)
        style_layout.addWidget(self.outline_width_slider, 4, 1)
        
        self.outline_width_label = QLabel("2")
        style_layout.addWidget(self.outline_width_label, 4, 2)
        
        left_layout.addWidget(style_group)
        
        # Preview Controls
        preview_controls_group = QGroupBox("Preview Controls")
        preview_controls_layout = QVBoxLayout(preview_controls_group)
        
        # Primary controls
        primary_controls = QHBoxLayout()
        
        add_text_btn = QPushButton("Add Text")
        add_text_btn.clicked.connect(self.add_text_to_preview)
        primary_controls.addWidget(add_text_btn)
        
        center_text_btn = QPushButton("Center")
        center_text_btn.clicked.connect(self.force_text_center)
        primary_controls.addWidget(center_text_btn)
        
        preview_controls_layout.addLayout(primary_controls)
        
        # Secondary controls
        secondary_controls = QHBoxLayout()
        
        test_btn = QPushButton("Test Output")
        test_btn.clicked.connect(self.test_single_generation)
        secondary_controls.addWidget(test_btn)
        
        verify_btn = QPushButton("Verify")
        verify_btn.clicked.connect(self.verify_current_position)
        secondary_controls.addWidget(verify_btn)
        
        preview_controls_layout.addLayout(secondary_controls)
        
        # Advanced controls
        advanced_controls = QHBoxLayout()
        
        font_test_btn = QPushButton("Font Test")
        font_test_btn.clicked.connect(self.test_font_scaling)
        advanced_controls.addWidget(font_test_btn)
        
        long_text_btn = QPushButton("Long Text")
        long_text_btn.clicked.connect(self.test_long_text)
        advanced_controls.addWidget(long_text_btn)
        
        font_btn = QPushButton("Reload Font")
        font_btn.clicked.connect(self.test_font_and_reload)
        advanced_controls.addWidget(font_btn)
        
        preview_controls_layout.addLayout(advanced_controls)
        
        left_layout.addWidget(preview_controls_group)
        
        # Control buttons
        button_group = QGroupBox("Processing")
        button_layout = QVBoxLayout(button_group)
        
        self.start_btn = QPushButton("🚀 Start Processing All Titles")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Stop Processing")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        left_layout.addWidget(button_group)
        
        # Progress and status
        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready - Load template and titles to begin")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; }")
        left_layout.addWidget(self.status_label)
        
        # Status info in compact layout
        status_layout = QHBoxLayout()
        
        self.count_label = QLabel("Titles: 0")
        self.count_label.setStyleSheet("font-size: 11px; color: #666;")
        status_layout.addWidget(self.count_label)
        
        # Font status indicator
        self.font_status_label = QLabel("Font: Checking...")
        self.font_status_label.setStyleSheet("font-size: 11px; color: #666;")
        status_layout.addWidget(self.font_status_label)
        
        status_layout.addStretch()
        left_layout.addLayout(status_layout)
        
        left_layout.addStretch()
        
        # Right panel for preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_label = QLabel("Interactive Preview - Drag, resize, and edit text")
        preview_label.setStyleSheet("font-weight: bold; padding: 5px;")
        right_layout.addWidget(preview_label)
        
        # Create a scroll area for the preview to handle large templates
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")
        
        self.preview_widget = PreviewWidget()
        scroll_area.setWidget(self.preview_widget)
        right_layout.addWidget(scroll_area)
        
        # Compact help text
        help_text = QLabel("""
<b>Quick Guide:</b><br>
• Load template and titles → Add text → Drag to position<br>
• <b>Double-click text</b> to edit • <b>Auto-fit & Multi-line</b> for long text<br>
• <b>Margins:</b> H.Margin/V.Margin control text spacing from edges<br>
• Adjust width/spacing sliders • Test output to verify<br>
• Using Inter font for professional typography
        """)
        help_text.setStyleSheet("font-size: 11px; color: #666; padding: 8px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 4px;")
        help_text.setWordWrap(True)
        right_layout.addWidget(help_text)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([420, 980])  # Adjusted for optimized width
        
    def update_current_text(self):
        """Update the current text when input field changes"""
        new_text = self.current_text_input.text()
        if self.current_text_label and new_text:
            self.current_text_label.text_content = new_text
            self.current_text_label.update_display()
            debug_log(f"Updated current text to: '{new_text}'")
            
    def update_h_margin(self, value):
        debug_log(f"Horizontal margin changed to: {value}%")
        self.settings['h_margin'] = value
        self.h_margin_label.setText(f"{value}%")
        self.update_text_properties()
        
    def update_v_margin(self, value):
        debug_log(f"Vertical margin changed to: {value}%")
        self.settings['v_margin'] = value
        self.v_margin_label.setText(f"{value}%")
        self.update_text_properties()
        
    def toggle_auto_fit(self, checked):
        debug_log(f"Auto-fit toggled: {checked}")
        self.settings['auto_fit_text'] = checked
        self.update_text_properties()
        
    def toggle_multi_line(self, checked):
        debug_log(f"Multi-line toggled: {checked}")
        self.settings['multi_line_text'] = checked
        self.update_text_properties()
        
    def update_max_width(self, value):
        debug_log(f"Max width changed to: {value}%")
        self.settings['max_text_width'] = value
        self.max_width_label.setText(f"{value}%")
        self.update_text_properties()
        
    def update_line_spacing(self, value):
        debug_log(f"Line spacing changed to: {value}%")
        self.settings['line_spacing'] = value
        self.line_spacing_label.setText(f"{value}%")
        self.update_text_properties()
        
    def update_text_alignment(self, button, checked):
        """Update text alignment when radio button changes"""
        if checked:
            if button == self.left_align_radio:
                alignment = Qt.AlignmentFlag.AlignLeft
                self.settings['text_alignment'] = 'left'
            elif button == self.center_align_radio:
                alignment = Qt.AlignmentFlag.AlignCenter
                self.settings['text_alignment'] = 'center'
            elif button == self.right_align_radio:
                alignment = Qt.AlignmentFlag.AlignRight
                self.settings['text_alignment'] = 'right'
            
            if self.current_text_label:
                self.current_text_label.text_alignment = alignment
                self.current_text_label.update_display()
                
            debug_log(f"Text alignment updated to: {self.settings['text_alignment']}")
        
    def add_text_to_preview(self):
        debug_log("Add text to preview button clicked")
        
        # Use text from input field if available
        if self.current_text_input.text().strip():
            sample_text = self.current_text_input.text().strip()
        elif self.titles:
            sample_text = self.titles[0]
            debug_log(f"Using first title: '{sample_text}'")
        else:
            sample_text = "Sample Title Text"
            debug_log("No titles loaded, using sample text")
            
        self.current_text_label = self.preview_widget.add_text_label(sample_text)
        
        if self.current_text_label:
            debug_log("Text label created successfully")
            # Update the input field to match
            self.current_text_input.setText(sample_text)
            self.update_text_properties()
            
            # Connect signals
            try:
                self.current_text_label.position_changed.connect(self.on_text_position_changed)
                self.current_text_label.size_changed.connect(self.on_text_size_changed)
                self.current_text_label.text_edited.connect(self.on_text_edited)
                debug_log("Signals connected successfully")
                
                # IMPORTANT: Set initial position correctly
                self.update_position_from_preview()
                
            except Exception as e:
                debug_log(f"Error connecting signals: {e}")
                traceback.print_exc()
        else:
            debug_log("Failed to create text label")
            
    def update_position_from_preview(self):
        """Update settings position from current text label position in preview"""
        if not self.current_text_label:
            return
            
        try:
            # Get current position and size
            x = self.current_text_label.x()
            y = self.current_text_label.y()
            width = self.current_text_label.width()
            height = self.current_text_label.height()
            
            # Calculate center
            center_x = x + width // 2
            center_y = y + height // 2
            
            debug_log(f"Updating position from preview: label at ({x},{y}), center at ({center_x},{center_y})")
            
            # Convert to template coordinates
            template_x, template_y = self.preview_widget.preview_to_template_coordinates(center_x, center_y)
            
            # Update settings
            self.settings['x_position'] = template_x
            self.settings['y_position'] = template_y
            
            debug_log(f"Updated settings position to: ({template_x}, {template_y})")
            
        except Exception as e:
            debug_log(f"Error updating position from preview: {e}")
            traceback.print_exc()
            
    def on_text_edited(self, new_text):
        """Handle when text is edited directly in the preview"""
        debug_log(f"Text edited in preview: '{new_text}'")
        self.current_text_input.setText(new_text)
        
    def update_text_properties(self):
        debug_log("Updating text properties")
        if self.current_text_label:
            try:
                debug_log(f"Applying settings: font_size={self.settings['font_size']}, bold={self.settings['is_bold']}")
                self.current_text_label.font_size = self.settings['font_size']
                self.current_text_label.is_bold = self.settings['is_bold']
                self.current_text_label.is_italic = self.settings['is_italic']
                self.current_text_label.text_color = QColor(*self.settings['text_color'])
                self.current_text_label.outline_enabled = self.settings['outline_enabled']
                self.current_text_label.outline_color = QColor(*self.settings['outline_color'])
                self.current_text_label.outline_width = self.settings['outline_width']
                
                # Set alignment
                if self.settings['text_alignment'] == 'left':
                    self.current_text_label.text_alignment = Qt.AlignmentFlag.AlignLeft
                elif self.settings['text_alignment'] == 'center':
                    self.current_text_label.text_alignment = Qt.AlignmentFlag.AlignCenter
                elif self.settings['text_alignment'] == 'right':
                    self.current_text_label.text_alignment = Qt.AlignmentFlag.AlignRight
                    
                self.current_text_label.update_display()
                
                # Update position after display change (size might have changed)
                self.update_position_from_preview()
                
                debug_log("Text properties updated successfully")
            except Exception as e:
                debug_log(f"Error updating text properties: {e}")
                traceback.print_exc()
        else:
            debug_log("No current text label to update")
            
    def on_text_position_changed(self, x, y):
        try:
            debug_log(f"=== TEXT POSITION CHANGE DEBUG ===")
            debug_log(f"Text label moved to preview coordinates: ({x}, {y})")
            
            # Get the center point of the text label for consistent positioning
            if self.current_text_label:
                label_width = self.current_text_label.width()
                label_height = self.current_text_label.height()
                center_x = x + label_width // 2
                center_y = y + label_height // 2
                
                debug_log(f"Text label size: {label_width}x{label_height}")
                debug_log(f"Text label center in preview: ({center_x}, {center_y})")
                debug_log(f"Preview widget size: {self.preview_widget.size()}")
                debug_log(f"Template display rect: {self.preview_widget.template_display_rect}")
                
                # Convert preview coordinates to template coordinates
                template_x, template_y = self.preview_widget.preview_to_template_coordinates(center_x, center_y)
                
                # Validation check
                if hasattr(self.preview_widget, 'original_template_size') and self.preview_widget.original_template_size:
                    template_size = self.preview_widget.original_template_size
                    debug_log(f"Template size validation: {template_size}")
                    if template_x < 0 or template_y < 0 or template_x > template_size.width() or template_y > template_size.height():
                        debug_log(f"WARNING: Converted coordinates ({template_x}, {template_y}) are outside template bounds!")
                
                self.settings['x_position'] = template_x
                self.settings['y_position'] = template_y
                
                debug_log(f"Final template center position: ({template_x}, {template_y})")
                debug_log("=== END POSITION CHANGE DEBUG ===")
        except Exception as e:
            debug_log(f"Error updating position: {e}")
            traceback.print_exc()
            
    def on_text_size_changed(self, width, height):
        try:
            debug_log(f"Text size changed to: {width}x{height}")
            if self.current_text_label:
                old_font_size = self.settings['font_size']
                self.settings['font_size'] = self.current_text_label.font_size
                
                # Update UI controls
                self.font_size_slider.setValue(self.settings['font_size'])
                self.font_size_label.setText(str(self.settings['font_size']))
                
                debug_log(f"Font size changed from {old_font_size} to {self.settings['font_size']}")
        except Exception as e:
            debug_log(f"Error updating size: {e}")
            traceback.print_exc()
            
    def test_font_and_reload(self):
        """Test font availability and reload font status"""
        debug_log("Testing font and reloading status")
        
        try:
            # Check Inter font file existence
            inter_font_path = r"D:\Script\Image Overlay Task\fonts\Inter-VariableFont_opsz,wght.ttf"
            inter_bold_path = r"D:\Script\Image Overlay Task\fonts\Inter-Bold.ttf"
            
            if os.path.exists(inter_font_path):
                self.status_label.setText(f"✅ Inter font file found: {os.path.basename(inter_font_path)}")
                
                # Test PIL font loading specifically
                try:
                    pil_test_font = ImageFont.truetype(inter_font_path, 24)
                    debug_log(f"PIL successfully loaded Inter font: {inter_font_path}")
                    
                    # Test bold font availability
                    if os.path.exists(inter_bold_path):
                        try:
                            pil_bold_font = ImageFont.truetype(inter_bold_path, 24)
                            debug_log(f"PIL successfully loaded Inter Bold font: {inter_bold_path}")
                            self.status_label.setText(f"✅ Inter regular + bold fonts loaded in PIL")
                        except Exception as bold_error:
                            debug_log(f"PIL failed to load Inter Bold: {bold_error}")
                            self.status_label.setText(f"✅ Inter regular loaded, bold will be simulated")
                    else:
                        debug_log("Inter-Bold.ttf not found, bold will be simulated")
                        self.status_label.setText(f"✅ Inter regular loaded, bold will be simulated")
                        
                except Exception as pil_error:
                    debug_log(f"PIL failed to load Inter font: {pil_error}")
                    self.status_label.setText(f"❌ PIL cannot load Inter font: {str(pil_error)}")
                
                # Try to reload the font in Qt
                font_id = QFontDatabase.addApplicationFont(inter_font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    debug_log(f"Qt reloaded font families: {font_families}")
                else:
                    debug_log("Qt failed to reload Inter font")
            else:
                self.status_label.setText(f"❌ Inter font file not found: {inter_font_path}")
                debug_log(f"Inter font file does not exist: {inter_font_path}")
                
                # Check current working directory
                cwd = os.getcwd()
                debug_log(f"Current working directory: {cwd}")
                
                # List fonts directory if it exists
                fonts_dir = os.path.join(cwd, "fonts")
                if os.path.exists(fonts_dir):
                    fonts_list = os.listdir(fonts_dir)
                    debug_log(f"Fonts directory contents: {fonts_list}")
                    
                    # Check for Inter Bold specifically
                    if "Inter-Bold.ttf" in fonts_list:
                        debug_log("✅ Inter-Bold.ttf found in fonts directory")
                    else:
                        debug_log("❌ Inter-Bold.ttf not found in fonts directory")
                        debug_log("💡 Consider adding Inter-Bold.ttf for better bold rendering")
                else:
                    debug_log("No fonts directory found in current working directory")
            
            # Update font status
            self.check_font_status()
            
            # Update current text if available
            if self.current_text_label:
                self.current_text_label.update_display()
                
            # Test PIL font loading with worker including bold support
            worker = TitleOverlayWorker(None, None, None, None)
            pil_font_path = worker.find_font()
            if pil_font_path:
                debug_log(f"Worker found font: {pil_font_path}")
                if "Inter" in pil_font_path:
                    # Test bold font support
                    bold_font = worker.get_bold_font(pil_font_path, 24)
                    if bold_font:
                        debug_log("✅ PIL will use Inter with dedicated bold font for output")
                    else:
                        debug_log("✅ PIL will use Inter with enhanced bold simulation for output")
                else:
                    debug_log(f"⚠️ PIL will use fallback font: {os.path.basename(pil_font_path)}")
            else:
                debug_log("❌ PIL will use default font for output generation")
                
        except Exception as e:
            debug_log(f"Error testing font: {e}")
            traceback.print_exc()
            self.status_label.setText(f"Error testing font: {str(e)}")
            
    def test_bold_rendering(self):
        """Test bold text rendering specifically"""
        debug_log("=== BOLD RENDERING TEST ===")
        
        try:
            # Set text to a bold test
            self.current_text_input.setText("BOLD TEST TEXT")
            
            # Enable bold
            self.bold_check.setChecked(True)
            self.toggle_bold(True)
            
            # Add/update text in preview
            if self.current_text_label:
                self.current_text_label.text_content = "BOLD TEST TEXT"
                self.current_text_label.is_bold = True
                self.current_text_label.update_display()
            else:
                self.add_text_to_preview()
            
            # Generate test image immediately
            self.test_single_generation()
            
            debug_log("Bold test completed - check output image for bold effect")
            self.status_label.setText("Bold test completed - check test_output_debug.png")
            
        except Exception as e:
            debug_log(f"Error in bold test: {e}")
            traceback.print_exc()
            self.status_label.setText(f"Bold test error: {str(e)}")
            
    def test_long_text(self):
        """Test the app with a sample of long text"""
        debug_log("Testing with long text")
        
        long_text_samples = [
            "Global Renewable Energy Market Analysis and Future Growth Projections Report",
            "Comprehensive Study of Advanced Artificial Intelligence Applications in Healthcare and Medical Research",
            "Economic Impact Assessment of Digital Transformation on Small and Medium Enterprises in Developing Countries",
            "Climate Change Adaptation Strategies for Sustainable Urban Development in Coastal Cities Worldwide"
        ]
        
        # Use the first sample
        test_text = long_text_samples[0]
        
        # Set the text in the input field
        self.current_text_input.setText(test_text)
        
        # Enable multi-line if not already enabled
        if not self.multi_line_check.isChecked():
            self.multi_line_check.setChecked(True)
            self.toggle_multi_line(True)
        
        # Enable auto-fit if not already enabled
        if not self.auto_fit_check.isChecked():
            self.auto_fit_check.setChecked(True)
            self.toggle_auto_fit(True)
        
        # Add/update text in preview
        if self.current_text_label:
            self.current_text_label.text_content = test_text
            self.current_text_label.update_display()
        else:
            self.add_text_to_preview()
        
        self.status_label.setText(f"Testing with long text: '{test_text[:50]}...' - Check multi-line and auto-fit options")
        debug_log(f"Long text test applied: '{test_text}'")
        
    def test_font_scaling(self):
        """Test and display font scaling information"""
        debug_log("=== FONT SCALING TEST ===")
        
        if not self.current_text_label or not self.preview_widget.original_template_size:
            self.status_label.setText("Error: Add text and load template first")
            return
            
        try:
            template_size = self.preview_widget.original_template_size
            display_rect = self.preview_widget.template_display_rect
            
            debug_log(f"Template size: {template_size}")
            debug_log(f"Display rect: {display_rect}")
            debug_log(f"Settings font size: {self.settings['font_size']}")
            
            if display_rect.isValid() and display_rect.width() > 0:
                scale_factor = display_rect.width() / template_size.width()
                preview_font_size = max(8, int(self.settings['font_size'] * scale_factor))
                
                debug_log(f"Scale factor: {scale_factor:.3f}")
                debug_log(f"Calculated preview font size: {preview_font_size}")
                
                # Get actual font size being used in preview
                actual_font = self.current_text_label.font()
                actual_size = actual_font.pointSize()
                
                debug_log(f"Actual preview font size: {actual_size}")
                
                # Calculate what the text size should be in the output
                # Create a test font at template scale
                try:
                    from PIL import ImageFont
                    worker = TitleOverlayWorker(None, None, None, None)
                    font_path = worker.find_font()
                    if font_path:
                        pil_font = ImageFont.truetype(font_path, self.settings['font_size'])
                    else:
                        pil_font = ImageFont.load_default()
                    
                    # Create a temporary image to measure text
                    from PIL import Image, ImageDraw
                    temp_img = Image.new('RGB', (100, 100))
                    temp_draw = ImageDraw.Draw(temp_img)
                    bbox = temp_draw.textbbox((0, 0), self.current_text_label.text_content, font=pil_font)
                    output_text_width = bbox[2] - bbox[0]
                    output_text_height = bbox[3] - bbox[1]
                    
                    debug_log(f"Expected output text size: {output_text_width}x{output_text_height}")
                    
                    # Calculate what this should be in preview
                    expected_preview_width = output_text_width * scale_factor
                    expected_preview_height = output_text_height * scale_factor
                    
                    debug_log(f"Expected preview text size: {expected_preview_width:.1f}x{expected_preview_height:.1f}")
                    debug_log(f"Actual preview text size: {self.current_text_label.width()}x{self.current_text_label.height()}")
                    
                    # Check if sizes match
                    width_ratio = self.current_text_label.width() / expected_preview_width if expected_preview_width > 0 else 0
                    height_ratio = self.current_text_label.height() / expected_preview_height if expected_preview_height > 0 else 0
                    
                    debug_log(f"Size ratios: width={width_ratio:.2f}, height={height_ratio:.2f}")
                    
                    if 0.8 <= width_ratio <= 1.2 and 0.8 <= height_ratio <= 1.2:
                        status = "✅ Font scaling appears correct"
                    else:
                        status = f"❌ Font scaling issue: ratios {width_ratio:.2f}, {height_ratio:.2f}"
                        
                except Exception as e:
                    debug_log(f"Error calculating output text size: {e}")
                    status = "⚠️ Could not verify output text size"
                
            else:
                status = "❌ Invalid display rect for scaling test"
                
            self.status_label.setText(status)
            debug_log("=== END FONT SCALING TEST ===")
            
        except Exception as e:
            debug_log(f"Error testing font scaling: {e}")
            traceback.print_exc()
            self.status_label.setText(f"Font scaling test error: {str(e)}")
            
    def verify_current_position(self):
        """Verify and display current position information"""
        debug_log("=== POSITION VERIFICATION ===")
        
        if not self.current_text_label:
            self.status_label.setText("No text label to verify")
            return
            
        try:
            # Get current preview position
            preview_x = self.current_text_label.x()
            preview_y = self.current_text_label.y()
            width = self.current_text_label.width()
            height = self.current_text_label.height()
            center_x = preview_x + width // 2
            center_y = preview_y + height // 2
            
            debug_log(f"Preview position: ({preview_x}, {preview_y})")
            debug_log(f"Text size: {width}x{height}")
            debug_log(f"Preview center: ({center_x}, {center_y})")
            debug_log(f"Current settings: ({self.settings['x_position']}, {self.settings['y_position']})")
            
            # Convert to template coordinates
            template_x, template_y = self.preview_widget.preview_to_template_coordinates(center_x, center_y)
            
            debug_log(f"Converted template coords: ({template_x}, {template_y})")
            
            # Check if they match settings
            if template_x == self.settings['x_position'] and template_y == self.settings['y_position']:
                status = "✅ MATCH: Preview and settings are synchronized"
            else:
                status = f"❌ MISMATCH: Settings({self.settings['x_position']}, {self.settings['y_position']}) != Converted({template_x}, {template_y})"
                debug_log("COORDINATE MISMATCH DETECTED!")
                
                # Update settings to match current position
                self.settings['x_position'] = template_x
                self.settings['y_position'] = template_y
                debug_log(f"Settings updated to match current position: ({template_x}, {template_y})")
            
            self.status_label.setText(status)
            debug_log("=== END VERIFICATION ===")
            
        except Exception as e:
            debug_log(f"Error verifying position: {e}")
            traceback.print_exc()
            self.status_label.setText(f"Verification error: {str(e)}")
            
    def force_text_center(self):
        """Force text to center of template for debugging"""
        debug_log("Forcing text to template center")
        
        if not self.current_text_label or not self.preview_widget.original_template_size:
            debug_log("Cannot center - no text label or template")
            self.status_label.setText("Error: Add text and load template first")
            return
            
        try:
            # Get template center in template coordinates
            template_size = self.preview_widget.original_template_size
            template_center_x = template_size.width() // 2
            template_center_y = template_size.height() // 2
            
            debug_log(f"Template size: {template_size}")
            debug_log(f"Template center: ({template_center_x}, {template_center_y})")
            
            # Update settings FIRST
            self.settings['x_position'] = template_center_x
            self.settings['y_position'] = template_center_y
            
            # Now position the text in the preview to match
            if self.preview_widget.template_display_rect.isValid():
                # Convert template center back to preview coordinates
                display_rect = self.preview_widget.template_display_rect
                
                # Calculate relative position within the template (0.5, 0.5 for center)
                rel_x_ratio = template_center_x / template_size.width()
                rel_y_ratio = template_center_y / template_size.height()
                
                # Convert to preview coordinates
                preview_center_x = display_rect.x() + (rel_x_ratio * display_rect.width())
                preview_center_y = display_rect.y() + (rel_y_ratio * display_rect.height())
                
                # Position text label so its center is at the calculated preview center
                text_x = preview_center_x - self.current_text_label.width() // 2
                text_y = preview_center_y - self.current_text_label.height() // 2
                
                debug_log(f"Preview center: ({preview_center_x}, {preview_center_y})")
                debug_log(f"Text label position: ({text_x}, {text_y})")
                
                self.current_text_label.move(int(text_x), int(text_y))
                
                # Manually emit position change to ensure settings are synchronized
                self.current_text_label.position_changed.emit(int(text_x), int(text_y))
                
            self.status_label.setText(f"Text centered at template coordinates ({template_center_x}, {template_center_y})")
            debug_log("Text centered successfully")
            
        except Exception as e:
            debug_log(f"Error centering text: {e}")
            traceback.print_exc()
            self.status_label.setText(f"Error centering text: {str(e)}")
            
    def test_single_generation(self):
        """Generate a single test image to verify positioning"""
        debug_log("Testing single image generation")
        
        if not self.template_path or not self.current_text_label:
            debug_log("Cannot test - missing template or text label")
            self.status_label.setText("Error: Load template and add text first")
            return
            
        try:
            # Load template
            template = Image.open(self.template_path)
            img = template.copy()
            draw = ImageDraw.Draw(img)
            
            # Get test title
            test_title = self.current_text_label.text_content
            
            # Load font
            try:
                worker = TitleOverlayWorker(None, None, None, None)
                font_path = worker.find_font()
                if font_path:
                    font = ImageFont.truetype(font_path, self.settings['font_size'])
                    debug_log(f"Test generation using font: {font_path}")
                else:
                    font = ImageFont.load_default()
                    debug_log("Test generation using default font")
            except Exception as font_error:
                debug_log(f"Test font loading error: {font_error}")
                font = ImageFont.load_default()
            
            # DEBUG: Print all coordinate information
            debug_log("=== COORDINATE DEBUG INFO ===")
            debug_log(f"Template actual size: {template.size}")
            debug_log(f"Preview widget size: {self.preview_widget.size()}")
            debug_log(f"Template display rect: {self.preview_widget.template_display_rect}")
            debug_log(f"Current text label position: {self.current_text_label.pos()}")
            debug_log(f"Current text label size: {self.current_text_label.size()}")
            debug_log(f"Settings position: ({self.settings['x_position']}, {self.settings['y_position']})")
            debug_log(f"Settings font size: {self.settings['font_size']}")
            
            # Calculate what the preview font size should be
            if self.preview_widget.template_display_rect.isValid():
                scale_factor = self.preview_widget.template_display_rect.width() / template.size[0]
                preview_font_size = int(self.settings['font_size'] * scale_factor)
                debug_log(f"Preview scale factor: {scale_factor:.3f}")
                debug_log(f"Calculated preview font size: {preview_font_size}")
            
            # Use center position from preview settings
            center_x = self.settings['x_position']
            center_y = self.settings['y_position']
            
            # Process text for multi-line and auto-fitting (same as worker)
            worker = TitleOverlayWorker(None, None, None, None)
            processed_title, final_font_size = worker.process_text_for_output(
                test_title, font, template.size[0], self.settings
            )
            
            # Update font if size was adjusted
            if final_font_size != self.settings['font_size']:
                try:
                    worker = TitleOverlayWorker(None, None, None, None)
                    font_path = worker.find_font()
                    if font_path:
                        font = ImageFont.truetype(font_path, final_font_size)
                        debug_log(f"Adjusted font size to {final_font_size} using: {font_path}")
                    else:
                        font = ImageFont.load_default()
                        debug_log(f"Adjusted font size to {final_font_size} using default font")
                except Exception as font_error:
                    debug_log(f"Error loading adjusted font: {font_error}")
                    font = ImageFont.load_default()
            
            # Get text dimensions for positioning with margin considerations
            template_width = template.size[0]
            template_height = template.size[1]
            h_margin_px = int(template_width * (self.settings.get('h_margin', 5) / 100))
            v_margin_px = int(template_height * (self.settings.get('v_margin', 5) / 100))
            
            if self.settings.get('multi_line_text') and '\n' in processed_title:
                # Multi-line text positioning
                lines = processed_title.split('\n')
                max_line_width = 0
                line_height = font.size * (self.settings.get('line_spacing', 120) / 100)
                total_height = line_height * len(lines)
                
                for line in lines:
                    line_bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = line_bbox[2] - line_bbox[0]
                    max_line_width = max(max_line_width, line_width)
                
                text_width = max_line_width
                text_height = total_height
            else:
                # Single line text
                bbox = draw.textbbox((0, 0), processed_title, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            
            debug_log(f"Text dimensions: {text_width}x{text_height}")
            debug_log(f"Processed title: '{processed_title}' (original: '{test_title}')")
            debug_log(f"Final font size: {final_font_size} (original: {self.settings['font_size']})")
            debug_log(f"Template margins: H={h_margin_px}px, V={v_margin_px}px")
            
            # Calculate actual draw position based on alignment with margins (same logic as worker)
            if self.settings.get('text_alignment') == 'center':
                x = center_x - text_width // 2
                y = center_y - text_height // 2
            elif self.settings.get('text_alignment') == 'right':
                x = template_width - h_margin_px - text_width
                y = center_y - text_height // 2
            elif self.settings.get('text_alignment') == 'left':
                x = h_margin_px
                y = center_y - text_height // 2
            else:
                x = center_x - text_width // 2
                y = center_y - text_height // 2
            
            # Ensure text stays within vertical margins
            y = max(v_margin_px, min(y, template_height - v_margin_px - text_height))
            
            debug_log(f"Final draw position: ({x}, {y})")
            debug_log("=== END COORDINATE DEBUG ===")
            
            # Check if position is within template bounds
            if x < 0 or y < 0 or x > template.size[0] or y > template.size[1]:
                debug_log(f"WARNING: Text position ({x}, {y}) is outside template bounds {template.size}")
                # Clamp to template bounds for testing
                x = max(0, min(x, template.size[0] - text_width))
                y = max(0, min(y, template.size[1] - text_height))
                debug_log(f"Clamped position to: ({x}, {y})")
            
            # Draw text (multi-line or single line) - same as worker with strong bold
            worker = TitleOverlayWorker(None, None, None, None)
            
            # Force debug logging for bold text
            if self.settings.get('is_bold', False):
                debug_log("=== BOLD TEXT RENDERING DEBUG ===")
                debug_log(f"Bold enabled in settings: {self.settings.get('is_bold', False)}")
                debug_log(f"Text to render: '{processed_title}'")
                debug_log("About to call draw functions with bold enabled")
            
            if self.settings.get('multi_line_text') and '\n' in processed_title:
                worker.draw_multiline_text(draw, processed_title, x, y, font, self.settings)
            else:
                worker.draw_single_text(draw, processed_title, x, y, font, self.settings)
                
            if self.settings.get('is_bold', False):
                debug_log("=== END BOLD TEXT RENDERING DEBUG ===")
            
            # Draw a red dot at the center position for debugging
            debug_center_x, debug_center_y = center_x, center_y
            if 0 <= debug_center_x < template.size[0] and 0 <= debug_center_y < template.size[1]:
                # Draw a small red cross at the center point
                for i in range(-5, 6):
                    if 0 <= debug_center_x + i < template.size[0]:
                        img.putpixel((debug_center_x + i, debug_center_y), (255, 0, 0))
                    if 0 <= debug_center_y + i < template.size[1]:
                        img.putpixel((debug_center_x, debug_center_y + i), (255, 0, 0))
            
            # Save test image
            test_path = "test_output_debug.png"
            img.save(test_path, 'PNG')
            
            debug_log(f"Test image saved as: {test_path}")
            self.status_label.setText(f"Debug test image generated: {test_path}")
            
        except Exception as e:
            debug_log(f"Test generation error: {e}")
            traceback.print_exc()
            self.status_label.setText(f"Test generation failed: {str(e)}")
            
    def update_font_size(self, value):
        debug_log(f"Font size slider changed to: {value}")
        self.settings['font_size'] = value
        self.font_size_label.setText(str(value))
        self.update_text_properties()
        
    def toggle_bold(self, checked):
        debug_log(f"Bold toggled: {checked}")
        self.settings['is_bold'] = checked
        self.update_text_properties()
        
    def toggle_italic(self, checked):
        debug_log(f"Italic toggled: {checked}")
        self.settings['is_italic'] = checked
        self.update_text_properties()
        
    def toggle_outline(self, checked):
        debug_log(f"Outline toggled: {checked}")
        self.settings['outline_enabled'] = checked
        self.update_text_properties()
        
    def update_outline_width(self, value):
        debug_log(f"Outline width changed to: {value}")
        self.settings['outline_width'] = value
        self.outline_width_label.setText(str(value))
        self.update_text_properties()
        
    def select_text_color(self):
        debug_log("Selecting text color")
        color = QColorDialog.getColor()
        if color.isValid():
            self.settings['text_color'] = [color.red(), color.green(), color.blue()]
            self.text_color_btn.setStyleSheet(f"background-color: {color.name()};")
            debug_log(f"Text color changed to: {color.name()}")
            self.update_text_properties()
            
    def select_outline_color(self):
        debug_log("Selecting outline color")
        color = QColorDialog.getColor()
        if color.isValid():
            self.settings['outline_color'] = [color.red(), color.green(), color.blue()]
            self.outline_color_btn.setStyleSheet(f"background-color: {color.name()};")
            debug_log(f"Outline color changed to: {color.name()}")
            self.update_text_properties()
            
    def select_template(self):
        debug_log("Selecting template image")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Template Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if file_path:
            debug_log(f"Template selected: {file_path}")
            self.template_path = file_path
            self.template_label.setText(os.path.basename(file_path))
            
            # Load and display template in preview
            try:
                pixmap = QPixmap(file_path)
                debug_log(f"Template loaded with size: {pixmap.size()}")
                self.preview_widget.set_template(pixmap)
                
                # Force multiple repaints and calculations to ensure everything is set up
                self.preview_widget.repaint()
                self.preview_widget.updateGeometry()
                QApplication.processEvents()  # Process any pending events
                self.preview_widget.calculate_template_display_rect()
                
                debug_log(f"Final template display rect: {self.preview_widget.template_display_rect}")
                self.check_ready_state()
                
                # Update status
                self.status_label.setText(f"Template loaded: {pixmap.width()}x{pixmap.height()}")
                
            except Exception as e:
                debug_log(f"Error loading template: {e}")
                traceback.print_exc()
            
    def select_titles(self):
        debug_log("Selecting titles file")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Titles File", "", 
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            debug_log(f"Titles file selected: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.endswith('.csv'):
                        import csv
                        reader = csv.reader(f)
                        self.titles = [row[0] for row in reader if row]
                    else:
                        self.titles = [line.strip() for line in f if line.strip()]
                
                debug_log(f"Loaded {len(self.titles)} titles")
                self.titles_label.setText(f"{os.path.basename(file_path)} ({len(self.titles)} titles)")
                self.count_label.setText(f"Titles: {len(self.titles)}")
                self.check_ready_state()
                
            except Exception as e:
                debug_log(f"Error loading titles: {e}")
                self.status_label.setText(f"Error loading titles: {str(e)}")
                traceback.print_exc()
                
    def select_output_dir(self):
        debug_log("Selecting output directory")
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            debug_log(f"Output directory selected: {dir_path}")
            self.output_dir = dir_path
            self.output_label.setText(os.path.basename(dir_path))
            self.check_ready_state()
            
    def check_ready_state(self):
        ready = bool(self.template_path and self.titles and self.output_dir)
        debug_log(f"Ready state check: template={bool(self.template_path)}, titles={bool(self.titles)}, output={bool(self.output_dir)} -> ready={ready}")
        self.start_btn.setEnabled(ready)
        
    def start_processing(self):
        debug_log("Starting batch processing")
        if not self.template_path or not self.titles or not self.output_dir:
            debug_log("Cannot start - missing requirements")
            return
            
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Create worker thread with CURRENT settings (not a copy)
        debug_log(f"Creating worker thread with {len(self.titles)} titles")
        debug_log(f"Current bold setting being passed to worker: {self.settings.get('is_bold', False)}")
        
        self.worker = TitleOverlayWorker(
            self.template_path, self.titles, self.output_dir, self.settings  # Pass reference, not copy
        )
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()
        
    def stop_processing(self):
        debug_log("Stopping processing")
        if self.worker:
            self.worker.stop()
            
    def processing_finished(self):
        debug_log("Processing finished")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker = None

def main():
    debug_log("Starting application")
    app = QApplication(sys.argv)
    
    # Register Inter font as the primary font
    inter_font_path = r"D:\Script\Image Overlay Task\fonts\Inter-VariableFont_opsz,wght.ttf"
    
    font_paths_to_register = [
        inter_font_path,
        "./fonts/Inter-VariableFont_opsz,wght.ttf",
        "fonts/Inter-VariableFont_opsz,wght.ttf",
        "Roboto-Regular.ttf",
        "./fonts/Roboto-Regular.ttf",
        "C:/Windows/Fonts/Roboto-Regular.ttf",
        "/System/Library/Fonts/Roboto.ttf",
        "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf"
    ]
    
    font_loaded = False
    for path in font_paths_to_register:
        if os.path.exists(path):
            debug_log(f"Loading font from: {path}")
            font_id = QFontDatabase.addApplicationFont(path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                debug_log(f"Successfully loaded font families: {font_families}")
                font_loaded = True
                break
            else:
                debug_log(f"Failed to load font from: {path}")
    
    if not font_loaded:
        debug_log("No custom font loaded, using system default")
    
    debug_log("Creating main window")
    window = TitleOverlayApp()
    window.show()
    
    debug_log("Application ready - starting event loop")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()