# React Calculator (Docker-Only)

A simple, user-friendly calculator application built with **React + TypeScript + Vite**, containerized and served via **Docker** and **Nginx**.

It supports basic arithmetic operations:
- Addition (`+`)
- Subtraction (`-`)
- Multiplication (`*`)
- Division (`/`)

The UI includes:
- A calculator display area for the current value/expression
- Buttons for digits, decimal input, operators, equals, and clear

## Run the Application (Required: Docker)

This project is intended to run via Docker only.

From the project root, run:

docker compose up --build

Once the containers are up, open:

http://localhost:8080

## Notes

- The app is served on port **8080** on your host machine.
- The production image uses a multi-stage build (Node for build, Nginx for serving static assets).