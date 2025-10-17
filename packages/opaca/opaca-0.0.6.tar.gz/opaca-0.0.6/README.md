# OPACA API Python Implementation

This module provides an implementation of the OPACA API in Python, using FastAPI to provide the different REST routes.
The 'agents' in this module are not 'real' agents in the sense that they run in their own thread, but just objects that
react to the REST routes.

## Installation

You can install the package by running `pip install opaca` and then `import opaca` into your project files.

## Developing new Agents

Following is a minimal example of how to develop a new agent by using the OPACA Python SDK.

1. Start by creating a new directory for your project and add the following files to it:

    ```
    your_project/
    ├── src/
    │   ├── my_agent.py
    │   └── main.py
    ├── resources/
    │   └── container.json
    ├── Dockerfile
    └── requirements.txt
    ```

2. Then add the following basic contents to these files:

    #### requirements.txt
    
    ```pycon
    opaca
    # Other required packages
    ```
    
    #### Dockerfile
    
    ```docker
    FROM python:3.12-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    COPY . .
    CMD ["python", "main.py"]
    ```
    
    #### resources/container.json
    
    ```json
    {
      "imageName": "<your-container-name>"
    }
    ```
    
    #### src/main.py
    
    ```pycon
    from opaca import Container, run
    from my_agent import MyAgent
    
    # Create a container based on the container.json file
    container = Container("../resources/container.json")
    
    # Initialize the agents. The container must be passed to the agent, to automatically register the agent on the container.
    MyAgent(container=container, agent_id='MyAgent')
    
    # Run the container. This will start a FastAPI server and expose endpoints required for communication within the OPACA framework.
    if __name__ == "__main__":
        run(container)
    ```

3. Finally, define the actual agent class in `src/my_agent.py` by creating a new class inheriting from `opaca.AbstractAgent`. Then add a class method for each action you want to expose and use the `@action` decorator to register it as an OPACA action.

    #### src/my_agent.py

    ```pycon
    from opaca import AbstractAgent, action
    
    class MyAgent(AbstractAgent):
    
        def __init__(self, **kwargs):
            super(MyAgent, self).__init__(**kwargs)
   
        @action
        def add(x: float, y: float) -> float:
            """Returns the sum of numbers x and y."""
            return x + y
    ```

    **`@action` Decorator - Additional Notes**:

   - It is required for **all input and output parameters to be annotated with type hints**. The type hints are later resolved into JSON schema to be used within HTTP requests.
   - Action methods need to be defined as **non-static**, even if they are not accessing any class attributes or methods. This is to ensure that the method can be pickled and registered as an OPACA action for that agent.
   - You can also use type hints from the `typing` library to define the input and output parameters. This includes types such as `List`, `Dict`, `Tuple`, `Optional`, etc.
   - Agent actions can also be defined `async`.
   - If there are any issues with specific type hints, please open a new [issue in this repository](https://github.com/GT-ARC/opaca-python-sdk/issues), explain what type hint is causing issues, and provide a minimal example. We will try to fix the issue as soon as possible. As a workaround, you can always fall back to using the `self.add_action()` in the agent constructor to manually register an action. A reference implementation can be found in [src/sample.py](https://github.com/GT-ARC/opaca-python-sdk/blob/main/src/sample.py).

## Testing & Deployment

### Build and Deploy the Agent Container (recommended)

1. Build your container image from the root directory by using the `Dockerfile` you created: 

    ```shell
    docker build -t <your-container-name> .
    ```

2. Next, make sure you have a running OPACA Runtime Platform instance. The easiest way to achieve this is by using the published docker image from the [OPACA-Core](https://github.com/gt-arc/opaca-core) repository. (**Note**: Find out your local IP by running `ipconfig` on Windows or `ifconfig` on Linux. `localhost` will not work!)

    ```shell
    docker container run -d -p 8000:8000 \
   -v /var/run/docker.sock:/var/run/docker.sock \
   -e PUBLIC_URL=http://<YOUR_IP>:8000 \
   -e PLATFORM_ENVIRONMENT=DOCKER ghcr.io/gt-arc/opaca/opaca-platform:main
    ```

3. Finally, you can deploy your container to the running OPACA Platform. For this, you can use the integrated Swagger UI, which will be available at `http://<YOUR_IP>:8000/swagger-ui/index.html` once the OPACA Runtime Platform has been started. Navigate to the `POST /containers` endpoint, click "Try it out", replace the request body with the following content and then click "Execute":
    
    ```json
    {
      "image": {
        "imageName": "<your-container-name>"
      }
    }
    ```

    If an uuid is returned, the container has been deployed successfully. You can then test your implemented function by calling the `POST /invoke/{action}` route with your implemented action name and input parameters in the request body.

    If you find a problem with your container and want to test it again after fixing, you can paste the payload from `POST /container` to `PUT /container`. This will automatically DELETE and then POST a new container (effectively updating the old container), whereas calling POST again would start a second instance.

    An implemented example can be found in [src/sample.py](https://github.com/GT-ARC/opaca-python-sdk/blob/main/src/sample.py).

### Run the Agent Container Locally

Alternatively, you can directly start your agent container by running `python main.py` from the root directory. This will start a FastAPI server and make the endpoints of the agent available for testing at http://localhost:8082/docs, assuming you haven't customized the port in the `run()` function.

## Custom Data Types

If your agent is using custom data types as either input or output parameters, you need to register them in the `resources/container.json` file in OpenAPI format. It is recommended to define custom data types with the `BaseModel` class from the [Pydantic](https://pydantic-docs.helpmanual.io/) library.

Here is an example for a custom data type `MyType`:

In your agent class:

```pycon
from pydantic import BaseModel
from typing import List

class MyType(BaseModel):
    var_a: str
    var_b: int = 0
    var_c: List[str] = None
```

In the `resources/container.json` file:

```json
{
  "imageName": "<your-container-name>",
  "definitions": {
    "MyType": {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "MyType",
      "type": "object",
      "properties": {
        "var_a": {
          "description": "Optional description of var_a.",
          "type": "string"
        },
        "var_b": {
          "description": "Optional description of var_b.",
          "type": "integer"
        },
        "var_c": {
          "description": "Optional description of var_c.",
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": ["var_a"]
    }
  }
}
```

## Environment Variables

Agent Containers can be passed environment variables during deployment. This is useful if you need to pass either sensitive information, such as an api-key, or if you want to configure your agent based on some external configuration, such as a database connection string.

You can pass environment variables to your agent container by declaring them in the `resources/container.json` file and then passing the actual values during the container deployment via the `POST /containers` endpoint.

Here is an example for an environment variable `MY_API_KEY`:

In your `resources/container.json` file:

```json
{
  "imageName": "<your-container-name>",
  "parameters": [
    {
        "name": "MY_API_KEY",
        "type": "string",
        "required": true,
        "confidential": true,
        "defaultValue": null
    }
  ]
}
```

During the container deployment, your request body to the `POST /containers` would then look like this:

```json
{
  "image": {
    "imageName": "<your-container-name>",
    "parameters": [
      {
        "name": "MY_API_KEY",
        "type": "string",
        "required": true,
        "confidential": true,
        "defaultValue": null
      }
    ]
  },
  "arguments": {
    "MY_API_KEY": "<your-api-key>"
  }
}
```

#### Parameter explanation:

- `name`: The name of the environment variable.
- `type`: The type of the environment variable. Use [JSON schema](https://json-schema.org/understanding-json-schema/reference/type) types.
- `required`: Whether the environment variable is required or not. If `true`, the environment variable must be passed during the container deployment. Otherwise the container deployment will fail.
- `confidential`: If `true`, the value of this environment variable will never be logged or exposed within any OPACA API calls.
- `defaultValue`: The default value of the environment variable. Set to `null` if the parameter is required.

## Custom Routes

You can also define custom routes for your container, by manually creating a FastAPI app with the `create_routes()` function and adding custom routes to it. Remember that you then need to pass your custom FastAPI app to the `run()` function.

```pycon
from opaca import Container, run, create_routes
from my_agent import MyAgent

# Create a container based on the container.json file
container = Container("../resources/container.json")

# Initialize the agents. The container must be passed to the agent, to automatically register the agent on the container.
MyAgent(container=container, agent_id='MyAgent')

# Create a pre-configured FastAPI app and add custom routes to it.
app = create_routes("my-agent", container)

@app.get("/my-custom-route")
def my_custom_route():
    return "Hello World!"

# Run the container. This will start a FastAPI server and expose endpoints required for communication within the OPACA framework.
if __name__ == "__main__":
    run(container, app=app)
```

## Authentication

It might be useful for your use-case to implement authentication for your agent, so it can determine the identity of the user who is calling the agent. This might be applicable when impelementing agents, connecting to external APIs, requiring user credentials. The OPACA framework defines a so-called "Container Login", in which an identifiable user token (uuid) is sent with each request. This token can then be used in your agent logic and to restrict specific actions to users with valid credentials, or make external API calls with the provided credentials.

### Container Login Routes

To differentiate between different users, you first need to implement the following two functions in your agent:

```pycon
self.clients: Dict[str, Callable] = {}

async def handle_login(self, login_msg: LoginMsg):
    # LoginMsg has the following attributes:
    # - login.token - a unique token generated by your container
    # - login.login.username - The username a user has entered
    # - login.login.password - The password a user has entered
    self.clients[login.token] = lambda: f'Logged in as user: {login.login.username}'

async def handle_logout(self, login_token: str):
    # Here you can handle logout operation, e.g., deleting clients bound to the token
    del self.clients[login_token]
```

The `handle_login()` function will be called whenever a user attempts a container login. Currently, the only supported authentication method is username and password. It lies in your responsibility to handle the password hashing and comparison if necessary. This function does not need to return anything, but you could attempt an external API login, check if it succeeded, and if not, raise an `HttpException(401, "Invalid Credentials")` error.

The `handle_logout()` function is optional to implement, but it is strongly recommended to implement it, as it allows you to clean up any resources associated with the user.

### Actions with Authentication

Once you have implemented the `handle_login()` and `handle_logout()` functions, you can now declare actions as `@action(auth=True)`, which will indicate to the action, that any attempt without a `login_token` shall automatically raise an `HttpException(401, "Missing Credentials")` error.

**Important**: Any actions you do decide to declare as requiring authentication, **must** include the parameter `login_token` in the function definition. This value will then hold the `login_token`, that was sent with each request following a container login of the OPACA platform in the header field `ContainerLoginToken`. If no `login_token` parameter was found in an action with `auth=True`, the container will raise an exception during startup. The `login_token` does not need to be provided via the request body, as it will be automatically extracted from the correct header field.

Following is an example of an action that requires authentication:

```pycon
@action(auth=True)
async def login_test(self, login_token: str)
    # Check if the login_token has been sent previously with a successful login attempt.
    # Otherwise, raise an appropriate exception.
    # The agent container will automatically handle missing requests with a missing login_token
    if login_token not in self.clients.keys():
        raise HTTPException(status_code=403, detail='Forbidden')
    return f'Calling authenticated client with login_token: {login_token}\n{self.clients[login_token]()}'
```

Please note that it is in your own responsibility to check if the provided login_token matches the same token that was sent during the call to the `handle_login()` function.

### Streams with Authentication

Streams can be declared with `@stream(mode=StreamDescription.Mode.GET, auth=True)`, expecting the parameter `login_token` to be present in the function definition as well. The overall structure is very similar to actions.

```pycon
@stream(mode=StreamDescription.Mode.GET, auth=True)
async def login_test_stream(self, login_token: str):
    if login_token not in self.clients.keys():
        raise HTTPException(status_code=403, detail='Forbidden')
    yield b'Calling authenticated stream with login_token: ' + login_token.encode() + b'\n' + self.clients[login_token]().encode()
```

## Additional Information

* All agent classes should extend the `AbstractAgent` class. Make sure to pass a `Container` object to the agent.
* In the agent's constructor `__init__`, you can register actions the agents can perform using the `add_action()` method from the super-class. 
* Alternatively, you can expose actions by using the `@action` decorator on a method.
* Similarly, stream responses can be defined using the `@stream` decorator or the `add_stream()` method in the constructor `__init__`.
* Decorators will use the method name as the action name in PascalCase, the docstring as description, and use type hints to determine the input and output parameter types.
* When registering actions or streams, you can manually specify their name and description by using the `name` and `description` field within the parameter, e.g. `@action(name="MyAction", description="My description")`.
* Methods declared as streams should return some iterator, e.g. by using the `yield` keyword on an iterable.
* Messages from the `/send`  and `/broadcast` routes can be received by overriding the `receive_message()` method.

## Linked Projects

* [OPACA Core](https://github.com/GT-ARC/opaca-core): The OPACA Runtime Platform.
* [OPACA-LLM](https://github.com/GT-ARC/opaca-llm-ui): A complementary LLM integration, autonomously calling agent actions on a connected OPACA Runtime Platform.
