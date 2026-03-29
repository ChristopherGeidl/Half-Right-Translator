import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from DataBaseManager import DataBaseManager

#Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("Appearance/red_theme.json")

class App(ctk.CTk):
    def __init__(self, width, height):
        super().__init__()

        self.db = DataBaseManager("HRT.db")

        self.title("Half Right Translator")
        self.geometry(f"{width}x{height}")

        # header
        self.header = ctk.CTkFrame(self, width=width)
        self.header.pack()
        self.header.grid_columnconfigure(0, weight=0)
        self.header.grid_columnconfigure(1, weight=1)
        self.header.grid_columnconfigure(2, weight=0)

        self.back_btn = ctk.CTkButton(
                self.header, 
                text="<",
                command=lambda: self.refresh_folder_list(),
                width=40,
                height=10,
                font=("Roboto", 24, "bold")
            )
        self.back_btn.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.label = ctk.CTkLabel(
                self.header, 
                text="Select a Study Group", 
                font=("Roboto", 15, "bold"),
                width=(width*0.85)
            )
        self.label.grid(row=0, column=1)

        spacer = ctk.CTkFrame(self.header, width=40, height=1)
        spacer.grid(row=0, column=2, padx=0, pady=0)

        # Container for the list of files
        self.scroll_frame = ctk.CTkScrollableFrame(
                self, 
                width=(width*9/10), 
                height=(height*7/10), 
                border_width=2
            )
        self.scroll_frame.pack(pady=10)

        #footer
        self.footer = ctk.CTkFrame(self, width=width)
        self.footer.pack()
        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_columnconfigure(1, weight=1)


        self.refresh_folder_list()
    def delete_widgets(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        for widget in self.footer.winfo_children():
            widget.destroy()
    def addFolder(self):
        dialog = ctk.CTkInputDialog(text="Enter folder name:", title="New Folder")
        foldername = dialog.get_input()

        folders = self.db.getFolders()

        if(foldername in folders):
            messagebox.showerror("Name Error", f"{foldername} already exists")
            return

        if(foldername): 
            self.db.addFolder(foldername)
            print(f"Added folder: {foldername}")
            self.refresh_folder_list()
    def refresh_folder_list(self):
        self.back_btn.configure(command=lambda: self.refresh_folder_list())
        self.label.configure(text="Select a Study Group")
        self.delete_widgets()

        folders = self.db.getFolders()

        if not folders:
            no_folder_label = ctk.CTkLabel(self.scroll_frame, text="No folders found")
            no_folder_label.pack(pady=20)
        
        for folder in folders:
            btn = ctk.CTkButton(
                self.scroll_frame, 
                text=folder,
                command=lambda f=folder: self.load_folder(f),
                height=40,
            )
            btn.pack(fill="x", pady=5, padx=10)

        btn = ctk.CTkButton(
            self.scroll_frame,
            text="+",
            command=lambda: self.addFolder(),
            height=40,
            font=("Roboto", 15, "bold"),
        )
        btn.pack(pady=5, padx=5)
    def importTXT(self, foldername, overrideConsent=0):
        file_path = filedialog.askopenfilename(
            title="Select TXT file",
            filetypes=[("Text Files", "*.txt")]
        )

        if not file_path:
            return  # user canceled

        print(f"Importing: {file_path}")

        try:
            #if the user does already know they are adding to existing
            if(not overrideConsent): 
                set_names = self.db.getSetsInFolder(foldername)
                file_name = ""
                
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.lower().startswith("set_name:"):
                            file_name =  line.split(":", 1)[1].strip()
                            break

                if(file_name in set_names):
                    add = messagebox.askyesno(
                        "File Exists",
                        f"{foldername}/{file_name}\nalready exists.\nDo you want to add to the existing file?"
                    )
                    if not add:
                        print("Import canceled by user.")
                        return

            self.db.importTXT(file_path, foldername)
            print("Import successful!")
            self.load_folder(foldername)
        except Exception as e:
            print(f"Error importing file: {e}")
            messagebox.showerror("Import Error", str(e))
    def export_file(self, foldername, setname):
        pass
    def load_folder(self, foldername):
        self.back_btn.configure(command=lambda: self.refresh_folder_list())
        self.label.configure(text=f"{foldername}")  
        self.delete_widgets()
        
        sets = self.db.getSetsInFolder(foldername)

        if not sets:
            no_files_label = ctk.CTkLabel(self.scroll_frame, text="No files found in /Test_Sets/"+foldername+" folder")
            no_files_label.pack(pady=20)
        
        for set in sets:
            btn = ctk.CTkButton(
                self.scroll_frame, 
                text=set,
                command=lambda f=set: self.load_set(foldername,f),
                height=40,
            )
            btn.pack(fill="x", pady=5, padx=10)

        btn = ctk.CTkButton(
            self.scroll_frame,
            text="+",
            command=lambda: self.importTXT(foldername),
            height=40,
            font=("Roboto", 15, "bold"),
        )
        btn.pack(pady=5, padx=5)
    def load_set(self, foldername, setname):
        self.back_btn.configure(command=lambda: self.load_folder(foldername))
        self.label.configure(text=f"{foldername}: {setname}")  
        self.delete_widgets()

        if(self.db.isCardsInSet(foldername, setname)):
            btn = ctk.CTkButton(
                    self.scroll_frame, 
                    text="Cards",
                    command=lambda f=set: self.load_cards(foldername,setname),
                    height=40,
                )
            btn.pack(fill="x", pady=5, padx=10)
        if(self.db.isWritingInSet(foldername, setname)):
            btn = ctk.CTkButton(
                    self.scroll_frame, 
                    text="Writing",
                    command=lambda f=set: self.load_writing(foldername,setname),
                    height=40,
                )
            btn.pack(fill="x", pady=5, padx=10)
        btn = ctk.CTkButton(
                self.scroll_frame, 
                text="Test",
                command=lambda f=set: self.load_test(foldername,setname),
                height=40,
            )
        btn.pack(fill="x", pady=5, padx=10)


        import_button = ctk.CTkButton(
            self.footer,
                text="Import File",
                command=lambda:self.importTXT(foldername, 1),
                height=40,
                font=("Roboto", 15, "bold"),
            )
        import_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        export_button = ctk.CTkButton(
                self.footer,
                text="Export File",
                command=lambda:self.export_file(foldername,setname),
                height=40,
                font=("Roboto", 15, "bold"),
            )
        export_button.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    def load_cards(self, foldername, setname, reversed=0):
        self.back_btn.configure(command=lambda: self.load_set(foldername,setname))
        if(reversed):
            print(f"Loading: {setname} cards reversed")
            self.label.configure(text=f"{setname}: Cards Reversed")  
        else:
            print(f"Loading: {setname} cards")
            self.label.configure(text=f"{setname}: Cards")
        self.delete_widgets()

        cardIDs = self.db.getCardIDsInSet(foldername, setname)

        if(len(cardIDs)==0):
            label = ctk.CTkLabel(self.scroll_frame, text=f"No Cards in {foldername}/{setname}")
            label.pack(anchor="w", padx=10, pady=2)

        
        label = ctk.CTkLabel(self.scroll_frame, text=f"{self.db.getCardByID(cardIDs[0])}")
        label.pack(anchor="w", padx=10, pady=2)
    def load_writing(self, foldername, setname):
        self.back_btn.configure(command=lambda: self.load_set(foldername,setname))
        self.label.configure(text=f"{setname}: Writing")  
        print(f"Loading: {setname} writing")
        self.delete_widgets()

        writingIDs = self.db.getWritingIDsInSet(foldername, setname)

        if(len(writingIDs)==0):
            label = ctk.CTkLabel(self.scroll_frame, text=f"No Writing in {setname}")
            label.pack(anchor="w", padx=10, pady=2)

        label = ctk.CTkLabel(self.scroll_frame, text=self.db.getWritingByID(writingIDs[0]))
        label.pack(anchor="w", padx=10, pady=2)
    def load_test(self, foldername, setname):
        self.back_btn.configure(command=lambda: self.load_set(foldername,setname))
        print(f"Loading: {setname} test")
        self.delete_widgets()

WIDTH = 800
HEIGHT = 600

if __name__ == "__main__":
    app = App(WIDTH, HEIGHT)
    app.mainloop()