# About this project

This is a pure functional and complete typed aws lambda runtime interface client implementation.

Unlike the `awslambdaric` that dynamically imports the function code/module and acts like a module wrapper, this library brings tools to make your module the listener itself.
This architectural change is necessary to ensure type-correctness.

# How to use?

1. define an event function handler

    Create a function that will be called on each lambda trigger.
    The function should be of type `HandlerFunction` i.e.

    Inputs:

        1. `Event`: the json event data supplied to the lambda.
        2. `Context`: the lambda metadata.
    Output: `Cmd[Result[JsonObj, LambdaError]]`
    - a command that will produce a result i.e. a json successful value or a `LambdaError`

2. define the handler map

    Set a name for your handler and add it to the handler map.
    - The handler is of type `FrozenDict[HandlerId, HandlerFunction]`

    e.g.
    ```
    handler_map = FrozenDict({
        HandlerId("my_function_name"): my_function
    })
    ```
    You can add as many handlers as you want.

3. start the listener

    Wrap all your handler map definition, even the imports, into a callable.
    Then pass it into `start_lambda_listener` to build a command that will execute the event loop with your custom handler map.
    e.g.
    ```
    import logging
    LOG = logging.getLogger(__name__)

    def handler_map(): -> HandlerMap:
        from . import my_function
        return FrozenDict({
            HandlerId("my_function_name"): my_function
        })

    start_lambda_listener(LOG, handler_map).compute()
    ```

4. call the entrypoint

    Since the handler map and the listener trigger are within your module/code, you must define and call the entrypoint that calls `start_lambda_listener`

    - wrap the listener call into a function
    ```
    def my_entrypoint() -> NoReturn:
        start_lambda_listener(LOG, handler_map).compute()
    ```

    - define a script on pyproject.toml
    ```
    [project.scripts]
    my-entrypoint = 'my_pkg.my_module:my_entrypoint'
    ```

    - configure the entrypoint on the docker image
    ```
    ENTRYPOINT [ "/path/to/my-entrypoint" ]
    ```
