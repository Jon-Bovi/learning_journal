"""View handlers."""
from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from datetime import date, datetime
# from sqlalchemy.exc import DBAPIError
from pyramid.security import remember, forget
from ..security import check_credentials
from ..models import Entry


@view_config(route_name='home', renderer='../templates/home.jinja2')
def home_view(request):
    """Grab homepage data from db and send it to jinja."""
    if request.method == "POST":
        title = request.POST['title']
        body = request.POST['body']
        creation_date = datetime.strptime(request.POST['creation_date'], "%Y-%m-%d")
        entry = Entry(title=title, body=body, creation_date=creation_date)
        request.dbsession.add(entry)
        return HTTPFound(location=request.route_url('home'))
    entries = request.dbsession.query(Entry).order_by(Entry.id).all()[::-1]
    latest = entries[0] if entries else ""
    left_entries, right_entries = [], []
    for i in range(1, len(entries)):
        if i % 2:
            left_entries.append(entries[i])
        else:
            right_entries.append(entries[i])
    return {'latest': latest,
            'left_entries': left_entries,
            'right_entries': right_entries,
            "creation_date": date.today()}


@view_config(route_name='detail', renderer='../templates/detail.jinja2')
def detail_view(request):
    """Grab detail data from db and hand it off to jinja."""
    e = request.dbsession.query(Entry).get(int(request.matchdict['id']))
    if not e:
        raise HTTPNotFound(detail="This entry does not exist...yet")
    edit_date = None
    if e.edit_date:
        edit_date = e.edit_date.strftime("%b %d, %Y")
    return {'entry': e, 'edit_date': edit_date}


@view_config(route_name='update',
             permission='admin',
             renderer='../templates/update.jinja2')
def update_view(request):
    """Handle get and post requests for editing entries."""
    e = request.dbsession.query(Entry).get(int(request.matchdict['id']))
    if not e:
        raise HTTPNotFound(detail="You cannot edit that which does not exist")
    if request.method == "POST":
        e.title = request.POST['title']
        e.body = request.POST['body']
        e.edit_date = date.today()
        request.dbsession.flush()
        return HTTPFound(location=request.route_url('detail', id=e.id),)
    if request.method == "GET":
        return {'title': e.title, 'body': e.body}


@view_config(route_name='create',
             permission='admin',
             renderer='../templates/create.jinja2')
def create_view(request):
    """Return new entry form and/or add new entry to db with form data."""
    if request.method == "POST":
        title = request.POST['title']
        body = request.POST['body']
        creation_date = datetime.strptime(request.POST['creation_date'], "%Y-%m-%d")
        entry = Entry(title=title, body=body, creation_date=creation_date)
        request.dbsession.add(entry)
        return HTTPFound(location=request.route_url('home'))
    if request.method == "GET":
        today = date.today()
        return {"creation_date": today}


@view_config(route_name="login",
             renderer='../templates/login.jinja2',
             require_csrf=False)
def login_view(request):
    """Return login form and/or attempt login with form data."""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        if check_credentials(username, password):
            auth_head = remember(request, username)
            return HTTPFound(
                request.route_url('home'),
                headers=auth_head
            )

    return {}


@view_config(route_name='logout')
def logout_view(request):
    """Forget authentication of user and redirect to home."""
    auth_head = forget(request)
    return HTTPFound(request.route_url('home'), headers=auth_head)


@forbidden_view_config(renderer='../templates/forbidden.jinja2')
def forbidden_view(request):
    """Return 403 forbidden page."""
    return {}
