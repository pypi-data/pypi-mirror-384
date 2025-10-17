# one_logger_core

## Summary

This Python project contains the API and libraries for OneLogger: A library for collecting telemetry information from jobs.

The following are the dependency rules for various packages (which we will enforce by creating separate python projects in the end state):

- core: Classes representing core concepts such as span, event, attributes. All other packages can depend on this package but this package must not depend on any one_logger or telemetry package. Moreover, we must try to minimize the third-party dependencies of this package so that it remains lightweight and easy to adopt by internal and external users (any new dependency can conflict with existing dependencies of the app that is being instrumented).

- exporter: This package will contain code for various supported exporters. We have a few simple exporters in one_logger_core project. Vendor-specific exporters (OTEL, Kafka, etc) can be added to extend the system. However, each exporter must be added in a separate Python project so that we don't pull in extra dependencies in the `one_logger_core` project.

- api: This package contains the API to record spans and events.

The application is expected to depend on `one_logger_core` project and optionally on any project that contains vendor-specific exporters.

## Concepts

We have defined our abstractions based on open telemetry concepts.

- **Span**: A span represents a unit of work or operation. It can contain events, and can have attributes associated with it. Spans are used to track the execution of operations and their relationships in a distributed system. A span can have a set of events as well as attributes associated with it. In our library, we ensure that a start event is created when the span is created and an end event when the span is stopped. [more info](https://opentelemetry.io/docs/concepts/signals/traces/#spans).
- **Event**: A Span Event represents a meaningful, singular point in time during the Span's duration. Each event has a name, timestamp, and a set of attributes. [more info](https://opentelemetry.io/docs/concepts/signals/traces/#span-events).
- **Attribute**: A property of a span or event.
- **Exporter**: An exporter sends the data from the instrumented application to an observability backend. This can be Kafka, an experiment management system such as Weights and Biases, or a `collector pipeline`. The exporter is responsible to format and serialize data for a particular backend type. For production environments, Open Telemetry recommends exporting the data to a collector pipeline, which then can process and further export the data to the final destination(s). Using a collector pipeline allows the local exporter to stay vendor agnostic, simply send the data to a collector pipeline (e.g., a cluster-level OTEL receiver) and let the collector deal with communication with vendor-specific solutions and backends (serialization for the vendor, retries, filtering sensitive data, and even sending data to multiple backends). Note that this is different from OpenTelemetry's exporter

- **Recorder**: A Recorder makes using all of the above easier. The application can call the Recorder API to start/stop spans, add events, or report errors. The Recorder is in charge of creating the Span/Event objects and then using one or more exporters to send the spans, events, and errors to one or more backends. The recorder decides which exporters to use and when to call them. Here are a few examples of what can be done in a Recorder:

  - Filter (not export) certain events (based on attribute values or verbosity).
  - Add new attributes to a span or events or even create new events. For example, if you have a long-running span for model training in which multiple "save checkpoint" events are emitted, and you want to keep track of the avg, max, and min save times across all the checkpoints, the recorder can keep track of all "save checkpoint" events so far and maintain avg, max, and min values of the "duration" attribute of those events and then emit a "check point stats update" event periodically.

## How to use OneLogger

There are 3 options for colleting telemetry information from applications (including long-running jobs such as ML training):

- Using higher-level domain-specific libraries built on top of One Logger (e.g., one_logger_training_telemetry library). These libraries expose high-level APIs that allow the user to capture well-known operations and events in that domain (e.g., reporting the start/completion of checkpointing in training). If your application is in the domain of one of these high-level libraries, this approach is preferred.

- Using an implementation of the `one_logger.api.Recorder` interface (e.g., `one_logger.recorder.DefaultRecorder`) directly or via the `one_logger.api.timed_span` context manager. Here are a few examples:

```python
from nv_one_logger.api.timed_span import configure_one_logger, get_recorder, timed_span

def main():
    # One-time initialization of the library
    config = OneLoggerConfig(....) # You can use a factory that takes a json or other representation of the configs and creates a OneLoggerConfig object.
    recorder = ... # You can use a factory that takes some config parameters and builds a recorder. 
                   # Or in simple use cases, just use recorder = DefaultRecorder(exporters=[...])
    OneLoggerProvider.instance().configure(config, recorder)

    # A span corresponding to the entire execution of the application. All the work done within the
    # "with timed_span" block will be considered part of a new span.
    with timed_span(name="application", span_attributes=Attributes({"app_tag": "some tag"})):
        # some business logic
        foo()
        # some more business logic

def foo():
    # Another span corresponding to operation Foo
    with timed_span(name="foo", start_event_attributes=Attributes({...})) as span:
        # business logic for operation Foo

        # You can record events of interests within a timed span.
        get_recorder().event(span, Event.create(...))

        # Or record errors
        if(...):
            get_recorder().error(span, ...)
```

- Or you can simply use the `Recorder` interface directly:

```python
def main():

    # One-time initialization at app start up.

    config = OneLoggerConfig(....) # You can use a factory that takes a json or other representation of the configs and creates a OneLoggerConfig object.
    recorder = ... # You can use a factory that takes some config parameters and builds a recorder. 
                   # Or in simple use cases, just use recorder = DefaultRecorder(exporters=[...])
    OneLoggerProvider.instance().configure(config, recorder)

def some_func():
    # ....

    recorder.event(...)

    # ....

    recorder.error(...)

    # ....

    recorder.stop(span)
```

- You can also bypass the `Recorder` interface and `timed_span` and directly instantiate one of more `Exporter`s and use them to export spans and events you have created using the classes under `one_logger.core`. Try to avoid this approach unless really necessary. Using a `Recorder` is preferred as it reduces the chance of making mistakes.

## Exporter Configuration System

One Logger provides a flexible exporter configuration system that allows you to configure exporters through multiple sources with clear priority rules. This system supports:

- **Direct configuration** in code using lists of dictionaries (highest priority)
- **Configuration files** (YAML/JSON) (medium priority)
- **Package-provided configurations** via Python entry points (lowest priority)

**Priority Order**: Direct configuration completely overrides file configuration, which completely replaces package configuration. For detailed information on how to use the exporter configuration system, see the [Exporter Configuration Guide](src/nv_one_logger/core/exporter/README.md).

## Design Considerations

While we could have used Python classes defined in the OpenTelemetry API (such as Span, Attribute, etc.) instead of creating our own classes, this would force any application using our core library to depend on both the OpenTelemetry API and SDK (the latter is needed in the bootstrap code that creates a provider object for creation of spans). This dependency requirement could potentially conflict with the application's existing dependencies or create unnecessary constraints (e.g., when an application already depends on a different version of OpenTelemetry SDK for its own instrumentation needs. A similar problem can happen with conflicting transitive dependencies).

This design decision means applications can use our core library without worrying about OpenTelemetry dependency conflicts, while still benefiting from OpenTelemetry-compatible instrumentation patterns. Users who would like to export data to OpenTelemetry collectors can easily map the data to OpenTelemetry Python classes in the appropriate Exporter implementation.

## Dealing with Telemetry Failures

Like any other piece of software, the one logger library may encounter failures due to misconfiguration, incorrect usage, connection issues with the telemetry backends, or internal bugs in the library. For the rest of this section, we collectively refer to these issues as **telemetry errors**. The library provides several mechanisms to handle telemetry errors correctly:

- Users of the library can choose how telemetry errors are handled using `config.error_handling_strategy`. This enum allows users to treat telemetry as a critical part of the application (potentially letting telemetry errors cause a crash) or as a non-critical component (gracefully handling errors). Please see `OneLoggerErrorHandlingStrategy` enum for more information.

- Regardless of the error handling strategy, If the library encounters a telemetry error, the data exported to the telemetry backends is not guaranteed to be correct anymore. In such cases, the library calls the `export_telemetry_data_error` method of all the exporters. The implementation of this method in each type of Exporter is responsible to send a signal to the corresponding telemetry backend that informs the backend the colelcted data is not reliable. Make sure you familiarize yourself with how the exporters that you use send this signal and have the backend and the any analytics code you write for the backend data use that signal to exclude the data from analytics.

- Note that if you choose to use `DefaultRecorder`, there is another mechanism to help with errors. DefaultRecorder monitors the errors encountered while exporting data to each exporter (note that any recorder can be configured to export to multiple exporters). If a telemetry error is related to exporting to a certain exporter (as opposed to a general issue such as inconsistent telemetry state or misconfigured library). `DefaultRecorder` calls `export_telemetry_data_error` only on that exporter (as the data exported to the other exporters is not affected by that issue). If the exporter continues to fail frequently, `DefaultRecorder` disables that exporter.

In summary:

- Choose your desired error handling stratgy via `config.error_handling_strategy`.
- For each backend, the corresponding Exporter implementation sends some info about missing or corrupted data to that backend. When using the telemetry data stored on your telemetry backend, pay attention to reports about data issues.
