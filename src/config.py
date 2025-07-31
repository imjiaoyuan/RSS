import os

RSS_FEEDS = {
    'Blog Posts': [
        "https://blog.ursb.me/feed.xml",
        "https://innei.in/feed",
        "https://thiscute.world/index.xml",
        "https://polebug.github.io/atom.xml",
        "https://imzm.im/feed/",
        "https://hellogithub.com/rss",
        "https://www.longluo.me/atom.xml",
        "https://1q43.blog/feed/",
        "https://justgoidea.com/rss.xml",
        "https://yukieyun.net/index.xml",
        "https://www.pseudoyu.com/feed.xml",
        "https://blog.drpika.com/atom.xml",
        "https://ada3104.pages.dev/index.xml",
        "https://manateelazycat.github.io/feed.xml",
        "https://www.ntiy.com/feed",
        "https://feeds.feedburner.com/ruanyifeng",
        "https://darmau.co/zh/article/rss.xml",
        "https://cyp0633.icu/index.xml",
        "https://divingintogeneticsandgenomics.com/index.xml",
        "https://lutaonan.com/rss.xml",
        "https://xxu.do/feed",
        "https://kowyo.com/index.xml",
        "https://ysx.cosine.ren/atom.xml",
        "https://idealclover.top/feed",
        "https://www.eaimty.com/rss.xml",
        "https://blog.illsky.com/rss.xml",
        "https://www.xheldon.com/feed.xml",
        "https://diygod.cc/feed",
        "https://xlog.dreamo.ink/feed",
        "https://hutusi.com/feed.xml",
        "https://thirdshire.com/index.xml",
        "https://www.darknavy.org/zh/index.xml",
        "https://www.wordpace.com/feed/",
        "https://www.gaojinan.com/feed",
        "https://tw93.fun/feed.xml",
        "https://anotherdayu.com/feed/",
        "https://hualet.org/index.xml",
        "https://www.microsoft.com/en-us/research/feed/",
        "https://blog.ferstar.org/atom.xml",
        "https://www.archlinuxcn.org/feed/",
    ],
}

RECEIVER_EMAILS_LIST = [
    "imjiaoyuan@gmail.com",
]

EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 465)),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('SENDER_PASSWORD'),

    'receiver_emails': RECEIVER_EMAILS_LIST
}