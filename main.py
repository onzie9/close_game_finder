from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

columns = ["Player", "game_url", "player1_score", "player2_score", "final_score_difference"]
data = []
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}

# Find high-ranking players first.

base_url = 'https://www.cross-tables.com/'
r = requests.get(base_url, headers=headers)
base_soup = BeautifulSoup(r.text, "html.parser")

top_players = []

for row in range(1, 21):
    player = base_soup.find("tr", {"id": "rowtopplayers" + str(row)})
    url = player.find("a", href=True)
    name = player.find("a", href=True).contents[0]
    name = name.split("\t")[0]
    annotated_games = url['href'].replace("results", "anno")
    top_players.append([name, url['href'], annotated_games])

for tp in top_players:

    r = requests.get("https://www.cross-tables.com/" + tp[2], headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    games = soup.find_all("tr", id=re.compile("row"))
    num_games = len(games)

    for game in range(1,num_games):
        game_url = soup.find("tr", id="row" + str(game))
        game_url = str(game_url)
        game_url = game_url.split('href="')[1].split('">View')[0]
        annotated_game = requests.get("https://www.cross-tables.com/" + game_url, headers=headers)
        annotated_soup = BeautifulSoup(annotated_game.text, "html.parser")

        moves = annotated_soup.find_all("a", id=re.compile('moveselector'))
        num_moves = 0
        for m in moves:
            try:
                move_number = int(m.contents[0])
                if move_number > num_moves:
                    num_moves = move_number
            except:
                continue

        final_score_url = game_url + "#%0.0f#" % (num_moves)

        final_score_source = requests.get(base_url + final_score_url, headers=headers)
        final_score_soup = BeautifulSoup(final_score_source.text, "html.parser")
        try:
            player1_score = int(str(final_score_soup).split('playermove0" style="display: none; text-align: right;">')[-1].split('</td')[0])
            player2_score = int(str(final_score_soup).split('playermove1" style="display: none; text-align: right;">')[-1].split('</td')[0])
            if abs(player1_score-player2_score)<=3:
                data.append([tp[0], "https://www.cross-tables.com/" + game_url, player1_score, player2_score, abs(player1_score-player2_score)])
            if len(data) > 10:
                print(len(data))
                df = pd.DataFrame(columns=columns, data=data)
                df.to_csv('close_games.csv', index=False)
        except ValueError:
            continue
