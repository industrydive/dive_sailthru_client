from sailthru.sailthru_client import SailthruClient
from errors import SailthruApiError
import datetime

# TODO: enforce structure on returned dicts -- make all keys present even if
# value is zero. Maybe replace with class.


class DiveEmailTypes:
    """
    Provides standard email types we use.
    """
    Blast = "blast"
    WelcomeSeries = "welcome"
    Newsletter = "newsletter"
    Weekender = "weekender"
    Unknown = "unknown"
    BreakingNews = "breaking"


class DiveSailthruClient(object):
    """
    Our Sailthru client implementation that adds our own concepts.

    This includes dive brand, dive email type, and easier ways to query
    campaigns.
    """

    def __init__(self, api_key=None, api_secret=None, sailthru_client=None):
        """
        Set up the sailthru client using composition.

        :param api_key:
        :param api_secret:
        :param sailthru_client:
        """
        if sailthru_client is None:
            if api_key is None:
                raise ValueError('Sailthru API key not provided.')
            elif api_secret is None:
                raise ValueError('Sailthru API secret not provided.')
            sailthru_client = SailthruClient(api_key, api_secret)

        self.sailthru_client = sailthru_client

    def get_primary_lists(self):
        """
        Return list data about all lists marked as primary.

        :return: A list of sailthru list data dicts.
        :rtype: list[dict]
        """
        return self.api_get('list', {"primary": 1}).json['lists']

    def _infer_dive_email_type(self, campaign):
        """
        Industry Dive specific function to try to figure out how to
        categorize a given campaign/blast in terms we understand.

        :param dict campaign: A dict representing metadata for one email send
            ("blast" in Sailthru langauge).
        :return: A string that corresponds to one of the DiveEmailTypes
            options.
        :rtype: string
        """
        labels = campaign.get('labels', [])
        name = campaign.get('name', '')
        list_name = campaign.get('list', '')
        subject = campaign.get('subject', '').encode('utf-8', errors='replace')
        if "Blast" in labels or '-blast-' in name:
            return DiveEmailTypes.Blast
        if "Welcome Series" in labels:
            return DiveEmailTypes.WelcomeSeries
        if list_name.endswith("Weekender") or \
                name.startswith("Newsletter Weekly Roundup"):
            return DiveEmailTypes.Weekender
        if "newsletter" in labels or name.startswith("Issue: "):
            return DiveEmailTypes.Newsletter
        if list_name.lower().endswith("blast list"):
            return DiveEmailTypes.Blast
        if subject.startswith("BREAKING"):
            return DiveEmailTypes.BreakingNews

        return DiveEmailTypes.Unknown

    def _infer_dive_brand(self, campaign):
        """
        Guesses the Dive newsletter brand.

        :param dict campaign: A dict of campaign metadata.
        :return: String representing main Dive name (like "Healthcare Dive")
            or None.
        :rtype: string|None
        """
        import re

        list_name = campaign.get('list', '')
        if list_name.lower().endswith("blast list"):
            return re.sub(r' [Bb]last [Ll]ist$', '', list_name)
        if list_name.lower().endswith("weekender"):
            return re.sub(r' [Ww]eekender$', '', list_name)
        if list_name.endswith(" Dive") or \
                re.match(r'[A-Za-z]+ Dive: [a-zA-Z]+', list_name):
            return list_name

        return None

    def raise_exception_if_error(self, response):
        """
        Raises an exception if there was a problem with the given API response.
        """
        if not response.is_ok():
            api_error = response.get_error()
            raise SailthruApiError(
                "%s (%s)" % (api_error.message, api_error.code)
            )

    def get_campaigns_in_range(self, start_date, end_date, list_name=None):
        """
        Get sent campaign (blast) metadata based on date range and optionally
        only sent to a named list. In addition to data returned from sailthru
        api, adds additional fields dive_email_type and dive_brand to each
        campaign.

        THIS USES THE 'blast' API endpoint, calling based on status and date (this
        returns different data than calling the 'blast' endpoint for a single campaign).

        :param start_date: date or datetime
        :param end_date: date or datetime
        :param list_name: Optionally limit results to sends to one named list.
        :return: list of dicts where each dict is one campaign (see below)
         { 'abtest': 'final',
          'abtest_segment': 'Final',
          'abtest_winner_metric': 'beacon',
          'blast_id': 4889393,
          'copy_blast_id': 4889394,
          'email_count': 16796,
          'final_blast_id': 4889393,
          'labels': ['Blast'],
          'list': 'Utility Dive: Solar blast list',
          'mode': 'email',
          'modify_time': 'Thu, 06 Aug 2015 15:28:17 -0400',
          'modify_user': 'xxx@industrydive.com',
          'name': 'ABB Survey recruitment-blast-UD Solar-Aug6',
          'schedule_time': 'Thu, 06 Aug 2015 15:28:00 -0400',
          'sent_count': 16796,
          'start_time': 'Thu, 06 Aug 2015 15:28:17 -0400',
          'stats': { 'total': { 'beacon_click': 38,
                                'beacon_noclick': 2521,
                                'click_multiple_urls': 12,
                                'click_total': 165,
                                'count': 16796,
                                'hardbounce': 1,
                                'nobeacon_click': 59,
                                'open_total': 3404,
                                'optout': 9,
                                'softbounce': 331}},
          'status': 'sent',
          'subject': 'Utilities: Is your grid secure?'}
        """
        campaigns = []
        # Sailthru API does not appear able to handle requests for large
        # numbers of campaigns, so we somewhat arbitrarily break down requests
        # for "large" date ranges to multiple API requests and then stitch them
        # together in this function.
        page_size_in_days = 30
        page_start_date = start_date
        while page_start_date < end_date:
            page_end_date = \
                page_start_date + datetime.timedelta(days=page_size_in_days)
            if page_end_date > end_date:
                page_end_date = end_date  # Don't go past the request end_date.

            # Build api parameters. Dates must converted to strings.
            api_params = {
                'status': 'sent',
                'start_date': page_start_date.strftime("%Y-%m-%d"),
                'end_date': page_end_date.strftime("%Y-%m-%d"),
            }
            if list_name is not None:
                api_params['list'] = list_name

            result = self.api_get('blast', api_params)

            data = result.json
            # We reverse the results to keep everything in ascending
            # chronological order.
            for c in reversed(data.get('blasts', [])):
                c['dive_email_type'] = self._infer_dive_email_type(c)
                c['dive_brand'] = self._infer_dive_brand(c)
                # Automatically "fix" unicode problems.
                # TODO: Not sure this is right.
                c['name'] = c['name'].encode('utf-8', errors='replace')
                c['subject'] = c['subject'].encode('utf-8', errors='replace')
                campaigns.append(c)

            page_start_date = page_end_date

        return campaigns

    def get_campaign_stats(self, blast_id, include_clickmap=False,
                           include_subject=False, include_click_times=False,
                           include_urls=False, include_device=False):
        """ blast stats (opens clicks etc) for a given blast_id
            Results look like the following (depending on options)
            { 'beacon': 2559,
              'click': 97,
              'click_multiple_urls': 12,
              'click_total': 165,
              'confirmed_opens': 2618,
              'count': 16796,
              'estopens': 6532,
              'hardbounce': 1,
              'open_total': 3404,
              'optout': 9,
              'softbounce': 331,

              // if clickmap = 1
              'clickmap': [ { 'count': 15,
                                  'ix': '1',
                                  'url': 'http://www.utilitydive.com/signup/'},
                                { 'count': 1, 'ix': '4', 'url': 'http://svy.mk/1SoQww1'},
                                { 'count': 18, 'ix': '2', 'url': 'http://svy.mk/1SoQww1'},
                                { 'count': 11,
                                  'ix': '1',
                                  'url': 'http://www.utilitydive.com/about/privacy/'},
                                { 'count': 59, 'ix': '3', 'url': 'http://svy.mk/1SoQww1'},
                                { 'count': 4,
                                  'ix': '2',
                                  'url': 'http://www.utilitydive.com/about/privacy/'},
                                { 'count': 2,
                                  'ix': '2',
                                  'url': 'http://www.utilitydive.com/signup/'},
                                { 'count': 55, 'ix': '1', 'url': 'http://svy.mk/1SoQww1'}],

              // if subject = 1
              'subject': { 'Utilities: Is your grid secure?': { 'beacon': 2559,
                                                                'click': 97,
                                                                'click_multiple_urls': 12,
                                                                'click_total': 165,
                                                                'confirmed_opens': 2618,
                                                                'count': 16796,
                                                                'estopens': 6532,
                                                                'hardbounce': 1,
                                                                'open_total': 3404,
                                                                'optout': 9,
                                                                'softbounce': 331}}}

              // clicktimes = 1
              'click_times': { '1438889100': 58,
                               '1438889400': 3,
                               '1438889700': 1,
                               '1438890000': 1,
                               [...]

              // urls = 1
              'urls': { 'http://svy.mk/1SoQww1': { 'click': 93,
                                                   'click_total': 133,
                                                   'count': 16796},
                        'http://www.utilitydive.com/about/privacy/': { 'click': 6,
                                                                       'click_total': 15,
                                                                       'count': 16796},
                        'http://www.utilitydive.com/signup/': { 'click': 4,
                                                                'click_total': 17,
                                                                'count': 16796}}}


              'device': { 'Android': { 'beacon': 93,
                                       'click': 0,
                                       'confirmed_opens': 93,
                                       'count': 93,
                                       'estopens': 93,
                                       'open_total': 131},
                          'Android Tablet': { 'beacon': 3,
                          [...]
        """
        options = {}
        if include_clickmap:
            options['clickmap'] = '1'
        if include_click_times:
            options['click_times'] = '1'
        if include_device:
            options['device'] = '1'
        if include_subject:
            options['subject'] = '1'
        if include_urls:
            options['urls'] = '1'

        result = self.stats_blast(blast_id=blast_id, options=options)
        self.raise_exception_if_error(result)

        return result.json

    def get_campaign_data(self, blast_id):
        """ get content_html (and other meta data) for particular message
            Results like:
            { 'abtest_fields': ['subject'],
              'abtest_id': '55c2462f15dd96ec76b56393',
              'abtest_percent': 70,
              'abtest_segment': 'Final',
              'abtest_type': 'final',
              'abtest_winner_metric': 'beacon',
              'app_badge': None,
              'app_data': None,
              'app_id': None,
              'app_sound': None,
              'blast_id': 4889393,
              'content_app': None,
              'content_html': u'<html> [.....] </html>\r\n',
              'content_sms': None,
              'content_text': u'Utility Dive\r\n\r\n [.....]',
              'copy_blast_id': 4889394,
              'email_count': 16796,
              'from_email': 'newsletter@divenewsletter.com',
              'from_name': 'Utility Dive: Solar',
              'is_google_analytics': False,
              'is_link_tracking': True,
              'labels': ['Blast'],
              'list': 'Utility Dive: Solar blast list',
              'modify_time': 'Thu, 06 Aug 2015 15:28:17 -0400',
              'modify_user': 'xxx@industrydive.com',
              'name': 'ABB Survey recruitment-blast-UD Solar-Aug6',
              'replyto': None,
              'report_email': 'xxx@industrydive.com',
              'schedule_time': 'Thu, 06 Aug 2015 15:28:00 -0400',
              'seed_emails': [ 'xxx@example.com',
                               'yyy@example.com',
                               'zzz@example.com'],
              'start_time': 'Thu, 06 Aug 2015 15:28:17 -0400',
              'status': 'sent',
              'stop_time': 'Thu, 06 Aug 2015 15:28:36 -0400',
              'subject': 'Utilities: Is your grid secure?',
              'suppress_list': None}

        """
        result = self.api_get('blast', {
            'blast_id': blast_id,
        })

        return result.json

    def api_post(self, *args, **kwargs):
        """
        Wrapper around api_post to raise exception if there is any problem.
        """
        response = self.sailthru_client.api_post(*args, **kwargs)
        self.raise_exception_if_error(response)

        return response

    def api_get(self, *args, **kwargs):
        """
        Wrapper around api_get to raise exception if there is any problem.
        """
        response = self.sailthru_client.api_get(*args, **kwargs)
        self.raise_exception_if_error(response)

        return response
