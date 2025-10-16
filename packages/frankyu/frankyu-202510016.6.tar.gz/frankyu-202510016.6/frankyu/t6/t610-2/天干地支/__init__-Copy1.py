tian = ""



tiangan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
dizhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

for i in tiangan:
    tian = tian+i
print(tian)

di = ""
for i in dizhi:
    di = di + i
print(di)




# 组合成60甲子
ganzhi_cycle = []
for i in range(60):
    gan = tiangan[i % 10]
    zhi = dizhi[i % 12]
    ganzhi_cycle.append(gan + zhi)

print(ganzhi_cycle)

t = tian*6
t

d = di*5
d

nian = []
for i in range(1,61,1):
    nian.append(i)


tt = [i for i in t]
dd = [i for i in d]
nian = nian



ttdd = [(x+y) for x,y in zip(tt,dd)]
ttdd









