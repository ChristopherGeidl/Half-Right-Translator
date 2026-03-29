import sys
import os

PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.append(PATH)

from reader import Reader


tests = [
    [f"{PATH}/Code_Tests/reader/test1.png",True,"学习"],
    [f"{PATH}/Code_Tests/reader/test2.png",False,"学习"],
    [f"{PATH}/Code_Tests/reader/test3.png",True,"谢谢"],
    [f"{PATH}/Code_Tests/reader/test4.png",False,""],
    [f"{PATH}/Code_Tests/reader/test5.png",True,""]
]

r1 = Reader()
for img, expected_res, expected_read in tests:
    res, read, conf = r1.verify_text(img,expected_read)
    if res == expected_res:
        print(f"Pass: expected=[{expected_res},{expected_read}] | got=[{res},{read}]")
    else:
        print(f"Fail: expected=[{expected_res},{expected_read}] | got=[{res},{read}]")