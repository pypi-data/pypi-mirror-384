TYPE_COMPATIBILITY = {
    # Inteiros
    "integer": ["int64", "int32", "int", "Int64", "Int32", "int16"],
    "int": ["int64", "int32", "int", "Int64", "Int32", "int16"],
    "smallint": ["int16", "int32", "int64", "int", "Int64"],
    "bigint": ["int64", "Int64", "int"],
    "tinyint": ["int8", "int", "int64", "bool", "boolean", "Int8"],

    # Flutuantes
    "float": ["float64", "float32", "float", "Float64", "Float32"],
    "real": ["float64", "float32", "float"],
    "numeric": ["float64", "int64", "int", "float"],
    "decimal": ["float64", "int64", "int", "float"],

    # Strings (exceto bool)
    "varchar": [
        "object", "string", "str",
        "int", "int64", "int32", "Int64", "Int32", "int16",
        "float", "float64", "float32", "Float64", "Float32",
        "datetime64[ns]"
    ],
    "char": ["object", "string", "str"],
    "text": [
        "object", "string", "str",
        "int", "int64", "int32", "Int64", "Int32", "int16",
        "float", "float64", "float32", "Float64", "Float32",
        "datetime64[ns]"
    ],

    # Datas
    "date": ["datetime64[ns]", "object"],
    "datetime": ["datetime64[ns]", "object"],
    "timestamp": ["datetime64[ns]", "object"],
    "time": ["datetime64[ns]", "object"],

    # Booleanos
    "boolean": ["bool", "boolean", "int", "int64"],
    "bool": ["bool", "boolean", "int", "int64"],

    # UUIDs
    "uuid": ["object", "string"],

    # JSON
    "json": ["object", "string", "dict"],

    # Outros comuns em bancos corporativos
    "nchar": ["object", "string"],
    "nvarchar": ["object", "string"],
    "clob": ["object", "string"],
    "blob": ["bytes"],
    "binary": ["bytes"],
}

SCHEMA_CONFIG_EXTRACT = {
    "type": "object",
    "required": ["db", "path", "tables"],
    "properties": {
        "db": {
            "type": "object",
            "required": ["hostname", "username", "password", "database", "port", "sgbd"],
            "properties": {
                "hostname": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "database": {"type": "string"},
                "port": {"type": "integer"},
                "sgbd": {"type": "string"},
            }
        },
        "path": {"type": "string"},
        "tables": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name_table", "query", "type_file"],
                "properties": {
                    "name_table": {"type": "string"},
                    "query": {"type": "string"},
                    "type_file": {
                        "type": "string",
                        "enum": ["csv", "json", "parquet"]
                    },
                    "file_sep": {"type": "string"}
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

SCHEMA_CONFIG_INSET = {
    "type": "object",
    "required": ["db", "tables"],
    "properties": {
        "db": {
            "type": "object",
            "required": ["hostname", "username", "password", "database", "port", "sgbd"],
            "properties": {
                "hostname": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "database": {"type": "string"},
                "port": {"type": "integer"},
                "sgbd": {"type": "string"},
            },
            "additionalProperties": False
        },
        "tables": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name_table", "type_file", "path_file", "unwanted_attributes"],
                "properties": {
                    "name_table": {"type": "string"},
                    "type_file": {
                        "type": "string",
                        "enum": ["csv", "json", "parquet"]
                    },
                    "path_file": {"type": "string"},
                    "unwanted_attributes": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "file_sep": {"type": "string"},
                    "primary_key": {"type": "string"},
                    "not_primary_key": {"type": "boolean"},
                    "autoIncrement": {"type": "boolean"}
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

MAP_LENGTH_TYPE = {
    "mysql": {
        "integer": 4,
        "bigint": 8,
        "smallint": 2,
        "tinyint": 1,
        "varchar": lambda length: (length if length and length > 0 else 255) + 1,
        "char": lambda length: (length if length and length > 0 else 1),
        "text": lambda length=None: 30535,
        "float": 4,
        "double": 8,
        "decimal": 8
    },
    "postgresql": {
        "integer": 4,
        "bigint": 8,
        "smallint": 2,
        "varchar": lambda length: (length if length and length > 0 else 255),
        "char": lambda length: (length if length and length > 0 else 1),
        "text": lambda length=None: 30535,
        "real": 4,
        "double precision": 8,
        "numeric": 8
    },
    "oracle": {
        "number": 8,  # estimativa geral
        "varchar2": lambda length: (length if length and length > 0 else 255),
        "char": lambda length: (length if length and length > 0 else 1),
        "nchar": lambda length: ((length if length and length > 0 else 1) * 2),
        "nvarchar2": lambda length: ((length if length and length > 0 else 1) * 2),
        "date": 7,
        "timestamp": 11
    }
}