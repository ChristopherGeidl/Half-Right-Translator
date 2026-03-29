from reader import Reader
import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QFrame, QInputDialog,
                             QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from DataBaseManager import DataBaseManager
from PyQt6.QtGui import QPainter, QPen, QImage, QColor
from PyQt6.QtCore import QPoint
import cv2
import numpy as np

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
    def paintEvent(self, event):
        canvas_painter = QPainter(self)
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = event.position().toPoint()
            self.drawing = True
    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing:
            new_point = event.position().toPoint()
            
            # 1. Math: Calculate smooth thickness
            distance = (new_point - self.last_point).manhattanLength()
            target = max(10, min(18, 20 - distance))
            lerp_factor = 0.1 
            self.current_thickness += (target - self.current_thickness) * lerp_factor
    
            # 2. Drawing: Use ONE painter
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Use int() for the thickness to avoid type errors
            pen = QPen(Qt.GlobalColor.black, int(self.current_thickness), 
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            painter.drawLine(self.last_point, new_point)
            
            # 3. Cleanup
            painter.end() # Explicitly end the painter (Good practice)
            self.last_point = new_point
            self.update()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
    def resizeEvent(self, event):
        # Handle window resizing so the drawing doesn't disappear
        if self.width() > self.image.width() or self.height() > self.image.height():
            new_image = QImage(self.size(), QImage.Format.Format_RGB32)
            new_image.fill(Qt.GlobalColor.white)
            painter = QPainter(new_image)
            painter.drawImage(QPoint(0, 0), self.image)
            self.image = new_image
    def downloadIMG(self, filename):
        ptr = self.image.bits()
        ptr.setsize(self.image.sizeInBytes())
        arr = np.frombuffer(ptr, np.uint8).reshape(self.image.height(), self.image.width(), 4)
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        blurred_img = cv2.GaussianBlur(img_bgr, (3, 3), 0)
        cv2.imwrite(filename, blurred_img)
    def clear(self):
        self.image.fill(Qt.GlobalColor.white)
        self.update()

class HRT(QMainWindow):
    def __init__(self, width, height):
        super().__init__()

        self.db = DataBaseManager("HRT.db")
        self.reader = Reader()
        self.setWindowTitle("Half Right Translator")
        self.resize(width, height)

        self.main_container = QWidget()
        self.setCentralWidget(self.main_container)
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.header = QFrame()
        self.header_layout = QHBoxLayout(self.header)
        self.header.setObjectName("header")
        
        self.back_btn = QPushButton("<")
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.clicked.connect(self.refresh_folder_list)
        self.back_btn.setObjectName("back_btn")
        
        self.label = QLabel("Select a Study Group")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")

        self.header_layout.addWidget(self.back_btn)
        self.header_layout.addWidget(self.label, stretch=1) # Stretch=1 makes it take middle space
        
        self.main_layout.addWidget(self.header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.Box)
        self.scroll.setLineWidth(2)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Buttons start at top
        
        self.scroll.setWidget(self.scroll_content)
        self.scroll.setObjectName("scroll")
        self.main_layout.addWidget(self.scroll)

        self.footer = QFrame()
        self.footer_layout = QHBoxLayout(self.footer)
        self.footer.setObjectName("footer")
        
        self.main_layout.addWidget(self.footer)

        self.refresh_folder_list()
    def delete_widgets(self):
        def clear_layout(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()

        clear_layout(self.scroll_layout)
        clear_layout(self.footer_layout)
    def addFolder(self):
        foldername, ok_pressed = QInputDialog.getText(
            self, "New Folder", "Enter folder name:"
        )

        if not ok_pressed:
            return

        foldername = foldername.strip()

        if not foldername:
            QMessageBox.warning(self, "Input Error", "Folder name cannot be empty.")
            return

        folders = self.db.getFolders()
        if foldername in folders:
            QMessageBox.critical(self, "Name Error", f"'{foldername}' already exists.")
            return

        self.db.addFolder(foldername)
        print(f"Added folder: {foldername}")
        self.refresh_folder_list()
    def refresh_folder_list(self):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
            
        self.back_btn.clicked.connect(self.refresh_folder_list)
        self.label.setText("Select a Study Group")
        self.delete_widgets()

        folders = self.db.getFolders()

        if not folders:
            no_folder_label = QLabel("No folders found")
            no_folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_folder_label)

        for folder in folders:
            btn = QPushButton(folder)
            btn.clicked.connect(lambda checked, f=folder: self.load_folder(f))
            self.scroll_layout.addWidget(btn)

        add_btn = QPushButton("+")
        add_btn.clicked.connect(self.addFolder)
        self.scroll_layout.addWidget(add_btn)
    def importTXT(self, foldername, overrideConsent=0):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select TXT file",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return  # user canceled

        print(f"Importing: {file_path}")

        try:
            if not overrideConsent:
                set_names = self.db.getSetsInFolder(foldername)
                file_name = ""

                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.lower().startswith("set_name:"):
                            file_name = line.split(":", 1)[1].strip()
                            break

                if file_name and file_name in set_names:
                    reply = QMessageBox.question(
                        self,
                        "File Exists",
                        f"{foldername}/{file_name}\nalready exists.\nDo you want to add to the existing file?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No # Default focus
                    )

                    if reply == QMessageBox.StandardButton.No:
                        print("Import canceled by user.")
                        return

            self.db.importTXT(file_path, foldername)
            print("Import successful!")

            self.load_folder(foldername)
            
        except Exception as e:
            print(f"Error importing file: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import: {str(e)}")
    def export_file(self, foldername, setname):
        initial_name = f"{foldername} - {setname}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Set",
            initial_name,
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return 

        try:
            self.db.exportTXT(foldername, setname, file_path)

            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Saved '{setname}' to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Export Error", 
                f"Could not export file:\n{str(e)}"
            )
    def load_folder(self, foldername):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(self.refresh_folder_list)
        self.label.setText(foldername)

        self.delete_widgets()

        sets = self.db.getSetsInFolder(foldername)

        if not sets:
            no_files_label = QLabel(f"No files found in {foldername}")
            no_files_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_files_label)

        for setname in sets:
            btn = QPushButton(setname)
            btn.clicked.connect(lambda _, f=foldername, s=setname: self.load_set(f, s))
            self.scroll_layout.addWidget(btn)

        import_btn = QPushButton("Import TXT (+)")
        import_btn.clicked.connect(lambda: self.importTXT(foldername))
        self.footer_layout.addWidget(import_btn)
    def load_set(self, foldername, setname):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_folder(foldername))
        self.label.setText(f"{foldername}: {setname}")
        self.delete_widgets()

        cardGroups = self.db.getCardGroupNames(foldername, setname)
        writingGroups = self.db.getWritingGroupNames(foldername, setname)

        for c_group in cardGroups:
            btn = QPushButton(f"Cards: {c_group}")
            btn.clicked.connect(lambda _, g=c_group: self.load_card(foldername, setname, g, index=0))
            self.scroll_layout.addWidget(btn)

        for w_group in writingGroups:
            btn = QPushButton(f"Writing: {w_group}")
            btn.clicked.connect(lambda _, g=w_group: self.load_writing(foldername, setname, g))
            self.scroll_layout.addWidget(btn)

        test_btn = QPushButton("Mixed Test Mode")
        test_btn.clicked.connect(lambda: self.load_test(foldername, setname))
        self.scroll_layout.addWidget(test_btn)

        import_btn = QPushButton("Import File")
        import_btn.clicked.connect(lambda: self.importTXT(foldername, 1))
        self.footer_layout.addWidget(import_btn)

        export_btn = QPushButton("Export File")
        export_btn.clicked.connect(lambda: self.export_file(foldername, setname))
        self.footer_layout.addWidget(export_btn)
    def load_card(self, foldername, setname, groupname, index=0, flipped=0, reversed=0):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))

        title_text = f"{groupname}: {'Reversed' if reversed else 'Standard'}"
        self.label.setText(title_text)
        print(f"Loading: {groupname} ({'reversed' if reversed else 'normal'})")
        self.delete_widgets()

        cardIDs = self.db.getCardIDsByGroup(foldername, setname, groupname)

        if not cardIDs:
            empty_label = QLabel(f"No Cards in {foldername}/{setname}")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
            return

        if(index >= len(cardIDs)):
            display_label = QLabel("No More Cards")
            display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(display_label)

            fin_btn = QPushButton("Finish")
            fin_btn.clicked.connect(lambda: self.load_set(foldername, setname))
            self.footer_layout.addWidget(fin_btn)
        else:
            card = self.db.getCardByID(cardIDs[index])
            
            card_container = QFrame()
            card_container.setMinimumHeight(400)
            card_container.setObjectName("flashcard")
            
            card_inner_layout = QVBoxLayout(card_container)
            
            front_side = card['back'] if (reversed ^ flipped) else card['front']
            
            content_text = "\n".join([str(v) for v in front_side.values()])
            
            display_label = QLabel(content_text)
            display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            display_label.setWordWrap(True)
            
            card_inner_layout.addWidget(display_label)
            self.scroll_layout.addWidget(card_container)

            flip_btn = QPushButton("Flip Card")
            flip_btn.clicked.connect(lambda _, i=index, f=(not flipped): self.load_card(foldername, setname, groupname, i, f, reversed))
            self.footer_layout.addWidget(flip_btn)

            next_btn = QPushButton("Next →")
            next_btn.clicked.connect(lambda _, i=(index+1), f=flipped: self.load_card(foldername, setname, groupname, i, f, reversed))
            self.footer_layout.addWidget(next_btn)
    def load_writing(self, foldername, setname, groupname, index=0):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))
        self.label.setText(f"{groupname}: Writing Mode")
        print(f"Loading: {setname} writing group: {groupname}")
        self.delete_widgets()

        writingIDs = self.db.getWritingIDsByGroup(foldername, setname, groupname)

        if not writingIDs:
            empty_label = QLabel(f"No Writing exercises in {groupname}")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
            return

        writing_data = self.db.getWritingByID(writingIDs[index])

        writing_container = QFrame()
        writing_container.setFrameShape(QFrame.Shape.StyledPanel)
        
        writing_layout = QVBoxLayout(writing_container)

        prompt_label = QLabel(f"{writing_data['prompt']}")
        prompt_label.setWordWrap(True)
        prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        writing_layout.addWidget(prompt_label)

        self.canvas = DrawingCanvas()
        writing_layout.addWidget(self.canvas)
        
        self.scroll_layout.addWidget(writing_container)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.canvas.clear())
        self.footer_layout.addWidget(clear_btn)

        check_btn = QPushButton("Check Answer")
        check_btn.clicked.connect(lambda: self.writing_result(foldername, setname, groupname, index, writing_data))
        self.footer_layout.addWidget(check_btn)

        next_btn = QPushButton("Next →")
        next_btn.clicked.connect(lambda _, i=(index+1): self.load_writing(foldername, setname, groupname, i))
        self.footer_layout.addWidget(next_btn)
    def writing_result(self, foldername, setname, groupname, index, writing):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))
        self.label.setText(f"{groupname}: Writing Mode")
        print(f"Checking: {setname} writing group: {groupname}")
        self.delete_widgets()

        writing_container = QFrame()
        writing_container.setFrameShape(QFrame.Shape.StyledPanel)
        
        writing_layout = QVBoxLayout(writing_container)

        self.canvas.downloadIMG("writing.png")
        is_correct, full_detected_text, avg_confidence = self.reader.verify_text("writing.png", writing['write'])


        if(is_correct):
            correct_label = QLabel("Correct")
        else:
            correct_label = QLabel("Incorrect")
        correct_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        writing_layout.addWidget(correct_label)

        prompt_label = QLabel(f"Prompt: {writing['prompt']}\nYour Answer: {full_detected_text}\nCorrect Answer: {writing['write']}\n")
        prompt_label.setWordWrap(True)
        prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        writing_layout.addWidget(prompt_label)
        
        self.scroll_layout.addWidget(writing_container)

        retry_btn = QPushButton("Try Again")
        retry_btn.clicked.connect(lambda: self.load_writing(foldername, setname, groupname, index))
        self.footer_layout.addWidget(retry_btn)

        next_btn = QPushButton("Next →")
        next_btn.clicked.connect(lambda _, i=(index+1): self.load_writing(foldername, setname, groupname, i))
        self.footer_layout.addWidget(next_btn)
    def load_test(self, foldername, setname):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))
        self.label.setText(f"Test: {setname}")
        self.delete_widgets()

WIDTH = 800
HEIGHT = 600

theme = {
    "--black": "#1a1a1a",
    "--mid-black": "#393939",
    "--less-black": "#474747",
    "--gray": "#737373",
    "--white": "#f3f3f3"
}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open("style.qss", "r") as f:
            style = f.read()
            for var, value in theme.items():
                style = style.replace(f"var({var})", value)
            app.setStyleSheet(style)
    except FileNotFoundError:
        print("Style file not found, loading default styles.")

    window = HRT(WIDTH, HEIGHT)
    window.show()

    sys.exit(app.exec())