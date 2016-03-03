from jenskipper import utils


def assert_xml_strings_equal(xml_text_1, xml_text_2):
    xml_text_1 = utils.format_xml(xml_text_1)
    xml_text_2 = utils.format_xml(xml_text_2)
    assert xml_text_1 == xml_text_2
