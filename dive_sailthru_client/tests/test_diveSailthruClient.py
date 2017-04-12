from unittest import TestCase
from dive_sailthru_client.client import DiveSailthruClient, DiveEmailTypes
from dive_sailthru_client.errors import SailthruApiError
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
                'expected_brand': 'Mobile Marketer',
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
                'expected_brand': 'Mobile Marketer',
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
                'expected_brand': 'Mobile Marketer',
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
                # 'expected_brand': 'Construction Dive: Tech',  # TODO: doesn't work!
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
                # 'expected_brand': 'Healthcare Dive: IT',  # TODO: doesn't work!
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
                'expected_brand': 'Education Dive: Higher Ed',
                'expected_type': DiveEmailTypes.Newsletter,
                'comment': 'Old higher ed newsletter',
            }
            # TODO: add tests for Breaking news
        ]

        for test_case in test_cases:
            # test email type is correct
            if 'expected_type' in test_case.keys():
                actual_email_type = self.sailthru_client._infer_dive_email_type(test_case['input'])
                msg = "dive_email_type '%s' != '%s' while testing '%s'" % \
                      (actual_email_type, test_case['expected_type'], test_case['comment'])
                self.assertEqual(actual_email_type, test_case['expected_type'], msg)
            # test brand is correct
            if 'expected_brand' in test_case.keys():
                actual_brand = self.sailthru_client._infer_dive_brand(test_case['input'])
                msg = "dive_brand '%s' != '%s' while testing '%s'" % \
                      (actual_brand, test_case['expected_brand'], test_case['comment'])
                self.assertEqual(actual_brand, test_case['expected_brand'], msg)

    def test__infer_dive_email_type(self):
        """
        Test that we can guess the dive email type from the mailing.
        :return:
        """
        # TODO: reorganize this test to match the style of test__infer_dive_brand
        inputs = [
            {
                'blast_id': 4889393,
                'labels': ['Blast'],
                'list': 'Utility Dive: Solar blast list',
                'name': 'ABB Survey recruitment-blast-UD Solar-Aug6',
                'subject': 'Utilities: Is your grid secure?'
            },
            {
                'blast_id': 12345,
                'labels': ['Welcome Series', 'Fake label', ]
            },
            {
                'labels': ['newsletter', 'fake label', ]
            },
            {
                'list': 'This is the Weekender',
            },
            {
                'blast_id': 12345,
                'labels': [
                    'not a blast',
                    'not a welcome series',
                    'not a newsletter',
                    'not BREAKING',
                    'NOT A WEEKENDER'
                ]
            },
            {
                'subject': 'BREAKING the law'
            }
        ]

        expected = [
            DiveEmailTypes.Blast,
            DiveEmailTypes.WelcomeSeries,
            DiveEmailTypes.Newsletter,
            DiveEmailTypes.Weekender,
            DiveEmailTypes.Unknown,
            DiveEmailTypes.BreakingNews
        ]

        for index, input in enumerate(inputs):
            output = self.sailthru_client._infer_dive_email_type(input)
            self.assertEqual(output, expected[index])

    def test__infer_dive_brand(self):
        test_campaigns = [
            {
                # test that brand = list for regular newsletters
                'input': {
                    'list': 'foo',
                    'dive_email_type': DiveEmailTypes.Newsletter
                },
                'expected_brand': 'foo'
            },
            {
                # test that missing campaign data has brand of None
                'input': {'gibberish': 'nothing useful'},
                'expected_brand': None
            },
            {
                # test that brand = list minus " Weekender" for weekender
                'input': {
                    'list': 'Wkndr Test Weekender',
                    'dive_email_type': DiveEmailTypes.Weekender
                },
                'expected_brand': 'Wkndr Test'
            },
            {
                # test that brand = list minus " Blast List" for blasts
                'input': {
                    'list': 'Blast Test Blast List',
                    'dive_email_type': DiveEmailTypes.Blast
                },
                'expected_brand': 'Blast Test'
            },
        ]
        for test_campaign in test_campaigns:
            output_brand = self.sailthru_client._infer_dive_brand(test_campaign['input'])
            self.assertEqual(output_brand, test_campaign['expected_brand'])

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

        self.assertEqual(cm.exception.message, 'this is the error (1234)')
        self.assertTrue(mock_response.get_error.called)

    @patch('dive_sailthru_client.client.DiveSailthruClient')
    @patch('sailthru.sailthru_response.SailthruResponse')
    def test_get_campaigns_in_range(self, mock_response, mock_client):
        # TODO
        # mock_response.is_ok.return_value = True
        # mock_response.json.return_value = {
        #     'blasts': [
        #         {
        #             'subject': 'this is a blast'
        #         }
        #     ]
        # }
        #
        # mock_client._infer_dive_brand_email_type.return_value = 'the type'
        # mock_client._infer_dive_brand.return_value = 'the brand'
        # mock_client.api_get.return_value = mock_response
        #
        # from datetime import datetime, timedelta
        # campaigns = mock_client.get_campaigns_in_range(datetime.now(), datetime.now() + timedelta(1))
        #
        # self.assertEqual(campaigns[0].subject, 'this is a blast')
        # self.assertEqual(campaigns[0].dive_email_type, 'the type')
        # self.assertEqual(campaigns[0].dive_brand, 'the brand')

        # self.fail()
        pass

    def test_get_campaign_stats(self):
        # self.fail()
        pass

    def test_get_campaign_data(self):
        # self.fail()
        pass
