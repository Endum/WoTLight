from asyncio import current_task
import json
import sys
import tornado.gen
from tornado.ioloop import IOLoop
from wotpy.protocols.http.server import HTTPServer
from wotpy.wot.servient import Servient
import asyncio
from threading import Thread

CATALOGUE_PORT = 9200
HTTP_PORT = 9202

TD = {
    'title': 'Sensor-Light',
    'id': 'it:unibo:filippo:benvenuti3:wot-detect',
    'description': '''A sensor which can detect level of light.''',
    '@context': [
        'https://www.w3.org/2019/wot/td/v1',
    ],
    'properties': {
        'light': {
            'type': 'string',
            'observable': True
        }
    },
    #'actions': { },
    'events': {
        'lightChanged': {
            'description': '''Light level changed.''',
            'data': {
                'type': 'string'
            },
        },
    },
}

def read_input():
    asyncio.set_event_loop(asyncio.new_event_loop())
    global exposed_thing
    while True:
        print("Enter '[0.[0-9] - 1.0]' to change light level: ", end='')
        exposed_thing.properties['light'].write(input())

@tornado.gen.coroutine
def main():

    # Http service.
    http_server = HTTPServer(port=HTTP_PORT)
    
    # Servient.
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(http_server) # Adding http functionalities.

    # Start servient.
    wot = yield servient.start()

    global exposed_thing
    # Creating thing from TD.
    exposed_thing = wot.produce(json.dumps(TD))

    # Initialize thing property.
    exposed_thing.properties['light'].write('0.0')

    # Observe presence value changing.
    exposed_thing.properties['light'].subscribe(
        on_next=lambda data: exposed_thing.emit_event('lightChanged', f'{data}'), # What to do when value change.
        on_completed= print('Subscribed for an observable property: light'), # What to do when subscribed.
        on_error=lambda error: print(f'Error trying to observe light: {error}') # What to do in case of error.
    )

    # Expose detection sensor thing.
    exposed_thing.expose()
    print(f'{TD["title"]} is ready')

    Thread(target=read_input).start()

if __name__ == '__main__':
    #asyncio.set_event_loop(asyncio.ProactorEventLoop())
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    IOLoop.current().add_callback(main)
    IOLoop.current().start()