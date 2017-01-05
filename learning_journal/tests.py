# -*- coding: utf-8 -*-
import pytest
import transaction
from .models import Entry, get_tm_session
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from zope.interface.interfaces import ComponentLookupError
from .models.meta import Base
from pyramid import testing
import faker
import datetime
import contextlib
import os


fake = faker.Faker()

ENTRIES = [Entry(
    title=fake.catch_phrase(),
    body=fake.paragraph(),
    creation_date=fake.date_object(),
    edit_date=fake.date_object()
) for i in range(99)] + [Entry(
    title="Boomshakalaka",
    body='last airbender',
    creation_date=fake.date_object()
)]


ROUTES = ['/',
          '/journal/new-entry',
          '/journal/3',
          '/journal/3/edit-entry']


@pytest.fixture(scope="session")
def configuration(request):
    """Return config for a db_session."""
    settings = {'sqlalchemy.url': 'postgres://forf@localhost:5432/lj_testing'}
    config = testing.setUp(settings=settings)
    config.include('learning_journal.models')

    def teardown():
        testing.tearDown()

    request.addfinalizer(teardown)
    return config


@pytest.fixture
def db_session(configuration, request):
    """Return a db_session."""
    session_factory = configuration.registry['dbsession_factory']
    session = session_factory()
    engine = session.bind
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    def teardown():
        session.transaction.rollback()

    request.addfinalizer(teardown)
    return session


@pytest.fixture
def dummy_request(db_session):
    """."""
    return testing.DummyRequest(dbsession=db_session)


@pytest.fixture
def add_models(dummy_request):
    """."""
    dummy_request.dbsession.add_all(ENTRIES)


# Unit Tests #


def test_entries_are_added(db_session):
    """Test all entries are added to database."""
    db_session.add_all(ENTRIES)
    query = db_session.query(Entry).all()
    assert len(query) == len(ENTRIES)


def test_home_view_filled(dummy_request, add_models):
    """Test home_view returns all entries."""
    from .views.default import home_view
    res = home_view(dummy_request)
    entries = res['left_entries'] + res['right_entries'] + [res['latest']]
    assert len(entries) == len(ENTRIES)


def test_detail_view(dummy_request, add_models):
    """Test detail page for first entry."""
    from .views.default import detail_view
    dummy_request.matchdict['id'] = 1
    res = detail_view(dummy_request)
    assert res['entry'].title == ENTRIES[0].title


def test_detail_view_not_found(dummy_request):
    """Test 404 not found for detail."""
    from .views.default import detail_view
    dummy_request.matchdict['id'] = 1
    with pytest.raises(Exception):
        detail_view(dummy_request)


def test_update_view(dummy_request, add_models):
    """."""
    from .views.default import update_view
    dummy_request.matchdict['id'] = 1
    res = update_view(dummy_request)
    assert res['title'] == ENTRIES[0].title
    assert res['body'] == ENTRIES[0].body


def test_update_view_not_found(dummy_request):
    """Test update view for a non-existant entry."""
    from .views.default import update_view
    dummy_request.matchdict['id'] = 1
    with pytest.raises(Exception):
        update_view(dummy_request)


def test_update_view_post(dummy_request, add_models):
    """Test ability to update db."""
    from .views.default import update_view
    dummy_request.matchdict['id'] = 2
    dummy_request.method = 'POST'
    dummy_request.POST['title'] = 'Blah'
    dummy_request.POST['body'] = 'nononoyes'
    try:
        update_view(dummy_request)
    except ComponentLookupError:
        pass
    entry = dummy_request.dbsession.query(Entry).get(2)
    assert entry.title == 'Blah'
    assert entry.body == 'nononoyes'


def test_create_view_get(dummy_request):
    """Test create view initial get."""
    from .views.default import create_view
    res = create_view(dummy_request)
    assert type(res['creation_date']) is datetime.date


def test_create_view_post(dummy_request):
    """Test create view form submission adds to db."""
    from .views.default import create_view
    dummy_request.method = 'POST'
    dummy_request.POST['title'] = 'Boomshakalaka'
    dummy_request.POST['body'] = 'nononoyes'
    dummy_request.POST['creation_date'] = '2012-11-22'
    try:
        create_view(dummy_request)
    except ComponentLookupError:
        pass
    entry = dummy_request.dbsession.query(Entry).first()
    assert entry.title == 'Boomshakalaka'
    assert entry.body == 'nononoyes'
    assert 'datetime' in str(type(entry.creation_date))


def test_check_credentials_invalid():
    """Test check credentials returns false for invalid username and pswrd."""
    from .security import check_credentials
    assert check_credentials('bobby', '') is False
    assert check_credentials('bobby', 'password') is False
    assert check_credentials('ffowler', 'password') is False


@contextlib.contextmanager
def set_env(**environ):
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


def test_check_credentials_valid():
    """Test check credentials returns true for valid username and pswrd."""
    from .security import check_credentials
    from passlib.apps import custom_app_context as pwd_context
    pswrd = pwd_context.hash('pass')
    with set_env(AUTH_PASSWORD=pswrd):
        assert check_credentials('ffowler', 'pass')


def test_login_view_get(dummy_request):
    """Test login view returns empty dict for get request."""
    from .views.default import login_view
    assert login_view(dummy_request) == {}


# Functional Tests #


@pytest.fixture
def testapp():
    """Return mock app."""
    from webtest import TestApp
    from pyramid.config import Configurator

    def main(global_config, **settings):
        """The function returns a Pyramid WSGI application."""
        config = Configurator(settings=settings)
        config.include('pyramid_jinja2')
        config.include('learning_journal.models')
        config.include('learning_journal.routes')
        config.scan()
        return config.make_wsgi_app()

    app = main({}, **{"sqlalchemy.url": "postgres://forf@localhost:5432/lj_testing"})
    testapp = TestApp(app)

    session_factory = app.registry["dbsession_factory"]
    engine = session_factory().bind
    Base.metadata.create_all(bind=engine)

    return testapp


@pytest.fixture
def fill_db(testapp):
    session_factory = testapp.app.registry["dbsession_factory"]
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        dbsession.add_all(ENTRIES)


@pytest.mark.parametrize("route", ROUTES)
def test_view_css_links(route, testapp, fill_db):
    """Test css links."""
    response = testapp.get(route, status=200)
    assert str(response.html).count('text/css') == 3


def test_home_has_list(testapp):
    response = testapp.get('/', status=200)
    assert str(response.html).count('div class="one-half column"') == 2


def test_home_route_with_data_has_all_articles(testapp, fill_db):
    """Test all articles are rendered."""
    response = testapp.get('/', status=200)
    assert len(response.html.find_all('article')) == 100


def test_detail_page(testapp, fill_db):
    """Test detail page renders correctly."""
    res = testapp.get('/journal/100', status=200).html
    assert res.find('h4').text == 'Boomshakalaka'
    assert res.find('p').text == 'last airbender'


@pytest.mark.parametrize('route', ['/journal/1032', '/journal/1032/edit-entry'])
def test_detail_and_update_page_404_redirect(route, testapp):
    """Test detail page redirects to 404 page if entry doesn't exist."""
    res = testapp.get(route, status=404).html.find_all('p')
    assert res[0].text == '404'
    assert res[1].text == u'¶∆‰Œ πø† ∫◊µπ¿'


def test_update_page_redirect(testapp, fill_db):
    """Test update page redirects to detail view."""
    post_params = {
        'title': 'geronimo',
        'body': 'downward dog'
    }
    res = testapp.post('/journal/1/edit-entry', post_params).follow()
    assert res.html.find('h4').text == 'geronimo'
    assert res.html.find('p').text == 'downward dog'


# def test_create_page_redirect(testapp, fill_db):
#     """Test create page redirects to home."""
#     post_params = {
#         'title': 'baby bond',
#         'body': 'gold powder',
#         'creation_date': '2000-10-21'
#     }
#     res = testapp.post('/journal/new-entry', post_params)
#     assert res.html.find('article').find('h4').text == 'baby bond'


def test_login_view_post(testapp):
    """Test login view re"""
    from .views.default import login_view
    from passlib.apps import custom_app_context as pwd_context
    pswrd = pwd_context.hash('pass')
    with set_env(AUTH_PASSWORD=pswrd):
        post_params = {
            'password': 'pass',
            'username': 'ffowler'
        }
        res = testapp.post('/login', post_params)
        assert res.headers['Location'] == 'http://localhost/'


def test_logout_view(testapp):
    """."""
    from .views.default import logout_view
    res = testapp.get('/logout')
    assert res.headers['Location'] == 'http://localhost/'
