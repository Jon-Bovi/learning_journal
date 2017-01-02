from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from datetime import date, datetime
from sqlalchemy.exc import DBAPIError

from ..models import Entry


@view_config(route_name='home', renderer='../templates/home.jinja2')
def home_view(request):
    """Grab homepage data from db and send it to jinja."""
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
            'right_entries': right_entries}


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


@view_config(route_name='update', renderer='../templates/update.jinja2')
def update_view(request):
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


@view_config(route_name='create', renderer='../templates/create.jinja2')
def create_view(request):
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
