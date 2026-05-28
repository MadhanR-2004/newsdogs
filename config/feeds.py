# config/feeds.py
# Feeds are grouped by category. The category tag is attached to every article
# fetched from that feed, so the triage step can guarantee coverage across categories.

RSS_FEEDS = {

    "International": [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.reuters.com/reuters/topNews",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],

    "Tech / Science / Space": [
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "https://www.theguardian.com/science/space/rss",
        "https://www.space.com/feeds/all",
        "https://www.skyandtelescope.com/feed/",
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://podcasts.files.bbci.co.uk/p002w557.rss",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.blog.google/rss/",
        "https://www.cnet.com/rss/news/",
        "https://www.wired.com/feed/rss",
    ],

    "India": [
        "https://www.thehindu.com/rssfeeds/",
        "https://indianexpress.com/syndication/",
        "https://www.news18.com/rss/",
        "https://economictimes.indiatimes.com/rss.cms",
        "https://www.indiatoday.in/rss",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    ],

    "Music": [
        "https://www.billboard.com/articles/rss.xml",
        "http://consequenceofsound.net/feed",
        "https://edm.com/.rss/full/",
        "https://www.musicbusinessworldwide.com/feed/",
        "http://pitchfork.com/rss/news",
    ],

    "Fashion": [
        "https://www.fashionlady.in/category/fashion/feed",
        "https://www.elle.com/rss/fashion.xml/",
        "https://www.theguardian.com/fashion/rss",
        "https://fashionista.com/.rss/excerpt/",
        "https://www.fashionbeans.com/rss-feed/?category=fashion",
    ],

    "Hollywood / Entertainment": [
        "https://feeds2.feedburner.com/slashfilm",
        "https://www.aintitcool.com/node/feed/",
        "https://www.comingsoon.net/feed",
        "https://deadline.com/feed/",
        "https://filmschoolrejects.com/feed/",
        "https://www.firstshowing.net/feed/",
        "https://www.indiewire.com/feed",
        "https://reddit.com/r/movies/.rss",
        "https://www.bleedingcool.com/movies/feed/",
        "https://film.avclub.com/rss",
        "https://variety.com/feed/",
    ],

    "Sports": [
        "http://www.espncricinfo.com/rss/content/story/feeds/0.xml",
        "https://www.reddit.com/r/Cricket/.rss",
        "https://www.spreaker.com/show/3387348/episodes/feed",
        "https://www.theguardian.com/sport/cricket/rss",
        "http://feeds.feedburner.com/ndtvsports-cricket",
        "http://feeds.bbci.co.uk/sport/cricket/rss.xml",
        "http://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.reddit.com/r/sports.rss",
        "http://feeds.skynews.com/feeds/rss/sports.xml",
        "https://www.sportskeeda.com/feed",
        "https://sports.yahoo.com/rss/",
        "https://www.espn.com/espn/rss/news",
    ],

}
