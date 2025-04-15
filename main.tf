# --- Provider Configuration ---
provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Variable Definitions ---
variable "project_id" {
  description = "The Google Cloud project ID."
  type        = string
  # Example: default = "your-gcp-project-id"
}

variable "region" {
  description = "The Google Cloud region for resources like the Cloud SQL instance."
  type        = string
  default     = "us-central1"
}

variable "network_name" {
  description = "The name for the VPC network."
  type        = string
  default     = "cloudsql-vpc"
}

variable "psa_range_name" {
  description = "The name for the allocated IP range for Private Service Access."
  type        = string
  default     = "google-managed-services-range"
}

variable "psa_ip_cidr_range" {
  description = "The IP CIDR range to allocate for Private Service Access (e.g., /24 or /20). MUST NOT overlap with existing subnets."
  type        = string
  default     = "10.100.0.0/24" # Example range - ensure it's free in your VPC address space
}

variable "sql_instance_name" {
  description = "Name for the Cloud SQL instance."
  type        = string
  default     = "corporate-analyst-instance"
}

variable "sql_database_version" {
  description = "Database version for the Cloud SQL instance."
  type        = string
  default     = "POSTGRES_15" # Ensure this is a PostgreSQL version
}

variable "sql_tier" {
  description = "Machine type for the Cloud SQL instance."
  type        = string
  default     = "db-f1-micro" # Use a small tier for example purposes
}

variable "sql_db_name" {
  description = "Name for the PostgreSQL database to be created."
  type        = string
  default     = "corporate-analyst-db"
}

variable "sql_db_user" {
  description = "Username for the PostgreSQL database user."
  type        = string
  default     = "corporate-analyst-user"
}

variable "allowed_source_cidr" {
  description = "CIDR range allowed to connect to the database (e.g., your application subnet or 0.0.0.0/0 for testing - not recommended)."
  type        = string
  default     = "10.0.0.0/8" # Example: Allows common private ranges. Adjust for your specific application sources.
}

variable "db_pass" {
  description = "The password for the database user."
  type        = string
  sensitive   = true
}

# variable "env_file_path" {
#   description = "Path to the .env file"
#   type        = string
#   default     = "/usr/local/google/home/veermuchandi/code/agents/corporate_agent/corporate_analyst/.env"
# }

# Use derived variable for port based on database type
locals {
  sql_db_port = var.sql_database_version == "POSTGRES_15" ? "5432" : (var.sql_database_version == "MYSQL_8_0" ? "3306" : "1433") # Basic logic, extend if needed
  env_file_path = "${path.cwd}/.env"
}

# --- Enable Necessary APIs ---
resource "google_project_service" "compute_api" {
  project            = var.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin_api" {
  project            = var.project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "servicenetworking_api" {
  project            = var.project_id
  service            = "servicenetworking.googleapis.com"
  disable_on_destroy = false
  # Ensure this API is enabled before attempting the connection
  depends_on = [google_project_service.compute_api]
}

# --- VPC Network ---
resource "google_compute_network" "main" {
  project                 = var.project_id
  name                    = var.network_name
  auto_create_subnetworks = true # Set to false for custom subnet mode
  depends_on              = [google_project_service.compute_api]
}

# --- Private Service Access Setup ---

# 1. Reserve an IP Range for Google Services
resource "google_compute_global_address" "private_ip_alloc" {
  project       = var.project_id
  name          = var.psa_range_name
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  ip_version    = "IPV4"
  prefix_length = tonumber(split("/", var.psa_ip_cidr_range)[1])
  network       = google_compute_network.main.id
  address       = split("/", var.psa_ip_cidr_range)[0]

  depends_on = [google_project_service.compute_api]
}

# 2. Create the Private Service Connection (VPC Peering)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]

  depends_on = [
    google_project_service.servicenetworking_api,
    google_compute_global_address.private_ip_alloc
  ]
}

# --- Cloud SQL Instance using Private IP ---
resource "google_sql_database_instance" "main" {
  project             = var.project_id
  name                = var.sql_instance_name
  region              = var.region
  database_version    = var.sql_database_version
  deletion_protection = false # Set to true for production environments

  settings {
    tier = var.sql_tier
    ip_configuration {
      ipv4_enabled    = false # Disable public IP
      private_network = google_compute_network.main.id
    }
    #require_ssl = true
    backup_configuration {
      enabled = false # Disable backups for example speed
    }
    # Availability type (zonal/regional) - default is zonal
    # availability_type = "REGIONAL"
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# --- Cloud SQL Database ---
resource "google_sql_database" "main_db" {
  project  = var.project_id
  name     = var.sql_db_name
  instance = google_sql_database_instance.main.name
  charset  = "UTF8" # Optional: specify charset
  # collation = "en_US.UTF8" # Optional: specify collation for PostgreSQL

  depends_on = [google_sql_database_instance.main]
}

# --- Cloud SQL User ---
resource "google_sql_user" "db_user" {
  project  = var.project_id
  name     = var.sql_db_user
  instance = google_sql_database_instance.main.name
  password_wo = var.db_pass

  depends_on = [google_sql_database_instance.main]
}

# --- Execute SQL to Create Tables ---
# Uses a null_resource with local-exec to run gcloud sql connect.
# WARNING: This requires 'gcloud' and 'psql' (implicitly used by gcloud sql connect for postgres)
#          to be installed and authenticated on the machine running Terraform.
#          It also requires network connectivity or the Cloud SQL Auth Proxy
#          to be implicitly handled by 'gcloud sql connect'.
resource "null_resource" "create_tables" {
  # Triggers ensure this runs when the referenced resources change.
  triggers = {
    instance_name = google_sql_database_instance.main.name
    db_name       = google_sql_database.main_db.name
    db_user       = google_sql_user.db_user.name
    project_id    = var.project_id
  }

  # Ensure the database and user exist before attempting connection
  depends_on = [
    google_sql_database.main_db,
    google_sql_user.db_user
  ]

  provisioner "local-exec" {
    # Use bash -c for better handling of complex commands and heredoc
    interpreter = ["bash", "-c"]

    # Use heredoc for the SQL command for readability and escaping
    # gcloud sql connect implicitly handles authentication and proxy if needed.
    # We pipe the SQL command to the gcloud connect command.
    command = <<-EOT
      echo "Attempting to connect to instance '${self.triggers.instance_name}' database '${self.triggers.db_name}' as user '${self.triggers.db_user}'..."

      # Check if the database is ready for connections
      pg_isready -h $(gcloud sql instances describe "${self.triggers.instance_name}" --project="${self.triggers.project_id}" --format="value(ipAddresses[0].ipAddress)") -p ${local.sql_db_port} -U "${self.triggers.db_user}"

      if [ $? -eq 0 ]; then
        echo "Database is ready for connections."
      else
        echo "Database is not ready. Exiting."
        exit 1
      fi

      # Define the SQL command using heredoc
      SQL_COMMAND=$(cat <<EOF
        CREATE TABLE IF NOT EXISTS sec_filings (
            url TEXT PRIMARY KEY,
            text_report TEXT,
            ticker TEXT,
            date_of_report DATE,
            date_of_download DATE
        );
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE sec_filings TO "${self.triggers.db_user}";

        CREATE TABLE IF NOT EXISTS zoominfo_enrichments (
            ticker TEXT PRIMARY KEY,
            company_domain TEXT,
            company_enrichment_data JSONB,
            last_update_date DATE
        );
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE zoominfo_enrichments TO "${self.triggers.db_user}";

        CREATE TABLE IF NOT EXISTS nubela_enrichments (
            ticker VARCHAR(255) PRIMARY KEY,
            linkedin_company_profile TEXT,
            company_domain TEXT,
            company_name TEXT,
            nubela_enrichment_data JSONB,
            last_update_date DATE
        );
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE nubela_enrichments TO "${self.triggers.db_user}";
EOF
      )

      # Execute using gcloud sql connect, piping the SQL command
      # Use PGPASSWORD environment variable for non-interactive password supply with psql (invoked by gcloud)
      export PGPASSWORD='${var.db_pass}'

      echo "$SQL_COMMAND" | gcloud sql connect "${self.triggers.instance_name}" \
        --user="${self.triggers.db_user}" \
        --database="${self.triggers.db_name}" \
        --project="${self.triggers.project_id}" \
        --quiet # Suppress interactive prompts

      # Unset password immediately after use
      unset PGPASSWORD

      echo "SQL execution attempt finished."
    EOT
  }
}


# --- Firewall Rule to Allow Access TO Cloud SQL ---
resource "google_compute_firewall" "allow_sql_ingress" {
  project     = var.project_id
  name        = "${var.network_name}-allow-sql-ingress"
  network     = google_compute_network.main.id
  direction   = "INGRESS"
  priority    = 1000

  allow {
    protocol = "tcp"
    ports    = [local.sql_db_port] # Use the correct port (dynamically determined)
  }

  source_ranges      = [var.allowed_source_cidr]
  destination_ranges = [google_sql_database_instance.main.private_ip_address] # Target traffic TO the private IP of the instance

  depends_on = [
    google_compute_network.main,
    google_compute_global_address.private_ip_alloc
  ]
}



# --- Outputs ---
output "cloud_sql_instance_private_ip" {
  description = "The private IP address of the Cloud SQL instance."
  value       = google_sql_database_instance.main.private_ip_address
  sensitive   = true
}

output "cloud_sql_instance_connection_name" {
  description = "The connection name of the Cloud SQL instance (used by proxies)."
  value       = google_sql_database_instance.main.connection_name
}

output "vpc_network_name" {
  description = "Name of the created VPC network."
  value       = google_compute_network.main.name
}

output "psa_allocated_range" {
  description = "The CIDR block allocated for Private Service Access."
  value       = google_compute_global_address.private_ip_alloc.address
}

output "database_name" {
  description = "Name of the PostgreSQL database created."
  value       = google_sql_database.main_db.name
}

output "database_user" {
  description = "Username created for the PostgreSQL database."
  value       = google_sql_user.db_user.name
}
