import requests, json, re

url = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
resp = requests.get(url, timeout=10)
match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', resp.text, flags=re.S)
if match:
    data = json.loads(match.group(1))
    questions = data[1][1]
    print(f"Total raw items: {len(questions)}")
    for i, q in enumerate(questions):
        title = q[1] or ""
        type_code = q[3]
        desc = q[2] or ""
        sub = q[4] if len(q) > 4 else None
        entry_id = sub[0][0] if sub and len(sub) > 0 and len(sub[0]) > 0 else None
        options = []
        if sub and len(sub) > 0 and len(sub[0]) > 1 and sub[0][1]:
            options = [o[0] for o in sub[0][1] if o and len(o) > 0 and o[0] is not None]
        scale_labels = []
        if sub and len(sub) > 0 and len(sub[0]) > 3 and sub[0][3]:
            scale_labels = sub[0][3]
        required = bool(sub[0][2]) if sub and len(sub) > 0 and len(sub[0]) > 2 else False
        print(f"[{i}] type={type_code:2d} entry={str(entry_id):12s} req={str(required):5s} title='{title[:40]}' opts={options[:5]}")
