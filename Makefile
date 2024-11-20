LAMBDA_DIR=lambda
ZIP_FILE=lambda.zip
TERRAFORM_DIR=tf

all: zip_lambda deploy_terraform

# Step 1: Zip Lambda function code
zip_lambda:
	@echo "Zipping Lambda function code..."
	cd $(LAMBDA_DIR) && zip -r $(ZIP_FILE) *.py python/ && cd ..

# Step 2: Run Terraform
deploy_terraform: zip_lambda
	@echo "Running Terraform..."
	cd $(TERRAFORM_DIR) && terraform init && terraform plan -out=tfplan && terraform apply tfplan

# Step 3: Clean up
clean:
	@echo "Cleaning up..."
	rm -f $(ZIP_FILE)