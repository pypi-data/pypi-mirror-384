import pytest
import asyncio
from linkaudit import linkaudit 
import pprint  # pretty print

@pytest.mark.asyncio
async def test_url_status_client_error():
    """Tests the status of multiple URLs """
    expected_results = [
        ("https://nocomplexity.com ", 200),
        ("https://nocomplexity.com/smurfen ", 'HTTP Error: 404 Not Found'),
        ("https://smurf.nocomplexity.com", 'HTTP Error: 500 Internal Server Error'),
        ("https://bm-support.org", 200),
        ("https://www.organisatieontwerp.nl", 200) # Added a real url
    ]
    

    urls = [url for url, _ in expected_results]
    actual_results = await linkaudit.process_multiple_urlchecks(urls)
    
    print('Result of test run:')
    pprint.pp(actual_results)

    # Reformat actual results to match expected format
    actual_results_formatted = [(url, status) for url, status in actual_results]
    

    for expected, actual in zip(expected_results, actual_results_formatted):
        assert expected == actual
