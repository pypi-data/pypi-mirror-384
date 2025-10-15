# Arthub SDK for python

This python project provides a series of API interfaces to access the ArtHub server

## Installing

You can install via pip.

```
pip install arthub_api
```

or build from source

```
git clone https://git.woa.com/arthub/arthub-python-sdk.git
cd arthub-python-sdk
python setup.py install
```

## Testing

We provide unit tests in ./test, you can use them with pytest

```
pytest ./tests
```
You can test under different domain by passing the parameter 'env'
```
pytest ./tests --env=oa_test
pytest ./tests --env=qq_test
pytest ./tests --env=oa
pytest ./tests --env=qq
```

## Using the SDK

* Please refer to the SDK usage guide:
  [Usage Guide](./docs/usage_guide.md)
* If you have any questions, please contact joeyding on WeChat Work


## For Developer
* [Developer](./docs/developer_guide.md)