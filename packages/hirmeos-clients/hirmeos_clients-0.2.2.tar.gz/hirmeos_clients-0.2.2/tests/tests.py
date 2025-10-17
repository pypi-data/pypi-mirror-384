import unittest
from unittest.mock import patch

from src.hirmeos_clients import (
    TokenClient,
    TranslatorClient,
    AltmetricsClient
)

from variables import (
    canonical_uri_values,
    expected_decoded_token,
    expected_prepared_canonical_uris,
    expected_prepared_uris,
    expected_uri_schemes,
    expected_uri_values,
    obscure_valid_doi,
)


def new_translator_client():
    return TranslatorClient(
        translator_api_base='http://localhost:8000/translator_test',
        tokens_key='LooksLikeATestKey...',
    )


def new_token_client():
    token_email = 'test.token@testemail.test'
    return TokenClient(
        tokens_key='LooksLikeATestKey...',
        tokens_email=token_email,
        tokens_account=f'acct:{token_email}',
        tokens_name='test admin',
    )


def new_altmetrics_client():
    with patch(
        'src.hirmeos_clients.altmetrics.AltmetricsClient.get_token'
    ) as mock_get_token:
        mock_get_token.return_value = 'test_token'
        return AltmetricsClient(
            email='test.token@testemail.test',
            password='test_pass',
        )


class LogicTestCase(unittest.TestCase):

    def setUp(self):
        self.translator = new_translator_client()
        self.altmetrics = new_altmetrics_client()

    def test_get_scheme_from_uri_fails_for_obscure_dois(self):
        """Test that function still cannot handle obscure DOIs."""
        self.assertNotEqual(
            self.translator.get_scheme_from_uri(obscure_valid_doi),
            'info:doi',
            'Can now correctly determine URI scheme for obscure DOIs!'
        )

    def test_get_scheme_from_uri_works_for_expected_uris(self):
        """Test that function can determine the schemes of expected URIs."""
        calculated_uri_schemes = [
            self.translator.get_scheme_from_uri(uri)
            for uri in sorted(expected_uri_values)
        ]
        self.assertEqual(
            calculated_uri_schemes,
            expected_uri_schemes,
            'Failed to determine correct URI schemes for expected URIs.'
        )

    def test_format_uri_produces_expected_values(self):
        """Test that function ."""
        formatted_uri_values = [
            self.translator.format_uri(uri)
            for uri in sorted(expected_uri_values)
        ]
        self.assertEqual(
            formatted_uri_values,
            expected_uri_values,
            'Failure to correctly format expected URIs.'
        )

    def test__prepare_new_work_prepares_work_as_expected(self):
        """Test that function ."""
        prepared_work = self.translator._prepare_new_work(
            'book',
            'The book',
            expected_uri_values,
            [],
        )
        expected_work = {
            'type': 'book',
            'title': 'The book',
            'uri': expected_prepared_uris,
        }
        self.assertEqual(
            prepared_work,
            expected_work,
            'Failure to correctly prepare a work as expected.'
        )

    def test__prepare_new_work_adds_canonincal_uris_as_expected(self):
        """Test canonical URIs being added to works."""
        uris = [
            uri for uri in expected_uri_values
            if uri not in canonical_uri_values
        ]

        prepared_work = self.translator._prepare_new_work(
            'book',
            'The book',
            uris,
            canonical_uri_values,
        )
        expected_work = {
            'type': 'book',
            'title': 'The book',
            'uri': expected_prepared_canonical_uris,
        }

        self.assertEqual(
            prepared_work,
            expected_work,
            'Failure to correctly prepare a work as expected.'
        )

    def test__token_client_ecodes_and_decodes_token(self):
        """Test token client processes token."""
        client = new_token_client()
        client.set_token()
        decoded = client.decode_token()
        decoded.pop('exp')
        decoded.pop('iat')

        self.assertEqual(
            decoded,
            expected_decoded_token,
            'Failure to correctly create and decode token.'
        )

    def test__get_token_success_altmetrics(self):
        self.assertEqual(self.altmetrics.token, 'test_token')

    @patch('requests.get')
    def test__get_token_failure_altmetrics(self, mock_get):
        mock_get.return_value.status_code = 401
        mock_get.return_value.content = 'unauthorised'

        with self.assertRaises(ValueError):
            AltmetricsClient(
                email='test.token@testemail.test',
                password='test_pass',
            )

    def test__set_header_altmetrics(self):
        self.altmetrics.token = 'new_token'
        self.altmetrics.set_header()
        self.assertEqual(
            self.altmetrics.header, {'Authorization': 'Bearer new_token'}
        )

    @patch('requests.post')
    def test__register_dois_altmetrics(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.content = (
            b'{"message": "DOIs registered successfully"}'
        )

        status_code, response = self.altmetrics.register_dois(
            [{'doi': 'example_doi'}]
        )

        self.assertEqual(status_code, 201)
        self.assertEqual(
            response.content, b'{"message": "DOIs registered successfully"}'
        )

    @patch('requests.post')
    def test__post_success_altmetrics(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.content = (
            b'{"message": "Metrics posted successfully"}'
        )

        response = self.altmetrics.post(
            'https://example.com/metrics', json={'metric': 'value'}
        )

        self.assertEqual(
            response.content, b'{"message": "Metrics posted successfully"}'
        )
