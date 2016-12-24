import pytest
import transaction
from .models import Entry, get_engine, get_session_factory, get_tm_session
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from .models.meta import Base
from pyramid import testing
import faker


fake = faker.Faker()

ENTRIES = [Entry(
    title=fake.catch_phrase(),
    body=fake.paragraph(),
    creation_date=fake.date_object(),
    edit_date=fake.date_object()
) for i in range(100)]


ROUTES = ['/',
          '/journal/3',
          '/journal/new-entry',
          '/journal/3/edit-entry']


@pytest.fixture(scope="session")
def configuration(request):
    settings = {'sqlalchemy.url': 'sqlite:///:memory:'}
    config = testing.setUp(settings=settings)
    config.include('.models')

    def teardown():
        testing.tearDown()

    request.addfinalizer(teardown)
    return config


@pytest.fixture(scope="function")
def db_session(configuration, request):
    SessionFactory = configuration.registry['dbsession_factory']
    session = SessionFactory()
    engine = session.bind
    Base.metadata.create_all(engine)

    def teardown():
        transaction.abort()

    request.addfinalizer(teardown)
    return session


# @pytest.fixture
# def dummy_request(db_session):
#     req = testing.DummyRequest(dbsession=db_session)
#     add_models(req)
#     return req


def add_models(dummy_request):
    for entry in ENTRIES:
        dummy_request.dbsession.add(entry)
    dummy_request.dbsession.flush()


@pytest.fixture
def testapp():
    """Return mock app."""
    from webtest import TestApp
    from learning_journal import main
    app = main({}, **{"sqlalchemy.url": "postgresql://forf@localhost:5432/lj_testing"})
    testapp = TestApp(app)

    # SessionFactory = app.registry["dbsession_factory"]
    # engine = SessionFactory().bind
    settings = {'sqlalchemy.url': 'postgresql://forf@localhost:5432/lj_testing'}
    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)
    fill_db(testapp)
    return testapp


def fill_db(testapp):
    session_factory = testapp.app.registry["dbsession_factory"]
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        dbsession.add_all(ENTRIES)



# Unit Tests


def test_entries_are_added(db_session):
    """Test all entries are added to database."""
    db_session.add_all(ENTRIES)
    query = db_session.query(Entry).all()
    assert len(query) == len(ENTRIES)


def test_home_view_returns_100_when_db_populated(db_session):
    """Test home_view returns all entries."""
    from .views.default import home_view
    dbsession = db_session
    for entry in ENTRIES:
        dbsession.add(entry)
        print(entry)
        dbsession.flush()
    req = testing.DummyRequest()
    req.dbsession = dbsession
    res = home_view(req)
    entries = res['left_entries'] + res['right_entries'] + [res['latest']]
    assert len(entries) == len(ENTRIES)


def test_detail_page(dummy_request):
    from .views.default import detail_view
    dummy_request.matchdict['id'] = 1
    res = detail_view(dummy_request)
    assert res['entry'].title == ENTRIES[0].title



# Functional Tests


def test_home_has_list(testapp):
    response = testapp.get('/', status=200)
    assert str(response.html).count('div class="one-half column"') == 2


def test_home_route_with_data_has_all_articles(testapp):
    """Test all articles are rendered."""
    response = testapp.get('/', status=200)
    assert len(response.html.find_all('article')) == 100


def test_view_css_links(testapp):
    """Test css links."""
    response = testapp.get('/', status=200)
    assert str(response.html).count('text/css') == 3


def test_not_found_detail(testapp):
    with pytest.raises(Exception):
        testapp.get('/journal/1000')

