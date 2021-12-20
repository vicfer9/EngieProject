

from flask import Flask
from flask_restful import Api, Resource, reqparse
import json
import itertools

app = Flask(__name__)
api = Api(app)

def clc(pwpList,  load):

    tmpList = sorted(pwpList, key=lambda d: d['€/MWh'])
    resDic = [{"name" : i['name'], "p" : 0} for i in tmpList]
    minMax = [(load, load)]
    arrMinMax= []

    #free nrj
    toAdd=[]
    for i in tmpList :
        if i['€/MWh']==0:
            minMax.append((round(minMax[-1][0]-i['pmax'],2), round(minMax[-1][1]-i['pmin'],2)))
            toAdd.append(i['name'])
        else : break

    newDic = {}

    for i in tmpList:
        newDic[i['name']] = (i['pmin'], i['pmax'], i['€/MWh'])

    del tmpList[:len(minMax)-1]
    del minMax[0]

    lstTmp=[]
    for i in tmpList :
        lstTmp.append(i['name'])
    a=testRec(lstTmp)

    sizeMM=len(minMax)
    for i in a:
        for j in i:
            minMax.append((round(max(minMax[-1][0]-newDic[j][1], 0),2), minMax[-1][1]-newDic[j][0]))
            if minMax[-1][0]==0 :
                arrMinMax.append((minMax[:],(tuple(toAdd) + i)))
                break
        del minMax[sizeMM:]
    arrMinMax.sort()
    tp=0
    newArr=[]
    for i in arrMinMax:
        if(i[0]!=tp):
            newArr.append(i)
        tp = i[0]
    lstTot = []

    for i in newArr :
        remLoad = load
        lstNew = []
        for j in i[1] :
            if j == i[1][-1]:
                minLoad = newDic[j][0]
                lstNew.append(max(remLoad,minLoad))
                remLoad = round(remLoad-minLoad, 2)
                for r in reversed(range(len(lstNew)-1)) :
                    if remLoad>=0 :
                        break
                    remLoad=round(remLoad+lstNew[r],2)
                    lstNew[r]= max(remLoad,0)
            else :
                lstNew.append(newDic[j][1])
                remLoad=round(remLoad-newDic[j][1],2)
        lstTot.append(lstNew)

    totList=[]
    for i in range(len(lstTot)):
        tot=0
        for j in range(len(lstTot[i])):
            tot+=lstTot[i][j]*newDic[newArr[i][1][j]][2]
        totList.append(tot)

    index_min = min(range(len(totList)), key=totList.__getitem__)
    finalDic = { newArr[index_min][1][i] : lstTot[index_min][i] for i in range(len(lstTot))}

    for i in resDic:
        for j in finalDic:
            if i['name']==j:
                i['p']=finalDic[j]
    return resDic

def testRec(lstTmp):
    stuff=lstTmp
    ls=[]
    for L in range(0, len(stuff) + 1):
        for subset in itertools.permutations(stuff, L):
            ls.append(subset)
    return ls

class productionPlan(Resource):
    def get(self):

        return "bite", 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('load', required=True)
        parser.add_argument('fuels', required=True)
        parser.add_argument('powerplants', action = 'append')
        args = parser.parse_args()
        load = [args['load']][0]
        fuelsTmp = [args['fuels']][0]
        powerplantsTemp = [args['powerplants']][0]

        temp_str = fuelsTmp.replace("\'","\"")
        fuels = json.loads(temp_str)
        fuels['gasfired'] = fuels.pop('gas(euro/MWh)')
        fuels['turbojet'] = fuels.pop('kerosine(euro/MWh)')
        fuels['windturbine'] = 0
        powerPlants=[]
        for i in range(len(powerplantsTemp)):
            temp_str = powerplantsTemp[i].replace("\'", "\"")
            powerPlants.append(json.loads(temp_str))
            if powerPlants[i]['type'] == "windturbine" :
                powerPlants[i]['pmax'] = round(powerPlants[i]['pmax']*fuels['wind(%)']/100, 2)
            powerPlants[i]['€/MWh'] = round(fuels[powerPlants[i]['type']] * (1/powerPlants[i]['efficiency']),2)

        #tmp=clc(powerPlants, float(load))
        #with open('data.json', 'w') as outfile:
        #    json.dump(tmp, outfile, indent=2)

        return json.dumps(clc(powerPlants, float(load)), indent=2), 201




api.add_resource(productionPlan, '/productionPlan')

if __name__ == '__main__':
    app.run(host='localhost',port=8888)
