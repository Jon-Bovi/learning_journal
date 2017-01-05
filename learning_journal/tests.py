# -*- coding: utf-8 -*-
import pytest
import transaction
from .models import Entry, get_tm_session
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from zope.interface.interfaces import ComponentLookupError
from passlib.apps import custom_app_context as pwd_context
from pyramid.security import Allow, Everyone, Authenticated
from .models.meta import Base
from pyramid import testing
import faker
import datetime
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


class DummyAuthenticationPolicy(object):
    def __init__(self, userid):
        self.userid = userid

    def authenticated_userid(self, request):
        return self.userid

    def unauthenticated_userid(self, request):
        return self.userid

    def effective_principals(self, request):
        principals = [Everyone]
        if self.userid:
            principals += [Authenticated]
        return principals

    def remember(self, request, userid, **kw):
        return []

    def forget(self, request):
        return []


@pytest.fixture(scope="session")
def configuration(request):
    """Return config for a db_session."""
    settings = {'sqlalchemy.url': 'postgres:///lj_testing'}
    config = testing.setUp(settings=settings)
    config.include('learning_journal.models')
    config.include('learning_journal.routes')

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


@pytest.fixture
def set_auth_credentials():
    """Set password and username env variables."""
    os.environ["AUTH_PASSWORD"] = pwd_context.hash('pass')
    os.environ["AUTH_USERNAME"] = 'Bill'


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


def test_check_credentials_valid(set_auth_credentials):
    """Test check credentials returns true for valid username and pswrd."""
    from .security import check_credentials
    assert check_credentials('Bill', 'pass')


def test_login_view_get(dummy_request):
    """Test login view returns empty dict for get request."""
    from .views.default import login_view
    assert login_view(dummy_request) == {}


def test_login_view_success_redirect(dummy_request, set_auth_credentials):
    from .views.default import login_view
    dummy_request.method = 'POST'
    dummy_request.POST['username'] = 'Bill'
    dummy_request.POST['password'] = 'pass'

    assert isinstance(login_view(dummy_request), HTTPFound)

# Functional Tests #


@pytest.fixture(scope="session")
def testapp(request):
    """Return mock app."""
    from webtest import TestApp
    from pyramid.config import Configurator

    def main(global_config, **settings):
        """The function returns a Pyramid WSGI application."""
        config = Configurator(settings=settings)
        config.include('pyramid_jinja2')
        config.include('learning_journal.models')
        config.include('learning_journal.routes')
        config.include('learning_journal.security')
        config.scan()
        return config.make_wsgi_app()

    app = main({}, **{'sqlalchemy.url': 'postgres:///lj_testing'})
    testapp = TestApp(app)

    SessionFactory = app.registry["dbsession_factory"]
    engine = SessionFactory().bind
    Base.metadata.create_all(bind=engine)

    def tear_down():
        Base.metadata.drop_all(bind=engine)

    request.addfinalizer(tear_down)
    return testapp


@pytest.fixture
def fill_db(testapp):
    """."""
    session_factory = testapp.app.registry["dbsession_factory"]
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        dbsession.add_all(ENTRIES)

    return dbsession


def test_home_has_list(testapp):
    """."""
    response = testapp.get('/', status=200)
    assert str(response.html).count('div class="one-half column"') == 2


def test_get_login_shows_input_fields(testapp):
    """."""
    response = testapp.get("/login")
    html = response.html
    username = html.find("input", {"name": "username"})
    password = html.find("input", {"name": "password"})
    assert username and password


def test_user_log_in_and_auth(set_auth_credentials, testapp):
    """Test login authenicates user."""
    testapp.post("/login", params={
        'username': 'Bill',
        'password': 'pass'
    })
    assert "auth_tkt" in testapp.cookies


def test_authed_user_can_create_new_entry(testapp):
    """Foo."""
    response = testapp.get("/journal/new-entry")
    csrf_token = response.html.find(
        "input",
        {"name": "csrf_token"}).attrs["value"]

    testapp.post("/journal/new-entry", params={
        "csrf_token": csrf_token,
        "title": "THIS IS NOT A TEST",
        "creation_date": "2000-10-10",
        "body": "can't touch this"
    })

    response = testapp.get("/")
    assert "THIS IS NOT A TEST" in response.text


def test_authed_user_can_edit_entry(testapp):
    """Test logged in user can edit entry."""
    response = testapp.get("/journal/1/edit-entry")
    csrf_token = response.html.find(
        "input",
        {"name": "csrf_token"}).attrs["value"]

    testapp.post("/journal/new-entry", params={
        "csrf_token": csrf_token,
        "title": "THIS IS A TEST",
        "creation_date": "2010-10-10",
        "body": "don't touch this"
    })

    response = testapp.get("/")
    assert "THIS IS A TEST" in response.text


@pytest.mark.parametrize('route', ['/journal/1032', '/journal/1032/edit-entry'])
def test_detail_and_update_page_404_redirect(route, testapp):
    """Test detail page redirects to 404 page if entry doesn't exist."""
    res = testapp.get(route, status=404).html.find_all('p')
    assert res[0].text == '404'
    assert res[1].text == u'¶∆‰Œ πø† ∫◊µπ¿'


def test_home_route_with_data_has_all_articles(testapp, fill_db):
    """Test all articles are rendered."""
    response = testapp.get('/', status=200)
    assert len(response.html.find_all('article')) == 100


def test_detail_page(testapp, fill_db):
    """Test detail page renders correctly."""
    res = testapp.get('/journal/100', status=200).html
    assert res.find('h4').text == 'Boomshakalaka'
    assert res.find('p').text == 'last airbender'


def test_logout_removes_authentication(testapp):
    """Foo."""
    testapp.get("/logout")
    assert "auth_tkt" not in testapp.cookies


def test_login_button_now_present_on_homepage(testapp):
    """FOO."""
    response = testapp.get("/")
    assert "login" in response.text


def test_edit_view_is_forbidden_again(testapp, fill_db):
    """Foo."""
    response = testapp.get("/journal/5/edit-entry", status=403)
    assert response.status_code == 403
