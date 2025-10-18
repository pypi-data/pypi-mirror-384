#!/usr/bin/env python3
"""
DcisionAI MCP Server - Setup Validation Script
==============================================

Comprehensive validation of the MCP server setup to ensure
seamless customer experience with zero dependency issues.
"""

import os
import sys
import subprocess
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class SetupValidator:
    """Validates the complete DcisionAI MCP Server setup."""
    
    def __init__(self):
        self.results = {
            'system_requirements': {},
            'python_environment': {},
            'dependencies': {},
            'configuration': {},
            'aws_credentials': {},
            'agentcore_connection': {},
            'mcp_server': {},
            'ide_integration': {},
            'docker_setup': {},
            'cloud_deployment': {}
        }
        self.overall_status = True
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.WHITE}{title.center(60)}{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
    
    def print_status(self, message: str, status: str = "INFO"):
        """Print a status message with color coding."""
        color = Colors.BLUE
        if status == "SUCCESS":
            color = Colors.GREEN
        elif status == "WARNING":
            color = Colors.YELLOW
        elif status == "ERROR":
            color = Colors.RED
        
        print(f"{color}[{status}]{Colors.NC} {message}")
    
    def run_command(self, command: str, capture_output: bool = True) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            if capture_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                return result.returncode == 0, result.stdout + result.stderr
            else:
                result = subprocess.run(command, shell=True, timeout=30)
                return result.returncode == 0, ""
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_system_requirements(self):
        """Check system requirements."""
        self.print_header("SYSTEM REQUIREMENTS")
        
        # Check OS
        import platform
        os_name = platform.system()
        os_version = platform.release()
        self.print_status(f"Operating System: {os_name} {os_version}")
        self.results['system_requirements']['os'] = f"{os_name} {os_version}"
        
        # Check Python version
        python_version = sys.version
        self.print_status(f"Python Version: {python_version}")
        self.results['system_requirements']['python'] = python_version
        
        # Check available memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            self.print_status(f"Available Memory: {memory_gb:.1f} GB")
            self.results['system_requirements']['memory'] = f"{memory_gb:.1f} GB"
        except ImportError:
            self.print_status("psutil not available - cannot check memory", "WARNING")
        
        # Check disk space
        try:
            disk_usage = os.statvfs('.')
            free_space_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**3)
            self.print_status(f"Available Disk Space: {free_space_gb:.1f} GB")
            self.results['system_requirements']['disk_space'] = f"{free_space_gb:.1f} GB"
        except Exception as e:
            self.print_status(f"Cannot check disk space: {e}", "WARNING")
    
    def check_python_environment(self):
        """Check Python environment setup."""
        self.print_header("PYTHON ENVIRONMENT")
        
        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if in_venv:
            self.print_status("✅ Running in virtual environment", "SUCCESS")
        else:
            self.print_status("⚠️ Not running in virtual environment", "WARNING")
        
        self.results['python_environment']['virtual_env'] = in_venv
        
        # Check Python path
        python_path = sys.executable
        self.print_status(f"Python Executable: {python_path}")
        self.results['python_environment']['executable'] = python_path
        
        # Check pip
        success, output = self.run_command("pip --version")
        if success:
            self.print_status(f"✅ pip available: {output.strip()}", "SUCCESS")
        else:
            self.print_status("❌ pip not available", "ERROR")
            self.overall_status = False
        
        self.results['python_environment']['pip'] = success
    
    def check_dependencies(self):
        """Check required dependencies."""
        self.print_header("DEPENDENCIES")
        
        required_packages = [
            'fastmcp', 'uvicorn', 'boto3', 'python-dotenv', 
            'pyyaml', 'click', 'requests', 'pydantic', 'typing_extensions'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                # Handle special cases for package names
                import_name = package.replace('-', '_')
                if package == 'python-dotenv':
                    import_name = 'dotenv'
                elif package == 'pyyaml':
                    import_name = 'yaml'
                elif package == 'typing_extensions':
                    import_name = 'typing_extensions'
                
                __import__(import_name)
                self.print_status(f"✅ {package}", "SUCCESS")
                self.results['dependencies'][package] = True
            except ImportError:
                self.print_status(f"❌ {package} - Missing", "ERROR")
                self.results['dependencies'][package] = False
                missing_packages.append(package)
                self.overall_status = False
        
        if missing_packages:
            self.print_status(f"Missing packages: {', '.join(missing_packages)}", "ERROR")
            self.print_status("Run: pip install -e . to install missing dependencies", "INFO")
    
    def check_configuration(self):
        """Check configuration files."""
        self.print_header("CONFIGURATION")
        
        # Check for .env file
        env_file = Path('.env')
        if env_file.exists():
            self.print_status("✅ .env file found", "SUCCESS")
            self.results['configuration']['env_file'] = True
            
            # Check required environment variables
            required_vars = [
                'DCISIONAI_ACCESS_TOKEN',
                'DCISIONAI_GATEWAY_URL',
                'DCISIONAI_GATEWAY_TARGET'
            ]
            
            missing_vars = []
            for var in required_vars:
                if os.getenv(var):
                    self.print_status(f"✅ {var} is set", "SUCCESS")
                else:
                    self.print_status(f"❌ {var} is not set", "ERROR")
                    missing_vars.append(var)
                    self.overall_status = False
            
            if missing_vars:
                self.print_status(f"Missing environment variables: {', '.join(missing_vars)}", "ERROR")
        else:
            self.print_status("❌ .env file not found", "ERROR")
            self.print_status("Copy env.example to .env and fill in your credentials", "INFO")
            self.results['configuration']['env_file'] = False
            self.overall_status = False
    
    def check_aws_credentials(self):
        """Check AWS credentials."""
        self.print_header("AWS CREDENTIALS")
        
        try:
            import boto3
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            
            self.print_status("✅ AWS credentials valid", "SUCCESS")
            self.print_status(f"Account ID: {identity['Account']}")
            self.print_status(f"User ARN: {identity['Arn']}")
            
            self.results['aws_credentials']['valid'] = True
            self.results['aws_credentials']['account_id'] = identity['Account']
            
        except Exception as e:
            self.print_status(f"❌ AWS credentials error: {e}", "ERROR")
            self.results['aws_credentials']['valid'] = False
            self.overall_status = False
    
    def check_agentcore_connection(self):
        """Check AgentCore Gateway connection."""
        self.print_header("AGENTCORE GATEWAY CONNECTION")
        
        gateway_url = os.getenv('DCISIONAI_GATEWAY_URL')
        access_token = os.getenv('DCISIONAI_ACCESS_TOKEN')
        
        if not gateway_url or not access_token:
            self.print_status("❌ Gateway URL or access token not configured", "ERROR")
            self.results['agentcore_connection']['configured'] = False
            self.overall_status = False
            return
        
        try:
            import httpx
            
            response = httpx.post(
                f"{gateway_url}/mcp",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"method": "ping"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                self.print_status("✅ AgentCore Gateway connection successful", "SUCCESS")
                self.results['agentcore_connection']['connected'] = True
            else:
                self.print_status(f"❌ Gateway connection failed: {response.status_code}", "ERROR")
                self.results['agentcore_connection']['connected'] = False
                self.overall_status = False
                
        except Exception as e:
            self.print_status(f"❌ Gateway connection error: {e}", "ERROR")
            self.results['agentcore_connection']['connected'] = False
            self.overall_status = False
    
    def check_mcp_server(self):
        """Check MCP server functionality."""
        self.print_header("MCP SERVER FUNCTIONALITY")
        
        try:
            # Test CLI commands
            success, output = self.run_command("dcisionai-mcp-server --help")
            if success:
                self.print_status("✅ MCP server CLI available", "SUCCESS")
                self.results['mcp_server']['cli'] = True
            else:
                self.print_status("❌ MCP server CLI not available", "ERROR")
                self.results['mcp_server']['cli'] = False
                self.overall_status = False
                return
            
            # Test health check
            success, output = self.run_command("dcisionai-mcp-server health-check")
            if success and "All health checks passed" in output:
                self.print_status("✅ MCP server health check passed", "SUCCESS")
                self.results['mcp_server']['health_check'] = True
            else:
                self.print_status("❌ MCP server health check failed", "ERROR")
                self.print_status(f"Output: {output}", "INFO")
                self.results['mcp_server']['health_check'] = False
                self.overall_status = False
            
            # Test workflow listing
            success, output = self.run_command("dcisionai-mcp-server list-workflows")
            if success and "Total Workflows:" in output:
                self.print_status("✅ Workflow templates loaded", "SUCCESS")
                self.results['mcp_server']['workflows'] = True
            else:
                self.print_status("❌ Workflow templates not loaded", "ERROR")
                self.results['mcp_server']['workflows'] = False
                self.overall_status = False
                
        except Exception as e:
            self.print_status(f"❌ MCP server check error: {e}", "ERROR")
            self.overall_status = False
    
    def check_ide_integration(self):
        """Check IDE integration setup."""
        self.print_header("IDE INTEGRATION")
        
        # Check Cursor integration
        cursor_config = Path.home() / '.cursor' / 'mcp.json'
        if cursor_config.exists():
            self.print_status("✅ Cursor MCP configuration found", "SUCCESS")
            self.results['ide_integration']['cursor'] = True
        else:
            self.print_status("⚠️ Cursor MCP configuration not found", "WARNING")
            self.results['ide_integration']['cursor'] = False
        
        # Check VS Code integration
        vscode_config = Path.home() / '.vscode' / 'settings.json'
        if vscode_config.exists():
            try:
                with open(vscode_config, 'r') as f:
                    settings = json.load(f)
                    if 'mcp.servers' in settings:
                        self.print_status("✅ VS Code MCP configuration found", "SUCCESS")
                        self.results['ide_integration']['vscode'] = True
                    else:
                        self.print_status("ℹ️ VS Code MCP configuration not found (optional)", "INFO")
                        self.results['ide_integration']['vscode'] = False
            except Exception:
                self.print_status("ℹ️ VS Code settings.json not readable (optional)", "INFO")
                self.results['ide_integration']['vscode'] = False
        else:
            self.print_status("ℹ️ VS Code settings.json not found (optional)", "INFO")
            self.results['ide_integration']['vscode'] = False
    
    def check_docker_setup(self):
        """Check Docker setup."""
        self.print_header("DOCKER SETUP")
        
        # Check Docker installation
        success, output = self.run_command("docker --version")
        if success:
            self.print_status(f"✅ Docker available: {output.strip()}", "SUCCESS")
            self.results['docker_setup']['installed'] = True
            
            # Check Docker daemon
            success, output = self.run_command("docker info")
            if success:
                self.print_status("✅ Docker daemon running", "SUCCESS")
                self.results['docker_setup']['daemon'] = True
            else:
                self.print_status("⚠️ Docker daemon not running (start Docker Desktop)", "WARNING")
                self.results['docker_setup']['daemon'] = False
                # Don't fail overall validation for Docker daemon not running
        else:
            self.print_status("❌ Docker not installed", "ERROR")
            self.results['docker_setup']['installed'] = False
            self.overall_status = False
        
        # Check Docker Compose
        success, output = self.run_command("docker-compose --version")
        if success:
            self.print_status(f"✅ Docker Compose available: {output.strip()}", "SUCCESS")
            self.results['docker_setup']['compose'] = True
        else:
            self.print_status("⚠️ Docker Compose not available", "WARNING")
            self.results['docker_setup']['compose'] = False
    
    def check_cloud_deployment(self):
        """Check cloud deployment readiness."""
        self.print_header("CLOUD DEPLOYMENT READINESS")
        
        # Check AWS CLI
        success, output = self.run_command("aws --version")
        if success:
            self.print_status(f"✅ AWS CLI available: {output.strip()}", "SUCCESS")
            self.results['cloud_deployment']['aws_cli'] = True
        else:
            self.print_status("❌ AWS CLI not available", "ERROR")
            self.results['cloud_deployment']['aws_cli'] = False
            self.overall_status = False
        
        # Check deployment scripts
        deploy_script = Path('deploy/aws-deploy.sh')
        if deploy_script.exists():
            self.print_status("✅ AWS deployment script found", "SUCCESS")
            self.results['cloud_deployment']['deploy_script'] = True
        else:
            self.print_status("❌ AWS deployment script not found", "ERROR")
            self.results['cloud_deployment']['deploy_script'] = False
            self.overall_status = False
    
    def generate_report(self):
        """Generate a comprehensive validation report."""
        self.print_header("VALIDATION REPORT")
        
        total_checks = 0
        passed_checks = 0
        
        for category, checks in self.results.items():
            for check, result in checks.items():
                total_checks += 1
                if result is True:
                    passed_checks += 1
        
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"\n{Colors.WHITE}Overall Status: {Colors.NC}", end="")
        if self.overall_status:
            print(f"{Colors.GREEN}✅ READY FOR PRODUCTION{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ SETUP INCOMPLETE{Colors.NC}")
        
        print(f"{Colors.WHITE}Success Rate: {Colors.NC}{success_rate:.1f}% ({passed_checks}/{total_checks})")
        
        # Save detailed report
        report_file = Path('validation-report.json')
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'overall_status': self.overall_status,
                'success_rate': success_rate,
                'results': self.results
            }, f, indent=2)
        
        self.print_status(f"Detailed report saved to: {report_file}")
        
        # Provide recommendations
        if not self.overall_status:
            self.print_header("RECOMMENDATIONS")
            self.print_status("To complete the setup, please:")
            
            if not self.results['dependencies'].get('fastmcp', True):
                self.print_status("1. Install missing dependencies: pip install -e .")
            
            if not self.results['configuration'].get('env_file', False):
                self.print_status("2. Create .env file with your credentials")
            
            if not self.results['aws_credentials'].get('valid', False):
                self.print_status("3. Configure AWS credentials: aws configure")
            
            if not self.results['agentcore_connection'].get('connected', False):
                self.print_status("4. Verify AgentCore Gateway URL and access token")
            
            if not self.results['mcp_server'].get('health_check', False):
                self.print_status("5. Run: dcisionai-mcp-server health-check")
    
    def run_validation(self):
        """Run the complete validation process."""
        print(f"{Colors.PURPLE}🔍 DcisionAI MCP Server - Setup Validation{Colors.NC}")
        print(f"{Colors.PURPLE}==========================================={Colors.NC}")
        
        self.check_system_requirements()
        self.check_python_environment()
        self.check_dependencies()
        self.check_configuration()
        self.check_aws_credentials()
        self.check_agentcore_connection()
        self.check_mcp_server()
        self.check_ide_integration()
        self.check_docker_setup()
        self.check_cloud_deployment()
        self.generate_report()
        
        return self.overall_status

def main():
    """Main validation function."""
    validator = SetupValidator()
    success = validator.run_validation()
    
    if success:
        print(f"\n{Colors.GREEN}🎉 Validation completed successfully!{Colors.NC}")
        print(f"{Colors.GREEN}Your DcisionAI MCP Server is ready for production use.{Colors.NC}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}❌ Validation failed. Please address the issues above.{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
