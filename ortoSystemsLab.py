import math
# import autoLin
print "Algorithm for finding the orthogonal systems in set of lines"

# get statistic properties of input set
def autoLin_getProperties(mySet):
  mySet.sort()
  n = len(mySet)
  myMin = mySet[0]
  myMax = mySet[n-1]
  mean = sum(mySet)/len(mySet)
  std = math.sqrt(sum((x-mean) ** 2 for x in mySet) / n)
  medianIndex = int(0.5*(n+1))
  if len(mySet) == 1:
    median = mySet[0]
  else:
    median = mySet[medianIndex]
  print " n: %i \n mean: %0.2f \n std: %0.2f \n median: %0.2f \n min: %0.2f \n max: %0.2f \n " % (n, mean, std, median, myMin, myMax)
  return [n, mean, std, median, myMin, myMax]

def getUpperQuartileIndexes(mySet):
  sortedSet = sorted(mySet.items(), key=lambda x: x[1])
  upIdxs = []
  for pair in sortedSet:
    upIdxs.append(pair[0])
  n = len(mySet)
  upperIndex = int(0.75*n)
  upIdxs = upIdxs[upperIndex:]
  upIdxs.sort()
  return upIdxs
  
def getMaxDir(pairs, cluster):
  clusterValues = {}
  for idx in cluster:
    clusterValues[idx] = pairs[idx]
  sortedClusters = sorted(clusterValues.items(), key=lambda x: x[1])
  return sortedClusters[-1][0]

# STEP 1 COMPUTE HISTOGRAM
# load data/compute using autolin stats!
inSHP = r"c:\Users\jsilhavy\Documents\Prace\Projekty\Uni\Thesis\Vyzkum\Artefakt\hs_0_r0.shp"
# hist = autoLin.getHistogram(inSHP, 4)
# hist = r"c:\Users\jsilhavy\Documents\Prace\Projekty\Uni\Thesis\Vyzkum\Artefakt\hs_0_r0_hist.csv"
# hist = r"c:\Users\jsilhavy\Documents\Prace\Projekty\Uni\Thesis\Vyzkum\Artefakt\hs_0_r27_hist.csv"
hist = r"c:\Users\jsilhavy\Documents\Prace\Projekty\Uni\Thesis\Papers\AutoLin\GISData\AutoLin\auto_zm50_dem_50_hist.csv"
hist = r"c:\Users\jsilhavy\Documents\Prace\Projekty\Uni\Thesis\Papers\AutoLin\GISData\AutoLin\geology_faults_zm10_hist.csv"

p7 = 3

inHist = open(hist, 'r')
# fill up dictionary
# aDict = {}
# for line in inHist:
#   line = line.strip()
#   line = line.replace(",", ".")
#   histValues = line.split(';')
#   angle = int(histValues[0])
#   lw = float(histValues[4])
#   # print "%s: %s" % (angle, lw)
#   aDict[angle] = lw
#   if angle == 90:
#     break
# 
# # find ortho pairs:
# for i in range(0, 90, 1):
#   
#   aDict[i]


# STEP 2 COMPUTE MOVING AVERAGE
def getSubset(angles, size, angle):
  if angle < size:
    subsetA = angles[angle-size:]
    subsetB = angles[:angle+size+1]
    subset = subsetA+subsetB
  elif angle > len(angles)-1-size:
    subsetA = angles[angle-size:]
    subsetB = angles[:size+1-(len(s)-angle)]
    subset = subsetA+subsetB
  else:
    subset = angles[angle-size:angle+size+1]
  return subset

t = range(0, 180, 1)
count = 0
s = []

for row in inHist:
  rs = row.split(";")
  lw = rs[4].strip()
  angle = int(rs[1].strip())
  count += angle
  s.append(float(lw.replace(",", ".")))
  if angle == 90:
    break

mA = {}
for i in t:
  subset = getSubset(s, p7, i)
  mAvalue = mean = sum(subset)#/len(subset)
  mA[i] = mAvalue
  
# print mA

# STEP 3 FIND ORTHOGONAL PAIRS
pairsArray = []
pairs = {}
for i in range(0,90,1):
  pairsArray.append(mA[i] + mA[i+90])
  pairs[i] = mA[i] + mA[i+90]

# STEP 4 FILTER PAIRS
upIdxs = getUpperQuartileIndexes(pairs)

# STEP 5 CLUSTER PAIRS
clusters = []
clusters.append([])
cIdx = 0
gap = p7+1
for i in range(0, len(upIdxs)-1, 1):
  clusters[cIdx].append(upIdxs[i])
  if ((upIdxs[i+1] - upIdxs[i]) > gap):
    cIdx+=1
    clusters.append([])
  # last feature:
  if (i == (len(upIdxs)-2)):
    clusters[cIdx].append(upIdxs[i+1])
print clusters

# connect clusters over zero
firstIdx = clusters[0][0]
lastIdxDiff = clusters[-1][-1] - 90
if (firstIdx - lastIdxDiff) < gap:
  clusters[0] = clusters[0] + clusters[-1]
  del clusters[-1]
print clusters

# STEP 6 COMPUTE REPRESENTATIVE DIRECTIONS
orthoDir = []
for cluster in clusters:
  maxDir = getMaxDir(pairs, cluster)
  orthoDir.append("{0} - {1} dg".format(maxDir, maxDir+90))

print orthoDir