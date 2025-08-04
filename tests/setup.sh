#!/bin/bash
# Setup script to make all test scripts executable
# Run this once after cloning the repository in WSL2

echo "🔧 Setting up Price Tracker testing environment..."

# Make all test scripts executable
chmod +x tests/*.sh
chmod +x scripts/*.sh
chmod +x docs/*.sh

echo "✅ Test scripts are now executable"
echo ""

echo "⚠️  IMPORTANT: Create secrets before deploying!"
echo "   Run: ./docs/secrets-reference.sh"
echo "   Or see: docs/SECRETS.md for complete guide"
echo ""

echo "📋 Available test commands:"
echo "   ./tests/run-tests.sh              # Run all tests"
echo "   ./tests/run-tests.sh wsl2         # Test WSL2 environment only"
echo "   ./tests/run-tests.sh --skip-deploy # Test without requiring deployment"
echo "   ./tests/test-infrastructure.sh    # Test infrastructure directly"
echo ""

echo "🚀 Deployment workflow:"
echo "   1. Create secrets: ./docs/secrets-reference.sh"
echo "   2. Deploy: ./scripts/deploy.sh"
echo "   3. Test: ./tests/run-tests.sh"
echo ""

echo "✅ Setup complete! Ready for Price Tracker development."
