from webservice import AuthorizedHumbleAPI


def test_filename_from_web_link():
    web_link = 'https://dl.humble.com/Almost_There_Windows.zip?gamekey=AbR9TcsD4ecueNGw&ttl=1587335864&t=a04a9b4f6512b7958f6357cb7b628452'
    expected = 'Almost_There_Windows.zip'
    assert expected == AuthorizedHumbleAPI._filename_from_web_link(web_link)
