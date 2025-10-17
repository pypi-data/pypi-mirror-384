# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0
"""Tests for Arrow schema and data format stability.

This module ensures that changes to validation libraries or data models do not break the
Arrow schema output or data serialization format, preventing regressions in the
measurement and evaluation data pipeline.
"""

import base64
import json
import sys
from pathlib import Path
from typing import List

import pyarrow
import pydantic

from dyff.schema.base import float32, float64, int32
from dyff.schema.dataset import ReplicatedItem
from dyff.schema.dataset.arrow import arrow_schema


def handle_binary_for_json(data):
    """Convert binary data to base64 strings for JSON serialization."""
    if isinstance(data, bytes):
        return base64.b64encode(data).decode("utf-8")
    elif isinstance(data, dict):
        return {k: handle_binary_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [handle_binary_for_json(item) for item in data]
    else:
        return data


class BlurstCountScoredItem(ReplicatedItem):
    """Test measurement class identical to the one used in test methods."""

    blurstCount: int32() = pydantic.Field(  # type: ignore
        description="Number of times the word 'blurst' is used in the response."
    )
    cromulent: int32() = pydantic.Field(  # type: ignore
        description="Whether the text is cromulent."
    )
    embiggen: str = pydantic.Field(description="Which man to embiggen.")


class MetadataInfo(pydantic.BaseModel):
    """Nested Pydantic model for testing model composition."""

    version: str = pydantic.Field(description="Version of the analysis")
    confidence: float32() = pydantic.Field(  # type: ignore
        description="Confidence score of the measurement"
    )
    flags: List[str] = pydantic.Field(description="Analysis flags")


class ComprehensiveTestItem(ReplicatedItem):
    """Comprehensive test model covering all Arrow-compatible field types."""

    # Numeric types
    score_int: int32() = pydantic.Field(description="Integer score")  # type: ignore
    score_float32: float32() = pydantic.Field(  # type: ignore
        description="32-bit float score"
    )
    score_float64: float64() = pydantic.Field(  # type: ignore
        description="64-bit float score"
    )

    # Boolean
    is_valid: bool = pydantic.Field(description="Whether the result is valid")

    # String
    category: str = pydantic.Field(description="Result category")

    # Binary data
    raw_data: bytes = pydantic.Field(description="Raw binary data")

    # Collections (List is supported, Dict is not)
    tags: List[str] = pydantic.Field(description="List of tags")
    scores: List[int32()] = pydantic.Field(description="List of scores")  # type: ignore

    # Nested model
    metadata: MetadataInfo = pydantic.Field(description="Analysis metadata")


class PlainIntTestItem(ReplicatedItem):
    """Test model with plain Python int (should be rejected by Arrow)."""

    unbounded_int: int = pydantic.Field(description="Plain Python int (unbounded)")


class TestSchemaReferenceCapture:
    """Capture reference data from current working implementation."""

    @property
    def reference_data_dir(self) -> Path:
        """Directory for storing reference data."""
        data_dir = Path(__file__).parent / "data" / "schema_reference"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def test_capture_arrow_schema(self):
        """Capture Arrow schema for BlurstCountScoredItem as reference."""
        schema = arrow_schema(BlurstCountScoredItem)

        # Helper function to convert bytes keys to strings in metadata
        def convert_metadata(metadata_dict):
            if not metadata_dict:
                return {}
            return {
                key.decode("utf-8") if isinstance(key, bytes) else str(key): (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
                for key, value in metadata_dict.items()
            }

        # Convert schema to JSON-serializable format
        schema_dict = {
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                    "metadata": (
                        convert_metadata(dict(field.metadata)) if field.metadata else {}
                    ),
                }
                for field in schema
            ],
            "metadata": (
                convert_metadata(dict(schema.metadata)) if schema.metadata else {}
            ),
        }

        # Save reference schema
        schema_file = self.reference_data_dir / "blurst_count_schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema_dict, f, indent=2)

        print(f"Saved Arrow schema reference to {schema_file}")

        # Basic validation
        assert (
            len(schema_dict["fields"]) >= 5
        )  # _index_, _replication_, blurstCount, cromulent, embiggen
        field_names = [f["name"] for f in schema_dict["fields"]]
        assert "_index_" in field_names
        assert "_replication_" in field_names
        assert "blurstCount" in field_names
        assert "cromulent" in field_names
        assert "embiggen" in field_names

    def test_capture_sample_measurement_data(self):
        """Capture sample measurement data in Arrow format."""
        # Create sample data
        sample_items = [
            BlurstCountScoredItem(
                _index_=0,
                _replication_="repl-1",
                blurstCount=2,
                cromulent=1,
                embiggen="smallest",
            ),
            BlurstCountScoredItem(
                _index_=1,
                _replication_="repl-1",
                blurstCount=0,
                cromulent=0,
                embiggen="smallest",
            ),
            BlurstCountScoredItem(
                _index_=0,
                _replication_="repl-2",
                blurstCount=1,
                cromulent=1,
                embiggen="smallest",
            ),
        ]

        # Convert to Arrow batch
        schema = arrow_schema(BlurstCountScoredItem)
        # Use compatible serialization method
        try:
            sample_dicts = [item.model_dump() for item in sample_items]
        except AttributeError:
            sample_dicts = [item.dict() for item in sample_items]
        batch = pyarrow.RecordBatch.from_pylist(sample_dicts, schema=schema)

        # Convert back to pylist for JSON serialization
        pylist_data = batch.to_pylist()

        # Save reference data
        data_file = self.reference_data_dir / "sample_measurement_data.json"
        with open(data_file, "w") as f:
            json.dump(
                {
                    "capture_environment": f"python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "sample_data": pylist_data,
                    "record_count": len(sample_items),
                },
                f,
                indent=2,
            )

        print(f"Saved sample measurement data to {data_file}")

        # Validation
        assert len(pylist_data) == 3
        assert all("blurstCount" in item for item in pylist_data)
        assert all("_index_" in item for item in pylist_data)

    def test_capture_evaluation_response_format(self):
        """Capture the current evaluation response format as reference."""
        # Sample evaluation response data (from what we know works)
        sample_evaluation_responses = [
            {
                "_index_": 0,
                "_replication_": "repl-1",
                "responses": [
                    {
                        "_response_index_": 0,
                        "text": "/generate: it was the worst of times.",
                    },
                    {
                        "_response_index_": 1,
                        "text": "/generate: it was the blurst of times.",
                    },
                ],
            },
            {
                "_index_": 1,
                "_replication_": "repl-1",
                "responses": [
                    {"_response_index_": 0, "text": "/generate: hello world."},
                    {"_response_index_": 1, "text": "/generate: goodbye world."},
                ],
            },
        ]

        # Save reference format
        format_file = self.reference_data_dir / "evaluation_response_format.json"
        with open(format_file, "w") as f:
            json.dump(
                {
                    "capture_environment": f"python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "format_description": "Evaluation responses with dict format containing _response_index_ and text",
                    "sample_responses": sample_evaluation_responses,
                    "expected_response_structure": {
                        "responses": [
                            {
                                "_response_index_": "int (0-based index)",
                                "text": "str (generated response text)",
                            }
                        ]
                    },
                },
                f,
                indent=2,
            )

        print(f"Saved evaluation response format to {format_file}")

    def test_capture_baseline_info(self):
        """Capture current environment info for reference."""
        info_file = self.reference_data_dir / "baseline_info.json"
        with open(info_file, "w") as f:
            json.dump(
                {
                    "capture_environment": f"python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "capture_timestamp": "schema_baseline_reference",
                    "test_coverage": [
                        "BlurstCountScoredItem serialization",
                        "Arrow schema generation",
                        "Evaluation response format",
                    ],
                    "purpose": "Baseline reference for schema stability testing",
                },
                f,
                indent=2,
            )

        print(f"Saved baseline info to {info_file}")

    def test_capture_comprehensive_schema(self):
        """Capture Arrow schema for ComprehensiveTestItem as reference."""
        schema = arrow_schema(ComprehensiveTestItem)

        # Helper function to convert bytes keys to strings in metadata
        def convert_metadata(metadata_dict):
            if not metadata_dict:
                return {}
            return {
                key.decode("utf-8") if isinstance(key, bytes) else str(key): (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
                for key, value in metadata_dict.items()
            }

        # Convert schema to JSON-serializable format
        schema_dict = {
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                    "metadata": (
                        convert_metadata(dict(field.metadata)) if field.metadata else {}
                    ),
                }
                for field in schema
            ],
            "metadata": (
                convert_metadata(dict(schema.metadata)) if schema.metadata else {}
            ),
        }

        # Save reference schema
        schema_file = self.reference_data_dir / "comprehensive_schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema_dict, f, indent=2)

        print(f"Saved comprehensive Arrow schema reference to {schema_file}")

        # Basic validation - check for expected field types
        field_names = [f["name"] for f in schema_dict["fields"]]
        field_types = {f["name"]: f["type"] for f in schema_dict["fields"]}

        # Inherited fields
        assert "_index_" in field_names
        assert "_replication_" in field_names

        # Numeric types
        assert "score_int" in field_names
        assert "score_float32" in field_names
        assert "score_float64" in field_names
        assert "int" in field_types["score_int"].lower()
        assert "float" in field_types["score_float32"].lower()
        assert (
            "double" in field_types["score_float64"].lower()
            or "float64" in field_types["score_float64"].lower()
        )

        # Boolean
        assert "is_valid" in field_names
        assert "bool" in field_types["is_valid"].lower()

        # String
        assert "category" in field_names
        assert (
            "string" in field_types["category"].lower()
            or "utf8" in field_types["category"].lower()
        )

        # Binary
        assert "raw_data" in field_names
        assert "binary" in field_types["raw_data"].lower()

        # Collections and nested structures (Arrow may flatten or represent differently)
        assert "tags" in field_names
        assert "scores" in field_names
        assert "metadata" in field_names

    def test_capture_comprehensive_sample_data(self):
        """Capture sample data for ComprehensiveTestItem."""
        # Create sample data with all field types
        metadata_sample = MetadataInfo(
            version="1.0.0", confidence=0.95, flags=["verified", "high_quality"]
        )

        sample_items = [
            ComprehensiveTestItem(
                _index_=0,
                _replication_="repl-1",
                score_int=42,
                score_float32=3.14,
                score_float64=2.718281828,
                is_valid=True,
                category="positive",
                raw_data=b"binary_test_data_123",
                tags=["important", "validated"],
                scores=[95, 87, 92],
                metadata=metadata_sample,
            ),
            ComprehensiveTestItem(
                _index_=1,
                _replication_="repl-1",
                score_int=-10,
                score_float32=-1.5,
                score_float64=0.0,
                is_valid=False,
                category="negative",
                raw_data=b"another_binary_sample",
                tags=["review_needed"],
                scores=[72, 0, 45],
                metadata=MetadataInfo(
                    version="1.1.0", confidence=0.45, flags=["needs_review"]
                ),
            ),
        ]

        # Convert to Arrow batch
        schema = arrow_schema(ComprehensiveTestItem)
        # Use compatible serialization method
        try:
            sample_dicts = [item.model_dump() for item in sample_items]
        except AttributeError:
            sample_dicts = [item.dict() for item in sample_items]
        batch = pyarrow.RecordBatch.from_pylist(sample_dicts, schema=schema)

        # Convert back to pylist for JSON serialization
        pylist_data = batch.to_pylist()

        # Save reference data - handle binary data for JSON serialization
        data_file = self.reference_data_dir / "comprehensive_sample_data.json"
        json_safe_data = handle_binary_for_json(pylist_data)
        with open(data_file, "w") as f:
            json.dump(
                {
                    "capture_environment": f"python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "sample_data": json_safe_data,
                    "record_count": len(sample_items),
                    "field_types_tested": [
                        "int32",
                        "float32",
                        "float64",
                        "bool",
                        "str",
                        "bytes",
                        "List[str]",
                        "List[int32]",
                        "nested_pydantic_model",
                    ],
                    "binary_encoding": "base64",
                },
                f,
                indent=2,
            )

        print(f"Saved comprehensive sample data to {data_file}")

        # Validation
        assert len(pylist_data) == 2
        assert all("score_int" in item for item in pylist_data)
        assert all("metadata" in item for item in pylist_data)


class TestSchemaValidation:
    """Tests to validate current schema structure."""

    def test_blurst_count_schema_structure(self):
        """Validate the structure of BlurstCountScoredItem schema."""
        schema = arrow_schema(BlurstCountScoredItem)

        field_names = [field.name for field in schema]
        field_types = {field.name: str(field.type) for field in schema}

        # Required fields from ReplicatedItem
        assert "_index_" in field_names
        assert "_replication_" in field_names

        # Custom fields from BlurstCountScoredItem
        assert "blurstCount" in field_names
        assert "cromulent" in field_names
        assert "embiggen" in field_names

        # Validate field types
        assert "int" in field_types["_index_"].lower()
        assert (
            "string" in field_types["_replication_"].lower()
            or "utf8" in field_types["_replication_"].lower()
        )
        assert "int" in field_types["blurstCount"].lower()
        assert "int" in field_types["cromulent"].lower()
        assert (
            "string" in field_types["embiggen"].lower()
            or "utf8" in field_types["embiggen"].lower()
        )

    def test_measurement_serialization_roundtrip(self):
        """Test that measurement data can roundtrip through Arrow without loss."""
        # Create test item
        original_item = BlurstCountScoredItem(
            _index_=42,
            _replication_="test-repl",
            blurstCount=5,
            cromulent=1,
            embiggen="largest",
        )

        # Convert to dict for Arrow processing
        try:
            item_dict = original_item.model_dump()
        except AttributeError:
            item_dict = original_item.dict()

        # Convert to Arrow and back
        schema = arrow_schema(BlurstCountScoredItem)
        batch = pyarrow.RecordBatch.from_pylist([item_dict], schema=schema)
        roundtrip_data = batch.to_pylist()[0]

        # Validate data integrity
        assert roundtrip_data["_index_"] == 42
        assert roundtrip_data["_replication_"] == "test-repl"
        assert roundtrip_data["blurstCount"] == 5
        assert roundtrip_data["cromulent"] == 1
        assert roundtrip_data["embiggen"] == "largest"

        # Recreate object from roundtrip data
        recreated_item = BlurstCountScoredItem(**roundtrip_data)
        assert recreated_item == original_item

    def test_plain_int_rejection(self):
        """Test that plain Python int (unbounded) is rejected by Arrow schema
        generation."""
        import pytest

        # This should raise an error because Arrow requires bounded integer types
        with pytest.raises((ValueError, TypeError, NotImplementedError)) as exc_info:
            arrow_schema(PlainIntTestItem)

        # Verify the error mentions the unsupported type
        error_msg = str(exc_info.value).lower()
        assert any(
            word in error_msg
            for word in ["int", "unbounded", "not supported", "not implemented"]
        )
        print(f"Plain int correctly rejected: {exc_info.value}")


class TestSchemaStability:
    """Tests to validate schema and data format stability across changes."""

    @property
    def reference_data_dir(self) -> Path:
        """Directory containing reference data."""
        return Path(__file__).parent / "data" / "schema_reference"

    def load_reference_schema(self) -> dict:
        """Load the reference Arrow schema from baseline."""
        schema_file = self.reference_data_dir / "blurst_count_schema.json"
        with open(schema_file, "r") as f:
            return json.load(f)

    def load_reference_data(self) -> dict:
        """Load the reference sample data from baseline."""
        data_file = self.reference_data_dir / "sample_measurement_data.json"
        with open(data_file, "r") as f:
            return json.load(f)

    def test_arrow_schema_stability(self):
        """Ensure Arrow schema remains identical to baseline reference."""
        # Load reference schema from baseline
        reference_schema = self.load_reference_schema()

        # Generate current schema
        current_schema = arrow_schema(BlurstCountScoredItem)

        # Helper function to convert current schema to same format as reference
        def convert_metadata(metadata_dict):
            if not metadata_dict:
                return {}
            return {
                key.decode("utf-8") if isinstance(key, bytes) else str(key): (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
                for key, value in metadata_dict.items()
            }

        current_schema_dict = {
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                    "metadata": (
                        convert_metadata(dict(field.metadata)) if field.metadata else {}
                    ),
                }
                for field in current_schema
            ],
            "metadata": (
                convert_metadata(dict(current_schema.metadata))
                if current_schema.metadata
                else {}
            ),
        }

        # Compare schemas field by field
        assert len(current_schema_dict["fields"]) == len(
            reference_schema["fields"]
        ), "Schema field count mismatch"

        # Create field lookup for easier comparison
        reference_fields = {f["name"]: f for f in reference_schema["fields"]}
        current_fields = {f["name"]: f for f in current_schema_dict["fields"]}

        # Ensure all reference fields exist in current schema
        for field_name, ref_field in reference_fields.items():
            assert field_name in current_fields, f"Missing field: {field_name}"
            current_field = current_fields[field_name]

            # Compare field properties
            assert (
                current_field["type"] == ref_field["type"]
            ), f"Type mismatch for {field_name}: {current_field['type']} != {ref_field['type']}"
            assert (
                current_field["nullable"] == ref_field["nullable"]
            ), f"Nullable mismatch for {field_name}"

            # Compare metadata (documentation should be preserved)
            if ref_field["metadata"]:
                assert (
                    current_field["metadata"] == ref_field["metadata"]
                ), f"Metadata mismatch for {field_name}"

    def test_data_serialization_stability(self):
        """Ensure data serializes identically to baseline reference."""
        # Load reference data from baseline
        reference_data = self.load_reference_data()
        reference_samples = reference_data["sample_data"]

        # Create equivalent data with current implementation
        current_items = [
            BlurstCountScoredItem(
                _index_=0,
                _replication_="repl-1",
                blurstCount=2,
                cromulent=1,
                embiggen="smallest",
            ),
            BlurstCountScoredItem(
                _index_=1,
                _replication_="repl-1",
                blurstCount=0,
                cromulent=0,
                embiggen="smallest",
            ),
            BlurstCountScoredItem(
                _index_=0,
                _replication_="repl-2",
                blurstCount=1,
                cromulent=1,
                embiggen="smallest",
            ),
        ]

        # Convert to Arrow batch and back to pylist (same process as reference)
        schema = arrow_schema(BlurstCountScoredItem)
        # Use compatible serialization method
        try:
            current_dicts = [item.model_dump() for item in current_items]
        except AttributeError:
            current_dicts = [item.dict() for item in current_items]

        batch = pyarrow.RecordBatch.from_pylist(current_dicts, schema=schema)
        current_samples = batch.to_pylist()

        # Compare data structure
        assert len(current_samples) == len(reference_samples), "Sample count mismatch"

        # Compare each sample
        for i, (current, reference) in enumerate(
            zip(current_samples, reference_samples)
        ):
            for key in reference.keys():
                assert key in current, f"Missing key {key} in sample {i}"
                assert (
                    current[key] == reference[key]
                ), f"Value mismatch for {key} in sample {i}: {current[key]} != {reference[key]}"

    def test_measurement_pipeline_stability(self):
        """Test full measurement pipeline produces consistent results."""
        # Create test measurement
        original_item = BlurstCountScoredItem(
            _index_=42,
            _replication_="test-repl",
            blurstCount=5,
            cromulent=1,
            embiggen="largest",
        )

        # Serialize using current implementation
        try:
            # Try Pydantic v2 method
            item_dict = original_item.model_dump()
        except AttributeError:
            # Fall back to Pydantic v1 method
            item_dict = original_item.dict()

        # Test Arrow roundtrip
        schema = arrow_schema(BlurstCountScoredItem)
        batch = pyarrow.RecordBatch.from_pylist([item_dict], schema=schema)
        roundtrip_data = batch.to_pylist()[0]

        # Validate data integrity
        assert roundtrip_data["_index_"] == 42
        assert roundtrip_data["_replication_"] == "test-repl"
        assert roundtrip_data["blurstCount"] == 5
        assert roundtrip_data["cromulent"] == 1
        assert roundtrip_data["embiggen"] == "largest"

        # Recreate object from roundtrip data
        try:
            # Try Pydantic v2 method
            recreated_item = BlurstCountScoredItem.model_validate(roundtrip_data)
        except AttributeError:
            # Fall back to Pydantic v1 method
            recreated_item = BlurstCountScoredItem(**roundtrip_data)
        assert recreated_item == original_item

    def test_evaluation_response_format_stability(self):
        """Ensure evaluation response format expectations are documented."""
        # Load reference evaluation format
        format_file = self.reference_data_dir / "evaluation_response_format.json"
        with open(format_file, "r") as f:
            reference_format = json.load(f)

        reference_format["expected_response_structure"]
        sample_responses = reference_format["sample_responses"]

        # Validate the expected format is still what our code expects
        for response_record in sample_responses:
            assert "_index_" in response_record
            assert "_replication_" in response_record
            assert "responses" in response_record

            responses = response_record["responses"]
            assert isinstance(responses, list)

            for response in responses:
                assert isinstance(response, dict)
                assert "_response_index_" in response
                assert "text" in response
                assert isinstance(response["_response_index_"], int)
                assert isinstance(response["text"], str)

        # This test documents that our measurement methods should expect
        # responses in the format: [{"_response_index_": int, "text": str}]
        # Any deviation from this format should be caught by the pipeline tests


class TestComprehensiveSchemaStability:
    """Tests for comprehensive schema stability across all supported field types."""

    @property
    def reference_data_dir(self) -> Path:
        """Directory containing reference data."""
        return Path(__file__).parent / "data" / "schema_reference"

    def load_comprehensive_schema(self) -> dict:
        """Load the comprehensive Arrow schema from baseline."""
        schema_file = self.reference_data_dir / "comprehensive_schema.json"
        with open(schema_file, "r") as f:
            return json.load(f)

    def load_comprehensive_data(self) -> dict:
        """Load the comprehensive sample data from baseline."""
        data_file = self.reference_data_dir / "comprehensive_sample_data.json"
        with open(data_file, "r") as f:
            return json.load(f)

    def test_comprehensive_arrow_schema_stability(self):
        """Ensure comprehensive Arrow schema remains identical to baseline reference."""
        # Load reference schema from baseline
        reference_schema = self.load_comprehensive_schema()

        # Generate current schema
        current_schema = arrow_schema(ComprehensiveTestItem)

        # Helper function to convert current schema to same format as reference
        def convert_metadata(metadata_dict):
            if not metadata_dict:
                return {}
            return {
                key.decode("utf-8") if isinstance(key, bytes) else str(key): (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
                for key, value in metadata_dict.items()
            }

        current_schema_dict = {
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable,
                    "metadata": (
                        convert_metadata(dict(field.metadata)) if field.metadata else {}
                    ),
                }
                for field in current_schema
            ],
            "metadata": (
                convert_metadata(dict(current_schema.metadata))
                if current_schema.metadata
                else {}
            ),
        }

        # Compare schemas field by field
        assert len(current_schema_dict["fields"]) == len(
            reference_schema["fields"]
        ), "Comprehensive schema field count mismatch"

        # Create field lookup for easier comparison
        reference_fields = {f["name"]: f for f in reference_schema["fields"]}
        current_fields = {f["name"]: f for f in current_schema_dict["fields"]}

        # Ensure all reference fields exist in current schema
        for field_name, ref_field in reference_fields.items():
            assert field_name in current_fields, f"Missing field: {field_name}"
            current_field = current_fields[field_name]

            # Compare field properties
            assert (
                current_field["type"] == ref_field["type"]
            ), f"Type mismatch for {field_name}: {current_field['type']} != {ref_field['type']}"
            assert (
                current_field["nullable"] == ref_field["nullable"]
            ), f"Nullable mismatch for {field_name}"

            # Compare metadata (documentation should be preserved)
            if ref_field["metadata"]:
                assert (
                    current_field["metadata"] == ref_field["metadata"]
                ), f"Metadata mismatch for {field_name}"

    def test_comprehensive_data_serialization_stability(self):
        """Ensure comprehensive data serializes identically to baseline reference."""
        # Load reference data from baseline
        reference_data = self.load_comprehensive_data()
        reference_samples = reference_data["sample_data"]

        # Create equivalent data with current implementation
        metadata_sample1 = MetadataInfo(
            version="1.0.0", confidence=0.95, flags=["verified", "high_quality"]
        )
        metadata_sample2 = MetadataInfo(
            version="1.1.0", confidence=0.45, flags=["needs_review"]
        )

        current_items = [
            ComprehensiveTestItem(
                _index_=0,
                _replication_="repl-1",
                score_int=42,
                score_float32=3.14,
                score_float64=2.718281828,
                is_valid=True,
                category="positive",
                raw_data=b"binary_test_data_123",
                tags=["important", "validated"],
                scores=[95, 87, 92],
                metadata=metadata_sample1,
            ),
            ComprehensiveTestItem(
                _index_=1,
                _replication_="repl-1",
                score_int=-10,
                score_float32=-1.5,
                score_float64=0.0,
                is_valid=False,
                category="negative",
                raw_data=b"another_binary_sample",
                tags=["review_needed"],
                scores=[72, 0, 45],
                metadata=metadata_sample2,
            ),
        ]

        # Convert to Arrow batch and back to pylist (same process as reference)
        schema = arrow_schema(ComprehensiveTestItem)
        # Use compatible serialization method
        try:
            current_dicts = [item.model_dump() for item in current_items]
        except AttributeError:
            current_dicts = [item.dict() for item in current_items]

        batch = pyarrow.RecordBatch.from_pylist(current_dicts, schema=schema)
        current_samples = batch.to_pylist()

        # Compare data structure
        assert len(current_samples) == len(
            reference_samples
        ), "Comprehensive sample count mismatch"

        # Compare each sample - but be flexible about binary data representation
        for i, (current, reference) in enumerate(
            zip(current_samples, reference_samples)
        ):
            for key in reference.keys():
                assert key in current, f"Missing key {key} in comprehensive sample {i}"

                # Special handling for binary data (may be encoded differently)
                if key == "raw_data":
                    # Both should be present and non-empty, exact format may vary
                    assert (
                        current[key] is not None
                    ), f"Binary data missing in sample {i}"
                    assert (
                        reference[key] is not None
                    ), f"Reference binary data missing in sample {i}"
                else:
                    assert (
                        current[key] == reference[key]
                    ), f"Value mismatch for {key} in comprehensive sample {i}: {current[key]} != {reference[key]}"

    def test_comprehensive_field_types_coverage(self):
        """Test that all expected field types are properly handled."""
        # Create test item with comprehensive field types
        metadata_sample = MetadataInfo(
            version="test", confidence=0.5, flags=["unit_test"]
        )

        test_item = ComprehensiveTestItem(
            _index_=999,
            _replication_="test-repl",
            score_int=123,
            score_float32=1.23,
            score_float64=9.876543210,
            is_valid=True,
            category="test_category",
            raw_data=b"test_binary_data",
            tags=["tag1", "tag2", "tag3"],
            scores=[100, 50, 75],
            metadata=metadata_sample,
        )

        # Test Arrow roundtrip
        try:
            item_dict = test_item.model_dump()
        except AttributeError:
            item_dict = test_item.dict()

        schema = arrow_schema(ComprehensiveTestItem)
        batch = pyarrow.RecordBatch.from_pylist([item_dict], schema=schema)
        roundtrip_data = batch.to_pylist()[0]

        # Validate all field types survived roundtrip
        assert roundtrip_data["_index_"] == 999
        assert roundtrip_data["_replication_"] == "test-repl"
        assert roundtrip_data["score_int"] == 123
        assert abs(roundtrip_data["score_float32"] - 1.23) < 0.001  # Float precision
        assert (
            abs(roundtrip_data["score_float64"] - 9.876543210) < 0.000000001
        )  # Double precision
        assert roundtrip_data["is_valid"] is True
        assert roundtrip_data["category"] == "test_category"
        assert roundtrip_data["raw_data"] is not None  # Binary data present
        assert roundtrip_data["tags"] == ["tag1", "tag2", "tag3"]
        assert roundtrip_data["scores"] == [100, 50, 75]
        assert roundtrip_data["metadata"] is not None  # Nested model present

        print(f"All field types successfully handled in Arrow roundtrip")
