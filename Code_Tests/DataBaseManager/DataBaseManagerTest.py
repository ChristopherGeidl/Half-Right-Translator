import sys
import os

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.append(PATH)

from DataBaseManager import DataBaseManager

testTXTPath = f"{PATH}/Code_Tests/DataBaseManager/test.txt"
dbPath = f"{PATH}/Code_Tests/DataBaseManager/test.db"
db = DataBaseManager(dbPath)

PRINT_PASS = 0

def test(text, folderName, testName, testNumber, expectedError=0):
    try:
        with open(testTXTPath, "w", encoding="utf-8") as f:
            f.write(text)
        db.importTXT(testTXTPath, folderName)
        if(expectedError == 0):
            if(PRINT_PASS):
                print(f"PASSED: {folderName} + {testName}  + {testNumber} had no errors")
        else:
            print(f"FAILED: {folderName} + {testName}  + {testNumber} had no errors")
    except Exception as e:
        if(expectedError == 1):
            if(PRINT_PASS):
                print(f"PASSED: {folderName} + {testName}  + {testNumber} had error: {e}")
        else:
            print(f"FAILED: {folderName} + {testName}  + {testNumber} had errors {e}")
def testSet(folderName, testName):
    #nameless cards and writing
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]pinyin | [back]definition]
        学习 | xué xí | to study
        |  | 
        [[back]pinyin | [front]hanzi | [back]definition | [front]extra front | [back] extra back]
        xiè xie | 谢谢 | thank you | extra front | extra back
        |  | | |

        [writing]
        [prompt | write]
        xué xí - to study | 学习
        xué xí - to study | 学习
        xué xí - to study | 学习
        | 

        [writing]
        [write | prompt]
        谢谢 | xiè xie - thank you
        """
    test(text, folderName, testName, 0, 0)
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]pinyin | [back]definition]

        [writing]
        [prompt | write]

        [writing]
        [write | prompt]
        """
    test(text, folderName, testName, 1, 0)
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]definition | [back]pinyin]
        addedLater1 | addedLater2 | addedLater3
        """
    test(text, folderName, testName, 2, 0)
    text = f"""
        set_name: {testName}
        """
    test(text, folderName, testName, 3, 0)
    text = f"""
        """
    test(text, folderName, testName, 4, 1)
    text = f"""
        set_name: {testName}

        [auz]
        [cards]
        [[front]hanzi | [back]definition | [back]pinyin]
        a1 | a2 | a3
        """
    test(text, folderName, testName, 5, 1)
    text = f"""
        set_name: {testName}
        set_name: {testName}
        """
    test(text, folderName, testName, 6, 1)
    text = f"""
        set_name: {testName}

        [[front]hanzi | [back]definition | [back]pinyin]
        b1 | b2 | b3    
    """
    test(text, folderName, testName, 7, 1)
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]definition | [back]pinyin
        c1 | c2 | c3
        """
    test(text, folderName, testName, 8, 1)
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]definition | pinyin]
        d1 | d2 | d3
        """
    test(text, folderName, testName, 9, 1)
    text = f"""
        set_name: {testName}

        [cards]
        [hanzi | [back]definition | [back]pinyin]
        e1 | e2 | e3
        """
    test(text, folderName, testName, 10, 1)
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]definition | [back]pinyin]
        f1 | f2
        """
    test(text, folderName, testName, 11, 1)
    text = f"""
        set_name: {testName}

        [cards]
        [[front]hanzi | [back]definition | [back]pinyin]
        g1 | g2 | g3 | g4
        """
    test(text, folderName, testName, 12, 1)
    text = f"""
        set_name: {testName}

        [prompt | write]
        b1 | b2
    """
    test(text, folderName, testName, 13, 1)
    text = f"""
        set_name: {testName}

        [writing]
        [prompt | write
        b1 | b2  
        """
    test(text, folderName, testName, 14, 1)
    text = f"""
        set_name: {testName}

        [writing]
        [prompt | ]
        b1 | b2  
        """
    test(text, folderName, testName, 15, 1)
    text = f"""
        set_name: {testName}

        [writing]
        [prompt | write | ]
        b1 | b2  
        """
    test(text, folderName, testName, 16, 1)
    text = f"""
        set_name: {testName}

        [writing]
        [prompt | write]
        b1 | b2 |  
        """
    test(text, folderName, testName, 17, 1)
    text = f"""
        set_name: {testName}

        [writing]
        [prompt | write]
        b1 | b2 | b3
        """
    test(text, folderName, testName, 18, 1)

    #named cards and writing
    text = f"""
        set_name: {testName}

        [cards]
        [[back]pinyin | [front]hanzi | [back]definition | [front]extra front | [back] extra back]
        xiè xie | 谢谢 | thank you | extra front | extra back
        |  | | |
        cards: name1
        [[front]hanzi | [back]pinyin | [back]definition]
        学习 | xué xí | to study
        |  | 
        [cards]
        [[back]pinyin | [front]hanzi | [back]definition | [front]extra front | [back] extra back]
        xiè xie | 谢谢 | thank you | extra front | extra back
        |  | | |
        cards: name1
        [[front]hanzi | [back]pinyin | [back]definition]
        学习 | xué xí | to study
        |  | 
        
        [writing]
        [prompt | write]
        xué xí - to study | 学习
        xué xí - to study | 学习

        writing: name1
        [write | prompt]
        xué xí - to study | 学习
        | 

        cards: name2
        [[back]pinyin | [front]hanzi | [back]definition | [front]extra front | [back] extra back]
        xiè xie | 谢谢 | thank you | extra front | extra back
        |  | | |

        [writing]
        [write | prompt]
        谢谢 | xiè xie - thank you
        """
    test(text, folderName, testName, 19, 0)
    text = f"""
        set_name: {testName}

        cards: name1
        [[front]hanzi | [back]pinyin | [back]definition]

        writing: name1
        [prompt | write]

        [writing]
        [write | prompt]
        """
    test(text, folderName, testName, 20, 0)
    text = f"""
        set_name: {testName}

        cards: name1
        [[front]hanzi | [back]definition | [back]pinyin]
        addedLater1 | addedLater2 | addedLater3
        """
    test(text, folderName, testName, 21, 0)
    text = f"""
        set_name: {testName}

        auz: name1
        cards: name1
        [[front]hanzi | [back]definition | [back]pinyin]
        a1 | a2 | a3
        """
    test(text, folderName, testName, 22, 0) #gets ignored
    text = f"""
        set_name: {testName}

        cards: name1
        [[front]hanzi | [back]definition | [back]pinyin
        c1 | c2 | c3
        """
    test(text, folderName, testName, 23, 1)
    text = f"""
        set_name: {testName}

        cards: name1
        [[front]hanzi | [back]definition | pinyin]
        d1 | d2 | d3
        """
    test(text, folderName, testName, 24, 1)
    text = f"""
        set_name: {testName}

        cards: name1
        [hanzi | [back]definition | [back]pinyin]
        e1 | e2 | e3
        """
    test(text, folderName, testName, 25, 1)
    text = f"""
        set_name: {testName}

        cards: name1
        [[front]hanzi | [back]definition | [back]pinyin]
        f1 | f2
        """
    test(text, folderName, testName, 26, 1)
    text = f"""
        set_name: {testName}

        cards: name1
        [[front]hanzi | [back]definition | [back]pinyin]
        g1 | g2 | g3 | g4
        """
    test(text, folderName, testName, 27, 1)
    text = f"""
        set_name: {testName}

        writing: name1
        [prompt | write
        b1 | b2  
        """
    test(text, folderName, testName, 27, 1)
    text = f"""
        set_name: {testName}

        writing: name1
        [prompt | ]
        b1 | b2  
        """
    test(text, folderName, testName, 28, 1)
    text = f"""
        set_name: {testName}

        writing: name1
        [prompt | write | ]
        b1 | b2  
        """
    test(text, folderName, testName, 29, 1)
    text = f"""
        set_name: {testName}

        writing: name1
        [prompt | write]
        b1 | b2 |  
        """
    test(text, folderName, testName, 30, 1)
    text = f"""
        set_name: {testName}

        writing: name1
        [prompt | write]
        b1 | b2 | b3
        """
    test(text, folderName, testName, 31, 1)

testSet("Folder1", "test1")
testSet("Folder1", "test2")
testSet("Folder1", "test3")

testSet("Folder2", "test1")
testSet("Folder2", "test2")
testSet("Folder2", "test3")

testSet("Folder3", "test1")
testSet("Folder3", "test2")
testSet("Folder3", "test3")