import asyncio
import logging

from edp.redy.app import App
from edp.redy.cli.argparser import parser

logging.basicConfig(
    level='INFO',
    format='%(asctime)s %(levelname)s '
    '%(name)s::%(funcName)s(line %(lineno)s): %(message)s'
)


log = logging.getLogger(__name__)


async def consumed(value):
    log.info(f'Consumed: {value} W')


async def produced(value):
    log.info(f'Produced: {value} W')


async def injected(value):
    log.info(f'Injected: {value} W')


async def self_consumed(value):
    log.info(f'Self Consumed: {value} W')


async def get_history_task(app: App):
    while True:
        try:
            consumed_today = await app.energy.consumed.today
            log.info(f'Energy Consumed today: {consumed_today}')
        except Exception as ex:
            log.error(ex)

        await asyncio.sleep(60 * 5)


async def main():

    # Get the inputs
    args = parser.parse_args()

    # Start the app
    app = App(
        username=args.username,
        password=args.password,
        user_pool_id=args.user_pool_id,
        client_id=args.client_id,
        region=args.region,
        identity_id=args.identity_id,
        identity_login=args.identity_login
    )

    await app.start()

    # Task that periodically gets energy history
    asyncio.get_event_loop().create_task(get_history_task(app))

    # Configure the callbacks to stream the real time power consumption
    app.power.consumed.stream(consumed)
    app.power.produced.stream(produced)
    app.power.injected.stream(injected)
    app.power.self_consumed.stream(self_consumed)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(main())
    loop.run_forever()
