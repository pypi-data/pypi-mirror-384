# Guidelight

**A library for developing task-oriented AI systems that integrate with Endeavor.**

## Getting Started

Install the guidelight library as follows:

```
$ pip install guidelight
```

To connect to Endeavor you will need an API Key; set the following environment variables to enable Endeavor interactions:

```
ENDEAVOR_URL=https://guidelight.dev
ENDEAVOR_CLIENT_ID=
ENDEAVOR_CLIENT_SECRET=
```

You can then connect to Endeavor as follows:

```python
import guidelight as gdl

endeavor = gdl.connect()
print(endeavor.status())
```
