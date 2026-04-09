import sqlite3
from datetime import datetime
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
                    name TEXT,
                    FOREIGN KEY(folder_id) REFERENCES folders(id)
                    UNIQUE(folder_id, name))''')
    
        # Updated Cards Table
        self.c.execute('''CREATE TABLE IF NOT EXISTS cards 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    set_id INTEGER,
                    name TEXT,
                    reversed INTEGER DEFAULT 0,
                    front_data TEXT, 
                    back_data TEXT,
                    type TEXT DEFAULT 'N',
                    grade INT DEFAULT 0,
                    last_studied DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(set_id) REFERENCES test_sets(id),
                    UNIQUE(set_id, name, front_data, back_data))''')

        # Updated Writing Table
        self.c.execute('''CREATE TABLE IF NOT EXISTS writing 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    set_id INTEGER, 
                    name TEXT,
                    prompt TEXT, 
                    write TEXT,
                    type TEXT DEFAULT 'N',
                    grade INT DEFAULT 0,
                    last_studied DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(set_id) REFERENCES test_sets(id),
                    UNIQUE(set_id, name, prompt, write))''')
        self.conn.commit()

        self.updateAllTypes()
    def importTXT(self, txtFilePath, foldername, setname=""):
        self.c.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)", (foldername,))
        self.c.execute("SELECT id FROM folders WHERE name = ?", (foldername,))
        folder_id = self.c.fetchone()[0]
        
        
        with open(txtFilePath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.read().splitlines() if line.strip()]
        
        set_name = setname #default "" otherwise forced to existing
        if(set_name != ""):
            self.c.execute("INSERT OR IGNORE INTO test_sets (name, folder_id) VALUES (?, ?)", (set_name, folder_id))
            self.c.execute("SELECT id FROM test_sets WHERE name = ? AND folder_id = ?", (set_name, folder_id))
            set_id = self.c.fetchone()[0]
        section = None
        card_groupname = ""
        card_column_names = []
        card_column_side = [] # 0 = front , 1 = back
        writing_groupname = ""
        writingOrder = 2 # 0 = prompt | write, 1 = write | prompt, 2 = uninitialized

        for line in lines:
            if(line.lower().startswith("set_name: ") and setname == ""):
                if(set_name != ""):
                    raise Exception(f"Invalid File Format Error: setname already declared: {line}")
                set_name = line[10:].strip()
                self.c.execute("INSERT OR IGNORE INTO test_sets (name, folder_id) VALUES (?, ?)", (set_name, folder_id))
                self.c.execute("SELECT id FROM test_sets WHERE name = ? AND folder_id = ?", (set_name, folder_id))
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
    def updateTableTypes(self, table):
        today = datetime.now().strftime('%Y-%m-%d')
        self.c.execute(f"""
                UPDATE {table}
                SET type = CASE 
                    WHEN grade == 0 AND type = 'N' THEN 'N'
                    WHEN grade <= 0 AND date(last_studied) != ? THEN 'L'
                    WHEN grade > 0 AND date(last_studied) != ? THEN 'D'
                    ELSE 'A'
                END
            """, (today, today))
        self.conn.commit()
    def updateAllTypes(self):
        self.updateTableTypes("cards")
        self.updateTableTypes("writing")
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
    def getTableGroupNames(self, foldername, setname, table):
        self.c.execute(f"""
                SELECT DISTINCT {table}.name 
                FROM {table}
                JOIN test_sets ON {table}.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? AND test_sets.name = ?
            """, (foldername, setname))
        return [row[0] for row in self.c.fetchall() if row[0]]
    def getTableGroupNumStudy(self, foldername, setname, groupname, table):
        self.c.execute(f"""
                SELECT 
                    SUM(CASE WHEN {table}.type = 'N' THEN 1 ELSE 0 END) as New,
                    SUM(CASE WHEN {table}.type = 'L' THEN 1 ELSE 0 END) as Learn,
                    SUM(CASE WHEN {table}.type = 'D' THEN 1 ELSE 0 END) as Due,
                    COUNT({table}.id) as Total
                FROM {table}
                JOIN test_sets ON {table}.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? 
                AND test_sets.name = ? 
                AND {table}.name = ?
            """, (foldername, setname, groupname))
        result = self.c.fetchone()

        return [res if res is not None else 0 for res in result]
    def getTableItemIDsByGroup(self, foldername, setname, groupname, table):
        self.c.execute(f"""
                SELECT {table}.id 
                FROM {table}
                JOIN test_sets ON {table}.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? AND test_sets.name = ? AND {table}.name = ?
                ORDER BY {table}.grade ASC, {table}.last_studied ASC
            """, (foldername, setname, groupname))
        return [row[0] for row in self.c.fetchall()]
    def getTableItemIDsByType(self, foldername, setname, groupname, table, type):
        self.c.execute(f"""
            SELECT {table}.id 
            FROM {table}
            JOIN test_sets ON {table}.set_id = test_sets.id
            JOIN folders ON test_sets.folder_id = folders.id
            WHERE folders.name = ? AND test_sets.name = ? AND {table}.name = ? AND {table}.type = ?
            """, (foldername, setname, groupname, type))
        return [row[0] for row in self.c.fetchall()]
    def getTableItemByID(self, id, table):
        if(table == "cards"):
            self.c.execute(f"SELECT front_data, back_data FROM {table} WHERE id = ?", (id,))
            row = self.c.fetchone()
            return {"front": json.loads(row[0]), "back": json.loads(row[1])}
        elif(table == "writing"):
            self.c.execute(f"SELECT prompt, write FROM {table} WHERE id = ?", (id,))
            row = self.c.fetchone()
            return {"prompt": row[0], "write": row[1]}
    def updateItemByID(self, table, id, grade_change):      
        try:
            self.c.execute(f"""
                    UPDATE {table}
                    SET 
                        type = 'A',
                        grade = MAX(-10, MIN(10, grade + ?)),
                        last_studied = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (grade_change, id))
            self.conn.commit()
        except Exception as e:
            print(f"Error updating {table} item {id}: {e}")
    def getTenItemsInGroup(self, foldername, setname, groupname, table, index):
        content_col = "front_data" if table == "cards" else "prompt"

        self.c.execute(f"""
                SELECT {table}.* FROM {table}
                JOIN test_sets ON {table}.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? 
                AND test_sets.name = ? 
                AND {table}.name = ?
                ORDER BY {table}.{content_col} ASC
                LIMIT 10 OFFSET ?
            """, (foldername, setname, groupname, index))
        rows = self.c.fetchall()
        if(table == "cards"):
            for i in range(len(rows)):
                rows[i] = (rows[i][4], rows[i][5])
        else:
            for i in range(len(rows)):
                rows[i] = (rows[i][3], rows[i][4])
        return rows
    def deleteItem(self, foldername, setname, groupname, table, item):
        x= item[0]
        y= item[1]

        if table == "cards":
            col_x, col_y = "front_data", "back_data"
        else:
            col_x, col_y = "prompt", "write"
        
        self.c.execute(f"""
                DELETE FROM {table}
                WHERE {col_x} = ? 
                AND {col_y} = ? 
                AND name = ?
                AND set_id = (
                    SELECT ts.id FROM test_sets ts
                    JOIN folders f ON ts.folder_id = f.id
                    WHERE f.name = ? AND ts.name = ?
                )
            """, (x, y, groupname, foldername, setname))
        self.conn.commit()
    def editItem(self, foldername, setname, groupname, table, original_item, new_item):
        if table == "cards":
            col_x, col_y = "front_data", "back_data"
        else:
            col_x, col_y = "prompt", "write"
        
        self.c.execute(f"""
                UPDATE {table} 
                SET {col_x} = ?, 
                    {col_y} = ? 
                WHERE {col_x} = ? 
                AND {col_y} = ? 
                AND name = ?
                AND set_id = (
                    SELECT ts.id FROM test_sets ts
                    JOIN folders f ON ts.folder_id = f.id
                    WHERE f.name = ? AND ts.name = ?
                )
            """, (
                new_item[0], new_item[1],
                original_item[0], original_item[1],
                groupname,
                foldername, setname
            ))
        self.conn.commit()
    def isItemInGroup(self, foldername, setname, groupname, table, item):
        val_x, val_y = item[0], item[1]
        if table == "cards":
            col_x, col_y = "front_data", "back_data"
        else:
            col_x, col_y = "prompt", "write"
        
        self.c.execute(f"""
                SELECT 1 FROM {table}
                JOIN test_sets ON {table}.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? 
                AND test_sets.name = ? 
                AND {table}.name = ?
                AND {table}.{col_x} = ? 
                AND {table}.{col_y} = ?
                LIMIT 1
            """, (foldername, setname, groupname, val_x, val_y))
        
        return self.c.fetchone() is not None
    def isCardsReversed(self, foldername, setname, groupname):
        self.c.execute(f"""
                SELECT cards.reversed 
                FROM cards
                JOIN test_sets ON cards.set_id = test_sets.id
                JOIN folders ON test_sets.folder_id = folders.id
                WHERE folders.name = ? AND test_sets.name = ? AND cards.name = ?
                LIMIT 1
            """, (foldername, setname, groupname))
        
        result = self.c.fetchone()
        return result[0] if result else 0
    def reverseCards(self, foldername, setname, groupname):
        query = f"""
                UPDATE cards 
                SET reversed = 1 - reversed 
                WHERE name = ? 
                AND set_id = (
                    SELECT ts.id FROM test_sets ts
                    JOIN folders f ON ts.folder_id = f.id
                    WHERE f.name = ? AND ts.name = ?
                )
            """
        self.c.execute(query, (groupname, foldername, setname))
        self.conn.commit()
    def getTotalNumberOfItemsInSet(self, foldername, setname):
        self.c.execute("""
                SELECT ts.id 
                FROM test_sets ts
                JOIN folders f ON ts.folder_id = f.id
                WHERE ts.name = ? AND f.name = ?
            """, (setname, foldername))
        
        result = self.c.fetchone()
        if not result:
            return 0
        
        set_id = result[0]

        self.c.execute("SELECT COUNT(*) FROM cards WHERE set_id = ?", (set_id,))
        cards_count = self.c.fetchone()[0]

        self.c.execute("SELECT COUNT(*) FROM writing WHERE set_id = ?", (set_id,))
        writing_count = self.c.fetchone()[0]

        return cards_count + writing_count
    def close(self):
        self.conn.close()

