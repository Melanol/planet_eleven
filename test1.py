import os


subds = next(os.walk('./sprites'))[1]
print("subds =", subds)

allsubds = []
for subd in subds:
    next_subd = next(os.walk('./sprites/' + subd))[1]
    if next_subd:
        arr = []
        for d in next_subd:
            arr.append('sprites/' + subd + '/' + d)
        allsubds += arr
    else:
        allsubds += ['sprites/' + subd]
print("allsubds =", allsubds)
