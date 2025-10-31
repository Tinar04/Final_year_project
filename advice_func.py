from advice_data import advise_18_21, advise_22_60
import random

# advice functions for age group 18-21 people
def get_advice_18_21(user_input, result):
     stress_map = {0: "Low", 1: "Medium", 2: "High"}
     stress_level = stress_map.get(result,"Low")
     advice_list = []
    

    # indexs
     indexs_of_data = [0,6,13,14,15,19]

    #  loop through eah column
     for index,key in enumerate(user_input.keys()):
          if index in indexs_of_data and index in advise_18_21:
              column_advice = advise_18_21[index]
              if stress_level in column_advice:
                   advice_list.append(random.choice(column_advice[stress_level]))

     if not advice_list:
          advice_list.append("Keep maintaining a healthy lifestyle and manage stress effectively.")
     return advice_list  
    