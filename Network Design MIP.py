#%%
try:
    import pulp as pu
    import pandas as pd
    import numpy as np
    import gurobipy as gp
    from gurobipy import GRB
    import networkx as nx
    import matplotlib.pyplot as plt
    from geopy import distance
    import multidict as md
    from mpl_toolkits.basemap import Basemap as Basemap
    import openpyxl as xl
    import os
    import datetime as dt
    import requests
    import json
    import traceback

    ####################################################################
    ###This section contains functions that support data in the model###
    ####################################################################
    '''
    sqft_to_outbound_cuft(x,y,z,a,r) where:
    x = whs sqft
    y = sqft to cuft conversion
    z = useable sqft
    a = slope or inventory turns
    f = fullness
    r = racking yes/no
    v = throughput volume

    Note: In the calc_distance function, 1.25 is the circuity factor used to account for elevation, road curves and other factors impacting overland distances.
    '''

    plt.rcParams['figure.figsize'] = [400, 200]
    plt.rcParams['savefig.facecolor']='white'

    now1 = dt.datetime.now()
    now = now1.strftime("%Y%m%d_%H_%M_%S")

    saveTo = os.getcwd()

    def sqft_to_throughput(x,y,z,a,r):
        if x <= 0:
                return 0
        elif r > 0 :
                return (a*x*y*z*(1.25*r))/365
        else:
            return (a*x*y*z)/365

    def throughput_to_sqft(v,y,z,a,r):
        if v <= 0:
                return 0
        elif r > 0 :
                return (365*v)/(a*y*z*(1.25*r))
        else:
            return (365*v)/(a*y*z)

    def calc_distance(from_loc, to_loc):
        return distance.GreatCircleDistance(from_loc,to_loc).km*1.25

    def driving_distance(from_loc, to_loc):
        # call the OSMR API ---- This is very very slow as each route is called one at a time...
        r = requests.get(f"http://router.project-osrm.org/route/v1/car/{from_loc[1]},{from_loc[0]};{to_loc[1]},{to_loc[0]}?overview=false""")
        # then you load the response using the json libray
        # by default you get only one alternative so you access 0-th element of the `routes`
        routes = json.loads(r.content)
        return routes.get("routes")[0]['distance']/1000

    def oh_inventory(x,y,z,f,r):
        if x <= 0:
            return 0
        elif r > 0 :
                return (f*x*y*z*(1.25*r))
        else:
            return (f*x*y*z)

    def racking_cost(x,r):
        if r == 0:
            return 0
        else:
            return 3.9375*x

    ##########################################################################################
    ###This section is used to pull raw data in from csv files and create useful dataframes###
    ##########################################################################################

    ### pull csv files into python
    parameters = pd.read_excel(saveTo + "/Network Design Launcher.xlsm",sheet_name='parameters')
    user_form = pd.read_excel(saveTo +"/Network Design Launcher.xlsm",sheet_name='user form')
    demand_info = pd.read_excel(saveTo +"/Network Design Launcher.xlsm",sheet_name='demand')

    #remove Hawaii from dataset, since it cannot be reached by road
    demand_info.drop(demand_info[demand_info.region =="Hawaii"].index, inplace=True)
    demand_info.drop(demand_info[demand_info.city =="Rankin Inlet, Nunavut"].index, inplace=True)
    demand_info.drop('location',axis=1,inplace=True)

    #Demand dataframe
    state_demand_cuft = demand_info[['city','volume']].copy()
    state_demand_cuft['city'] = state_demand_cuft['city'].str.title()
    state_demand_cuft['city'] = state_demand_cuft['city'].str.replace(' ','_')
    state_demand_cuft['city'] = state_demand_cuft['city'].str.replace(',_',', ')
    state_demand_cuft=state_demand_cuft.set_index('city')

    #customer dataframe
    customer_csv = demand_info[['country','region','city','lat','long']].copy()
    customer_csv.rename(columns={'region':'state_province'},inplace=True)
    customer_csv['city'] = customer_csv['city'].str.title()

    #facility dataframe
    na_fc_csv = user_form[['facility','type','Location','lat','long','current sqft','cost/sqft','tax','avg operating cost','avg management cost','avg labour cost','Total Cost','Average Volume Inbound per Week','Average Volume Outbound per Week','country']].copy()
    na_fc_csv.rename(columns={'facility':'Name'},inplace=True)

    ####################################################
    ###This section contains parameters for the model###
    ####################################################

    #Demand Parameters
    parameters = parameters.set_index('parameter')
    parameters = parameters.value.to_dict()

    modelName = parameters['model_name']
    annual_dollar_forecast = parameters['annual demand']
    dol_cuft = parameters['dol_cuft']
    annual_volume_forecast = annual_dollar_forecast/dol_cuft
    daily_forecast = annual_volume_forecast/365
    bigM = daily_forecast

    # Level of Service Parameters
    serviceGoal = parameters['service goal']
    losM = 1/bigM
    los_limit = parameters['los_limit']/0.621371 # convert miles to KM
    in_los_limit = 1500/0.621371 # convert miles to KM
    co2e_perTEUkm = 373 # emissions factor for road transportation

    ###################################################################################
    ###This section is used to clean the imported data, or create new data as needed###
    ###################################################################################

    ######################################################
    #set up middle mile network with prices and distances#
    ######################################################

    facility_nodes = na_fc_csv[['Name','lat','long','country']].copy()
    facility_nodes['Name'] = facility_nodes['Name'].map(str)+'; '+facility_nodes['country'].map(str)
    facility_nodes['point'] = list(zip(facility_nodes['lat'],facility_nodes['long']))
    facility_nodes =facility_nodes.drop(['lat','long','country'], axis=1) 
    facility_nodes_dict = dict(zip(facility_nodes.Name,facility_nodes.point))
    #%%
    fac_to_fac = [(x,y) for x in list(facility_nodes.Name) for y in list(facility_nodes.Name) if x!=y]
    fac_to_fac = pd.DataFrame(fac_to_fac, columns=['source','destination'])

    if parameters['distance'] == 'car':
        fac_to_fac['distance'] = fac_to_fac.apply(lambda row: driving_distance(facility_nodes_dict[row.source], facility_nodes_dict[row.destination]), axis=1)
    else:
        fac_to_fac['distance'] = fac_to_fac.apply(lambda row: calc_distance(facility_nodes_dict[row.source], facility_nodes_dict[row.destination]), axis=1)

    fac_to_fac[['source','s_country']] = fac_to_fac['source'].str.split('; ', expand=True)
    fac_to_fac[['destination','d_country']] = fac_to_fac['destination'].str.split('; ', expand=True)

    # masks for distance = 0
    m_distance = fac_to_fac.distance==0

    #masks to set prices
    m_xCountryNS = (fac_to_fac.s_country == "Canada")&(fac_to_fac.d_country=='United States') # north to south border is under 5% on average (25% on Chinese origin goods)
    m_xCountrySN = (fac_to_fac.s_country == "United States")&(fac_to_fac.d_country=='Canada') # south to north (SIMA is ~200% (only applies to 10% of products), but the rest is 10%)

    ###updated to kilometers from miles by dividing 0.621371
    m_local = fac_to_fac.distance <= 10/0.621371
    m_short = ((fac_to_fac.distance > 10/0.621371) & (fac_to_fac.distance <= 150/0.621371))
    m_medium = ((fac_to_fac.distance>150/0.621371) & (fac_to_fac.distance<=600/0.621371))
    m_long = fac_to_fac.distance>600/0.621371

    # update distances
    fac_to_fac['distance'].mask(m_distance,100,inplace=True)

    #set prices
    fac_to_fac['price'] = 1
    fac_to_fac['price'].mask(m_long,(fac_to_fac['distance']*2)/(2700*0.85),inplace=True)  # where 0.85 is the max fullness of the trailer
    fac_to_fac['price'].mask(m_medium,(fac_to_fac['distance']*4)/(2700*0.85),inplace=True)
    fac_to_fac['price'].mask(m_short,(fac_to_fac['distance']*20)/(2700*0.85),inplace=True)
    fac_to_fac['price'].mask(m_local,(fac_to_fac['distance']*450)/(2700*0.85),inplace=True)
    fac_to_fac['price'].where(m_xCountryNS,(fac_to_fac['price']*1.1),inplace=True) #if there is a cross-border stock transfer add the cost of customs/duties/taxes to the average cost of delivery
    fac_to_fac['price'].where(m_xCountrySN,(fac_to_fac['price']*1.5),inplace=True) #if there is a cross-border stock transfer add the cost of customs/duties/taxes to the average cost of delivery
    fac_to_fac = fac_to_fac.drop(['d_country','s_country'],axis=1)

    #####################################################
    #set up final mile network with prices and distances#
    #####################################################

    customer_nodes = customer_csv[['city','lat','long','country']].copy()
    states = customer_nodes.city.copy()

    customer_nodes['city'] = customer_nodes['city'].map(str)+'; '+customer_nodes['country'].map(str)
    customer_nodes['point'] = list(zip(customer_nodes['lat'],customer_nodes['long']))
    customer_nodes =customer_nodes.drop(['lat','long','country'], axis=1)

    customer_nodes_dict = dict(zip(customer_nodes.city,customer_nodes.point))
    customer_nodes_dict

    fac_to_cust = [(x,y) for x in list(facility_nodes.Name) for y in list(customer_nodes.city) if x!=y]
    fac_to_cust = pd.DataFrame(fac_to_cust, columns=['source','destination'])

    if parameters['distance'] == 'car':
        fac_to_cust['distance'] = fac_to_cust.apply(lambda row: driving_distance(facility_nodes_dict[row.source], customer_nodes_dict[row.destination]), axis=1)
    else:
        fac_to_cust['distance'] = fac_to_cust.apply(lambda row: calc_distance(facility_nodes_dict[row.source], customer_nodes_dict[row.destination]), axis=1)

    fac_to_cust['destination'] = fac_to_cust.destination.str.title()
    fac_to_cust['destination'] = fac_to_cust.destination.str.replace(' ','_')
    fac_to_cust['source'] = fac_to_cust.source.str.replace(' ','_')
    fac_to_cust['destination'] = fac_to_cust.destination.str.replace(',_',', ')
    fac_to_cust['source'] = fac_to_cust.source.str.replace(',_',', ')
    fac_to_cust[['destination','d_country']] = fac_to_cust['destination'].str.split(';', expand=True)
    fac_to_cust[['source','s_country']] = fac_to_cust['source'].str.split(';', expand=True)

    #mask for distance = 0
    m_distance = fac_to_cust.distance == 0

    #masks for setting prices (wait for the actual final mile prices)
    m_final_xCountryNS = (fac_to_cust.s_country == "Canada")&(fac_to_cust.d_country=='United States') # north to south border is under 5% on average (25% on Chinese origin goods)
    m_final_xCountrySN = (fac_to_cust.s_country == "United States")&(fac_to_cust.d_country=='Canada') # south to north (SIMA is ~200% (only applies to 10% of products), but the rest is 10%)

    # update distances
    fac_to_cust['distance'].mask(m_distance,100,inplace=True)

    fac_to_cust['price'] = (fac_to_cust['distance']*7)/(1023*0.85) # where 7 is the average final mile delivery cost per mile (including labour cost) and 0.85 is the max fullness of the trailer. 1023cuft is the weighted average volume of our final mile truck fleet.
    fac_to_cust['price'].where(m_final_xCountryNS,(fac_to_cust['price']*1.1),inplace=True) #if there is a cross-border delivery add the cost of customs/duties/taxes
    fac_to_cust['price'].where(m_final_xCountrySN,(fac_to_cust['price']*1.4),inplace=True) #if there is a cross-border delivery add the cost of customs/duties/taxes
    fac_to_cust = fac_to_cust.drop(['d_country','s_country'],axis=1)

    distance_lookup = fac_to_cust.append(fac_to_fac)
    distance_lookup['key'] = distance_lookup.source+"_"+distance_lookup.destination
    distance_lookup.drop(['source','destination','price'],axis=1,inplace=True)

    ################################
    ### create indices for model ###
    ################################

    mFC = na_fc_csv.type=='FC'
    mXD = na_fc_csv.type=='XD'
    na_facilities = na_fc_csv.Name.to_list()
    na_fc = na_fc_csv.Name.where(mFC).dropna().to_list()
    na_xd = na_fc_csv.Name.where(mXD).dropna().to_list()
    states = states.str.title()
    states = states.str.replace(' ','_')
    states = states.str.replace(',_',', ')
    states = states.to_list()

    # ensure that the indices are in alphabetical order to match the order of the dataframes
    na_facilities.sort()
    na_fc.sort()
    na_xd.sort()
    states.sort()

    #################################################
    ### create the level of service distance data ###
    #################################################

    fac_to_cust['los'] = fac_to_cust.distance
    fac_to_fac['los'] = fac_to_fac.distance

    fac_to_cust['los'] = fac_to_cust.los.mask(fac_to_cust.los <= los_limit,1)
    fac_to_cust['los'] = fac_to_cust.los.mask(fac_to_cust.los > los_limit,0)

    fac_to_fac['los'] = fac_to_fac.los.mask(fac_to_fac.los <= in_los_limit,1)
    fac_to_fac['los'] = fac_to_fac.los.mask(fac_to_fac.los > in_los_limit,0)

    #######################################
    ### create input data for the model ###
    #######################################

    # create the demand-related data
    state_percentage_split_demand = state_demand_cuft['volume'].div(state_demand_cuft['volume'].sum(axis=0))
    state_demand_forecast = state_percentage_split_demand*daily_forecast

    # create the facility-related data
    # get the cost/sqft for each potential facility
    keep_columns = ['Name','cost/sqft']
    na_fc_cost = na_fc_csv[keep_columns]
    na_fc_cost=na_fc_cost.set_index('Name')
    na_fc_cost.sort_index(inplace=True)
    mean_cost = na_fc_cost.mean()

    # generate the outbound throughput and cost of floorspace for each facility, based on the parameters set in the user form
    user_form['outbound_throughput']=user_form.apply(lambda x: sqft_to_throughput(x['total sqft'],x['sqft to cuft'],x['useable sqft'],x['turns'],x['racked']), axis=1)
    user_form['cost/sqft']=user_form['cost/sqft'].fillna(10)
    user_form['floorspace cost'] = (user_form['total sqft']*user_form['cost/sqft'] + user_form.apply(lambda x: racking_cost(x['total sqft'],x['racked']), axis=1))/365
    user_form['oh_inventory']= user_form.apply(lambda x: oh_inventory(x['total sqft'],x['sqft to cuft'],x['useable sqft'],x['fullness'],x['racked']), axis=1)
    user_form['expansion cost'] = (user_form['expansion']*user_form['cost/sqft'] + user_form.apply(lambda x: racking_cost(x['expansion'],x['racked']), axis=1))/365
    user_form['expansion_throughput']=user_form.apply(lambda x: sqft_to_throughput(x['expansion'],x['sqft to cuft'],x['useable sqft'],x['turns'],x['racked']), axis=1)
    user_form['expansion_inventory']=user_form.apply(lambda x: oh_inventory(x['expansion'],x['sqft to cuft'],x['useable sqft'],x['fullness'],x['racked']), axis=1)
    user_form = user_form.set_index('facility')

    ##################################################################################
    ### This section uses the above data to create dictionary for use in the model ###
    ##################################################################################

    ### create dcitionaries of input data for use in model
    demand = state_demand_forecast.to_dict()
    throughput = user_form['outbound_throughput'].to_dict()
    open_cost = user_form['floorspace cost'].to_dict()
    expand_cost = user_form['expansion cost'].to_dict()
    available_inventory = user_form['oh_inventory'].to_dict()
    expansion_inventory = user_form['expansion_inventory'].to_dict()
    expansion_throughput = user_form['expansion_throughput'].to_dict()

    #################################################################################################
    ### This section creates the multidict needed to easily load data into the optimization model ###
    #################################################################################################

    ### reformat input dataframes for the arc, cost multidict
    final_mile_price = fac_to_cust[['source','destination','price']].set_index('source').pivot(columns='destination',values='price')
    final_mile_price = final_mile_price.transpose().unstack().dropna()

    final_mile_dist = fac_to_cust[['source','destination','los']].set_index('source').pivot(columns='destination',values='los')
    final_mile_dist = final_mile_dist.transpose().unstack().dropna()

    stock_transfer_price = fac_to_fac[['source','destination','price']].set_index('source').pivot(columns='destination',values='price')
    stock_transfer_price = stock_transfer_price.transpose().unstack().dropna()

    stock_transfer_dist = fac_to_fac[['source','destination','los']].set_index('source').pivot(columns='destination',values='los')
    stock_transfer_dist = stock_transfer_dist.transpose().unstack().dropna()


    ### append all the reformatted dataframes to feed the multidict

    multidict_feed = final_mile_price.append(stock_transfer_price)
    # multidict_feed.to_csv(r"G:\Shared drives\Supply Chain Shared Drive\Supply Chain Planning Team\Network Design\MIP csvs\arcs.csv")

    multidict_feed_dist = final_mile_dist.append(stock_transfer_dist)
    # multidict_feed_dist.to_csv(r"G:\Shared drives\Supply Chain Shared Drive\Supply Chain Planning Team\Network Design\MIP csvs\arcs_dist.csv")

    ### build the multidict
    arcs, cost = gp.multidict(multidict_feed)
    arcs_out, dist = gp.multidict(multidict_feed_dist)

    flowSource = [i[0] for i in arcs]
    flowDestination = [i[1] for i in arcs]
    flowSource = list(dict.fromkeys(flowSource))
    flowDestination = list(dict.fromkeys(flowDestination))

    ##############################################################
    ### This section creates and runs the optimization program ###
    ##############################################################

    # Creates the 'prob' variable to contain the problem data
    prob = pu.LpProblem("Network_Design_Problem",pu.LpMinimize)

    # A dictionary called 'inVars' is created to contain the referenced variables (the inbound routes)
    flowVars = pu.LpVariable.dicts("Flow",(flowSource,flowDestination),0,None,pu.LpContinuous)

    # # A dictionary called 'inVars' is created to contain the referenced variables (the inbound routes)
    # inVars = pu.LpVariable.dicts("Inbound",(na_fc,na_xd),0,None,pu.LpContinuous)

    # # A dictionary called 'outVars' is created to contain the referenced variables (the outbound routes)
    # outVars = pu.LpVariable.dicts("Outbound",(na_facilities,states),0,None,pu.LpContinuous)

    # A dictionary called 'fcOpen' is created to contain the referenced variables (the open FCs)
    fcOpen = pu.LpVariable.dicts("Opened",na_facilities,0,1,pu.LpBinary)

    # A dictionary called 'fcExpand' is created to contain the referenced variables (the expand FCs)
    fcExpand = pu.LpVariable.dicts("Expanded",na_facilities,0,1,pu.LpBinary)

    #force open or closed the facilities based on user input
    for fac in na_facilities:
        if user_form['force open'][fac] == 1:
            fcOpen[fac].lowBound=1
        else:
            fcOpen[fac].lowBound=0

        if user_form['force close'][fac] == 1:
            fcOpen[fac].upBound=0
        else:
            fcOpen[fac].upBound=1       

    # The objective function is added to 'prob' first

    # ###racking requires a non-linear funciton and so substitution of non-linear objective function for linear function might be needed (13.5 of http://web.mit.edu/15.053/www/AMP-Chapter-13.pdf)
    # x1=fcRack[f]
    # x2=(3.9375 * fcExpand[f]*expand_size[f])
    # y1 = ((fcRack[f]+(3.9375 * fcExpand[f]*expand_size[f]))/2)
    # y2 = ((fcRack[f]-(3.9375 * fcExpand[f]*expand_size[f]))/2)
    # x1*x2 = y1**2-y2**2

    prob += (
        pu.lpSum([flowVars[s][d] * cost[(s, d)] for (s, d) in arcs]) # transportation costs
        + pu.lpSum([fcOpen[f] * open_cost[f]  for f in na_facilities]) # FC Fixed Costs
        + pu.lpSum([fcExpand[f] * expand_cost[f] for f in na_facilities]) # expand costs
        ,"Sum_of_Network_Costs",
    )

    # The available maximum inventory are added to prob for each supply node (fc)
    for f in na_fc:
        prob += (
            pu.lpSum([flowVars[f][d] for d in flowDestination]) <= available_inventory[f] + expansion_inventory[f]*fcExpand[f],
            "Flow from %s FC" % f,
        )

    # The inbound and outbound throughput constraints are added to prob for each facility node (fc, xd)
    for f in na_facilities:
        prob += (
            pu.lpSum([flowVars[s][f] for s in flowSource]) + pu.lpSum([flowVars[f][d] for d in flowDestination]) <= throughput[f] + expansion_throughput[f]*fcExpand[f],
            "Flow through %s facility" % f,
        )

    # # The outbound maximum constraints are added to prob for each fc node (fc)
    # for f in fc:
    #     prob += (
    #         pu.lpSum([outVars[f][t] for t in territories]) <=  outbound_capacity[f] + expand_out_capacity[f]*expand[f],
    #         "Sum of Products out of %s FC" % f,
    #     )

    # The demand minimum constraints are added to prob for each demand node (territory)
    for s in states:
        prob += (
            pu.lpSum([flowVars[f][s] for f in na_facilities]) == demand[s],
            "Sum of Products into %s" % s,
        )

    # The flow constraint is added to prob for each xd node (what flows in must flow out of xd)
    for x in na_xd:
        prob += (
            pu.lpSum([flowVars[x][s] for s in states]) == pu.lpSum([flowVars[f][x] for f in na_fc]),
            "Conservation of Flow Constaint for %s Cross Dock" % x,
        )

    # The flow constraint is added to prob for each xd node (xd cannot initiate stock transfers to fc or other xd)
    for x in na_xd:
        prob += (
            pu.lpSum([flowVars[x][f] for f in na_fc]) + pu.lpSum([flowVars[x][d] for d in na_xd])==0,
            "Flow Constaint for %s Cross Dock" % x,
        )  

    # The linking constraint is added to prob for each fc node (fc)
    for f in na_facilities:
        prob += (
            pu.lpSum([flowVars[f][d] for d in flowDestination])-bigM*fcOpen[f] <= 0,
            "Linking Constraint for %s Facilty" % f,
        )

    # Final Mile Level of Service Constraint
    prob += (
    pu.lpSum([(flowVars[s][d] * dist[(s, d)])*losM for (s, d) in arcs_out if d in states]) >= serviceGoal,
    "Level of Service",
    )

    # Maximum number of FCs that can be opened
    prob += (
        pu.lpSum([fcOpen[f] for f in na_facilities]) <= 99,
        "Maximum Opened FCs"
    )

    # Minimum number of FCs that can be opened
    prob += (
        pu.lpSum([fcOpen[f] for f in na_facilities]) >= 1,
        "Minimum Opened FCs"
    )

    # The problem data is written to an .lp file
    prob.writeLP("Network_Design_Problem.lp")

    # The problem is solved using PuLP's choice of Solver
    prob.solve()

    ####################################################
    ### This section creates the output for the user ###
    ####################################################

    if pu.LpStatus[prob.status] != 'Optimal':
        print('No feasible solution could be found. Perhaps the warehouse capacity is insufficient to handle demand. Try loosening the Force Open/Close constraints, increasing the expansion size of FCs, adding racking or increasing turns to boost capacity. It could also be that the service goal is too high, try reducing it be 5 or 10% (Note: a goal above 95% will likely be an issue).')
        input("Press enter to close window.")
        exit()
    else:
        ###gather model outputs for reporting
        expand_dict = {}
        flow_dict = {}
        los_list = []

        for v in prob._variables:
            if v.name[:4] == 'Flow' and v.varValue > 0.00001:
                flow_dict[v]=v.varValue

        for v in prob._variables:
            if v.name[:8] == 'Expanded' and v.varValue > 0.00001:
                expand_dict[v]=v.varValue

        for k in prob.constraints['Level_of_Service'].keys():
            if flow_dict.get(k) is not None:
                los_list.append(flow_dict[k]*losM)

        los_A = np.array(los_list)
        los = np.sum(los_A)

        expandDF = pd.DataFrame(expand_dict.items(),columns=['expand','status'])
        expandDF['facility'] = expandDF.expand.astype(str).str[9:]
        expandDF = expandDF.set_index('facility').drop('expand',axis=1)

        flowDF = pd.DataFrame(flow_dict.items(),columns=['flow','volume'])
        flowDF['flow'] = flowDF["flow"].astype(str).str.replace("Flow_","")
        flowDF['flow'] = flowDF["flow"].astype(str).str.replace(",_",", ")
        flowDF = flowDF.set_index('flow').join(distance_lookup.set_index('key'))
        flowDF['source'] = flowDF.index.str[:3]
        flowDF['destination'] = flowDF.index.str[4:]

        report_flow = flowDF.copy()
        report_flow['volume']=np.round(report_flow['volume'],0)
        report_flow['TEU']=np.round(report_flow['volume']/1172,1)
        report_flow['kg of co2e'] = np.round((report_flow.volume*report_flow.distance*co2e_perTEUkm)/1172000,1)
        report_flow.rename(columns={'volume':'daily volume flow'},inplace=True)
        report_flow = report_flow.pivot_table(index= ['source','destination'],columns=[],values=['daily volume flow','kg of co2e','TEU'])

        openDF = flowDF[['source','destination','volume']].copy()
        openDF = openDF.groupby('source').sum('volume')
        openDF = openDF.join(user_form)
        openDF = openDF.join(expandDF)

        m_expand = openDF['status'] == 1
        openDF['total sqft'] = openDF['total sqft'].mask(m_expand,openDF['total sqft']+openDF['expansion'])
        openDF['outbound_throughput'] = openDF['outbound_throughput'].mask(m_expand,openDF['outbound_throughput']+openDF['expansion_throughput'])
        openDF['floorspace cost'] = openDF['floorspace cost'].mask(m_expand,openDF['floorspace cost']+openDF['expansion cost'])
        openDF['remaining throughput capacity'] = np.round(openDF.outbound_throughput-openDF.volume,1)
        openDF['estimated_sqft'] = np.round(openDF.apply(lambda x: throughput_to_sqft(x['volume'],x['sqft to cuft'],x['useable sqft'],x['turns'],x['racked']), axis=1),0)
        openDF['floorspace used'] = np.round(openDF.estimated_sqft/openDF['total sqft'],3)
        openDF['daily floorspace cost'] = np.round(openDF['floorspace cost'],2)
        openDF['status'] = openDF['status'].fillna('no')
        openDF['status'] = openDF['status'].replace(1,'yes')
        openDF['racked'] = openDF['racked'].replace(1,'yes')
        openDF['racked'] = openDF['racked'].replace(0,'no')
        openDF = openDF.drop(['type','oh_inventory','sqft to cuft','useable sqft','turns','outbound_throughput','expansion cost','expansion_throughput','expansion_inventory'],axis=1)
        openDF['volume'] = np.round(openDF.volume,0)
        openDF = openDF.sort_values(by=['total sqft'], ascending = False)
        openDF=openDF[['volume', 'remaining throughput capacity',
            'estimated_sqft', 'total sqft', 'cost/sqft', 'floorspace used', 'daily floorspace cost','status','racked']]

            
        print("An {} solution has been found!\n\nFor annual demand of ${:,.2f}, approximately {} TEU totalling {:,.2f} cuft of inventory would need to flow to fulfill daily demand.\n\nThe middle and final mile delivery cost, plus opening FCs, would be approximately ${:,.2f} per day, or ${:,.2f} per TEU.".format(pu.LpStatus[prob.status],annual_dollar_forecast,np.ceil(openDF.volume.sum()/1172),openDF.volume.sum(),pu.value(prob.objective),pu.value(prob.objective)/np.ceil(openDF.volume.sum()/1172)),file=open(saveTo+'/'+now+'_'+'OptimizationResults_'+modelName+'.txt', "w"))
        print('\nTo accomplish this, we would need to open {} warehouses for a total of {:,} sqft. This would place approximately {:.2%} of final mile deliveries within {} miles of the customer. Transportation from this network would release approximately {:.2f} Kg of CO2 equivalent emissions.'.format(len(openDF.index),openDF.estimated_sqft.sum(),los,np.round(los_limit*0.621371,0),report_flow['kg of co2e'].sum()),file=open(saveTo+'/'+now+'_'+'OptimizationResults_'+modelName+'.txt', "a"))

        openDF.rename(columns={'volume':'daily volume flow', 'cost/sqft':'cost/sqft per year','estimated_sqft':'estimated required sqft','status':'expandedYN','racked':'rackedYN'},inplace = True)
        
        with pd.ExcelWriter(saveTo +'/'+now+'_'+'Network Design Model_'+modelName+'.xlsx') as writer:  
            openDF.to_excel(writer, sheet_name='Summary')
            report_flow.sort_values(by=['source','daily volume flow'], ascending=False).to_excel(writer, sheet_name='Details')

    ################################################################################
    ### This section creates and outputs the network onto a map of north america ###
    ################################################################################

    ###plot design on a graph
    # prepare data for graph
    plt.figure(figsize = (15,13.5))
    product_flow_graph = flowDF[['source','destination','volume']]
    product_flow_graph.columns = ['From','To','Flow']
    product_flow_graph['agenttype'] = product_flow_graph['To'].apply(len)
    m=product_flow_graph['agenttype']==3
    product_flow_graph['agenttype'].mask(m,'stock_transfer',inplace=True)
    product_flow_graph['agenttype'].mask(~m,'outbound',inplace=True)
    product_flow_graph['From']=product_flow_graph['From'].str.replace("_"," ")
    product_flow_graph['To']=product_flow_graph['To'].str.replace("_"," ")

    #get the total flow in and out
    total_out = product_flow_graph.groupby('From').sum('Flow')
    total_out.rename(columns={'Flow':'out_flow'},inplace=True)
    total_in = product_flow_graph.groupby('To').sum('Flow')
    total_in.rename(columns={'Flow':'in_flow'},inplace=True)

    #get all the possible final mile destinations
    state_loc = customer_csv[['city','lat','long']]
    state_loc.rename(columns={'city':'Name'},inplace=True)

    #get all the possible facilities
    pos_data = na_fc_csv[['Name','lat','long']]
    pos_data = pos_data.append(state_loc)
    pos_data = pos_data.set_index('Name')

    #add the in and out flows, and sum them up for the total flow
    pos_data = pos_data.join(total_in)
    pos_data = pos_data.join(total_out)
    pos_data['in_flow'] = pos_data.in_flow.fillna(0)
    pos_data['out_flow'] = pos_data.out_flow.fillna(0)
    pos_data['flow']=pos_data.in_flow+pos_data.out_flow
    pos_data = pos_data.drop(['in_flow','out_flow'],axis=1)

    #grab a map outline
    mp = Basemap(
            projection='merc',
            llcrnrlon=-180,
            llcrnrlat=10,
            urcrnrlon=-50,
            urcrnrlat=70,
            lat_ts=0,
            resolution='l',
            suppress_ticks=True)

    #setup node positions using lat and long
    mx, my = mp(pos_data['long'].values, pos_data['lat'].values)
    pos = {}
    for count, elem in enumerate (pos_data.index):
        pos[elem] = (mx[count], my[count])

    #split out the data by agenttype
    df_o = product_flow_graph[(product_flow_graph.agenttype == "outbound")]
    df_st = product_flow_graph[(product_flow_graph.agenttype == "stock_transfer")]
    product_flow_graph['agenttype'].mask(product_flow_graph['agenttype']=='outbound','green',inplace=True)
    product_flow_graph['agenttype'].mask(product_flow_graph['agenttype']=='stock_transfer','pink',inplace=True)
    edges = [tuple(x) for x in product_flow_graph[['From','To','Flow','agenttype']].values.tolist()]

    #iniate graph
    B = nx.DiGraph()

    #add nodes
    B.add_nodes_from(df_o['From'].unique())
    B.add_nodes_from(df_st['To'].unique())
    B.add_nodes_from(df_o['To'].unique())

    # add edges
    for row in edges:
        B.add_edge(row[0], row[1], Flow=row[2],color=row[3])

    #3. If you want, add labels to the nodes
    labels = {}
    for node_name in B.nodes():
        if len(node_name)==3:
            labels[str(node_name)] =str(node_name)
            nx.draw_networkx_labels(B,pos,labels,font_size=6,font_color='red',font_weight='bold')
        else:
            pass

    nx.draw_networkx_nodes(G = B, pos = pos, nodelist = B.nodes(), 
                        node_color = ['coral' if len(s)==3 else 'black' for s in B.nodes()], alpha = 0.8, node_size = [(pos_data['flow'][s]/1172)*15 if len(s)==3 else 3 for s in B.nodes()])

    all_weights = []

    #4 a. Iterate through the graph nodes to gather all the weights
    for (node1,node2,weight,color) in edges:
        all_weights.append(weight) #we'll use this when determining edge thickness

    #4 c. Plot the edges - one by one!
    for weight in all_weights:
    #4 d. Form a filtered list with just the weight you want to draw
        weighted_edges = [(node1,node2) for (node1,node2,edge_attr) in B.edges(data=True) if edge_attr['Flow']==weight]
        color = [(edge_attr['color']) for (node1,node2,edge_attr) in B.edges(data=True) if edge_attr['Flow']==weight]
    # #4 e. I think multiplying by [num_nodes/sum(all_weights)] makes the graphs edges look cleaner
        width = 0.5*weight*len(B.nodes())/sum(all_weights)
        nx.draw_networkx_edges(B,pos,edgelist=weighted_edges,edge_color = color, width=width, alpha=0.6, arrows=True,connectionstyle="arc3,rad=0.2")
        nx.draw_networkx_edges(B,pos,edgelist=weighted_edges,edge_color = color, width=0.5, alpha=0.3,connectionstyle="arc3,rad=0.2", arrows=True)

    mp.drawcountries(linewidth = 0.5)
    mp.drawstates(linewidth = 0.2)
    mp.drawcoastlines(linewidth=0.5)
    plt.tight_layout()
    plt.ioff()
    plt.savefig(saveTo+'/'+now+'_'+"Network Design Map Model_"+modelName+".png", format = "png", dpi = 300)

    end1 = dt.datetime.now()
    end = end1.strftime("%Y%m%d_%H_%M_%S")

    runtime = end1 - now1
    print(file=open(saveTo+'/'+now+'_'+'OptimizationResults_'+modelName+'.txt', "a"))
    print('Runtime = {}'.format(runtime),file=open(saveTo+'/'+now+'_'+'OptimizationResults_'+modelName+'.txt', "a"))
except:
    print("Uh Oh....Error in the script somewhere...time to debug.")
    print(traceback.format_exc())
    input("Press enter to close window.")
    exit()
#%%