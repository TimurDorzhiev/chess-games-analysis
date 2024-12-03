import chess
import chess.svg
from flask import Flask, render_template
import pandas as pd
import plotly.express as px


# Создаем Flask-приложение
app = Flask(__name__)


# Загружаем данные
# from Kaggle https://www.kaggle.com/datasets/datasnaek/chess/data
data = pd.read_csv('data/games.csv')
print(data.columns)

# Переименуем столбцы для удобства (опционально)
data.rename(columns={
    'id': 'game_id',
    'moves': 'moves',
    'opening_name': 'opening_name',
    'winner': 'result'
}, inplace=True)

# Оставим только нужные столбцы
columns_to_keep = ['game_id', 'moves', 'opening_name', 'result']
data = data[columns_to_keep]

# Удалим строки с пропущенными значениями
data.dropna(inplace=True)

print(data.head())

# Главная страница: список игр


@app.route('/')
def index():
    games = data[['game_id', 'opening_name', 'result']].to_dict(
        orient='records')
    return render_template('index.html', games=games)

# Страница конкретной игры: отображение шахматной доски


@app.route('/game/<string:game_id>')
def show_game(game_id):
    # Получаем данные игры
    game = data[data['game_id'] == game_id]
    if game.empty:
        return "Game not found", 404
    game = game.iloc[0]

    # Преобразуем ходы
    board = chess.Board()
    uci_moves = []
    for move in game['moves'].split():
        try:
            uci_move = board.parse_san(move)
            uci_moves.append(uci_move.uci())
            board.push(uci_move)
        except ValueError as e:
            print(f"Ошибка хода '{move}': {e}")
            return f"Invalid move detected: {move}", 400

    # Проверяем результат
    print(f"Переданные UCI-ходы: {uci_moves}")

    # Передаём в шаблон
    return render_template('game.html', moves=" ".join(uci_moves))


@app.route('/analysis')
def analysis():
    # Общая статистика
    total_games = len(data)
    result_distribution = data['result'].value_counts()

    # Генерация графиков
    result_chart = get_result_distribution_chart(data)
    game_length_chart = get_game_length_chart(data)

    return render_template(
        'analysis.html',
        total_games=total_games,
        result_distribution=result_distribution.to_dict(),
        result_chart=result_chart,
        game_length_chart=game_length_chart


    )


# Распределение результатов
def get_result_distribution_chart(data):
    result_counts = data['result'].value_counts()
    fig = px.pie(
        names=result_counts.index,
        values=result_counts.values,
        title='Result Distribution'
    )
    return fig.to_html(full_html=False)


# (Опционально) Распределение длины игр
def get_game_length_chart(data):
    data['move_count'] = data['moves'].apply(lambda x: len(x.split()))
    fig = px.histogram(
        data,
        x='move_count',
        title='Distribution of Game Length',
        labels={'move_count': 'Number of Moves'}

    )
    return fig.to_html(full_html=False)


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
