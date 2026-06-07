# GitHub Analytics API Documentation

## Overview

The GitHub Analytics API provides REST endpoints to access GitHub repository metrics and analytics data stored in ClickHouse.

## Base URL
http://localhost:5000

## Authentication

Most endpoints require JWT authentication. Obtain a token using the login endpoint:

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}