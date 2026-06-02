#!/bin/bash
# Wrapper script to run indexing with all environment variables
cd /home/judicandus/kolibri_ai
export ALIBABA_API_KEY="sk-236f8f3579c74c138c09f037210231ce"
export DATABASE_URL="postgresql://kolibri_ai:KolibriAI2024Secure!@localhost:5432/kolibri_ai"

echo "Starting indexing at $(date)" >> indexing_final.log
python3 -u scripts/index_to_postgres_local.py >> indexing_final.log 2>&1
echo "Finished indexing at $(date)" >> indexing_final.log
