from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QImage, QColor
from PyQt6.QtCore import Qt, QPoint, QRect

class DrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StaticContents)
        self.drawing = False
        self.setStyle(self.style())
        self.last_point = QPoint()
        self.image = QImage(self.size(), QImage.Format.Format_RGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.current_thickness = 12
        self.overlay_text = ""
        self.show_overlay = False
    def set_overlay(self, text, show=True):
        self.overlay_text = text
        self.show_overlay = show
        self.update()
    def paintEvent(self, event):
        canvas_painter = QPainter(self)
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

        if self.show_overlay and self.overlay_text:
            overlay_height = 100
            
            bottom_rect = QRect(0, self.height() - overlay_height, self.width(), overlay_height)
            
            canvas_painter.fillRect(bottom_rect, QColor(0, 0, 0, 150))
            
            font = canvas_painter.font()
            font.setPointSize(48)
            font.setBold(True)
            canvas_painter.setFont(font)
            
            canvas_painter.setPen(QColor(255, 255, 255, 255)) 
            
            canvas_painter.drawText(bottom_rect, Qt.AlignmentFlag.AlignCenter, self.overlay_text)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = event.position().toPoint()
            self.drawing = True
    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing:
            new_point = event.position().toPoint()

            dynamic_base = self.width() * 0.02
            
            distance = (new_point - self.last_point).manhattanLength()
            reference_speed = self.width() * 0.03 
            speed_ratio = distance / reference_speed
            thickness_mult = max(0.5, min(1.5, 1.5 - speed_ratio))
            target = dynamic_base * thickness_mult
            lerp_factor = 0.15 
            self.current_thickness += (target - self.current_thickness) * lerp_factor
    
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            pen = QPen(Qt.GlobalColor.black, int(self.current_thickness), 
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            painter.drawLine(self.last_point, new_point)

            painter.end()
            self.last_point = new_point
            self.update()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
    def resizeEvent(self, event):
        new_image = QImage(self.size(), QImage.Format.Format_RGB32)
        new_image.fill(Qt.GlobalColor.white)
        
        painter = QPainter(new_image)
        
        painter.drawImage(self.rect(), self.image, self.image.rect())
        painter.end()
        
        self.image = new_image
        super().resizeEvent(event)
    def clear(self):
        self.image.fill(Qt.GlobalColor.white)
        self.update()