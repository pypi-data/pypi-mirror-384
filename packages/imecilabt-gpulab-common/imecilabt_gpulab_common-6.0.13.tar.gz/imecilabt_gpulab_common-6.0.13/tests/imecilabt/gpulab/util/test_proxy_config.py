from pathlib import Path

from imecilabt.gpulab.util.proxy_config import ProxyConfig
from imecilabt_utils.urn_util import URN


def test_proxy_config1() -> None:
    yml_in = """proxy_username_prefix:
   wall2.ilabt.iminds.be: ''
   ilabt.imec.be: 'fff'
"""

    proxy_config = ProxyConfig.load_from_ymlstr(yml_in)

    assert proxy_config.find_proxy_username("urn:publicid:IDN+wall2.ilabt.iminds.be+user+ftester") == "ftester"
    assert proxy_config.find_proxy_username("urn:publicid:IDN+ilabt.imec.be+user+ftester") == "fffftester"
    assert proxy_config.find_proxy_username("urn:publicid:IDN+example.com+user+ftester") is None


def test_proxy_config2() -> None:
    yml_in = """proxy_username_prefix:
   wall2.ilabt.iminds.be: ''
   ilabt.imec.be: 'blah-'
"""

    proxy_config = ProxyConfig.load_from_ymlstr(yml_in)

    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+wall2.ilabt.iminds.be+user+blih")) == "blih"
    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+ilabt.imec.be+user+blih")) == "blah-blih"
    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+example.com+user+blih")) is None


def test_proxy_save_load_dict() -> None:
    yml_in = """proxy_username_prefix:
   wall2.ilabt.iminds.be: ''
   ilabt.imec.be: 'blah-'
"""

    proxy_config = ProxyConfig.load_from_ymlstr(yml_in)

    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+wall2.ilabt.iminds.be+user+blih")) == "blih"
    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+ilabt.imec.be+user+blih")) == "blah-blih"
    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+example.com+user+blih")) is None

    tmp_proxy_dict = proxy_config.model_dump()
    proxy_config2 = ProxyConfig.model_validate(tmp_proxy_dict)

    assert proxy_config2.find_proxy_username(URN(urn="urn:publicid:IDN+wall2.ilabt.iminds.be+user+blih")) == "blih"
    assert proxy_config2.find_proxy_username(URN(urn="urn:publicid:IDN+ilabt.imec.be+user+blih")) == "blah-blih"
    assert proxy_config2.find_proxy_username(URN(urn="urn:publicid:IDN+example.com+user+blih")) is None


def test_proxy_save_load_file(tmp_path: Path) -> None:
    yml_in = """proxy_username_prefix:
   wall2.ilabt.iminds.be: ''
   ilabt.imec.be: 'blah-'
"""

    proxy_config = ProxyConfig.load_from_ymlstr(yml_in)

    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+wall2.ilabt.iminds.be+user+blih")) == "blih"
    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+ilabt.imec.be+user+blih")) == "blah-blih"
    assert proxy_config.find_proxy_username(URN(urn="urn:publicid:IDN+example.com+user+blih")) is None

    tmp_proxy_cfg_file = tmp_path / "tmp_proxy_cfg_file.yaml"
    proxy_config.save_to_file(str(tmp_proxy_cfg_file))
    proxy_config2 = ProxyConfig.load_from_file(str(tmp_proxy_cfg_file))

    assert proxy_config2.find_proxy_username(URN(urn="urn:publicid:IDN+wall2.ilabt.iminds.be+user+blih")) == "blih"
    assert proxy_config2.find_proxy_username(URN(urn="urn:publicid:IDN+ilabt.imec.be+user+blih")) == "blah-blih"
    assert proxy_config2.find_proxy_username(URN(urn="urn:publicid:IDN+example.com+user+blih")) is None
