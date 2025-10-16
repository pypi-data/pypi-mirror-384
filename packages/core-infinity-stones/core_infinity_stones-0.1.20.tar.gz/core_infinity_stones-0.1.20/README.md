# To Build and Deploy
python3 setup.py sdist bdist_wheel && twine upload dist/*

# Breaking Changes:

## v0.0.28
1- The `url` param in the logger initializer, was removed
2- the request_details param is mandatory
3- The `user_agent` param form the logger initializer, was moved inside the RequestDetails object.


## v0.1.0
1- The `service` param in the logger initializer, was removed
2- The `tracing_details_resolver` param in the logger initializer was removed
3- The `trace_id` mandatory param was added in in the logger initializer

## v0.1.7
1- The `logger` param in the logger initializer, was removed