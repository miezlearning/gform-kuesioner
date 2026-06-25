"""Check raw_data[1][10][3] value for email collection detection"""
import requests, re, json

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
response = requests.get(FORM_URL, timeout=15)
html = response.text

match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
raw_data = json.loads(match.group(1))

# raw_data[1][10] seems to contain form settings
settings = raw_data[1][10]
print(f"raw_data[1][10] = {settings}")
print(f"  [0] = {settings[0]}")
print(f"  [1] = {settings[1]}")
print(f"  [2] = {settings[2]}")
print(f"  [3] = {settings[3]}  <-- possible email collection flag (2=collect email?)")
print(f"  [4] = {settings[4]}")
print(f"  [5] = {settings[5]}")
print(f"  [6] = {settings[6]}")

# Also check raw_data[1][2] and other top-level settings
for i in range(min(len(raw_data[1]), 15)):
    val = raw_data[1][i]
    if isinstance(val, (int, float, bool, str, type(None))):
        print(f"raw_data[1][{i}] = {val}")
    elif isinstance(val, list) and len(val) < 20:
        print(f"raw_data[1][{i}] = {val}")
    else:
        typ = type(val).__name__
        ln = len(val) if hasattr(val, '__len__') else '?'
        print(f"raw_data[1][{i}] = <{typ}, len={ln}>")
