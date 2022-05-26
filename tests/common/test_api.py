import json
from unittest.mock import patch, Mock

from galaxy.api.errors import BackendError
from galaxy.unittest.mock import async_raise, async_return_value
import pytest

from webservice import AuthorizedHumbleAPI


@pytest.fixture
def client_session():
    with patch("aiohttp.ClientSession", autospec=True) as mock:
        yield mock.return_value


@pytest.fixture
def api():
    return AuthorizedHumbleAPI(headers={})


def test_filename_from_web_link(api):
    web_link = 'https://dl.humble.com/Almost_There_Windows.zip?gamekey=AbR9TcsD4ecueNGw&ttl=1587335864&t=a04a9b4f6512b7958f6357cb7b628452'
    expected = 'Almost_There_Windows.zip'
    assert expected == api._filename_from_web_link(web_link)


@pytest.mark.asyncio
async def test_handle_exception(client_session, api):
    client_session.request.return_value = async_raise(BackendError)
    with pytest.raises(BackendError):
        await api._get_webpack_data("mock_path", "mock_webpack_id")


@pytest.mark.asyncio
async def test_get_user_subscription_state(client_session, api):
    subscription_state_raw = '{"newestOwnedTier": "basic", "nextBilledPlan": "monthly_v2_basic", "consecutiveContentDropCount": 12, "canResubscribe": false, "currentlySkippingContentHumanName": null, "perksStatus": "active", "billDate": "2021-11-30T18:00:00", "monthlyNewestOwnedContentMachineName": "october_2021_choice", "willReceiveFutureMonths": true, "monthlyOwnsActiveContent": false, "unpauseDt": "2021-12-07T18:00:00", "creditsRemaining": 0, "currentlySkippingContentMachineName": null, "canBeConvertedFromGiftSubToPayingSub": false, "lastSkippedContentMachineName": "january_2021_choice", "contentEndDateAfterBillDate": "2021-12-07T18:00:00", "isPaused": false, "monthlyNewestOwnedContentGamekey": "xVr5VcHnrd4KFATZ", "failedBillingMonths": 0, "monthlyNewestSkippedContentEnd": "2021-02-05T18:00:00", "wasPaused": false, "monthlyPurchasedAnyContent": true, "monthlyNewestOwnedContentEnd": "2021-11-02T17:00:00", "monthlyOwnsAnyContent": true}'
    shorten_page_source = R"""
<!doctype html>
<html lang="en" class="">
  <head>
    <title>
  Humble Choice Subscription Management | Humble Bundle</title>
    <script>
      window.humble = window.humble || {};
      window.humble.locale = "en";
      window.humble.ie11ScriptsToLoad = [
        "https://humblebundle-a.akamaihd.net/static/hashed/c5b3c44cb77ebe3f6a35879673a9eaf7dee99d90.js",
      ];
    </script>
    <script id="main-js" data-dist_version="c9ed87a47d080e3663d596d7acf24ed2c605d66f" src="https://humblebundle-a.akamaihd.net/c9ed87a47d080e3663d596d7acf24ed2c605d66f/dist/main.min.js"></script>
  <meta name="application-name" content="Humble Bundle">

<link rel="apple-touch-icon" sizes="144x144" href="https://humblebundle-a.akamaihd.net/static/hashed/03df0490a53d595fd930f9fff52038366d60a05d.png">
<link rel='alternate' type='application/rss+xml' title='Humble Mumble' href='http://blog.humblebundle.com/rss' />

<style>
body {
  font-family: 'Sofia Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 14px;
  padding: 0;
}
</style>
<link rel="stylesheet" href="https://humblebundle-a.akamaihd.net/static/hashed/673e36717b185e40205fe87f064db1aa400af09e.css" />

<script>
  window.models = window.models || {};

window.models.user_json = {
  "maxRewardAmount": 10,
  "needs_to_opt_in": false,
  "wishlist": [
    "babaisyou_storefront"
  ],
  "has_epic_account_id": false,
  "gog_account_id": null,
  "battlenet_tag": null,
  "remind_me_products": [],
  "has_steam_link": true,
  "has_battlenet_link": false,
  "has_admin_access": false,
  "hasSharedDiscount": null,
  "rewardsDiscountAmount": 10,
  "origin_username": null,
  "selectedCountry": "DE",
  "selectedLatitude": "00.129676",
  "selectedCity": "warsaw",
  "created": "2019-07-16T15:00:00.000000",
  "rewardsCharityAmount": 0,
  "logout_url": "/logout?goto=/",
  "selectedLongitude": "00.012229",
  "rewardsWalletAmount": 0,
  "is_logged_in": true,
  "gog_username": null,
  "origin_is_linked": false,
  "email": "redacted@redacted.com",
  "selectedRegion": "redacted"
};

window.models.userSubscriptionState = %s;
window.models.request = {
  country_code: "DE",
  captcha_enabled: true,
  vat_rate: 0.20,
  is_mobile: false,
  isAndroidApp: false
};
</script>

<script>
// dimension5 = 'Logged State' to differentiate logged in vs. logged out users
ga('set', 'dimension5', 'Logged In');
// TODO: Clean this up in ENG-22003
if (window.models.userSubscriptionState.perksStatus === 'active') {
  // dimension6 = 'Subscriber State' to differentiate subscribed users vs. not
  ga('set', 'dimension6', 'Subscribed');
} else {
  ga('set', 'dimension6', 'Not Subscribed');
}
</script>

<script>
(function() {
  // Load the heap library JS
  window.heap = window.heap || [], heap.load = function (e, t) {window.heap.appid = e, window.heap.config = t = t || {};var r = document.createElement("script");r.type = "text/javascript", r.async = !0, r.src = "https://cdn.heapanalytics.com/js/heap-" + e + ".js";var a = document.getElementsByTagName("script")[0];a.parentNode.insertBefore(r, a);for (var n = function (e) {return function () {heap.push([e].concat(Array.prototype.slice.call(arguments, 0)))}}, p = ["addEventProperties", "addUserProperties", "clearEventProperties", "identify", "resetIdentity", "removeEventProperty", "setEventProperties", "track", "unsetEventProperty"], o = 0; o < p.length; o++) heap[p[o]] = n(p[o])};
  // Initialize the heap object with our heap app ID
  heap.load('2199522758', {
    rewrite: (props) => {
      // We need to remove PII like emails and gamekeys from the `query` property
      let pageviewQuery = props.pageview_properties.query;
      let sessionQuery = props.session_properties.query;

      // Redact any email query param
      const emailRegex = /email=(.+?[^\?|&|#]+)/g;
      if (pageviewQuery) {
        pageviewQuery = pageviewQuery.replace(emailRegex, 'email=redacted');
      }
      if (sessionQuery) {
        sessionQuery = sessionQuery.replace(emailRegex, 'email=redacted');
      }
      // Redact gamekeys
      const pathsWithGamekeyQuery = ['/downloads', '/gift'];
      const gamekeyRegex = /(key|gift)=([^\&]+)/g;
      if (pathsWithGamekeyQuery.indexOf(props.session_properties.path) > -1 || pathsWithGamekeyQuery.indexOf(props.pageview_properties.path) > -1) {
        if (pageviewQuery) {
          pageviewQuery = pageviewQuery.replace(gamekeyRegex, '$1=redacted');
        }
        if (sessionQuery) {
          sessionQuery = sessionQuery.replace(gamekeyRegex, '$1=redacted');
        }
      }
      if (props.event_properties.href && (props.event_properties.href.indexOf('/downloads') > -1 || props.event_properties.href.indexOf('/gift') > -1)) {
        props.event_properties.href = props.event_properties.href.replace(gamekeyRegex, '$1=redacted');
      }
      // Finally we can set the cleaned query strings onto `props`
      if (pageviewQuery) {
        props.pageview_properties.query = pageviewQuery;
      }
      if (sessionQuery) {
        props.session_properties.query = sessionQuery;
      }
      return props;
    },
  });
  var userJson = window.models.user_json;
  var subscriptionJson = window.models.userSubscriptionState;
  var userProperties = $.extend({}, subscriptionJson);
  // Gamekeys are unique per-user, so for privacy, we strip it out.
  delete userProperties['monthlyNewestOwnedContentGamekey'];
  userProperties.userCountry = userJson.selectedCountry || window.models.request.country_code;
  userProperties.locale = 'en';
  var userID = 'ahFzfmhyLWh1bWJsZWJ1bmRsZXIRCxIEVXNlchiAgPipmq7TCgw';
  if (userID) {
    heap.identify(userID);
  }
  heap.addUserProperties(userProperties);
  var eventProperties = {
    'logged_in': userJson.is_logged_in,
    'subscription_perks_status': subscriptionJson.perksStatus,
    'pause_state': subscriptionJson.isPaused,
    'owns_active_content': subscriptionJson.monthlyOwnsActiveContent,
  };
  heap.addEventProperties(eventProperties);
})();
</script>

<script type="application/ld+json">
  {
    "@context": "http://schema.org",
    "@type": "WebSite",
    "url": "https://www.humblebundle.com/",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://www.humblebundle.com/store/search?search={search_term}",
      "query-input": "required name=search_term"
    }
  }
</script>
  
<link rel="alternate" hreflang="x-default" href="https://www.humblebundle.com/subscription/home" />
</head>

<body>
  <div class="page-wrap">
    <div id="page-top-messages"></div>
    <div class="js-navigation-tracker"></div>  
    <p> dummy</p>
  </div>
</body>
</html>
""" % subscription_state_raw

    response_mock = Mock(spec=())
    response_mock.text = Mock(return_value=async_return_value(shorten_page_source))
    client_session.request.return_value = async_return_value(response_mock)

    result = await api.get_user_subscription_state()

    assert result == json.loads(subscription_state_raw)


@pytest.mark.parametrize('gamekeys, expected_url', [
    pytest.param(
        ["FIRST"],
        "https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys=FIRST",
        id="one gamekey"
    ),
    pytest.param(
        ["FIRST", "SECOND"],
        "https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys=FIRST&gamekeys=SECOND",
        id="two gamekeys"
    )
])
@pytest.mark.asyncio
async def test_get_orders_bulk_details(api, aioresponse, gamekeys, expected_url):
    stubbed_response = {"dummy": "json"}
    aioresponse.get(expected_url, payload=stubbed_response)

    result = await api.get_orders_bulk_details(gamekeys)

    assert result == stubbed_response
