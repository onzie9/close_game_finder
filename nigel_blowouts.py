# At the request of Will Anderson, this code is to find all the annotated Nigel Richards losses.

from bs4 import BeautifulSoup
import requests
import re
import pandas as pd


def find_vs_context(input_string):
    # Find the index of "vs."
    index = input_string.find("vs.")

    # If "vs." is found, return 100 characters before and after it
    if index != -1:
        start_index = max(0, index - 100)  # Ensure we don't go below the start of the string
        end_index = min(len(input_string), index + 103)  # 3 characters after "vs."
        return input_string[start_index:end_index]
    else:
        return "Substring 'vs.' not found."


def extract_player(input_string, player_one: bool=True):
    # Define the regular expression pattern to match text between '-->' and '<a'
    if player_one:
        pattern = r'-->(.*?)<a'
    else:
        pattern = r'vs(.*?)<a'

    # Use re.search to find the first match
    match = re.search(pattern, input_string, re.DOTALL)

    # If a match is found, return the matched group (the text between '-->' and '<a')
    if match:
        if player_one:
            return match.group(1)[4:-1]
        else:
            return match.group(1)[2:-1]
    else:
        return "No match found"


columns = ["Player", "game_url", "Nigel_score", "player2_score", "Nigel_loss", "Player 2"]
data = []
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}

# Find high-ranking players first.

base_url = 'https://www.cross-tables.com/'
nigel_url = 'https://www.cross-tables.com/anno.php?p=6003'

for tp in [nigel_url]:

    r = requests.get(tp, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    games = soup.find_all("tr", id=re.compile("row"))
    num_games = len(games)
    print(num_games)
    for game in range(1,num_games):
        game_url = soup.find("tr", id="row" + str(game))
        game_url = str(game_url)
        try:
            game_url = game_url.split('href="')[1].split('">View')[0]
        except IndexError:
            continue
        annotated_game = requests.get("https://www.cross-tables.com/" + game_url, headers=headers)
        annotated_soup = BeautifulSoup(annotated_game.text, "html.parser")

        vs_str = find_vs_context(str(annotated_soup))
        player_1 = extract_player(vs_str)
        player_2 = extract_player(vs_str,player_one=False)

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
        #print(final_score_soup)
        try:
            player1_score = int(str(final_score_soup).split('playermove0" style="display: none; text-align: right;">')[-1].split('</td')[0])
            player2_score = int(str(final_score_soup).split('playermove1" style="display: none; text-align: right;">')[-1].split('</td')[0])
            if player_1 == 'Nigel Richards':
                nigel_score = player1_score
                p2_score = player2_score
            else:
                nigel_score = player2_score
                p2_score = player1_score
                player_2 = player_1
            if p2_score > nigel_score:
                data.append([tp[0], "https://www.cross-tables.com/" + game_url, nigel_score, p2_score, abs(player1_score-player2_score), player_2])
            if len(data) > 10:
                df = pd.DataFrame(columns=columns, data=data)
                df.to_csv('nigel_batch.csv', index=False)
        except ValueError:
            print("failed")
            print(final_score_url)
            continue
