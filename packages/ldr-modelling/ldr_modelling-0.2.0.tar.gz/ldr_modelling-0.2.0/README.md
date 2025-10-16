# Pydantic extensions for modelling

> ⚠️  This library is in beta, breaking API changes may happen prior to version 1.0.0. We stringly recommend pinning your chosen version.

## Motivation

Create a set of extensions to the [Pydantic](https://docs.pydantic.dev/latest/) library to make it easier to create schema definitions for BigQuery from modelled data.

### BigQuery

Included in `ldr.modelling.bigquery` is the `Model` class which is a subclass of `pydantic.BaseModel` that adds `to_bigquery_schema` and `to_bigquery_schema_dict`, and `to_bigquery_schema_ser` methods to the class. These methods return the schema in various different formats.

#### Usage

```python
from ldr.modelling import bigquery
from datetime import datetime

class MyModel(bigquery.Model):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
```

```python
>>> MyModel.to_bigquery_schema_dict()
[
    {'name': 'id', 'type': 'INTEGER', 'mode': 'REQUIRED'},
    {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED'},
    {'name': 'description', 'type': 'STRING', 'mode': 'REQUIRED'},
    {'name': 'created_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
    {'name': 'updated_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'}
]
```

This also supports `pydantic.Field` as default values, and will use the `description` attribute as the BigQuery description.

```python
from ldr.modelling import bigquery
from datetime import datetime
from pydantic import Field

class MyModel(bigquery.Model):
    id: int = Field(description="The ID of the model")
    name: str = Field(description="The name of the model")
    description: str = Field(description="The description of the model")
    created_at: datetime = Field(description="The date the model was created")
    updated_at: datetime = Field(description="The date the model was last updated")
```

```python
>>> MyModel.to_bigquery_schema_dict()
[
    {'name': 'id', 'type': 'INTEGER', 'mode': 'REQUIRED', 'description': 'The ID of the model'},
    {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The name of the model'},
    {'name': 'description', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The description of the model'},
    {'name': 'created_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED', 'description': 'The date the model was created'},
    {'name': 'updated_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED', 'description': 'The date the model was last updated'}
]
```

You can use `T | None` union types to specify nullable fields. Note that no other union types are supported, as they are not supported in BigQuery.

```python
from ldr.modelling import bigquery
from datetime import datetime
from pydantic import Field

class MyModel(bigquery.Model):
    id: int = Field(description="The ID of the model")
    name: str = Field(description="The name of the model")
    description: str = Field(description="The description of the model")
    created_at: datetime = Field(description="The date the model was created")
    updated_at: datetime = Field(description="The date the model was last updated")
    deleted_at: datetime | None = Field(description="The date the model was deleted")
```

```python
>>> MyModel.to_bigquery_schema_dict()
[
    {'name': 'id', 'type': 'INTEGER', 'mode': 'REQUIRED', 'description': 'The ID of the model'},
    {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The name of the model'},
    {'name': 'description', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The description of the model'},
    {'name': 'created_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED', 'description': 'The date the model was created'},
    {'name': 'updated_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED', 'description': 'The date the model was last updated'},
    {'name': 'deleted_at', 'type': 'TIMESTAMP', 'mode': 'NULLABLE', 'description': 'The date the model was deleted'}
]
```

Lastly you can also use subclasses of `bigquery.Model` as fields. This will create a `RECORD` type in BigQuery. Lists of `bigquery.Model` subclasses are supported and will generate a `REPEATED RECORD` type in BigQuery.

```python
from ldr.modelling import bigquery
from datetime import datetime
from pydantic import Field

class MySubModel(bigquery.Model):
    id: int = Field(description="The ID of the model")
    name: str = Field(description="The name of the model")

class MyModel(bigquery.Model):
    id: int = Field(description="The ID of the model")
    name: str = Field(description="The name of the model")
    description: str = Field(description="The description of the model")
    created_at: datetime = Field(description="The date the model was created")
    updated_at: datetime = Field(description="The date the model was last updated")
    deleted_at: datetime | None = Field(description="The date the model was deleted")
    sub_model: MySubModel = Field(description="A sub model")
```

```python
>>> MyModel.to_bigquery_schema()
[
    {'name': 'id', 'type': 'INTEGER', 'mode': 'REQUIRED', 'description': 'The ID of the model'},
    {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The name of the model'},
    {'name': 'description', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The description of the model'},
    {'name': 'created_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED', 'description': 'The date the model was created'},
    {'name': 'updated_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED', 'description': 'The date the model was last updated'},
    {'name': 'deleted_at', 'type': 'TIMESTAMP', 'mode': 'NULLABLE', 'description': 'The date the model was deleted'},
    {'name': 'sub_model', 'type': 'RECORD', 'mode': 'REQUIRED', 'description': 'A sub model', 'fields': [
        {'name': 'id', 'type': 'INTEGER', 'mode': 'REQUIRED', 'description': 'The ID of the model'},
        {'name': 'name', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'The name of the model'}
    ]}
]
```

You can also use `enum.Enum` classes and `typing.Literal` expressions, under the condition that all members are of the same type. The type output in BigQuery will depend on the inner type of the `typing.Literal`, e.g `typing.Literal[1, 2, 3]` will become `INTEGER`, same for `enum.Enum`.

```python
import enum
import typing
from ldr.modelling import bigquery

State = typing.Literal["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
# OR
class State(enum.StrEnum):
    ACT = "ACT"
    NSW = "NSW"
    NT = "NT"
    QLD = "QLD"
    SA = "SA"
    TAS = "TAS"
    VIC = "VIC"
    WA = "WA"

class Address(bigquery.Model):
    state: State
    postcode: int

>>> Address.to_bigquery_schema_dict()
[
    {'name': 'state', 'type': 'STRING', 'mode': 'REQUIRED'},
    {'name': 'postcode', 'type': 'INTEGER', 'mode': 'REQUIRED'},
]
```

#### Support for NUMERIC, BIGNUMERIC, TIMESTAMP, and GEOGRAPHY types.

To define fields as the above types, use the exposed classes from the `ldr.modelling.bigquery.types` module. This module provides types and pydantic validators for each of the above, for example `ldr.modelling.bigquery.types.Numeric` and `ldr.modelling.bigquery.types.NumericValidator`. These should be used as:

```python
from typing import Annotated

from ldr.modelling import bigquery
from ldr.modelling.bigquery.types import (
    BigNumeric,
    BigNumericValidator,
    Geography,
    GeographyValidator,
    Numeric,
    NumericValidator,
    Timestamp,
    TimestampValidator,
)

class Model(bigquery.Model):
    geo: Annotated[Geography, GeographyValidator]
    bignum: Annotated[BigNumeric, BigNumericValidator]
    num: Annotated[Numeric, NumericValidator]
    ts: Annotated[Timestamp, TimestampValidator]
```

Behind the scenes, these provided types are effectively marker types for the actual types used by the `google-cloud-bigquery` client library for these fields, those being:

- `GEOGRAPHY`: `shapely.geometry.base.BaseGeometry`
- `BIGNUMERIC`: `decimal.Decimal`
- `NUMERIC`: `decimal.Decimal`
- `TIMESTAMP`: `datetime.datetime`

You may also use `decimal.Decimal` directly in order to specify a `NUMERIC` field.

The `ldr.modelling.bigquery.types.GeographyValidator` can handle validation and parsing of `str` in [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format, `bytes` in [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format, a `shapely.geometry.base.BaseGeometry` object, or a `dict` in [GeoJSON](geojson.io) format.


### Models for case conventions

Included in `ldr.modelling` are modules named after case conventions such as `camel_case`. This allows for aliasing fields easily in Pydantic models. For example:

```python
from ldr.modelling import camel

class MyModel(camel.Model):
    my_field: str
```

```python

>>> MyModel(my_field="test").model_dump(by_alias=True)
{'myField': 'test'}
```

Since python supports multiple inheritance, you can use these classes in conjunction with `bigquery.Model` to create models that are both serialisable to BigQuery and have fields that are named in a case convention.

```python
from ldr.modelling import bigquery, camel

class MyModel(camel.Model, bigquery.Model):
    my_field: str
```

```python
>>> MyModel.to_bigquery_schema_dict(by_alias=True)
[
    {'name': 'myField', 'type': 'STRING', 'mode': 'REQUIRED'}
]
```
