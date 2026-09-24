# 課程用「待重構」範例：刻意寫得很糟，供單元 3「Codex 重構」練習。
# 練習目標：讓 Codex 把它改成有型別註記、無重複、可測試的版本，並保持行為不變。
def r(t):
    x = ""
    c = 0
    d = 0
    for i in range(len(t)):
        if t[i]["done"] == True:
            d = d + 1
            x = x + "[x] " + t[i]["title"] + "\n"
        else:
            x = x + "[ ] " + t[i]["title"] + "\n"
        c = c + 1
    if c == 0:
        x = x + "no todos\n"
    x = x + "----\n"
    x = x + str(d) + "/" + str(c) + " done\n"
    return x
