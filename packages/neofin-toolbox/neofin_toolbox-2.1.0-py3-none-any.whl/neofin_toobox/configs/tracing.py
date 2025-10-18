import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource

# --- Imports de Trace ---
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# --- Imports de Metrics ---
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# --- Imports de Logs (Versão Estável) ---
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

# --- Imports de Instrumentação Automática ---
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def get_resource(service_name: str):
  """Retorna um Resource configurado com o nome do serviço."""
  return Resource(attributes={
    "service.name": service_name
  })

def define_tracer(service_name: str):
    """Define e retorna um TracerProvider configurado."""
    return trace.get_tracer(service_name)

def setup_telemetry(service_name: str, otel_collector_endpoint: str):
    """Configura Traces, Métricas e Logs para enviar ao OTel Collector."""

    # Define o "recurso" com o nome do serviço recebido como parâmetro
    resource = Resource(attributes={
        "service.name": service_name
    })

    # --- Configuração de TRACES ---
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=otel_collector_endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    print(f"TracerProvider configurado para o serviço: {service_name}")

    # --- Configuração de MÉTRICAS ---
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otel_collector_endpoint, insecure=True)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    print("MeterProvider configurado.")

    # --- Configuração de LOGS ---
    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=otel_collector_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    LoggingInstrumentor().instrument(set_logging_format=True, logger_provider=logger_provider)
    print("LoggerProvider configurado.")

    # --- Instrumentação Automática ---
    RequestsInstrumentor().instrument()
    print("Instrumentação automática (Requests) aplicada.")

def instrument_chalice(service_name: str, endpoint: str):
    """
    Função principal da toolbox.
    Recebe o nome do serviço e o endpoint do OTel Collector.
    """
    if not service_name or not endpoint:
        raise ValueError("service_name e endpoint não podem ser vazios.")

    setup_telemetry(service_name=service_name, otel_collector_endpoint=endpoint)
