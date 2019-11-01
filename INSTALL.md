# openc2-yuuki

Yuuki is compatible with Python 3. It is a reference implementation of an OpenC2 actuator, and comes with a simple client that will send commands to the actuator.
As a demonstration, this actuator implements an imaginary OpenC2 Profile called "ACME Anti-RoadRunner", which might be sold to a famous Coyote.

## Installation

Install virtualenv via pip:

    $ pip3 install virtualenv

Create and activate a python virtual environment:
    
    $ mkdir test_yuuki
    $ cd test_yuuki
    $ virtualenv venv
    $ source venv/bin/activate

Download and install yuuki
    
    $ git clone https://github.com/oasis-open/openc2-yuuki.git
    $ pip3 install ./openc2-yuuki



## Start Actuator

Start the actuator in the background with default settings, and silence its stdout, etc:

    $ python3 -m yuuki.actuator > /dev/null 2>&1 &

## Query the Actuator's Features

Now that we have the actuator running, let's see what it can do. To start, let's query its features. We can type this command out manually, but for now, let's just send a prewritten command that our client program comes with.

    $ python3 -m yuuki.client send 0

OUTPUT:

    >>> COMMAND
            {'action': 'query',
             'target': {'features': []}}

    <<< RESPONSE
            {'results': {'pairs': [['detonate', 'x-acme:road_runner'],
                                   ['locate',   'x-acme:road_runner'],
                                   ['restart',  'device'],
                                   ['set',      'properties'],
                                   ['start',    'device'],
                                   ['stop',     'device']],
                         'profiles': ['x-acme'],
                         'rate_limit': 30,
                         'versions': ['1.0']},
             'status': 200,
             'status_text': 'OK - the Command has succeeded.'}

OK, we can see we sent an action-target pair of 'query features'. The response shows us everything we need to know about this actuator, and perhaps most importantly, which OpenC2 profile(s) it implements. Looks like it implements one profile with a NameSpace Identifer (NSID) of 'x-acme', and has six action-target 'pairs'. This means the actuator supports six specific commands; one for each pair.

## Send a Command: Locate RoadRunner!

From the list of action-target pairs above, we can see the actuator supports a command for locating the road runner. Let's do it. Again, we'll use a pre-written command from our client. To see what pre-written commands the client came with, just type

    $ python3 -m yuuki.client show

Now let's actually locate the bird!

    $ python3 -m yuuki.client send 5

OUTPUT:

    >>> COMMAND
            {'action': 'locate',
            'target': {'x-acme:road_runner': ''}
            'args': {'response_requested': 'complete'},}

    <<< RESPONSE
            {'status': 200,
            'status_text': "Road Runner has been located!"}

## Send a Command: Destroy RoadRunner!

Ok, we've found our target; let's act!

    $ python3 -m yuuki.client send 6

    >>> COMMAND
            {'action': 'destroy',
            'target': {'x-acme:road_runner': ''}
            'args': {'response_requested': 'complete'},}

    <<< RESPONSE
            {'status': 500,
            'status_text': "INTERNAL ERROR! Now targetting Coyote!!"}

## Try Again

Our previous command failed! Maybe we should hit the reset button on the actuator. We know that command exists becuase we saw it in the 'query features' response. This time we'll type in the command.
    
    $ python3 -m yuuki.client type-it
    $ {
    $ "action" : "reset",
    $ "target" : { "device" : ""}
    $ }
    $ <enter>

    >>> COMMAND
            {'action': 'restart',
             'target': {'device': []}}

    <<< RESPONSE
            {'status': 200,
             'status_text': 'OK - the Command has succeeded.'}


## That's all, folks!

Stop the actuator:

    $ fg
    $ CTRL-C


## What just happened?

The actuator started a server that waits for messages on 127.0.0.0:9001.
The client sent a pre-written OpenC2 command from command_examples.json to the server.
The server dispatched to any profile implementations it had loaded, if appropriate, then returned the response.



## Next Steps
Look at 'profile_acme_anti_roadrunnery.py' in yuuki/actuator_src/profiles as a starting point to see what's happening.