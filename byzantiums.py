#Travis Eickmeyer
#DATE: 3/12/14
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
#TODO: add Alive section to clientTable True False inorder to limit player who be allys or attacked
#TODO: Add message section to clientTable to hold onto messages that where created during the previous phase

class Server(object):

    def __init__(self,timeout=30,lobby=30,player=3,force=1000,port=36716):
        self.timestarted = time.time()
        self.force = int(force)
        self.timeout = int(timeout)
        self.lobbyTimeout = int(lobby)
        self.minPlayers = int(player)
        self.argString = "%s,%s,%s,%s"%(self.minPlayers,self.lobbyTimeout,self.timeout,self.force)
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
        self.battleMatrix = [[0 for x in xrange(30) ] for x in xrange(30)]
        self.phaseTime = 0
        self.playingGame = False
        self.notWaiting = True
        self.lobbyWait = 0
        self.toKill = False
        self.foundWinner = False
        self.oneResponse = False
        self.alivePlayers = {}
        self.nameNum  = {}
        self.ni = 0
        self.sentOffers = 0
        self.recvOffers = 0
        self.attackList = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('',port))
        except socket.error, e:
            print "This port: %d is still active. Please wait a few moments before trying again."%port
            self.server.close()
            time.sleep(2)   #Wait for a bit
            sys.exit()
        self.server.listen(1)
        host = socket.gethostbyname(socket.gethostname())
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
        print "|    Name     ||     Address     ||  Port  || Strike || Units || Joined || SentTo || RcvFrm |"
        print "*********************************************************************************************"
        for i in self.clientTable:
            c = self.clientTable[i]
            host,name,strikes,units,offical,send,recv = c[0],c[1],c[2],c[3],c[4],c[5],c[6]
            ip,port = host[0],host[1]
            print  "|%12s :: %15s :: %6s ::   %2s   :: %5d :: %5s  :: %5d  :: %5d  |" %(name,ip,port,strikes,units,offical,send,recv)
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
            a,b,c,u,f,s,r = self.clientTable[conn]  #address, name , strikes,units,flags
            self.clientTable[conn] = (a,b,snum,u,f,s,r)
        except LookupError, e:
            print "Strikes Loop up error:",conn,reason,comment
            snum = 1
        strike = "(strike(%d)(%s))" % (snum,reason)
        self.sending(conn,strike)
        print "%s has received a %s strike Number %d: Comment: %s"%(self.getName(conn),reason,snum,comment)
        if snum >= 3:
            print "Disconnecting Client"
            self.toKill = True

    def removeClient(self,conn):
        del self.alivePlayers[conn]
        del self.playerTable[conn]
        del self.phaseRespond[conn]
        del self.clientTable[conn]
        conn.close()

    def validateJoinName(self,name,s):
        #print "Name given:|%s|"%name
        if name == '':
            print "No name given"
            name = 'NAME'
            self.sendStrike(s,'malformed',"ValidjName: No name given")
        if name.lower == 'all':
            print "Reserved Name: all"
            self.sendStrike(s,'malformed',"ValidjName: Reserved Name Given: all")
        if name.lower == 'any':
            print "Reserved Name: any"
            self.sendStrike(s,'malformed',"ValidjName: Reserved Name Given: all")
        #if name.upper == 'SERVER':     #For phase 2
            #print "Reserved Name: any"
            #self.sendStrike(s,'malformed',"ValidjName: Reserved Name Given: all")
        name = name.upper()
        #print "Name before removing:|%s|" %(name)
        #name = self.stripNon(name) #May not need this 
        #print "Name After removing :|%s|" %(name)
        dos = name.split('.',1)
        end = ''
        if len(dos) > 1:
            if len(dos[1]) > 3:
                dos[1] = dos[1][0:3] #should keep it 3 or less
            end = '.' + dos[1]
        pre = dos[0][:7] #CHANGED  THIS FROM 6 to 7
        name = pre + end
        #print "Almost name is: %s" %(name)
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
            #print "The DOS name:",name+mid+end
            return name+mid+end

    def allsend(self,msg,s):
        sendmsg = '(schat(%s)(%s))' %(self.getName(s),msg)
        for c in self.clientTable:
            #if s != c: #This is to not send to themself
            if self.getName(c) != '##':
                self.sending(c,sendmsg)

    def ServerAllSend(self,msg):
        for i in self.clientTable:
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
            self.addSend(s)
            s.send(msg)
        except socket.error, e:
            self.msgBad += 1
            print "DO Nothing"

    def sendallstat(self):
        statmsg = '(sstat(%s))' %(self.getPlayers())
        for c in self.clientTable:
            if self.getName(c) != '##':
                self.msgsSent += 1
                self.sending(c,statmsg)

    def zeroBattleTable(self):
        for i in range(0,30):
            for j in range(0,30):
                self.battleMatrix[i][j] = 0

    def proccessPhase1Message(self,s,name,msg):
        print "Recv Round %d Phase 1 Messages"%self.round
        #Check if message contains (PLAN,R#,PASS) or (PLAN,R#,APPROACH,ALLY,ATTACKEE)
        #                               Round number PASS       APPROACH who to ally and who to attack
        print "Phase 1 message: %s"%msg
        args = msg.split(',')
        phase = ''
        rnd = 0
        if len(args) == 3:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            if phase != "PLAN":
                self.sendStrike(s,"malformed","Phase 1: Did not give PLAN phase gave:%s"%(phase))
                print "Assuming Player passes or see if they send again"
                return False 
            if action != "PASS":
                self.sendStrike(s,"malformed","Phase 1: Did not give PASS gave:%s"%(action))
                print "Assuming Player passes or see if they send again"
                return False 
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 1: Not the correct Round Number:%d"%(rnd))
                print "Assuming Player passes or see if they send again"
                return False 
            print "Player does not wish to make an allicance"
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
                print "Assuming Player passes or see if they send again"
                return False 
            if action != "APPROACH":
                self.sendStrike(s,"malformed","Phase 1: Did not give PASS gave:%s"%(action))
                print "Assuming Player passes or see if they send again"
                return False 
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 1: Not the correct Round Number:%d"%(rnd))
                print "Assuming Player passes or see if they send again"
                return False               
            #Check if ally exist else send strike
            #check if attackee exist else send strike 
            #Need to save phase 1 message somewhere to be sent in phase 2
            #make sure ally is not himself or attacking himself Might just allow it for the stupid people
            sec = "ALLY WITH %s TO ATTACK %s" %(ally,attackee)
            self.playerTable[s] = True
            self.phaseRespond[s] = (True,sec)
            sendTo = self.getConn(ally)
            allyToBe = self.getName(s)
            phase2msg = "(schat(SERVER)(OFFERL,%s,%s,%s))"%(self.round,allyToBe,attackee)
            self.allyTable.append((sendTo,phase2msg))
            print "P1 AP: Send:%s TO:%s FROM:%s" %(phase2msg,ally,allyToBe)
            #self.sending(sendTo,phase2msg) Might add to clientTable for message part
            #msg = (schat(SERVER)(OFFERL,R#,ALLY,ATTACKEE))
            #ally is 
            return True
        else:
            self.sendStrike(s,"malformed","Phase 1: Not the Correct number of Arguments:%d"%(len(args)))
            print "Assuming Player passes or see if they send again"
            return False
        return True

    def proccessPhase2Message(self,s,name,msg):
        print "Recv Round %d Phase 2 Messages"%self.round
        #Already sent off messages to people
        print "Phase 1 message: %s"%msg
        print "Number of sent offers sent: %d"%self.sentOffers
        args = msg.split(',')
        if len(args) == 3:
            decision = args[0]
            rnd = int(args[1])
            ally = args[2]
            if rnd != self.round:
                self.sendStrike(s,"malformed %s"%msg,"Phase 2: Not the correct Round Number:%d"%(rnd))
                print "Bad Round number sent"
                return False
            #check i ally is good. and has sent current client a ally message
            ######What happens if client accepts or rejects a an ally that they did not receive a ally message from or something.
            if decision == "ACCEPT":
                self.recvOffers +=1
                #inform origonal client of action
                self.phaseRespond[s] = (True,"ACCEPT")
                print "%s Accepted allyship from ally:%s" %(self.getName(s),ally)
                line = "(schat(SERVER)(ACCEPT,%s,%s))"%(self.round,self.getName(s))
                self.phaseRespond[s] = (True,"DECLINE")
                self.sending(self.getConn(ally),line)
            elif decision == "DECLINE":
                self.recvOffers +=1
                self.phaseRespond[s] = (True,)
                #inform origonal client of action
                print "%s Rejected allyship from ally:%s" %(self.getName(s),ally)
            else:
                print "did not send accept or reject"
        else:
            self.sendStrike(s,"malformed","Phase 2: Not the Correct number of Arguments:%d"%(len(args)))
            print "Assuming Player passes or see if they send again"
            return False
        return True

    def proccessPhase3Message(self,s,name,msg):
        print "Recv Round %d Phase 3 Messages"%self.round
        #This is the real phase what ever happens here is there real answer
        print "Phase 3 message: %s"%msg
        args = msg.split(',')
        phase = ''
        rnd = 0
        if len(args) == 3:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            if phase != "ACTION":
                self.sendStrike(s,"malformed","Phase 3: Did not give ACTION phase gave:%s"%(phase))
                print "Assuming Player passes or see if they send again"
                return False 
            if action != "PASS":
                self.sendStrike(s,"malformed","Phase 3: Did not give PASS gave:%s"%(action))
                print "Assuming Player passes or see if they send again"
                return False 
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 3: Not the correct Round Number:%d"%(rnd))
                print "Assuming Player passes or see if they send again"
                return False 
            print "Player does not wish attack this turn"
            self.phaseRespond[s] = (True,"ACTION PASS")
            #Set zero in all rows of his table
        elif len(args) == 4:
            phase = args[0]
            action = args[2]
            rnd = int(args[1])
            attackee = args[3]
            if phase != "ACTION":
                self.sendStrike(s,"malformed","Phase 3: Did not give ACTION phase gave:%s"%(phase))
                print "Assuming Player passes or see if they send again"
                return False
            if rnd != self.round:
                self.sendStrike(s,"malformed","Phase 3: Not the correct Round Number:%d"%(rnd))
                print "Assuming Player passes or see if they send again"
                return False
            if action != "ATTACK":
                self.sendStrike(s,"malformed","Phase 3: Did not give ATTACK gave:%s"%(action))
                print "Assuming Player passes or see if they send again"
                return False
            #check if attackee exits 
            #And Then add the appropriate 1 in the battleMatrix
            attacker = self.getName(s)
            print "%s will Attack %s"%(attacker,attackee)
            self.phaseRespond[s] = (True,"ACTION ATTACK %s"%attackee)
            line = "(schat(SERVER)(NOTIFY,%s,%s,%s))"%(self.round,attacker,attackee)
            self.attackList.append(line)
            i = self.nameNum[attacker]
            j = self.nameNum[attackee]
            print "i: %d and j: %d"%(i,j)
            self.battleMatrix[i][j] = 1
            return True
        else:
            self.sendStrike(s,"malformed","Phase 3: Not the Correct number of Arguments:%d"%(len(args)))
            print "Assuming Player passes or see if they send again"
            return False
        return True

    def clearRespond(self):
        for i in self.phaseRespond:
            self.phaseRespond[i] = (False,'')


    def printRespond(self):
        for i in self.phaseRespond:
            info = self.phaseRespond[i]
            print "stuff",info

    def sendPhase1(self):
        msg = "(schat(SERVER)(PLAN,%s))"%(self.round)
        print "Sent Out Round %d Phase 1 Messages"%self.round
        self.ServerAllSend(msg)

    def sendPhase2(self): # for those who do not send a message in time they could not recieve a message with this current method
        #send (schat(SERVER)(OFFERL,R#,ALLY,ATTACKEE)) can have more than one offer Need to figure out a way to store this for each player
        #or
        #Send (schat)(SERVER)(OFFERL,R#)) if no offers easy to send 
        print "Sent out Round %d Phase 2 Messages"%self.round
        self.clearRespond()
        for i in self.allyTable:
            s = i[0]
            self.playerTable[s] = False
            msg = i[1]
            print msg
            self.sentOffers +=1
            self.sending(s,msg)
            print "Phase 2:[%s] Got alliance message"%self.getName(s)
        self.allyTable = []
        msg = "(schat(SERVER)(OFFERL,R#))"
        for i in self.playerTable:
            if self.playerTable[i]: #Has not receved any offers
                self.phaseRespond[i] = (True,'')
                print "Phase 2:[%s] Got no offers"%(self.getName(i))    # Expect no response from these people 
                self.sending(i,msg)

    def sendPhase3(self):
        print "Sent out Round %d Phase 3 Messages"%self.round
        self.clearRespond()
        msg = "(schat(SERVER)(ACTION,%s))"%(self.round)
        print "Sent Out Phase 3 Messages"
        self.ServerAllSend(msg)

    def sendNotify(self):
        print "Sent out Round %d Phase Nofity Messages"%self.round
        self.clearRespond()
        #(schat(SERVER)(NOTIFY,R#,ATTACKER,ATTACKEE))
        #send notifcation messages to each client of what each client did
        for i in self.attackList:
            print "notify line: %s"%i
            self.ServerAllSend(i)
        #for i in self.phaseRespond:
        #    self.phaseRespond[i] = (True,'')
        self.attackList = []

    def sendChatMessage(self,names,msg,s):
        nameNoExist = False
        if len(msg) > 80:
            msg = msg[0:80]
            #print "Msg was too long it is now size:" ,len[msg]
        fromWhom = self.getName(s)
        playerList = names.split(',')
        #print '[%s] - %s' %(fromWhom,msg)
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
        a,b,c,d,e,f,g = self.clientTable[s]
        g+=1
        self.clientTable[s] = (a,b,c,d,e,f,g)

    def addSend(self,s):
        a,b,c,d,e,f,g = self.clientTable[s]
        f+=1
        self.clientTable[s] = (a,b,c,d,e,f,g)

    def checkAllRespond(self):
        for i in self.phaseRespond:     #This looks to be very ineffiecient but I don't care
            info = self.phaseRespond[i]
            resp = info[0]
            also = info[1]
            if resp == False:
                return False
        return True

    def checkIfWinner(self):
        if self.foundWinner:
            print "Winner Found"


    def printMatrix(self):
        header = '    '
        spacer = '****'
        for i in range(0,self.clients):
            header += ' |%2d|'%i
            spacer += '*****'
        print header
        print spacer
        for i in range(0,self.ni):
            row = '|%d|*'%i
            for j in range(0,self.ni):
                row += " |%2d|"%self.battleMatrix[i][j]
            print row


    def battle(self):
        print "**********************"
        print "*ROUND: %5s*"%self.round
        print "**********************"
        self.printMatrix()



    #*****************************#
    ##State Machine begins below##
    #*****************************#
    # All the resync calls may have to pass in 
    # data[pos:] instead of data                                

    def state0(self,data,pos,s,officalPlayer):
        #State 0 checks for (c if found go to state 2 else sending strike and resync  
        #print "State 0"    
        if data[:2] == '(c':
            return self.state1(data,2,s,officalPlayer)
        else:
            #print "Sending Strike here state 0: Malformed"
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
        #print "Sending Strike here state 1: Malformed"
        self.sendStrike(s,"malformed","State 1: Unknown Comd: data[i:i+5]= |%s|"%(data[pos:pos+5]))
        return self.resync(data[pos+1:],0,s,officalPlayer)

    def chatS2(self,data,pos,names,s):
        #print "chat state 2"
        if pos > BUFSIZE:
            #print "Message Too Large Need to Stop chat state 2"
            self.sendStrike(s,"toolong","Chat State 2-1:pos [%d]?"%(pos))
            return self.resync(data[pos+1:],0,s,True)
        if pos > len(data)-1:   #others have pos >= len(data)
            self.sendStrike(s,"malformed","Chat State 2-2:[pos %d >= len %d]?"%(pos,len(data)))
            return self.resync(data[pos+1:],0,s,True)
        if data[pos] == ')':
            #print "Name(s) to Sending to:",names
            return self.chatS3(data,pos+1,names,s)
        else:
            names += data[pos]
            return self.chatS2(data,pos+1,names,s)

    def chatS3(self,data,pos,names,s):
        #print "chat state 3"
        if pos >= len(data):
            self.sendStrike(s,"malformed","Chat State 3-1:[pos %d >= len %d]? data:|%s|"%(pos,len(data)),data)
            #print "chat S4 -malformed: "
            return True
        if data[pos] == '(':
            return self.chatS4(data,pos+1,names,'',s)
        else:
            #print "malformed: chat S3"
            self.sendStrike(s,"malformed","Chat State 3-2: data[pos] %s != )"%(data[pos]))
            return self.resync(data[pos+1:],0,s,True)

    def chatS4(self,data,pos,names,msg,s):
        #print "chat state 4"
        if pos > BUFSIZE-2:
            #print "chat S4: toolong - toolong"
            self.sendStrike(s,"toolong","Chat State 4:pos %d"%(pos))
            return self.resync(data[pos+1:],0,s,True)
        if pos >= len(data):                #CHANGED FROM >
            self.sendStrike(s,"malformed","Chat State 4-1:pos %d line: |%s|"%(pos,data))
            return self.resync(data[pos+1:],0,s,True)
        if (ord(data[pos]) >= 32) and (ord(data[pos]) <= 126):
            #print "Striped data: |%s|%s|%s|" %(data[:pos],data[pos],data[pos+1:])
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
            #print "Sending Strike here chat state 5"
            self.sendStrike(s,"malformed","Chat State 5-2: data[pos] %s != )"%(data[pos]))
            return self.resync(data[pos+1:],0,s,True)

    def chatS6(self,data,pos,names,msg,s): #Final State
        #print "chat state 6"
        #SendMessage and be done
        #print "Sending this schat message to", names,"msg is: (schat(FROM)(", msg,"))"
        self.addRecv(s)
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
        #What do I do with the lambda
        return self.resync(data[pos:],0,s,True)
        return True

    def joinS2(self,data,pos,name,s):
        #print "Msg data:", data
        #print "join state 2"
        if pos > BUFSIZE:
            #print "Message is too long Need to stop join state 2"
            self.sendStrike(s,"toolong","Join State 2")
            return self.resync(data[pos+1:],0,s,False)
        if pos >= len(data):
            #print "Message is too long Need to stop join state 2"
            self.sendStrike(s,"malformed","Join State 2-1")
            return self.resync(data[pos+1:],0,s,False)
        if data[pos] == ')':
            #print "Name to be used:", name
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
        #print "join state 3"
        #print "data[%d]- %s and name %s" %(pos,data[pos],name)
        if data[pos] == ')':
            return self.joinS4(data,pos,name,s)
        else:
            #print "Sending strike here join state 3"
            self.sendStrike(s,"malformed","Join State 3-2")
            return self.resync(data[pos+1:],0,s,False)

    def joinS4(self,data,pos,name,s): #Final State 
        #print "join state 3"
        #print "Name is:" ,name
        name = self.validateJoinName(name,s)
        players = self.getPlayers()
        smsg = "(sjoin(%s)(%s)(%s))" %(name,players,self.argString) #need to update this with names,units...
        self.addRecv(s)
        self.sending(s,smsg)
        #print "Message to be sent: (sjoin(%s)(%s)(%s))" %(name,players,self.argString)
        self.joinClient(s,name)
        #print "joadwd",data[pos]
        return self.resync(data[pos],0,s,False)

    def statS2(self,data,pos,s): #Final State
        #print "stat state 2"
        #Finalize stat message
        players = self.getPlayers()
        statMsg ="(sstat(%s))" %(players)
        self.addRecv(s)
        self.sending(s,statMsg)
        return self.resync(data[pos-1],0,s,True)

    def resync(self,data,i,s,officalPlayer): #Looks Like I Got it
        #sys.stdout.write('[Resync:')
        if self.toKill: #Player has received their third strike so stop
            #sys.stdout.write('Kicked]\n')
            return False
        #print "resync state"
        #print "Resync Data:",data," i:", i,"officalPlayer:",officalPlayer
        if i != 0:
            i=0
            print "IN resync i is not zero trace this:"
        #print "Data Length: %d"%(len(data))
        datalen = len(data)
        while i < datalen:
            #print "Data[%d]=\'%c\'" %(i,data[i])
            if i > BUFSIZE:
                #print "Sending Strike here resync: toolong"
                self.sendStrike(s,"toolong","Resync State")
                if self.toKill:
                    #sys.stdout.write('StrikeOut: %s]\n'%(self.getName(s)))
                    return False
                #sys.stdout.write('To Resync]\n')
                return self.resync(data[i+1:],0,s,officalPlayer)
            if data[i:i+2] == '(c':
                #print "test resync: data[%d:]: |%s|"%(i,data[i:])
                #print "test resync: data[%d:]: |%s|"%(i+2,data[i+2:])
                #sys.stdout.write("To S0:\'(c\')]\n")
                return self.state1(data[i:],2,s,officalPlayer)
            i += 1
        #print "Resync: final i=%d" %i  
        #sys.stdout.write('Norm exit]\n')
        return False

    #**************************#
    ##State Machine ends here##
    #**************************#

    def newGame(self):  #Will initize a new game to be played for the first time or again and set any variable and globals that need to be set inorder to do so
        for i in self.clientTable:
            name = self.getName(i)
            units = self.getUnits(i)
            self.alivePlayers[i] = (name,True,units)

    def joinClient(self,client,name):
        #self.inputs.append(client)
        info = self.clientTable[client]
        host,badname, strikes,units,flag,send,recv = info[0], info[1], info[2],info[3],info[4],info[5],info[6]
        self.clients += 1
        self.nameNum[name] = self.ni
        self.ni += 1
        self.alivePlayers[client] = (name,True,units)
        self.clientTable[client] = (host,name,strikes,units,True,send,recv) #offically adds the client to the table
        self.phaseRespond[client] = (False,'')
        #self.outputs.append(client)
        self.sendallstat()

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
            if self.clients >= self.minPlayers and self.playingGame == False:
                if self.notWaiting == True:
                    print "Lobby has enough player to begin a game. Now waiting..."
                    self.lobbyWait = time.time()
                    self.notWaiting = False
                elif ((time.time() - self.lobbyWait) > self.lobbyTimeout):
                    print "Starting Round 1"
                    self.newGame()
                    self.round = 1
                    self.phase = 1
                    self.playingGame = True
                    self.sendPhase1()
                    self.phaseTime = time.time()
            if self.playingGame:       #dont have to check this stuff unless I am playing the game
                #Check if there is a winner
                if self.checkAllRespond(): #check if all repsond
                    #reset aserespond table
                    if self.phase == 1:
                        print "Everyone has responded onto phase 2"
                        self.phase = 2
                        self.sendPhase2()
                        self.phaseTime = time.time()
                    elif self.phase == 2 and (self.recvOffers == self.sentOffers):
                        print "Everyone has responded onto phase 3"
                        self.recvOffers = 0
                        self.sentOffers = 0
                        self.phase = 3
                        self.zeroBattleTable()
                        self.sendPhase3()
                        self.phaseTime = time.time()
                    elif self.phase == 3:
                        print "Everyone has responded onto phase notify"
                        self.sendNotify()
                        self.battle()
                        print "End of round %d"%self.round
                        self.phase = 1
                        self.round +=1
                        self.sendPhase1()
                        print "Next Round: ",self.checkAllRespond()
                        self.phaseTime = time.time()
                if ((time.time() - self.phaseTime) > self.timeout) and (self.playingGame == True):
                    #Send timeout Strikes to player who have not responded
                    for i in self.phaseRespond:
                        info = self.phaseRespond[i]
                        if info[0] == False:
                            print "Send timeout Strike to %s"%self.getName(i)
                    print "Send Timeout strikes to those who took too long to respond"
                    #then go to phase 2 
                    self.phaseTime = time.time()
            if self.round >= 100:
                sys.exit()
            for s in self.inputready:
                if s == self.server:        #this is for cjoin
                    client,address = self.server.accept()
                    if self.clients >= MAXPLAYERS:
                        print "MAX Players reached"
                        self.sending(client,'(snovac)')
                    else:
                        self.clientTable[client] = (address,'##',0,self.force,False,0,0)  #Unoffically adds the client to the table
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
                        self.printArguments()
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
                                self.sendallstat()
                                print 'Kick: %s has been kicked from the chat server.' %(ename)
                        else:
                            print 'Left: %s has left the chat server.' %(self.getName(s))
                            self.clients -= 1
                            s.close()
                            self.inputs.remove(s)
                            self.outputs.remove(s)
                            self.removeClient(s)
                            self.sendallstat()
                    except socket.error, e:
                        print 'Error: %s has errored out of the chat server.' %(self.getName(s))
                        self.clients -=1
                        self.inputs.remove(s)
                        self.outputs.remove(s)
                        self.removeClient(s)
                        self.sendallstat()
        for o in self.outputs:
            o.close()
        self.server.close()
        self.server.close()

if __name__ == "__main__":
    t,l,m,f = 30,10,3,1000
    numArgs = len(sys.argv)
    if numArgs%2 == 0:
        print numArgs
        print 'Usage: %s -t # -l # -m # -f #' %(sys.argv[0])
        sys.exit()
    for x in range(1,numArgs):
        if (sys.argv[x] == '-t'):
            #print "-t Getting timeout length"
            p = int(sys.argv[x+1])
            #print "-t: ",t
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
