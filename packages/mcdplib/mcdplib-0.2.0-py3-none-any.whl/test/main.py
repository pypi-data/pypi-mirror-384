from mcdplib import *

print(os.listdir("."))

dp = Datapack({})
dp.load("data")
dp.build({})
dp.write(".out")