#!/bin/bash

# Script to set up AWS Secrets Manager secrets for the application
# Usage: ./setup-secrets.sh

set -e

echo "Setting up AWS Secrets Manager secrets for Incept Multilingual Generation..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "Error: AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

AWS_REGION=${AWS_REGION:-us-east-1}
echo "Using AWS Region: $AWS_REGION"

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region "$AWS_REGION" > /dev/null 2>&1; then
        echo "Updating existing secret: $secret_name"
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION"
    else
        echo "Creating new secret: $secret_name"
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$description" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION"
    fi
}

# Read secrets from environment or prompt
read_secret() {
    local var_name=$1
    local prompt=$2
    local current_value=${!var_name}
    
    if [ -z "$current_value" ]; then
        read -sp "$prompt: " current_value
        echo
    fi
    echo "$current_value"
}

# Load from .env file if it exists
if [ -f "../.env" ]; then
    echo "Loading secrets from .env file..."
    source ../.env
else
    echo "No .env file found, will prompt for values..."
fi

# Get secrets (will use values from .env if loaded)
OPENAI_API_KEY=$(read_secret "OPENAI_API_KEY" "Enter OpenAI API Key")
GEMINI_API_KEY=$(read_secret "GEMINI_API_KEY" "Enter Gemini API Key")
SUPABASE_URL=$(read_secret "SUPABASE_URL" "Enter Supabase URL")
SUPABASE_ANON_KEY=$(read_secret "SUPABASE_ANON_KEY" "Enter Supabase Anon Key")
MONGODB_URI=$(read_secret "MONGODB_URI" "Enter MongoDB Connection URI")
POSTGRES_URI=$(read_secret "POSTGRES_URI" "Enter PostgreSQL Connection URI")
APP_API_KEYS=$(read_secret "APP_API_KEYS" "Enter API Keys (comma-separated)")
HUGGINGFACE_TOKEN=$(read_secret "HUGGINGFACE_TOKEN" "Enter HuggingFace Token")
ANTHROPIC_API_KEY=$(read_secret "ANTHROPIC_API_KEY" "Enter Anthropic API Key")

# Create secrets in AWS Secrets Manager
create_or_update_secret "incept/openai-api-key" "$OPENAI_API_KEY" "OpenAI API Key for Incept"
create_or_update_secret "incept/gemini-api-key" "$GEMINI_API_KEY" "Gemini API Key for Incept"
create_or_update_secret "incept/supabase-url" "$SUPABASE_URL" "Supabase URL for Incept"
create_or_update_secret "incept/supabase-anon-key" "$SUPABASE_ANON_KEY" "Supabase Anon Key for Incept"
create_or_update_secret "incept/mongodb-uri" "$MONGODB_URI" "MongoDB Connection URI for Incept"
create_or_update_secret "incept/postgres-uri" "$POSTGRES_URI" "PostgreSQL Connection URI for Incept"
create_or_update_secret "incept/app-api-keys" "$APP_API_KEYS" "Application API Keys for Incept (comma-separated)"
create_or_update_secret "incept/huggingface-token" "$HUGGINGFACE_TOKEN" "HuggingFace Token for Incept"
create_or_update_secret "incept/anthropic-api-key" "$ANTHROPIC_API_KEY" "Anthropic API Key for Incept"

echo "✅ All secrets have been set up successfully!"
echo ""
echo "Next steps:"
echo "1. Ensure your GitHub repository has the following secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - OPENAI_API_KEY (for tests)"
echo "   - GEMINI_API_KEY (for tests)"
echo ""
echo "2. Run 'terraform init' and 'terraform apply' in the infrastructure directory"
echo "3. Push your code to the main branch to trigger the deployment"