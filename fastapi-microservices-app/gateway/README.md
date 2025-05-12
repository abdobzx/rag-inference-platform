# FastAPI Microservices Gateway

This directory contains the implementation of the Gateway service for the FastAPI microservices application. The Gateway acts as a single entry point for clients to interact with the various microservices, including authentication, inference, and logging services.

## Structure

- `src/main.py`: The entry point of the FastAPI application for the Gateway service. It initializes the application and configures the routes.
- `src/routes/gateway.py`: This file defines the routes for the Gateway, which redirect requests to the appropriate microservices.

## Features

- **Routing**: The Gateway service routes requests to the appropriate microservices based on the endpoint.
- **Security**: Integrates with the authentication service to ensure secure access to the microservices.
- **Scalability**: Designed to handle multiple microservices, allowing for easy addition of new services in the future.

## Setup

To set up the Gateway service, ensure you have the necessary dependencies listed in `requirements.txt`. You can install them using:

```
pip install -r requirements.txt
```

## Running the Service

To run the Gateway service, execute the following command from the `src` directory:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Documentation

The API documentation for the Gateway service can be accessed at `http://localhost:8000/docs` after running the service.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.