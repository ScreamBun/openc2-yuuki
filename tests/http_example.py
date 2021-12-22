import cbor2

from yuuki import Http, HttpConfig, Serialization


serializations = [
    Serialization(name='cbor', deserialize=cbor2.loads, serialize=cbor2.dumps)
]

consumer = Http(rate_limit=60, versions=['1.0'], http_config=HttpConfig(), serializations=serializations)
consumer.start()
