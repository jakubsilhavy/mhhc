# function to compute statistic of two line segments
import math
class point:
  def __init__(self, X, Y):
    self.X = X
    self.Y = Y
    
def lineLength(A,B):
  return math.sqrt(math.pow(A.X-B.X,2)+math.pow(A.Y-B.Y,2))
  
def lineAzimuth(A,B):
  # arctg(dY/dX)
#   dY = math.fabs(A.Y - B.Y)
#   dX = math.fabs(A.X - B.X)
  dY = (A.Y - B.Y)
  dX = (A.X - B.X)
  atan2 = math.atan2(dY,dX)
  if (atan2<0):
    atan2+=math.pi
  if (atan2<=math.pi/2):
    atan2=math.pi/2-atan2
  if (atan2>math.pi/2):
    atan2=3*math.pi/2-atan2
  return math.degrees(atan2)

# orthogonal distance between point C and line segment A,B
def orthoDist(C, A, B):
  a = lineLength(B,C)
  b = lineLength(A,C)
  c = lineLength(A,B)
  s = (a+b+c)/2
  sqrtDomain = s*(s-a)*(s-b)*(s-c)
  if (sqrtDomain > 0):
    S = math.sqrt(s*(s-a)*(s-b)*(s-c))
  else:
    S = 0
  return 2*S/c

def lineStat(A,B,C,D):

  # postupne kontrola parametru - jeden vyjde nula - ostatni nepocitam!
  # lenght ratio
  lenghtAB = lineLength(A,B)
  lenghtCD = lineLength(C,D)
  
  # ratio 
  dL = (lenghtAB / lenghtCD)
  if dL > 1:
    dL = 1/dL
#   dL = 100*dL
#   print "lenght ratio: %s" % dL

  # azimuth difference
  sigmaMin = 30*math.pi/180
  sigmaAB = lineAzimuth(A,B)
  sigmaCD = lineAzimuth(C,D)
  dSigma = math.fabs(sigmaAB - sigmaCD)
  sigmaRatio =  1 - dSigma/sigmaMin
#   print "azimuth differences: %f [dg]" % (dSigma/math.pi*180)
#   print "azimuth ratio: %f" % (sigmaRatio)
  
  # orthogonal distance
  orthoA = orthoDist(A, C, D)
  orthoB = orthoDist(B, C, D)
  orthoC = orthoDist(C, A, B)
  orthoD = orthoDist(D, A, B)
#   print "ortho"
#   print orthoA
#   print orthoB
#   print orthoC
#   print orthoD
  
  orthoAv = (orthoA+orthoB+orthoC+orthoD)/4
  scaleNumber = 50 # 1:50 000
  mmTolerance = 4 # mm
  orthoRatio = 1 - orthoAv/(scaleNumber*mmTolerance)
#   print "ortho ratio: %f" % (orthoRatio)
  
  # vahy
  angleW = 0.5
  distW = 0.25
  lengthW = 0.25
  
  return (angleW*sigmaRatio+distW*orthoRatio+lengthW*dL)/(angleW+distW+lengthW)
#   # THE INPUT:  
#   # first line-segment
#   A = point(-418854.84,-1188851.413)
#   B = point(-417543.136,-1189892.849)
#   
#   # second line-segment
#   C = point(-418840.426,-1188963.124)
#   D = point(-417633.225,-1189867.624)
#   
#   # call the fucntion to compute similarity degree of two lines (A,B) and (C,D)
#   print lineStat(A,B,C,D)