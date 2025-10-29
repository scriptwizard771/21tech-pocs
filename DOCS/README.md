# 21Tech POCS Documentation

Welcome to the documentation for the 21Tech Proof-of-Concepts (POCs) Django project. This documentation provides a detailed overview of the various applications, their architecture, and their functionalities.

## Quick Start

**🚀 Production Deployment**: For quick deployment instructions, see [Deployment Guide](./deployment.md)

**🔗 API Access**: The production API is available at `https://54.219.76.120:8001/`

**⚠️ SSL Certificate Notice**: First-time users need to manually accept the self-signed SSL certificate in their browser. See [Usage Guide](./deployment.md#accessing-the-api) for details.

## Table of Contents

### Applications

- [Common Services](./common.md)
- [Equipment Entry Assistant](./equipment_entry_app.md)
- [Maintenance Assistant](./maintenance_assistant.md)
- [Safety Procedure Assistant](./safety_procedure_assistant.md)
- [Service Manuals Assistant](./service_manuals_assistant.md)
- [Training Manuals Assistant](./training_manuals_assistant.md)

### Deployment & Usage

- [Deployment Guide](./deployment.md) - Production deployment with Docker
- [API Usage Guide](./deployment.md#api-endpoints) - How to use the REST APIs
- [SSL Certificate Setup](./deployment.md#ssl-certificate-setup) - Browser configuration for HTTPS

### Architecture

For a high-level overview of the system architecture, please refer to the documentation for the [Common Services](./common.md#architecture-overview).
