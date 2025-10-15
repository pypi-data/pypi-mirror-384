# airflow-operators

Custom operators for Apache Airflow

## Installation

> It is assumed that `Apache Airflow` is installed. It is not added to the dependencies for some reason.

> The `mysqlclient` dependency is used. If it is not installed, there may be errors during installation. 
> Install it explicitly using the [documentation](https://pypi.org/project/mysqlclient/).

## List of operators

### Kafka

- CustomConsumeFromTopicOperator
- ConsumeMessageDataOperator

### SQLAlchemy

- SQLAlchemySessionOperator