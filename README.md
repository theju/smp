
# Scheduled Social Media Poster

A simple web app to schedule your Social Media Posts either through a web
interface or an API. Currently supports Facebook and Twitter.

## Install

* Clone the git repo
  ```
  git clone https://github.com/theju/smp
  cd smp
  ```
* Install the dependencies listed in the requirements.txt
  ```
  pip install -r requirements.txt
  ```
* Create the db schema. Uses sqlite3 by default. Create a local.py file under the
  `smp/smp` directory to change it.
  ```
  python manage.py migrate
  ```
* Run the dev server.
  ```
  python manage.py runserver
  ```
* Create an admin user
  ```
  python manage.py createsuperuser
  ```
* Login to the admin page at http://localhost:8000/admin/ and enter the social application
  credentials at http://localhost:8000/admin/socialaccount/socialapp/
  ([FB app instructions](https://developers.facebook.com/apps/) and [Twitter app instructions](https://apps.twitter.com/)).
* Setup a crontab script that runs the following command every minute
  ```
  python manage.py autopost
  ```

## Advanced

### Schedule posts through API

* Fetch the API Key from the web interface for the user and perform a HTTP
  Basic Authenticated POST request with the username as your API Key and
  blank password at http://localhost:8000/api/post/add/ to schedule posts.

  **CURL Example**
  ```
  curl -X POST -u <api_key> -d "status=Hello+World&service=facebook&scheduled_datetime=2016-01-01T00:01:00Z" http://localhost:8000/api/post/add/
  ```

  **Requests Example**
  ```
  import requests
  import datetime
  
  requests.post("http://localhost:8000/api/post/add/", data={
      "status": "Hello World",
      "service": "facebook",
      "scheduled_datetime": datetime.datetime(2016, 01, 01, 00, 01, 00).strftime("%Y-%m-%dT%H:%M:%SZ"),
      "scheduled_tz": "UTC"
  }, auth=("<api_key>", ""))
  ```
