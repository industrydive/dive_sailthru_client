from __future__ import absolute_import
from unittest import TestCase
from dive_sailthru_client.client import DiveSailthruClient, DiveEmailTypes
from dive_sailthru_client.errors import SailthruApiError, SailthruUserEmailError
from mock import patch
from nose.plugins.attrib import attr


@attr('unittest')
class TestDiveSailthruClient(TestCase):

    def setUp(self):
        self.sailthru_client = DiveSailthruClient('abc', 'def')

    def test_infer_dive_email_type_and_brand_real_examples(self):
        test_cases = [
            {
                'input': {
                    'blast_id': 9354623,
                    'email_count': 22134,
                    'labels': ['Mobile Marketer', 'daily-newsletter', 'newsletter'],
                    'list': 'Mobile Marketer',
                    'mode': 'email',
                    'modify_time': 'Mon, 10 Apr 2017 11:03:45 -0400',
                    'name': 'Issue: 2017-04-10 Mobile Marketer [issue:9825]',
                    'public_url': 'link.mobilemarketer.com/public/9354623',
                    'schedule_time': 'Mon, 10 Apr 2017 11:18:45 -0400',
                    'sent_count': 22134,
                    'start_time': 'Mon, 10 Apr 2017 11:19:01 -0400',
                    'status': 'sent',
                    'subject': ("Apr. 10 -  How video glues together branding, direct response:"
                                " Snapchat's Bitmoji is most downloaded app")
                },
                'expected_type': DiveEmailTypes.Newsletter,
                'expected_publication': 'Mobile Marketer',
                'comment': 'MM newsletter',
            },
            {
                'input': {
                    'blast_id': 9344866,
                    'data_feed_url': 'http://feed.sailthru.com/ws/feed?id=58d3f044ade9c205068b4569',
                    'email_count': 22014,
                    'email_hour_range': 8,
                    'labels': ['Mobile Marketer', 'newsletter', 'weekender-newsletter'],
                    'list': 'Mobile Marketer Weekender',
                    'mode': 'email',
                    'modify_time': 'Sat, 08 Apr 2017 10:00:47 -0400',
                    'name': 'Newsletter Weekly Roundup: Mobile Marketer 04-08-2017',
                    'public_url': 'link.mobilemarketer.com/public/9344866',
                    'schedule_time': 'Sat, 08 Apr 2017 11:00:47 -0400',
                    'sent_count': 22014,
                    'start_time': 'Sat, 08 Apr 2017 11:01:02 -0400',
                    'status': 'sent',
                    'subject': 'Weekender: {{top_stories[0].title}}',
                },
                'expected_publication': 'Mobile Marketer',
                'expected_type': DiveEmailTypes.Weekender,
                'comment': 'MM weekender',
            },
            {
                'input': {
                    'blast_id': 9318162,
                    'email_count': 25339,
                    'labels': ['Blast'],
                    'list': 'Mobile Marketer Blast List',
                    'mode': 'email',
                    'modify_time': 'Thu, 06 Apr 2017 09:20:43 -0400',
                    'modify_user': 'xxx@industrydive.com',
                    'name': 'Vibes-0060L00000jG8MGQA0-Blast-MobileMarketer-April6',
                    'public_url': 'link.divenewsletter.com/public/9318162',
                    'schedule_time': 'Thu, 06 Apr 2017 09:27:00 -0400',
                    'sent_count': 25339,
                    'start_time': 'Thu, 06 Apr 2017 09:27:01 -0400',
                    'status': 'sent',
                    'subject': 'Vibes brings you mobile consumer preference data for 2017',
                    'suppress_list': []
                },
                'expected_publication': 'Mobile Marketer',
                'expected_type': DiveEmailTypes.Blast,
                'comment': 'MM Email Blast',
            },
            {
                'input': {
                    'blast_id': 9238319,
                    'copy_template': 'welcome_construction_tech_4A',
                    'data_feed_url': 'http://feed.sailthru.com/ws/feed?id=546b70c81092031f7b04e8c0',
                    'email_count': 3,
                    'email_hour_range': 2,
                    'labels': ['Construction', 'Welcome Series'],
                    'list': 'Construction: Tech Welcome 120 Days ACTIVE',
                    'mode': 'email',
                    'modify_time': 'Sat, 25 Mar 2017 10:00:05 -0400',
                    'modify_user': 'xxx@industrydive.com',
                    'name': 'Construction: Tech 120 Days Active 2017-03-25',
                    'schedule_time': 'Sat, 25 Mar 2017 10:00:04 -0400',
                    'sent_count': 2,
                    'start_time': 'Sat, 25 Mar 2017 10:01:01 -0400',
                    'status': 'sent',
                    'subject': 'Question: Construction Dive: Tech',
                    'suppress_list': ['Suppression: have NOT opened or clicked or viewed page in last 28 days']
                },
                # 'expected_publication': 'Construction Dive: Tech',  # TODO: doesn't work!
                'expected_type': DiveEmailTypes.WelcomeSeries,
                'comment': 'CD:Tech Welcome Series',
            },
            {
                'input': {
                    'blast_id': 4069224,
                    'copy_template': 'welcome_healthcare_it_2B',
                    'data_feed_url': 'http://feed.sailthru.com/ws/feed?id=546f7257109203ec1470cec1',
                    'email_count': 10,
                    'email_hour_range': 4,
                    'labels': ['Healthcare', 'Welcome Series'],
                    'list': 'Health: IT Welcome 30 Days',
                    'mode': 'email',
                    'modify_time': 'Wed, 25 Mar 2015 10:00:42 -0400',
                    'modify_user': 'xxx@industrydive.com',
                    'name': 'Health: IT 30 days Inactive 2015-03-25',
                    'schedule_time': 'Wed, 25 Mar 2015 10:00:42 -0400',
                    'sent_count': 3,
                    'start_time': 'Wed, 25 Mar 2015 10:01:05 -0400',
                    'stats': {'total': {'beacon_noclick': 1, 'count': 3, 'open_total': 1}},
                    'status': 'sent',
                    'subject': 'Everything okay?'
                },
                # 'expected_publication': 'Healthcare Dive: IT',  # TODO: doesn't work!
                'expected_type': DiveEmailTypes.WelcomeSeries,
                'comment': 'Old HC:IT welcome message',
            },
            {
                'input': {
                    'blast_id': 4069274,
                    'email_count': 22671,
                    'labels': [],
                    'list': 'Education Dive: Higher Ed',
                    'mode': 'email',
                    'modify_time': 'Wed, 25 Mar 2015 10:02:08 -0400',
                    'modify_user': 'xxx@industrydive.com',
                    'name': 'Issue: 2015-03-25 Higher Ed Education Dive Newsletter',
                    'public_url': 'link.divenewsletter.com/public/4069274',
                    'schedule_time': 'Wed, 25 Mar 2015 10:17:08 -0400',
                    'sent_count': 22670,
                    'start_time': 'Wed, 25 Mar 2015 10:18:02 -0400',
                    'status': 'sent',
                    'subject': "Mar. 25 - Jones' ouster could cost Ole Miss $20M grant"
                },
                'expected_publication': 'Education Dive: Higher Ed',
                'expected_type': DiveEmailTypes.Newsletter,
                'comment': 'Old higher ed newsletter',
            },
            {
                "input": {
                    'blast_id': 9566780,
                    'email_count': 23490,
                    'labels': ["Education", "spotlight-newsletter"],
                    'list': 'Education Dive: K12 Blast List',
                    'mode': 'email',
                    'modify_time': 'Mon, 08 May 2017 14:00:24 -0400',
                    'modify_user': 'xxx@industrydive.com',
                    'name': 'Issue: 2017-05-08 Education K12 Spotlight [issue:10161]',
                    'public_url': 'link.educationdive.com/public/9566780',
                    'schedule_time': 'Mon, 08 May 2017 14:15:24 -0400',
                    'sent_count': 23490,
                    'start_time': 'Mon, 08 May 2017 14:16:02 -0400',
                    'status': 'sent',
                    'subject': "Spotlight on Literacy"

                },
                'expected_publication': 'Education Dive: K12',
                'expected_type': DiveEmailTypes.Spotlight,
                'comment': 'Education K12 spotlight',
            },
            {
                'input': {
                    'blast_id': 20694038,
                    'email_count': 41445,
                    'labels': ['Blast'],
                    'list': 'HR Dive Blast List - Group B',
                    'modify_time': 'Thu, 25 Jun 2020 08:48:11 -0400',
                    'name': 'InStride-0060L00000spHSF-blast-HR-June25',
                    'public_url': 'link.divenewsletter.com/public/20694038',
                    'schedule_time': 'Thu, 25 Jun 2020 08:50:00 -0400',
                    'start_time': 'Thu, 25 Jun 2020 08:50:03 -0400',
                    'status': 'sent',
                    'subject': '[Webinar] Tackling the Skills Gap: Why Quality Education Matters',

                },
                'expected_publication': 'HR Dive',
                'expected_type': DiveEmailTypes.HalfBlast,
                'comment': 'HR Dive Half Blast',
            },
            {
                'input': {
                    "blast_id": 25987691,
                    "name": "Pagero-0064W00000yYmXL-blast-CFO-Dec18",
                    "suppress_list": [],
                    "from_name": "CFO Dive",
                    "subject": "A CFO's guide on invoice automation",
                    "list": "CFO Dive Thirds Blast List - Group C",
                    "list_id": "60f1b0d6fb306d352d7a7dd1",
                    "email_count": 30258,
                    "start_time": "Sat, 18 Dec 2021 09:00:03 -0500",
                    "stop_time": "Sat, 18 Dec 2021 09:02:46 -0500",
                    "schedule_time": "Sat, 18 Dec 2021 09:00:00 -0500",
                    "schedule_type": "specific",
                    "status": "sent",
                    "public_url": "link.divenewsletter.com/public/25987691",
                    "labels": [
                        "Blast"
                    ],

                },
                'expected_publication': 'CFO Dive',
                'expected_type': DiveEmailTypes.ThirdBlast,
                'comment': 'CFO Dive third blast',
            },
            {
                'input': {
                    'blast_id': 31437039,
                    'email_count': 54245,
                    'labels': [],
                    'list': 'Marketing Dive Quarter Blast List - Group B',
                    'mode': 'email',
                    'modify_time': 'Tue, 23 May 2023 09:20:43 -0400',
                    'modify_user': 'xxx@industrydive.com',
                    'name': 'client_name=Salesforce.com&pt_id=a12K50000005y8oIAA&blast=quarterblast&site=MarketingDive&send_date=05.23.2023',
                    'public_url': 'link.divenewsletter.com/public/31437039',
                    'schedule_time': 'Tue, 23 May 2023 09:27:00 -0400',
                    'sent_count': 54245,
                    'start_time': 'Tue, 23 May 2023 09:27:01 -0400',
                    'status': 'sent',
                    'subject': 'See how personalized marketing can lift loyalty and raise ROI',
                    'suppress_list': []
                },
                'expected_publication': 'Marketing Dive',
                'expected_type': DiveEmailTypes.QuarterBlast,
                'comment': 'Marketing Dive Quarter Blast with param-type blast name',
            },
            # You can pull the data for these tests from sailthru_tools scripts/get_campaign.py
        ]

        for test_case in test_cases:
            # test email type is correct
            if 'expected_type' in list(test_case.keys()):
                actual_email_type = self.sailthru_client._infer_dive_email_type(test_case['input'])
                msg = "dive_email_type '%s' != '%s' while testing '%s'" % \
                      (actual_email_type, test_case['expected_type'], test_case['comment'])
                self.assertEqual(actual_email_type, test_case['expected_type'], msg)
            # test publication is correct
            if 'expected_publication' in list(test_case.keys()):
                actual_brand = self.sailthru_client._infer_dive_publication(test_case['input'])
                msg = "dive_brand key was '%s' != '%s' while testing '%s'" % \
                      (actual_brand, test_case['expected_publication'], test_case['comment'])
                self.assertEqual(actual_brand, test_case['expected_publication'], msg)

    def test__infer_dive_email_type(self):
        """
        Test that we can guess the dive email type from the mailing.
        :return:
        """
        test_cases = [
            {
                'blast_id': 4889393,
                'labels': ['Blast'],
                'list': 'Utility Dive: Solar blast list',
                'name': 'ABB Survey recruitment-blast-UD Solar-Aug6',
                'subject': 'Utilities: Is your grid secure?',
                'expected_type': DiveEmailTypes.Blast,
            },
            {
                'blast_id': 12345,
                'labels': ['Welcome Series', 'Fake label', ],
                'expected_type': DiveEmailTypes.WelcomeSeries,
            },
            {
                'labels': ['newsletter', 'fake label', ],
                'expected_type': DiveEmailTypes.Newsletter,
            },
            {
                'list': 'This is the Weekender',
                'expected_type': DiveEmailTypes.Weekender,
            },
            {
                'blast_id': 12345,
                'labels': [
                    'not a blast',
                    'not a welcome series',
                    'not a newsletter',
                    'not BREAKING',
                    'NOT A WEEKENDER'
                ],
                'expected_type': DiveEmailTypes.Unknown,
            },
            {
                'subject': 'BREAKING the law',
                'expected_type': DiveEmailTypes.BreakingNews
            }
        ]

        for test_case in test_cases:
            output = self.sailthru_client._infer_dive_email_type(test_case)
            self.assertEqual(output, test_case['expected_type'])

    def test__infer_dive_publication(self):
        test_campaigns = [
            {
                # test that publication = list for regular newsletters
                'input': {
                    'list': 'foo',
                    'dive_email_type': DiveEmailTypes.Newsletter
                },
                'expected_publication': 'foo'
            },
            {
                # test that missing campaign data has publication of None
                'input': {'gibberish': 'nothing useful'},
                'expected_publication': None
            },
            {
                # test that publication = list minus " Weekender" for weekender
                'input': {
                    'list': 'Wkndr Test Weekender',
                    'dive_email_type': DiveEmailTypes.Weekender
                },
                'expected_publication': 'Wkndr Test'
            },
            {
                # test that publication = list minus " Blast List" for blasts
                'input': {
                    'list': 'Blast Test Blast List',
                    'dive_email_type': DiveEmailTypes.Blast
                },
                'expected_publication': 'Blast Test'
            },
        ]
        for test_campaign in test_campaigns:
            output_publication = self.sailthru_client._infer_dive_publication(test_campaign['input'])
            self.assertEqual(output_publication, test_campaign['expected_publication'])

    @patch('sailthru.sailthru_response.SailthruResponse')
    @patch('sailthru.sailthru_response.SailthruResponseError')
    def test_raise_exception_if_error(self, mock_response, mock_error):
        """
        Test that an exception is raised on a sailthru error.

        :param mock_response:
        :param mock_error:
        :return:
        """
        mock_response.is_ok.return_value = True
        self.sailthru_client.raise_exception_if_error(mock_response)
        self.assertTrue(mock_response.is_ok.called)

        mock_error.message = 'this is the error'
        mock_error.code = 1234
        mock_response.is_ok.return_value = False
        mock_response.get_error.return_value = mock_error

        with self.assertRaises(SailthruApiError) as cm:
            self.sailthru_client.raise_exception_if_error(mock_response)

        self.assertEqual(str(cm.exception), 'this is the error (1234)')
        self.assertTrue(mock_response.get_error.called)

    @patch('sailthru.sailthru_response.SailthruResponse')
    @patch('sailthru.sailthru_response.SailthruResponseError')
    def test_raise_exception_if_error_for_email_related_errors(self, mock_response, mock_error):
        """
        Test that an error of one of the specific user-email-related types raises a SailthruUserEmailError
        See the list at https://getstarted.sailthru.com/developers/api-basics/responses/
        Our definition of the user-email-related errors is in the constant client.USER_EMAIL_ERROR_CODES, used here.

        :param mock_response:
        :param mock_error:
        :return:
        """
        # set up mock response so it will simulate these errors
        mock_response.is_ok.return_value = False
        mock_response.get_error.return_value = mock_error

        for code, message in SailthruUserEmailError.USER_EMAIL_ERROR_CODES.items():
            with self.assertRaises(SailthruUserEmailError):
                mock_error.code = code
                mock_error.message = message
                self.sailthru_client.raise_exception_if_error(mock_response)
