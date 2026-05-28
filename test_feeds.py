import feedparser
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# All candidate feeds grouped by category
candidates = {
    "International": [
        ("BBC World News", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("CNN World", "http://rss.cnn.com/rss/edition_world.rss"),
        ("CNBC World", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
        ("NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
        ("Google News", "https://news.google.com/rss"),
        ("Washington Post World", "http://feeds.washingtonpost.com/rss/world"),
        ("Reddit WorldNews", "https://www.reddit.com/r/worldnews/.rss"),
        ("The Guardian World", "https://www.theguardian.com/world/rss"),
        ("Yahoo News", "https://www.yahoo.com/news/rss"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ],
    "Tech": [
        ("Ars Technica", "http://feeds.arstechnica.com/arstechnica/index"),
        ("CNET News", "https://www.cnet.com/rss/news/"),
        ("Gizmodo", "https://gizmodo.com/rss"),
        ("Hacker News", "https://news.ycombinator.com/rss"),
        ("Lifehacker", "https://lifehacker.com/rss"),
        ("Mashable", "http://feeds.mashable.com/Mashable"),
        ("TechCrunch", "http://feeds.feedburner.com/TechCrunch"),
        ("Google Blog", "https://www.blog.google/rss/"),
        ("The Next Web", "https://thenextweb.com/feed/"),
        ("Wired", "https://www.wired.com/feed/rss"),
        ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
        ("Slashdot", "http://rss.slashdot.org/Slashdot/slashdotMain"),
        ("ReadWrite", "https://readwrite.com/feed/"),
    ],
    "Science": [
        ("BBC Science", "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
        ("Science Daily", "https://www.sciencedaily.com/rss/all.xml"),
        ("NYT Science", "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml"),
        ("Nature", "https://www.nature.com/nature.rss"),
        ("Phys.org", "https://phys.org/rss-feed/"),
        ("Reddit Science", "https://reddit.com/r/science/.rss"),
        ("Wired Science", "https://www.wired.com/feed/category/science/latest/rss"),
        ("Gizmodo Science", "https://gizmodo.com/tag/science/rss"),
        ("Scientific American", "http://rss.sciam.com/ScientificAmerican-Global"),
    ],
    "India": [
        ("BBC India", "http://feeds.bbci.co.uk/news/world/asia/india/rss.xml"),
        ("Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"),
        ("The Hindu", "https://www.thehindu.com/feeder/default.rss"),
        ("NDTV Top Stories", "https://feeds.feedburner.com/ndtvnews-top-stories"),
        ("India Today", "https://www.indiatoday.in/rss/home"),
        ("Indian Express", "http://indianexpress.com/print/front-page/feed/"),
        ("Firstpost India", "https://www.firstpost.com/rss/india.xml"),
        ("The Print", "https://theprint.in/feed/"),
        ("Scroll.in", "http://feeds.feedburner.com/ScrollinArticles.rss"),
        ("Economic Times", "https://economictimes.indiatimes.com/rssfeedsdefault.cms"),
    ],
    "Fashion": [
        ("Elle Fashion", "https://www.elle.com/rss/fashion.xml/"),
        ("The Guardian Fashion", "https://www.theguardian.com/fashion/rss"),
        ("Fashion Lady", "https://www.fashionlady.in/category/fashion/feed"),
        ("Fashionista", "https://fashionista.com/.rss/excerpt/"),
        ("NYT Fashion", "https://rss.nytimes.com/services/xml/rss/nyt/FashionandStyle.xml"),
        ("PopSugar Fashion", "https://www.popsugar.com/fashion/feed"),
        ("Refinery29 Fashion", "https://www.refinery29.com/fashion/rss.xml"),
        ("Who What Wear", "https://www.whowhatwear.com/rss"),
        ("Fashionbeans", "https://www.fashionbeans.com/rss-feed/?category=fashion"),
        ("Vogue", "https://www.vogue.com/feed/rss"),
    ],
    "Hollywood": [
        ("Deadline", "https://deadline.com/feed/"),
        ("Variety", "https://variety.com/feed/"),
        ("IndieWire", "https://www.indiewire.com/feed"),
        ("Film School Rejects", "https://filmschoolrejects.com/feed/"),
        ("Slash Film", "https://feeds2.feedburner.com/slashfilm"),
        ("Coming Soon", "https://www.comingsoon.net/feed"),
        ("First Showing", "https://www.firstshowing.net/feed/"),
        ("Reddit Movies", "https://reddit.com/r/movies/.rss"),
        ("AV Club Film", "https://film.avclub.com/rss"),
        ("Bleeding Cool Movies", "https://www.bleedingcool.com/movies/feed/"),
        ("Hollywood Reporter", "https://www.hollywoodreporter.com/c/news/feed/"),
        ("Entertainment Weekly", "https://ew.com/feed/"),
        ("E! Online", "https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml"),
        ("TVLine", "https://tvline.com/feed/"),
        ("TV Fanatic", "https://www.tvfanatic.com/rss.xml"),
    ],
    "Sports": [
        ("BBC Sport", "http://feeds.bbci.co.uk/sport/rss.xml"),
        ("Reddit Sports", "https://www.reddit.com/r/sports.rss"),
        ("Sky News Sports", "http://feeds.skynews.com/feeds/rss/sports.xml"),
        ("Sportskeeda", "https://www.sportskeeda.com/feed"),
        ("Yahoo Sports", "https://sports.yahoo.com/rss/"),
        ("ESPN", "https://www.espn.com/espn/rss/news"),
    ],
    "Football": [
        ("Reddit Football", "https://www.reddit.com/r/football/.rss?format=xml"),
        ("Goal.com", "https://www.goal.com/feeds/en/news"),
        ("Football365", "https://www.football365.com/feed"),
        ("Soccer News", "https://www.soccernews.com/feed"),
        ("Reddit Championship", "https://www.reddit.com/r/Championship/.rss?format=xml"),
        ("Sky Sports Football", "https://www.skysports.com/rss/12040"),
        ("BBC Sport Football", "http://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("Guardian Football", "https://www.theguardian.com/football/rss"),
    ],
    "Cricket": [
        ("BBC Sport Cricket", "http://feeds.bbci.co.uk/sport/cricket/rss.xml"),
        ("ESPN Cricinfo", "http://www.espncricinfo.com/rss/content/story/feeds/0.xml"),
        ("Reddit Cricket", "https://www.reddit.com/r/Cricket/.rss"),
        ("The Guardian Cricket", "https://www.theguardian.com/sport/cricket/rss"),
        ("NDTV Sports Cricket", "http://feeds.feedburner.com/ndtvsports-cricket"),
        ("Wisden", "https://www.wisden.com/feed"),
        ("The Roar Cricket", "https://www.theroar.com.au/cricket/feed/"),
        ("Cricbuzz", "https://www.cricbuzz.com/cricket-rss-feeds"),
        ("Cricket.com.au", "https://www.cricket.com.au/rss.xml"),
    ],
    "NBA_NFL_UFC": [
        ("ESPN NBA", "https://www.espn.com/espn/rss/nba/news"),
        ("ESPN NFL", "https://www.espn.com/espn/rss/nfl/news"),
        ("ESPN UFC", "https://www.espn.com/espn/rss/mma/news"),
        ("Reddit NBA", "https://www.reddit.com/r/nba/.rss"),
        ("Reddit NFL", "https://www.reddit.com/r/nfl/.rss"),
        ("Reddit UFC", "https://www.reddit.com/r/ufc/.rss"),
        ("NBA.com", "https://www.nba.com/news/rss.xml"),
        ("NFL.com", "https://www.nfl.com/rss/rsslanding?searchString=news"),
        ("Yahoo Sports NBA", "https://sports.yahoo.com/nba/rss.xml"),
        ("Yahoo Sports NFL", "https://sports.yahoo.com/nfl/rss.xml"),
        ("Bleacher Report NBA", "https://bleacherreport.com/nba.rss"),
        ("Bleacher Report NFL", "https://bleacherreport.com/nfl.rss"),
        ("MMA Fighting", "https://www.mmafighting.com/rss/current"),
        ("MMAJunkie", "https://mmajunkie.usatoday.com/feed"),
    ],
    "Celebrity": [
        ("E! Online", "https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml"),
        ("People Magazine", "https://people.com/feed/"),
        ("TMZ", "https://www.tmz.com/rss.xml"),
        ("Us Weekly", "https://www.usmagazine.com/rss/"),
        ("PopSugar Celebrity", "https://www.popsugar.com/celebrity/feed"),
        ("Entertainment Weekly", "https://ew.com/feed/"),
        ("Just Jared", "https://www.justjared.com/feed/"),
        ("Hollywood Life", "https://hollywoodlife.com/feed/"),
        ("Perez Hilton", "https://perezhilton.com/feed/"),
        ("Celebrity Gossip", "https://www.celebitchy.com/feed/"),
        ("Dlisted", "https://dlisted.com/feed/"),
        ("Oh No They Didnt", "https://ohnotheydidnt.livejournal.com/data/rss"),
    ],
}

def test_feed(name, url, timeout=15):
    try:
        feed = feedparser.parse(url)
        n = len(feed.entries)
        return name, url, n, None
    except Exception as e:
        return name, url, 0, str(e)

results = {}

for category, feeds in candidates.items():
    print(f"\n{'='*60}")
    print(f"Testing category: {category}")
    print(f"{'='*60}")

    working = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_feed, name, url): (name, url) for name, url in feeds}
        for future in as_completed(futures):
            name, url, n, err = future.result()
            status = f"OK ({n} entries)" if n > 0 else f"FAIL (0 entries)" if err is None else f"ERROR: {err}"
            print(f"  [{status}] {name}: {url}")
            if n > 0:
                working.append((name, url, n))

    # Sort by entry count descending, take top 5
    working.sort(key=lambda x: x[2], reverse=True)
    results[category] = working[:5]

print("\n\n" + "="*60)
print("FINAL RESULTS (up to 5 working feeds per category)")
print("="*60)

final = {}
for category, feeds in results.items():
    print(f"\n{category}:")
    cat_feeds = []
    for name, url, n in feeds:
        print(f"  ({n} entries) {name}: {url}")
        cat_feeds.append((name, url, n))
    final[category] = cat_feeds

print("\n\nPython dict output:")
print("{")
for category, feeds in final.items():
    print(f'    "{category}": [')
    for name, url, n in feeds:
        print(f'        ("{name}", "{url}"),  # {n} entries')
    print("    ],")
print("}")
