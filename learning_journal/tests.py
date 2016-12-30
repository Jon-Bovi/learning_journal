import pytest
from pyramid import testing


@pytest.fixture
def req():
    """Return dummy request."""
    reque = testing.DummyRequest()
    return reque


@pytest.fixture
def testapp():
    """Return mock app."""
    from webtest import TestApp
    from learning_journal_basic import main
    app = main({})
    return TestApp(app)


@pytest.fixture(params=['/',
                        '/journal/3',
                        '/journal/new-entry',
                        '/journal/3/edit-entry'])
def test_response(request):
    """Return test responses."""
    from webtest import TestApp
    from learning_journal_basic import main
    app = main({})
    testapp = TestApp(app)
    response = testapp.get(request.param, status=200)
    return response


def test_home_view_renders_home_data(req):
    """My home page view returns dictionary."""
    from .views.default import home_view
    response = home_view(req)
    assert 'latest' in response
    assert 'left_entries' in response
    assert 'right_entries' in response


def test_home_has_iterables(req):
    """Test home view response returns iterable(dictionary)."""
    from .views.default import home_view
    response = home_view(req)
    assert hasattr(response['left_entries'], '__iter__')
    assert hasattr(response['right_entries'], '__iter__')


def test_home_has_list(testapp):
    response = testapp.get('/', status=200)
    inner_html = response.html
    assert str(inner_html).count('div class="one-half column"') == 2


def test_home_css_links(test_response):
    inner_html = test_response.html
    print(inner_html)
    assert str(inner_html).count('text/css') == 3

# class BaseTest(unittest.TestCase):
#     def setUp(self):
#         self.config = testing.setUp(settings={
#             'sqlalchemy.url': 'sqlite:///:memory:'
#         })
#         self.config.include('.models')
#         settings = self.config.get_settings()

#         from .models import (
#             get_engine,
#             get_session_factory,
#             get_tm_session,
#             )

#         self.engine = get_engine(settings)
#         session_factory = get_session_factory(self.engine)

#         self.session = get_tm_session(session_factory, transaction.manager)

#     def init_database(self):
#         from .models.meta import Base
#         Base.metadata.create_all(self.engine)

#     def tearDown(self):
#         from .models.meta import Base

#         testing.tearDown()
#         transaction.abort()
#         Base.metadata.drop_all(self.engine)


# class TestMyViewSuccessCondition(BaseTest):

#     def setUp(self):
#         super(TestMyViewSuccessCondition, self).setUp()
#         self.init_database()

#         from .models import Entry

#         model = Entry(id=1, title='one', body='wat', date="2016-12-21")
#         self.session.add(model)

#     def test_passing_view(self):
#         from .views.default import my_view
#         info = my_view(dummy_request(self.session))
#         self.assertEqual(info['one'].name, 'one')
#         self.assertEqual(info['project'], 'learning_journal')


# class TestMyViewFailureCondition(BaseTest):

#     def test_failing_view(self):
#         from .views.default import my_view
#         info = my_view(dummy_request(self.session))
#         self.assertEqual(info.status_int, 500)
