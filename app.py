'''
Script to extract data faor each keywords from api.keywordseverywhere.com

'''

import streamlit as st
import pandas as pd
import requests
import os
import time
from countries import country
from currencies import currency
import json
import datetime

API_KEY = '5950067cd49519c3e277'        #change api key here

st.title('Get keywords volume App :zap:')
st.sidebar.header('Configure request parameter')
#Country  Dropdown
countryDF = pd.DataFrame()
countryDF['Code']=[x for x in country.keys()]
countryDF['Country']=[y for y in country.values()]

sel_country = st.sidebar.selectbox('Select Country',countryDF['Country'],index=0)
req_countryID = countryDF.loc[countryDF['Country'] == sel_country, 'Code'].iloc[0]

#Currency Dropdown
currencyDF = pd.DataFrame()
currencyDF['Code']=[x for x in currency.keys()]
currencyDF['Country']=[y for y in currency.values()]

sel_currency = st.sidebar.selectbox('Select Currency',currencyDF['Country'],index=0)
req_currencyID = currencyDF.loc[currencyDF['Country'] == sel_currency, 'Code'].iloc[0]



#Data Source Dropdown
data_source_list=('gkp','cli')

sel_datasource = st.sidebar.selectbox('Select Data Source',data_source_list,0)

num_key_req= st.sidebar.number_input('Keywords per request',min_value=1,max_value=100,value=5)

my_data = {
    'country': str(req_countryID),
    'currency': str(req_currencyID),
    'dataSource': str(sel_datasource),
    'kw[]': []
}

my_headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer '+ API_KEY
}
if st.button("View configuration") :
    st.json(my_data)
# Make unique filename
timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%X")
filecountry = req_countryID if req_countryID !="" else 'global'
filecurrency = req_currencyID if req_currencyID !="" else 'usd'
outfiledefault='out_'+filecountry+'_'+filecurrency+'_'+sel_datasource+'_'+timestamp+'.csv'
outfilename=outfiledefault.replace(':','-')

#Upload file
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

i = 0
if uploaded_file is not None:
    #outfilename = st.text_input('Enter output file name', value=outfiledefault)
    if st.button('Send Request'):
        if uploaded_file is not None:

            start_time = time.time()
            df = pd.DataFrame(columns=["Keyword", "Search volume", 'CPC', 'Currency', 'Competition'])
            x = 13
            now = time.localtime()
            months = [time.localtime(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0)))[:2] for n in
                      range(1, x)]

            monthheaders = []
            for y, m in months:
                monthString = datetime.date(y, m, 1).strftime('%b') + ' ' + str(y)
                monthheaders.append(monthString)

            headers = ["Keyword", "Search volume", 'CPC', 'Currency', 'Competition'] + monthheaders

            df = pd.DataFrame(columns=headers)

            df.to_csv(outfilename, mode='w', index=False)       #write headers once
            progress_bar = st.progress(0)
            with st.spinner('Fetching Keywordseverywhere API...'):
                for df in pd.read_csv(uploaded_file, iterator=True, chunksize=num_key_req):

                    if i <70 :
                        i = i + 1

                    req_keywords=df['Keyword'].tolist()
                    my_data['kw[]'] = req_keywords
                    # print("Accessing",my_data)

                    response = requests.post('https://api.keywordseverywhere.com/v1/get_keyword_data', data=my_data,
                                             headers=my_headers)

                    if response.status_code == 200:
                        req_response=response.json()
                        print("API response OK : 200")
                    else :
                        st.error("An error occurred ", response.content.decode('utf-8'))
                        print("Error  ocuured while processing keywords \n ",req_keywords)
                        continue


                    keyword = []
                    volume = []
                    cpc = []
                    currency = []
                    competition = []
                    monthdict = {"m1": [], "m2": [], "m3": [], "m4": [], "m5": [], "m6": [], "m7": [], "m8": [],
                                 "m9": [], "m10": [], "m11": [], "m12": []}

                    with open('response.txt', 'w') as outfile:
                        json.dump(req_response,outfile)
                    data = req_response.get('data')
                    #some times response data contains list type object and some time dicttionary handling both cases

                    if type(data) is list:

                        for row in data:

                            keyword.append(row['keyword'])
                            volume.append(row['vol'])
                            cpc.append(row['cpc']['value'])
                            currency.append(row['cpc']['currency'])
                            competition.append(row['competition'])
                            j = 1
                            # add monthly trends
                            for tr in row['trend']:
                                monthdict['m' + str(j)].append(tr['value'])
                                j += 1
                            if j == 1:
                                for k in range(1, 13):
                                    monthdict['m' + str(k)].append("0")

                    else :
                        for row in data.values():
                            # print("dict")
                            keyword.append(row['keyword'])
                            volume.append(row['vol'])
                            cpc.append(row['cpc']['value'])
                            currency.append(row['cpc']['currency'])
                            competition.append(row['competition'])
                            j = 1
                            #add monthly trends
                            for tr in row['trend']:
                                monthdict['m' + str(j)].append(tr['value'])
                                j += 1
                            if j == 1:
                                for k in range(1, 13):
                                    monthdict['m' + str(k)].append("0")


                    df['Keyword'] = keyword
                    df['Search volume'] = volume
                    df['CPC'] = cpc
                    df['Currency'] = currency
                    df['Competition'] = competition
                    j = 12
                    for month in monthheaders:
                        df[month] = monthdict['m' + str(j)]
                        j = j - 1

                    df.to_csv(outfilename, mode='a', header=False, index=False)

                    progress_bar.progress(i)

            progress_bar.progress(100)

            st.success(" :sunglasses: Completed  in " + format(time.time() - start_time, '.2f') + " seconds")
            st.markdown(":white_check_mark: **Output saved to file:** "+os.getcwd()+os.sep+outfilename)

            st.write(pd.read_csv(outfilename))


        else:
            st.error("Please Upload CSV file first")





