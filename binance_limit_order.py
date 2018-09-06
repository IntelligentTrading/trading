import argparse
import json
from decimal import Decimal

from exchange.binance import Binance


def parse_args(*argument_array):
    parser = argparse.ArgumentParser()
    base_parser = argparse.ArgumentParser(
        description="creates binance limit order, and returns response",
        add_help=False)

    base_parser.add_argument('--credentials-path', type=str)
    product_arg = base_parser.add_mutually_exclusive_group()
    product_arg.add_argument('--symbol', type=str)
    product_arg.add_argument('--product', type=str)

    create_parser = argparse.ArgumentParser(add_help=False)
    create_parser.set_defaults(q='create')
    create_parser.add_argument('--action', choices=['BUY', 'SELL'])
    create_parser.add_argument('--quantity', type=str, default=1)

    cancel_parser = argparse.ArgumentParser(add_help=False)
    cancel_parser.set_defaults(q='cancel')
    cancel_parser.add_argument('--order-id', type=str)

    get_open_orders_parser = argparse.ArgumentParser(add_help=False)
    get_open_orders_parser.set_defaults(q='get_open_orders')

    subparsers = parser.add_subparsers(help="help")
    subparsers.add_parser(
        'create', parents=[create_parser, base_parser], help='create help')
    subparsers.add_parser('cancel', parents=[cancel_parser, base_parser])
    subparsers.add_parser(
        'get-open-orders', parents=[get_open_orders_parser, base_parser])
    args = parser.parse_args(*argument_array)
    if hasattr(args, 'quantity'):
        args.quantity = Decimal(args.quantity)
    args.symbol = args.symbol or ''.join(args.product.split('_'))
    return args


def main(args):
    with open(args.credentials_path, 'r') as rfile:
        credentials = json.load(rfile)
    binance = Binance(api_key=credentials['BINANCE_API_KEY'],
                      secret_key=credentials['BINANCE_API_SECRET'])
    if args.q == 'get_open_orders':
        print(*binance.client.get_open_orders(symbol=args.symbol), sep='\n')
        return
    if args.q == 'cancel':
        print(binance.client.cancel_order(
            symbol=args.symbol, orderId=args.order_id))
        return
    assert args.q == 'create'
    exchange_info = binance.client.get_exchange_info()
    for _symbol in exchange_info['symbols']:
        if _symbol['symbol'] == args.symbol:
            filt = _symbol['filters'][0]
            if args.action == 'SELL':
                price = filt['maxPrice']
            else:
                price = filt['minPrice']
    order_response = binance.client.create_order(
        symbol=args.symbol, side=args.action,
        quantity=Decimal(args.quantity), price=price,
        type='LIMIT_MAKER')
    print(f'create order response {order_response}')
    orderId = order_response['orderId']
    order_response = binance.client.get_order(
        symbol=args.symbol, orderId=orderId)
    print(f'get order response {order_response}')


if __name__ == '__main__':
    args = parse_args()
    main(args)
