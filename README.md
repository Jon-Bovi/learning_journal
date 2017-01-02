# learning_journal

http://ford-learning-journal.herokuapp.com/

Daily learning journal app with capability to view past entries, edit past
entries, and create new entries.

Build using the Pyramid framework with a postgres database and jinja2 templates.

## Testing

#### Python 2.7

```
platform darwin -- Python 2.7.10, pytest-3.0.5, py-1.4.32, pluggy-0.4.0
collected 20 items

learning_journal/tests.py ....................

---------- coverage: platform darwin, python 2.7.10-final-0 ----------
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
learning_journal/__init__.py                  10      7    30%   8-14
learning_journal/models/__init__.py           22      0   100%
learning_journal/models/entrymodel.py         10      0   100%
learning_journal/models/meta.py                5      0   100%
learning_journal/routes.py                     6      0   100%
learning_journal/scripts/__init__.py           0      0   100%
learning_journal/scripts/initializedb.py      27     12    56%   63-66, 70-79
learning_journal/views/__init__.py             0      0   100%
learning_journal/views/default.py             45      0   100%
learning_journal/views/notfound.py             4      0   100%
------------------------------------------------------------------------
TOTAL                                        129     19    85%
```

#### Python 3.5

```
platform darwin -- Python 3.5.2, pytest-3.0.5, py-1.4.32, pluggy-0.4.0
collected 20 items

learning_journal/tests.py ....................

---------- coverage: platform darwin, python 3.5.2-final-0 -----------
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
learning_journal/__init__.py                  10      7    30%   8-14
learning_journal/models/__init__.py           22      0   100%
learning_journal/models/entrymodel.py         10      0   100%
learning_journal/models/meta.py                5      0   100%
learning_journal/routes.py                     6      0   100%
learning_journal/scripts/__init__.py           0      0   100%
learning_journal/scripts/initializedb.py      27     12    56%   63-66, 70-79
learning_journal/views/__init__.py             0      0   100%
learning_journal/views/default.py             45      0   100%
learning_journal/views/notfound.py             4      0   100%
------------------------------------------------------------------------
TOTAL                                        129     19    85%
```
