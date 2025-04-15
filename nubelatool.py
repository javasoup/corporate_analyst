"""Tool that pulls corporate information from LinkedIn using Proxycurl API."""

import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
import requests
import sqlalchemy
from datetime import date, timedelta


class NubelaTool:
    """
    A class to handle LinkedIn data enrichment using Proxycurl API.
    """

    def __init__(self):
        """
        Initializes the NubelaTool, including logging and database connection pool.
        """
        load_dotenv()  # Load environment variables from .env file
        self._init_logging()
        self.proxycurl_api_key = os.environ.get("PROXYCURL_API_KEY")
        if not self.proxycurl_api_key:
            self.logger.error("PROXYCURL_API_KEY environment variable not set.")
        self.db_pool = None
        self._init_db_pool()
        self.enrichment_data_timelimit = int(os.environ.get("NUBELA_ENRICHMENT_DATA_TIMELIMIT", "60"))
        self.enable_nubela_api = os.getenv("ENABLE_NUBELA_API_CALLS", "false").lower() == "true"

    def _init_logging(self):
        """
        Initializes logging for the NubelaTool.
        """
        logging.basicConfig(
            level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Add a StreamHandler to send log messages to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # Set the level for the console handler
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _init_db_pool(self):
        """
        Initializes the database connection pool using Cloud SQL Python Connector.
        """
        if self.db_pool is None:
            db_user = os.environ["DB_USER"]
            db_pass = os.environ["DB_PASS"]
            db_name = os.environ["DB_NAME"]
            db_connection_name = os.environ[
                "DB_CONNECTION_NAME"
            ]  # e.g., project:region:instance

            self.logger.debug(f"db_connection_name: {db_connection_name}")
            

            from google.cloud.sql.connector import Connector

            def getconn():
                """Creates a connection to the database using the Cloud SQL Python Connector."""
                connector = Connector()
                conn = connector.connect(
                    db_connection_name,
                    "pg8000",
                    user=db_user,
                    password=db_pass,
                    db=db_name,
                )
                return conn

            self.db_pool = sqlalchemy.create_engine(
                "postgresql+pg8000://",  # Use pg8000 in the connection string
                creator=getconn,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
            )
            self.logger.info(
                "Database connection pool initialized using Cloud SQL Connector."
            )

    def _get_db_pool(self):
        """
        Returns the database connection pool.
        """
        if self.db_pool is None:
            self._init_db_pool()
        return self.db_pool

    def enrich_linkedin_company(
        self, linkedin_company_profile: str, company_domain: str, company_name: str, ticker: str
    ) -> Optional[str]:
        """
        Enriches company data from LinkedIn using Proxycurl API or retrieves it from the database.

        Args:
            linkedin_company_profile: The LinkedIn company profile URL.
            company_domain: The company's domain name.
            company_name: The name of the company.
            ticker: The ticker symbol of the company.

        Returns:
            Enriched information about the company from LinkedIn in JSON format as a string or None if an error occurs.
        """
        self.logger.debug(
            f"enrich_linkedin_company called with linkedin_company_profile: {linkedin_company_profile}, company_domain: {company_domain}, company_name: {company_name}, ticker: {ticker}"
        )
        
        # Check if Nubela API calls are enabled
        if not self.enable_nubela_api:
            self.logger.info("Nubela API calls are disabled. Using only database data.")

        db_pool = self._get_db_pool()
        with db_pool.connect() as db_conn:
            # Check if the report already exists in the database
            result = db_conn.execute(
                sqlalchemy.text(
                    "SELECT nubela_enrichment_data, last_update_date FROM nubela_enrichments WHERE ticker = :ticker"
                ),
                {"ticker": ticker},
            ).fetchone()

            if result:
                nubela_enrichment_data, last_update_date = result
                if (
                    last_update_date
                    and date.today() - last_update_date
                    < timedelta(days=self.enrichment_data_timelimit)
                ):
                    self.logger.info(
                        f"Enrichment data for company ticker '{ticker}' found in the database and is recent."
                    )
                    # Ensure nubela_enrichment_data is a string before loading
                    if isinstance(nubela_enrichment_data, str):
                        return nubela_enrichment_data  # Return the nubela_enrichment_data from the database
                    else:
                        self.logger.error(f"Data from database is not a string: {type(nubela_enrichment_data)}")
                        return None
                elif not self.enable_nubela_api:
                    self.logger.info(
                        f"Enrichment data for company ticker '{ticker}' found in the database but Nubela API calls are disabled."
                    )
                    if isinstance(nubela_enrichment_data, str):
                        return nubela_enrichment_data
                    else:
                        self.logger.error(f"Data from database is not a string: {type(nubela_enrichment_data)}")
                        return None
                else:
                    self.logger.info(
                        f"Enrichment data for company ticker '{ticker}' found in the database but is older than {self.enrichment_data_timelimit} days. Refreshing..."
                    )
                    # Delete the old record
                    db_conn.execute(
                        sqlalchemy.text(
                            "DELETE FROM nubela_enrichments WHERE ticker = :ticker"
                        ),
                        {"ticker": ticker},
                    )
                    db_conn.commit()

            # If not in the database or the report is too old, download and process the report
            # Check if Nubela API calls are enabled
            if not self.enable_nubela_api:
                return None
            
            if not self.proxycurl_api_key:
                self.logger.error("Cannot enrich LinkedIn data: PROXYCURL_API_KEY not set.")
                return None

            headers = {"Authorization": "Bearer " + self.proxycurl_api_key}
            api_endpoint = "https://nubela.co/proxycurl/api/linkedin/company"
            params = {
                "url": linkedin_company_profile,
                "categories": "include",
                "funding_data": "include",
                "exit_data": "include",
                "acquisitions": "include",
                "extra": "include",
                "use_cache": "if-present",
                "fallback_to_cache": "on-error",
            }
            try:
                response = requests.get(api_endpoint, params=params, headers=headers)
                response.raise_for_status()
                retval = json.loads(json.dumps(json.loads(response.text)))

                # Check and see if we could load the company. If not, then let's go ahead and search for it by domain
                if retval.get("code", None) is not None:
                    # Try and look up the company
                    self.logger.info(f"Could not find company using linkedin profile {linkedin_company_profile}. Trying to find it by domain {company_domain}")
                    api_endpoint = "https://nubela.co/proxycurl/api/linkedin/company/resolve"
                    params = {
                        "company_domain": company_domain,
                        "company_name": company_name,
                        "enrich_profile": "enrich",
                    }
                    response = requests.get(api_endpoint, params=params, headers=headers)
                    response.raise_for_status()
                    retval = json.loads(json.dumps(json.loads(response.text)))
                else:
                    if "similar_companies" in retval:
                        del retval["similar_companies"]
                    if "updates" in retval:
                        del retval["updates"]
                    if "exit_data" in retval:
                        del retval["exit_data"]
                    if "affiliated_companies" in retval:
                        del retval["affiliated_companies"]
                    if "acquisitions" in retval:
                        del retval["acquisitions"]

                # Check for error code on return if no error then return
                if retval.get("code", None) is not None:
                    self.logger.error(f"Could not enrich or find the company from Proxy Curl. Error: {retval.get('code', '')}")
                    return json.dumps({
                        "status": "error",
                        "message": "Could not enrich or find the company from Proxy Curl. Error:"
                        + str(retval.get("code", "")),
                    })
                
                last_update_date = date.today()
                db_conn.execute(
                    sqlalchemy.text(
                        "INSERT INTO nubela_enrichments (ticker, linkedin_company_profile, company_domain, company_name, nubela_enrichment_data, last_update_date) VALUES (:ticker, :linkedin_company_profile, :company_domain, :company_name, :nubela_enrichment_data, :last_update_date) ON CONFLICT (ticker) DO UPDATE SET nubela_enrichment_data = :nubela_enrichment_data, linkedin_company_profile = :linkedin_company_profile, company_domain = :company_domain, company_name = :company_name, last_update_date = :last_update_date"
                    ),
                    {
                        "ticker": ticker,
                        "linkedin_company_profile": linkedin_company_profile,
                        "company_domain": company_domain,
                        "company_name": company_name,
                        "nubela_enrichment_data": json.dumps(retval),
                        "last_update_date": last_update_date,
                    },
                )
                db_conn.commit()
                self.logger.info(
                    f"Enrichment data for company ticker '{ticker}' saved to the database."
                )

                return json.dumps(retval)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error during Proxycurl API call: {e}")
                return json.dumps({
                    "status": "error",
                    "message": "Could not enrich this company from linkedin:" + str(e),
                })
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON from Proxycurl API: {e}")
                return json.dumps({
                    "status": "error",
                    "message": "Could not decode JSON from Proxycurl API:" + str(e),
                })
            except Exception as e:
                self.logger.error(f"An unexpected error occurred: {e}")
                return json.dumps({
                    "status": "error",
                    "message": "An unexpected error occurred:" + str(e),
                })


# Example usage (for testing):
if __name__ == "__main__":
    nubela_tool = NubelaTool()
    linkedin_company_profile = "https://www.linkedin.com/company/google/"
    company_domain = "www.google.com"
    company_name = "Google"
    ticker = "GOOG"
    result = nubela_tool.enrich_linkedin_company(
        linkedin_company_profile, company_domain, company_name, ticker
    )
    print(result)
