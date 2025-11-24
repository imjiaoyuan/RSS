import os

RSS_FEEDS = {
    'Blog Posts': [
        "https://blog.ursb.me/feed.xml",
        "https://thiscute.world/index.xml",
        "https://polebug.github.io/atom.xml",
        "https://hellogithub.com/rss",
        "https://www.longluo.me/atom.xml",
        "https://1q43.blog/feed/",
        "https://manateelazycat.github.io/feed.xml",
        "https://www.ntiy.com/feed",
        "https://feeds.feedburner.com/ruanyifeng",
        "https://cyp0633.icu/index.xml",
        "https://lutaonan.com/rss.xml",
        "https://idealclover.top/feed",
        "https://www.eaimty.com/rss.xml",
        "https://www.xheldon.com/feed.xml",
        "https://diygod.cc/feed",
        "https://www.darknavy.org/zh/index.xml",
        "https://tw93.fun/feed.xml",
        "https://blog.ferstar.org/atom.xml",
        "https://blog.lilydjwg.me/feed",
        "https://forums.debiancn.org/c/5-category/5.rss",
        "https://www.lainme.com/feed",
        "https://szclsya.me/zh-cn/index.xml",
        "https://bigeagle.me/index.xml",
        "https://yufree.cn/cn/index.xml",
        "https://www.tianxianzi.me/index.xml",
        "https://thirdshire.com/index.xml",
        "https://wangyurui.com/feed.xml"
    ],
    'News':[
        "https://www.solidot.org/index.rss",
        "https://www.landiannews.com/feed",
        "https://www.ithome.com/rss"
    ]
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