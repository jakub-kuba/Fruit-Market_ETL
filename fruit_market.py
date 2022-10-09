# Author: jakub-kuba

import pandas as pd
import ssl
import numpy as np
from textblob import TextBlob
from textblob import Word
import requests
import bs4
import sys
from datetime import datetime
import time

#import data from engine.py
#from engine import engine
from db_engine import engine

ssl._create_default_https_context = ssl._create_unverified_context


def get_website_date(address):
    """
    Checks if the website has the required elements
    and get quotation date.
    """
    try:
        res = requests.get(address)
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        elems = soup.select('#notowania-data')
    except:
        print("Problem with the source website!")
        sys.exit()
    try:
        date = elems[0].getText()[-10:]
        datetime.strptime(date, '%d.%m.%Y')
    except:
        print("Problem with the source website!")
        sys.exit()
    return date


def get_last_date(table, engine):
    """
    Connects to the database and
    gets the date of the last entry.
    """
    try:
        tab = pd.read_sql_table(table, engine)
    except:
        print("Cannot connect to database!")
        sys.exit()
    if len(tab) == 0:
        result = None
    else:
        get_date = tab['Date'].values[-1]
        result = pd.to_datetime(str(get_date)).strftime('%d.%m.%Y')
    return result


def process_data(no, address, prices, pl_eng_columns, cols):
    """Calculates the average price of the selected fruits."""
    try:
        market = pd.read_html(address)[no]
        market.columns = market.columns.str.lower()
    except:
        print("Website doesn't have the required elements.")
        sys.exit()
    if not set(list(pl_eng_columns.keys())).issubset(market.columns):
        print("The table does not contain the required columns.")
        sys.exit()
        
    market.rename(columns=pl_eng_columns, inplace=True)
    df = market[cols].copy()
    df = df.loc[df['Unit'] == 'kg']
    df = df[df['Name'].notna()]
    df[prices] = df[prices].replace('zł', '', regex=True)
    df[prices] = df[prices].replace(',', '.', regex=True)
    df['Max'] = np.where((df['Max'].isnull()) & (df['Min'].notna()),
                             df['Min'], df['Max'])
    df['Min'] = np.where((df['Min'].isnull()) & (df['Max'].notna()),
                             df['Max'], df['Min'])
    for col in df.columns:
        df[col] = df[col].str.strip()
    df['Name'] = df['Name'].replace(" polska", "", regex=True)
    df[prices] = df[prices].replace(" ", "", regex=True)
    df[prices] = df[prices].replace("-", np.nan, regex=True)
    df[prices] = df[prices].astype(float)
    df['Avarage_Price'] = df[prices].mean(axis=1)
    df['Name'] = df['Name'].str.split(':').str[0]
    df = df.loc[~df['Name'].str.contains('mix')]
    return df


def translate_list(my_list):
    """Translates fruit names from Polish to English."""
    final_list = []
    for f in my_list:
        try:
            blob = TextBlob(f)
            time.sleep(0.5)
            eng = str(blob.translate(from_lang='pl', to='en')).title()
            final_list.append(Word(eng).singularize())
        except:
            print("Connection problem")
            sys.exit()
    return final_list


def create_dataframe(date, row_list):
    """Creates an initial DataFrame with the required rows."""
    first_cols = {'Date': date,
                  'Name': [x for x in row_list]}
    first_df = pd.DataFrame(data=first_cols)
    first_df['Date'] = pd.to_datetime(first_df['Date'], format='%d.%m.%Y')
    return first_df


def map_and_cut(first_df, second_df, poleng_dict):
    """Merges the inital and new DataFrames."""
    second_df['Name'] = second_df['Name'].map(poleng_dict)
    second_df = second_df[['Name', 'Avarage_Price']]
    dfs_merged = pd.merge(first_df,second_df, how='left')
    return dfs_merged


def send_to_db(df, table_name, engine):
    """Updates the database."""
    df.to_sql(
        name=table_name,
        con=engine,
        index=False,
        if_exists='append'
    )


def overwrite_csv(df, csv_file):
    """Adds a new row to an existing csv file."""
    df_pivot = df.pivot_table(index=['Date'], columns=['Name'], dropna=False).droplevel(level=0, axis=1).reset_index()
    df_pivot['Date'] = df_pivot['Date'].astype(str)
    df_source = pd.read_csv(csv_file)
    df_list = [df_source]
    df_list.append(df_pivot)
    df_concat = pd.concat(df_list)
    df_concat.to_csv(csv_file, index=False)
    

def main():
    #variables with column names
    pl_eng_columns = {'nazwa': 'Name',
                      'jednostka': 'Unit',
                      'cena min': 'Min',
                      'cena max': 'Max'}
    prices = ['Min', 'Max']
    cols = ['Name', 'Unit', 'Min', 'Max']

    #fruit we're interested in
    fruit_required = ['Apple', 'Banana', 'Blackberry', 'Blueberry', 'Cherry',
                      'Chokeberry', 'Dark Grape', 'Ginger', 'Grapefruit', 'Hazelnut',
                      'Lemon', 'Lime', 'Orange', 'Peach', 'Pear',
                      'Plum', 'Raspberry', 'Strawberry', 'Tangerine', 'Walnut',
                      'Watermelon', 'White Grape']

    #path to csv file
    fruit_folder = 'files/fruit.csv'
    
    #address of the website with fruit prices
    address = 'https://khrybitwy.pl/notowania_cenowe/ceny-owocow-i-warzyw.html'

    #get the data you needed to connect the DB
    mkt = engine()

    check_date = get_website_date(address)
    my_date = get_last_date('fruit', mkt)

    #my_date = '10.10.2022'

    print("website date:", check_date)
    print("last database date:", my_date)

    if my_date != check_date:
        print("work in progress...")
        #create 1st df
        first_df = create_dataframe(check_date, fruit_required)

        #create 2nd df
        fruit = process_data(0, address, prices, pl_eng_columns, cols)

        #transle 2nd df from PL to ENG
        fruit_list = fruit['Name'].to_list()
        tr_fruit = translate_list(fruit_list)
        eng_fruit = dict(zip(fruit_list, tr_fruit))

        #merge both dfs
        fruit = map_and_cut(first_df, fruit, eng_fruit)

        #update csv
        overwrite_csv(fruit, fruit_folder)

        #update database
        send_to_db(fruit, 'fruit', mkt)

        print("Job complete!")

    else:
        print("No new data on the website.")


if __name__ == "__main__":
    main()