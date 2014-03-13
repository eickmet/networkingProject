#Travis Eickmeyer
#DATE: 3/09/14
#CLASS: CSCI 367
#Project: Chat Server/Client
#File: client.py
#Professor: Michael Meehan

import socket
import sys
import select
import random
import time
import errno

BUFSIZE = 240
MAXRECV = 512

#TODO: Parseing the data from the recv also try this in server as well.
# Broken pipe issue need to catch the broken pipe error. Ak other people how to do that maybe a try except thing with an exit or something like that.

class Client(object):

    def __init__(self,name,debug,man,ai,host,port):
        self.name = name.upper()
        self.flag = False
        self.port = int(port)
        self.host = host
        self.players = ()
        self.sendList = ()
        self.debug = debug
        self.man = man
        self.ai = ai
        self.minplayers = 0
        self.lobbytimeout = 0
        self.actiontimeout = 0
        #Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host,self.port))
            #Send my name
            joinmsg = '(cjoin(%s))' % (self.name)
            self.sock.send(joinmsg)
            data = self.sock.recv(BUFSIZE)
            #print "Message received:",data
            # Contains client address, set it
            valid = self.parseLine(data)
            if valid == False:
                sys.exit(1)     #Could cjoin again
            else:
                print "Name is %s"%(self.name)
                self.prompt = '<'+ self.name + '>: '
        except socket.error,e:
            print 'Could not connect to chat server @%d' % self.port
            sys.exit(1)

    def printServerData(self):
        print "******************"
        print "* Server Details *"
        print "******************"
        print "Min Players - %d" %(self.minplayers)
        print "Lobby Timeout - %d" %(self.lobbytimeout)
        print "Action Timeout - %d" %(self.actiontimeout)
        print "*********************"

    def printPlayers(self):
        nan = '' 
        print "Here are the player currently on the server:" 
        print "********************************************"
        for p in self.players:
            if p == self.name:
                print "%s <- YOU" %(p)
                nan = p
            else:
                print p
        print "********************************************"
        print "Your Name is: %s"%(nan)
        print "********************************************"

    def printStrike(self,num,reason):
        line  = "STRIKE: This is strike %s. Reason: %s" %(num,reason)
        print line 

    def displayMessage(self,fromWho,message):
        line = "[%s]: %s" %(fromWho,message)
        print line

    def makeAutoArr(self):
        autoArr = []
        autoArr.append("(cchat(all)(Cats have somewhere between one and three tongues and thier tail have been known to fall off but luckly they can be regrown.))")
        autoArr.append("(cchat(all)(Horses can not live in space.))")
        autoArr.append("(cchat(all)(PoKeMoN has the most accurate representation of evolution.))")
        autoArr.append("(cchat(all)(The rain falls due to its wish to be closer to the ground.))")            
        autoArr.append("(cchat(all)(In the name \'DJANGO\' the D is silent.))")
        autoArr.append("(cchat(all)(Trees grow straight up due to their innate fear of the ground))")
        autoArr.append("(cchat(all)(Ping Pong balls are more spherical than LEGO blocks.))")
        autoArr.append("(cchat(all)(A Dog\'s tail can wag up to 100 miles per hour.))")
        autoArr.append("(cchat(all)(Wild Buffalo are actaully domesticated.))")
        autoArr.append("(cchat(all)(Deer prance more often than raindeer.))")
        autoArr.append("(cchat(all)(It is unknown what happens when matter and anti-matter meet))")
        autoArr.append("(cchat(all)(Roads were initial developed for travel.))")
        autoArr.append("(cchat(all)(Alaska is not an island next to Hawaii.))")
        autoArr.append("(cchat(all)(Chairs are not designed for Blue Whales.))")
        autoArr.append("(cchat(all)(Pineapples cannot fly.))")
        autoArr.append("(cchat(all)(All facts have been said before, even this one.))")
        autoArr.append("(cchat(all)(The Vacican City currently has 11.8 popes per square mile.))")
        autoArr.append("(cchat(all)(Clouds kill more people every year than asteroids.))")
        autoArr.append("(cchat(all)(Statisticlly you have a 4.5% chance of receiving this message))")
        autoArr.append("(cchat(all)(The greenest place in the world is not in Greenland.))")
        autoArr.append("(cchat(all)(China is the largest producer of the color red.))")
        autoArr.append("(cchat(all)(If Elephants had big enough ears it still could not fly.))")
        autoArr.append("(cchat(all)(Blank spaces are actually 12 pixels across.))")
        autoArr.append("(cchat(all)(Blind people can read invisible ink.))")
        return autoArr

    def randomPlayer(self):
        sendTo = random.choice(self.sendList)
        #print "Player messgae is send To: ",sendTo
        return sendTo

    def stripNon(self,line):    #Not used but kept in case I need it.
        newline = ''
        for x in range(0,len(line)):
            if (ord(line[x]) >= 32 and (ord(line[x]) <= 126)):
                newline += line[x]
        return newline

    def checkForMore(self,line,i):
        if i >= len(line):
            #print "Recved more"
            return self.sock.recv(MAXRECV)
        return ''
            
    def dosstat(self,line):
        i = 0
        players = ''
        line += self.checkForMore(line,i)
        if line[0] == '(':
            i+= 1
            line += self.checkForMore(line,i)
            while line[i] != ')':
                players += line[i]
                i += 1
                line += self.checkForMore(line,i)
            i += 1
            line += self.checkForMore(line,i)
            if line[i] == ')':
                line = line[i+1:]
                players = players.split(',')
                self.players = players
                self.sendList = players
                self.sendList.append('all')
                self.sendList.append('any')
                self.printPlayers()
                if len(line) > 0:
                    self.parseLine(line)
                else:
                    return True
            else:
                return False
        else:
            return False

    def doschat(self,line):
        #look for '('
        pfrom = ''
        msg = ''
        i = 0
        line += self.checkForMore(line,i)
        if line[i] == '(':      #Paren for first arg in this case who it is from
            i +=1
            line += self.checkForMore(line,i)
            while line[i] != ')':   # loop until finds matching paren stuff between is who it is from
                pfrom += line[i]
                i += 1
                line += self.checkForMore(line,i)
            i += 1
            line += self.checkForMore(line,i)
            if line[i] == '(':
                i +=1
                line += self.checkForMore(line,i)
                try:
                    while line[i] != ')':
                        msg += line[i]
                        i += 1
                        line += self.checkForMore(line,i)
                    i += 1
                except LookupError,e:
                    line += self.checkForMore(line,i)
                    print "Lookup Error len(line): %d| pos: %d: line: %s" %(len(line),i,line)
                    sys.exit()
                except IndexError,e:
                    line += self.checkForMore(line,i)
                    print "Index Error len(line): %d| pos: %d: line: %s" %(len(line),i,line)
                    sys.exit()
                line += self.checkForMore(line,i)
                if line[i] == ')':

                    #looks to be a properly formatted chat message set line to Line[i:]
                    line = line[i+1:]
                    self.displayMessage(pfrom,msg)
                    if len(line) > 0:       #more stuff in data
                        self.parseLine(line)
                    else:
                        return True
                else:
                    #print "Strike Malformed missing ending )"
                    #print "Line:", line
                    return False
            else:
                #print "Strike Malformed missing ending )"
                #print "Line:", line
                return False

        else:
            #print "Strike Malformed missing ending )"
            #print "Line:", line
            return False
        return True

    def dosjoin(self, line):
        #print "In sjoin"
        #look for '('
        name = ''
        players = ''
        serverArgs = ''
        i = 0
        line += self.checkForMore(line,i)
        if line[i] == '(':      #Paren for first arg in this case who it is from
            i +=1
            line += self.checkForMore(line,i)
            while line[i] != ')':   # loop until finds matching paren stuff between is who it is from
                name += line[i]
                i += 1
                line += self.checkForMore(line,i)
            i += 1
            line += self.checkForMore(line,i)
            if line[i] == '(':
                i +=1
                line += self.checkForMore(line,i)
                while line[i] != ')':
                    players += line[i]
                    i += 1
                    line += self.checkForMore(line,i)
                i += 1
                line += self.checkForMore(line,i)
                if line[i] == '(':  #phase 2
                    i +=1
                    line += self.checkForMore(line,i)
                    while line[i] != ')':
                        serverArgs += line[i]
                        i += 1
                        line += self.checkForMore(line,i)
                    i += 1
                    line += self.checkForMore(line,i)
                    if line[i] == ')':
                        line = line[i+1:]
                        #print "JOIN:%s:%s:%s:" %(name,players,serverArgs)
                        self.processJoinPhase2(name,players,serverArgs)
                        if len(line) > 0:       #more stuff in data
                            self.parseLine(line)
                elif line[i] == ')':    #phase 1
                    line = line[i+1:]
                    #print "JOIN:%s:%s:" %(name,players)
                    self.processJoinPhase1(name,players)
                    if len(line) > 0:       
                        self.parseLine(line)
                    else:
                        return True
                else:
                    #print "Join malformed Missing ending )"
                    return False
            else:
                #print "Join malformed Missing begin players ("
                return False
        else:
            #print "Join malformed missing begining name ("
            return False
        return True

    def processJoinPhase2(self,name,players,serverArgs):
        self.name = name
        serverArgs = serverArgs.split(',')
        self.minplayers = int(serverArgs[0])
        self.lobbytimeout = int(serverArgs[1])
        self.actiontimeout = int(serverArgs[2])
        self.printServerData()
        playerList = players.split(',')
        self.players = playerList
        self.printPlayers()
        return True

    def processJoinPhase1(self,name,players):
        self.name = name
        playerList = players.split(',')
        self.players = playerList
        self.printPlayers()
        return True

    def dosnovac(self,line):
        print "No Vacancy in Server"
        return False

    def dostrike(self,line):
        i = 0
        num = ''
        reason = ''
        line += self.checkForMore(line,i)
        if line[i] == '(':
            i+=1
            line += self.checkForMore(line,i)
            num += line[i]
            i+=1
            line += self.checkForMore(line,i)
            i+= 1
            line += self.checkForMore(line,i)
            if line[i] == '(':
                i += 1
                line += self.checkForMore(line,i)
                while line[i] != ')':
                    reason += line[i]
                    i += 1
                    line += self.checkForMore(line,i)
                i +=1
                line += self.checkForMore(line,i)
                if line[i] == ')':
                    line += self.checkForMore(line,i)
                    line = line[i+1:]
                    self.printStrike(num,reason)
                    if line == None:
                        self.parseLine(line)
                    else:
                        return True
                else:
                    #print "Stuff wrong"
                    return False
            else:
                #print "More stuff wrong"
                return False
        else:
            #print "Silimare to previous stuff wrong"
            return False
        return False

    def parseLine(self,line):
        line += self.checkForMore(line,0)
        if line[0] == '(':
            line += self.checkForMore(line,1)
            if line[1] == 's':
                line += self.checkForMore(line,2)
                if line[2] == 'c':
                    line += self.checkForMore(line,6)
                    if line[2:6] == 'chat':
                        return self.doschat(line[6:])
                elif line[2] == 's':
                    line += self.checkForMore(line,6)
                    if line[2:6] == 'stat':
                        return self.dosstat(line[6:])
                elif line[2] == 'j':
                    line += self.checkForMore(line,6)
                    if line[2:6] == 'join':
                        #print "Found sjoin"
                        return self.dosjoin(line[6:])
                elif line[2] == 'n':
                    if line[2:8] == 'novac)':
                        #print "Found snovac"
                        return self.dosnovac(line[8:])
                elif line[2] == 't':
                    line += self.checkForMore(line,7)
                    if line[2:7] == 'trike':
                        #print "Found Strike"
                        return self.dostrike(line[7:])
                else:
                    #print "Parse: Malformed: Command no known: %s"%line
                    return False
            else:
                #print "Parse: Malformed: no begining s: %s"%(line)
                return False
        else:
            #print "Parse: Malformed: No starting (: %s" %line
            return False

    def cmdLoop(self):
        autoSendArr = []
        if self.man == False:
            autoSendArr = self.makeAutoArr()
            print "<ENTER> to start Auto Mode"
        while not self.flag:
            try:            #This is different in my program
                #Wait for input from stdin & socket
                if self.man:
                    sys.stdout.write('%s'%self.prompt)
                    sys.stdout.flush()
                inputready, outputready,exceptrdy = select.select([0, self.sock], [],[])
                for i in inputready:
                    if i ==0:
                        if self.man == False:
                            sleepy = random.randint(1,5)
                            time.sleep(sleepy)
                            data = random.choice(autoSendArr)
                            pl = self.players
                            #print 'Removed chatand name Data[10:] %s' %(data[10:])
                            name = self.randomPlayer()
                            data = "(cchat(" + name + data[10:]
                            #print 'Message to be sent: %s' %(data)
                        else:
                            data = sys.stdin.readline().strip()
                        if self.man:
                            print data
                        if data == 't':
                            data = '(cjoin(BILL))(cchat(all)(hello People on here))'
                        if data == "c":
                            data = '(cchat(all)(This is a test message.))'
                        if data == 's':
                            data = '(cstat)'
                        if data == 'j':
                            data = '(cjoin(BILLO))'
                        if data == 'q':
                            print 'Shutting down.'
                            self.flag = True
                            break
                        #print "Line to be Sent:",data
                        self.sock.send(data)
                    elif i == self.sock:
                        print ''
                        data = self.sock.recv(MAXRECV) #Fixed for chat but not sstat yet.
                        if not data:
                            print 'Shutting down.'
                            self.flag = True
                            break
                        else:
                            vplret = self.parseLine(data)
            except KeyboardInterrupt:
                print 'Interrupted.'
                self.sock.close()
                break
            except IOError, e:
                if e.errno == errno.EPIPE:
                    print "Server Disconnected"
                    self.sock.close()
                    sys.exit(1)
                else:
                    print "Other error received:", e.errno
                    self.sock.close()
                    sys.exit(1)
                break

if __name__ == '__main__':
    import sys
    p,h,d,m,a,name = 0,'',0,False,False,''
    skipNext = False
    numArgs = len(sys.argv)
    for x in range(1,numArgs):
        if (sys.argv[x] == '-h'):
            print "usage: server.py [options]"
            print "Options and arguments:"
            print "-a     : Run program in a A.I. mode when playing the game"
            print "-d num : Include a number for debugging"
            print "-g     : Launches a client GUI"
            print "-m     : Manual mode. User controls game and chat(auto mode is enabled by default)"
            print "-n str : Name of the user running the client used in chat and game"
            print "-p num : Port number of the server to connect to"
            print "-s str : Address of the server to connect to. Using either IP (127.0.0.1) or DNS name (cf416-00.cs.wwu.edu)"
            print "\n"
            sys.exit()
        if (sys.argv[x] == '-p'):
            #print "-p Getting Port Number"
            p = int(sys.argv[x+1])
            #print "-p: ",p
            skipNext = True
        elif (sys.argv[x] == '-s'):
            #print "-s Getting Server IP"
            h = sys.argv[x+1]
            #print "-s: ",h
            skipNext = True
        elif (sys.argv[x] == '-d'):
            #print "-d Getting Debugging number"
            d = int(sys.argv[x+1])
            #print "-d: ",d
            skipNext = True
        elif (sys.argv[x] == '-m'):
            #print "-m Manual Mode initiated"
            m = True
        elif (sys.argv[x] == '-a'):
            #print "-a AI Mode initiated"
            a = True
            #print "\tPlease note AI has not been initiated yet"
        elif (sys.argv[x] == '-n'):
            #print "-n Getting username"
            name = sys.argv[x+1]
            #name = "A#$%^57aZz0-9.+t=x\"t:1"
            #print "-n: ",name
            skipNext = True
        elif skipNext == False:
            print "Unknown argument: %s. Please use -h for help" %(sys.argv[x])
            #sys.exit()
        else:
            skipNext = False
    #print "Manual Mode:", m
    if name == '':
        name = raw_input("Please enter a username: ")
    if h == '':
        h = "127.0.0.1"
    if p == 0:
        p = 36716

    client = Client(name,d,m,a,h,p)
    client.cmdLoop()