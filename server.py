#Travis Eickmeyer
#DATE: 3/9/14
#CLASS: CSCI 367
#Project: Chat Server/Client
#File: server.py
#Professor: Michael Meehan

import select
import socket
import sys
import signal
import random
import time

BUFSIZE = 480      #Change to reflect the current BUFSIZE
MAXPLAYERS = 30     #Max number of player in the server 
#TODO: all and any working and I think that might be it. But I don't know. Do snovac so keep a track of the number of players
#Isssue/bug when sending a strike that would be there third my server disconnects this is in sendstrike why does it exit
#Have half the parse/statemachine working finished but cchat/schat next is cjoin/sjoin and then cstat/sstat fit in snovac
#Get rid of obsolete code ok.
#

class Server(object):

    def __init__(self,timeout,lobby,player,port=36716):
        self.timestarted = time.time()
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
        self.toKill = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('',port))
        except socket.error, e:
            print "This port is still active. Please wait a few moments before trying again."
            self.server.close()
            time.sleep(2)   #Wait for a bit
            sys.exit()
        self.server.listen(1)
        host = socket.gethostbyname(socket.gethostname())
        print "Maximum number of player on server is %d" %(MAXPLAYERS)
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

    def searchNames(self, name):
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
        print "|    Name     ||     Address     ||  Port  || Strikes |"
        print "*******************************************************"
        for i in self.clientTable:
            c = self.clientTable[i]
            host,name,strk = c[0],c[1],c[2]
            ip,port = host[0],host[1]
            print  "|%12s :: %15s :: %6s :: %5s   |" %(name,ip,port,strk)
        print "There are %d players on the server" %(self.clients)

    def getStrikes(self,conn):
        info = self.clientTable[conn]
        host,name,strikes = info[0], info[1], info[2]
        int(strikes)
        return strikes

    def sendStrike(self,conn,reason,comment):
        try:
            snum = self.getStrikes(conn)
            snum += 1
            a,b,c = self.clientTable[conn]
            self.clientTable[conn] = (a,b,snum)
        except LookupError, e:
            print "Strikes Loop up error:",conn,reason,comment
            snum = 1

        strike = "(strike(%d)(%s))" % (snum,reason)
        self.sending(conn,strike)
        print "%s has received a %s strike Number %d: Comment: %s"%(self.getName(conn),reason,snum,comment)
        if snum >= 3:
            print "Disconnecting Client"
            self.toKill = True

    def stripNon(self,line):
        #print "Line Before:", line
        newline = ''
        for x in range(0,len(line)):
            if ((ord(line[x])>=65) and (ord(line[x]) <= 90)) or ((ord(line[x])>=48) and (ord(line[x])>=48)):
                newline += line[x]
        return newline #Unsure if this is need I will test for it.

    def removeClient(self,conn):
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
            #if s != c:
            self.sending(c,sendmsg)

    def anysend(self,msg,s):
        sender = '(schat(%s)(%s))' %(self.getName(s),msg)
        per =random.choice(self.clientTable.keys())
        self.sending(per,sender)

    def sending(self,s,msg):
        try:
            self.msgsSent +=1 
            s.send(msg)
        except socket.error, e:
            self.msgBad += 1
            print "DO Nothing"

    def sendallstat(self):
        statmsg = '(sstat(%s))' %(self.getPlayers())
        for c in self.clientTable:
            self.msgsSent += 1
            self.sending(c,statmsg)

    def sendChatMessage(self,names,msg,s):
        nameNoExist = False
        if len(msg) > 80:
            msg = msg[0:80]
            #print "Msg was too long it is now size:" ,len[msg]
        fromWhom = self.getName(s)
        playerList = names.split(',')
        #print '[%s] - %s' %(fromWhom,msg)
        for p in playerList:
            if self.searchNames(p) == False:
                sendmsg = '(schat(%s)(%s))' %(fromWhom,msg)
                conn = self.getConn(p)
                self.sending(conn,sendmsg)
            elif p == 'any':
                self.anysend(msg,s)
            elif p == 'all':
                self.allsend(msg,s)
            else:
                nameNoExist = True
        #if nameNoExist == True:
            #print "Name does not here"
            #self.sendStrike(s,"malformed","sendChatmsg: Bad name")

    #*****************************#
    ##State Machine begins below##
    #*****************************#
    # All the resync calls may have to pass in 
    # data[pos:] instead of data                                

    def state0(self,data,pos,s,newPlayer):
        #State 0 checks for (c if found go to state 2 else sending strike and resync  
        #print "State 0"
        if data[:2] == '(c':
            return self.state1(data,2,s,newPlayer)
        else:
            #print "Sending Strike here state 0: Malformed"
            self.sendStrike(s,"malformed","State 0: Not (c:%s"%(data[:2]))
            return self.resync(data[pos+1:],0,s,newPlayer)

    def state1(self,data,pos,s,newPlayer):
        #print "State 1"
        if newPlayer:   #newPlayers can only sending cjoin messages 
            if data[pos:pos+5] == 'join(':
                return self.joinS2(data,pos+5,'',s)
        else:           #Old players can only sending cchat and cstat messages
            if data[pos:pos+5] == 'chat(':
                return self.chatS2(data,pos+5,'',s)
            elif data[pos:pos+5] == 'stat)':
                return self.statS2(data,pos+5,s)
        #print "Sending Strike here state 1: Malformed"
        self.sendStrike(s,"malformed","State 1: Unknown Comd: data[i:i+5]= |%s|"%(data[pos:pos+5]))
        return self.resync(data[pos+1:],0,s,newPlayer)

    def chatS2(self,data,pos,names,s):
        #print "chat state 2"
        if pos > BUFSIZE:
            #print "Message Too Large Need to Stop chat state 2"
            self.sendStrike(s,"toolong","Chat State 2-1:pos [%d]?"%(pos))
            return self.resync(data[pos+1:],0,s,False)
        if pos > len(data)-1:   #others have pos >= len(data)
            self.sendStrike(s,"malformed","Chat State 2-2:[pos %d >= len %d]?"%(pos,len(data)))
            return self.resync(data[pos+1:],0,s,False)
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
            return False
        if data[pos] == '(':
            return self.chatS4(data,pos+1,names,'',s)
        else:
            #print "malformed: chat S3"
            self.sendStrike(s,"malformed","Chat State 3-2: data[pos] %s != )"%(data[pos]))
            return self.resync(data[pos+1:],0,s,False)

    def chatS4(self,data,pos,names,msg,s):
        #print "chat state 4"
        if pos > BUFSIZE-2:
            #print "chat S4: toolong - toolong"
            self.sendStrike(s,"toolong","Chat State 4:pos %d"%(pos))
            return self.resync(data[pos+1:],0,s,False)
        if pos >= len(data):                #CHANGED FROM >

            self.sendStrike(s,"malformed","Chat State 4-1:pos %d line: |%s|"%(pos,data))
            return self.resync(data[pos+1:],0,s,False)
        if (ord(data[pos]) >= 32) and (ord(data[pos]) <= 126):
            #print "Striped data: |%s|%s|%s|" %(data[:pos],data[pos],data[pos+1:])
            data = data[:pos] + data[pos:] #Not Sure if this works
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
            return self.resync(data[pos+1:],0,s,False)

    def chatS6(self,data,pos,names,msg,s): #Final State
        #print "chat state 6"
        #SendMessage and be done
        #print "Sending this schat message to", names,"msg is: (schat(FROM)(", msg,"))"
        self.sendChatMessage(names,msg,s)
        #What do I do with the lambda
        return self.resync(data[pos:],0,s,False)
        return True

    def joinS2(self,data,pos,name,s):
        #print "Msg data:", data
        #print "join state 2"
        if pos > BUFSIZE:
            #print "Message is too long Need to stop join state 2"
            self.sendStrike(s,"toolong","Join State 2")
            return self.resync(data[pos+1:],0,s,True)
        if pos >= len(data):
            #print "Message is too long Need to stop join state 2"
            self.sendStrike(s,"malformed","Join State 2-1")
            return self.resync(data[pos+1:],0,s,True)
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
            return self.resync(data[pos+1:],0,s,True)
        #print "join state 3"
        #print "data[%d]- %s and name %s" %(pos,data[pos],name)
        if data[pos] == ')':
            return self.joinS4(data,pos,name,s)
        else:
            #print "Sending strike here join state 3"
            self.sendStrike(s,"malformed","Join State 3-2")
            return self.resync(data[pos+1:],0,s,True)

    def joinS4(self,data,pos,name,s): #Final State 
        #print "join state 3"
        #print "Name is:" ,name
        name = self.validateJoinName(name,s)
        players = self.getPlayers()
        smsg = "(sjoin(%s)(%s)(%s))" %(name,players,self.argString)
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
        self.sending(s,statMsg)
        return self.resync(data[pos-1],0,s,False)

    def resync(self,data,i,s,newPlayer): #Looks Like I Got it
        #sys.stdout.write('[Resync:')
        if self.toKill: #Player has received their third strike so stop
            #sys.stdout.write('Kicked]\n')
            return False
        #print "resync state"
        #print "Resync Data:",data," i:", i,"NewPlayer:",newPlayer
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
                return self.resync(data[i+1:],0,s,newPlayer)
            if data[i:i+2] == '(c':
                #print "test resync: data[%d:]: |%s|"%(i,data[i:])
                #print "test resync: data[%d:]: |%s|"%(i+2,data[i+2:])
                #sys.stdout.write("To S0:\'(c\')]\n")
                return self.state1(data[i:],2,s,newPlayer)
            i += 1
        #print "Resync: final i=%d" %i  
        #sys.stdout.write('Norm exit]\n')
        return False

    #**************************#
    ##State Machine ends here##
    #**************************#


    def joinClient(self,client,name):
        self.clients += 1
        self.inputs.append(client)
        info = self.clientTable[client]
        host,badname, strikes = info[0], info[1], info[2]
        self.clientTable[client] = (host,name,strikes)
        self.outputs.append(client)
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

            #I feel I need to get rid of most of this and replace with the state machine.
            for s in self.inputready:
                if s == self.server:        #this is for cjoin
                    client,address = self.server.accept()
                    if self.clients >= MAXPLAYERS:
                        print "MAX Players reached"
                        self.sending(client,'(snovac)')
                    else:
                        data = client.recv(BUFSIZE)
                        self.msgsRecv +=1
                        self.clientTable[client] = (address,'',0)
                        self.state0(data,0,client,True) 
                        '''if cname:            #Old method of adding client to Client table
                            self.clients += 1
                            inputs.append(client)
                            self.clientTable[client] = (address,cname,0)
                            self.outputs.append(client)
                            self.sendallstat()'''
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
                            self.state0(data,0,s,False)
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
    t,l,m = 0,0,0
    numArgs = len(sys.argv)
    if numArgs%2 == 0:
        print numArgs
        print 'Usage: %s -t # -l # -m #' %(sys.argv[0])
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
    Server(t,l,m).serves()