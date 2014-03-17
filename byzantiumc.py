#Travis Eickmeyer
#DATE: 3/12/14
#CLASS: CSCI 367
#Project: Chat Server/Client
#File: byzantiumc.py
#Professor: Michael Meehan

import socket
import sys
import select
import random
import time
import errno

BUFSIZE = 240
MAXRECV = 512

class Client(object):

    def __init__(self,name,debug,man,ai,host,port):
        self.name = name.upper()
        self.flag = False
        self.port = int(port)
        self.host = host
        self.players = ''
        self.sendList = ()
        self.debug = debug
        self.man = man
        self.ai = ai
        self.playerTable = {}
        self.minplayers = 0
        self.lobbytimeout = 0
        self.actiontimeout = 0
        self.round = 0
        self.potentialAttackee = ''
        self.attackee = ''
        #Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host,self.port))
            #Send my name
            if self.ai == True:    # For those that wait
                time.sleep(500)
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
        plist = self.players.split(',')
        for p in plist:
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
        if len(self.sendList) > 0:
            sendTo = random.choice(self.sendList)
            #print "Player messgae is send To: ",sendTo
        else:
            sendTo = random.choice(['all','any'])
        return sendTo

    def updatePlayerTable(self):
        #need to make a player list that keep tracks of each players unit number allicances with me and betrals or not keeping his word 
        # betrayal is someone who i made an allicece to attack a person and they attack me 
        # A lier is someone who made and allicane and did not attack this person
        print "Neeed to actually update the table"


    '''def addPlayers(self):       #(units,currently Allied,times allied,Time betrayed,Time lied To)
        for i in self.players:
            if i not in self.playerTable:
                print "player not in player Table so add them"
                self.playerTable[i] = ()
    ''' 

    def handleGame(self,msg):
        parts = msg.split(',')
        phaseAction = parts[0]
        self.round = parts[1]
        print "Round recieved: %s"%self.round
        #use phaseAction to determin how many more 
        print "Action: %s"%phaseAction
        if phaseAction == "PLAN": #len is 2
            print "PHASE 1 begining send plan"
            if self.name == "EICKMET" or self.name == "HARVEY":
                self.potentialAttackee = "PETER" 
                data = '(cchat(SERVER)(PLAN,%s,APPROACH,KELLY,PETER))'%self.round
            else:
                data = '(cchat(SERVER)(PLAN,%s,PASS))'%self.round
            print "Message to be sent: %s"%data
            self.sock.send(data)
            #do phase 1 planing stuff
        elif phaseAction == "OFFERL":   #len is 2 or 4
            print "PHASE 2 begining send accept or decline to offer or nothing"
            if len(parts) == 2:
                print "NO OFFERS OF AN ALLICANCE" #meaning attack whom ever
            elif len(parts) == 4:
                print "AN OFFER IS HERE"
                ally = parts[2]
                attackee = parts[3]
                self.attackee = attackee
                print "Message: (cchat(SERVER)(ACCEPT,%s,%s))"%(self.round,ally)
                self.sock.send("(cchat(SERVER)(ACCEPT,%s,%s))"%(self.round,ally))
                print "AN OFFER OF ALLICANCE: From %s to attck %s" %(ally,attackee)
            else:
                print "BAD SERVER With offerl"
            #check to see what offer I recieved
            #check to see if allyoffer is to attack me but most likely accept all offer especially if two or more offers is to attack the same person
            #do pahse 2 accept or decline stuff here
        elif phaseAction == "ACCEPT":   #len is 3
            ally = parts[2]
            print "PHASE 2 player: %s has accepted the allicence"%ally
            #Accepting stuff here
        elif phaseAction == "DECLINE": # len is 3
            ally = parts[2]
            print "PHASE 2 player: %s has Declined the allicence"%ally
            #declining stuff here
        elif phaseAction == "ACTION":   # len is 2
            print "potAtt: |%s| and Att: |%s|"%(self.potentialAttackee,self.attackee)
            print "PHASE 3 begining tell final plan"
            if self.attackee != '':
                if self.potentialAttackee == self.attackee:
                    line = "(cchat(SERVER)(ACTION,%s,ATTACK,%s))"%(self.round,self.attackee)
                elif self.potentialAttackee == '':
                    print "2"
                    line = "(cchat(SERVER)(ACTION,%s,ATTACK,%s))"%(self.round,self.attackee)
                else:
                    print "3"
                    personToAttack = random.choice([self.attackee,self.potentialAttackee])
                    line = "(cchat(SERVER)(ACTION,%s,ATTACK,%s))"%(self.round,personToAttack)
            elif self.potentialAttackee != '':
                line = "(cchat(SERVER)(ACTION,%s,ATTACK,%s))"%(self.round,self.potentialAttackee)
            else:
                rawr = random.randint(1,5)
                if rawr == 1:   #attack lowest units
                    pers=random.choice(self.players.split(','))
                    print "Random person attacking is: %s"%pers
                    line = "(cchat(SERVER)(ACTION,%s,ATTACK,%s))"%(self.round,pers)
                else:
                    line = "(cchat(SERVER)(ACTION,%s,PASS))"%(self.round)
            print "Attack message: %s"%line
            self.sock.send(line)
            #Send who to attack or pass send len 3 or 4
        elif phaseAction == "NOTIFY": # len is 4
            self.attackee = ''
            self.potentialAttackee = ''
            attacker = parts[2]
            attackee = parts[3]
            print "%s has attacked %s"%(attacker,attackee)
            print "Phase 3 ended here are the results"
            #handle nofity messages
        else:
            print "SERVER sent a bad message: |%s|"%msg

    def checkForMore(self,line,i):
        if i >= len(line):
            print "Recved more&*******************************"
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
                self.players = players
                self.sendList = players.split(',')
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
        print "chat"
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
                    print "From",pfrom
                    if pfrom == "SERVER":
                        self.handleGame(msg)
                    self.displayMessage(pfrom,msg)
                    if len(line) > 0:       #more stuff in data
                        self.parseLine(line)
                    else:
                        return True
                else:
                    print "S1trike Malformed missing ending )"
                    #print "Line:", line
                    return False
            else:
                print "2Strike Malformed missing ending )"
                #print "Line:", line
                return False

        else:
            print "3Strike Malformed missing ending )"
            #print "Line:", line
            return False
        return True

    def dosjoin(self, line):    #NOTE handle the name,units stuff.
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
        self.players = players
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
                    sys.exit()
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
        print "Parse"
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
        while not self.flag:
            try:            #This is different in my program
                #Wait for input from stdin & socket
                if self.man:
                    sys.stdout.write('%s'%self.prompt)
                    sys.stdout.flush()
                    inputready, outputready,exceptrdy = select.select([0, self.sock], [],[])
                else:
                    sleepy = random.randint(1,5)
                    inputready, outputready,exceptrdy = select.select([0, self.sock], [],[],sleepy)
                if (not inputready or outputready or exceptrdy) and (self.man == False):
                    data = random.choice(autoSendArr)
                    pl = self.players
                    #print 'Removed chatand name Data[10:] %s' %(data[10:])
                    name = self.randomPlayer()
                    data = "(cchat(" + name + data[10:]
                    self.sock.send(data)
                else:
                    for i in inputready:
                        if i ==0:
                            data = sys.stdin.readline().strip()
                            print data
                            if data == 't':
                                data = '(cjoin(BILL))(cchat(all)(hello People on here))'
                            if data == "pp":
                                data = '(cchat(SERVER)(PLAN,%s,PASS))'%self.round
                            if data == "pa":
                                data = '(cchat(SERVER)(PLAN,%s,APPROACH,KELLY,PETER))'%self.round
                            if data == "a":
                                data = '(cchat(SERVER)(ACCEPT,%s,JOEY))'%self.round
                            if data == "d":
                                data = '(cchat(SERVER)(DECLINE,%s,FRANK))'%self.round
                            if data == "ap":
                                data = '(cchat(SERVER)(ACTION,%s,PASS))'%self.round
                            if data == "aa":
                                data = '(cchat(SERVER)(ACTION,%s,ATTACK,PETER))'%self.round
                            if data == 's':
                                data = '(cstat)'
                            if data == 'j':
                                data = '(cjoin(BILLO))'
                            if data == 'q':
                                print 'Shutting down.'
                                self.flag = True
                                break
                            print "Line to be Sent:",data
                            self.sock.send(data)
                        elif i == self.sock:
                            if self.man:
                                print ''   #off for auto mode 
                            data = self.sock.recv(MAXRECV) #Fixed for chat but not sstat yet.
                            if not data:
                                print 'Shutting down.'
                                self.flag = True
                                break
                            else:
                                print "Message received: %s" %data
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