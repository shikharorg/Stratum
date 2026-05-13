#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE stratum_identity;
    CREATE DATABASE stratum_ingestion;
    CREATE DATABASE stratum_retrieval;
    CREATE DATABASE stratum_workflow;
    CREATE DATABASE stratum_connectors;
    CREATE DATABASE stratum_evaluation;
    CREATE DATABASE stratum_observer;
EOSQL
