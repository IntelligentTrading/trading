# Portfolio Allocation API

### API service for auto-trading on portfolio allocations (aka. Project Bodysnatch)

The goal is to create an independent service for trading via portfolio allocations.
Using Technical Analysis, there are many buy and sell opportunities happening simultaneously and at different time horizons. In trading that is not super high-frequency, these indicators can be used to promote and demote allocations across a large portfolio of coins. This application is responsible for efficiently placing orders and trading against a portfolio in order to achieve an update target allocation state. Additionally, there is a secondary goal of minimizing trading fees and slippage during such trades.

This system is proposed to run on a Python/Django/Postgres stack, hosted on Heroku

**Currently In Scope**

- Check coin balances and for any Binance exchange account given a set of api keys.
- Represent a Binance exchange account as a portfolio of coins with portion allocations.
- Calculate difference between current state and desired state of a portfolio allocation.
- Determine shortest/cheapest path for trading from current state to desired state
- Make trades by taking market orders
- 5 minute expiration on processing orders. We will fail if we can't execute limit orders in 5 minutes if the volume of transactions is too high.
- extra/leftover assets held in BTC, i.e. if requested portfolio ratios do not sum to one, we assume the rest is BTC.
- secure way of passing exchange api keys.
- use of API auth keys
- Track amount of slippage made using market orders

**Currently out of Scope, but maybe add later**

- placing orders at high frequency in order to capture prices better than taking market orders
- Operating on Bittrex, Poloniex, and other exchanges
- Accounting for amounts held offline when converting allocation % to trades
- simulation mode, check order book, simulate trades, and return API responses normally
- ignore very small leftover/untradable amounts of coins `portoin < 0.0001 or value < 0.00001 BTC` 

**Will NEVER be in Scope**

- deposit or withdraw coins from any account
- expose public api endpoints
- publish data on intended trades *before* placing orders
- hold exchange api keys in *persistant* storage or database
- compare or analyze portfolios against each other



## Binance Exchange Get Portfolio State

`/api/portfolio` with data in request body

```
POST /api/portfolio
{
        "api_key": "...",
	"binance": {
		"api_key": "***",
		"secret_key": "***",
	}
}
```

`
curl -H "Content-Type: application/json" \
-d '{"binance": {"secret_key": "secret", "api_key": "api-aaa"}, "api_key": "aaaaa"}' \
-X POST localhost:8000/api/portfolio/
`

In request data, includes json data for Exchange account access (binance only for v.1)

```
RESPONSE 200 OK
{
	"binance": {
		"value": 2.53439324,  # BTC value
		"allocations": [
			{
				"coin": "ETH",
				"amount": 231.12321311  # amount of tokens
				"portion": 0.4999  # floor at 4th decimal place
			},
			{
				"coin": "BCC",
				"amount": 22.12932881  # amount of tokens
				"portion": 0.4999  # floor at 4th decimal place 
			},
			...
		]
	}
}
```

ITF price API is available for checking estimated current prices of coins

Value is the estimated total value of all assets on binance, denominated in BTC

Sum of all portions should be between 0.9900 and 1.0000

```
allocations_sum = sum([float([a["portion"]) for a in data["binance"]["allocations"]])
assert allocations_sum <= 1 and allocations_sum > 0.99
```

`
curl -H "Content-Type: application/json" \
-d '{"binance": {"secret_key": "secret", "api_key": "wrong key"}, "api_key": "aaaaa"}' \
-X POST localhost:8000/api/portfolio/
`

```
RESPONSE 404 NOT FOUND
{ "error": "exchange API keys invalid" }
```

`
curl -H "Content-Type: application/json" \
-d '{"bitfinex": {"secret_key": "secret", "api_key": "api-aaa"}, "api_key": "aaaaa"}' \
-X POST localhost:8000/api/portfolio/
`

```
RESPONSE 418 I'M A TEAPOT
{ "error": "only binance exchange support available at this time" }
```


## Binance Exchange Set Portfolio New State
This defines a new target allocatoin for a portfolio. The difference between this target allocatoin and the current state could range from a very small to a very large differenc. Given a set of target alloctions, a portfolio might aim to "cash out" 150 coins and move 100% of assets to USDT, or vis versa.

`
curl -H "Content-Type: application/json" 
-d '{"binance": {"secret_key": "secret", "api_key": "api-aaa", "allocations": [{"coin": "ETH", "portion": 0.43}, {"coin":"USDT", "portion": 0.2100}, {"coin":"BCC", "portion": 0.3599}]}, "api_key": "aaaaa"}' 
-X PUT localhost:8000/api/portfolio/
`

```
PUT /api/portfolio
{
        "api_key": "...",
	"binance": {
		"api_key": "***",
		"secret_key": "***",
		"allocations": [
			{"coin":"ETH", "portion": 0.43},
			{"coin":"USDT", "portion": 0.2100},
			{"coin":"BCC", "portion": 0.3599}
		]
	}
}
```
This example targets 43% ETH, 36% BCC and 21% USDT. The sum of portions should be close to 100% (between 99% and 100%). Any and all leftover/extra assets always assume to being held in BTC. In this example it's expected that some small amount ~0.01% will be leftover in BTC

```
RESPONSE 202 Accepted
{ 
	"status": "target allocations queued for processing",
	"portfolio_processing_request": "/api/portfolio_process/1234ABCD",
	"retry_after": 25000  # milliseconds
}
```

`portfolio_processing_request` is a uri to and endpoint for checking the status of the processing

`retry_after` informs the client that it can check back after some period of time if they want to check on the status of the processing. This is simply an estimate of when the system expects to be nearly done processing trades.

`
curl -H "Content-Type: application/json" 
-d '{"binance": {"secret_key": "secret", "api_key": "api-aaa", "allocations": [{"coin": "ETH", "portion": 0.43}, {"coin":"USDT", "portion": 0.2100}, {"coin":"BCC", "portion": 0.5}]}, "api_key": "aaaaa"}' 
-X PUT localhost:8000/api/portfolio/
`

```
RESPONSE 400 Bad Request
{"error": "portions add to more than 1.0"}
```

`
curl -H "Content-Type: application/json" 
-d '{"binance": {"secret_key": "secret", "api_key": "wrong key", "allocations": [{"coin": "ETH", "portion": 0.43}, {"coin":"USDT", "portion": 0.2100}, {"coin":"BCC", "portion": 0.5}]}, "api_key": "aaaaa"}' 
-X PUT localhost:8000/api/portfolio/
`

```
RESPONSE 404 NOT FOUND
{ "error": "exchange API keys invalid" }
```

`
curl -H "Content-Type: application/json" 
-d '{"coinbase-pro": {"secret_key": "secret", "api_key": "api-aaa", "allocations": [{"coin": "ETH", "portion": 0.43}, {"coin":"USDT", "portion": 0.2100}, {"coin":"BCC", "portion": 0.5}]}, "api_key": "aaaaa"}' 
-X PUT localhost:8000/api/portfolio/
`

```
RESPONSE 418 I'M A TEAPOT
{ "error": "only binance exchange support available at this time" }
```

## Binance Exchange Check Portfolio Processing

```
POST /api/portfolio_process/<processing_id>
{
    "api_key": "..."
}
```

`
curl -H "Content-Type: application/json" 
-d '{"api_key": "key"}' 
-X POST localhost:5000/api/portfolio_process/a5bf73ecbbaf
`

```
RESPONSE 202 Accepted
{ 
	"status": "processing in progress",
	"portfolio_processing_request": "/api/portfolio_process/1234ABCD",
	"retry_after": 12000  # milliseconds
}
```

```
RESPONSE 200 Accepted
{ 
	"status": "processing complete in 16092ms",
	"binance": {
		"value": 2.53439324,  # BTC value
		"allocations": [
			{
				"coin": "ETH",
				"amount": 231.12321311  # amount of tokens
				"portion": 0.4999  # floor at 4th decimal place
			},
			{
				"coin": "BCC",
				"amount": 22.12932881  # amount of tokens
				"portion": 0.4999  # floor at 4th decimal place 
			},
			...
		]
	}
}
```



```
RESPONSE 410 Gone OR 404 Not Found
{ 
	"status": "not found or expired"
}
```
processing task not found because it was expired from the cache, client should start over with a new set of requests


### Authentication with the server

Each request should have `api_key` attribute, that will server to authenticate with out server.
```
{
  "api_key": "...",
  ...
}
```
if the api key is not valid, the user will get 
 
```
RESPONSE 401 Unauthorized
{ 
	"status": "Not authorized"
}
```

If trying to view another user's rebalance it will get 410 or 404

```
RESPONSE 410 Gone OR 404 Not Found
{ 
	"status": "not found or expired"
}
```

## Getting Statistics about market order execution.

`GET /market_order_statistics/`

```
{ 
	"market orders": {
		"mean absoluate difference percent": 0.3
	}
}
```

#### API key creation

Key creation will be manual, and will be done using the django admin interface by superusers.

### Storing executed orders in the postgres database

In order to allow for monitoring how much slippage was in place,
we are going to store the following information in the postgres database for market orders.

- Mid Market price when deciding to place orders (the number fed into the algorithm)
- effective execution price of the order (weighted sum if order was split into parts by the exchange)
- amount bought or sold.

## Architecture Proposal for async execution

This proposal works very well with the requirements, but is not very
simple and since it is async, could potentially result in a lot of
expirations if there are not enough workers running.

This will be a very scalable architecture, but will require at least 4 different services.
- django webserver
- postgres database [used for user authentication]
- redis for message brokerage
- celery worker(s) for task execution.

### Creating rebalance request

User will interact with the django webserver, that will use the database
to make sure user has appropriate access rights.

After the webserver receives a rebalance request (PUT /api/portfolio),
it creates a rebalance tasks and stores the tasks in an redis database
(message broker). [This is ephemeral database that will lose all data
if restarted.] Each task will have a unique id which will be relayed to
the user as a rebalance id, and the user could query the webserver in
the future to get the progress report.

There are going to be multiple workers (this should be scaled so very
low latency in the system) that will retrieve tasks from the message
broker (redis) and execute desired trades, and update the task with results.

### Checking rebalance progress

Whenever the webserver receives request to see the progress
(GET /api/portfolio_process/TASK-ID) it will query the webserver, to see the
status of the task, which will be stored in the redis message broker
together with the result of the task.

### Checking Portfolio State

This process will query binance api directly (after checking access
rights) for allocations, and augment results returned by Binance will
allocation ratios.


### Securing api key passing.

In order to make exchange api key passing secure
- we are going to use SSL on the broker server, to make sure we can pass
exchange api keys over internet without jeopardizing them.
- we are going to use ssl on the webserver as well.


## Algorithm proposal for placing orders

We propose execution using market orders or limit orders. Depending
on volume. **Note** there is a problem with limit orders that there
are slow by nature and they might be direct orders between currency
pairs and BTC, and we might not pick the most liquid currency pair,
and we don't have a performance guarantee, because prices change within
5 minute period as well.

Executed on celery workers, see above proposal for details.
This algorithm requires VOLUME_THRESHOLD variable which we propose should
be given by the user.

1. Get user resources
1. Get market prices for all commodities
1. estimate the volume of trades using wall prices and market order algorithm
1. if volume < VOLUME_THRESHOLD
   - execute market orders
1. if volume > VOLUME_THRESHOLD
   - use mid market prices and create efficient limit orders
   - place limit orders with 1 minute expiration
   - sleep for 1 minute
   - if retries_left > 0: retry with 1 less retry
   - stop execution without rebalancing
