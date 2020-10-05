# Info to be obtained:
# Movie Title
# Keywords
# Genre
# Ratings
# Runtime
# Plot Summary
# Credits

import json
import requests
from selectolax.parser import HTMLParser
from datetime import datetime
import sys
import re

class ImdbMovieInfo():
    def __init__(self, title):
        self.title = title
    
    def get_movie_name(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}")
        content = HTMLParser(r.content)
        movie_name = []
        movie_name_data = content.css("h1")
        movie_name.append(movie_name_data[0].text().strip())
        return movie_name

    def get_keywords(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}/keywords")
        content = HTMLParser(r.content)
        keywords_data = content.css("div.sodatext")
        keywords = []
        if keywords_data is not None:
            for keyword in keywords_data:
                keywords.append(keyword.text().strip())

        return keywords
    
    def get_genre(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}")
        content = HTMLParser(r.content)
        genre_data = content.css("div.see-more.inline.canwrap")
        genres = []
        if genre_data is not None:
            for genre in genre_data[1].text().strip().split():
                if(genre != 'Genres:' and genre != '|'):
                    genres.append(genre)
        return genres

    def get_ratings(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}/ratings")
        p = HTMLParser(r.content)
        div = p.css_first("div.allText")
        output = {}
        fields = div.text().strip().split("\n")
        num_votes = int(fields[0].replace(",",""))
        avg_rating = float(re.search(r"[\d,\.]+", fields[1])[0])
        output['globalRating'] = {}
        output['globalRating']['numVotes'] = num_votes
        output['globalRating']['avgRating'] = avg_rating
        tables = p.css("table")
        fields = tables[0].text().strip().split("\n")

        rating_fields = []
        for f in fields:
            f = f.strip()
            if f != "":
                rating_fields.append(f)

        output['detailedRatings'] = []
        rating_fields = rating_fields[2:]
        for x in range(0,10):
            obj = {}
            rating = int(rating_fields[x*3])
            num_votes = int(rating_fields[(x*3)+2].replace(",",""))
            obj['rating'] = rating
            obj['numVotes'] = num_votes
            output['detailedRatings'].append(obj)

        demographic_data = tables[1].text().strip().split("\n")

        rating_fields = []
        for f in demographic_data:
            f = f.strip()
            if f != "":
                rating_fields.append(f)

        output['demographicRatings'] = {}
        output['demographicRatings']['all'] = {}
        output['demographicRatings']['males'] = {}
        output['demographicRatings']['females'] = {}
        rf = rating_fields
        for idx, f in enumerate(rf[0:5]):
            output['demographicRatings']['all'][f] = {'rating':float(rf[(idx*2)+6]),'numVotes':int(rf[(idx*2)+7].replace(",",""))}
            output['demographicRatings']['males'][f] = {'rating':float(rf[(idx*2)+17]),'numVotes':int(rf[(idx*2)+18].replace(",",""))}
            output['demographicRatings']['females'][f] = {'rating':float(rf[(idx*2)+28]),'numVotes':int(rf[(idx*2)+29].replace(",",""))}

        return output
    
    def get_runtime(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}/technical")
        content = HTMLParser(r.content)
        tech_data = content.css("tr.odd")
        runtime = []
        if( tech_data[0].text().strip().split()[0] == 'Runtime' ):
            runtime.append(" ".join(tech_data[0].text().strip().split()[1:]))
            return runtime
        return runtime

    def get_plot_summary(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}/plotsummary")
        p = HTMLParser(r.content)
        summaries = []
        summaries_data = p.css("li.ipl-zebra-list__item")
        if summaries_data is not None:
            for summary in summaries_data:
                obj = {}
                obj['author'] = None
                author_data = summary.css_first("div.author-container")
                if author_data is not None:
                    obj['author'] = author_data.text().strip()
                summary.strip_tags(["div.author-container"])
                obj['summary'] = summary.text().strip()
                summaries.append(obj)

        return summaries
    
    def get_credits(self):
        r = requests.get(f"https://www.imdb.com/title/{self.title}/fullcredits")
        p = HTMLParser(r.content)
        tables = p.css("h4.dataHeaderWithBorder + table.simpleCreditsTable")
        headers = p.css("h4.dataHeaderWithBorder:not([id])")

        main_cast = []

        for idx, table in enumerate(tables):
            trs = table.css("tr")
            category = headers[idx].text().strip()
            for tr in trs:
                actor = {}
                td = tr.css("td")
                a = td[0].css_first("a")
                if a is not None:
                    actor['id'] = a.attrs['href'].split("?",1)[0]
                    actor['name'] = a.text().strip()
                else:
                    continue
                if len(td) > 2:
                    actor['description'] = td[2].text().strip()
                actor['category'] = category
                main_cast.append(actor)

        cast_list = p.css_first("table.cast_list")
        rows_odd = cast_list.css("tr.odd")
        rows_even = cast_list.css("tr.even")
        rows = [val for pair in zip(rows_odd, rows_even) for val in pair] # Join rows by interleaving to maintain order

        for row in rows:
            actor = {}
            actor['category'] = "Cast"
            tds = row.css("td")
            actor['image_link'] = None
            photo = tds[0].css_first("a")
            if photo is not None:
                img = photo.css_first("img")
                if img is not None:
                    if 'loadlate' in img.attrs:
                        actor['image_link'] = img.attrs['loadlate']

            a = tds[1].css_first("a")
            actor['actor_id'] = a.attrs['href'].strip().rsplit("/",1)[0]
            actor['actor_name'] = a.text().strip()
            a = tds[3].css_first("a")
            if a is not None and a.attrs['href'] != "#":
                actor['character_id'] = a.attrs['href'].strip().rsplit("?",1)[0]
                actor['character_name'] = a.text().strip()
            else:
                actor['character_name'] = re.sub(' +', ' ', tds[3].text().strip().replace("\n",""))
            main_cast.append(actor)

        return main_cast
    
data = {}
title = None
if len(sys.argv) < 2:
    print ("You can provide title for movie as Command Line Argument (e.g. 'tt0123456')")
    print("Default movie title: tt4154796")
    title = "tt4154796"
if title is None:
    title = sys.argv[1]

movie_info = ImdbMovieInfo(title)
print("Fetching name for title from IMDB.")
data['name'] = movie_info.get_movie_name()
print('Fetching keywords for title from IMDB.')
data['keywords'] = movie_info.get_keywords()
print('Fetching genres for title from IMDB.')
data['genres'] = movie_info.get_genre()
print("Fetching extended ratings from IMDB.")
data['ratings'] = movie_info.get_ratings()
print('Fetching Runtime for title from IMDB.')
data['runtime'] = movie_info.get_runtime()
print('Fetching plot summaries for title from IMDB.')
data['summaries'] = movie_info.get_plot_summary()
print("Fetching full credits from IMDB.")
data['credits'] = movie_info.get_credits()

filename = './'+title+'.json'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
