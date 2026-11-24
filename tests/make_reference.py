import json
import platform
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

LEVEL_DATA = json.loads((HERE / "levels.json").read_text(encoding="utf-8"))
LEVELS, ANSWERS = LEVEL_DATA["levels"], LEVEL_DATA["answers"]
BLANK = {"start": {"x": 0, "y": 5, "dir": 1}, "goal": {"x": 5, "y": 0}, "obs": []}

LANGUAGE = [
    ("ก. ข้อมูลพื้นฐาน", "หารปัดเศษ เศษเหลือ ยกกำลัง", """
print(7 // 2, 7 % 2, -7 // 2, -7 % 2, 2 ** 10, 7 / 2)
"""),
    ("ก. ข้อมูลพื้นฐาน", "การแสดงผลทศนิยม", """
print(0.1 + 0.2, 1 / 3, 1e16, 2.5e-5, 10 / 2)
"""),
    ("ก. ข้อมูลพื้นฐาน", "จำนวนเต็มขนาดใหญ่", """
print(2 ** 100)
print(12345678901234567890 * 98765432109876543210)
"""),
    ("ก. ข้อมูลพื้นฐาน", "การปัดเศษด้วย round", """
print(round(2.5), round(3.5), round(2.675, 2), round(-0.5), round(7))
"""),
    ("ก. ข้อมูลพื้นฐาน", "คำสั่งของข้อความ", """
s = "PyRocket Lab"
print(s.upper(), s.lower(), len(s), s[0], s[-1], s[2:8], s[::-1])
print(s.replace("Lab", "Robot"), s.split(), "-".join(["a", "b", "c"]))
print(s.find("R"), s.count("o"), s.startswith("Py"), "   x  ".strip())
"""),
    ("ก. ข้อมูลพื้นฐาน", "การจัดรูปแบบข้อความ", """
print("%d-%s-%.2f" % (3, "x", 3.14159))
print("{:>6}|{:<6}|{:^6}".format("a", "b", "c"))
print(f"{3.14159:.2f} {42:05d} {255:x} {1234567:,}")
"""),
    ("ก. ข้อมูลพื้นฐาน", "การแปลงชนิดข้อมูล", """
print(int("42") + 1, float("3.5") * 2, str(10) + "0", int(3.99), bool(""), bool("0"))
print(type(1).__name__, type(1.0).__name__, type("a").__name__, type([]).__name__)
"""),
    ("ก. ข้อมูลพื้นฐาน", "ข้อความภาษาไทย", """
s = "สวัสดี"
print(len(s), s[0:3], s * 2)
"""),
    ("ข. โครงสร้างควบคุม", "if / elif / else ในลูป", """
for score in [45, 60, 79, 80, 100]:
    if score >= 80:
        grade = "A"
    elif score >= 60:
        grade = "B"
    else:
        grade = "F"
    print(score, grade)
"""),
    ("ข. โครงสร้างควบคุม", "range แบบมีระยะก้าว", """
print(list(range(5)), list(range(2, 8)), list(range(10, 0, -3)))
total = 0
for i in range(1, 11):
    total += i
print(total)
"""),
    ("ข. โครงสร้างควบคุม", "while กับ break และ continue", """
n = 0
while True:
    n += 1
    if n % 2 == 0:
        continue
    if n > 9:
        break
    print(n)
"""),
    ("ข. โครงสร้างควบคุม", "ลูปซ้อนลูป", """
for i in range(1, 4):
    row = ""
    for j in range(1, 4):
        row += str(i * j) + " "
    print(row)
"""),
    ("ข. โครงสร้างควบคุม", "เงื่อนไขต่อเนื่องและ and / or", """
x = 5
print(1 < x < 10, 1 < x > 10, x == 5 and x != 4, x < 0 or "fallback")
print("คู่" if x % 2 == 0 else "คี่", not x, 3 in [1, 2, 3])
"""),
    ("ข. โครงสร้างควบคุม", "for-else และ while-else", """
for n in [1, 3, 5]:
    if n % 2 == 0:
        break
else:
    print("ไม่มีเลขคู่")
k = 3
while k > 0:
    k -= 1
else:
    print("จบ", k)
"""),
    ("ค. โครงสร้างข้อมูล", "คำสั่งของ list", """
a = [3, 1, 2]
a.append(5)
a.insert(0, 9)
a.remove(1)
print(a, len(a), sum(a), max(a), min(a))
a.sort()
print(a, a.pop(), a.index(3), a[::-1])
"""),
    ("ค. โครงสร้างข้อมูล", "การตัด list และ list comprehension", """
nums = list(range(10))
print(nums[2:5], nums[:3], nums[-3:], nums[::2])
print([n * n for n in nums if n % 2 == 0])
print([[r * c for c in range(3)] for r in range(2)])
"""),
    ("ค. โครงสร้างข้อมูล", "tuple และการแตกค่า", """
a, b = 1, 2
a, b = b, a
first, *rest = [10, 20, 30]
print(a, b, first, rest, (1, 2) + (3,), len((1, 2, 3)))
"""),
    ("ค. โครงสร้างข้อมูล", "dict", """
d = {"b": 2, "a": 1}
d["c"] = 3
print(d, d.get("x", 0), list(d.keys()), list(d.items()))
print({k: v * 2 for k, v in d.items()}, "a" in d, len(d))
"""),
    ("ค. โครงสร้างข้อมูล", "set", """
a = {1, 2, 3, 3}
b = {3, 4}
print(sorted(a | b), sorted(a & b), sorted(a - b), len(a), 2 in a)
"""),
    ("ค. โครงสร้างข้อมูล", "enumerate / zip / sorted", """
names = ["cat", "ant", "bee"]
for i, n in enumerate(names, 1):
    print(i, n)
print(list(zip(names, [3, 1, 2])), sorted(names), sorted(names, key=len, reverse=True))
print(list(reversed(names)), any(n == "bee" for n in names), all(len(n) == 3 for n in names))
"""),
    ("ค. โครงสร้างข้อมูล", "ตาราง 2 มิติ", """
grid = [[0] * 3 for _ in range(3)]
grid[1][2] = 7
for row in grid:
    print(row)
print(sum(sum(r) for r in grid))
"""),
    ("ง. ฟังก์ชันและคลาส", "ค่าเริ่มต้นและการส่งค่าแบบระบุชื่อ", """
def area(w, h=2, *, unit="cm"):
    return f"{w * h} {unit}"
print(area(3), area(3, 4), area(h=5, w=2), area(1, unit="m"))
"""),
    ("ง. ฟังก์ชันและคลาส", "ฟังก์ชันเรียกตัวเอง", """
def fact(n):
    return 1 if n <= 1 else n * fact(n - 1)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
print(fact(10), [fib(i) for i in range(10)])
"""),
    ("ง. ฟังก์ชันและคลาส", "*args และ **kwargs", """
def show(*args, **kwargs):
    return len(args), sorted(kwargs.items())
print(show(1, 2, 3, b=2, a=1))
print(show(*[1, 2], **{"z": 0}))
"""),
    ("ง. ฟังก์ชันและคลาส", "lambda / map / filter", """
sq = lambda x: x * x
print(list(map(sq, [1, 2, 3])), list(filter(lambda x: x > 1, [1, 2, 3])))
"""),
    ("ง. ฟังก์ชันและคลาส", "คลาสและเมท็อด", """
class Robot:
    count = 0
    def __init__(self, name):
        self.name = name
        self.steps = 0
        Robot.count += 1
    def walk(self, n):
        self.steps += n
        return self
    def __str__(self):
        return f"{self.name} เดิน {self.steps} ก้าว"
r = Robot("Rocket").walk(2).walk(3)
print(r, Robot.count, isinstance(r, Robot))
"""),
    ("ง. ฟังก์ชันและคลาส", "การสืบทอดคลาส", """
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        return "..."
class Dog(Animal):
    def speak(self):
        return super().speak() + " โฮ่ง"
d = Dog("บ๊อบ")
print(d.name, d.speak(), isinstance(d, Animal))
"""),
    ("ง. ฟังก์ชันและคลาส", "try / except / finally", """
class TooFar(Exception):
    pass
def move(n):
    if n > 5:
        raise TooFar(f"ไกลเกินไป: {n}")
    return n
for n in [3, 9]:
    try:
        print(move(n))
    except TooFar as e:
        print("ผิดพลาด:", e)
    finally:
        print("จบรอบ")
try:
    int("x")
except (ValueError, TypeError) as e:
    print(type(e).__name__)
"""),
    ("ง. ฟังก์ชันและคลาส", "generator", """
def countdown(n):
    while n > 0:
        yield n
        n -= 1
print(list(countdown(4)), sum(x for x in countdown(4)))
"""),
    ("จ. ไลบรารีมาตรฐาน", "math", """
import math
print(math.sqrt(16), math.floor(2.7), math.ceil(2.1), math.gcd(12, 18), round(math.pi, 5))
print(math.sin(0), math.pow(2, 3), math.fabs(-3))
"""),
    ("จ. ไลบรารีมาตรฐาน", "random แบบกำหนด seed", """
import random
random.seed(7)
print(random.randint(1, 6), random.choice(["ซ้าย", "ขวา"]), round(random.random(), 6))
"""),
    ("จ. ไลบรารีมาตรฐาน", "string", """
import string
print(string.ascii_lowercase[:5], string.digits)
"""),
    ("จ. ไลบรารีมาตรฐาน", "collections", """
from collections import Counter, defaultdict
print(Counter("banana").most_common(2))
d = defaultdict(list)
d["a"].append(1)
print(dict(d))
"""),
    ("จ. ไลบรารีมาตรฐาน", "itertools", """
import itertools
print(list(itertools.permutations("abc", 2))[:3], list(itertools.accumulate([1, 2, 3])))
"""),
    ("จ. ไลบรารีมาตรฐาน", "json", """
import json
text = json.dumps({"b": [1, 2], "a": None}, sort_keys=True)
print(text, json.loads(text)["b"][1])
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "f-string แบบ = (3.8)", """
steps = 3
print(f"{steps=} {steps * 2=}")
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "ตัวดำเนินการ := (3.8)", """
data = [1, 5, 8]
if (n := len(data)) > 2:
    print("ยาว", n)
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "พารามิเตอร์แบบตำแหน่งเท่านั้น (3.8)", """
def move(dist, /, unit="ช่อง"):
    return f"{dist} {unit}"
print(move(2), move(3, unit="ก้าว"))
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "รวม dict ด้วย | (3.9)", """
print({"a": 1} | {"b": 2}, {"a": 1} | {"a": 9})
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "removeprefix / removesuffix (3.9)", """
print("robot.straight".removeprefix("robot."), "level1.py".removesuffix(".py"))
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "match-case (3.10)", """
def act(cmd):
    match cmd:
        case "left":
            return "เลี้ยวซ้าย"
        case ("go", n):
            return f"เดิน {n}"
        case _:
            return "ไม่รู้จัก"
print(act("left"), act(("go", 2)), act(0))
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "int.bit_count และ zip(strict) (3.10)", """
print((5).bit_count(), list(zip([1, 2], "ab", strict=True)))
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "add_note ของ exception (3.11)", """
try:
    raise ValueError("ค่าผิด")
except ValueError as e:
    e.add_note("ตรวจบรรทัดก่อนหน้า")
    print(e, e.__notes__)
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "คำสั่ง type และ f-string ซ้อนเครื่องหมายคำพูด (3.12)", """
type Point = tuple[int, int]
print(Point.__name__, f"{"a" + "b"}")
"""),
    ("ฉ. ไวยากรณ์รุ่นใหม่", "copy.replace (3.13)", """
import copy
from dataclasses import dataclass
@dataclass
class P:
    x: int
    y: int
print(copy.replace(P(1, 2), x=5))
"""),
]

ERRORS = [
    ("ก. ไวยากรณ์", "ลืมเครื่องหมาย : หลัง for", """
for i in range(3)
    print(i)
"""),
    ("ก. ไวยากรณ์", "ลืมปิดวงเล็บ", """
print("สวัสดี"
print("PyRocket")
"""),
    ("ก. ไวยากรณ์", "ลืมปิดเครื่องหมายคำพูด", """
print("สวัสดี)
"""),
    ("ก. ไวยากรณ์", "ใช้ = แทน == ในเงื่อนไข", """
x = 5
if x = 5:
    print("ห้า")
"""),
    ("ก. ไวยากรณ์", "ลืมเครื่องหมายจุลภาคใน list", """
nums = [1 2 3]
print(nums)
"""),
    ("ก. ไวยากรณ์", "พิมพ์คำสั่งด้วยตัวพิมพ์ใหญ่", """
For i in range(3):
    print(i)
"""),
    ("ก. ไวยากรณ์", "return นอกฟังก์ชัน", """
x = 1
return x
"""),
    ("ข. การเยื้องบรรทัด", "ไม่เยื้องบรรทัดหลัง for", """
for i in range(3):
print(i)
"""),
    ("ข. การเยื้องบรรทัด", "เยื้องบรรทัดโดยไม่จำเป็น", """
x = 1
    print(x)
"""),
    ("ข. การเยื้องบรรทัด", "เยื้องกลับไม่ตรงระดับเดิม", """
for i in range(2):
    print(i)
  print("จบ")
"""),
    ("ค. ชื่อผิด", "สะกดชื่อตัวแปรผิด", """
total = 10
print(totl + 5)
"""),
    ("ค. ชื่อผิด", "สะกดชื่อคำสั่ง print ผิด", """
pritn("สวัสดี")
"""),
    ("ค. ชื่อผิด", "สะกดชื่อคำสั่งของหุ่นยนต์ผิด", """
robot.straigt(1)
"""),
    ("ค. ชื่อผิด", "สะกดชื่อคำสั่งของโมดูล math ผิด", """
import math
print(math.sqroot(16))
"""),
    ("ค. ชื่อผิด", "สะกดชื่อคำสั่งของ list ผิด", """
items = [1, 2]
items.apend(3)
"""),
    ("ค. ชื่อผิด", "ใช้ตัวแปรในฟังก์ชันก่อนกำหนดค่า", """
count = 0
def add():
    count += 1
add()
"""),
    ("ค. ชื่อผิด", "เรียกโมดูลที่ไม่มี", """
import robots
"""),
    ("ง. ชนิดข้อมูลและค่า", "บวกข้อความกับตัวเลข", """
score = 8
print("คะแนน " + score)
"""),
    ("ง. ชนิดข้อมูลและค่า", "แปลงข้อความที่ไม่ใช่ตัวเลข", """
n = int("สาม")
"""),
    ("ง. ชนิดข้อมูลและค่า", "หารด้วยศูนย์", """
steps = 0
print(10 / steps)
"""),
    ("ง. ชนิดข้อมูลและค่า", "เรียกลำดับเกินขนาดของ list", """
path = [1, 2, 3]
print(path[3])
"""),
    ("ง. ชนิดข้อมูลและค่า", "เรียก key ที่ไม่มีใน dict", """
pos = {"x": 1}
print(pos["y"])
"""),
    ("ง. ชนิดข้อมูลและค่า", "เรียกตัวแปรเหมือนเป็นฟังก์ชัน", """
speed = 5
speed()
"""),
    ("ง. ชนิดข้อมูลและค่า", "ส่งค่าให้ฟังก์ชันเกินจำนวน", """
def walk(n):
    return n
walk(1, 2)
"""),
    ("ง. ชนิดข้อมูลและค่า", "เรียกคำสั่งจากค่า None", """
result = None
result.append(1)
"""),
    ("ง. ชนิดข้อมูลและค่า", "ส่งข้อความให้คำสั่งหุ่นยนต์", """
robot.straight("2")
"""),
    ("ง. ชนิดข้อมูลและค่า", "ฟังก์ชันเรียกตัวเองไม่สิ้นสุด", """
def loop(n):
    return loop(n + 1)
loop(0)
"""),
]

ROBOT = [
    ("ก. ผ่านด่าน", "เฉลยด่าน 1", "1", ANSWERS["1"]["code"]),
    ("ก. ผ่านด่าน", "เฉลยด่าน 2", "2", ANSWERS["2"]["code"]),
    ("ก. ผ่านด่าน", "เฉลยด่าน 3", "3", ANSWERS["3"]["code"]),
    ("ก. ผ่านด่าน", "เฉลยด่าน 4", "4", ANSWERS["4"]["code"]),
    ("ก. ผ่านด่าน", "ด่าน 1 ด้วยฟังก์ชันที่เขียนเอง", "1", """
def stair(n):
    robot.straight(n)
    robot.turn(-90)
    robot.straight(n)
    robot.turn(90)

for i in range(3):
    stair(1)
    print("ขั้นที่", i + 1)
"""),
    ("ก. ผ่านด่าน", "ด่าน 1 ด้วย while และตัวแปร", "1", """
done = 0
while done < 3:
    robot.straight(1)
    robot.turn(-90)
    robot.straight(1)
    robot.turn(90)
    done += 1
print("ถึงธงแล้ว", done)
"""),
    ("ข. ไม่ถึงธง", "เดินก้าวเดียวแล้วจบ", "1", """
robot.straight(1)
"""),
    ("ข. ไม่ถึงธง", "เดินหน้า ถอยหลัง และหมุนครบรอบ", "1", """
robot.straight(1)
robot.straight(-1)
robot.turn(360)
robot.turn(-450)
"""),
    ("ข. ไม่ถึงธง", "เดินทีละเศษส่วนของช่อง", "1", """
robot.straight(0.5)
robot.straight(0.5)
robot.turn(-90)
robot.straight(0.25)
robot.straight(0.75)
"""),
    ("ข. ไม่ถึงธง", "เรียกคำสั่งโดยไม่ใส่ค่า", "1", """
robot.straight()
robot.turn()
robot.straight(1)
"""),
    ("ข. ไม่ถึงธง", "print สลับกับการเดิน", "1", """
print("เริ่ม", end=" ")
print("เดิน")
robot.straight(1)
print("ค้าง", end="")
robot.turn(-90)
print("จบ")
"""),
    ("ค. ชน", "ชนสิ่งกีดขวาง", "1", """
robot.straight(2)
"""),
    ("ค. ชน", "ชนขอบสนาม", "1", """
robot.turn(180)
robot.straight(1)
"""),
    ("ค. ชน", "ชนกลางลูป while", "1", """
steps = 0
while steps < 6:
    robot.straight(1)
    steps += 1
    if steps == 3:
        print("ครึ่งทางแล้ว!")
"""),
    ("ค. ชน", "เดินเฉียงออกนอกสนาม", "1", """
robot.straight(0.5)
robot.turn(45)
robot.straight(1.2)
"""),
    ("ค. ชน", "ชนสิ่งกีดขวางด่าน 4", "4", """
robot.straight(1)
robot.turn(-90)
robot.straight(2)
"""),
    ("ง. ผิดพลาดและขีดจำกัด", "โค้ดผิดหลังหุ่นเดินไปแล้ว", "1", """
robot.straight(1)
x = 1 / 0
robot.turn(90)
"""),
    ("ง. ผิดพลาดและขีดจำกัด", "ส่งค่า True ให้คำสั่งเดิน", "1", """
robot.straight(True)
"""),
    ("ง. ผิดพลาดและขีดจำกัด", "ลูปไม่สิ้นสุดที่ไม่มีคำสั่งหุ่นยนต์", "1", """
x = 0
while True:
    x = x + 1
"""),
    ("ง. ผิดพลาดและขีดจำกัด", "ลูปไม่สิ้นสุดที่สั่งหุ่นหมุน", "1", """
while True:
    robot.turn(90)
"""),
    ("ง. ผิดพลาดและขีดจำกัด", "ดักการชนด้วย try / except", "1", """
try:
    robot.straight(5)
except Exception:
    print("จับได้")
robot.turn(90)
"""),
]

def load_harness():
    src = (ROOT / "pyodide_worker.js").read_text(encoding="utf-8")
    m = re.search(r"const HARNESS = String\.raw`(.*?)`;", src, re.S)
    if not m:
        sys.exit("หา HARNESS ใน pyodide_worker.js ไม่เจอ")
    ns = {}
    exec(compile(m.group(1), "<harness>", "exec"), ns)
    return ns["run_student"]

def main():
    if sys.version_info[:2] != (3, 13):
        print(f"คำเตือน: กำลังใช้ Python {platform.python_version()} — ผลอ้างอิงควรสร้างด้วย 3.13.x "
              "ให้ตรงกับ Pyodide", file=sys.stderr)
    run_student = load_harness()

    cases = []
    def add(suite, prefix, i, group, name, code, level_key=None):
        lv = dict(LEVELS[level_key]) if level_key else dict(BLANK)
        cases.append({
            "id": f"{prefix}{i:02d}", "suite": suite, "group": group, "name": name,
            "code": code.strip("\n"), "levelKey": level_key,
            "level": {"N": 6, "start": lv["start"], "goal": lv["goal"], "obs": lv["obs"]},
        })
    for i, (g, n, c) in enumerate(LANGUAGE, 1):
        add("language", "L", i, g, n, c)
    for i, (g, n, c) in enumerate(ERRORS, 1):
        add("error", "E", i, g, n, c)
    for i, (g, n, k, c) in enumerate(ROBOT, 1):
        add("robot", "R", i, g, n, c, k)

    results = {}
    for case in cases:
        data = json.loads(run_student(case["code"], json.dumps(case["level"])))
        data.pop("stats", None)
        results[case["id"]] = data

    meta = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cases": {s: sum(1 for c in cases if c["suite"] == s) for s in ("language", "error", "robot")},
    }
    (HERE / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "reference.json").write_text(
        json.dumps({"meta": meta, "results": results}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"{meta['implementation']} {meta['python']} — {len(cases)} โปรแกรม {meta['cases']}")
    for case in cases:
        st = results[case["id"]]["outcome"]["status"]
        if case["suite"] == "language" and st != "ok":
            print("  ! ชุดภาษา แต่รันไม่ผ่าน:", case["id"], case["name"], results[case["id"]]["outcome"].get("full"))
        if case["suite"] == "error" and st != "error":
            print("  ! ชุดข้อผิดพลาด แต่ไม่ได้ผลเป็น error:", case["id"], case["name"], st)

if __name__ == "__main__":
    main()
