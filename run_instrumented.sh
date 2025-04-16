#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install the opentelemetry-instrument package if not already installed
pip install opentelemetry-instrumentation

# Run the specified script with OpenTelemetry instrumentation
opentelemetry-instrument --exporter_otlp_endpoint=http://localhost:4317 python "$@" 