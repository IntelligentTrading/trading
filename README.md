# Portfolio Allocation API

### API service for auto-trading on portfolio allocations (aka. Project Bodysnatch)

The goal is to create an independent service for trading via portfolio allocations.
Using Technical Analysis, there are many buy and sell opportunities happening simultaneously and at different time horizons. In trading that is not super high-frequency, these indicators can be used to promote and demote allocations across a large portfolio of coins. This application is responsible for efficiently placing orders and trading against a portfolio in order to achieve an update target allocation state. Additionally, there is a secondary goal of minimizing trading fees and slippage during such trades.

This system is proposed to run on a Python/Django/Postgres stack, hosted on Heroku

### Todo (Tom and Arsèn):

- [ ] how are API auth keys created and used
- [ ] more secure way of passing exchange api keys?
- [ ] set requirements for accuracy, dynamic to support small/large portfolios and coins with low volume
- [ ] estimate expected load on the service
- [ ] finalize architecture requirements


**Currently In Scope**

- Check coin balances and for any Binance exchange account given a set of api keys.
- Represent a Binance exchange account as a portfolio of coins with portion allocations.
- Calculate difference between current state and desired state of a portfolio allocation.
- Determine shortest/cheapest path for trading from current state to desired state
- Make trades by taking market orders
- Limit slippage using a price difference threshold (1%?)
- 5 minute expiration on processing orders
- extra/leftover assets held in BTC


**Currently out of Scope, but maybe add later**

- placing orders at high frequency in order to capture prices better than taking market orders
- Operating on Bittrex, Poloniex, and other exchanges
- Accounting for amounts held offline when converting allocation % to trades
- simulation mode, check order book, simulate trades, and return API responses normally

**Will NEVER be in Scope**

- deposit or withdraw coins from any account
- expose public api endpoints
- publish data on intended trades *before* placing orders
- hold exchange api keys in *persistant* storage or database
- compare or analyze portfolios against each other


## Binance Exchange Get Portfolio State

`/api/portfolio` with data in request body

```
GET /api/portfolio
{
	"binance": {
		"api_key": "***",
		"secret_key": "***",
	}
}
```

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
        "coin": "BCH",
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

```
RESPONSE 404 NOT FOUND
{ "error": "exchange API keys invalid" }
```

```
RESPONSE 418 I'M A TEAPOT
{ "error": "only binance exchange support available at this time" }
```


## Binance Exchange Set Portfolio New State

```
PUT /api/portfolio
{
	"binance": {
		"api_key": "***",
		"secret_key": "***",
		"allocations": [
			{"coin":"ETH", "portion": 0.43},
			{"coin":"USDT", "portion": 0.21},
			{"coin":"BCH", "portion": 0.36}
		]
	}
}
```

```
RESPONSE 202 Accepted
{ 
	"status": "target allocations queued for processing",
	"portfolio_processing_request": "/api/portfolio_process/1234ABCD",
	"retry_after": 15000  # milliseconds
}
```

`portfolio_processing_request` is a uri to and endpoint for checking the status of the processing

`retry_after` informs the client that it can check back after some period of time if they want to check on the status of the processing. This is simply an estimate of when the system expects to be nearly done processing trades.

```
RESPONSE 400 Bad Request
{"error": "portions add to more than 1.0"}
```

```
RESPONSE 404 NOT FOUND
{ "error": "exchange API keys invalid" }
```

## Binance Exchange Check Portfolio Processing


`GET /api/portfolio_process/<processing_id>`

```
RESPONSE 200 Accepted
{ 
	"status": "processing complete",
	"portfolio_processing_request": "/api/portfolio_process/1234ABCD",
	"retry_after": 15000  # milliseconds
}
```

```
RESPONSE 202 Accepted
{ 
	"status": "processing in progress",
	"portfolio_processing_request": "/api/portfolio_process/1234ABCD",
	"retry_after": 15000  # milliseconds
}
```

```
RESPONSE 410 Gone OR 404 Not Found
{ 
	"status": "not found or expired"
}
```
processing task not found because it was expired from the cache, client should start over with a new set of requests


