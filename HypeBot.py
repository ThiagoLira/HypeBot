from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
from bs4 import BeautifulSoup
import re
from pytube import Search        

games_buffered = {}
last_plataform_requested = 'PC'

def get_releases_metacritic_builder(link):

    def get_releases_base():
        user_agent = {'User-agent': 'Mozilla/5.0'}
        html = requests.get(link,headers=user_agent).text
        soup = BeautifulSoup(html,'lxml')
        categories = soup.find_all('div',class_='product_group_items')    
        results = {}
        for sp in categories:
            plataform = sp.find(class_='group-title').text
            list_games = sp.find('table').find_all('a','title')
            list_dates = sp.find('table').find_all('div','clamp-details')        
            list_scores = sp.find('table').find_all('div','metascore_w')
            list_links = sp.find('table').find_all('a','title') 
            
            links_plataform = list(map(lambda x:f"https://www.metacritic.com{x['href']}",list_links))
            scores_plataform = [score.text for score in list_scores]
            games_plataform = list(map(lambda x:x.text,list_games))
            dates_plataform = list(map(lambda x:x.find_all('span')[2].text,list_dates[1:]))

            # store for later use by get_trailer function
            global games_buffered 
            games_buffered[plataform] = games_plataform
            
            results[plataform] = list(zip(games_plataform,dates_plataform,scores_plataform, links_plataform)) 
            

        return results

    return get_releases_base

link_upcoming_metacritic = "https://www.metacritic.com/browse/games/release-date/coming-soon/all/date"
link_last_metacritic = "https://www.metacritic.com/browse/games/release-date/new-releases/all/date"

get_last_releases_metacritic = get_releases_metacritic_builder(link_last_metacritic)
get_upcoming_releases_metacritic = get_releases_metacritic_builder(link_upcoming_metacritic)

def parse_new_releases_open_critic():
    link = "https://opencritic.com/browse/all/upcoming/date"

    user_agent = {'User-agent': 'Mozilla/5.0'}

    html = requests.get(link,headers=user_agent).text

    soup = BeautifulSoup(html,'lxml')

    games = soup.find('div',class_='desktop-game-display').find_all(class_='row no-gutters py-2 game-row align-items-center')
    results = {}
    base_link = "https://opencritic.com"

    for g in games:
        plataforms = g.find(class_='platforms col-auto' ).text.split(',')
        plataforms = list(map(lambda x:x.strip(),plataforms))
        game_element = g.find(class_='game-name col').find('a')
        game_title,game_link = game_element.text,base_link + game_element['href']
        score = g.find(class_='score col-auto').text
        release_date = g.find(class_='first-release-date col-auto show-year').text
        score = '?' if score == ' ' else score
        for plataform in plataforms:
            if plataform not in results:
                results[plataform] = []
            results[plataform].append((game_title,release_date,score,game_link))
            
            # store for later use by get_trailer function
            global games_buffered
            if plataform not in games_buffered:
                games_buffered[plataform] = []
            games_buffered[plataform].append(game_title)

    # results is a dict indexed by plataform
    # each entry is a list of tuples (game,date,score)
    return results


    
def dict_to_markdown(dic,plataform):
    out = ""
    
    pts = ""
    for pt in dic.keys():
        pts += pt + ', '
    
    
    # filter dict by selected plataforms
    dic = {key:value for key,value in dic.items() if key in plataform}
    
    if not dic:
        out += "Meu parça, escreve direito alguma plataforma se não você não me ajuda a te ajudar.\n\n"

        out += f"Você pode pedir das plataformas: {pts}"
        return out
    
    for key,value in dic.items():
        out+=f"*{key}* \n"
        for idx,(game,date,score,link) in enumerate(value):
            out+=f"{idx+1}) {game}: {date} (Metacritic Score: {score}) [LINK]({link})\n"
        out+="\n"

    out+="Para pedir um trailer digite o comando /gettrailer NUMEROJOGO.\n"
    return out

def get_last_releases(update,context):
    
    
    plataform = context.args
    if (not plataform):
        plataform = ['PC']
    
    markdown_output = dict_to_markdown(get_last_releases_metacritic(),plataform)
    update.message.reply_markdown(text=markdown_output)

def get_upcoming_releases(update,context):
    
    
    plataform = context.args
    if (not plataform):
        plataform = ['PC']
    
    markdown_output = dict_to_markdown(get_upcoming_releases_metacritic(),plataform)
    update.message.reply_markdown(text=markdown_output)

def get_trailer(update,context):
    out = ''

    global games_buffered
    if (games_buffered):
        game_number = context.args
        if (not game_number):
            game_number = 1
        else:
            game_number = int(game_number[0])

        game_title = games_buffered[last_plataform_requested][game_number-1]
        print(f"Procurando titulo {game_title}")
        # query game title on youtube
        query = f"{game_title} trailer"
        query = query.replace(' ','+')
        query = query.replace(':',' ')

        link = Search(query).results[0].watch_url

        if(link):
            out = link 
        else:
            out = "Não encontrei nenhum trailer"
    else:
        out = "Use primeiro o comando \/lastreleases ou \/upcomingreleases para receber uma lista de jogos." 
    
    update.message.reply_text(text=out)

def main():

    # read key from file and create bot
    with open('key','r') as f:
        key = f.read()
    updater = Updater(key,use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('lastreleases',get_last_releases))
    dp.add_handler(CommandHandler('upcomingreleases',get_upcoming_releases))
    dp.add_handler(CommandHandler('get_trailer',get_trailer))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
