import pandas as pd 
import matplotlib.pyplot as plt


ahat = pd.ExcelFile("C:\\Users\\Emre\\Desktop\\bilancolar\\SASA.xlsx")

for i in range(0,len(ahat.sheet_names)):
    ahat2 = pd.DataFrame(pd.read_excel(ahat,sheet_name=ahat.sheet_names[i]))

    print(ahat2) 
    
ahat3 = pd.read_excel(ahat)
ahat4 = ahat3.loc[0]

print(ahat4)
