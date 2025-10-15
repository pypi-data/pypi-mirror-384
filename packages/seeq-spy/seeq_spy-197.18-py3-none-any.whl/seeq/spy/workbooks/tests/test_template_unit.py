import pytest

from seeq import spy
from seeq.spy.workbooks._item import replace_items


@pytest.mark.unit
def test_replace_items_sorts_item_map():
    # Tests the fix for CRAB-52212
    def create_document(_id):
        return f'<img src="/api/annotations/{_id}/images/test.png" />'

    annotation_id = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"
    annotation_id_with_label = f"{annotation_id} label"
    replacement_id = "11111111-1111-1111-1111-111111111111"
    document = create_document(annotation_id_with_label)
    item_map = spy.workbooks.ItemMap({
        annotation_id: replacement_id,
        annotation_id_with_label: replacement_id
    })
    updated_document = replace_items(document, item_map)
    expected_document = create_document(replacement_id)
    assert updated_document == expected_document
