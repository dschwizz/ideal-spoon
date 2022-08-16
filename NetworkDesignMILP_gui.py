# to create the exe version do the following in the console
    # cd C:\Users\Daniel Schwartz\AppData\Local\Programs\Python\Python39\    
    # pyinstaller articleNetworkDesignMILP_gui.py -F -w -n SCN_Optimizer_v001
    # see here for the pyinstaller docs: https://pyinstaller.readthedocs.io/en/stable/usage.html

#%%
import pulp as pu
import numpy as np
import pandas as pd
import numpy as np
import tkinter as tk
import tkinter.filedialog
import os
#%%
def milp(saveTo,demandForecast,SLgoal,FCmax,FCmin,dol_cuft,whs1,whs2,whs3,whs4,whs5,whs6,whs7,whs8,whs9,whs10,whs1_x,whs2_x,whs3_x,whs4_x,whs5_x,whs6_x,whs7_x,whs8_x,whs9_x,whs10_x,whs1_o,whs2_o,whs3_o,whs4_o,whs5_o,whs6_o,whs7_o,whs8_o,whs9_o,whs10_o,whs1_c,whs2_c,whs3_c,whs4_c,whs5_c,whs6_c,whs7_c,whs8_c,whs9_c,whs10_c):
    ports = ['Jacksonville','Long Beach','Seattle','New Jersey','Houston','Oakland','Norfolk']

    inbound_supply = {
    'Jacksonville':99999999,
    'Long Beach':99999999,
    'Seattle':99999999,
    'New Jersey':99999999,
    'Houston':99999999,
    'Oakland':99999999,
    'Norfolk':99999999
    }

    fc = ['EWR','JAX','IAH','LAX','SEA','STO','ORF','ORD','OAK','DEN']

    # f(x) = (3.5*x)**0.755 # inbound_trucks(sqft)
    inbound_capacity = {
    'EWR':(whs1 * 3.5)**0.755,
    'JAX':(whs2 * 3.5)**0.755, 
    'IAH':(whs3 * 3.5)**0.755, 
    'LAX':(whs4 * 3.5)**0.755, 
    'SEA':(whs5 * 3.5)**0.755, 
    'STO':(whs6 * 3.5)**0.755, 
    'ORF':(whs7 * 3.5)**0.755, 
    'ORD':(whs8 * 3.5)**0.755,
    'OAK':(whs9 * 3.5)**0.755,
    'DEN':(whs10 * 3.5)**0.755
    }
    
    expand_in_capacity = {
    'EWR':(whs1_x * 3.5)**0.755,
    'JAX':(whs2_x * 3.5)**0.755, 
    'IAH':(whs3_x * 3.5)**0.755, 
    'LAX':(whs4_x * 3.5)**0.755, 
    'SEA':(whs5_x * 3.5)**0.755, 
    'STO':(whs6_x * 3.5)**0.755, 
    'ORF':(whs7_x * 3.5)**0.755, 
    'ORD':(whs8_x * 3.5)**0.755,
    'OAK':(whs9_x * 3.5)**0.755,
    'DEN':(whs10_x * 3.5)**0.755
    }

    # f(x) = 0.164*x - 727 # outbound_trucks(sqft)
    outbound_capacity = {
    'EWR':(whs1 * 0.164) - 727,
    'JAX':(whs2 * 0.164) - 727, 
    'IAH':(whs3 * 0.164) - 727, 
    'LAX':(whs4 * 0.164) - 727, 
    'SEA':(whs5 * 0.164) - 727, 
    'STO':(whs6 * 0.164) - 727, 
    'ORF':(whs7 * 0.164) - 727, 
    'ORD':(whs8 * 0.164) - 727,
    'OAK':(whs9 * 0.164) - 727,
    'DEN':(whs10 * 0.164) - 727 
    }

    expand_out_capacity = {
    'EWR':(whs1_x * 0.164) - 727,
    'JAX':(whs2_x * 0.164) - 727, 
    'IAH':(whs3_x * 0.164) - 727, 
    'LAX':(whs4_x * 0.164) - 727, 
    'SEA':(whs5_x * 0.164) - 727, 
    'STO':(whs6_x * 0.164) - 727, 
    'ORF':(whs7_x * 0.164) - 727, 
    'ORD':(whs8_x * 0.164) - 727,
    'OAK':(whs9_x * 0.164) - 727,
    'DEN':(whs10_x * 0.164) - 727    
    }

    territories = ['Surf & Turf','Gold Rush 2','Gold Rush','Mountain West','Northeast','Oil','Beltway','Gators','Mountain Central']

    M = (demandForecast/dol_cuft)/365

    demand = {
    'Surf & Turf':(M*0.11),
    'Gold Rush 2':(M*0.12),
    'Gold Rush':(M*0.12),
    'Mountain West':(M*0.08),
    'Northeast':(M*0.19),
    'Oil':(M*0.08),
    'Beltway':(M*0.15),
    'Gators':(M*0.08),
    'Mountain Central':(M*0.07)
    }

    trucks = sum(demand.values())
    losM = 1/sum(demand.values())

    outbound_cost = [
    [2070.09,3619.73,3477.29,5032.03,1234.55,2747.92,1333.26,2938.30,3582.00], #ewr
    [1759.57,2774.98,3013.76,4453.01,2322.89,1488.06,1725.08,772.30,3155.85], #jax
    [2523.49,2887.26,1928.18,4814.09,4282.01,1333.84,3486.64,2667.05,2896.34], #iah
    [6497.89,1565.64,786.06,3847.91,7908.38,4848.72,7812.68,7369.77,3908.23], #lax
    [4473.83,1198.23,1435.37,935.91,7347.69,4471.47,6162.77,6049.60,3544.00], #sea
    [5182.69,597.07,836.94,3217.44,8082.87,4850.55,7495.31,6859.50,4100.68], #sto
    [2537.74,3700.94,3384.17,5950.72,1565.96,2738.72,1222.83,2429.76,4115.44], #orf
    [1631.12,3196.33,3044.71,4188.93,3249.26,2694.34,2507.67,3456.76,3100.94], #ord
    [5182.69,597.07,836.94,3217.44,8082.87,4850.55,7495.31,6859.50,4100.68], #oak
    [1389.68,1485.77,957.29,2737.65,4300.19,1201.44,3320.64,3339.00,2147.08] #den
    ]


    outbound_A = np.array(outbound_cost)
    outbound_A = np.round(outbound_A/2700,3)
    outbound_cost = outbound_A.tolist()

    outbound_cost = pu.makeDict([fc,territories], outbound_cost,0)

    inbound_cost = [
    [2137.50,7000.00,5031.25,340.00,4062.50,7125.00,1487.50], #ewr 
    [440.00,7275.00,5293.75,2612.50,2625.00,2750.00,1200.00], #jax 
    [1312.50,4650.00,3675.00,2437.50,275.00,2812.50,3037.50], #iah 
    [3031.25,325.00,1100.00,2775.00,1937.50,1487.50,8100.00], #lax 
    [3781.25,4312.50,495.00,4987.50,5512.50,3200.00,6637.50], #sea 
    [2750.00,1487.50,968.75,3562.50,2812.50,815.00,8175.00], #sto 
    [1200.00,8175.00,5950.00,1312.50,3037.50,8175.00,300.00], #orf 
    [766.00,2561.00,1656.00,730.00,1000.00,2561.00,1170.00], #ord
    [2750.00,1487.50,968.75,3562.50,2812.50,645.00,8175.00], #oak
    [3375.57,3835.32,3106.95,3157.72,3069.00,4401.34,3739.84] #den
    ]

    inbound_A = np.array(inbound_cost)
    inbound_A = np.round(inbound_A/2200,3)
    inbound_cost = inbound_A.tolist()

    inbound_cost = pu.makeDict([fc,ports], inbound_cost,0)
      
    whs_box_cost = {
    'EWR':(whs1 * 10.03)/365,
    'JAX':(whs2 * 3.61)/365, 
    'IAH':(whs3 * 7.80)/365, 
    'LAX':(whs4 * 13.08)/365, 
    'SEA':(whs5 * 8.10)/365, 
    'STO':(whs6 * 7.30)/365, 
    'ORF':(whs7 * 5.30)/365, 
    'ORD':(whs8 * 8.50)/365,
    'OAK':(whs9 * 12.20)/365,
    'DEN':(whs10 * 6.79)/365  
    }

    whs_expand_cost = {
    'EWR':(whs1_x * 16.0)/365,
    'JAX':(whs2_x * 3.61)/365, 
    'IAH':(whs3_x * 7.80)/365, 
    'LAX':(whs4_x * 14.0)/365, 
    'SEA':(whs5_x * 8.10)/365, 
    'STO':(whs6_x * 7.30)/365, 
    'ORF':(whs7_x * 5.30)/365, 
    'ORD':(whs8_x * 8.50)/365,
    'OAK':(whs9_x * 12.20)/365,
    'DEN':(whs10_x * 6.79)/365   
    }

    whs_labour_cost = {
    'EWR':13452, 
    'JAX':8600, 
    'IAH':6390, 
    'LAX':8892, 
    'SEA':6748, 
    'STO':6210, 
    'ORF':6624, 
    'ORD':7260,
    'OAK':6210,
    'DEN':6210
    }

    purchasing_cost = {
    'Jacksonville':0,
    'Long Beach':0,
    'Seattle':0,
    'New Jersey':0,
    'Houston':0,
    'Oakland':0,
    'Norfolk':0
    }

    within_500 = [
    [0,0,0,0,1,0,1,0,0], #ewr
    [0,0,0,0,0,0,0,1,0], #jax
    [0,0,0,0,0,1,0,0,0], #iah
    [0,1,1,0,0,0,0,0,0], #lax
    [0,0,0,1,0,0,0,0,0], #sea
    [0,1,1,0,0,0,0,0,0], #sto
    [0,0,0,0,1,0,1,0,0], #orf
    [1,0,0,0,0,0,0,0,0], #ord
    [0,1,1,0,0,0,0,0,0],  #oak
    [0,0,0,0,0,0,0,0,1]  #den
    ]

    within_500 = pu.makeDict([fc,territories], within_500,0)

    #%%
    # Scenario Control Parameters
    serviceGoal = SLgoal
    minFC = FCmin
    maxFC = FCmax

    # Creates the 'prob' variable to contain the problem data
    prob = pu.LpProblem("Network_Design_Problem",pu.LpMinimize)

    # Creates a list of tuples containing all the possible inbound routes for transport
    inbound_routes = [(f,p) for f in fc for p in ports]

    # Creates a list of tuples containing all the possible outbound routes for transport
    outbound_routes = [(f,t) for f in fc for t in territories]

    # A dictionary called 'inVars' is created to contain the referenced variables (the inbound routes)
    inVars = pu.LpVariable.dicts("Inbound Route",(fc,ports),0,None,pu.LpContinuous)

    # A dictionary called 'outVars' is created to contain the referenced variables (the outbound routes)
    outVars = pu.LpVariable.dicts("Outbound Route",(fc,territories),0,None,pu.LpContinuous)

    # A dictionary called 'fcOpen' is created to contain the referenced variables (the open FCs)
    fcOpen = pu.LpVariable.dicts("FC Opened",fc,0,1,pu.LpBinary)
    
    fcOpen['EWR'].lowBound = whs1_o
    fcOpen['LAX'].lowBound = whs2_o
    fcOpen['JAX'].lowBound = whs3_o
    fcOpen['IAH'].lowBound = whs4_o
    fcOpen['SEA'].lowBound = whs5_o
    fcOpen['STO'].lowBound = whs6_o
    fcOpen['ORF'].lowBound = whs7_o
    fcOpen['ORD'].lowBound = whs8_o
    fcOpen['OAK'].lowBound = whs9_o
    fcOpen['DEN'].lowBound = whs10_o
    fcOpen['EWR'].upBound = whs1_c
    fcOpen['LAX'].upBound = whs2_c
    fcOpen['JAX'].upBound = whs3_c
    fcOpen['IAH'].upBound = whs4_c
    fcOpen['SEA'].upBound = whs5_c
    fcOpen['STO'].upBound = whs6_c
    fcOpen['ORF'].upBound = whs7_c
    fcOpen['ORD'].upBound = whs8_c
    fcOpen['OAK'].upBound = whs9_c
    fcOpen['DEN'].upBound = whs10_c

    expand = pu.LpVariable.dicts("Expand FC",fc,0,1,pu.LpBinary)

    # The objective function is added to 'prob' first

    prob += (
        pu.lpSum([outVars[f][t] * outbound_cost[f][t] for (f, t) in outbound_routes]) # final mile costs)
        + pu.lpSum([inVars[f][p] * inbound_cost[f][p]  for (f, p) in inbound_routes]) # middle mile costs)
        + pu.lpSum([fcOpen[f] * whs_box_cost[f]  for f in fc]) # FC Fixed Costs
        + pu.lpSum([fcOpen[f] * whs_labour_cost[f]  for f in fc]) # FC Labour Costs
        + pu.lpSum([inVars[f][p] * purchasing_cost[p] for (f,p) in inbound_routes]) # Purchasing Costs  
        + pu.lpSum([expand[f] * whs_expand_cost[f] for f in fc]), #cost of expanding
        "Sum_of_Network_Costs",
    )

    # The supply maximum constraints are added to prob for each supply node (port)
    for p in ports:
        prob += (
            pu.lpSum([inVars[f][p] for f in fc]) <= inbound_supply[p],
            "Sum of Products out of %s Port" % p,
        )

    # The inbound maximum constraints are added to prob for each fc node (fc)
    for f in fc:
        prob += (
            pu.lpSum([inVars[f][p] for p in ports]) <= inbound_capacity[f] + expand_in_capacity[f]*expand[f],
            "Sum of Products into %s FC" % f,
        )

    # The outbound maximum constraints are added to prob for each fc node (fc)
    for f in fc:
        prob += (
            pu.lpSum([outVars[f][t] for t in territories]) <= outbound_capacity[f] + expand_out_capacity[f]*expand[f],
            "Sum of Products out of %s FC" % f,
        )

    # The demand minimum constraints are added to prob for each demand node (territory)
    for t in territories:
        prob += (
            pu.lpSum([outVars[f][t] for f in fc]) == demand[t],
            "Sum of Products into %s Territory" % t,
        )

    # The flow constraint is added to prob for each fc node (fc)
    for f in fc:
        prob += (
            pu.lpSum([outVars[f][t] for t in territories]) == pu.lpSum([inVars[f][p] for p in ports]),
            "Flow Constaint for %s FC" % f,
        )    

    # The linking constraint is added to prob for each fc node (fc)
    for f in fc:
        prob += (
            pu.lpSum([outVars[f][t] for t in territories])-trucks*fcOpen[f] <= 0,
            "Linking Constraint for %s FC" % f,
        )

    # Level of Service Constraint
    prob += (
    pu.lpSum([(outVars[f][t] * within_500[f][t])*losM for (f, t) in outbound_routes]) >= serviceGoal,
    "Level of Service",
    )

    # Maximum number of FCs that can be opened
    prob += (
        pu.lpSum([fcOpen[f] for f in fc]) <= maxFC,
        "Maximum Opened FCs"
    )

    # Minimum number of FCs that can be opened
    prob += (
        pu.lpSum([fcOpen[f] for f in fc]) >= minFC,
        "Minimum Opened FCs"
    )

    #%%

    # The problem data is written to an .lp file
    prob.writeLP("Network_Design_Problem.lp")

    # The problem is solved using PuLP's choice of Solver
    prob.solve()

    fcs = []
    for v in prob.variables():
            if v.varValue > 0:
                if 'FC_Opened' in v.name:
                    fcs.append(1)
    fcCount = len(fcs)

    open_dict = {}
    expand_dict = {}
    inbound_dict = {}
    outbound_dict = {}
    los_list = []

    for v in prob._variables[20:90]:
        if v.varValue > 0.5:
            inbound_dict[v]=v.varValue

    for v in prob._variables[90:]:
        if v.varValue > 0.5:
            outbound_dict[v]=v.varValue

    for v in prob._variables[10:20]:
        if v.varValue > 0.5:
            open_dict[v]=v.varValue
    
    for v in prob._variables[:10]:
        if v.varValue > 0.5:
            expand_dict[v]=v.varValue

    for k in prob.constraints['Level_of_Service'].keys():
        if outbound_dict.get(k) is not None:
            los_list.append(outbound_dict[k]*losM)

    los_A = np.array(los_list)
    los = np.sum(los_A)

    if pu.LpStatus[prob.status] == 'Infeasible':
        print("There is no solution for the given parameters:\nTotal Demand = ${:,.2f} or {:,.2f} CuFT of demand\nService Level Goal >= {:.0%}\nMin FCs = {}\nMax FCs = {}".format(demandForecast,M,serviceGoal,minFC,maxFC),file=open(saveTo+'/OptimizationResults.txt', "w"))
        print(file=open(saveTo+'/OptimizationResults.txt', "a"))
        print(prob,file=open(saveTo+'/OptimizationResults.txt', "a"))
    else:
    # The status of the solution is printed to the screen
        print("Status: {} solution found\n\nWe can fulfill demand for {:,.2f} CuFt of furniture each day.".format(pu.LpStatus[prob.status],trucks),file=open(saveTo+'/OptimizationResults.txt', "w"))
        print("We should open {} FCs at a total network cost of ${:,.2f} per day.".format(fcCount,pu.value(prob.objective)),file=open(saveTo+'/OptimizationResults.txt', "a"))
        print("Approximately {:.0%} of the deliveries are within 500 miles of their destination.".format(los),file=open(saveTo+'/OptimizationResults.txt', "a"))
    
    # Print the FCs that were opened
        print("\nTo do this, we should open the following FCs:",file=open(saveTo+'/OptimizationResults.txt', "a"))
        opened = ""
        for k in open_dict.keys():
            opened = opened + k.name[10:] + ", "
        print(opened[:-2],file=open(saveTo+'/OptimizationResults.txt', "a"))
    
    # Print the FC that were expanded
        print("\nWe should expand the following FCs:",file=open(saveTo+'/OptimizationResults.txt', "a"))
        expanded = ""
        for k in expand_dict.keys():
            expanded = expanded + k.name[10:] + ", "
        print(expanded[:-2],file=open(saveTo+'/OptimizationResults.txt', "a"))
        print(file=open(saveTo+'/OptimizationResults.txt', "a"))
    
    # Each of the variables is printed with it's resolved optimum value
        print("Drayage Details:",file=open(saveTo+'/OptimizationResults.txt', "a"))
        for k in inbound_dict.keys():
            print("{:.0f} CuFt from the Port of {} to {} FC".format(inbound_dict[k],k.name[18:],k.name[14:17]),file=open(saveTo+'/OptimizationResults.txt', "a"))
        print(file=open(saveTo+'/OptimizationResults.txt', "a"))
        print("Final Mile Delivery Details:",file=open(saveTo+'/OptimizationResults.txt', "a"))
        for k in outbound_dict.keys():
            print("{:.0f} CuFt from {} FC to the {} territory".format(outbound_dict[k],k.name[15:18],k.name[19:]),file=open(saveTo+'/OptimizationResults.txt', "a"))

        # # Print the objective function, constraints and variables
        # print(file=open(saveTo+'/OptimizationResults.txt', "a"))
        # print(prob,file=open(saveTo+'/OptimizationResults.txt', "a"))

# %%

root = tk.Tk()
root.geometry("1000x600")
root.title('Article USA Network Design')

topFrame = tk.Frame(root)
topFrame.pack(side=tk.TOP)

frame = tk.Frame(root)
frame.pack()

bottomFrame = tk.Frame(root)
bottomFrame.pack(side=tk.BOTTOM)

def createNewWindow(fileLoc):
    newWindow = tk.Toplevel()
    newWindow.title('Optimization Results')
    with open(fileLoc +'/OptimizationResults.txt') as f:
        contents = f.read()

    msg = tk.Text(newWindow,font=('Consolas', 11), width=85, height = 35)
    tk.Label(newWindow,text = 'Here are the results of the optimization.',font = "Helvetica 12 bold").pack(side=tk.TOP)
    msg.insert(tk.END, contents)
    msg.pack()

def entry_fields():
    FCmin = int(e1.get())
    FCmax = int(e2.get())
    SLgoal = float(e3.get())
    demandForecast = float(e4.get())
    dol_cuft = float(e5.get())
    whs1 = int(e6.get())
    whs2 = int(e7.get())
    whs3 = int(e8.get())
    whs4 = int(e9.get())
    whs5 = int(e10.get())
    whs6 = int(e11.get())
    whs7 = int(e12.get())
    whs8 = int(e13.get())
    whs9 = int(e14.get())
    whs10 = int(e42.get())
    whs1_x=int(e15.get())
    whs2_x=int(e16.get())
    whs3_x=int(e17.get())
    whs4_x=int(e18.get())
    whs5_x=int(e19.get())
    whs6_x=int(e20.get())
    whs7_x=int(e21.get())
    whs8_x=int(e22.get())
    whs9_x=int(e23.get())
    whs10_x=int(e43.get())
    whs1_o=int(w1_o.get())
    whs2_o=int(w2_o.get())
    whs3_o=int(w3_o.get())
    whs4_o=int(w4_o.get())
    whs5_o=int(w5_o.get())
    whs6_o=int(w6_o.get())
    whs7_o=int(w7_o.get())
    whs8_o=int(w8_o.get())
    whs9_o=int(w9_o.get())
    whs10_o=int(w10_o.get())
    whs1_c=int(w1_c.get())
    whs2_c=int(w2_c.get())
    whs3_c=int(w3_c.get())
    whs4_c=int(w4_c.get())
    whs5_c=int(w5_c.get())
    whs6_c=int(w6_c.get())
    whs7_c=int(w7_c.get())
    whs8_c=int(w8_c.get())
    whs9_c=int(w9_c.get())
    whs10_c=int(w10_c.get())
    
    saveTo = tk.filedialog.askdirectory(title="Please Select a Folder")
    milp(saveTo,demandForecast,SLgoal,FCmax,FCmin,dol_cuft,whs1,whs2,whs3,whs4,whs5,whs6,whs7,whs8,whs9,whs10,whs1_x,whs2_x,whs3_x,whs4_x,whs5_x,whs6_x,whs7_x,whs8_x,whs9_x,whs10_x,whs1_o,whs2_o,whs3_o,whs4_o,whs5_o,whs6_o,whs7_o,whs8_o,whs9_o,whs10_o,whs1_c,whs2_c,whs3_c,whs4_c,whs5_c,whs6_c,whs7_c,whs8_c,whs9_c,whs10_c)
    createNewWindow(saveTo)

def quit():
        root.destroy()

tk.Label(topFrame,
        justify = tk.LEFT,
        pady = 5,
        text = 'Please Enter Your Desired Parameters',
        font = "Helvetica 14 bold").pack(side=tk.TOP)

tk.Label(frame,
        font = "Helvetica 13",
        text = 'What is the minimum number of FCs?').grid(row=0)

tk.Label(frame,
        font = "Helvetica 13",
        text = 'What is the maximum number of FCs?').grid(row=1)
        
tk.Label(frame,
        font = "Helvetica 13",
        text = 'What % of demand is fulfilled from within 500 miles?').grid(row=2)

tk.Label(frame,
        font = "Helvetica 13",
        text = 'What is the dollar demand for this scenario?').grid(row=3)

tk.Label(frame,
        font = "Helvetica 13",
        text = 'What is the $ to CuFt conversion rate?').grid(row=4)

tk.Label(frame,
        font = "Helvetica 13 bold",
        text = 'Facility Name').grid(row=5,column=0)

tk.Label(frame,
        font = "Helvetica 13 bold",
        text = 'Total Sq Ft Capacity').grid(row=5,column=1)

tk.Label(frame,
        font = "Helvetica 13 bold",
        text = 'Total Sq Ft Expansion').grid(row=5,column=2)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(EWR) New Jersey FC').grid(row=6)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(JAX) Jacksonville FC').grid(row=7)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(IAH) Houston FC').grid(row=8)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(LAX) Los Angeles FC').grid(row=9)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(SEA) Seattle FC').grid(row=10)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(STO) Stockton FC').grid(row=11)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(ORF) Norfolk FC').grid(row=12)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(ORD) Chicago FC').grid(row=13)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(OAK) Oakland FC').grid(row=14)

tk.Label(frame,
        font = "Helvetica 13",
        text = '(DEN) Denver FC').grid(row=15)

e1 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e2 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e3 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e4 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e5 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e6 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e7 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e8 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e9 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e10 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e11 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e12 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e13 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e14 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e15 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e16 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e17 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e18 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e19 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e20 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e21 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e22 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e23 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e42 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)
e43 = tk.Entry(frame,font = "Helvetica 11", justify=tk.CENTER)

w1_o = tk.IntVar()
w2_o = tk.IntVar()
w3_o = tk.IntVar()
w4_o = tk.IntVar()
w5_o = tk.IntVar()
w6_o = tk.IntVar()
w7_o = tk.IntVar()
w8_o = tk.IntVar()
w9_o = tk.IntVar()
w10_o = tk.IntVar()

w1_c = tk.IntVar()
w2_c = tk.IntVar()
w3_c = tk.IntVar()
w4_c = tk.IntVar()
w5_c = tk.IntVar()
w6_c = tk.IntVar()
w7_c = tk.IntVar()
w8_c = tk.IntVar()
w9_c = tk.IntVar()
w10_c = tk.IntVar()

w1_o.set(1)
w2_o.set(1)
w3_o.set(1)
w4_o.set(1)
w5_o.set(1)
w6_o.set(0)
w7_o.set(0)
w8_o.set(1)
w9_o.set(0)
w10_o.set(0)

w1_c.set(1)
w2_c.set(1)
w3_c.set(1)
w4_c.set(1)
w5_c.set(1)
w6_c.set(1)
w7_c.set(1)
w8_c.set(1)
w9_c.set(1)
w10_c.set(1)

e24 = tk.Checkbutton(frame,text="Force Open", variable = w1_o) #, onvalue = 1, offvalue = 0)
e25 = tk.Checkbutton(frame,text="Force Open", variable = w2_o) #, onvalue = 1, offvalue = 0)
e26 = tk.Checkbutton(frame,text="Force Open", variable = w3_o) #, onvalue = 1, offvalue = 0)
e27 = tk.Checkbutton(frame,text="Force Open", variable = w4_o) #, onvalue = 1, offvalue = 0)
e28 = tk.Checkbutton(frame,text="Force Open", variable = w5_o) #, onvalue = 1, offvalue = 0)
e29 = tk.Checkbutton(frame,text="Force Open", variable = w6_o) #, onvalue = 1, offvalue = 0)
e30 = tk.Checkbutton(frame,text="Force Open", variable = w7_o) #, onvalue = 1, offvalue = 0)
e31 = tk.Checkbutton(frame,text="Force Open", variable = w8_o) #, onvalue = 1, offvalue = 0)
e32 = tk.Checkbutton(frame,text="Force Open", variable = w9_o) #, onvalue = 1, offvalue = 0)
e44 = tk.Checkbutton(frame,text="Force Open", variable = w10_o) #, onvalue = 1, offvalue = 0)
e33 = tk.Checkbutton(frame,text = "Force Close", variable = w1_c, onvalue = 0, offvalue = 1)
e34 = tk.Checkbutton(frame,text = "Force Close", variable = w2_c, onvalue = 0, offvalue = 1)
e35 = tk.Checkbutton(frame,text = "Force Close", variable = w3_c, onvalue = 0, offvalue = 1)
e36 = tk.Checkbutton(frame,text = "Force Close", variable = w4_c, onvalue = 0, offvalue = 1)
e37 = tk.Checkbutton(frame,text = "Force Close", variable = w5_c, onvalue = 0, offvalue = 1)
e38 = tk.Checkbutton(frame,text = "Force Close", variable = w6_c, onvalue = 0, offvalue = 1)
e39 = tk.Checkbutton(frame,text = "Force Close", variable = w7_c, onvalue = 0, offvalue = 1)
e40 = tk.Checkbutton(frame,text = "Force Close", variable = w8_c, onvalue = 0, offvalue = 1)
e41 = tk.Checkbutton(frame,text = "Force Close", variable = w9_c, onvalue = 0, offvalue = 1)
e45 = tk.Checkbutton(frame,text = "Force Close", variable = w10_c, onvalue = 0, offvalue = 1)

e1.insert(10, "0")
e2.insert(10, "99")
e3.insert(10, "0.93")
e4.insert(10, "1510000000")
e5.insert(10,"31.28")
e6.insert(10,"340000") 
e7.insert(10,"320000") 
e8.insert(10,"500000")
e9.insert(10,"290000")
e10.insert(10,"170000")
e11.insert(10,"200000")
e12.insert(10,"200000")
e13.insert(10,"170000")
e14.insert(10,"200000")
e15.insert(10,"300000")
e16.insert(10,"200000")
e17.insert(10,"0")
e18.insert(10,"200000")
e19.insert(10,"30000")
e20.insert(10,"0")
e21.insert(10,"0")
e22.insert(10,"80000")
e23.insert(10,"0")
e42.insert(10,"150000")
e43.insert(10,"0")


e1.grid(row=0, column=1, pady=5,padx=6)
e2.grid(row=1, column=1, pady=5,padx=6)
e3.grid(row=2, column=1, pady=5,padx=6)
e4.grid(row=3, column=1, pady=5,padx=6)
e5.grid(row=4, column=1, pady=5,padx=6)
e6.grid(row=6, column=1, pady=5,padx=6)
e7.grid(row=7, column=1, pady=5,padx=6)
e8.grid(row=8, column=1, pady=5,padx=6)
e9.grid(row=9, column=1, pady=5,padx=6)
e10.grid(row=10, column=1, pady=5,padx=6)
e11.grid(row=11, column=1, pady=5,padx=6)
e12.grid(row=12, column=1, pady=5,padx=6)
e13.grid(row=13, column=1, pady=5,padx=6)
e14.grid(row=14, column=1, pady=5,padx=6)
e15.grid(row=6, column=2, pady=5,padx=6)
e16.grid(row=7, column=2, pady=5,padx=6)
e17.grid(row=8, column=2, pady=5,padx=6)
e18.grid(row=9, column=2, pady=5,padx=6)
e19.grid(row=10, column=2, pady=5,padx=6)
e20.grid(row=11, column=2, pady=5,padx=6)
e21.grid(row=12, column=2, pady=5,padx=6)
e22.grid(row=13, column=2, pady=5,padx=6)
e23.grid(row=14, column=2, pady=5,padx=6)
e24.grid(row=6, column=3, pady=5,padx=6)
e25.grid(row=7, column=3, pady=5,padx=6)
e26.grid(row=8, column=3, pady=5,padx=6)
e27.grid(row=9, column=3, pady=5,padx=6)
e28.grid(row=10, column=3, pady=5,padx=6)
e29.grid(row=11, column=3, pady=5,padx=6)
e30.grid(row=12, column=3, pady=5,padx=6)
e31.grid(row=13, column=3, pady=5,padx=6)
e32.grid(row=14, column=3, pady=5,padx=6)
e33.grid(row=6, column=4, pady=5,padx=6)
e34.grid(row=7, column=4, pady=5,padx=6)
e35.grid(row=8, column=4, pady=5,padx=6)
e36.grid(row=9, column=4, pady=5,padx=6)
e37.grid(row=10, column=4, pady=5,padx=6)
e38.grid(row=11, column=4, pady=5,padx=6)
e39.grid(row=12, column=4, pady=5,padx=6)
e40.grid(row=13, column=4, pady=5,padx=6)
e41.grid(row=14, column=4, pady=5,padx=6)
e42.grid(row=15, column=1, pady=5,padx=6)
e43.grid(row=15, column=2, pady=5,padx=6)
e44.grid(row=15, column=3, pady=5,padx=6)
e45.grid(row=15, column=4, pady=5,padx=6)


button = tk.Button(bottomFrame,text='Run Optimization', fg = 'green', font = "Helvetica 13 bold", command=entry_fields)
button.pack(side=tk.LEFT, pady = 5)

button2 = tk.Button(bottomFrame,text='Quit Optimization', fg = 'red', font = "Helvetica 13 bold", command=quit)
button2.pack(side=tk.RIGHT, pady = 5)
root.protocol("WM_DELETE_WINDOW", quit)
root.mainloop()
# %%
