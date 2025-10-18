# NTP Facade SMR

[![PyPI version](https://badge.fury.io/py/ntp-facade-smr.svg)](https://badge.fury.io/py/ntp-facade-smr)

NTP facade package for use in our smart manufactoring robot project

## Installation

You can install the package from PyPI:

```bash
pip install ntp-facade-smr
```

## Testing

Using the test.py file in the tests/ dir will allow you to connect to a ntp server running on your network. It defaults to 127.0.0.1 (localhost) so you will want to change that to point to the running ntp server.

## Usage

The LOCAL_NTP_SERVER var is the IP address, and the LOCAL_NTP_PORT is the port, the port should always be 123 so it defaults to that when creating an instance of the TimeBrokerFacade.