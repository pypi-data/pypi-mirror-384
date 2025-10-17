import os
import tempfile
from doc_utils.unused_attributes import parse_attributes_file, find_adoc_files, scan_for_attribute_usage, find_unused_attributes, comment_out_unused_attributes

def make_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def test_parse_attributes_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":foo: bar\n:bar: baz\n:unused: 123\n")
        attrs = parse_attributes_file(attr_path)
        assert 'foo' in attrs
        assert 'bar' in attrs
        assert 'unused' in attrs

def test_find_adoc_files_and_usage():
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":foo: bar\n:bar: baz\n:unused: 123\n")
        adoc1 = os.path.join(tmpdir, 'a.adoc')
        adoc2 = os.path.join(tmpdir, 'b.adoc')
        make_file(adoc1, "This uses {foo} and {bar}.")
        make_file(adoc2, "No attributes here.")
        adoc_files = find_adoc_files(tmpdir)
        attrs = parse_attributes_file(attr_path)
        used = scan_for_attribute_usage(adoc_files, attrs)
        assert 'foo' in used
        assert 'bar' in used
        assert 'unused' not in used

def test_find_unused_attributes():
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":foo: bar\n:bar: baz\n:unused: 123\n")
        adoc1 = os.path.join(tmpdir, 'a.adoc')
        adoc2 = os.path.join(tmpdir, 'b.adoc')
        make_file(adoc1, "This uses {foo} and {bar}.")
        make_file(adoc2, "No attributes here.")
        unused = find_unused_attributes(attr_path, tmpdir)
        assert 'unused' in unused
        assert 'foo' not in unused
        assert 'bar' not in unused

def test_conditional_directives_ifdef():
    """Test that ifdef::attribute:: is recognized as usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":rh-only:\n:downstream:\n:unused:\n")
        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, "ifdef::rh-only[]\nSome content\nendif::rh-only[]\n")
        attrs = parse_attributes_file(attr_path)
        adoc_files = find_adoc_files(tmpdir)
        used = scan_for_attribute_usage(adoc_files, attrs)
        assert 'rh-only' in used
        assert 'downstream' not in used
        assert 'unused' not in used

def test_conditional_directives_ifndef():
    """Test that ifndef::attribute:: is recognized as usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":no-feature:\n:unused:\n")
        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, "ifndef::no-feature[]\nContent when feature exists\nendif::no-feature[]\n")
        attrs = parse_attributes_file(attr_path)
        adoc_files = find_adoc_files(tmpdir)
        used = scan_for_attribute_usage(adoc_files, attrs)
        assert 'no-feature' in used
        assert 'unused' not in used

def test_conditional_directives_endif():
    """Test that endif::attribute:: is recognized as usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":my-attr:\n:unused:\n")
        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, "ifdef::my-attr[]\nSome content\nendif::my-attr[]\n")
        attrs = parse_attributes_file(attr_path)
        adoc_files = find_adoc_files(tmpdir)
        used = scan_for_attribute_usage(adoc_files, attrs)
        assert 'my-attr' in used
        assert 'unused' not in used

def test_mixed_usage_patterns():
    """Test attributes used in both {attr} and ifdef::attr:: forms."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":version: 1.0\n:rh-only:\n:unused:\n")
        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, "Version {version}\nifdef::rh-only[]\nRH content\nendif::rh-only[]\n")
        unused = find_unused_attributes(attr_path, tmpdir)
        assert 'unused' in unused
        assert 'version' not in unused
        assert 'rh-only' not in unused

def test_no_prefix_attributes():
    """Test attributes with 'no-' prefix used in ifndef directives."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        make_file(attr_path, ":no-quarkus-security-jpa-reactive:\n:no-webauthn-authentication:\n:unused:\n")
        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, """
ifndef::no-quarkus-security-jpa-reactive[]
Content about JPA reactive security
endif::no-quarkus-security-jpa-reactive[]

ifndef::no-webauthn-authentication[]
Content about WebAuthn
endif::no-webauthn-authentication[]
""")
        unused = find_unused_attributes(attr_path, tmpdir)
        assert 'unused' in unused
        assert 'no-quarkus-security-jpa-reactive' not in unused
        assert 'no-webauthn-authentication' not in unused

def test_comment_out_unused_attributes():
    """Test commenting out unused attributes in the attributes file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        original_content = """:version: 1.0
:product: MyApp
:unused1: value1
:unused2: value2
:rh-only:
"""
        make_file(attr_path, original_content)

        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, "Version {version} Product {product}\nifdef::rh-only[]\nContent\nendif::rh-only[]\n")

        # Find unused attributes
        unused = find_unused_attributes(attr_path, tmpdir)
        assert 'unused1' in unused
        assert 'unused2' in unused
        assert 'version' not in unused
        assert 'product' not in unused
        assert 'rh-only' not in unused

        # Comment out unused attributes
        count = comment_out_unused_attributes(attr_path, unused)
        assert count == 2

        # Verify the file was modified correctly
        with open(attr_path, 'r') as f:
            content = f.read()

        assert '// Unused :unused1: value1\n' in content
        assert '// Unused :unused2: value2\n' in content
        assert ':version: 1.0\n' in content
        assert ':product: MyApp\n' in content
        assert ':rh-only:\n' in content

def test_comment_out_empty_list():
    """Test that comment_out_unused_attributes handles empty list correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        original_content = ":version: 1.0\n:product: MyApp\n"
        make_file(attr_path, original_content)

        # Comment out with empty list
        count = comment_out_unused_attributes(attr_path, [])
        assert count == 0

        # Verify file was not modified
        with open(attr_path, 'r') as f:
            content = f.read()

        assert content == original_content

def test_comment_out_preserves_formatting():
    """Test that commenting out preserves line formatting and comments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        attr_path = os.path.join(tmpdir, 'attributes.adoc')
        original_content = """// This is a comment
:version: 1.0

:unused: value with spaces
// Another comment
:product: MyApp
"""
        make_file(attr_path, original_content)

        adoc1 = os.path.join(tmpdir, 'test.adoc')
        make_file(adoc1, "Version {version} Product {product}\n")

        unused = find_unused_attributes(attr_path, tmpdir)
        count = comment_out_unused_attributes(attr_path, unused)
        assert count == 1

        with open(attr_path, 'r') as f:
            content = f.read()

        assert '// This is a comment\n' in content
        assert '// Unused :unused: value with spaces\n' in content
        assert '// Another comment\n' in content
        assert ':version: 1.0\n' in content
        assert ':product: MyApp\n' in content
