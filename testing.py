import random

tS = 1000

gen1 = ('ADAM' , tS,tS)
gen2 = ('BOB'  , tS,tS)
gen3 = ('CRIS' , tS,tS)
gen4 = ('DAN'  , tS,tS)
gen5 = ('ERIC' , tS,tS)
GenTable ={ 0 : gen1, 1 : gen2, 2: gen3,3:gen4,4: gen5}
#print GenTable
matrix = []

def getUnits(key):
    name,units,new = GenTable[key]
    return units


def printMatrix(r):
    print 'Round Number: %d'%r
    print '     1  2  3  4  5 '
    print '********************'
    c = 1
    for i in matrix:
        print c,'|',i
        c+=1


def rollDice(aU,bU,isAttA,isAttB):
    ARolls = []
    BRolls = []
    ARolls.append(random.randint(1,1000)%11)
    ARolls.append(random.randint(1,1000)%11)
    BRolls.append(random.randint(1,1000)%11)
    BRolls.append(random.randint(1,1000)%11)
    if isAttB:
        BRolls.append(random.randint(1,1000)%11)
    if isAttA:
        ARolls.append(random.randint(1,1000)%11)
    ARolls.sort()
    ARolls.reverse()
    BRolls.sort()
    BRolls.reverse()
    #print "A Rolled is:",ARolls
    #print "B Rolled is:",BRolls
    if ARolls[0] > BRolls[0]:   #Ties go to Defender
        #print '1: A Wins %d to %d' %(ARolls[0],BRolls[0])
        bU -= 1
    else:
        #print '1: B Wins %d to %d' %(BRolls[0],ARolls[0])
        aU -= 1
    if ARolls[1] > BRolls[1]:
        #print '2: A Wins %d to %d' %(ARolls[1],BRolls[1])
        bU-=1
    else:
        #print '2: B Wins %d to %d' %(BRolls[1],ARolls[1])
        aU -=1
    #print " Return values A: %d and B: %d" %(aU,bU)
    return aU,bU



def fight(i,j,a,b):     #i attacks j but j does not attack i
    starti = i
    startj = j
    loops = 0
    #isIatt = checkAttacking(i,j)
    #isJatt = checkAttacking(j,i)
    if starti <= 10 or startj <= 10:
        return deathFight(i,j)
    halfi = starti /2
    halfj = startj /2
    while (i > halfj) and (j > halfj) : #Could be >= instead of >
        #infinate Loop
        i,j =rollDice(i,j,a,b)      #Can use isIatt and isJatt
    i = starti -i
    j = startj - j
    return i,j

def updateUnits():  #Updates the gen table for the end of the round
    for i in GenTable:
        name,old,new = GenTable[i]
        GenTable[i] = (name,new,new)

def updateGenTable(key,units):
    name,old,new = GenTable[key]
    GenTable[key] = (name,old,new - units)

def battle(geni, genj,a,b,off):
    engi,engj = 0,0
    engi = getDefend(geni)+getEngaged(geni) -off
    engj = getDefend(genj)+ getEngaged(genj) -off

    print "Gen %d is engaged with %d other generals" %(geni,engi)
    print "Gen %d is engaged with %d other generals" %(genj,engj)
    unitsI = int(getUnits(geni) /engi)
    unitsJ = int(getUnits(genj) /engj)
    print "%d's Units: %d and %d's Units: %d" %(geni,unitsI,genj,unitsJ)
    unitsI,unitsJ = fight(unitsI,unitsJ,a,b)
    print "After Battle %d's Units: %d and %d's Units: %d" %(geni,unitsI,genj,unitsJ)
    updateGenTable(geni,unitsI)
    updateGenTable(genj,unitsJ)
    #update unit numbers and go on to next battle

def round(r,matrix):
    print "Battle Round",r
    for i in range(0,5):
        #general i's row 
        for j in range(0,5):
            if matrix[i][j] == 1:
                print "%d is attacking %d" %(i,j)
                #geni is attacking genj
                #need to see if genj is attacking geni
                if matrix[j][i] == 1:
                    #matrix[j][i] = 0
                    #matrix[i][j] += 1
                    print "Duel Attacking Battle"
                    battle(i,j,True,True,1)
                else:
                    battle(i,j,True,False,0)     #right Now We will have two different battle is both attacking
    updateUnits()

def getDefend(col):
    sums = 0
    for i in matrix:
        sums += i[col]  
    return sums

def getEngaged(row):
    sums = 0
    for i in range(0,5):
        sums += matrix[row][i]
    return sums

a = [0,0,0,0,0]
b = [0,0,0,0,0]
c = [0,0,0,0,0]
d = [0,0,0,0,0]
e = [0,0,0,0,0]
matrix = [a,b,c,d,e]

''' Rouund Descisions '''
dec1 = "Gen1 attacks Gen 2"
dec2 = "Geb2 passes round"
dec3 = "Gen3 attack Gen4"
dec4 = "Gen4 attack Gen3"
dec5 = "Gen 5 passes round"

matrix [0][1] = 1
matrix [2][3] = 1
matrix [3][2] = 1
printMatrix(1)
round(1,matrix)


print GenTable
'''Pause here'''
'''Round 2 Descisions'''

dec1 = "Gen1 attacking gen2"
dec2 = "Gen2 attacking gen1"
dec3 = "Gen3 attacking gen1"
dec4 = "Gen4 is passing"
dec5 = "Gen5 attacking gen3"

matrix [0][1] = 1
matrix [1][0] = 1
matrix [2][0] = 1
matrix [4][2] = 1
printMatrix(2)
round(2,matrix)



print GenTable



