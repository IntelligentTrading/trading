Rebalancing algorithms use min-cost-flow algorithm to minimize lost money while rebalancing. Market order rebalancing algorithm finds best way to rebalance minimizing lost money because of spread and fees and creates corresponding market orders.

Limit order rebalancing finds way to rebalance as market order rebalancing, but at first it minimizes number of orders to be created. Than the algorithm runs by the following steps:
1. find orders, that can be placed now, and create them
2. sleep for `time_delta` seconds
3. cancel all current orders
4. check canceled orders
  - if order is filled, it's removed from orders list
  - if order is filled partialy, it's quantity is decreased
  - if order is not placed because of invalid order quantity, it's removed from list
  - if order is not placed because of BinanceAPI exceptions or it's placed but not filled, it remains unchanged in list
5. if there remains orders, check number of trials
  - if number of trials for any product exceed `max_retries` go to step 6
  - if no order is left go to step 6
  - otherwise go to step 1
6. finish rebalancing and return all orders made.
