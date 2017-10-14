# GTCollab REST API

Georgia Tech CS 4261 Fall 2017

### Local Server

```
python manage.py runserver
```

### Production Server

hostname: [https://secure-headland-60131.herokuapp.com](#)

admin site: [https://secure-headland-60131.herokuapp.com/admin/](#)

Base URL: [https://secure-headland-60131.herokuapp.com/api/](#)

Docs: [https://secure-headland-60131.herokuapp.com/api/docs/](#)

### Authorization

All API endpoints (except for user creation) and the API docs require an HTTP `Authorization` header with a value of `Token <auth-token>`.
The `/api/api-token-auth` endpoint returns an `<auth-token>` upon receiving a POST request with valid `username` and `password` fields in the request body.