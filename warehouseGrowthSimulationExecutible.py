# to create the exe version do the following in the console
    # cd C:\Users\Daniel Schwartz\AppData\Local\Programs\Python\Python39\    
    # pyinstaller warehouseGrowthSimulationExecutible.py -F -w -n FC_Network_Growth_Simulation_v001
    # see here for the pyinstaller docs: https://pyinstaller.readthedocs.io/en/stable/usage.html
    
import tkinter as tk
import tkinter.filedialog
import os
import timeit
import pandas as pd
import numpy as np
from numpy import mean
import networkx as nx
from collections import defaultdict
from collections import deque
import matplotlib.pyplot as plt
from scipy.stats import expon, poisson, gamma, norm
import re
import tabulate

def runSim(simYears,splitWeeks,maxFull,splitIncrease,stockWeeks,cycleWeeks,growthChoice,runChoice,saveTo,costChoice,percFull):

    #########################
    ###formatting settings###
    #########################

    plt.rcParams['figure.figsize'] = [15, 10]
    pd.options.display.float_format = '{:,.2f}'.format

    #######################
    ###utility functions###
    #######################

    #make a list unique by turning it into a dictionary and then back to a list
    def uniqueList(x):
        return list(dict.fromkeys(x))

    #remove x from list y
    def removeFromList(x,y):
        y = [s for s in y if s != x]
        return y

    ########################
    ###initial parameters###
    ########################
    saveTo = saveTo
    cogsPerCuFt = costChoice
    # dollarsPerSqFt = 125
    # cogsPerSqFt = 50
    # rackingMultiplier = 2.5
    whsUsage = percFull

    #####################
    ###setup functions###
    #####################

    #set the initial conditions for zones, warehouses and balances
    def setInitialConditions():
        #current OH, last OH and Order Quantity from Warehouse Space Forecast documents, split by regional contribution from Network Analysis presentation
        warehouseData = {
            #'index':['Capacity','Current OH', 'Last Period OH', 'Order Quantity', 'Cumulative OH', 'Cumulative Sales','Rent per Week','Average Labour Cost per Week','Zone Sales', 'Secondary Warehouses','Region','Outbound Mean and SD'],
            '1' : [600000.0, 600000.0*whsUsage, 0, 0, 0, 0, (1.0/4),(170.0*30), 0, ['6'],'Eastern Canada', [20000,7000],
            '2' : [400000.0, 400000.0*whsUsage, 0, 0, 0, 0, (1.5/4),(160.0*30), 0, ['3'],'North West USA', [25000,8000]],
            '3' : [700000.0, 700000.0*whsUsage, 0, 0, 0, 0, (1.1/4),(160.0*30), 0, ['2'],'South West USA', [50000,12500]],
            '4' : [800000.0, 800000.0*whsUsage, 0, 0, 0, 0, (1.0/4),(150.0*30), 0, ['5'],'North East USA', [50000,15000]],
            '5' : [700000.0, 700000.0*whsUsage, 0, 0, 0, 0, (0.4/4),(140.0*30), 0, ['4'],'South East USA', [50000,12500]],
            '6' : [200000.0, 200000.0*whsUsage, 0, 0, 0, 0, (1.2/4),(180.0*30), 0, ['1'],'Western Canada', [8000,3000]],
            '7' : [600000.0, 600000.0*whsUsage, 0, 0, 0, 0, (0.7/4),(140.0*30), 0, ['8'],'South Central USA',[10000,4000]],
            '8' : [400000.0, 400000.0*whsUsage, 0, 0, 0, 0, (0.7/4),(160.0*30), 0, ['7'],'North Central USA',[10000,4000]]
        }

        balanceSheet = {
            'Expenditure':0,
            'Transportation':0,
            'Labour':0,
            'Rent':0,
            'Inventory':0,
            'Revenue':0,
            'Profit':0
        }

        whs = {
           }

        originalCapacity = {
            '1' : 600000.0,
            '2' : 400000.0,
            '3' : 700000.0,
            '4' : 800000.0,
            '5' : 700000.0,
            '6' : 200000.0,
            '7' : 600000.0,
            '8' : 400000.0
        }

        orderBook = {}
        
        wsr = {}

        return warehouseData, balanceSheet, whs, originalCapacity, orderBook, wsr
    
    #use intial setup data to create the dictionary that stores the warehouses and all their information 
    def buildInitialNetwork():
        for i in warehouseData.keys():
            # secondarySalesAnnual = 0
            try:
                whsName = warehouseData[i][10]
                whsSales = 0 # weekly sales
                whsOO = warehouseData[i][3] # on water POs
                whsOH =  warehouseData[i][1] # current OH
                whsCapacity =  warehouseData[i][0] # 85% of total warehouse space * COGS per sq. ft.
                pZone = [i]
                sZone = warehouseData[i][9]
                whsType = 'FC'
                calcTurns = 0
                overCapacityWeeks = 0

                whs[i] = [whsName, whsCapacity, whsOH, whsSales, whsOO, pZone, sZone, whsType, calcTurns, overCapacityWeeks]

            except:
                pass

    ##########################
    ###simulation functions###
    ##########################

    def expon_sales(mean,sd):
        # x = expon.rvs(loc=0,scale=29984.0)
        # x = poisson.rvs(mu=34)*1000
        # x = gamma.rvs(272.9,loc=-609101.3,scale=3055.1)
        mean, sd = mean, sd
        outbound = norm.rvs(mean, sd)

        whsOutbound = round(abs(outbound),0)
        return whsOutbound

    def shocker():
        shockWave = norm.rvs(10000.0, 1000.0)
        
        shockWave = round(shockWave,0)

        if shockWave % 13==0.0:
            inShock = 1
        else:
            inShock = 0

        if shockWave % 17==0.0:
            outShock = 1
        else:
            outShock = 0

        return [inShock, outShock]

    # def expon_inbound(growth):
        #     # x = expon.rvs(loc=0,scale=222375.0)
        #     # x = poisson.rvs(mu=3)
        #     # x = gamma.rvs(54.4,loc=-1165214.8,scale=29473.6)
        #     inbound = norm.rvs(70000.0, 30270.5)

        #     whsInbound = round(abs(inbound),0)
        #     return whsInbound

    #subratract weekly sales from OH
    def sales(outShock):
        for i in whs.keys():
            whsOutbound = expon_sales(warehouseData[i][11][0],warehouseData[i][11][1])
            pm = np.array([+1, -1])
            randBinary = np.random.choice([0,1])
            if outShock == 1: #whsOutbound % 10 == 0: #this skips a week of sales, simulating a disruption, if the outabound amount is divisible by 10 (about 9% of weeks)
                whsOutbound = whsOutbound*(pm[randBinary]*1.10)
            # print(['outbound',whsOutbound])
            try:
                currentOH = warehouseData[i][1] # get current on hand
                if currentOH <=0:
                    whsSales=0
                else:
                    whsSales = whsOutbound #np.ceil(whsOutbound) # weekly forecasted sales = random draw from distribution
                    updateOH = currentOH - whsOutbound
                    whs[i][2] = updateOH # whsOH = current on hand - fulfilled demand
                    warehouseData[i][2] = currentOH # update last period OH
                    warehouseData[i][1] = updateOH #update current on hand to account for sales
                    whs[i][3] = whsSales # update weekly sales
                    warehouseData[i][5] = warehouseData[i][5] + whsSales # update cumulative sales
                    warehouseData[i][8] = whsSales*52 # update annual sales
                    balanceSheet['Revenue'] = balanceSheet['Revenue'] + whsSales*cogsPerCuFt* (1 + margin)
            except:
                pass
            
    # this is code for a different order policy (order if oh < safety stock)
    # def orders(year,week,growth,inShock):
        # for i in whs.keys():
        #     whsInbound = expon_inbound(growth)
        #     # print(['inbound',whsInbound])
        #     maxSales = 85000
        #     medianSales = growth*31000
        #     pm = np.array([+1, -1])
        #     randBinary = np.random.choice([0,1])
        #     if inShock==1: #whsInbound % 17 == 0: #this is a "random" positive or negative shock that amplifies the inbound quantity (occurs in around 6.5% of weeks)
        #         whsInbound = whsInbound*1.20 #(pm[randBinary]*1.20)
        #     try:
        #         currentOH = warehouseData[i][1]
        #         sales = whs[i][3]
        #         safetyStock = 12*medianSales #maxSales - medianSales # np.ceil((sales * 1.15) - sales) # OR forecast * max error - forecast (ideally: (max sales per week * max leadtime weeks) - (average sales per week * average leadtime weeks)
        #         orderQuantity = whsInbound #np.ceil(whsInbound) # order = random draw from distribution
        #         #leadtimeSS = whs[i][3] * 4 # sales between order and arrival (assumes 30 day leadtime from order)
        #         orderPoint = safetyStock #+  leadtimeSS #if warehouse OH is greater than 1% of warehouse capacity, do not replenish inventory            # print([whs[i][2],orderPoint])
        #         if currentOH > orderPoint: #if OH is greater than the order point, don't order.
        #             pass
        #         else:
        #             warehouseData[i][3] = orderQuantity
        #             whs[i][4] = orderQuantity
        #             warehouseData[i][1] = currentOH + orderQuantity # new OH = current OH + on order 
        #             warehouseData[i][2] = currentOH # update last period on hand
        #             whs[i][2] = warehouseData[i][1]
        #             whs[i][8] = warehouseData[i][8] / ((warehouseData[i][2] + warehouseData[i][1]) / 2) # calculated turns = warehouse demand / OH
        #             warehouseData[i][4] = warehouseData[i][4] + warehouseData[i][3]
        #             balanceSheet['Expenditure'] = balanceSheet['Expenditure'] + orderQuantity*cogsPerCuFt
        #     except:
        #         pass

    #current order policy (periodic order policy)
    def orderCreator(j,lt,oc):
        for i in whs.keys():
            safetyStockSales = expon_sales(warehouseData[i][11][0],warehouseData[i][11][1])
            while safetyStockSales < warehouseData[i][11][0]-warehouseData[i][11][1] or safetyStockSales > warehouseData[i][11][0]+warehouseData[i][11][1]:
                safetyStockSales = expon_sales(warehouseData[i][11][0],warehouseData[i][11][1])

            forecastedSales = expon_sales(warehouseData[i][11][0],warehouseData[i][11][1])
            while forecastedSales < warehouseData[i][11][0]-warehouseData[i][11][1] or forecastedSales > warehouseData[i][11][0]+warehouseData[i][11][1]: 
                forecastedSales = expon_sales(warehouseData[i][11][0],warehouseData[i][11][1])

            safetyStock = weeksOfSafety*safetyStockSales

            try:
                coh = warehouseData[i][1]
                pm = np.array([+1, -1])
                randBinary = np.random.choice([0,1])

                eta = j + lt

                relevantOrders = []
                for x in orderBook.keys():
                    if i in orderBook[x].keys():
                        if x > j and x <= eta + oc:
                            relevantOrders.append(orderBook[x][i])
                    else:
                        pass

                arrivalOH = coh - lt*safetyStockSales + np.sum(relevantOrders) #current on hand after this weeks sales - sales during leadtime + orders arriving between order date and (eta date + 1 order cycle)
                orderQuantity =  safetyStock - arrivalOH + forecastedSales

                order = [eta + pm[randBinary]*poisson.rvs(1),orderQuantity,i] #Actual ETA shifts by +/- a few weeks, based on samples drawn from a poisson distribution with a mean of 1
                if order[1] <= 0: #if the calculated order is negative, order nothing
                    order[1] = 0
                thisOrder = {order[2]:order[1]}
                if order[0] in orderBook.keys():
                    orderBook[order[0]].update(thisOrder)
                else:
                    orderBook[order[0]]=thisOrder
            except:
                pass

    def receiveInventory(j):
        for i in whs.keys():  
            try:
                warehouseData[i][1] = warehouseData[i][1]+orderBook[j][i]
                warehouseData[i][3] = orderBook[j][i]
                whs[i][4] = orderBook[j][i]
                whs[i][2] = warehouseData[i][1]
                whs[i][8] = warehouseData[i][8] / ((warehouseData[i][2] + warehouseData[i][1]) / 2) # calculated turns = warehouse demand / OH
                warehouseData[i][4] = warehouseData[i][4] + warehouseData[i][3]
                balanceSheet['Inventory'] = balanceSheet['Inventory'] + orderBook[j][i]*cogsPerCuFt
                balanceSheet['Expenditure'] = balanceSheet['Expenditure'] + orderBook[j][i]*cogsPerCuFt
            except:
                pass

    def fill_balancer():
        df_balancer = pd.DataFrame.from_dict(warehouseData,orient="index")
        df_balancer = df_balancer[df_balancer.columns[0:2]]
        df_balancer.rename(columns = {0:'capacity',1:'value'},inplace=True)
        df_balancer['capacity'] = df_balancer['capacity'] * maxFull
        len = df_balancer.shape[0]
        df_balancer['target']=df_balancer.capacity/df_balancer.capacity.sum()
        df_balancer['actual']=df_balancer.value/df_balancer.value.sum()
        df_balancer['delta'] = df_balancer.target - df_balancer.actual
        df_balancer['changeBy'] = round(df_balancer.value.sum()*df_balancer.delta)
        return df_balancer

    #stock transfer proxy, rebalance warehouses
    def balancer(cost):
        balanceCheck = {'previous':0,'current':1}
        transferCost = cost
        rebalanceChecker = pd.DataFrame.from_dict(whs,orient="index")
        rebalanceChecker = rebalanceChecker[rebalanceChecker.columns[9:10]]
        rebalanceChecker.rename(columns={9:'weeksOver'},inplace=True)
        check = rebalanceChecker['weeksOver'].max()
        # print('Check: {}\n'.format(check),file=open(saveTo+'/FullSim.txt', "a"))
        # print('Houston OverCapacity Weeks = {}\n'.format(whs['7'][9]),file=open(saveTo+'/FullSim.txt', "a"))
        balanceSheet['Transportation'] = 0
        if check == 4 or check == 8:
            df_balancer = fill_balancer()
            while balanceCheck['current'] != balanceCheck['previous']:
                max = df_balancer['changeBy'] == df_balancer.changeBy.max()
                min = df_balancer['changeBy'] == df_balancer.changeBy.min()
                adjuster = df_balancer.changeBy.min()

                balanceSheet['Transportation'] += abs(adjuster)

                df_balancer['value'] = df_balancer['value'].where(max, df_balancer['value'] + adjuster)
                df_balancer['value'] = df_balancer['value'].where(min, df_balancer['value'] - adjuster)
                df_balancer['actual'] = df_balancer.value/df_balancer.value.sum()
                df_balancer['delta'] = df_balancer.target - df_balancer.actual
                df_balancer['changeBy'] = round(df_balancer.value.sum()*df_balancer.delta)
                balanceCheck['previous'] = balanceCheck['current']
                balanceCheck['current'] = round(df_balancer.changeBy.abs()).sum()

            balanceSheet['Transportation'] = round(balanceSheet['Transportation']/4000)*transferCost
            balancedInv = df_balancer.value.mean()
            # print('Balancer:\n{}\n'.format(df_balancer),file=open(saveTo+'/FullSim.txt', "a")) 
            for key in warehouseData.keys():
                warehouseData[key][2]=warehouseData[key][1]
                warehouseData[key][1]=balancedInv
                whs[key][2] = warehouseData[key][1]

    #if the warehouse is overcapacity, create a new warehouse and a new zone and split the sales and inventory evenly
    def overCapacity(year,week):
        keys = [str(item) for item in  list(range(1,len(warehouseData.keys())+1))]
        for i in keys:
            try:
                if warehouseData[i][1] < warehouseData[i][0]*maxFull and whs[i][9] > 0:
                    whs[i][9] -= 1
                    pass
                elif whs[i][9] >= overCapacityLimit:
                    warehouseData[i][0] = warehouseData[i][0]*capacityIncrease
                    whs[i][1] = whs[i][1]*capacityIncrease
                    wsr.setdefault(warehouseData[i][10],[]).append(year * 52 + week - 52)
                    whs[i][9] = 0
                else:
                    whs[i][9] += 1
            except:
                pass
        
    #########################
    ###reporting functions###
    #########################
    #ensure there is a folder of the user's drive to save charts into
    def makeDir():
        user = os.getlogin()
        if not os.path.exists(f'C:\\Users\\{user}\\Desktop\\SimCharts'):
            os.makedirs(f'C:\\Users\\{user}\\Desktop\\SimCharts')
            
    #get the warehouses that split and how many times they split (average over all simulations)
    def splitTracking():
        whsSplitTrackerStage = defaultdict(list)
        for key in wsr.keys():
            x = list(wsr[key])
            x = len(x)
            try:
                whsSplitTrackerStage[key].append(x)       
            except:
                pass
        
        for key in whsSplitTrackerStage.keys():
            averageSplits = round(np.array(whsSplitTrackerStage[key]).mean(),0)
            whsSplitTrackerStageTwo[key].append(averageSplits)

    def splitReporting():
        whsCapacityTrackerStage = {}
        for key in whsSplitTrackerStageTwo.keys():
            whsSplitTracker[key] = [round(np.array(whsSplitTrackerStageTwo[key]).mean(),0)]

        for key in whsCapacityTracker.keys():
            avgTotalCapacity = [round(np.array(whsCapacityTracker[key]).mean()/2.2,0)]
            whsCapacityTrackerStage[warehouseData[key][10]] = avgTotalCapacity

        whsCapacities = pd.DataFrame.from_dict(whsCapacityTrackerStage,orient="index",columns=["Average Final Sq. Ft. Capacity"])
        whsCapacities.reset_index(inplace=True)
        whsSplits = pd.DataFrame.from_dict(whsSplitTracker,orient="index",columns=["Average Count of Over-Capacity Splits"])
        whsSplits.reset_index(inplace=True)
        # print('{}\n'.format(whsCapacities),file=open(saveTo+'/FullSim.txt', "a"))
        # print('{}\n'.format(whsSplits),file=open(saveTo+'/FullSim.txt', "a"))
        whsSplits = whsSplits.set_index('index').join(whsCapacities.set_index('index'))
        whsSplits.sort_values(by=["Average Count of Over-Capacity Splits"], inplace=True, ascending = False)
        # print('{}\n'.format(whsSplits),file=open(saveTo+'/FullSim.txt', "a"))
        
        return whsSplits

    #plot the week when a new warehouse was created
    def createDateTracking():
        for key in wsr.keys():
            for j in range(len(wsr[key])):
                createDateTrackingStage[key].append(wsr[key][j])

    def warehouseCreateDate():
        
        fig, ax = plt.subplots(figsize=(12, 8))
        x = defaultdict(list)
        warehouseRegion = []
        week = []
        # for k in range(len(simNewWarehouseLocation)):
        
        for key in createDateTrackingStage.keys():
            for i in createDateTrackingStage[key]:
                warehouseRegion.append(key)
                week.append(i) #/52)
        dfWhs = pd.DataFrame(set(warehouseRegion),columns = ['warehouse'])

        year_dummy = list(range(1,years+1))
        quarter_dummy = list(range(1,5))
        crt_prd = ['Y'+str(x)+'Q'+str(y) for x in year_dummy for y in quarter_dummy]
        df1 = pd.DataFrame(crt_prd, columns = ['year_quarter'])

        chartDF = df1.merge(dfWhs,how='cross')

        zipped = list(zip(warehouseRegion, week))
        df = pd.DataFrame(zipped, columns = ['warehouse','week'])
        df['quarter'] = df.week.div(16).apply(np.ceil)
        df.quarter = df.quarter.div(years).apply(np.ceil).map(int)
        df['year'] = df.week.div(52).apply(np.ceil).map(int)
        df['year_quarter'] = 'Y'+df.year.map(str)+'Q'+df.quarter.map(str)
        splitsDF = df.groupby(['warehouse','year_quarter'])['week'].count().reset_index()

        chartDF = chartDF.merge(splitsDF,how='left', on = ['warehouse','year_quarter'])

        x = np.arange(len(chartDF.year_quarter.unique()))
        bar_width = 0.15
        try:
            b1 = ax.bar(x,chartDF.loc[chartDF['warehouse']=='North East USA','week'],width=bar_width, label='North East USA')
        except:
            pass
        try:
            b2 = ax.bar(x + bar_width,chartDF.loc[chartDF['warehouse']=='North West USA','week'],width=bar_width, label='North West USA')
        except:
            pass
        try:
            b3 = ax.bar(x + bar_width*2,chartDF.loc[chartDF['warehouse']=='South East USA','week'],width=bar_width, label='South East USA')
        except:
            pass
        try:
            b4 = ax.bar(x + bar_width*3,chartDF.loc[chartDF['warehouse']=='South West USA','week'],width=bar_width, label='South West USA')
        except:
            pass
        try:
            b5 = ax.bar(x+bar_width,chartDF.loc[chartDF['warehouse']=='South Central USA','week'],width=bar_width, label='South Central USA')
        except:
            pass
        try:
            b6 = ax.bar(x+bar_width,chartDF.loc[chartDF['warehouse']=='Eastern Canada','week'],width=bar_width, label='Eastern Canada')
        except:
            pass
        try:
            b7 = ax.bar(x + bar_width*4,chartDF.loc[chartDF['warehouse']=='Western Canada','week'],width=bar_width, label='Western Canada')
        except:
            pass

        # Fix the x-axes.
        ax.set_xticks(x + bar_width*2)
        ax.set_xticklabels(chartDF.year_quarter.unique())
        ax.legend()

        # Axis styling.
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#EEEEEE')
        ax.xaxis.grid(False)

        # Add axis and chart labels.
        ax.set_xlabel('Year and Quarter of Split', labelpad=15)
        ax.set_ylabel('# of Times Split', labelpad=15)
        ax.set_title('Timing of Warehouse Splits Due to Capacity Overage', pad=15)

        fig.tight_layout()
        plt.savefig(saveTo+'/warehouseCreateDate',dpi=fig.dpi)
        # plt.show()

    #calculate cost of running the warehouses each week
    def warehouseCosts():
        cost = 0.0
        for i in warehouseData.keys():
            try:
                labour = warehouseData[i][6]
                rent = warehouseData[i][7]
                cost = cost + labour + rent
            except:
                pass
        balanceSheet['Labour'] = balanceSheet['Labour'] + labour
        balanceSheet['Rent'] = balanceSheet['Rent'] + rent
        balanceSheet['Expenditure'] = balanceSheet['Expenditure'] + round(cost,2)

    #collect data on warehosue inventory, costs and revenues for each warehouse        
    def dataCollector():
    
        for key in warehouseData.keys():
                rawDataOH[key].append(warehouseData[key][1])

        for key in warehouseData.keys():
                rawDataCost[key].append(warehouseData[key][3]*cogsPerCuFt + warehouseData[key][0]*warehouseData[key][6] + warehouseData[key][7])

        for key in warehouseData.keys():
                rawDataRent[key].append(warehouseData[key][0]*warehouseData[key][6])

        for key in warehouseData.keys():
                rawDataLabour[key].append(warehouseData[key][7])
        
        for key in warehouseData.keys():
                rawDataInventory[key].append(warehouseData[key][3]*cogsPerCuFt)        

        for key in warehouseData.keys():
                rawDataRevenue[key].append(whs[key][3]*cogsPerCuFt*(1 + margin))

        for key in whs.keys():
                rawDataCalcTurns[key].append(whs[key][8])
        
        for key in warehouseData.keys():
            rawDataTransportation[key].append(balanceSheet['Transportation']/len(warehouseData.keys()))


    def simDataCollector(year,tries):
        dataSources = [rawDataOH,rawDataCost,rawDataRevenue,rawDataCalcTurns,rawDataRent,rawDataLabour,rawDataInventory,rawDataTransportation]
        weeks = year*52
        tries = str(tries)
        warehouseList = {}
        for x in list(range(len(dataSources))):
            for key in dataSources[x]:
                simList = 'try_'+tries+'_'+key
                simList = np.array(dataSources[x][key])
                padWidth = weeks - len(simList)
                simList = np.pad(simList,(0,padWidth),mode='empty')

                if x == 0:
                    listOfArrays_0[key].append(simList)
                elif x == 1:
                    listOfArrays_1[key].append(simList)
                elif x == 2:
                    listOfArrays_2[key].append(simList)
                elif x == 3:
                    listOfArrays_3[key].append(simList)
                elif x == 4:
                    listOfArrays_4[key].append(simList)
                elif x == 5:
                    listOfArrays_5[key].append(simList)
                elif x == 6:
                    listOfArrays_6[key].append(simList)                 
                else:
                    listOfArrays_7[key].append(simList)

    #present collected data as line charts, grouped by warehouse    
    def collectedDataCharts():
        
        for key in listOfArrays_0.keys():
            averageOH = np.nanmean(listOfArrays_0[key],axis=0)
            OH95 = np.nanpercentile(listOfArrays_0[key],97.5,axis=0),np.nanpercentile(listOfArrays_0[key],2.5,axis=0)
            
            averageCost = np.nanmean(listOfArrays_1[key],axis=0)
            Cost95 = np.nanpercentile(listOfArrays_1[key],97.5,axis=0),np.nanpercentile(listOfArrays_1[key],2.5,axis=0)
            
            averageRevenue = np.nanmean(listOfArrays_2[key],axis=0)
            Revenue95 = np.nanpercentile(listOfArrays_2[key],97.5,axis=0),np.nanpercentile(listOfArrays_2[key],2.5,axis=0)
            
            averageTurns = np.nanmean(listOfArrays_3[key],axis=0)
            Turns95 = np.nanpercentile(listOfArrays_3[key],97.5,axis=0),np.nanpercentile(listOfArrays_3[key],2.5,axis=0)
            
            averageRent = np.nanmean(listOfArrays_4[key],axis=0)
            Rent95 = np.nanpercentile(listOfArrays_4[key],97.5,axis=0),np.nanpercentile(listOfArrays_4[key],2.5,axis=0)
            
            averageLabour = np.nanmean(listOfArrays_5[key],axis=0)
            Labour95 = np.nanpercentile(listOfArrays_5[key],97.5,axis=0),np.nanpercentile(listOfArrays_5[key],2.5,axis=0)
            
            averageInventory = np.nanmean(listOfArrays_6[key],axis=0)
            Inventory95 = np.nanpercentile(listOfArrays_6[key],97.5,axis=0),np.nanpercentile(listOfArrays_6[key],2.5,axis=0)

            averageTransportation = np.nanmean(listOfArrays_7[key],axis=0)
            Transportation95 = np.nanpercentile(listOfArrays_7[key],97.5,axis=0),np.nanpercentile(listOfArrays_7[key],2.5,axis=0)

            week = list(range(1,(years*52)+1))

            year_dummy = list(range(1,years+1))
            quarter_dummy = list(range(1,5))
            crt_prd = ['Y'+str(x)+'Q'+str(y) for x in year_dummy for y in quarter_dummy]
            df1 = pd.DataFrame(crt_prd, columns = ['year_quarter'])

            fig, (ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax8) = plt.subplots(8,figsize=(25, 20))
            x_axis=np.arange(1,max(week)+1,13.00357)

            
            ax1.plot(week,averageOH,color='black',linewidth=3)
            for i in warehouseData.keys():
                if i==key:
                    oCapacity = originalCapacity[i]*maxFull
                    avgTotalCapacity = round(np.array(whsCapacityTracker[i]).mean(),0)
                    capacity = avgTotalCapacity
                else:
                    pass
            ax1.axhline(y=oCapacity,color='black',linestyle='--')
            ax1.axhline(y=capacity,color='red',linestyle='--')
            ax1.fill_between(week, OH95[1], OH95[0], color='grey', alpha=0.5)
            ax1.set_title('Aggregated Data for ' + whs[str(key)][0] + ' Warehouse',y=1.01)
            ax1.set_ylabel('Average On Hand Inventory')
            ax1.set_xticks(x_axis)
            ax1.set_xticklabels(df1.year_quarter.unique())
            ax1.grid()

            ax2.plot(week,averageCost,color='black',linewidth=3)
            ax2.fill_between(week, Cost95[1], Cost95[0], color='grey', alpha=0.5)
            ax2.set_ylabel('Total Cost')
            ax2.sharex(ax1)
            ax2.grid()

            ax3.plot(week,averageRent,color='black',linewidth=3)
            ax3.fill_between(week, Rent95[1], Rent95[0], color='grey', alpha=0.5)
            ax3.set_ylabel('Cost of Rent')
            ax3.sharex(ax1)
            ax3.grid()            
            
            ax4.plot(week,averageLabour,color='black',linewidth=3)
            ax4.fill_between(week, Labour95[1], Labour95[0], color='grey', alpha=0.5)
            ax4.set_ylabel('Cost of Labour')
            ax4.sharex(ax1)
            ax4.grid()

            ax5.plot(week,averageInventory,color='black',linewidth=3)
            ax5.fill_between(week, Inventory95[1], Inventory95[0], color='grey', alpha=0.5)
            ax5.set_ylabel('Cost Of Inventory')
            ax5.sharex(ax1)
            ax5.grid()

            ax6.plot(week,averageTransportation,color='black',linewidth=3)
            ax6.fill_between(week, Transportation95[1], Transportation95[0], color='grey', alpha=0.5)
            ax6.set_ylabel('Cost of Stock Transfers')
            ax6.sharex(ax1)
            ax6.grid()

            ax7.plot(week,averageRevenue,color='black',linewidth=3)
            ax7.fill_between(week, Revenue95[1], Revenue95[0], color='grey', alpha=0.5)
            ax7.set_ylabel('Revenue')
            ax7.sharex(ax1)
            ax7.grid()

            ax8.plot(week,averageTurns,color='black',linewidth=3)
            ax8.fill_between(week, Turns95[1], Turns95[0], color='grey', alpha=0.5)
            ax8.set_xlabel('Weeks Since Warehouse Creation')
            ax8.set_ylabel('Weekly Calculated Turns')
            ax8.sharex(ax1)
            ax8.grid()
            
            fig.tight_layout()

            plt.savefig(saveTo+'/warehouse_'+whs[str(key)][0],dpi=fig.dpi)
            # plt.show()

    def growthList(year,rate):
        dGrowthAnnual = []
        if growthChoice == 101:
            rate = 0.5
        elif growthChoice == 103:
            rate = 0.25
        else:
            rate = 0.45

        for x in list(range(simYears)):
            dGrowthAnnual.append(rate)

        return dGrowthAnnual

    def money():
        moneyList = []
        for key in listOfArrays_0.keys():  
            averageCost = np.nanmean(listOfArrays_1[key],axis=0)
            totalCost = np.nansum(averageCost)

            averageRevenue = np.nanmean(listOfArrays_2[key],axis=0)
            totalRevenue = np.nansum(averageRevenue)

            averageRent = np.nanmean(listOfArrays_4[key],axis=0)
            totalRent = np.nansum(averageRent)

            averageLabour = np.nanmean(listOfArrays_5[key],axis=0)
            totalLabour = np.nansum(averageLabour)

            averageInventory = np.nanmean(listOfArrays_6[key],axis=0)
            totalInventory = np.nansum(averageInventory)

            averageTransportation = np.nanmean(listOfArrays_7[key],axis=0)
            totalTransportation = np.nansum(averageTransportation)
            
            # moneyList.append([whs[key][0],round(averageRevenue.sum() - averageCost.sum(),2),round(averageRevenue.sum(),2),round(averageCost.sum(),2),round(averageInventory.sum(),2),round(averageRent.sum(),2),round(averageLabour.sum(),2),round(averageTransportation.sum(),2)])
            moneyList.append([whs[key][0],round(totalRevenue,2),round(totalCost,2),round(totalInventory,2),round(totalRent,2),round(totalLabour,2),round(totalTransportation,2)])
        df = pd.DataFrame(moneyList,columns=['Warehouse','Revenue','Total_Cost','Inventory','Rent','Labour','Transportation']).set_index('Warehouse')
        df.style.format({'Revenue': '${:20,.0f}', 
                          'Total_Cost': '${:20,.0f}',
                          'Inventory':'${:20,.0f}',
                          'Rent':'${:20,.0f}',
                          'Labour':'${:20,.0f}',
                          'Transportation':'${:20,.0f}'})
        return df

    def growth(rate):
        for i in warehouseData.keys():
            warehouseData[i][11][0] = warehouseData[i][11][0] + warehouseData[i][11][0]*rate

    def capacity():
        for key in warehouseData.keys():
                whsCapacityTracker[key].append(warehouseData[key][0]*maxFull)

    ###########################
    ###simulation parameters###
    ###########################

    maxFull  = maxFull #If warehouse OH > warehouse capacity * maxFull, a new warehouse is created
    m = 0 # choose first element of dGrowthAnnual list
    splitNew = 0.5 #percentage split of over-capacity zone's demand that goes to the new warehouse
    splitOld = 1 - splitNew #remaining demand for an over-capacity zone that has been split
    margin = 0.5 #Gross Margin %
    overCapacityLimit = splitWeeks
    years = simYears #number of years of network change to simulate
    leadtime = 2 # Since we order every 2 weeks, for the purpose of the simulation after the first leadtime period, the leadtime if effectively 2 weeks
    ordercycle = cycleWeeks #order cycle in weeks
    weeksOfSafety = stockWeeks #always have this many weeks of sales available (weeks of safety stock)
    transferCost = 3000
    dGrowthAnnual = growthList(simYears, growthChoice)
    capacityIncrease = splitIncrease #each split doubles capacity in the warehouse

    ##########################
    ###simulation variables###
    ##########################

    simWarehouseData = []
    simProfitList = []
    simRevenueList = []
    simExpenditureList = []

    whsSplitTrackerStageTwo = defaultdict(list)
    whsSplitTracker = defaultdict(list)
    whsCapacityTracker = defaultdict(list)
    createDateTrackingStage = defaultdict(list)

    listOfArrays_0 = defaultdict(list)
    listOfArrays_1 = defaultdict(list)
    listOfArrays_2 = defaultdict(list)
    listOfArrays_3 = defaultdict(list)
    listOfArrays_4 = defaultdict(list)
    listOfArrays_5 = defaultdict(list)
    listOfArrays_6 = defaultdict(list)
    listOfArrays_7 = defaultdict(list)

    tries = runChoice

    ##########################
    ###start the simulation###
    ##########################

    #run simulation
    startTime = timeit.default_timer()
    running = True
    for i in range(tries):
        warehouseData, balanceSheet, whs, originalCapacity, orderBook, wsr = setInitialConditions()
        buildInitialNetwork()
        rawDataRent = defaultdict(list)
        rawDataLabour = defaultdict(list)
        rawDataOH = defaultdict(list)
        rawDataCost = defaultdict(list)
        rawDataRevenue = defaultdict(list)
        rawDataCalcTurns = defaultdict(list)
        rawDataInventory = defaultdict(list)
        rawDataTransportation = defaultdict(list)

        overCapacity(0,0)
        for k in range(1,years+1):
            # dGrowthWeekly = dGrowthAnnual[m] ** (1 / 52) # annual growth in sales, converted to weekly growth
            if k > 1:
                dGrowth = dGrowthAnnual[m]
                growth(dGrowth)

            for j in range(1,53):
                week = k * 52 + j - 52
                
                # shocks = shocker()
                sales(0) # shocks[1])
                
                if j % 2==0:
                    orderCreator(week, leadtime, ordercycle)

                if week in orderBook.keys():
                    receiveInventory(week)

                # balancer(transferCost)
                overCapacity(k,j)
                # warehouseCosts()
                dataCollector()
                # print('Houston: {}\n'.format(warehouseData['7']),file=open(saveTo+'/FullSim.txt', "a"))
            m += 1

        simDataCollector(years,i)
        splitTracking()
        capacity()
        createDateTracking()
        newWarehouseCount = 0
        m = 0

        balanceSheet['Profit'] = balanceSheet['Revenue'] - balanceSheet['Expenditure']
        simProfitList.append(balanceSheet['Profit'])
        simRevenueList.append(balanceSheet['Revenue'])
        simExpenditureList.append(balanceSheet['Expenditure'])
        if i < tries-1:
            warehouseData.clear()
            balanceSheet.clear()
            whs.clear()
            originalCapacity.clear()
            orderBook.clear()
            wsr.clear()

    #simulation report preparation      
    aSimProfits = np.array(simProfitList)
    aSimRevenue = np.array(simRevenueList)
    aSimExpenditure = np.array(simExpenditureList)
    splitTracker = splitReporting()
    moneyDF = money()
    runtime = timeit.default_timer() - startTime
    

    #simulation report
    print('The {} year simulation ran {} times, taking about {:.2f} minutes.'.format(years,tries,runtime/60),file=open(saveTo+'/SimOutput.txt', "w"))
    print('The annual growth rate of demand for this analysis was {:.0%} per year, and FCs split after {} straight weeks being over-capacity.\nEach split increased FC capacity by {:.0%}.'.format(dGrowthAnnual[0],overCapacityLimit,capacityIncrease-1),file=open(saveTo+'/SimOutput.txt', "a"))
    print('\nThe breakdown of the Average Revenue and Expenditures for the simulation is as follows:',file=open(saveTo+'/SimOutput.txt', "a"))
    print(tabulate.tabulate(moneyDF, headers=['Warehouse','Revenue','Total_Cost','Inventory','Rent','Labour','Transportation'], tablefmt="pretty"),file=open(saveTo+'/SimOutput.txt', "a"))
    print('\nOn Average, FC space increased {:.0f} times.'.format(splitTracker["Average Count of Over-Capacity Splits"].sum()),file=open(saveTo+'/SimOutput.txt', "a"))
    print('This regional breakdown of over-capacity FCs is as follows:',file=open(saveTo+'/SimOutput.txt', "a"))
    print(tabulate.tabulate(splitTracker, headers=['Warehouse','Average Count of Over-Capacity Splits', 'Average Final Capacity'], tablefmt="pretty"),file=open(saveTo+'/SimOutput.txt', "a"))
    # warehouseCreateDate()
    collectedDataCharts()
    running = False

root = tk.Tk()
root.geometry("550x525")
root.title('FC Network Growth Simulation Setup')

topFrame = tk.Frame(root)
topFrame.pack(side=tk.TOP)

frame = tk.Frame(root)
frame.pack()

bottomFrame = tk.Frame(root)
bottomFrame.pack(side=tk.BOTTOM)

v = tk.IntVar()
v1 = tk.IntVar()

growthRates = [('Higher Growth (50% YoY)',101),
               ('Forecasted Growth (45% YoY)',102),
               ('Lower Growth (25% YoY)',103)]

runTime = [('Take ~30 seconds to Simulate Network Growth 100 times',100),
               ('Take ~5 minutes to Simulate Network Growth 1000 times',1000),
               ('Take longer to Simulate Network Growth 10000 times',10000)]

def createNewWindow(fileLoc):
    newWindow = tk.Toplevel()
    newWindow.title('Simulation Results')
    with open(fileLoc +'/SimOutput.txt') as f:
        contents = f.read()

    msg = tk.Text(newWindow,font=('Consolas', 11), width=130, height = 30)
    tk.Label(newWindow,text = 'Here are the results of your simulation.\nPlease click the Get Charts button to find the visual results.',font = "Helvetica 12 bold").pack(side=tk.TOP)
    msg.insert(tk.END, contents)
    msg.pack()

    chartsButton = tk.Button(newWindow,text='Get Charts', fg = 'black', font = "Helvetica 12 bold", command=lambda: getCharts(fileLoc))
    chartsButton.pack(side=tk.BOTTOM)

def entry_fields():
    simYears = int(e1.get())
    splitWeeks = int(e2.get())
    maxFull = float(e3.get())
    splitIncrease = float(e4.get())
    stockWeeks = int(e5.get())
    cycleWeeks = int(e6.get())
    costChoice = float(e7.get())
    percFull = float(e8.get())
    growthChoice = v.get()
    runChoice = v1.get()

    saveTo = tk.filedialog.askdirectory(title="Please Select a Folder")
    runSim(simYears,splitWeeks,maxFull,splitIncrease,stockWeeks,cycleWeeks,growthChoice,runChoice,saveTo,costChoice,percFull)
    createNewWindow(saveTo)

def getCharts(fileLoc):
        path = fileLoc
        path = os.path.realpath(path)
        os.startfile(path)

def quit():
        root.destroy()

tk.Label(topFrame,
        justify = tk.LEFT,
        pady = 5,
        text = 'Please Enter Your Simulation Parameters',
        font = "Helvetica 10 bold").pack(side=tk.TOP)

tk.Label(frame,
        text = 'How many years do you want to simulate?').grid(row=0)

tk.Label(frame,
        text = 'How many weeks before an Over Capacity Event?').grid(row=1)
        
tk.Label(frame,
        text = 'How full should the FC be before it is considered "Full"?').grid(row=2)

tk.Label(frame,
        text = 'By how much should capacity increase at each "Split"?').grid(row=3)

tk.Label(frame,
        text = 'How many weeks of Safety Stock should we hold?').grid(row=4)

tk.Label(frame,
        text = 'What is the Order Cycle Lead Time in Weeks?').grid(row=5)

tk.Label(frame,
        text = 'What is the Dollar Cost per CuFt?').grid(row=6)

tk.Label(frame,
        text = 'How full are the FCs at the start of the simulation?').grid(row=7)

e1 = tk.Entry(frame)
e2 = tk.Entry(frame)
e3 = tk.Entry(frame)
e4 = tk.Entry(frame)
e5 = tk.Entry(frame)
e6 = tk.Entry(frame)
e7 = tk.Entry(frame)
e8 = tk.Entry(frame)

e1.insert(10, "4")
e2.insert(10, "12")
e3.insert(10, "0.85")
e4.insert(10, "1.5")
e5.insert(10, "5")
e6.insert(10, "2")
e7.insert(10, "31.28")
e8.insert(10, "0.35")

e1.grid(row=0, column=1, pady=5)
e2.grid(row=1, column=1, pady=5)
e3.grid(row=2, column=1, pady=5)
e4.grid(row=3, column=1, pady=5)
e5.grid(row=4, column=1, pady=5)
e6.grid(row=5, column=1, pady=5)
e7.grid(row=6, column=1, pady=5)
e8.grid(row=7, column=1, pady=5)

growthLabel = tk.Label(bottomFrame,
        justify = tk.LEFT,
        pady = 5,
        text = 'Please Choose a Growth Path:',
        font = "Helvetica 10 bold").pack(side=tk.TOP)

x=0
for rate, val in growthRates:
    tk.Radiobutton(bottomFrame,
                    text = rate,
                    pady = 3,
                    variable = v,
                    value = val).pack(anchor=tk.W)
    x+=1

tk.Label(bottomFrame,
        justify = tk.LEFT,
        pady = 5,
        text = 'Choose a Runtime (NOTE: longer is more accurate):',
        font = "Helvetica 10 bold").pack(side=tk.TOP)

x=0
for time, val in runTime:
    tk.Radiobutton(bottomFrame,
                    text = time,
                    pady = 3,
                    variable = v1,
                    value = val).pack(anchor=tk.W)
    x+=1

v.set(102)
v1.set(100)

button = tk.Button(bottomFrame,text='Run Simulation', fg = 'green', font = "Helvetica 10 bold", command=entry_fields)
button.pack(side=tk.LEFT, pady = 5)

button2 = tk.Button(bottomFrame,text='Quit Simulation', fg = 'red', font = "Helvetica 10 bold", command=quit)
button2.pack(side=tk.RIGHT, pady = 5)
root.protocol("WM_DELETE_WINDOW", quit)
root.mainloop()
