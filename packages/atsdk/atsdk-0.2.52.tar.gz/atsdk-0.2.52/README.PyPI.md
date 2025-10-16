<h1><img width=250px src="https://atsign.com/wp-content/uploads/2022/05/atsign-logo-horizontal-color2022.svg" alt="The Atsign Foundation"></h1>

[![GitHub License](https://img.shields.io/badge/license-BSD3-blue.svg)](./LICENSE)
[![PyPI version](https://badge.fury.io/py/atsdk.svg)](https://badge.fury.io/py/atsdk)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/atsign-foundation/at_python/badge)](https://securityscorecards.dev/viewer/?uri=github.com/atsign-foundation/at_python&sort_by=check-score&sort_direction=desc)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/8104/badge)](https://www.bestpractices.dev/projects/8104)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)

# The atPlatform for Python developers - (Beta Version)

This repo contains library, samples and examples for developers who wish
to work with the atPlatform from Python code.

## Python 3.8 deprecation

This SDK was created to support Python 3.8 (specifically 3.8.1 due to some
dependency requirements). As of 7 Oct 2024 Python 3.8 is end-of-life, and
will no longer receive security patches. Occordingly we have
[decided](https://github.com/atsign-foundation/at_protocol/blob/trunk/decisions/2024-10-python-deprecation.md)
to continue support for 3.8 for another 6 months (on a best efforts basis).
As 7 Apr 2025 has now passed, Python 3.8 has been removeded from the test
matrix, and pyproject.toml bumped to require Python 3.9(.2).

Older versions of this package will of course remain available on
[PyPI](https://pypi.org/project/atsdk/), though they may lack features,
fixes and security updates; so it is recommended that you try to update
to a more recent Python.

## Python 3.9.0 and 3.9.1 not supported

To deal with a security vulnerability in the underlying OpenSSL library the
cryptography package was bumped to 44.0.1, and this forced the removal of
Python 3.9.0 and 3.9.1. Later versions of Python 3.9 are supported.

## Getting Started

### 1. Installation

This package can be installed from PyPI with:

```sh
pip install atsdk
```

Alternatively clone this repo and from the repo root:

```shell
pip install -r requirements.txt
pip install .
```

### 2. Setting up your `.atKeys`

To run the examples save .atKeys file in the '~/.atsign/keys/' directory.

### 3. Sending and Receiving Data

There are 3 ways in which data can be sent and received from at server.

1. Using PublicKey

    ```python
    from at_client import AtClient
    from at_client.common import AtSign
    from at_client.common.keys import PublicKey

    atsign = AtSign("@bob")
    atclient = AtClient(atsign)
    pk = PublicKey("key", atsign)

    # Sending data
    response = atclient.put(pk, "value")
    print(response)

    # Receiving Data
    response = atclient.get(pk)
    print(response)

    # Deleting data
    response = atclient.delete(pk)
    print(response)
    ```

2. Using SelfKey

    ```python
    from at_client import AtClient
    from at_client.common import AtSign
    from at_client.common.keys import SelfKey

    atsign = AtSign("@bob")
    atclient = AtClient(atsign)
    sk = SelfKey("key", atsign)

    # Sending data
    response = atclient.put(sk, "value")
    print(response)

    # Receiving Data
    response = atclient.get(sk)
    print(response)

    # Deleting data
    response = atclient.delete(sk)
    print(response)
    ```

3. Using SharedKey

    ```python
    from at_client import AtClient
    from at_client.common import AtSign
    from at_client.common.keys import SharedKey

    bob = AtSign("@bob")
    alice = AtSign("@alice")
    bob_atclient = AtClient(bob)
    sk = SharedKey("key", bob, alice)

    # Sending data
    response = bob_atclient.put(sk, "value")
    print(response)

    # Receiving Data
    alice_atclient = AtClient(alice)
    response = alice_atclient.get(sk)
    print(response)

    # Deleting data
    response = bob_atclient.delete(sk)
    print(response)
    ```

### CLI Tools

* **REPL** - you can use this to type atPlatform commands and see responses;
but the best thing about the REPL currently is that it shows the data
notifications as they are received. The REPL code has the essentials of what
a 'receiving' client needs to do - i.e.
  * create an AtClient (assigning a Queue object to its queue parameter)
  * start two new threads
    * one for the AtClient.start_monitor() task: receives data update/delete
    notification events (the event data contains the ciphertext)
    * the other one calls handle_event() method, which will read the
    upcoming events in the queue and handle them:
    * calling AtClient.handle_event() (to decrypt the notifications and
    introducing the result as a new event in the queue)
    * reading the new event, which contains the decrypted result
  * Instructions to run the REPL:
    1) Run repl.py and choose an atSign using option `1`
    2) Select option `2`. REPL will start and activate monitor mode
    automatically in a different thread. You can still send commands/verbs.
    You will start seeing your own notifications (from yourself to yourself)
    and heartbeat working (noop verb is sent from time to time as a keepalive)
    3) Use `at_talk` or any other tool to send notifications to your atSign
    from a different atSign. You should be able to see the complete
    notification, and the encrypted and decrypted value of it.

* **REGISTER** - use this cli to register new free atsign. Uses onboarding
cli to create atkey files.
  * Use following command to run the REGISTER cli using email:

    ```shell
    python register.py -e <email>
    ```

  * Use following command to run the REGISTER cli using api-key:

    ```shell
    python register.py -k <api-key>
    ```

* **ONBOARDING** - use this cli to onboard a new atSign. Once onboarding
is complete it creates the all-important keys file. Onboard is a subset of
Register.
  * Use following command to run the ONBOARDING cli:

    ```shell
    python onboarding.py -a <atsign> -c <cram-secret>
    ```

* **SHARE** - use this cli to share data between 2 atsigns.
  * Use following command to run the SHARE cli:

    ```shell
    python share.py -a <atsign> -o <other-atsign> -k <key-name> -s <value>
    ```

* **GET** - use this cli to get shared data between 2 atsigns.
  * Use following command to run the GET cli:

    ```shell
    python get.py -a <atsign> -o <other-atsign> -k <key-name>
    ```

* **DELETE** - use this cli to delete any key shared between 2 atsigns.
  * Use following command to run the DELETE cli:

    ```shell
    python delete.py -a <atsign> -o <other-atsign> -k <key-name>
    ```

## Open source usage and contributions

This is open source code, so feel free to use it as is, suggest changes or
enhancements or create your own version. See
[CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidance on how to setup
tools, tests and make a pull request.

## Maintainers

This project was created by [Umang Shah](https://github.com/shahumang19)
and is maintained by [Chris Swan](https://github.com/cpswan) and
[Xavier Lin](https://github.com/xlin123)
