#conda activate base, cd C:\Users\Sikma\Jupyter\whatcountry, python whatcountryFlask.py

from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
import plotly.express as px
app = Flask(__name__)
app.secret_key = 'KiciaKora'  # Klucz do sesji (zmień na bezpieczny w produkcji)


df_countries = pd.read_csv('world_data.csv')
df_countries = df_countries.drop(df_countries[df_countries['Country'].isin(['Palestinian National Authority', 'Vatican City'])].index)
df_countries.loc[df_countries['Country']=='Libya','Capital/Major City'] = 'Trypolis'
df_countries.loc[df_countries['Country']=='Singapore','Capital/Major City'] = 'Singapore'
df_countries.loc[df_countries['Country']=='S�����������','Country'] = 'Sao Tome and Principe'
df_countries.loc[df_countries['Country']=='Sao Tome and Principe','Capital/Major City'] = 'Sao Tome'
df_countries.loc[df_countries['Country']=='Sao Tome and Principe','Latitude'] = 0.255436
df_countries.loc[df_countries['Country']=='Sao Tome and Principe','Longitude'] = 6.602781
df_countries['Armed Forces size'] = df_countries['Armed Forces size'].fillna(0)

df_countries = df_countries[['Country',
                'Density\n(P/Km2)', 
              'Land Area(Km2)',
              'Armed Forces size',
              'Birth Rate',
              'Capital/Major City',
              'Fertility Rate',
              'Forested Area (%)',
              'GDP',
              'Infant mortality',
              'Life expectancy',
              'Population',
              'Latitude',
              'Longitude']]
df_countries["color"] = 0 
#df_countries.loc[df_countries['Country']=='Poland','color'] = 1
df_countries['Density\n(P/Km2)'] = df_countries['Density\n(P/Km2)'].replace({',': ''}, regex=True).astype(int)
df_countries['Land Area(Km2)'] = df_countries['Land Area(Km2)'].replace({',': ''}, regex=True).astype(int)
df_countries['Armed Forces size'] = df_countries['Armed Forces size'].replace({',': ''}, regex=True).astype(int)
df_countries['Population'] = df_countries['Population'].replace({',': ''}, regex=True).astype(int)

df_countries['Forested Area (%)'] = df_countries['Forested Area (%)'].replace({r'[%]': ''}, regex=True).astype(float)
df_countries['GDP'] = df_countries['GDP'].replace({r'[,\$]': ''}, regex=True).astype(float)

df_countries.reset_index(drop=True, inplace=True)


def edit_distance(x, y, cost_insert=1, cost_delete=1, cost_replace=1):
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i * cost_delete
    for j in range(n + 1):
        dp[0][j] = j * cost_insert

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i-1] == y[j-1]:  #to samo
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i-1][j] + cost_delete,  # usunięcie x[i-1]
                               dp[i][j-1] + cost_insert,  # wstawienie y[j-1]
                               dp[i-1][j-1] + cost_replace)  # zamiana x[i-1] na y[j-1]
    if (dp[m][n]) < 4:
        similarity = 'Capitals names similar in some ways\n'
    else:
        similarity = 'Capitals names not so similar\n'

    return similarity

def compare_countries(df_country_to_guess, df_user_answer):
    columns_to_choose = (df_country_to_guess.columns.intersection(df_user_answer.columns)).tolist()
    columns_to_choose.remove('Country')
    columns_to_choose.remove('Latitude')
    columns_to_choose.remove('Longitude')
    columns_to_choose.remove('color')

    results = []

    for i in range(5):
        chosen_column = random.choice(columns_to_choose)

        if (chosen_column == 'Capital/Major City'):
            similarity = edit_distance(df_country_to_guess[chosen_column].iloc[0], df_user_answer[chosen_column].iloc[0])
            results.append(f'{chosen_column}: \n{similarity}')
        else:
            if (df_country_to_guess[chosen_column].iloc[0] > df_user_answer[chosen_column].iloc[0]):
                results.append(f'{chosen_column}: \naim higher')
            else:
                results.append(f'{chosen_column}: \naim lower')
                
        columns_to_choose.remove(chosen_column)

    if df_country_to_guess['Latitude'].iloc[0] > df_user_answer['Latitude'].iloc[0] and df_country_to_guess['Longitude'].iloc[0] > df_user_answer['Longitude'].iloc[0]:
        results.append('Go northern-east')
    elif df_country_to_guess['Latitude'].iloc[0] > df_user_answer['Latitude'].iloc[0] and df_country_to_guess['Longitude'].iloc[0] < df_user_answer['Longitude'].iloc[0]:
        results.append('Go northern-west')
    elif df_country_to_guess['Latitude'].iloc[0] < df_user_answer['Latitude'].iloc[0] and df_country_to_guess['Longitude'].iloc[0] > df_user_answer['Longitude'].iloc[0]:
        results.append('Go southern-east')
    elif df_country_to_guess['Latitude'].iloc[0] < df_user_answer['Latitude'].iloc[0] and df_country_to_guess['Longitude'].iloc[0] < df_user_answer['Longitude'].iloc[0]:
        results.append('Go southern-west')
    
    return results



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'history' not in session:
        session['history'] = []

    if request.method == 'POST':
        user_answer = request.form['user_answer']
        country_to_guess = request.form['country_to_guess']
        
        df_user_answer = df_countries[df_countries['Country'] == user_answer]
        df_country_to_guess = df_countries[df_countries['Country'] == country_to_guess]
        df_country_to_guess = df_country_to_guess.dropna(axis=1)

        if not df_user_answer.empty and not df_country_to_guess.empty:
            comparison_results = compare_countries(df_country_to_guess, df_user_answer)
            if user_answer == country_to_guess:
                comparison_results.append('Brawo, odgadłeś/aś!')

            session['history'].append({'user_answer': user_answer, 'results': comparison_results})
            session.modified = True  # Zapisujemy zmiany w sesji

        return render_template('game.html', results_html=comparison_results, country_to_guess_html=country_to_guess, history=session['history'], user_answer_html=user_answer, map_html=generate_map())

    country_to_guess = random.choice(df_countries['Country'])
    session['history'] = []
    session.modified = True

    return render_template('game.html', country_to_guess_html=country_to_guess, history=[], results_html=[], user_answer_html=None, map_html=generate_map())


def generate_map():
    # Tworzymy mapę choropleth w jednym kolorze
    fig = px.choropleth(df_countries, 
                        locations="Country", 
                        locationmode="country names",
                        color="color",  
                        color_continuous_scale=[[0, "lightblue"], [1, "lightblue"]])  # Ustawienie jednolitego koloru
    #fig.update_layout(coloraxis_showscale=False, width=400, height=250, margin=dict(t=0, b=0, l=0, r=0))
    fig.update_layout(
        coloraxis_showscale=False, 
        margin=dict(t=0, b=0, l=0, r=0), 
        autosize=True,
        modebar_remove=['zoomin', 'zoomout', 'pan', 'lasso', 'select', 'reset', 'toImage'],
    )

    # Generujemy mapę w formacie HTML
    return fig.to_html(full_html=False, include_plotlyjs='cdn', config=({"responsive": True}, {'displayModeBar': False}))

if __name__ == '__main__':
    app.run(debug=True)