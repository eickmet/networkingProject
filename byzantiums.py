#Travis Eickmeyer
#DATE: 3/18/14
#CLASS: CSCI 367
#Project: Chat Server/Client
#File: byzantiums.py
#Professor: Michael Meehan

import select
import socket
import sys
import signal
import random
import time

BUFSIZE = 480      #Change to reflect the current BUFSIZE
MAXPLAYERS = 30     #Max number of player in the server
MAXINT = 99999
#TODO: add Alive section to clientTable True False inorder to limit player who be allys or attacked
#TODO: Add message section to clientTable to hold onto messages that where created during the previous phase

class Server(object):

    def __init__(self,timeout,lobby,player,force=1000,port=36716):
        self.timestarted = time.time()
        self.playGame = True
        self.force = int(force)
        self.timeout = int(timeout)
        self.lobbyTimeout = int(lobby)
        self.minPlayers = int(player)
        self.argString = "%s,%s,%s"%(self.minPlayers,self.lobbyTimeout,self.timeout)
        self.clients = 0
        self.msgsRecv = 0
        self.msgBad = 0
        self.msgsSent = 0
        self.clientTable = {}
        self.outputs = []
        self.inputready =  []
        self.outputready = []
        self.inputs = []
        self.round = 0
        self.phase = 0
        self.phaseRespond = {}
        self.allyTable = []
        self.playerTable = {}
        self.newPlayer = []
        self.battleMatrix = [[0 for x in xrange(40) ] for x in xrange(40)]
        self.phaseTime = 0
        self.playingGame = False
        self.notWaiting = True
        self.lobbyWait = 0
        self.toKill = False
        self.foundWinner = ''
        self.winner = False
        self.oneResponse = False
        self.alivePlayers = {}
        self.nameNum  = {}
        self.ni = 0
        self.sentOffers = 0
        self.recvOffers = 0
        self.attackList = []
        self.attackTable = {}
        self.defendTable = {}
        self.engagedTable = {}
        self.defeated = {}
        self.removeList = {}
        self.equalRolls = 0
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tempTroopTable = {}
        try:
            self.server.bind(('',port))
        except socket.error, e:
            print "This port: %d is still active. Please wait a few moments before trying again."%port
            self.server.close()
            time.sleep(2)   #Wait for a bit
            sys.exit()
        self.server.listen(1)
        host = socket.gethostbyname(socket.gethostname())
        if self.playGame == False:
            print "Chat Server only No Game to be played"
        print "Maximum number of player on server is %d" %(MAXPLAYERS)
        print "Lobby Wait time - %d\nMinimum players - %d\nAction Timeout - %d" %(self.lobbyTimeout,self.minPlayers,self.timeout)
        print "Type \'h\' or \'help\' for a list of built in commands."
        print 'Address: %s Listening to port: %d ...'%(host,port)
        #Trap keyboard interrupts
        signal.signal(signal.SIGINT,self.sig_handler)

    def sig_handler(self,signum,frame):
        print '\nShutting down server...'
        for o in self.outputs:
            o.close()
        self.server.close()

    def printHelp(self):
        print "**********************************************************"
        print "* Available Help Commands For When the Server is Running *"
        print "**********************************************************"
        print "\'a\' - Displays the values of the arguments passed in when starting the server."
        print "\'c\' - Displays a list of players along with their addresses, port number, and strikes."
        print "\'h\' - Displays this help section."
        print "\'m\' - This Displays the number of messages sent and received by the server."
        print "\'p\' - Number of players on the server."
        print "\'q\' - Exits/quits from the server and closes all connected sockets."
        print "\'s\' - Displays a table with each players name and their strikes."
        print "\'t\' - Displays the elapsed time the server has been running for."
        print "********************************************************************"

    def printArguments(self):
        print "Minimum players: %d" %(self.minPlayers)
        print "Lobby timeout:   %d" %(self.lobbyTimeout)
        print "Action Time out: %d" %(self.timeout)

    def getName(self, client):
        info = self.clientTable[client]
        host,name = info[0][0], info[1]
        return name

    def getJoined(self,client):
        info = self.clientTable[client]
        return info[4]

    def getUnits(self,client):
        info = self.clientTable[client]
        return info[3]

    def searchNames(self, name):
        if name == "##":
            return True #3Meaning fo not send to client
        for c in self.clientTable:
            p = self.getName(c)
            if name == p:
                return False
        return True

    def getConn(self,name):
        for c in self.clientTable:
            p = self.getName(c)
            if name == p:
                return c
        return False

    def getWins(self,conn):
        info = self.clientTable[conn]
        return info[7]

    def getTime(self):
        curTime = time.time()
        diff = curTime - self.timestarted
        sec = diff % 60
        min =   (diff/60) % 60
        hours = (diff/60/60) % 60
        print "Time elapsed: %d hours  %d mins  %d secs" %(hours,min,sec)

    def getPlayers(self):
        playerList = ''
        for i in self.clientTable:
            if self.getName(i) != '##':
                p = self.getName(i)
                playerList += (p  +',')
        playerList = playerList[:-1]
        return playerList       #Creates a string of players currently on the server

    def getPlayersPlus(self):
        playerList = ''
        for i in self.alivePlayers:
            if self.getName(i) != '##':
                p = self.getName(i)
                u = self.getUnits(i)
                s = self.getStrikes(i)
                #playerList += (p + ','+ s + ',' + u + ',')
                playerList += "%s,%d,%d,"%(p,s,u)
        playerList = playerList[:-1]
        return playerList       #Creates a string of players currently on the server

    def printStrikes(self):
        for i in self.clientTable:
            s = self.getStrikes(i)
            n = self.getName(i)
            print "%12s- %s" %(n,s)

    def printNumMsg(self):
        print "Number of Messages Received: %d" %(self.msgsRecv)
        print "Number of Messages Sent: %d" %(self.msgsSent)
        print "Number of Bad Messages Almost Send: %d" %(self.msgBad)

    def printClientTable(self):
        print "|     Name      ||     Address     ||  Port  || Strike || Units || Join || SentTo || RcvFrm || Won   |"
        print "******************************************************************************************************"
        for i in self.clientTable:
            c = self.clientTable[i]
            host,name,strikes,units,offical,send,recv,numwins = c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7]
            ip,port = host[0],host[1]
            if offical:
                offical = "True"
            else:
                offical = "False"
            print "| {:<14}:: {:^15} :: {:^6} :: {:^6} :: {:^5} :: {:^5}::  {:^5} ::  {:^5} :: {:^5} |".format(name,ip,port,strikes,units,offical,send,recv,numwins)
            #          name    add      port     strkes   units     joined   sento  recvfrom
        print "%d players on the server" %(self.clients)

    def getStrikes(self,conn):
        info = self.clientTable[conn]
        strikes = info[2]
        int(strikes)
        return strikes

    def sendStrike(self,conn,reason,comment):
        try:
            snum = self.getStrikes(conn)
            snum += 1
            a,b,c,u,f,s,r,w = self.clientTable[conn]  #address, name , strikes,units,flags
            self.clientTable[conn] = (a,b,snum,u,f,s,r,w)
        except LookupError, e:
            print "Strikes Loop up error:",conn,reason,comment
            snum = 1
        strike = "(strike(%d)(%s))" % (snum,reason)
        self.sending(conn,strike)
        print "%s has received a %s strike Number %d: Comment: %s"%(self.getName(conn),reason,snum,comment)
        if snum >= 3:
            if snum >=3:
                self.clients -=1
                conn.close()
                self.inputs.remove(conn)
                self.outputs.remove(conn)
                ename = self.getName(conn)
                self.removeClient(conn)
                self.sendallstat(True)
                print "Disconnecting Client"
                self.toKill = False
                print 'Kick: %s has been kicked from the chat server.' %(ename)
            else:
                self.toKill = True
                print "Disconnecting Client"

    def removeClient(self,conn):
        if conn in self.alivePlayers:
            del self.alivePlayers[conn]
        if conn in self.playerTable:
            del self.playerTable[conn]
        if conn in self.phaseRespond:
            self.phaseRespond[conn] = (True,'')
            self.removeList[conn] = True
            #del self.phaseRespond[conn]
        del self.clientTable[conn]
        conn.close()

    def validateJoinName(self,name,s):
        if name == '':
            print "No name given"
            name = "DEFAULT"
            self.sendStrike(s,'malformed',"ValidjName: No name given")
        if name.lower() == 'all':
            print "Reserved Name: all"
            name = "DEFAULT"
            self.sendStrike(s,'malformed',"ValidjName: Reserved Name Given: all")
        if name.lower() == 'any':
            print "Reserved Name: any"
            name = "DEFAULT"
            self.sendStrike(s,'malformed',"ValidjName: Reserved Name Given: any")
        if name.upper() == "SERVER":     #For phase 2
            print "Reserved Name: any"
            name = "DEFAULT"
            self.sendStrike(s,'malformed',"ValidjName: Reserved Name Given: SERVER")
        name = name.upper()
        dos = name.split('.',1)
        end = ''
        if len(dos) > 1:
            if len(dos[1]) > 3:
                dos[1] = dos[1][0:3] #should keep it 3 or less
            end = '.' + dos[1]
        pre = dos[0][:7] #CHANGED  THIS FROM 6 to 7
        name = pre + end
        name = self.dosname(pre,'',end,0)
        print "[%s] - joined"%(name)
        return name

    def dosname(self,name,mid,end,x):
        if self.searchNames(name+mid+end) == False: #This name does exist
            x+=1
            mid = "~"+str(x)
            if x > 9:
                name = name[:5]
            return self.dosname(name,mid,end,x)
        else:
            return name+mid+end

    def allsend(self,msg,s):
        sendmsg = '(schat(%s)(%s))' %(self.getName(s),msg)
        for c in self.clientTable:
            #if s != c: #This is to not send to themselves option
            if self.getName(c) != '##':
                self.sending(c,sendmsg)

    def ServerAllSend(self,msg):
        for i in self.clientTable:
            if self.getName(i) != '##':
                self.sending(i,msg)

    def ServerGameAllSend(self,msg):
        for i in self.alivePlayers:
            if self.getName(i) != '##':
                self.sending(i,msg)

    def anysend(self,msg,s):        #Change anysend to avoid unofficalPlayers but make sure it is not in a infinte loop
        sender = '(schat(%s)(%s))' %(self.getName(s),msg)
        per =random.choice(self.clientTable.keys())
        self.sending(per,sender)

    def sending(self,s,msg):
        #print "Message to be sent: %s"%msg
        try:
            self.msgsSent +=1
            #self.addSend(s)
            s.send(msg)
        except socket.error, e:
            self.msgBad += 1

    def sendallstat(self,boo):
        statmsg = '(sstat(%s))' %(self.getPlayersPlus())
        if self.playingGame:
            for c in self.alivePlayers:
                if self.getName(c) != '##':
                    self.msgsSent += 1
                    self.sending(c,statmsg)
        else:
            for c in self.clientTable:
                if self.getName(c) != '##':
                    self.msgsSent += 1
                    self.sending(c,statmsg)


    def zeroBattleTable(self):
        for i in range(0,30):
            for j in range(0,30):
                self.battleMatrix[i][j] = 0

    def proccessPhase1Message(self,s,name,msg):
        #print "Recv Round %d Phase 1 Messages"%self.round
        #Check if message contains (PLAN,R#,PASS) or (PLAN,R#,APPROACH,ALLY,ATTACKEE)
        #                               Round number PASS       APPROACH who to ally and who to attack
        #print "Phase 1 message: %s"%msg
        args = msg.split(',')
        phase = ''
        rnd = 0
        #print "Phase 1: Message recv:",msg
        if len(args) == 3:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            if phase != "PLAN":
                self.sendStrike(s,"malformed","Phase 1: Did not give PLAN phase gave:%s"%(phase))
                #print "Assuming Player passes or see if they send again"
                return False
            if action != "PASS":
                self.sendStrike(s,"malformed","Phase 1: Did not give PASS gave:%s"%(action))
                #print "Assuming Player passes or see if they send again"
                return False
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 1: Not the correct Round Number:%d"%(rnd))
                #print "Assuming Player passes or see if they send again"
                return False
            #print "Player does not wish to make an allicance"
            self.phaseRespond[s] = (True,"WAIT")
            self.playerTable[s] = True
            #check off the player has responeded so they can not send another phase 1 msg
        elif len(args) == 5:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            ally = args[3]
            attackee = args[4]
            if phase != "PLAN":
                self.sendStrike(s,"malformed","Phase 1: Did not give PLAN phase gave:%s"%(phase))
                #print "Assuming Player passes or see if they send again"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            if action != "APPROACH":
                self.sendStrike(s,"malformed","Phase 1: Did not give PASS gave:%s"%(action))
                #print "Assuming Player passes or see if they send again"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 1: Not the correct Round Number:%d"%(rnd))
                #print "Assuming Player passes or see if they send again"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            if self.getConn(ally) not in self.alivePlayers:
                #print ally,"not a valid ally"
                self.sendStrike(s,"malformed","Phase 1: Did not give valid ally name gave:%s"%(ally))
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return True
            if self.getConn(attackee) not in self.alivePlayers:
                #print attackee,"not a valid attackee"
                self.sendStrike(s,"malformed","Phase 1: Did not give valid attackee name gave:%s"%(attackee))
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return True
            #Check if ally exist else send strike
            #check if attackee exist else send strike
            #Need to save phase 1 message somewhere to be sent in phase 2
            #make sure ally is not himself or attacking himself Might just allow it for the stupid people
            sec = "ALLY WITH %s TO ATTACK %s" %(ally,attackee)
            self.phaseRespond[s] = (True,sec)
            sendTo = self.getConn(ally)
            allyToBe = self.getName(s)
            self.playerTable[s] = True
            phase2msg = "(schat(SERVER)(OFFERL,%s,%s,%s))"%(self.round,allyToBe,attackee)
            self.allyTable.append((sendTo,phase2msg))
            #print "P1 AP: Send:%s TO:%s FROM:%s" %(phase2msg,ally,allyToBe)
            #self.sending(sendTo,phase2msg) Might add to clientTable for message part
            #msg = (schat(SERVER)(OFFERL,R#,ALLY,ATTACKEE))
            #ally is
            return True
        else:
            self.sendStrike(s,"malformed","Phase 1: Not the Correct number of Arguments:%d"%(len(args)))
            #print "Assuming Player passes or see if they send again"
            return False
        return True

    def proccessPhase2Message(self,s,name,msg):
        #print "Recv Round %d Phase 2 Messages"%self.round
        #Already sent off messages to people
        #print "Phase 1 message: %s"%msg
        #print "Number of sent offers sent: %d"%self.sentOffers
        args = msg.split(',')
        if len(args) == 3:
            decision = args[0]
            rnd = int(args[1])
            ally = args[2]
            if rnd != self.round:
                self.sendStrike(s,"malformed %s"%msg,"Phase 2: Not the correct Round Number:%d"%(rnd))
                #print "Bad Round number sent"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            if self.getConn(ally) not in self.alivePlayers:
                #print ally,"not a valid ally"
                self.sendStrike(s,"malformed","Phase 2: Did not give valid ally name gave:%s"%(ally))
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return True
            #check i ally is good. and has sent current client a ally message
            ######What happens if client accepts or rejects a an ally that they did not receive a ally message from or something.
            if decision == "ACCEPT":
                self.recvOffers +=1
                #inform origonal client of action
                self.phaseRespond[s] = (True,"ACCEPT")
                #print "%s Accepted allyship from ally:%s" %(self.getName(s),ally)
                line = "(schat(SERVER)(ACCEPT,%s,%s))"%(self.round,self.getName(s))
                self.phaseRespond[s] = (True,"DECLINE")
                self.sending(self.getConn(ally),line)
            elif decision == "DECLINE":
                self.recvOffers +=1
                self.phaseRespond[s] = (True,'DECLINE')
                #inform origonal client of action
                #print "%s Rejected allyship from ally:%s" %(self.getName(s),ally)
            else:
                print "did not send accept or reject"
        else:
            self.sendStrike(s,"malformed","Phase 2: Not the Correct number of Arguments:%d,MSG is %s"%(len(args),msg))
            #print "Assuming Player passes or see if they send again"
            return False
        return True

    def proccessPhase3Message(self,s,name,msg):
        #print "Recv Round %d Phase 3 Messages"%self.round
        #This is the real phase what ever happens here is there real answer
        #print "Phase 3 message: %s"%msg
        args = msg.split(',')
        phase = ''
        rnd = 0
        if len(args) == 3:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            if phase != "ACTION":
                self.sendStrike(s,"malformed","Phase 3: Did not give ACTION phase gave:%s"%(phase))
                #print "Assuming Player passes or see if they send again"
                return False
            if action != "PASS":
                self.sendStrike(s,"malformed","Phase 3: Did not give PASS gave:%s"%(action))
                #print "Assuming Player passes or see if they send again"
                return False
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 3: Not the correct Round Number:%d"%(rnd))
                #print "Assuming Player passes or see if they send again"
                return False
            #print "Player does not wish attack this turn"
            self.phaseRespond[s] = (True,"ACTION PASS")
            #Set zero in all rows of his table
        elif len(args) == 4:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            attackee = args[3]
            if phase != "ACTION":
                self.sendStrike(s,"malformed","Phase 3: Did not give ACTION phase gave:%s"%(phase))
                #print "Assuming Player passes or see if they send again"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 3: Not the correct Round Number:%d"%(rnd))
                #print "Assuming Player passes or see if they send again"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            if action != "ATTACK":
                self.sendStrike(s,"malformed","Phase 3: Did not give ATTACK gave:%s"%(action))
                #print "Assuming Player passes or see if they send again"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            #check if attackee exits
            if self.getConn(attackee) not in self.alivePlayers:
                #print attackee,"not a valid attackee"
                self.sendStrike(s,"malformed","Phase 3: Did not give valid attackee gave:%s"%(attackee))
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            attacker = self.getName(s)
            #print attacker,attackee
            if attackee == attacker:
                #print "Attacking self to take advantege of server",attackee,"==",attacker
                self.sendStrike(s,"malformed","Phase 3: Trying to attack themselve")
                #print "Passing this round"
                #self.phaseRespond[s] = (True,"ACTION PASS")
                return False
            #And Then add the appropriate 1 in the battleMatrix
            #print "%s will Attack %s"%(attacker,attackee)
            self.phaseRespond[s] = (True,"ACTION ATTACK %s"%attackee)
            line = "(schat(SERVER)(NOTIFY,%s,%s,%s))"%(self.round,attacker,attackee)
            self.attackList.append(line)
            i = self.nameNum[attacker]
            j = self.nameNum[attackee]
            #print "i: %d and j: %d"%(i,j)
            self.battleMatrix[i][j] = 1
            return True
        else:
            self.sendStrike(s,"malformed","Phase 3: Not the Correct number of Arguments:%d"%(len(args)))
            #print "Assuming Player passes or see if they send again"
            return False
        return True

    def clearRespond(self):
        for i in self.phaseRespond:
            self.phaseRespond[i] = (False,'')


    def printRespond(self):
        for i in self.phaseRespond:
            info = self.phaseRespond[i]
            #print "stuff",info

    def sendPhase1(self):
        msg = "(schat(SERVER)(PLAN,%s))"%(self.round)
        #print "Sent Out Round %d Phase 1 Messages"%self.round
        self.ServerGameAllSend(msg)

    def sendPhase2(self): # for those who do not send a message in time they could not recieve a message with this current method
        #send (schat(SERVER)(OFFERL,R#,ALLY,ATTACKEE)) can have more than one offer Need to figure out a way to store this for each player
        #or
        #Send (schat)(SERVER)(OFFERL,R#)) if no offers easy to send
        #print "Sent out Round %d Phase 2 Messages"%self.round
        self.clearRespond()
        for i in self.allyTable:
            s = i[0]
            if s in self.clientTable:

                self.playerTable[s] = False
                msg = i[1]
                #print msg
                self.sentOffers +=1
                self.sending(s,msg)
                #print "Phase 2:[%s] Got alliance message"%self.getName(s)
            #else:
                #print "Player has been kicked recently got an alliance"
        self.allyTable = []
        msg = "(schat(SERVER)(OFFERL,%d))"%self.round
        for i in self.playerTable:
            if self.playerTable[i]:
                if i in self.clientTable:   
                    #print "Phase 2 no offer msg",self.getName(i),self.playerTable[i]
                    self.phaseRespond[i] = (True,'')
                    #print "Phase 2:[%s] Got no offers"%(self.getName(i))    # Expect no response from these people
                    self.sending(i,msg)
                #else:
                    #print "PLayer who has been kicked received no offers"
        #print "ptable len",len(self.playerTable)    
        self.playerTable = {}

    def sendPhase3(self):       #(schat(SERVER)(ACTION,R#))
        #print "Sent out Round %d Phase 3 Messages"%self.round
        self.clearRespond()
        msg = "(schat(SERVER)(ACTION,%s))"%(self.round)
        #print "Sent Out Phase 3 Messages"
        self.ServerGameAllSend(msg)

    def sendNotify(self):       #(schat(SERVER)(NOTIFY,R#,ATTACKER,ATTACKEE))
        #print "Sent out Round %d Phase Nofity Messages"%self.round
        self.clearRespond()
        for i in self.attackList:
            #print "notify line: %s"%i
            self.ServerGameAllSend(i)
        #for i in self.phaseRespond:
        #    self.phaseRespond[i] = (True,'')
        self.attackList = []

    def sendChatMessage(self,names,msg,s):
        nameNoExist = False
        if len(msg) > 80:
            msg = msg[0:80]
        fromWhom = self.getName(s)
        playerList = names.split(',')
        for p in playerList:
            p = p.upper()
            if self.searchNames(p) == False:
                sendmsg = '(schat(%s)(%s))' %(fromWhom,msg)
                conn = self.getConn(p)
                self.sending(conn,sendmsg)
            elif p == 'ANY':
                self.anysend(msg,s)
            elif p == 'ALL':
                self.allsend(msg,s)
            else:
                nameNoExist = True
        #if nameNoExist == True:
            #print "Name does not here"
            #self.sendStrike(s,"malformed","sendChatmsg: Bad name")

    def addRecv(self,s):
        try:
            a,b,c,d,e,f,g,h = self.clientTable[s]
            g+=1
            self.clientTable[s] = (a,b,c,d,e,f,g,h)
        except KeyError,e:
            print "Bad send"

    def addSend(self,s):
        try:
            a,b,c,d,e,f,g,h = self.clientTable[s]
            f+=1
            self.clientTable[s] = (a,b,c,d,e,f,g,h)
        except KeyError,e:
            print "Bad send"

    def checkAllRespond(self):
        for i in self.phaseRespond:     #This looks to be very ineffiecient but I don't care
            info = self.phaseRespond[i]
            #print info
            resp = info[0]
            if resp == False:
                return False
        return True

    #def printEngagedTable(self):
        #for i in self.engagedTable:
            #print i,"has %d engagments"%self.engagedTable[i]

    def printBTable(self):
        colLine = '      '
        for i in self.nameNum:
            if self.getConn(i) in self.alivePlayers:
                colLine += "[%s] " %i[:3]
        print colLine
        for i in self.nameNum:
            if self.getConn(i) in self.alivePlayers:
                row = '[%s]'%i[:3]
                for j in self.nameNum:
                    if self.getConn(j) in self.alivePlayers:
                        ii = self.nameNum[i]
                        jj = self.nameNum[j]
                        row += " |{:^3d}|".format(self.battleMatrix[ii][jj])
                print row

    def printMatrix(self):
        header = '     '
        spacer = '****'
        print "Row sum is either 1 or 0"
        print "Column sum can be 0 to %d"%self.clients
        print "Row attacks Column"
        for i in range(0,self.clients):
            header += ' |%2d|'%i
            spacer += '*****'
        print header +" Attackees"
        print spacer
        for i in range(0,self.ni):
            row = '|%2d|*'%i
            for j in range(0,self.ni):
                row += " |%2d|"%self.battleMatrix[i][j]
            print row
        print "  ^"
        print "Attackers"

    def printNameNum(self):
        line = ''
        print "Key for Battle Matrix"
        for i in self.nameNum:
            j = self.nameNum[i]
            line += "[%s=%d] "%(i,j)
        print line

    def printalive(self):
        for i in self.alivePlayers:
            print self.getName(i),self.alivePlayers[i]


    def battle(self):
        print "**********************"
        print "*ROUND: %5s*"%self.round
        print "**********************"
        #self.printNameNum()
        arr = []
        #get the engaged number for each player
        for i in self.nameNum:         #Replace self.client with number alive
            self.tempTroopTable[i] = 0
            colSum = 0
            rowSum = 0
            totEngage = 0
            arr = []
            arr2 =[]
            for j in self.nameNum:
                num =  self.battleMatrix[self.nameNum[j]][self.nameNum[i]]
                num2 = self.battleMatrix[self.nameNum[i]][self.nameNum[j]]
                if num == 1:
                    colSum += num
                    #totEngage +=
                    arr.append(j)
                if num2 == 1:
                    rowSum += num2
                    arr2.append(j)
            self.attackTable[i] = arr2
            self.defendTable[i] = arr
            totEngage = rowSum + colSum
            self.engagedTable[i] = totEngage
            #print "{:<12s} has {:2d} engagments(A)".format(i,rowSum)
            #print "{:<12s} has {:2d} engagments(d)".format(i,colSum)
        #once have sum check if both attacking each other
        #self.printBTable()
        #for i in self.defendTable:
            #print i,"defend",self.defendTable[i]
        for i in self.attackTable:
            for j in self.attackTable:
                if i in self.attackTable[j]:
                    if j in self.attackTable[i]:
                        #print "found",i,"and then ",j
                        self.engagedTable[i] -= 1
            #print i,"attack",self.attackTable[i]
        #for i in self.engagedTable:
            #print i,"has",self.engagedTable[i],"engagments total"
        for i in self.attackTable:
            for j in self.attackTable:
                if i in self.attackTable[j]:
                    if j in self.attackTable[i]:
                        #print "Duel Battle",i,j
                        print "{:<14}  Duals  {:>14}".format(i,j)
                        self.duelBattle(i,j)
                        self.attackTable[j].remove(i)
                        self.attackTable[i].remove(j)
                    else:
                        print "{:<14} Attacks {:>14}".format(j,i)
                        self.normalBattle(i,j)
        #update troop info
        for g in self.defeated:
            units = self.tempTroopTable[g]
            #print "deafeated",g,units
            if units == 0:
                print "[DEFEATED] -",g
                for zzz in self.defendTable[g]:
                    #print zzz,"Gets troops"
                    self.tempTroopTable[zzz] += self.force
                conna = self.getConn(g)
                del self.alivePlayers[conna]
                del self.phaseRespond[conna]
                a,b,c,d,e,f,g,h = self.clientTable[conna]
                del self.clientTable[conna]
                self.clientTable[conna] = (a,b,c,0,e,f,g,h)
        for i in self.clientTable:
            a,b,c,d,e,f,g,h = self.clientTable[i]
            r = self.tempTroopTable[b]
            #check if b is not dead
            if r == 0:
                r = d
            if r > 99999:
                r = 99999
            self.clientTable[i] = (a,b,c,r,e,f,g,h)
        for i in self.clientTable:
            info = self.clientTable[i]
            name = info[1]
            units = info[3]
            #print name,"has",units,"units left"
        self.tempTroopTable = {}
        self.attackTable = {}
        self.defendTable = {}
        self.engagedTable ={}
        if len(self.alivePlayers) == 1:
            #print "We have a winner"
            for i in self.alivePlayers:
                self.winner = True
                self.foundWinner = self.alivePlayers[i]
                #print self.alivePlayers[i],"Wins the battle"
        #else:
            #for i in self.alivePlayers:
                #print "Still alive",self.alivePlayers[i],"With", self.getUnits(i)
        self.defeated ={}


    def duelBattle(self,attA,attB):
        if self.getConn(attA) not in self.alivePlayers:
            return True
        if self.getConn(attB) not in self.alivePlayers:
            return True
        unitsA = self.getUnits(self.getConn(attA))
        engagA = self.engagedTable[attA]
        unitsB = self.getUnits(self.getConn(attB))
        engagB = self.engagedTable[attB]
        batUnitsA = unitsA/engagA
        batUnitsB = unitsB/engagB
        if batUnitsA <= 10 or batUnitsB <= 10:
            #print "Before DeathAA",attA,batUnitsA,attB,batUnitsB
            batUnitsA,batUnitsB = self.duelDeathBattle(batUnitsA,batUnitsB) #may have to pass battle units not total units
            #print "After DeathAA",attA,batUnitsA,attB,batUnitsB
            if batUnitsA == 0:
                #print attB,"Aduel Defeats",attA
                self.defeated[attA] = True
                self.tempTroopTable[attB] += batUnitsB
            else:
                #print attA,"Bduel Defeats",attB
                self.defeated[attB] = True
                self.tempTroopTable[attA] += batUnitsA
            return True
        halfA = batUnitsA/2
        halfB = batUnitsB/2
        while (batUnitsA>halfA) and (batUnitsB>halfB):
            batUnitsA,batUnitsB = self.duelAttackRoll(batUnitsA,batUnitsB,False)
        self.tempTroopTable[attA] += batUnitsA
        self.tempTroopTable[attB] += batUnitsB
        #need to put results in a temp table then after all battles update clientTable units

        #Get the number of troop they should both have
        #repeat unitl one has half the troops they statrted with.

    def duelDeathBattle(self,aa,bb):
        a = aa
        b = bb
        #print "Inside duelDeathBattle",a ,b
        while a > 0 and b > 0:
            a,b = self.duelAttackRoll(a,b,True)
        #print "A numbers",a,"B numbers",b
        return a,b


    def duelAttackRoll(self,a,b,c):
        aRolls = []
        bRolls = []
        aRolls.append(random.randint(1,1000)%11)
        bRolls.append(random.randint(1,1000)%11)
        bRolls.append(random.randint(1,1000)%11)
        aRolls.append(random.randint(1,1000)%11)
        aRolls.append(random.randint(1,1000)%11)
        bRolls.append(random.randint(1,1000)%11)
        aRolls.sort()
        aRolls.reverse()
        bRolls.sort()
        bRolls.reverse()
        #print "A Rolled is:",aRolls
        #print "B Rolled is:",bRolls
        if aRolls[0] == bRolls[0]:
            self.equalRolls += 1
            #print "Nothing happens00"
        elif aRolls[0] > bRolls[0]:
            b -= 1
        else:
            a -= 1
        if c:
            if a == 0 or b == 0:
                return a,b
        if aRolls[1] == bRolls[1]:
            self.equalRolls += 1
            #print "Nothing happens11"
        elif aRolls[1] > bRolls[1]:
            b -= 1
        else:
            a -= 1
        if c:
            if a == 0 or b == 0:
                return a,b
        if aRolls[2] == bRolls[2]:
            self.equalRolls += 1
            #print "Nothing happens2"
        elif aRolls[2] > bRolls[2]:
            b -= 1
        else:
            a -= 1
        #print 'A ends with',a
        #print 'B ends with',b
        return a,b

    def normalBattle(self,att,defe):
        if self.getConn(att) not in self.alivePlayers:
            return True
        if self.getConn(defe) not in self.alivePlayers:
            return True
        unitsA = self.getUnits(self.getConn(att))
        engagA = self.engagedTable[att]
        unitsB = self.getUnits(self.getConn(defe))
        engagB = self.engagedTable[defe]
        batUnitsA = unitsA/engagA
        batUnitsB = unitsB/engagB
        if batUnitsA <= 10 or batUnitsB <= 10:
            #print "Before DeathAD",att,batUnitsA,defe,batUnitsB
            batUnitsA,batUnitsB = self.deathBattle(batUnitsA,batUnitsB)      # where one of the parties has 10 or less and one is attacking
            #print "After DeathAD",att,batUnitsA,defe,batUnitsB
            if batUnitsA == 0:
                #print defe,"Defeats",att
                #check if defeated
                self.defeated[att] = True
                self.tempTroopTable[defe] += batUnitsB
            else:
                #print att,"Defeats",defe
                self.defeated[defe] = True
                self.tempTroopTable[att] += batUnitsA
            return True
        halfA = batUnitsA/2
        halfB = batUnitsB/2
        while (batUnitsA>halfA) and (batUnitsB>halfB):
            batUnitsA,batUnitsB = self.rollDice(batUnitsA,batUnitsB,False)
        self.tempTroopTable[att] += batUnitsA
        self.tempTroopTable[defe] += batUnitsB
        #addThese to a temp troop total for each player

    def rollDice(self,a,b,c):
        #A is attacking and b is defending
        aRolls = []
        bRolls = []
        aRolls.append(random.randint(1,1000)%11)
        bRolls.append(random.randint(1,1000)%11)
        bRolls.append(random.randint(1,1000)%11)
        aRolls.append(random.randint(1,1000)%11)
        aRolls.append(random.randint(1,1000)%11)
        aRolls.sort()
        aRolls.reverse()
        bRolls.sort()
        bRolls.reverse()
        #print "A Rolled is:",aRolls
        #print "B Rolled is:",bRolls
        if aRolls[0] == bRolls[0]:
            self.equalRolls += 1
            #print "Nothing happens0"
        elif aRolls[0] > bRolls[0]:
            b -= 1
        else:
            a -= 1
        if c:
            if a == 0 or b == 0:
                return a,b
        if aRolls[1] == bRolls[1]:
            self.equalRolls += 1
            #print "Nothing happens1"
        elif aRolls[1] > bRolls[1]:
            b -= 1
        else:
            a -= 1
        #print 'A ends with',a
        #print 'B ends with',b
        return a,b

    def deathBattle(self,aa,bb):
        a = aa
        b = bb
        while a > 0 and b > 0:
            a,b = self.rollDice(a,b,True)
        #print "A numbers",a,"B numbers",b
        return a,b

    #*****************************#
    ##State Machine begins below##
    #*****************************#
    def state0(self,data,pos,s,officalPlayer):
        if data[:2] == '(c':
            return self.state1(data,2,s,officalPlayer)
        else:
            self.sendStrike(s,"malformed","State 0: Not (c:%s"%(data[:2]))
            return self.resync(data[pos+1:],0,s,officalPlayer)

    def state1(self,data,pos,s,officalPlayer):
        #print "State 1"
        if not officalPlayer:   #nonofficalPlayers can only sending cjoin messages
            if data[pos:pos+5] == 'join(':
                return self.joinS2(data,pos+5,'',s)
        else:           #officalplayers can only sending cchat and cstat messages
            if data[pos:pos+5] == 'chat(':
                return self.chatS2(data,pos+5,'',s)
            elif data[pos:pos+5] == 'stat)':
                return self.statS2(data,pos+5,s)
        self.sendStrike(s,"malformed","State 1: Unknown Comd: data[i:i+5]= |%s|"%(data[pos:pos+5]))
        return self.resync(data[pos+1:],0,s,officalPlayer)

    def chatS2(self,data,pos,names,s):
        if pos > BUFSIZE:
            self.sendStrike(s,"toolong","Chat State 2-1:pos [%d]?"%(pos))
            return self.resync(data[pos+1:],0,s,True)
        if pos > len(data)-1:   #others have pos >= len(data)
            self.sendStrike(s,"malformed","Chat State 2-2:[pos %d >= len %d]?"%(pos,len(data)))
            return self.resync(data[pos+1:],0,s,True)
        if data[pos] == ')':
            return self.chatS3(data,pos+1,names,s)
        else:
            names += data[pos]
            return self.chatS2(data,pos+1,names,s)

    def chatS3(self,data,pos,names,s):
        if pos >= len(data):
            self.sendStrike(s,"malformed","Chat State 3-1:[pos %d >= len %d]? data:|%s|"%(pos,len(data)),data)
            return True
        if data[pos] == '(':
            return self.chatS4(data,pos+1,names,'',s)
        else:
            self.sendStrike(s,"malformed","Chat State 3-2: data[pos] %s != )"%(data[pos]))
            return self.resync(data[pos+1:],0,s,True)

    def chatS4(self,data,pos,names,msg,s):
        if pos > BUFSIZE-2:
            self.sendStrike(s,"toolong","Chat State 4:pos %d"%(pos))
            return self.resync(data[pos+1:],0,s,True)
        if pos >= len(data):                #CHANGED FROM >
            self.sendStrike(s,"malformed","Chat State 4-1:pos %d line: |%s|"%(pos,data))
            return self.resync(data[pos+1:],0,s,True)
        if (ord(data[pos]) >= 32) and (ord(data[pos]) <= 126):
            data = data[:pos] + data[pos:]
        if data[pos] == ')':
            return self.chatS5(data,pos+1,names,msg,s)
        else:
            msg += data[pos]
            return self.chatS4(data,pos+1,names,msg,s)

    def chatS5(self,data,pos,names,msg,s):
        #print "chat state 5"
        if pos >= len(data):
            self.sendStrike(s,"malformed","Chat State 5-1:[pos %d >= len %d]?"%(pos,len(data)))
            return False
        if data[pos] == ')':
            return self.chatS6(data,pos+1,names,msg,s)
        else:
            self.sendStrike(s,"malformed","Chat State 5-2: data[pos] %s != )"%(data[pos]))
            return self.resync(data[pos+1:],0,s,True)

    def chatS6(self,data,pos,names,msg,s): #Final State
        #self.addRecv(s)
        if names == "SERVER":
            if self.phase == 1:
                self.proccessPhase1Message(s,names,msg)
            elif self.phase == 2:
                self.proccessPhase2Message(s,names,msg)
            elif self.phase == 3:
                self.proccessPhase3Message(s,names,msg)
            else:
                print "Game has not started or bad phase: %d"%self.phase
        else:
            self.sendChatMessage(names,msg,s)
        return self.resync(data[pos:],0,s,True)

    def joinS2(self,data,pos,name,s):
        if pos > BUFSIZE:
            self.sendStrike(s,"toolong","Join State 2")
            return self.resync(data[pos+1:],0,s,False)
        if pos >= len(data):
            self.sendStrike(s,"malformed","Join State 2-1")
            return self.resync(data[pos+1:],0,s,False)
        if data[pos] == ')':
            return self.joinS3(data,pos+1,name,s)
        else:
            num = ord(data[pos])
            cap = (num>=65) and (num <= 90)
            low =(num>=97) and (num <= 122)
            per = (num == 46)
            til = (num == 126)
            nem = (num >=48) and (num <=57)
            if cap or low or per or til or nem:
                name += data[pos]
            return self.joinS2(data,pos+1,name,s)

    def joinS3(self,data,pos,name,s):
        if pos >= len(data):
            self.sendStrike(s,"malformed","Join State 3-1")
            return self.resync(data[pos+1:],0,s,False)
        if data[pos] == ')':
            return self.joinS4(data,pos,name,s)
        else:
            self.sendStrike(s,"malformed","Join State 3-2")
            return self.resync(data[pos+1:],0,s,False)

    def joinS4(self,data,pos,name,s): #Final State
        name = self.validateJoinName(name,s)
        players = self.getPlayers()
        smsg = "(sjoin(%s)(%s)(%s))" %(name,players,self.argString) #need to update this with names,units...
        #self.addRecv(s)
        self.sending(s,smsg)
        self.joinClient(s,name)
        return self.resync(data[pos],0,s,False)

    def statS2(self,data,pos,s): #Final State
        players = self.getPlayersPlus()
        statMsg ="(sstat(%s))" %(players)
        #self.addRecv(s)
        self.sending(s,statMsg)
        return self.resync(data[pos-1],0,s,True)

    def resync(self,data,i,s,officalPlayer): #Looks Like I Got it
        if self.toKill: #Player has received their third strike so stop
            return False
        if i != 0:
            i=0
            print "IN resync i is not zero trace this:"
        datalen = len(data)
        while i < datalen:
            if i > BUFSIZE:
                self.sendStrike(s,"toolong","Resync State")
                if self.toKill:
                    return False
                return self.resync(data[i+1:],0,s,officalPlayer)
            if data[i:i+2] == '(c':
                return self.state1(data[i:],2,s,officalPlayer)
            i += 1
        return False

    #**************************#
    ##State Machine ends here##
    #**************************#

    def nextPhase(self):
        if self.phase == 1:
            print "P1: Begin"
            #print "Starting Round %d"%self.round
            self.phase = 2
            self.sendPhase2()
            self.phaseTime = time.time()
        elif self.phase == 2:
            if (self.recvOffers == self.sentOffers): #This is so not to go on until Everybody has repsoned
                print "P2: Begin",self.phase
                self.recvOffers = 0
                self.sentOffers = 0
                self.phase = 3
                self.zeroBattleTable()
                self.sendPhase3()
                self.phaseTime = time.time()
        elif self.phase == 3:
            print "P3: Begin"
            self.sendNotify()
            self.battle()
            print "End of round %d"%self.round
            self.addNewPlayers()
            self.sendallstat(True)
            self.phase = 1
            self.round +=1
            self.sendPhase1()
            #print "Next Round: ",self.checkAllRespond()
            self.phaseTime = time.time()
        else:
            print "Phases",self.phase
            print "Recv offers",self.recvOffers
            print "Send offers",self.sentOffers


    def newGame(self):  #Will initize a new game to be played for the first time or again and set any variable and globals that need to be set inorder to do so
        for i in self.clientTable:
            name = self.getName(i)
            self.alivePlayers[i] = name
        for i in self.clientTable:
            self.phaseRespond[i] = (False,'')
            a,b,c,d,e,f,g,h = self.clientTable[i]
            d = self.force
            #print a,b,c,d,e,f,g,h
            self.clientTable[i] = (a,b,c,d,e,f,g,h)
        self.sendallstat(True)
        #for i in self.phaseRespond:
            #print i,self.phaseRespond[i]
        self.clearRespond()

    def addNewPlayers(self):
        for i in self.newPlayer:
            print "New PLayer[",i,"]being added"
            conn = self.getConn(i)
            self.alivePlayers[conn] = i
        self.newPlayer = []

    def joinClient(self,client,name):
        #self.inputs.append(client)
        info = self.clientTable[client]
        host,badname, strikes,units,flag,send,recv,win = info[0], info[1], info[2],info[3],info[4],info[5],info[6],info[7]
        self.clients += 1
        jj = 0
        self.nameNum[name] = self.ni
        self.ni += 1
        self.alivePlayers[client] = name
        self.clientTable[client] = (host,name,strikes,units,True,send,recv,win) #offically adds the client to the table
        if self.playingGame:
            self.phaseRespond[client] = (True,'')
            self.newPlayer.append(name)
        else:
            self.phaseRespond[client] = (False,'')
            self.alivePlayers[client] = name
        #self.outputs.append(client)
        self.sendallstat(False)

    def serves(self):
        self.inputs = [self.server,sys.stdin]    ##What does this do
        self.outputs = []
        running = 1
        while running:
            try:
                self.inputready,self.outputready,exceptready = select.select(self.inputs,self.outputs,[])
            except select.error, e:
                break
            except socket.error,e:
                break
            #Start a round somewhere
            #Need to begin phase 1 send out (schat(SERVER)(PLAN,R#))
            if self.playGame == True:
                if self.playingGame:
                    if self.winner:
                        conn = self.getConn(self.foundWinner)
                        a,b,c,d,e,f,g,h = self.clientTable[conn]
                        h +=1
                        self.clientTable[conn] =(a,b,c,d,e,f,g,h)
                        print "*"*30
                        print "{:<15s} {:<5} times".format(self.foundWinner,self.getWins(conn))
                        print "*"*30
                        #Found a winner need to get the name of winner self.winnerName or something
                        #print "I found a Winner display winner name then start a new round."
                        self.playingGame = False
                        self.winner = False
                        self.lobbyWait = time.time()
                    else:
                        if self.checkAllRespond():
                            self.nextPhase()
                        curr = time.time()
                        if ((curr - self.phaseTime) > self.timeout) and (self.playingGame == True):
                            self.printRespond()
                            copyData = self.phaseRespond
                            for i in copyData:
                                #waiting on this
                                info = copyData[i]
                                if info[0] == False:
                                    self.sendStrike(i,"timeout","Strike for timeout. Took %d needed less than %d "%(curr-self.phase,self.timeout))
                                    #need to say they passed or declined
                                    if self.phase == 1:
                                        self.playerTable[i] = True
                                    if self.phase == 2:
                                        self.recvOffers = self.sentOffers
                                        self.phaseRespond[s] = (True,'') 
                            for i in self.removeList:
                                del self.phaseRespond[i]
                            self.removeList = {}
                            self.phaseTime = time.time()
                            #self.phase += 1
                            self.nextPhase()
                else:
                    if self.clients >= self.minPlayers and self.playingGame == False:
                        if self.notWaiting == True:
                            print "Lobby has enough player to begin a game. Now waiting..."
                            self.lobbyWait = time.time()
                            self.notWaiting = False
                        elif ((time.time() - self.lobbyWait) > self.lobbyTimeout):
                            print "Starting Game"
                            self.newGame()
                            self.round = 1
                            self.phase = 1
                            self.playingGame = True
                            self.sendPhase1()
                            #print "FIRST CHECK IF RESPOND",self.checkAllRespond()
                            self.phaseTime = time.time()
            if self.clients == 0:
                self.playingGame = False
            if self.round >= 99999:
                self.round = 1
                #print "Only battling out a few rounds"
                running = 0
            for s in self.inputready:
                if s == self.server:        #this is for cjoin
                    client,address = self.server.accept()
                    if self.clients >= MAXPLAYERS:
                        print "MAX Players reached"
                        self.sending(client,'(snovac)')
                    else:
                        self.clientTable[client] = (address,'##',0,self.force,False,0,0,0)  #Unoffically adds the client to the table
                        self.inputs.append(client)
                        self.outputs.append(client)
                elif s == sys.stdin:
                    #Built in commands to call during runtime
                    j = sys.stdin.readline().strip()
                    if j == 't':    #prints amount of time elapsed
                        self.getTime()
                    elif j.lower() == 'q':
                        print "Exiting Server"
                        running = 0
                    elif j == 's':  #prints strikes
                        self.printStrikes()
                    elif j =='c':   #prints clientTable
                        self.printClientTable()
                    elif j =='p':
                        print "Number of Players: %d" %(self.clients)
                    elif j =='m':   #prints number of messages received
                        self.printNumMsg()
                    elif j == 'h' or j.lower == 'help':
                        self.printHelp()
                    elif j == 'a':
                        self.printalive()
                    elif j =="b":
                        self.printNameNum()
                        self.printMatrix()
                        print "nameNumValues",self.nameNum.values
                else:
                    try:
                        data = s.recv(1024)
                        self.msgsRecv += 1

                        #data = self.stripNon(data)
                        #print "Sending: %s sends: %s" %(self.getName(s),data
                        if data:
                            #print "Clients Clearance is: %s" %(self.clientTable[s][4])
                            self.state0(data,0,s,self.clientTable[s][4])
                            if self.toKill == True:
                                self.toKill = False
                                self.clients -=1
                                s.close()
                                self.inputs.remove(s)
                                self.outputs.remove(s)
                                ename = self.getName(s)
                                self.removeClient(s)
                                self.sendallstat(False)
                                print 'Kick: %s has been kicked from the chat server.' %(ename)
                        else:
                            print 'Left: %s has left the chat server.' %(self.getName(s))
                            self.clients -= 1
                            s.close()
                            self.inputs.remove(s)
                            self.outputs.remove(s)
                            self.removeClient(s)
                            self.sendallstat(False)
                    except socket.error, e:
                        print 'Error: %s has errored out of the chat server.' %(self.getName(s))
                        self.clients -=1
                        self.inputs.remove(s)
                        self.outputs.remove(s)
                        self.removeClient(s)
                        self.sendallstat(False)
        self.printalive()
        self.getTime()
        self.printClientTable()
        self.printNumMsg()
        print "*"*90
        print "*"*90
        for o in self.outputs:
            o.close()
        self.server.close()
        self.server.close()

if __name__ == "__main__":
    t,l,m,f = 30,15,3,1000
    numArgs = len(sys.argv)
    if numArgs%2 == 0:
        print numArgs
        print 'Usage: %s -t # -l # -m # -f #' %(sys.argv[0])
        sys.exit()
    for x in range(1,numArgs):
        if (sys.argv[x] == '-t'):
            #print "-t Getting timeout length"
            t = int(sys.argv[x+1])
            x+=1
        elif (sys.argv[x] == '-l'):
            #print "-l Getting lobby waittime "
            l = int(sys.argv[x+1])
            #print "-l: ",l
            x +=1
        elif (sys.argv[x] == '-m'):
            #print "-m Getting minimum number of players"
            m = int(sys.argv[x+1])
            #print "-m: ",m
            x += 1
        elif (sys.argv[x] == '-f'):
            f = int(sys.argv[x+1])
            x += 1
    Server(t,l,m,f).serves()
