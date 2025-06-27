# Destination Anonymization

This is the repository for the Destination Anonymization connector, written in Python.
This destination connector provides comprehensive data anonymization capabilities for Airbyte data pipelines.

## Features

- **Column-level anonymization**: Configure anonymization rules for specific columns
- **Multiple generator types**: Support for masking, synthetic data, numeric, and categorical generators
- **Referential integrity**: Maintain foreign key relationships across anonymized data
- **Consistency**: Ensure the same input values produce the same anonymized outputs
- **Flexible configuration**: YAML-based configuration system
- **Multiple destinations**: Output anonymized data to various destinations

## Configuration

The connector accepts the following configuration parameters:

### Anonymization Rules
Configure anonymization transforms by stream and column:

```yaml
anonymization_rules:
  streams:
    users:
      columns:
        email:
          generator_type: "mask_email"
          consistency_key: "user_email"
        first_name:
          generator_type: "fake_name"
          generator_config:
            name_type: "first_name"
          consistency_key: "user_name"
        ssn:
          generator_type: "mask_ssn"
```

### Generator Types

- **mask_email**: Masks email addresses while preserving domain structure
- **mask_phone**: Masks phone numbers while preserving format
- **mask_ssn**: Masks Social Security Numbers
- **fake_name**: Generates realistic fake names
- **fake_address**: Generates realistic fake addresses
- **fake_date**: Generates realistic fake dates
- **numeric_shift**: Shifts numeric values while preserving statistical properties
- **categorical_map**: Maps categorical values to consistent alternatives
- **custom**: Allows custom transformation logic

### Destination Configuration
Configure where to send anonymized data:

```yaml
destination:
  type: "file"  # or "database", "stream"
  config:
    path: "/path/to/output"
    format: "json"
```

## Local development

### Prerequisites
* Python 3.10+
* Poetry

### Installing the connector
From this connector directory, run:
```bash
poetry install
```

### Create credentials
**If you are a community contributor**, follow the instructions in the [documentation](https://docs.airbyte.com/integrations/destinations/anonymization) to generate the necessary credentials. Then create a file `secrets/config.json` conforming to the `destination_anonymization/spec.json` file.

### Locally running the connector
```
poetry run destination-anonymization spec
poetry run destination-anonymization check --config secrets/config.json
poetry run destination-anonymization write --config secrets/config.json --catalog integration_tests/configured_catalog.json
```

### Running unit tests
To run unit tests locally, from the connector directory run:
```
poetry run pytest unit_tests
```

### Building the docker image
1. Install [`airbyte-ci`](https://github.com/airbytehq/airbyte/blob/master/airbyte-ci/connectors/pipelines/README.md)
2. Run the following command to build the docker image:
```bash
airbyte-ci connectors --name=destination-anonymization build
```

An image will be available on your host with the tag `airbyte/destination-anonymization:dev`.

### Running as a docker container
Then run any of the connector commands as follows:
```
docker run --rm airbyte/destination-anonymization:dev spec
docker run --rm -v $(pwd)/secrets:/secrets airbyte/destination-anonymization:dev check --config /secrets/config.json
docker run --rm -v $(pwd)/secrets:/secrets -v $(pwd)/integration_tests:/integration_tests airbyte/destination-anonymization:dev write --config /secrets/config.json --catalog /integration_tests/configured_catalog.json
```

## Testing
Make sure to familiarize yourself with [pytest test discovery](https://docs.pytest.org/en/stable/explanation/goodpractices.html#test-discovery) to know how your test files and methods should be named.

First install test dependencies into your virtual environment:
```
poetry install --with dev
```

### Unit Tests
To run unit tests locally, from the connector directory run:
```
poetry run pytest unit_tests
```

### Integration Tests
There are two types of integration tests: Acceptance Tests (Airbyte's test suite for all destination connectors) and custom integration tests (which are specific to this connector).

#### Custom Integration tests
Place custom tests inside `integration_tests/` folder, then, from the connector directory, run
```
poetry run pytest integration_tests
```

#### Acceptance Tests
Customize `acceptance-test-config.yml` file to configure tests. See [Connector Acceptance Tests](https://docs.airbyte.com/connector-development/testing-connectors/connector-acceptance-tests-reference) for more information.
If your connector requires to create or destroy resources for use during acceptance tests create fixtures for it and place them inside integration_tests/acceptance.py.
To run your integration tests with acceptance tests, from the connector directory, run
```
poetry run pytest integration_tests -v
```

## Dependency Management
All of this connector's dependencies should go in `setup.py`, NOT `requirements.txt`. The requirements file is only used to connect internal Airbyte dependencies in the monorepo for local development.

### Publishing a new version of the connector
You've checked out the repo, implemented a million dollar feature, and you're ready to share your changes with the world. Now what?
1. Make sure your changes are passing our test suite: `airbyte-ci connectors --name=destination-anonymization test`
2. Bump the connector version in `metadata.yaml`: increment the `dockerImageTag` value. Please follow [semantic versioning for connectors](https://docs.airbyte.com/contributing-to-airbyte/resources/pull-requests-handbook/#semantic-versioning-for-connectors).
3. Make sure the `metadata.yaml` content is up to date.
4. Make the connector documentation and its changelog is up to date (`docs/integrations/destinations/anonymization.md`).
5. Create a Pull Request: use [our PR naming conventions](https://docs.airbyte.com/contributing-to-airbyte/resources/pull-requests-handbook/#pull-request-title-convention).
6. Pat yourself on the back for being an awesome contributor.
7. Someone from Airbyte will take a look at your PR and iterate with you to merge it into master.
