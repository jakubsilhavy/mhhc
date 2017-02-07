# class for working with timeBenchmark - id, length and azimuth
import time
class timeStamp:
  def __init__(self, comment, currTime, logFileName):
    self.comment = comment
    self.time = currTime
    self.logFileName = logFileName
    self.timeStamps = []
    
  def printMe(self):
    print ("%s: %s" % (self.time, self.comment))
    
  def log(self,comment):
    logFile = open(self.logFileName, 'a')
    currTime = time.time()
    myTimeStamp = timeStamp(comment, currTime, "")
    self.timeStamps.append(myTimeStamp)
    myTimeStamp.printMe()
    if comment != "start":
      textLog = "%s: %0.3f: %s" % (time.strftime("%m%d_%H%M%S"), self.timeStamps[-1].time-self.timeStamps[-2].time,self.timeStamps[-2].comment)
      logFile.write(textLog + "\n")
#       print textLog
    if comment == "finish":
      textLog = "%s: %0.3f: %s" % (time.strftime("%m%d_%H%M%S"), self.timeStamps[-1].time-self.timeStamps[0].time, "from start to end")
      logFile.write(textLog + "\n")
#       print textLog
    logFile.close()