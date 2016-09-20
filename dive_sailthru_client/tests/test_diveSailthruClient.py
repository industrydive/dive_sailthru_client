from unittest import TestCase
from dive_sailthru_client.client import DiveSailthruClient, DiveEmailTypes
from dive_sailthru_client.errors import SailthruApiError
from mock import patch
from nose.plugins.attrib import attr


@attr('unittest')
class TestDiveSailthruClient(TestCase):

    def setUp(self):
        self.sailthru_client = DiveSailthruClient('abc', 'def')

    def test__infer_dive_email_type(self):
        """
        Test that we can guess the dive email type from the mailing.
        :return:
        """
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
        """
        Test that we can guess the dive brand from the mailing.
        :return:
        """

        inputs = [
            'This is a Blast List',
            'This is not a BLAST LIST',
            'This is a Weekender',
            'This is not a WEEKENDER',
            'This is a Dive',
            'This is not a dive',
            'Word Dive: Word',
            'Is not a Dive: because spaces',
            'Not a dive: because capital D',
            'Not a Dive because colon'
            ''
        ]

        expected = [
            'This is a',
            'This is not a BLAST LIST',
            'This is a',
            'This is not a WEEKENDER',
            'This is a Dive',
            None,
            'Word Dive: Word',
            None,
            None,
            None,
            None
        ]

        for index, input in enumerate(inputs):
            output = self.sailthru_client._infer_dive_brand({'list': input})
            self.assertEqual(output, expected[index])

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
