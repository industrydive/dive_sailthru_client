from sailthru import sailthru_client
from .errors import SailthruApiError, SailthruUserEmailError
# We need the SailthruClientError to be able to handle retries in api_get
from sailthru.sailthru_error import SailthruClientError
# for patched_sailthru_http_request
from sailthru.sailthru_response import SailthruResponse
from sailthru.sailthru_http import flatten_nested_hash
import requests
import platform
# other libraries
import datetime
import time
import re

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
    Spotlight = "spotlight"
    Audience = "audience"  # e.g. Dive-iversary, "Update your profile"


# There is some skullduggery below in order to override the hardcoded 10 second timeout on HTTP requests
# per TECH-3849. First we copy/paste the sailthru_http_request() function that originally exists here:
# https://github.com/sailthru/sailthru-python-client/blob/521fdaa30890a29da8fbb02726e7d22ed174b878/sailthru/sailthru_http.py#L30
# Then we modify it to have a default timeout of 60 seconds and additionally to accept a timeout parameter
def timeout_patched_sailthru_http_request(url, data, method, file_data=None, timeout=60):
    """
    Perform an HTTP GET / POST / DELETE request

    This is a override of upstream sailthru_http_request with `timeout` added as a parameter and
    with the default set to 60 instead of 10.
    """
    data = flatten_nested_hash(data)
    method = method.upper()
    params, data = (None, data) if method == 'POST' else (data, None)

    try:
        headers = {'User-Agent': 'Sailthru API Python Client %s; Python Version: %s' % ('2.3.3-patched', platform.python_version())}
        response = requests.request(method, url, params=params, data=data, files=file_data, headers=headers, timeout=timeout)
        return SailthruResponse(response)
    except requests.HTTPError as e:
        raise SailthruClientError(str(e))
    except requests.RequestException as e:
        raise SailthruClientError(str(e))


# Now we need to patch the altered sailthru_http_request into a place where even functions defined in the upstream
# SailthruClient class that call it will call our new altered version. In the upstream class, the sailthru_http_request()
# function is `import`ed into the sailthru_client module (not the class), so we need to import the sailthru_client module
# and then redefine the sailthru_http_request that it had imported to instead point to our version. Then later we
# have to make sure we are subclassing SailthruClient by refering to it specifically as sailthru_client.SailthruClient
sailthru_client.sailthru_http_request = timeout_patched_sailthru_http_request


class DiveSailthruClient(sailthru_client.SailthruClient):  # must import from sailthru_client.SailthruClient for patched HTTP timeout
    """
    Our Sailthru client implementation that adds our own concepts.

    This includes dive publication (misnamed as key dive_brand), dive email type,
    and easier ways to query campaigns.
    """

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
        # WARNING! Order matters below
        if "Blast" in labels or '-blast-' in name:
            return DiveEmailTypes.Blast
        elif "Welcome Series" in labels:
            return DiveEmailTypes.WelcomeSeries
        elif "Welcome" in list_name and " days " in name.lower():
            return DiveEmailTypes.WelcomeSeries
        elif "Dive-iversary" in subject or "Dive-iversary" in list_name:
            return DiveEmailTypes.Audience
        elif "update profile" in list_name:
            return DiveEmailTypes.Audience
        elif "linkedin" in list_name.lower() and "linkedin" in name.lower():
            return DiveEmailTypes.Audience
        elif "spotlight-newsletter" in labels:
            # Note that spotlight's name also starts with "Issue: " so this check must
            # appear before thaat one
            return DiveEmailTypes.Spotlight
        elif list_name.endswith("Weekender") or \
                name.startswith("Newsletter Weekly Roundup"):
            return DiveEmailTypes.Weekender
        elif "newsletter" in labels or name.startswith("Issue: "):
            return DiveEmailTypes.Newsletter
        elif list_name.lower().endswith("blast list"):
            return DiveEmailTypes.Blast
        elif subject.startswith(b"BREAKING"):
            return DiveEmailTypes.BreakingNews
        elif list_name == "Supply Chain Dive: Operations" and "Issue" in name:
            return DiveEmailTypes.Newsletter
        else:
            return DiveEmailTypes.Unknown

    def _infer_dive_publication(self, campaign):
        """
        Guesses the Dive newsletter's publication based on its dive_email_type and list name

        :param dict campaign: A dict of campaign metadata.
        :return: String representing publication name (like "Healthcare Dive" or "Education Dive: Higher Ed")
            or None.
        :rtype: string|None
        """

        # This function requires a dive_email_type, so if 'dive_email_type' is already a key
        # in the campaign than use it, otherwise call it here.
        if 'dive_email_type' in campaign.keys():
            dive_email_type = campaign['dive_email_type']
        else:
            dive_email_type = self._infer_dive_email_type(campaign)

        list_name = campaign.get('list', '')
        if (dive_email_type in [DiveEmailTypes.Blast, DiveEmailTypes.Spotlight]) and list_name.lower().endswith("blast list"):
            # The Utility Dive Spotlight goes out to a special
            # blast list: "Utility Dive and sub pubs Blast List"
            # This regex handles that as well as normal blast lists
            return re.sub(r'( and sub pubs)? [Bb]last [Ll]ist$', '', list_name)
        if dive_email_type == DiveEmailTypes.Weekender and list_name.lower().endswith("weekender"):
            return re.sub(r' [Ww]eekender$', '', list_name)
        if dive_email_type == DiveEmailTypes.Newsletter:
            return list_name

        return None

    def raise_exception_if_error(self, response):
        """
        Raises an exception if there was a problem with the given API response.
        """
        if not response.is_ok():
            api_error = response.get_error()
            if api_error.code in SailthruUserEmailError.USER_EMAIL_ERROR_CODES.keys():
                raise SailthruUserEmailError(
                    '%s (%s)' % (api_error.message, api_error.code)
                )
            else:
                raise SailthruApiError(
                    '%s (%s)' % (api_error.message, api_error.code)
                )

    def get_campaigns_in_range(self, start_date, end_date, list_name=None):
        """
        Get sent campaign (blast) metadata based on date range and optionally
        only sent to a named list. In addition to data returned from sailthru
        api, adds additional fields dive_email_type and dive_brand (a misnomer for publication)
        to each campaign.

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
                'limit': 999999,  # workaround for limited data returned, see TECH-1615.
            }
            if list_name is not None:
                api_params['list'] = list_name

            result = self.api_get('blast', api_params)

            data = result.json
            blasts = data.get('blasts', [])
            filtered_count = data.get('filtered_count', 0)
            # We discovered in TECH-1615 that Sailthru is (accidentally?) limiting number of results. So let's
            # specifically raise an exception if the expected number of records doesn't match the actual returned.
            if filtered_count != len(blasts):
                raise SailthruApiError(
                    "Incomplete 'blast' API data. Expected %d records, got %d" % (filtered_count, len(blasts))
                )

            # We reverse the results to keep everything in ascending
            # chronological order.
            for c in reversed(blasts):
                c['dive_email_type'] = self._infer_dive_email_type(c)
                # technically below gets the pub, but keeping key `dive_brand` for backwards compatability
                c['dive_brand'] = self._infer_dive_publication(c)
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

    def export_list(self, list_name, fields=None, sailthru_vars=None, block_until_complete=True):
        """ When the job is complete, the response should look something like:

        {
          'status': 'completed',
          'job_id': '591b670d15dd96ab608b4c5f',
          'start_time': 'Tue, 16 May 2017 16:54:38 -0400',
          'list': 'Just Eli',
          'export_url': 'https://s3.amazonaws.com/sailthru/export/2017/05/16/64860e9036c829ed8a1c5f34xxxxxxx',
          'filename': 'just_eli.csv',
          'end_time': 'Tue, 16 May 2017 16:54:38 -0400',
          'name': 'Export All List Data: Just Eli'}

          And fetching the S3 URL looks like:
          [...]
          Content-Disposition: attachment; filename=just_eli.csv
          Accept-Ranges: bytes
          Content-Type: text/csv; charset=utf-8
          Content-Length: 4206
          [...]
        """
        job_params = {
            'job': 'export_list_data',
            'list': list_name,
            'fields': {},
        }
        if fields:
            for f in fields:
                job_params['fields'][f] = 1
        if sailthru_vars:
            job_params['fields']['vars'] = {}
            for v in sailthru_vars:
                job_params['fields']['vars'][v] = 1
        job_result_json = self.api_post('job', job_params).json
        job_id = job_result_json['job_id']
        if block_until_complete:
            job_result_json = self._block_until_job_complete(job_id)
        if job_result_json['status'] not in ('pending', 'completed'):
            raise SailthruApiError("Job '%s' ended with unexpected status '%s'", job_id, job_result_json['status'])
        return job_result_json

    def update_job(self, update_file_name=None, update_file_stream=None, block_until_complete=True):
        """
        Perform an 'update' job request, which bulk updates changes to a list of users typically
        in a file in JSON-lines format. See https://getstarted.sailthru.com/developers/api/job/#update
        Should pass in a file name (which will be opened for you) or a file-like object but not both!
        @param update_file_name: file name of update file to send; should be None if update_file_stream is set
        @param update_file_stream: an already opened stream to a file-link object of stuff to update
        @param block_until_complete: whether to simply request the job and return or to block until it's done
        """
        job_params = {
            'job': 'update',
        }
        assert not (update_file_name and update_file_stream)
        if update_file_name:
            job_params['file'] = update_file_name
            job_result_json = self.api_post('job', job_params).json
        else:  # update_file_stream
            job_result_json = self.api_post_with_binary_stream('job', job_params, update_file_stream).json
        job_id = job_result_json['job_id']
        if block_until_complete:
            job_result_json = self._block_until_job_complete(job_id)
        if job_result_json['status'] not in ('pending', 'completed'):
            raise SailthruApiError("Job '%s' ended with unexpected status '%s'", job_id, job_result_json['status'])
        return job_result_json

    def api_post_with_binary_stream(self, action, data, binary_stream):
        """
        A wrapper around _http_request that lets you pass in opened streams and doesn't assume
        it needs to open() them itself
        """
        request_type = 'POST'
        file_data = {'file': binary_stream}
        response = self._http_request(action, self._prepare_json_payload(data), request_type, file_data)
        self.raise_exception_if_error(response)
        return response

    def _block_until_job_complete(self, job_id, seconds_between_checks=1, max_wait_seconds=21600):
        """ returns result of the job; raises exception if job not complete in max_wait_seconds """
        max_iterations = int(max_wait_seconds / seconds_between_checks) + 1
        for _ in range(max_iterations):
            job_result_json = self.get_job_info(job_id)
            if job_result_json['status'] != 'pending':
                # It's either complete or something went wrong, so stop checking
                break
            time.sleep(seconds_between_checks)
        # If the loop finished and it's still pending, then it has now taken too long
        if job_result_json['status'] == 'pending':
            raise SailthruApiError("Exceeded max wait time of %d seconds on job id '%s'", max_wait_seconds, job_id)
        return job_result_json

    def get_job_info(self, job_id):
        """ Expected keys returned: status, name, start_time, end_time """
        result = self.api_get('job', {'job_id': job_id})
        return result.json

    def api_post(self, *args, **kwargs):
        """
        Wrapper around api_post to raise exception if there is any problem.
        """
        response = super(DiveSailthruClient, self).api_post(*args, **kwargs)
        self.raise_exception_if_error(response)

        return response

    def api_get(self, *args, **kwargs):
        """
        Wrapper around api_get to raise exception if there is any problem. And
        to add some simple retry logic for Connection Timeout errors. We encountered
        these timeout errors in the wild in some small percentage of stats_blast API
        calls. (See TECH-1736)
        """
        for _ in range(3):
            try:
                response = super(DiveSailthruClient, self).api_get(*args, **kwargs)
                break
            except SailthruClientError as e:
                if 'ConnectTimeoutError' in str(e):
                    # We want to retry connection timeout errors only. Sailthru client
                    #   smushes the original exception from Requests into a string arg
                    #   so we need to test for it with string matching here.
                    pass
                else:
                    # If it wasn't a ConnectTimeoutError than don't retry
                    raise
        else:
            # If we got here we exceeded the max number of retries
            raise

        # At this point we have a response from the server but we still need to check
        #   if the response itself is marked as an error
        self.raise_exception_if_error(response)

        return response
