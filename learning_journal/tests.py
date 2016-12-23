import pytest
import transaction
from .models import Entry, get_tm_session
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
def config(request):
    settings = {'sqlalchemy.url': 'sqlite:///:memory:'}
    conf = testing.setUp(settings=settings)
    conf.include('.models')

    def teardown():
        testing.tearDown()

    request.addfinalizer(teardown)
    return conf


@pytest.fixture
def db_session(config, request):
    SessionFactory = config.registry['dbsession_factory']
    session = SessionFactory()
    engine = session.bind
    Base.metadata.create_all(engine)

    def teardown():
        session.transaction.rollback()

    request.addfinalizer(teardown)
    return session


@pytest.fixture
def dummy_request(db_session):
    return testing.DummyRequest(dbsession=db_session)


@pytest.fixture
def add_models(dummy_request):
    dummy_request.dbsession.add_all(ENTRIES)


@pytest.fixture
def testapp():
    """Return mock app."""
    from webtest import TestApp
    from learning_journal import main
    app = main({}, **{"sqlalchemy.url": "sqlite:///:memory:"})
    testapp = TestApp(app)

    SessionFactory = app.registry["dbsession_factory"]
    engine = SessionFactory().bind
    Base.metadata.create_all(bind=engine)

    return testapp


@pytest.fixture
def fill_db(testapp):
    SessionFactory = testapp.app.registry["dbsession_factory"]
    with transaction.manager:
        dbsession = get_tm_session(SessionFactory, transaction.manager)
        dbsession.add_all(ENTRIES)


def test_entries_are_added(db_session):
    """Test all entries are added to database."""
    db_session.add_all(ENTRIES)
    query = db_session.query(Entry).all()
    assert len(query) == len(ENTRIES)


def test_home_view_returns_100_when_db_populated(dummy_request, add_models):
    """Test home_view returns all entries."""
    from .views.default import home_view
    res = home_view(dummy_request)
    entries = res['left_entries'] + res['right_entries'] + [res['latest']]
    assert len(entries) == len(ENTRIES)


def test_home_has_list(testapp, fill_db):
    response = testapp.get('/', status=200)
    assert str(response.html).count('div class="one-half column"') == 2


def test_home_route_with_data_has_all_articles(testapp, fill_db):
    response = testapp.get('/', status=200)
    assert len(response.html.find_all('article')) == 100


@pytest.mark.parametrize("route", ROUTES)
def test_view_css_links(route, testapp):
    response = testapp.get(route, status=200)
    assert str(response.html).count('text/css') == 3



