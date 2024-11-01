from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Example DataFrame
data = {'Player': ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 
                   'Grace', 'Henry', 'Ivy', 'Jack'],
        'Score': [98, 95, 92, 90, 89, 88, 85, 84, 82, 80]}
df = pd.DataFrame(data)

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    if request.method == 'POST':
        player_name = request.form.get('player')
        if player_name in df['Player'].values:
            score = df[df['Player'] == player_name]['Score'].values[0]
            result = f'{player_name} has a score of {score}.'
        else:
            result = 'Player not found. Please try again.'
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=False)
