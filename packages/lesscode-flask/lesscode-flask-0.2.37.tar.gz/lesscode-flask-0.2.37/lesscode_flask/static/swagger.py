swagger_json = {
  "openapi": "3.0.0",
  "info": {
    "title": "Example API",
    "version": "1.0.0",
    "description": "This is an example API that demonstrates OpenAPI 3.0 features."
  },
  "servers": [
    {
      "url": "https://api.example.com/v1",
      "description": "Main production server"
    }
  ],
  "paths": {
    "/api/v1/greet": {
      "get": {
        "summary": "Get a greeting message",
        "description": "This endpoint returns a greeting message to the user.",
        "operationId": "getGreeting",
        "security": [
          {
            "BearerAuth": []
          }
        ],
        "responses": {
          "200": {
            "description": "A greeting message",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Greeting"
                }
              }
            }
          },
          "400": {
            "description": "Bad Request - Missing or invalid Authorization header"
          }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    },
    "schemas": {
      "Greeting": {
        "type": "object",
        "properties": {
          "message": {
            "type": "string",
            "example": "Hello, John Doe!"
          },
          "lang": {
            "type": "string",
            "example": "en"
          }
        }
      }
    }
  }
}
