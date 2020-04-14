"""
Final Project
Data Visualization
EECE5642 - V30, Spring 2020

by Yiwen Ma, Apr 2020
"""

from .covid_data import CovidDataset
from .utils.progress_tracker import ProgressTracker
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

    # helper function that prints a percentage progress bar
    with ProgressTracker('finding growth rates') as progress:

        top10_countries = list(top10.index)

    # iterate over timestamps in reverse
        for i, date in enumerate(dataset.all_dates[::-1]):
            data_at_date = dataset.get_datapoints(date=date)
            for country in top10_countries.copy():
                ratio = top10.loc[country]['Confirmed'] / data_at_date.loc[country]['Confirmed']

                if ratio >= 2.0:
                    # stop searching for this country when we find doubling point
                    top10_countries.remove(country)
                    # growth ratio, calculated based on the source data
                    top10.at[country, 'growth_rate'] = ratio / (2*i)
                    progress.add(10)

            # break when we found growth rate for each top 10 country
            if not top10_countries:
                break
    
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
    ax2.plot(list(top10.index.values),top10['death_ratio'],color='green', marker='o', label= 'death ratio')
    ax2.plot(list(top10.index.values),top10['growth_rate'],color='purple', marker='^', label = 'confrimed case growth rate')
    ax2.set_ylabel('ratio', fontweight='bold')
    plt.title('Top 10 Countries Confirmed Cases (COVID-19) w/ Predication')
 
    # Create legend & Show graphic  
    ax.legend(loc=0)
    plt.legend(loc='upper left')
    plt.show()
