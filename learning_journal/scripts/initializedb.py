import os
import sys
import transaction
from datetime import datetime

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from pyramid.scripts.common import parse_vars

from ..models.meta import Base
from ..models import (
    get_engine,
    get_session_factory,
    get_tm_session,
)
from ..models import Entry

import faker


fake = faker.Faker()

ENTRIES = [{
    "title": fake.catch_phrase(),
    "body": fake.paragraph(),
    "creation_date": fake.date_object(),
    "edit_date": fake.date_object()
} for i in range(30)]


ENTRIES += [
    {
        "title": "TESTING",
        "body": "T0day we m0ved past vanillaish servers and jumped int0 pyth0n web framew0rks, specifically Pyramid. We discussed the t00ls Pyramid gives y0u t0 implement MVC architecture, with view c0ntr0llers and r0utes. Setting up the pyramid framew0rk is quite straightf0rward with the scaff0lds they pr0vide, I imagine it'd be h0rrend0us if th0se weren't available. F0r n0w, all 0f 0ur c0ntent is static, but we'll be building 0ur data 0ff 0f templates s00n. After setting up the pyramid app, we pushed it t0 her0ku. As 0ur daily data structure, we were intr0duced t0 d0uble ended queses, deques, which all0w p0pping and appending 0n b0th ends. They werer simple t0 implement using the d0uble-linked list under the h00d.",
        "creation_date": datetime.strptime("Dec 18, 2016", "%b %d, %Y")
    },
    {
        "title": "Pyramid Views and Routes",
        "body": "Today we moved past vanillaish servers and jumped into python web frameworks, specifically Pyramid. We discussed the tools Pyramid gives you to implement MVC architecture, with view controllers and routes. Setting up the pyramid framework is quite straightforward with the scaffolds they provide, I imagine it'd be horrendous if those weren't available. For now, all of our content is static, but we'll be building our data off of templates soon. After setting up the pyramid app, we pushed it to heroku. As our daily data structure, we were introduced to double ended queses, deques, which allow popping and appending on both ends. They werer simple to implement using the double-linked list under the hood.",
        "creation_date": datetime.strptime("Dec 19, 2016", "%b %d, %Y")
    },
    {
        "title": "Binary Heaps and Templating with Jinja2",
        "body": "Another big day! We are starting to move past hardcoded HTML (woo) into jinja2 templates. No longer are our view handlers reading straight from fully built individual html pages, now we build those pages as templates and fill in the relevant, requested data. This learning journal for instance. We build the unique data into dictionaries which jinja2 looks through and inserts into templates, and voila a fully built view. And, I haven't gotten to it yet, but we'll have to fully test our views now, with help from pyramid's dummyrequest and webtests TestApp. On top of that we briefly learned about binary heaps and then were asked to implement one. The easy method is to use a python list composition thing, and indeed we used that method. However, I wouldn't call it easy, though it was enjoyable to figure out. ALSO, we chose our projects. Whaddaday.",
        "creation_date": datetime.strptime("Dec 20, 2016", "%b %d, %Y")
    },
    {
        "title": "CAN YOU HEAR ME NOW?",
        "body": "Well I'm not totally sure this is actually working but it's looking like it might be. We weren't supposed to update the database, but I did? But really this right here is what today was all about: incorporating sqlalchemy into our pyramid apps. But less incorporating, more completely redoing. It's been somewhat confusing. The main thing I learned is that pshell is my best friend. I wasn't able to get much testing done, to be honest I haven't been following the tdd approach to this project, I don't think anyone has. The priority queue was interesting, we read some docs which said that a heap under the hood was the way to go, but other groups used dictionaries of queues which is more intuitive and might be faster...Sera ended up implemented her own version that way.",
        "creation_date": datetime.strptime("Dec 21, 2016", "%b %d, %Y")
    },
    {
        "title": "Starting to get testing going, still having problems.",
        "body": "Today was actually pretty easy in terms of workload, as we were given the entire afternoon to catch up on our learning journals, which I didn't really have to do. Testing this has been a bit of a nightmare, as even with Nick's fancy fixtures and fakers and testing modules, I'm running into so many errors. My TestApp fixture just isn't happy. I get an error saying, 'IntegrityError: ids must be UNIQUE' and as far as I can tell they are unique. Basically I was on a wild goose chase all evening and didn't make progress. HELP.",
        "creation_date": datetime.strptime("Dec 22, 2016", "%b %d, %Y")
    },
]


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    engine = get_engine(settings)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        for entry in ENTRIES:
            model = Entry(title=entry['title'],
                          body=entry['body'],
                          creation_date=entry['creation_date'])
            dbsession.add(model)
