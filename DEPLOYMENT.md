To setup and test service locally clone repository and make by command
`make`

After make is complete activate virtual environment `source .venv/.../activate`

<br>

If user is not authenticated on heroku use `heroku login`.\
To create heroku app use `heroku create` command. 
If everything goes right, you will see `Creating app... done, ⬢ young-above-487`
where `young-above-487` is the application name.

<br>

In heroku the databases are used as additions. To see if there are databases
attached simply run `heroku addons`.

By default heroku creates postgres instance and the URI is 
stored in heroku environment as DATABASE_URL. 
If it is not present then we need to add it manually.
`heroku addons:create heroku-postgresql:[plan] -a [application_name]`
For development purposes it is better to pick `hobby-dev` plan which is free.
For example `heroku addons:create heroku-postgresql:hobby-dev -a black-unicorn-123`

For celery workers we need to add redis manually. Again by using addons command
`heroku addons:create heroku-redis:[plan] -a [application_name]`

<br>

After these steps we have created heroku app, added postgres and redis. 

<br>

To deploy service locally we need to export postgres and redis URIs to our env.
For getting URIs just run `heroku run env | grep DATABASE` and 
`heroku run env | grep REDIS` and export returned values `export [returned_value]`.
Then just run by command `heroku local`. Congratulations you have running 
instance on your computer.

<br>
<br>

To deploy service remotely just run `git push heroku master`. 
And now it is ready! You can open app in browser by `heroku open`.

In order to scale the web or worker instances just `heroku ps:scale web=1` or 
`heroku ps:scale worker=1` correspondingly. 
To turn off the instance put the value 0 `heroku ps:scale worker=0`.
