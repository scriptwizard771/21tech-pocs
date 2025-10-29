# 21Tech AI-Powered EAM Assistants (POCS)

This repository contains a collection of Proof-of-Concept (POC) applications built with Django and leveraging AI to enhance and automate processes within the HxGN EAM system.

## Project Overview

The core of this project is a Django backend that serves as an "AI Development" platform. It integrates with HxGN EAM via its web services API and utilizes Large Language Models (LLMs) like OpenAI's GPT series, along with document parsing engines, to provide intelligent assistance for various maintenance and asset management tasks.

### Architecture

![Architecture Diagram](./DOCS/images/21%20Tech%20Use%20Cases-Template.jpg)

### Key Technologies

- **Backend**: Django
- **Database/Search**: Elasticsearch
- **AI/LLMs**: LangChain, OpenAI, Ollama
- **Document Parsing**: `unstructured`
- **EAM System**: HxGN EAM

## Applications

This project is structured as a series of Django apps, each serving a specific purpose:

- `equipment_entry_app`: Assists with the intelligent and automated entry of new equipment data.
- `maintenance_assistant`: Helps in processing maintenance documents to create structured task plans and checklists.
- `safety_procedure_assistant`: Analyzes safety incident reports to identify hazards and precautions.
- `service_manuals_assistant`: Extracts task plans from service manuals.
- `training_manuals_assistant`: Extracts technician qualifications from training manuals.
- `common`: A shared application providing core services for EAM communication, LLM integration, configuration management, etc.

## Documentation

For detailed technical documentation on the project architecture, applications, and modules, please see the **[./DOCS/README.md](./DOCS/README.md)** file.

## Setup and Installation

*... (To be added) ...*
