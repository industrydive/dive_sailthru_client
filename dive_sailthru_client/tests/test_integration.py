from unittest import TestCase
from nose.plugins.attrib import attr
from dive_sailthru_client.client import DiveSailthruClient
import os
import datetime
import tempfile
import StringIO
import unicodedata
import time
from datetime import date

@attr('external')
class TestDiveSailthruClientExternalIntegration(TestCase):
    def setUp(self):
        sailthru_key = os.getenv("SAILTHRU_API_KEY")
        sailthru_secret = os.getenv("SAILTHRU_API_SECRET")
        assert sailthru_key, "SAILTHRU_API_KEY env var must be defined"
        assert sailthru_secret, "SAILTHRU_API_SECRET env var must be defined"
        assert sailthru_key.lower().startswith("bc8"), "This test requires the DEV account Sailthru API key"
        self.sailthru_client = DiveSailthruClient(sailthru_key, sailthru_secret)
        self.test_email = 'eli+sailthru-client-integration-test@industrydive.com'
        self.test_var_key = "sailthruclienttestvalue"

    def _get_user_var(self, userid, key):
        response = self.sailthru_client.get_user(userid).response
        self.assertTrue(response.ok)
        json = response.json()
        if not json.get("vars"):
            return None
        return json["vars"].get(key)

    def _set_user_var(self, userid, key, value):
        response = self.sailthru_client.save_user(userid, options={"vars": {key: value}}).response
        self.assertTrue(response.ok)

    def test_get_set_var(self):
        """ Make sure the _get_user_var and _set_user_var functions work with the API as expected """
        # new_value = 'updated value %s' % datetime.datetime.now()
        new_value = str(datetime.datetime.now())
        value = self._get_user_var(self.test_email, self.test_var_key)
        self.assertNotEqual(value, new_value)
        self._set_user_var(self.test_email, self.test_var_key, new_value)
        value = self._get_user_var(self.test_email, self.test_var_key)
        self.assertEqual(value, new_value)

    def test_update_job_with_filename(self):
        """ Test that the update_job() function actually updates something """
        # first set a known value to the variable using set_var
        start_value = "start value %s" % datetime.datetime.now()
        self._set_user_var(self.test_email, self.test_var_key, start_value)

        # create temp file and stick our update string in it, then call update_job with the
        #   temp file's name. we set delete=False so that it isn't auto deleted when f.close()
        #   is called.
        f = tempfile.NamedTemporaryFile(delete=False)
        try:
            updated_value = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated_value = datetime.datetime.strptime(updated_value, '%Y-%m-%d %H:%M:%S')
            updated_value = "start value %s" % updated_value
            update_line = '{"id":"%s", "vars":{"%s":"%s"}}\n' % (self.test_email, self.test_var_key, updated_value)
            f.write(update_line)
            f.close()
            self.sailthru_client.update_job(update_file_name=f.name)
        finally:
            # since we set delete=False we need to clean up after ourselves manually
            os.unlink(f.name)
        # now check if it really updated
        test_updated_var = self._get_user_var(self.test_email, self.test_var_key)
        test_updated_var = unicodedata.normalize('NFKD', test_updated_var).encode('ascii', 'ignore')
        test_updated_var = datetime.datetime.strptime(test_updated_var[12:], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
        test_updated_var = 'start value %s' % test_updated_var
        self.assertEqual(test_updated_var, updated_value)

    def test_update_job_with_stream(self):
        """ Test that the update_job() function actually updates something """
        # first set a known value to the variable using set_var
        start_value = "start value %s" % datetime.datetime.now()
        self._set_user_var(self.test_email, self.test_var_key, start_value)
        # now let's set up the update "file" and turn it into a stream we can pass to API
        updated_value = "updated value %s" % datetime.datetime.now()
        update_line = '{"id":"%s", "vars":{"%s":"%s"}}\n' % (self.test_email, self.test_var_key, updated_value)
        stream = StringIO.StringIO(update_line)
        self.sailthru_client.update_job(update_file_stream=stream)
        # now check if it really updated
        test_updated_var = self._get_user_var(self.test_email, self.test_var_key)
        self.assertEqual(test_updated_var, updated_value)
