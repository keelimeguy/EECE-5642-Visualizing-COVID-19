from .covid_data import CovidDataset
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np



def test(self):
    print(self)

def plot_chart_and_table(dataset):
    # Create a new dataset:
    confirmed = dataset.get_datapoints()
    deaths = dataset.get_datapoints(target='Deaths')
    confirmed = pd.concat([confirmed,deaths], axis=1, sort=False)

    # calculate death ratio
    confirmed['death_ratio'] = confirmed['Deaths']/confirmed['Confirmed']
    print('\n')
    print('Calculate death_ratio for all countries (unsorted)')
    print("-----------------------------------------------------")
    print(confirmed)

    # calculate death_ratio and confirmed_after_5_days for top 10 countries
    print('\n')
    print("Calculate death_ratio and confrimed_after_5_days for top 10 countries")
    print("-------------------------------------------------------------------------------------------")
    
    # get top 10 
    top10 = confirmed.nlargest(10, 'Confirmed')

    # growth ratio, calculated based on the source data
    # source: https://ourworldindata.org/coronavirus
    top10['growth_rate'] = [0.125, 0.077, 0.059, 0.083, 0.091, 0.016, 0.071, 0.125, 0.167, 0.11]
    
    # predict the confirmed cases for each country after 5 days
    # final result would be round up to an integer
    day = 5 # change the value of 'day' to predict the amount of confirmed cases for different date
    top10['confirmed_after_5_days'] = round((top10['growth_rate'] * day + 1) * top10['Confirmed'])
    test(top10)

    # plot chart
    width = .3 # width of bar
    # Set position of bar on X axis
    r1 = np.arange(len(top10['Confirmed']))
    r2 = [x + width for x in r1]
    r3 = [x + width for x in r2]
    
    # create figure and axis objects with subplots()
    fig,ax = plt.subplots()
    
    # Add xticks on the middle of the group bars
    ax.set_xlabel('countries', fontweight='bold')
    ax.set_ylabel('cases', fontweight='bold')
    plt.xticks([r + width for r in range(len(top10['Confirmed']))], list(top10.index.values))
    plt.xticks(rotation=30)
    
    # Make the plot
    ax.bar(r1, top10['Confirmed'], color='blue', width=width, label='Confirmed')
    ax.bar(r2, top10['Deaths'], color='grey', width=width, edgecolor='white', label='Deaths')
    ax.bar(r3, top10['confirmed_after_5_days'], color='red', width=width, edgecolor='white', label='After 5 Days Confirmed')

    # twin object for two different y-axis on the sample plot
    ax2 = ax.twinx()

    # Add ratio plots
    ax2.plot(list(top10.index.values),top10['death_ratio'],color='brown', marker='o', label= 'death ratio')
    ax2.plot(list(top10.index.values),top10['growth_rate'],color='purple', marker='^', label = 'confrimed case growth rate')
    ax2.set_ylabel('ratio', fontweight='bold')
    plt.title('Top 10 Countries Confirmed Cases (COVID-19) w/ Predication')
 
    # Create legend & Show graphic  
    ax.legend(loc=0)
    plt.legend()
    plt.show()
