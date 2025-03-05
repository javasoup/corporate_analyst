"""Tool that downloads 10k report for a corporation."""

import os
import PyPDF2
import requests


def get_10k_report_link(ticker: str) -> str:
  """Downloads a 10-K report from the SEC API.

  Args:
      ticker: The company's ticker symbol

  Returns:
      The URL for the 10-K report or None if there's an error.
      Prints error information if the API call is not successful.
  """
  api_key = os.environ.get("SEC_API_KEY")
  url = f"https://api.sec-api.io?token={api_key}"

  payload = {
      "query": f'ticker:({ticker}) AND formType:"10-K"',
      "from": "0",
      "size": "1",
      "sort": [{"filedAt": {"order": "desc"}}],
  }

  headers = {"Content-Type": "application/json"}

  try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return extract_link_to_filing_details(response.json())

  except requests.exceptions.RequestException as e:
    print(f"Error during API call: {e}")
    return None
  except AttributeError:
    print("No response received from the API.")
    return None


def extract_link_to_filing_details(report_data):
  """Extracts the link to the filing details from the 10-K report data.

  Args:
      report_data: The data returned from the SEC API for the 10-K report.

  Returns:
      The link to the filing details or None if it's not found.
  """
  if report_data and report_data.get("total"):
    filings = report_data.get("filings", [])
    if filings:
      filing_details_link = filings[0].get("linkToFilingDetails")
      if filing_details_link:
        return filing_details_link
      else:
        print("linkToFilingDetails not found in the response.")
    else:
      print("No filings found in the response.")
  else:
    print("No 10-K reports found within the specified criteria.")
  return None


def download_sec_filing(url: str, filename: str) -> str:
  """Downloads a SEC filing from the provided URL.

  Args:
      url: The URL of the SEC filing.
      filename: The name of the file to download (should end in .pdf)

  Returns:
      The extracted text from the downloaded SEC filing and converted to text.
  """
  api_key = os.environ.get("SEC_API_KEY")
  download_url = (
      f"https://api.sec-api.io/filing-reader?token={api_key}&url={url}"
  )

  try:
    response = requests.get(download_url, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes

    if response.headers["Content-Type"] == "application/pdf":
      with open(filename, "wb") as pdf_file:
        for chunk in response.iter_content(chunk_size=8192):
          pdf_file.write(chunk)
      print(f"File '{filename}' downloaded successfully.")
      text_report = extract_text_from_pdf(filename)
      os.remove(filename)
      return text_report
    else:
      print(
          "The file at the given URL is not a PDF. Content-Type:"
          f" {response.headers['Content-Type']}"
      )

  except requests.exceptions.RequestException as e:
    print(f"Error downloading file: {e}")


def extract_text_from_pdf(pdf_path: str) -> str:
  """Extracts text from a PDF file.

  Args:
      pdf_path: The path to the PDF file.

  Returns:
      The extracted text from the PDF file or None if there's an error.
  """
  try:
    with open(pdf_path, "rb") as pdf_file:
      pdf_reader = PyPDF2.PdfReader(pdf_file)
      text = ""
      for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
      return text
  except FileNotFoundError:
    print(f"Error: PDF file not found at '{pdf_path}'")
    return None
  except PyPDF2.errors.PdfReadError:
    print(f"Error: Could not read PDF file at '{pdf_path}'")
    return None
