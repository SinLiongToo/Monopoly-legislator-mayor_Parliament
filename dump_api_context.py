with open("main.30476152531ff721.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = 0
while True:
    pos = text.find("https://priso.cy.gov.tw/api/", pos)
    if pos == -1:
        break
    print(f"\nFound at index {pos}:")
    print(text[max(0, pos-200):min(len(text), pos+300)])
    pos += 1
