from pathlib import Path

path = Path('xau_lab/real_tick_lab.py')
text = path.read_text(encoding='utf-8')

old = '    m15_modes = ["veto", "strict"]\n'
new = '    m15_modes = ["off", "veto", "strict"]\n'
if old not in text:
    raise SystemExit('m15 candidate marker not found')
text = text.replace(old, new, 1)

old2 = '''    m15_buy_ok = (not m15_down) if c.m15_mode == "veto" else m15_up
    m15_sell_ok = (not m15_up) if c.m15_mode == "veto" else m15_down
'''
new2 = '''    if c.m15_mode == "off":
        m15_buy_ok = True
        m15_sell_ok = True
    elif c.m15_mode == "veto":
        m15_buy_ok = not m15_down
        m15_sell_ok = not m15_up
    else:
        m15_buy_ok = m15_up
        m15_sell_ok = m15_down
'''
if old2 not in text:
    raise SystemExit('m15 signal marker not found')
text = text.replace(old2, new2, 1)

path.write_text(text, encoding='utf-8')
print('Added one economically defensible revision: optional M15 filter removal while retaining M5 and M1 trend logic')
