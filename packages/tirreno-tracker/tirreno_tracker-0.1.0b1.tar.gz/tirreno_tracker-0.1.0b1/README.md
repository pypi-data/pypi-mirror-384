# tirreno-python-tracker

Send data from your python application to tirreno console.

```python
from tirreno_tracker import Tracker

tirreno_url = "https://example.tld";
tracking_id = "XXX";

tracker = Tracker(tirreno_url, tracking_id)

event = tracker.create_event()

event.set_user_name(current_user.username) \    # johndoe42
    .set_ip_address(current_user.ip_address) \  # 1.1.1.1
    .set_user_agent(current_user.user_agent) \  # Mozilla/5.0
    .set_url(current_user.url) \                # /login
    .set_event_type_login()

tracker.track(event)
```

## Requirements

* Python 3.6+.

## Installation

### pip

Make sure that `pip` is installed.
Unix-based systems:
```
python -m ensurepip --upgrade
```
Windows:
```
py -m ensurepip --upgrade
```
Install the `tirreno_tracker` module.
```
python -m pip install tirreno_tracker
```

## License

Released under the [BSD License](https://opensource.org/license/bsd-3-clause). tirreno is a
registered trademark of tirreno technologies sàrl, Switzerland.
