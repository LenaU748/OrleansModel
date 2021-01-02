from shapely.geometry import Point as shapePoint
from shapely.geometry import Polygon as shapePolygon
import random
import math
import pandas as pd
import numpy 


def totalRiskCalculator(_age, _sex, _conditions): 

    #Conversion from risk to odds
    def riskToOdds(prob):
        odds = prob / (1 - prob)
        return odds

    def oddsToRisk(odds):
        prob = odds / (1 + odds)
        return prob

    #Lists that contain the hospitalization, icu, and death rate by age group
    #https://www.thelancet.com/journals/laninf/article/PIIS1473-3099(20)30243-7/fulltext
    hosp_list1 = [0, 0.0408, 1.04, 3.43, 4.25, 8.16, 11.8, 16.6, 18.4]
    hosp_list = [x / 100 for x in hosp_list1]

    icu_list1 = [0, 0, 2, 2, 3.7, 5.05, 6.4, 9.3, 8.4]
    #case to infection conversion 1.38% cfr, 0.657% infection fatality rate, use CDC ICU list
    icu_list = [x *.657/1.38/100 for x in icu_list1]

    death_list1 = [0.00161, 0.00695, 0.0309, 0.0844, 0.161, 0.595, 1.93, 4.28, 7.8]
    death_list = [x / 100 for x in death_list1]

    # OR source: https://www.medrxiv.org/content/10.1101/2020.02.24.20027268v1
    male_or = [1.8518, 1.85, 1.69]

    age_list = [0, 10, 20, 30, 40, 50, 60, 70, 80]

    def calcFemaleLists(listName, male, p_total):
        for x in range(len(p_total)):
            if p_total[x] == 0:
                listName.append(0)
            else:
                a = male-1
                b = male*(1-(2*p_total[x])) + (1+(2*p_total[x]))
                c = -2*p_total[x]

                p_female = (-1*b + math.sqrt(math.pow(b, 2) - 4*a*c))/(2*a) 

                listName.append(p_female)

        #print(listName)

    hosp_list_female = []
    icu_list_female = []
    death_list_female = []

    calcFemaleLists(hosp_list_female, male_or[0], hosp_list)
    calcFemaleLists(icu_list_female, male_or[1], icu_list)
    calcFemaleLists(death_list_female, male_or[2], death_list)

    ulh_all = []

    def calcComorbities(_conditions):
        #create dataframe 
        for i in range(len(_conditions)):
            #Odds Ratios for Underlying Health Conditions
            renal_or = [2.6, 5.82, 1.72] # aka kidney disease (CKD) - death OR not available in CCDC
            cvd_or = [1.4, 4.88, 1.27] # aka heart disease
            diabetes_or = [3.1, 4.57, 1.79]
            hyper_or = [1.1, 4.57, 1] # for ICU same as diabetes
            smoker_or = [2.3, 2.64, 1.12] # death OR not available in CCDC 
            #immune_or = [2.58, 2.86, 1.69] # death OR not available in CCDC
            lung_or = [1, 2.83, 1.78] # COPD
            obesity_or = [1.9, 3.41, 1.46]
            other_or = [4.21, 3.33, 6.11] # death OR not available in CCDC

            condition_or = eval(_conditions[i] + "_or")
            ulh_all.append(condition_or)

        conditions_df = pd.DataFrame(data=ulh_all, 
                                    index=[_conditions], 
                                    columns=['hosp', 'icu', 'death'])

        # adjust dataframe based on inputs
        if _conditions:
            # hosp OR are mutually adjusted except for immuno and other - for these 2 only adjust if they are only condition
            if not ["other"] == _conditions:
                if "other" in _conditions:
                    conditions_df.at['other', 'hosp'] = 1
            else:
                if "other" in _conditions:
                    conditions_df.at['other', 'hosp'] = conditions_df.at['other', 'hosp']

            if not ["immune"] == _conditions:
                if "immune" in _conditions:
                    conditions_df.at['immune', 'hosp'] = 1
            else:
                if "immune" in _conditions:
                    conditions_df.at['immune', 'hosp'] = conditions_df.at['immune', 'hosp']

            # ICU OR are not mutually adjusted, so use first 2 only
            for i in range(len(conditions_df['icu'])):
                conditions_df.iat[i, 1] = conditions_df.iat[i, 1] if i <= 1 else 1

            # Death OR are mutually adjusted except for other - for this one only adjust if it is only condition
            if not ["other"] == _conditions:
                if "other" in _conditions:
                    conditions_df.at['other', 'death'] = 1
            else:
                if "other" in _conditions:
                    conditions_df.at['other', 'death'] = conditions_df.at['other', 'death']

        hospCondProd = conditions_df['hosp'].tolist()
        icuCondProd = conditions_df['icu'].tolist()
        deathCondProd = conditions_df['death'].tolist()

        conditionsProds = [numpy.prod(hospCondProd), 
                            numpy.prod(icuCondProd), 
                            numpy.prod(deathCondProd)]
        return conditionsProds

    def calcAgeIndex(_age, _list):
        age_index_list = []

        for i in range(len(_list)):
            if _list[i] <= _age:
                age_index_list.append(i)
            else:
                break

        _age_index = max(age_index_list)

        return _age_index

    global age_index
    age_index = calcAgeIndex(_age, age_list)

    def calculateRisk():
        comorbities = calcComorbities(_conditions)
        hosp_odds = riskToOdds(hosp_list_female[age_index]) * comorbities[0]
        icu_odds = riskToOdds(icu_list_female[age_index]) * comorbities[1]
        death_odds = riskToOdds(death_list_female[age_index]) * comorbities[2]

        if _sex == "male":
            hosp_odds = hosp_odds * male_or[0]
            icu_odds = icu_odds * male_or[1]
            death_odds = death_odds * male_or[2]

        total_odds = [hosp_odds, icu_odds, death_odds]
        total_prob = [oddsToRisk(hosp_odds)*100, oddsToRisk(icu_odds)*100, oddsToRisk(death_odds)*100]
        total = [total_odds, total_prob]

        return total_prob

    return calculateRisk()
    #print(calculateRisk())

# def generateGrid():
#     grid = []
#     for x in range(225):
#         for y in range(225):
#             grid.append((x, y))
#     return grid
grid = []
for x in range(225):
    for y in range(225):
        grid.append((x, y))

def generatePopulation(pop_size):
    allAgentData = []
    # This reads as:
    # 6 percent of people in Orleans parish are between 0 and 4 years old
    # 20 - 6 percent of people in Orleans parish are between 5 and 17 years old
    popByAge = [(0.06, 0, 4),
                (0.20, 5, 17),
                (0.37, 18, 29),
                (0.54, 30, 39),
                (0.66, 40, 49),
                (0.78, 50, 59),
                (0.90, 60, 69),
                (1.00, 70, 100)]

    popBySex = [(0.53, "female"),
                (1.0, "male")]

    popByTime = [(0.099, "Less than 10 min", 1),
                 (0.241, "10 to 14 min", 2),
                 (0.438, "15 to 19 min", 3),
                 (0.624, "20 to 24 min", 4),
                 (0.692, "25 to 29 min", 5),
                 (0.845, "30 to 34 min", 6),
                 (0.889, "35 to 44 min", 7),
                 (0.934, "45 to 59 min", 8),
                 (1.000, "60 or more min", 9)]

    # coords = [(1.8, 4),(3.6, 2.6),(2, 0.6),(2.2, -0.4),(2.4, -3.8), (1.8, -3.8), (1.8, -2.2),
    #           (0.6, -1.6),(-0.6, -3.2),(-4.2, -0.2),(-1.6, 2.4),(-0.8, 1.6),(0, 2.2),(0.2, 2)]
    # checkPoly = shapePolygon(coords)

    for i in range(pop_size):
        rnd = random.uniform(0, 1)

        # Assigns agent an age
        for a in range(len(popByAge)):
            if rnd <= popByAge[a][0]:
                _age = random.randint(popByAge[a][1], popByAge[a][2])
                break

        # Assigns agent a sex
        for s in range(len(popBySex)):
            if rnd <= popBySex[s][0]:
                _sex = popBySex[s][1]
                break

        # Assigns agent underlying health conditions
        _conditions = []
        #if rnd <= 0.44:
        if _age >= 18:
            rnd1 = random.uniform(0, 1)
            rnd2 = random.uniform(0, 1)
            rnd3 = random.uniform(0, 1)
            rnd4 = random.uniform(0, 1)
            rnd5 = random.uniform(0, 1)
            rnd6 = random.uniform(0, 1)
            rnd7 = random.uniform(0, 1)
            rnd8 = random.uniform(0, 1)
    
            if rnd1 <= 0.04:
                _conditions.append("renal")
            if rnd2 <= 0.104:
                _conditions.append("cvd")
            if rnd3 <= 0.126:
                _conditions.append("diabetes")
            if rnd4 <= 0.397:
                _conditions.append("hyper")
            if rnd5 <= 0.219:
                _conditions.append("smoker")
            if rnd6 <= 0.086:
                _conditions.append("lung")
            if rnd7 <= 0.359:
                _conditions.append("obesity")
            if rnd8 <= 0.05: # change this later once stats are found
                _conditions.append("other")

            # else:
                # find stats for 18 and under here

        else:
            _conditions = []

        # Assigns agent a travel time
        for t in range(len(popByTime)):
            if rnd <= popByTime[t][0]:
                _travel_time = popByTime[t][1]
                break

        # Assigns agent home coordinates
        _home = random.choice(grid)
        # agentCoord = shapePoint(xh, yh)

        # if agentCoord.within(checkPoly):
        #     _home = (xh, yh)
        # else:
        #     while not agentCoord.within(checkPoly):
        #         wh = random.uniform(-8, 8)
        #         zh = random.uniform(-5, 5)
        #         agentCoord = shapePoint(wh, zh)

        #         if agentCoord.within(checkPoly):
        #             _home = (wh, zh)
        #             break
        #         else:
        #             continue

        # Assigns agent work coordinates
        for w in range(len(popByTime)):
            if _travel_time == popByTime[w][1]:
                xw = _home[0] + (popByTime[w][2] * random.choice([-1, 1]))
                yw = _home[1] + (popByTime[w][2] * random.choice([-1, 1]))
                _work = (xw, yw)
                break
        
        agentRisk = totalRiskCalculator(_age, _sex, _conditions)
        agentData = [i, agentRisk[0], agentRisk[1], agentRisk[2], _travel_time, _home, _work]
        allAgentData.append(agentData)

    return allAgentData

def indexGenerator(pop_size):
    _indexGen = []
    for i in range(pop_size):
        _indexGen.append(i)
    return _indexGen

def createPopDataframe():
    pop = 100
    _allAgentData = generatePopulation(pop)
    indexGen = indexGenerator(pop) 
    agent_df = pd.DataFrame(data=_allAgentData,
                            index=indexGen,
                            columns=['agent', 'hosp risk', 'icu risk', 'death risk', 'travel time', 'home', 'work'])
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    #print(agent_df)

    days = 100
    #currentPos = []

    #Calculates 4 locations of an agent per day
    for d in range(days):
        currentPos = []
        for i in range(pop):
            currentPos.append([agent_df.at[i, 'home'], #start at home
                               agent_df.at[i, 'work'], #go to work
                               random.choice(grid), #go to a random spot (recreation)
                               random.choice(grid), #go to a random spot (recreation)
                               agent_df.at[i, 'home']]) #end at home again
        ds = str(d)
        agent_df['Day ' + ds] = currentPos
        #agent_df['Status ' + ds] = 'S'

    #print(agent_df)
    def generateStatus(_days, _pop):
        _statAgentData = []
        _statAgent = []
        for p in range(_pop):
            _statAgent.append('S')
        for d in range(_days):
            _statAgentData.append(_statAgent)
            
        return _statAgentData

    def common_location(infected, other):
        infected_set = set(infected)
        other_set = set(other)

        return len(infected_set.intersection(other_set)) > 0

    def countDaysInfected(col):
        return (status_df[col].values == 'I').sum()

    statAgentData = generateStatus(days, pop)
    statIndexGen = indexGenerator(days) 
    statColumnGen = indexGenerator(pop)

    status_df = pd.DataFrame(data=statAgentData,
                             index=statIndexGen,
                             columns=statColumnGen)

    #print(status_df)

    #introduce COVID into population
    status_df.at[0, 1] = 'I'
    status_df.at[0, 2] = 'I'
    status_df.at[0, 3] = 'I'


    for d in range(days):
        infectedAgents = status_df.columns[status_df.isin(['I']).any()]
        for i in range(len(infectedAgents)):
            for p in range(pop):
                # Checks if infected agents share a location with other agents
                # If there is a shared location within the same day, the susceptible individual gets infected
                # and is added to the list of infectedAgents for futurre loops
                infect = agent_df.at[infectedAgents[i],'Day '+ str(d)]
                everyone = agent_df.at[p, 'Day ' + str(d)]

                if common_location(infect, everyone):
                    status_df.at[d+1, p] = 'I' 

                # Makes sure that infected people stay contaigious for 12 days 
                # Source:https://www.cdc.gov/flu/symptoms/flu-vs-covid19.htm#:~:text=How%20long%20someone%20can%20spread,or%20symptoms%20first%20appeared.
                if countDaysInfected(infectedAgents[i]) <= 12:
                    status_df.at[d+1, infectedAgents[i]] = 'I'

                    rndH = random.uniform(0, 1)
                #     rndD = random.uniform(0, 1)
                #     if rndH <= agent_df.at[p, 'hosp risk']:
                #         #Day 22: This is the median amount of days it takes for COVID-19 survivors to be released from hospital
                #         for h in range(10):
                #             status_df.at[d+h, p] = 'H'
                #         if rndD <= agent_df.at[p, 'death risk']:
                #             rTime = days - d - 10 
                #             for x in range(rTime):
                #                 r = days - rTime
                #                 status_df.at[r, p] = 'D'
                #         else:
                #             status_df.at[d+11, p] = 'S'
                #     elif rndD <= agent_df.at[p, 'death risk']:
                #         rTime = days - d - 6
                #         for x in range(6):
                #             status_df.at[x+d, p] = 'I'
                #         for y in range(rTime):
                #             r = days - rTime
                #             status_df.at[r, p] = 'D'
                #     else:
                #         status_df.at[d, p] = 'S'

                else:
                    status_df.at[d+1, infectedAgents[i]] = 'S'

    print(status_df)

    #start coding hospitalization and death overwrite here

    
                #elif daysInfected > 12:
                #     #status_df.at[d+1, infectedAgents[i]] = 'S'
                #     rndH = random.uniform(0, 1)
                #     rndD = random.uniform(0, 1)
                #     if rndH <= agent_df.at[p, 'hosp risk']:
                #         #Day 22: This is the median amount of days it takes for COVID-19 survivors to be released from hospital
                #         for h in range(10):
                #             status_df.at[d+h, p] = 'H'
                #         if rndD <= agent_df.at[p, 'death risk']:
                #             rTime = days - d - 10 
                #             for x in range(rTime):
                #                 r = days - rTime
                #                 status_df.at[r, p] = 'D'
                #         else:
                #             status_df.at[d+11, p] = 'S'
                #     elif rndD <= agent_df.at[p, 'death risk']:
                #         rTime = days - d - 6
                #         for x in range(6):
                #             status_df.at[x+d, p] = 'I'
                #         for y in range(rTime):
                #             r = days - rTime
                #             status_df.at[r, p] = 'D'
                #     else:
                #         status_df.at[d, p] = 'S'
                # else:
                #     status_df.at[d+1, p] = 'S'
    # for d in range(days):
    #     for p in range(pop):
    #         if status_df.at[d, p] == 'I':
    #             rndD = random.uniform(0, 1)
    #             rndH = random.uniform(0, 1)
    #             if rndD <= agent_df.at[p, 'death risk']:
    #                 status_df.at[d+1, p] = 'D'
    #             elif rndH <= agent_df.at[p, 'hosp risk']:
    #                 status_df.at[d+1, p] = 'H' 
    #             else:
    #                 status_df.at[d+1, p] = status_df.at[d+1, p]



createPopDataframe()