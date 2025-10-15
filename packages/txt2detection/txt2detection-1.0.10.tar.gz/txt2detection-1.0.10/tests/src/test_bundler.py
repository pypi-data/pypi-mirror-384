import pytest
import uuid
from unittest.mock import MagicMock, patch

import stix2
from txt2detection.bundler import Bundler
from txt2detection.models import DetectionContainer, SigmaRuleDetection
from datetime import datetime, timezone
from stix2 import Relationship

from txt2detection.utils import remove_rule_specific_tags


@pytest.fixture
def dummy_detection():
    detection = SigmaRuleDetection(
        title="Test Detection",
        description="Detects something suspicious.",
        detection=dict(condition="selection1", selection1=dict(ip="1.1.1.1")),
        tags=["tlp.red", "sigma.execution"],
        id="cd7ff0b1-fbf3-4c2d-ba70-5d127eb8b4be",
        external_references=[],
        logsource=dict(
            category="network-connection",
            product="firewall",
        ),
    )
    return detection




def test_bundler_initialization(bundler_instance):
    assert bundler_instance.report.name == "Test Report"
    assert bundler_instance.report.description == "This is a test report."
    assert bundler_instance.bundle is not None
    assert bundler_instance.report.object_marking_refs
    assert bundler_instance.report.labels == remove_rule_specific_tags(
        bundler_instance.labels
    )


def test_report_reference_urls():
    ref_urls = ["https://example.com/"]
    bundler = Bundler(
        name="Test Report",
        identity=None,
        tlp_level="red",
        description="This is a test report.",
        labels=["tlp.red", "test.test-var"],
        reference_urls=ref_urls,
    )
    assert set(ref_urls).issubset(
        {
            ref.get("url")
            for ref in bundler.report.external_references
            if ref["source_name"] == "txt2detection"
        }
    )


def test_report_hash():
    bundler = Bundler(
        name="Test Report",
        identity=None,
        tlp_level="red",
        description="This is a test report.",
        labels=["tlp.red", "test.test-var"],
        reference_urls=["https://example.com/"],
    )
    assert (
        stix2.ExternalReference(
            source_name="description_md5_hash",
            external_id="073c6065350473091a406bd7ba593e72",
        )
        in bundler.report.external_references
    )


@patch("txt2detection.bundler.observables.find_stix_observables", return_value=[])
@patch("txt2detection.bundler.Bundler.get_attack_objects", return_value=[])
@patch("txt2detection.bundler.Bundler.get_cve_objects", return_value=[])
@patch.object(SigmaRuleDetection, "make_rule", return_value="some rule")
@pytest.mark.parametrize("description", ["some description", None])
def test_add_rule_indicator_basic(
    mock_make_rule,
    mock_cve,
    mock_attack,
    mock_observables,
    dummy_detection,
    bundler_instance,
    description,
):
    bundler_instance.add_rule_indicator(dummy_detection)
    dummy_detection.description = description

    # Indicator should now be in the bundle
    indicators = [
        obj for obj in bundler_instance.bundle.objects if obj.get("type") == "indicator"
    ]
    assert len(indicators) == 1
    mock_cve.assert_called_once_with(dummy_detection.cve_ids)
    mock_attack.assert_called_once_with(dummy_detection.mitre_attack_ids)
    mock_observables.assert_called_once_with(dummy_detection.detection)
    mock_make_rule.assert_called_once_with(bundler_instance)
    indicator = indicators[0]
    assert dummy_detection.title == indicator["name"]
    assert indicator["pattern"] == mock_make_rule.return_value
    if description:
        assert "rule_md5_hash" in [
            ref["source_name"] for ref in indicator["external_references"]
        ], "rule_md5_hash should be present when description is non-null"
    else:
        assert "rule_md5_hash" in [
            ref["source_name"] for ref in indicator["external_references"]
        ], "rule_md5_hash should not be present when description is None"


def test_generate_report_id_deterministic():
    created = datetime(2023, 1, 1, tzinfo=timezone.utc).isoformat()
    id1 = Bundler.generate_report_id("identity--1234", created, "test")
    id2 = Bundler.generate_report_id("identity--1234", created, "test")
    assert id1 == id2


def test_bundle_dict_and_json(bundler_instance):
    # Ensure JSON and dict methods work without error
    json_data = bundler_instance.to_json()
    assert '"type": "bundle"' in json_data

    dict_data = bundler_instance.bundle_dict
    assert dict_data["type"] == "bundle"
    assert "objects" in dict_data


@patch("txt2detection.bundler.requests.get")
def test_get_objects_pagination(mock_get, bundler_instance):
    # Simulate paginated API
    mock_get.side_effect = [
        MagicMock(
            status_code=200,
            json=lambda: {
                "objects": [{"id": "x"}],
                "page_results_count": 1,
                "page_size": 1000,
            },
        ),
        MagicMock(
            status_code=200,
            json=lambda: {"objects": [], "page_results_count": 0, "page_size": 1000},
        ),
    ]

    result = bundler_instance._get_objects("http://example.com", headers={})
    assert result == [{"id": "x"}]


def test_add_ref_deduplication(bundler_instance):
    sdo = {"id": "indicator--1234", "type": "indicator"}
    bundler_instance.add_ref(sdo)
    bundler_instance.add_ref(sdo)  # Should be ignored second time

    objs = [obj for obj in bundler_instance.bundle.objects if isinstance(obj, dict)]
    assert objs.count(sdo) == 1


def test_add_relation_creates_relationship(bundler_instance: Bundler):
    id = str(uuid.uuid4())
    indicator = {
        "id": "indicator--" + id,
        "name": "Test Indicator",
        "external_references": [],
    }
    target = {
        "id": "attack-pattern--" + id,
        "name": "Execution",
        "external_references": [
            {"external_id": "T1059", "source_name": "mitre-attack"}
        ],
    }

    bundler_instance.add_relation(indicator, target)
    relationships = [
        o for o in bundler_instance.bundle.objects if isinstance(o, Relationship)
    ]
    assert any(r.source_ref == indicator["id"] for r in relationships)
    # make sure the ref is added in indicator.external_references
    assert target["external_references"][0] in indicator["external_references"]


def test_bundler_generates_valid_bundle(dummy_detection):
    bundler = Bundler(
        name="Test Report",
        identity=None,
        tlp_level="red",
        description="Simple test bundle",
        labels=["tlp.red"],
    )
    bundler.add_rule_indicator(dummy_detection)

    bundle = bundler.bundle_dict
    object_types = {obj["type"]: obj for obj in bundle["objects"]}

    # Basic assertions
    assert bundle["type"] == "bundle"
    assert "report" in object_types
    assert "indicator" in object_types

    # Check report correctness
    report = object_types["report"]
    assert report["name"] == "Test Report"
    assert "object_marking_refs" in report
    assert report["description"] == "Simple test bundle"

    # Check indicator correctness
    indicator = object_types["indicator"]
    assert indicator["pattern_type"] == "sigma"
    assert dummy_detection.title in indicator["name"]


def test_bundle_detections(dummy_detection, bundler_instance):
    container = DetectionContainer(success=False, detections=[])
    with patch.object(Bundler, "add_rule_indicator") as mock_add_rule_indicator:
        bundler_instance.bundle_detections(container)
        mock_add_rule_indicator.assert_not_called()
        mock_add_rule_indicator.reset_mock()
        detection = MagicMock()
        container.detections.append(detection)
        container.success = True
        bundler_instance.bundle_detections(container)
        mock_add_rule_indicator.assert_called_once_with(detection)


def test_bundle_detections__creates_log_source(dummy_detection, bundler_instance):
    dummy_detection.detection_id = "d73e1632-c541-4b09-8281-95dc7f9c5782"
    bundler_instance.add_rule_indicator(dummy_detection)
    objects = [
        obj
        for obj in bundler_instance.bundle_dict["objects"]
        if obj["id"]
        in (
            "data-source--f078a18f-0f04-5fde-b6cd-a5af90b6346b",
            "relationship--fe0a3715-6a21-5472-840f-39ea9c61ee83",
        )
    ]
    assert objects == [
        {
            "type": "data-source",
            "spec_version": "2.1",
            "id": "data-source--f078a18f-0f04-5fde-b6cd-a5af90b6346b",
            "category": "network-connection",
            "product": "firewall",
            "extensions": {
                "extension-definition--afeeb724-bce2-575e-af3d-d705842ea84b": {
                    "extension_type": "new-sco"
                }
            },
        },
        {
            "type": "relationship",
            "spec_version": "2.1",
            "id": "relationship--fe0a3715-6a21-5472-840f-39ea9c61ee83",
            "created_by_ref": "identity--a4d70b75-6f4a-5d19-9137-da863edd33d7",
            "created": "2025-01-01T00:00:00.000Z",
            "modified": "2025-01-01T00:00:00.000Z",
            "relationship_type": "related-to",
            "description": "Test Detection is created from log-source {category=network-connection, product=firewall}",
            "source_ref": "indicator--d73e1632-c541-4b09-8281-95dc7f9c5782",
            "target_ref": "data-source--f078a18f-0f04-5fde-b6cd-a5af90b6346b",
            "object_marking_refs": [
                "marking-definition--e828b379-4e03-4974-9ac4-e53a884c97c1",
                "marking-definition--a4d70b75-6f4a-5d19-9137-da863edd33d7",
            ],
        },
    ]

def test_get_attack_objects(bundler_instance):
    retval = bundler_instance.get_attack_objects(['T1190', 'T1547'])
    print({r['id'] for r in retval})
    assert {r['id'] for r in retval} == {'attack-pattern--1ecb2399-e8ba-4f6b-8ba7-5c27d49405cf', 'attack-pattern--3f886f2a-874f-4333-b794-aa6075009b1c'}

def test_get_cve_objects(bundler_instance):
    cves = ['CVE-2025-1234', 'CVE-2024-1234']
    retval = bundler_instance.get_cve_objects(cves)
    assert {r['name'] for r in retval} == set(cves)


def test_flow_objects__adds_extension_definition(bundler_instance):
    bundler_instance.flow_objects = [{'id': 'some-other', 'type': ''}]
    assert bundler_instance.all_objects.issuperset({'some-other', "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4"})
    assert "extension-definition--fb9c968a-745b-4ade-9b25-c324172197f4" not in bundler_instance.report.object_refs