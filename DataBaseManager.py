import sqlite3
import random
import json

class DataBaseManager:
    def __init__(self, dbPath):
        self.dbPath = dbPath

        self.conn = sqlite3.connect(dbPath)
        self.c = self.conn.cursor()
        
        self.c.execute('''CREATE TABLE IF NOT EXISTS folders 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT UNIQUE)''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS test_sets 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    folder_id INTEGER,
                    name TEXT UNIQUE, 
                    FOREIGN KEY(folder_id) REFERENCES folders(id))''')
    
        # Updated Cards Table
        self.c.execute('''CREATE TABLE IF NOT EXISTS cards 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    set_id INTEGER, 
                    name TEXT,
                    front_data TEXT, 
                    back_data TEXT,
                    FOREIGN KEY(set_id) REFERENCES test_sets(id),
                    UNIQUE(set_id, name, front_data, back_data))''')

        # Updated Writing Table
        self.c.execute('''CREATE TABLE IF NOT EXISTS writing 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    set_id INTEGER, 
                    name TEXT,
                    prompt TEXT, 
                    write TEXT,
                    FOREIGN KEY(set_id) REFERENCES test_sets(id),
                    UNIQUE(set_id, name, prompt, write))''')
        self.conn.commit()
    def importTXT(self, txtFilePath, foldername):
        self.c.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)", (foldername,))
        self.c.execute("SELECT id FROM folders WHERE name = ?", (foldername,))
        folder_id = self.c.fetchone()[0]
        
        
        with open(txtFilePath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.read().splitlines() if line.strip()]
        
        set_name= ""
        section = None
        card_groupname = ""
        card_column_names = []
        card_column_side = [] # 0 = front , 1 = back
        writing_groupname = ""
        writingOrder = 2 # 0 = prompt | write, 1 = write | prompt, 2 = uninitialized

        for line in lines:
            if(line.lower().startswith("set_name: ")):
                if(set_name != ""):
                    raise Exception(f"Invalid File Format Error: setname already declared: {line}")
                set_name = line[10:].strip()
                self.c.execute("INSERT OR IGNORE INTO test_sets (name, folder_id) VALUES (?, ?)", (set_name, folder_id))
                self.c.execute("SELECT id FROM test_sets WHERE name = ?", (set_name,))
                set_id = self.c.fetchone()[0]

            elif(line.lower() == "[cards]"):
                section = "cards"
            elif(line.lower() == "[writing]"):
                section = "writing"

            elif(line.startswith("cards:")):
                section = "cards"
                card_groupname = line[6:].strip()
            elif(line.startswith("writing:")):
                section = "writing"
                writing_groupname = line[8:].strip()
            
            elif(line.startswith("[") and line.endswith("]")):
                cols = [c.strip() for c in line[1:-1].split("|")]
                if(section == "cards"):
                    card_column_names = []
                    card_column_side = []
                    for c in cols:
                        if(c.startswith("[front]")):
                            card_column_names.append(c[7:].strip())
                            card_column_side.append(0)
                        elif(c.startswith("[back]")):
                            card_column_names.append(c[6:].strip())
                            card_column_side.append(1)
                        else:
                            raise Exception(f"Invalid File Format Error: column not labeled front or back. \"{c}\" in \"{line}\"")
                elif(section == "writing"):
                    if("prompt" not in cols or "write" not in cols):
                        raise Exception(f"Invalid File Format Error: writing section must have \"prompt\" and \"write\" columns. {line}")
                    if(len(cols) > 2):
                        raise Exception(f"Invalid File Format Error: too many writing columns. Only \"prompt\" and \"write\" are valid columns. {line}")
                    writingOrder = 0 if cols[0] == "prompt" else 1
                else:
                    raise Exception(f"Invalid File Format Error: at start and end of line {line}")
            
            else:
                parts = [p.strip() for p in line.split("|")]

                if(section == "cards"):
                    if(len(card_column_names) == 0):
                        raise Exception(f"Invalid File Format Error: lacking card columns")
                    
                    front = 0
                    back = 0
                    for c in card_column_side:
                        if(c == 0):
                            front = 1
                        else:
                            back = 1
                        if(front and back):
                            break
                    if(not front):
                        raise Exception(f"Invalid File Format Error: lacking front card columns ensure you use [front]")
                    elif(not back):
                        raise Exception(f"Invalid File Format Error: lacking back card columns ensure you use [back]")
                    
                    if(len(parts) != len(card_column_names)):
                        raise Exception(f"Invalid File Format Error: card has different number of columns than declared: {line}")
                    
                    empty = 1
                    for part in parts:
                        if(part != ""):
                            empty = 0
                            break
                    if(empty):
                        continue

                    front_map = {}
                    back_map = {}
                    for i in range(len(card_column_names)):
                        if card_column_side[i] == 0:
                            front_map[card_column_names[i]] = parts[i]
                        else:
                            back_map[card_column_names[i]] = parts[i]

                    self.c.execute("INSERT OR IGNORE INTO cards (set_id, name, front_data, back_data) VALUES (?, ?, ?, ?)",
                        (set_id,
                         card_groupname,
                         json.dumps(front_map, ensure_ascii=False, sort_keys=True), 
                         json.dumps(back_map, ensure_ascii=False, sort_keys=True)))
                elif(section == "writing"):
                    if(writingOrder == 2):
                        raise Exception(f"Invalid File Format Error: lacking writing columns.")
                    if(len(parts) != 2):
                        raise Exception(f"Invalid File Format Error: writing needs 2 columns: {line}")
                    if(parts[0] == "" and parts[1] == ""): # empty
                        continue
                    (prompt,write) = (parts[0],parts[1]) if writingOrder == 0 else (parts[1],parts[0])
                    self.c.execute("INSERT OR IGNORE INTO writing (set_id, name, prompt, write) VALUES (?, ?, ?, ?)",
                          (set_id, writing_groupname, prompt, write))
        
        if(set_name == ""):
            raise Exception("Invalid File Format Error: no set_name")
        if(section == None): #empty file
            return
        
        self.conn.commit()
        print(f"Successfully imported '{set_name}' into {self.dbPath}.")
    def exportTXT(self, foldername, setname, exportPath):
        with open(exportPath, "w", encoding="utf-8") as f:
            f.write(f"set_name: {setname}\n")

            cardGroups = self.getCardGroupNames(foldername, setname)
            for g in cardGroups:
                f.write(f"\ncards: {g}\n")
                
                last_header_str = "" 
                cardIDs = self.getCardIDsByGroup(foldername, setname, g)
                for id in cardIDs:
                    card = self.getCardByID(id)
                    new_cols = []
                    card_data = []

                    for key, val in card["front"].items():
                        new_cols.append(f"[front]{key}")
                        card_data.append(str(val))
                    for key, val in card["back"].items():
                        new_cols.append(f"[back]{key}")
                        card_data.append(str(val))

                    current_header_str = f"[{' | '.join(new_cols)}]"
                    if last_header_str != current_header_str:
                        f.write(f"{current_header_str}\n")
                        last_header_str = current_header_str
                    
                    f.write(f"{' | '.join(card_data)}\n")
            
            writingGroups = self.getWritingGroupNames(foldername, setname)
            for g in writingGroups:
                f.write(f"\nwriting: {g}\n")
                f.write("[prompt | write]\n")
                
                writingIDs = self.getWritingIDsByGroup(foldername, setname, g)
                for id in writingIDs:
                    writing = self.getWritingByID(id)
                    f.write(f"{writing['prompt']} | {writing['write']}\n")                 
    def addFolder(self, foldername):
        self.c.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)", (foldername,))
        self.conn.commit()
    def getFolders(self):
        self.c.execute("SELECT name FROM folders ORDER BY name ASC")
        return [row[0] for row in self.c.fetchall()]
    def getSetsInFolder(self, foldername):
        try:
            self.c.execute("""
                SELECT test_sets.name 
                FROM test_sets 
                JOIN folders ON test_sets.folder_id = folders.id 
                WHERE folders.name = ?
                ORDER BY test_sets.name ASC
                """, (foldername,))
            return [row[0] for row in self.c.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    def isCardsInSet(self, foldername, setname):
        self.c.execute("""
            SELECT COUNT(cards.id) 
            FROM cards
            JOIN test_sets ON cards.set_id = test_sets.id
            JOIN folders ON test_sets.folder_id = folders.id
            WHERE folders.name = ? AND test_sets.name = ?
            """, (foldername, setname))
        count = self.c.fetchone()[0]
        return count > 0
    def isWritingInSet(self, foldername, setname):
        self.c.execute("""
            SELECT COUNT(writing.id) 
            FROM writing
            JOIN test_sets ON writing.set_id = test_sets.id
            JOIN folders ON test_sets.folder_id = folders.id
            WHERE folders.name = ? AND test_sets.name = ?
            """, (foldername, setname))
        count = self.c.fetchone()[0]
        return count > 0
    def getCardGroupNames(self, foldername, setname):
        self.c.execute("""
                SELECT DISTINCT cards.name 
                FROM cards
                JOIN test_sets ON cards.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? AND test_sets.name = ?
            """, (foldername, setname))
        return [row[0] for row in self.c.fetchall() if row[0]]
    def getWritingGroupNames(self, foldername, setname):
        self.c.execute("""
                SELECT DISTINCT writing.name 
                FROM writing
                JOIN test_sets ON writing.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? AND test_sets.name = ?
            """, (foldername, setname))
        return [row[0] for row in self.c.fetchall() if row[0]]
    def getCardIDsByGroup(self, foldername, setname, groupname):
        self.c.execute("""
            SELECT cards.id 
            FROM cards
            JOIN test_sets ON cards.set_id = test_sets.id
            JOIN folders ON test_sets.folder_id = folders.id
            WHERE folders.name = ? AND test_sets.name = ? AND cards.name = ?
            """, (foldername, setname, groupname))
        return [row[0] for row in self.c.fetchall()]
    def getCardByID(self, card_id):
        self.c.execute("SELECT front_data, back_data FROM cards WHERE id = ?", (card_id,))
        row = self.c.fetchone()
        return {"front": json.loads(row[0]), "back": json.loads(row[1])}
    def getWritingIDsByGroup(self, foldername, setname, groupname):
        self.c.execute("""
            SELECT writing.id 
            FROM writing
            JOIN test_sets ON writing.set_id = test_sets.id
            JOIN folders ON test_sets.folder_id = folders.id
            WHERE folders.name = ? AND test_sets.name = ? AND writing.name = ?
            """, (foldername, setname, groupname))
        return [row[0] for row in self.c.fetchall()]
    def getWritingByID(self, writing_id):
        self.c.execute("SELECT prompt, write FROM writing WHERE id = ?", (writing_id,))
        row = self.c.fetchone()
        return {"prompt": row[0], "write": row[1]}
    def close(self):
        self.conn.close()

