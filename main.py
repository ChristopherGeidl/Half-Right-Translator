import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QFrame, QInputDialog,
                             QMessageBox, QFileDialog, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence
from DataBaseManager import DataBaseManager
from DrawingCanvas import DrawingCanvas


class HRT(QMainWindow):
    def __init__(self, width, height):
        super().__init__()

        self.db = DataBaseManager("HRT.db")
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
        self.header_layout.addWidget(self.label)
        
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
                    child_layout = item.layout()

                    if widget is not None:
                        widget.deleteLater()

                    elif child_layout is not None:
                        clear_layout(child_layout)
                        child_layout.deleteLater()

        for attr in ["flip_shortcut", "check_shortcut", "clear_shortcut", "finish_shortcut", "bad_shortcut", "alright_shortcut", "good_shortcut", "great_shortcut"]:
            if hasattr(self, attr):
                shortcut = getattr(self, attr)
                shortcut.setEnabled(False)
                shortcut.deleteLater()
                delattr(self, attr)

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

        cardGroups = self.db.getTableGroupNames(foldername, setname, "cards")
        writingGroups = self.db.getTableGroupNames(foldername, setname, "writing")

        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(6)

        headers = ["Type", "Name", "New", "Learn", "Due", "All", ""]

        for col, text in enumerate(headers):
            label = QLabel(text)
            label.setObjectName("group_label")
            layout.addWidget(label, 0, col, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.setColumnStretch(1, 2) # Name wider

        row = 1

        for c_group in cardGroups:
            New, Learn, Due, All = self.db.getTableGroupNumStudy(foldername, setname, c_group, "cards")
            
            type_label = QLabel("Cards")
            type_label.setObjectName("group_label_type")
            layout.addWidget(type_label, row, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            
            name_label = QLabel(c_group)
            name_label.setObjectName("group_label_name")
            layout.addWidget(name_label, row, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            
            btn = QPushButton(f"{New}")
            btn.clicked.connect(lambda _, g=c_group: self.load_card(foldername, setname, g, type='N'))
            btn.setObjectName("group_load_new")
            layout.addWidget(btn, row, 2, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(f"{Learn}")
            btn.clicked.connect(lambda _, g=c_group: self.load_card(foldername, setname, g, type='L'))
            btn.setObjectName("group_load_learn")
            layout.addWidget(btn, row, 3, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(f"{Due}")
            btn.clicked.connect(lambda _, g=c_group: self.load_card(foldername, setname, g, type='D'))
            btn.setObjectName("group_load_due")
            layout.addWidget(btn, row, 4, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(f"{All}")
            btn.clicked.connect(lambda _, g=c_group: self.load_card(foldername, setname, g, type='A'))
            btn.setObjectName("group_load_all")
            layout.addWidget(btn, row, 5, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton("Settings")
            btn.clicked.connect(lambda _, g=c_group: self.edit_items(foldername, setname, g, table="cards"))
            btn.setObjectName("group_settings")
            layout.addWidget(btn, row, 6, alignment=Qt.AlignmentFlag.AlignCenter)

            row += 1

        for w_group in writingGroups:
            New, Learn, Due, All = self.db.getTableGroupNumStudy(foldername, setname, w_group, "writing")

            type_label = QLabel("Writing")
            type_label.setObjectName("group_label_type")
            layout.addWidget(type_label, row, 0, alignment=Qt.AlignmentFlag.AlignCenter)

            name_label = QLabel(w_group)
            name_label.setObjectName("group_label_name")
            layout.addWidget(name_label, row, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            
            btn = QPushButton(f"{New}")
            btn.clicked.connect(lambda _, g=w_group: self.load_writing(foldername, setname, g, type='N'))
            btn.setObjectName("group_load_new")
            layout.addWidget(btn, row, 2, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(f"{Learn}")
            btn.clicked.connect(lambda _, g=w_group: self.load_writing(foldername, setname, g, type='L'))
            btn.setObjectName("group_load_learn")
            layout.addWidget(btn, row, 3, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(f"{Due}")
            btn.clicked.connect(lambda _, g=w_group: self.load_writing(foldername, setname, g, type='D'))
            btn.setObjectName("group_load_due")
            layout.addWidget(btn, row, 4, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton(f"{All}")
            btn.clicked.connect(lambda _, g=w_group: self.load_writing(foldername, setname, g, type='A'))
            btn.setObjectName("group_load_all")
            layout.addWidget(btn, row, 5, alignment=Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton("Settings")
            btn.clicked.connect(lambda _, g=w_group: self.edit_items(foldername, setname, g, table="writing"))
            btn.setObjectName("group_settings")
            layout.addWidget(btn, row, 6, alignment=Qt.AlignmentFlag.AlignCenter)

            row += 1
        
        self.scroll_layout.addLayout(layout)

        test_btn = QPushButton("Test All")
        test_btn.clicked.connect(lambda: self.load_test(foldername, setname))
        self.scroll_layout.addWidget(test_btn)

        import_btn = QPushButton("Import File")
        import_btn.clicked.connect(lambda: self.importTXT(foldername, 1))
        self.footer_layout.addWidget(import_btn)

        export_btn = QPushButton("Export File")
        export_btn.clicked.connect(lambda: self.export_file(foldername, setname))
        self.footer_layout.addWidget(export_btn)
    def next_card(self, foldername, setname, groupname, card_id, grade_change, type='A', index=0, flipped=0, reversed=0, finish_function=None):
        self.db.updateItemByID("cards", card_id, grade_change)
        self.load_card(foldername, setname, groupname, type, index, flipped, reversed, finish_function)
    def load_card(self, foldername, setname, groupname, type='A', index=0, flipped=0, reversed=0, finish_function=None):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))

        title_text = f"{groupname}: {'Reversed' if reversed else 'Standard'}"
        self.label.setText(title_text)
        print(f"Loading: {groupname} ({'reversed' if reversed else 'normal'})")
        self.delete_widgets()

        if(type == 'A'):
            cardIDs = self.db.getTableItemIDsByGroup(foldername, setname, groupname, "cards")
        else:
            index = 0
            cardIDs = self.db.getTableItemIDsByType(foldername, setname, groupname, "cards", type)

        
        if(not cardIDs or index >= len(cardIDs)):
            if(finish_function == None):
                finish_function = lambda f, s: self.load_set(f, s)
            display_label = QLabel(f"No More Cards in {groupname}")
            display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(display_label)

            self.finish_shortcut = QShortcut(QKeySequence("Space"), self)
            self.finish_shortcut.activated.connect(lambda: finish_function(foldername, setname))

            fin_btn = QPushButton("Finish")
            fin_btn.clicked.connect(lambda: finish_function(foldername, setname))
            self.footer_layout.addWidget(fin_btn)
        else:
            card = self.db.getTableItemByID(cardIDs[index], "cards")
            
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
            self.scroll_layout.addWidget(card_container, stretch=1)

            if(flipped):
                # 1 for Bad -2
                self.bad_shortcut = QShortcut(QKeySequence("1"), self)
                self.bad_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], -2, type, i, 0, reversed, finish_function))
                # 2 for Alright -1
                self.alright_shortcut = QShortcut(QKeySequence("2"), self)
                self.alright_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], -1, type, i, 0, reversed, finish_function))
                # 3 for Good +1
                self.good_shortcut = QShortcut(QKeySequence("3"), self)
                self.good_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], 1, type, i, 0, reversed, finish_function))
                # 4 for Great +2
                self.great_shortcut = QShortcut(QKeySequence("4"), self)
                self.great_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], 2, type, i, 0, reversed, finish_function))
                
                btn = QPushButton("Bad -2")
                btn.clicked.connect(lambda _, i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], -2, type, i, 0, reversed, finish_function))
                self.footer_layout.addWidget(btn)
                btn = QPushButton("Alright -1")
                btn.clicked.connect(lambda _, i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], -1, type, i, 0, reversed, finish_function))
                self.footer_layout.addWidget(btn)
                btn = QPushButton("Good +1")
                btn.clicked.connect(lambda _, i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], 1, type, i, 0, reversed, finish_function))
                self.footer_layout.addWidget(btn)
                btn = QPushButton("Great +2")
                btn.clicked.connect(lambda _, i=(index+1): 
                    self.next_card(foldername, setname, groupname, cardIDs[index], 2, type, i, 0, reversed, finish_function))
                self.footer_layout.addWidget(btn)
            else:
                # Space to flip
                self.flip_shortcut = QShortcut(QKeySequence("Space"), self)
                self.flip_shortcut.activated.connect(lambda i=index: 
                    self.load_card(foldername, setname, groupname, type, i, 1, reversed, finish_function))
                btn = QPushButton("Flip")
                btn.clicked.connect(lambda _, i=index: 
                    self.load_card(foldername, setname, groupname, type, i, 1, reversed, finish_function))
                self.footer_layout.addWidget(btn)
    def next_writing(self, foldername, setname, groupname, writing_id, grade_change, type='A', index=0, checked=0, finish_function=None):
        self.db.updateItemByID("writing", writing_id, grade_change)
        self.load_writing(foldername, setname, groupname, type, index, checked, finish_function)      
    def load_writing(self, foldername, setname, groupname, type='A', index=0, checked=0, finish_function=None):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))
        self.label.setText(f"{groupname}: Writing Mode")
        print(f"Loading: {setname} writing group: {groupname}")
        self.delete_widgets()

        if(type == 'A'):
            writingIDs = self.db.getTableItemIDsByGroup(foldername, setname, groupname, "writing")
        else:
            index = 0
            writingIDs = self.db.getTableItemIDsByType(foldername, setname, groupname, "writing", type)
        
        
        if(not writingIDs or index >= len(writingIDs)):
            if(finish_function == None):
                finish_function = lambda f, s: self.load_set(f, s)
            
            display_label = QLabel(f"No Writing exercises in {groupname}")
            display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(display_label)

            # Space to Finish
            self.finish_shortcut = QShortcut(QKeySequence("Space"), self)
            self.finish_shortcut.activated.connect(lambda: finish_function(foldername, setname))

            fin_btn = QPushButton("Finish")
            fin_btn.clicked.connect(lambda: finish_function(foldername, setname))
            self.footer_layout.addWidget(fin_btn)
        else:
            writing_data = self.db.getTableItemByID(writingIDs[index], "writing")

            writing_container = QFrame()
            writing_container.setFrameShape(QFrame.Shape.StyledPanel)
            
            writing_layout = QVBoxLayout(writing_container)

            prompt_label = QLabel(f"{writing_data['prompt']}")
            prompt_label.setWordWrap(True)
            prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            writing_layout.addWidget(prompt_label)

            if(not checked):
                self.canvas = DrawingCanvas()
            else:
                self.canvas.set_overlay(writing_data["write"], True)
            writing_layout.addWidget(self.canvas, stretch=1)

            self.scroll_layout.addWidget(writing_container)


            if(checked):
                # 1 for Bad -2
                self.bad_shortcut = QShortcut(QKeySequence("1"), self)
                self.bad_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], -2, type, i, 0, finish_function))
                # 2 for Alright -1
                self.alright_shortcut = QShortcut(QKeySequence("2"), self)
                self.alright_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], -1, type, i, 0, finish_function))
                # 3 for Good +1
                self.good_shortcut = QShortcut(QKeySequence("3"), self)
                self.good_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], 1, type, i, 0, finish_function))
                # 4 for Great +2
                self.great_shortcut = QShortcut(QKeySequence("4"), self)
                self.great_shortcut.activated.connect(lambda i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], 2, type, i, 0, finish_function))
                
                btn = QPushButton("Bad -2")
                btn.clicked.connect(lambda _ ,i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], -2, type, i, 0, finish_function))
                self.footer_layout.addWidget(btn)
                btn = QPushButton("Alright -1")
                btn.clicked.connect(lambda _ ,i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], -1, type, i, 0, finish_function))
                self.footer_layout.addWidget(btn)
                btn = QPushButton("Good +1")
                btn.clicked.connect(lambda _ ,i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], 1, type, i, 0, finish_function))
                self.footer_layout.addWidget(btn)
                btn = QPushButton("Great +2")
                btn.clicked.connect(lambda _ ,i=(index+1): 
                    self.next_writing(foldername, setname, groupname, writingIDs[index], 2, type, i, 0, finish_function))
                self.footer_layout.addWidget(btn)
            else:
                # C to Clear Answer
                self.clear_shortcut = QShortcut(QKeySequence("C"), self)
                self.clear_shortcut.activated.connect(lambda: self.canvas.clear())
                # Space to Check Answer
                self.check_shortcut = QShortcut(QKeySequence("Space"), self)
                self.check_shortcut.activated.connect(lambda i=index: 
                    self.load_writing(foldername, setname, groupname, type, i, 1, finish_function))
                
                clear_btn = QPushButton("Clear")
                clear_btn.clicked.connect(lambda: self.canvas.clear())
                self.footer_layout.addWidget(clear_btn)

                check_btn = QPushButton("Check Answer")
                check_btn.clicked.connect(lambda _, i=index: 
                    self.load_writing(foldername, setname, groupname, type, i, 1, finish_function))
                self.footer_layout.addWidget(check_btn)     
    def load_test(self, foldername, setname, group_index=0):
        try:
            self.back_btn.clicked.disconnect()
        except TypeError:
            pass
        self.back_btn.clicked.connect(lambda: self.load_set(foldername, setname))
        self.label.setText(f"Test: {setname}")
        self.delete_widgets()

        cardGroups = self.db.getTableGroupNames(foldername, setname, "cards")
        writingGroups = self.db.getTableGroupNames(foldername, setname, "writing")

        numCardGroups = len(cardGroups)
        numWritingGroups = len(writingGroups)

        if(group_index < numCardGroups):
            self.load_card(foldername, setname, cardGroups[group_index], finish_function=lambda f, s: 
                self.load_test(f, s, group_index+1))
        elif(group_index < (numCardGroups + numWritingGroups)):
            i = group_index - numCardGroups
            self.load_writing(foldername, setname, writingGroups[i], finish_function=lambda f, s: 
                self.load_test(f, s, group_index+1))
        else:
            display_label = QLabel(f"Finished Test")
            display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(display_label)

            self.check_shortcut = QShortcut(QKeySequence("Space"), self)
            self.check_shortcut.activated.connect(lambda: self.load_set(foldername, setname))

            fin_btn = QPushButton("Finish")
            fin_btn.clicked.connect(lambda: self.load_set(foldername, setname))
            self.footer_layout.addWidget(fin_btn)


WIDTH = 800
HEIGHT = 600

theme = {
    "--black": "#1a1a1a",
    "--mid-black": "#393939",
    "--less-black": "#474747",
    "--gray": "#737373",
    "--white": "#f3f3f3",
    "--light-blue": "#3292ff",
    "--lighter-blue": "#a1c9f7",
    "--light-green": "#37ff69",
    "--lighter-green": "#b2fab4",
    "--light-red": "#ff2b6b",
    "--lighter-red": "#ffabab"
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